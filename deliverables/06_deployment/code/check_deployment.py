"""Verify the saved HW5 procedure, then generate aggregate HW6 evidence."""

import argparse
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import platform
from secrets import token_urlsafe
import subprocess
import sys
import sysconfig
from tempfile import NamedTemporaryFile
from time import perf_counter
import unittest

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from nudgewell_hw6.api import create_app
from nudgewell_hw6.loopback import loopback_client
from nudgewell_hw6.bundle import (
    BASE, BUNDLE, CANDIDATE, FEATURES, RUN, VERSION, Bundle, export_graph,
    session_for, time_features, write_bundle,
)

HW5 = BASE.parent / "05_model_refinement_test_submission"
sys.path.insert(0, str(HW5 / "code"))

from nudgewell_hw5.data_contract import clock_parts, load_dataset, load_protocol
from nudgewell_hw5.runner import TestGate, _check_manifest, _load_selection
from nudgewell_hw5.splits import outer_splits


SOURCE_RUN = "hw5-v1-step5-20261117"
TOLERANCE = 1e-8
WARMUP = 30
REQUESTS = 200
EXAMPLE = {"local_hour": 9, "local_weekday": 1, "elapsed_minutes": 2.0}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def local_gate():
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--", str(RUN / "fold-0" / "model.onnx")],
        cwd=BASE, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("The HW6 run directory must be ignored before exporting.")
    tests = unittest.defaultTestLoader.discover(str(BASE / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(tests)
    if not result.wasSuccessful() or not result.testsRun:
        raise RuntimeError("The HW6 synthetic test gate failed.")
    return result.testsRun


def verify_export(csv):
    protocol = load_protocol()
    data = load_dataset(csv, protocol)
    source = HW5 / "run" / SOURCE_RUN
    results = HW5 / "build" / "results"
    manifest = json.loads((source / "run.json").read_bytes())
    check = json.loads((results / f"{SOURCE_RUN}_verification.json").read_bytes())
    selection = results / f"{SOURCE_RUN}_selection.json"
    evaluation = results / f"{SOURCE_RUN}_evaluation.json"
    predictions = source / "predictions_new_user.csv"
    if (manifest["status"] != "evaluation_complete" or manifest["fixture"]
            or digest(selection) != manifest["selection_public_sha256"]
            or digest(evaluation) != manifest["evaluation_public_sha256"]
            or digest(evaluation) != check["evaluation_sha256"]
            or protocol.digest != check["protocol_sha256"]
            or digest(predictions) != check["private_artifact_sha256"][predictions.name]):
        raise RuntimeError("The HW5 run does not match the independently checked results.")

    _check_manifest(data, TestGate(**manifest["test_gate"]), manifest)
    entry = next(item for item in manifest["folds"] if item["fold"] == 0)
    selected = _load_selection(source, entry)
    outer = outer_splits(data)[0]
    procedure = selected.procedures["refined_selector"]
    population = procedure.population
    population.validate(data)
    model = population.model
    calibration = population.calibration
    pipeline = model._pipeline
    if (selected.outer != outer or population.scope != outer.fit_scope()
            or procedure.candidate_id != CANDIDATE or model.pack != "time_session"
            or tuple(protocol.config["features"]["packs"][model.pack]) != FEATURES
            or model.constant is not None or calibration.kind != "sigmoid"
            or not isinstance(pipeline["classifier"], LogisticRegression)
            or pipeline["classifier"].classes_.tolist() != [0, 1]):
        raise RuntimeError("The saved first fold does not match the export contract.")

    lr = pipeline["classifier"]
    model_bytes = export_graph(
        pipeline["imputer"].statistics_, pipeline["scaler"].mean_, pipeline["scaler"].scale_,
        lr.coef_[0], lr.intercept_[0], calibration.a, calibration.b, procedure.cutoff.value,
    )
    bundle = Bundle(session_for(model_bytes), procedure.cutoff.value)
    held_out = list(outer.test)
    frame = data.frame().iloc[held_out]
    features = time_features(*clock_parts(frame))
    frozen_features = data.features(outer.test, model.pack).to_numpy(dtype=np.float64)
    np.testing.assert_allclose(features, frozen_features, atol=1e-12, rtol=0)
    expected = population.predict(data, outer.test)
    expected_flags = procedure.cutoff.flags(expected)
    archived = pd.read_csv(predictions, float_precision="round_trip", usecols=[
        "outer_fold", "row_position", "refined_selector", "refined_selector_flag",
    ])
    fold = archived.loc[archived["outer_fold"].eq(0)]
    np.testing.assert_array_equal(fold["row_position"].to_numpy(), held_out)
    np.testing.assert_allclose(fold["refined_selector"].to_numpy(), expected, atol=1e-12, rtol=0)
    np.testing.assert_array_equal(fold["refined_selector_flag"].to_numpy(), expected_flags)
    actual = bundle.probabilities(features)
    np.testing.assert_allclose(actual, expected, atol=TOLERANCE, rtol=0)
    np.testing.assert_array_equal(bundle.flags(actual), expected_flags)

    bundle_manifest = {
        "model_version": VERSION,
        "feature_order": list(FEATURES),
        "input_dtype": "float64",
        "validation_cutoff": bundle.cutoff,
        "onnx_sha256": sha256(model_bytes).hexdigest(),
        "hw5_protocol_sha256": protocol.digest,
        "hw5_checkpoint_sha256": entry["sha256"],
    }
    write_bundle(BUNDLE, model_bytes, bundle_manifest)
    return {
        "source_run": SOURCE_RUN,
        "outer_fold_index": 0,
        "candidate_id": CANDIDATE,
        "hw5_evaluation_sha256": check["evaluation_sha256"],
        **bundle_manifest,
        "onnx_opset": 17,
        "onnx_bytes": len(model_bytes),
        "held_out_rows": len(held_out),
        "held_out_participants": len(outer.forbidden_groups),
        "max_feature_difference": float(np.max(np.abs(features - frozen_features))),
        "probability_tolerance": TOLERANCE,
        "max_probability_difference": float(np.max(np.abs(actual - expected))),
        "disagreeing_alert_flags": int(np.count_nonzero(bundle.flags(actual) != expected_flags)),
        "held_out_candidate_flags": int(expected_flags.sum()),
    }


def measure_loopback():
    key = token_urlsafe(32)
    headers = {"X-API-Key": key}
    with loopback_client(create_app(BUNDLE, key)) as client:
        ready = client.get("/health").raise_for_status().json()
        unauthorized = client.post("/v1/predict", json=EXAMPLE).status_code
        invalid = client.post("/v1/predict", json=EXAMPLE | {"answer": 5}, headers=headers).status_code
        sample = client.post("/v1/predict", json=EXAMPLE, headers=headers).raise_for_status().json()
        latencies = []
        for i in range(WARMUP + REQUESTS):
            event = {"local_hour": i % 24, "local_weekday": i % 7,
                     "elapsed_minutes": (i % 61) / 4}
            start = perf_counter()
            client.post("/v1/predict", json=event, headers=headers).raise_for_status()
            if i >= WARMUP:
                latencies.append((perf_counter() - start) * 1000)
        metrics = client.get("/metrics", headers=headers).raise_for_status().json()
    if (ready != {"ready": True} or unauthorized != 401 or invalid != 422
            or metrics["prediction_status_counts"] != {"200": WARMUP + REQUESTS + 1, "401": 1, "422": 1}):
        raise RuntimeError("Loopback API or monitoring did not meet the serving contract.")
    p50, p95 = np.quantile(latencies, [.5, .95])
    return {
        "transport": "sequential HTTP on 127.0.0.1, synthetic check-ins, one server process",
        "warmup_requests": WARMUP,
        "timed_requests": REQUESTS,
        "latency_p50_ms": float(p50),
        "latency_p95_ms": float(p95),
        "synthetic_request": EXAMPLE,
        "synthetic_response": sample,
        "monitoring": metrics,
    }


def main(csv):
    passed = local_gate()
    export = verify_export(csv)
    serving = measure_loopback()
    paths = sorted((BASE / "code").rglob("*.py")) + sorted((BASE / "tests").rglob("*.py"))
    evidence = {
        "status": "verified_local_prototype",
        "synthetic_tests_passed": passed,
        "export": export,
        "serving": serving,
        "environment": {"os": platform.system(), "platform": sysconfig.get_platform(),
                        "python": platform.python_version(),
                        "packages": {name: version(name) for name in (
                            "onnx", "onnxruntime", "fastapi", "pydantic", "starlette", "uvicorn", "httpx",
                        )}},
        "code_sha256": {p.relative_to(BASE).as_posix(): digest(p) for p in paths},
    }
    output = BASE / "build" / "results" / "hw6_local_evidence.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=output.parent, delete=False) as staging:
        staging.write((json.dumps(evidence, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    Path(staging.name).replace(output)
    print(f"Verified {export['held_out_rows']} held-out rows, {passed} tests, "
          f"and {serving['timed_requests']} timed loopback requests.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    main(parser.parse_args().csv)
