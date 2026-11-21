"""Test-gated selection checkpoints and a separate frozen evaluation phase."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import importlib.metadata
import io
import json
import platform
from pathlib import Path
import re
import subprocess
import time
import unittest

import joblib
import numpy as np
import pandas as pd

from .data_contract import ContractError, HOME, ROOT, private_path, sha256, write_private_json, clock_parts
from .evaluation_contract import fit_personal_state, predict_personal_day
from .metrics import decisions, paired_difference, report_metrics
from .models import FitCache
from .selector import select_outer
from .splits import day_splits, outer_splits, split_manifest


def code_fingerprint():
    paths = sorted((HOME / "code").rglob("*.py")) + sorted((HOME / "tests").rglob("*.py"))
    return {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in paths}


def environment_snapshot():
    packages = {}
    for name in ["numpy", "pandas", "scipy", "scikit-learn", "joblib", "pytz", "tzdata"]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": platform.python_version(), "packages": packages}


def git_state():
    return {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "status_porcelain": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)}


@dataclass(frozen=True)
class TestGate:
    passed: bool
    tests_run: int
    protocol_sha256: str
    code_sha256: dict
    fixture_only: bool = False
    test_ids: tuple = ()


def _test_ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _test_ids(item)
        else:
            yield item.id()


def run_test_gate(protocol):
    before = code_fingerprint()
    suite = unittest.defaultTestLoader.discover(str(HOME / "tests"))
    ids = tuple(_test_ids(suite))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    if not result.wasSuccessful() or result.testsRun == 0:
        raise ContractError("Integration-test gate failed.\n" + stream.getvalue())
    if before != code_fingerprint():
        raise ContractError("Code changed during the test gate.")
    return TestGate(True, result.testsRun, protocol.digest, before, test_ids=ids)


def fixture_gate(data):
    if not data.fixture:
        raise ContractError("Fixture gate cannot authorize released-data experiments.")
    return TestGate(True, 1, data.protocol.digest, code_fingerprint(), fixture_only=True)


def assert_gate(data, gate):
    if not gate.passed or gate.tests_run < 1 or gate.protocol_sha256 != data.protocol.digest or gate.code_sha256 != code_fingerprint():
        raise ContractError("Missing, failed or stale integration-test gate.")
    if gate.fixture_only and not data.fixture:
        raise ContractError("Fixture gate cannot authorize released-data experiments.")


def _run_root(run_id):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ContractError("Invalid experiment run ID.")
    return private_path(HOME / "run" / run_id / "run.json").parent


@contextmanager
def _lock(root):
    root.mkdir(parents=True, exist_ok=True)
    lock = private_path(root / ".runner.lock")
    try:
        with lock.open("x", encoding="utf-8") as file:
            file.write("one authoritative HW5 runner\n")
    except FileExistsError:
        raise ContractError("This run already has an active/stale runner lock.") from None
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def _public_path(run_id, phase):
    _run_root(run_id)
    return HOME / "build/results" / f"{run_id}_{phase}.json"


def _write_public(path, payload):
    allowed_root = (HOME / "build/results").resolve()
    if not path.resolve().is_relative_to(allowed_root):
        raise ContractError("Aggregate output path escaped build/results.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _signature(data):
    return hashlib.sha256("|".join(data.keys).encode("ascii")).hexdigest()


def _check_manifest(data, gate, manifest):
    assert_gate(data, gate)
    if (manifest["protocol_sha256"] != data.protocol.digest or manifest["data_signature"] != _signature(data) or manifest["code_sha256"] != gate.code_sha256 or manifest["environment"] != environment_snapshot()):
        raise ContractError("Checkpoint source, protocol, data or environment differs.")


def _load_selection(root, entry):
    path = private_path(root / entry["file"])
    if not path.is_relative_to(root.resolve()) or sha256(path) != entry["sha256"]:
        raise ContractError("Selected-procedure artifact was altered or moved.")
    # Only our locally produced, fingerprinted joblib checkpoints are loaded.
    return joblib.load(path)


def execute_selection(data, run_id, gate, progress=None, fixture_estimator=None, resume=False):
    assert_gate(data, gate)
    if fixture_estimator is not None and not data.fixture:
        raise ContractError("Fixture estimators are not allowed on released data.")
    root = _run_root(run_id)
    manifest_path = root / "run.json"
    with _lock(root):
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            _check_manifest(data, gate, manifest)
            if manifest["status"] in ["selection_complete", "evaluation_running", "evaluation_complete"]:
                public = _public_path(run_id, "selection")
                if sha256(public) != manifest["selection_public_sha256"]:
                    raise ContractError("Stored aggregate selection summary changed.")
                for entry in manifest["folds"]:
                    _load_selection(root, entry)
                return json.loads(public.read_text(encoding="utf-8"))
            if not resume:
                raise ContractError("Partial run exists; use explicit resume with unchanged sources.")
        else:
            manifest = {"run_id": run_id, "status": "selection_running", "protocol_sha256": data.protocol.digest, "data_signature": _signature(data), "code_sha256": gate.code_sha256, "environment": environment_snapshot(), "git_state_at_start": git_state(), "test_gate": asdict(gate), "fixture": data.fixture, "folds": [], "outer_results_opened": False}
            write_private_json(manifest_path, manifest)
            write_private_json(root / "protocol_snapshot.json", data.protocol.config)
        start = time.perf_counter()
        summaries = []
        try:
            outers = outer_splits(data)
            for outer in outers:
                prior = next((x for x in manifest["folds"] if x["fold"] == outer.fold), None)
                if prior:
                    saved = _load_selection(root, prior)
                    summaries.append(saved.public)
                    continue
                if progress:
                    progress(f"outer {outer.fold + 1}/5: beginning inner-only selection")
                cache = FitCache(data, fixture_estimator=fixture_estimator)
                selected = select_outer(data, outer, cache, progress)
                if gate.code_sha256 != code_fingerprint():
                    raise ContractError("Code changed during selection.")
                artifact = private_path(root / f"outer_{outer.fold}.joblib")
                if artifact.exists():
                    raise ContractError("Unregistered artifact exists; refusing to overwrite it.")
                joblib.dump(selected, artifact, compress=3)
                manifest["folds"].append({"fold": outer.fold, "file": artifact.name, "sha256": sha256(artifact)})
                write_private_json(manifest_path, manifest)
                summaries.append(selected.public)
                if progress:
                    progress(f"outer {outer.fold + 1}/5: selected {selected.public['selected_refined']['id']}; checkpoints saved")
            if len(manifest["folds"]) != 5:
                raise ContractError("Selection did not complete all five frozen outer procedures.")
            summary = {"run_id": run_id, "phase": "selection_complete", "protocol_sha256": data.protocol.digest, "test_gate": {"passed": True, "tests_run": gate.tests_run, "fixture_only": gate.fixture_only}, "fixture": data.fixture, "code_sha256": gate.code_sha256, "environment": environment_snapshot(), "data_counts": data.counts, "folds": summaries, "total_fit_counts": {key: sum(s["fit_counts"][key] for s in summaries) for key in ["base_fit_jobs", "estimator_fit_attempts", "cache_hits", "failed_jobs", "constant_fallback_jobs"]}, "seconds_this_invocation": time.perf_counter() - start, "outer_predictions_created": False, "interpretation": "Inner-selection and optimistic training diagnostics only; Step 6 outer evaluation remains unopened."}
            public = _public_path(run_id, "selection")
            _write_public(public, summary)
            manifest.update(status="selection_complete", selection_public_sha256=sha256(public))
            write_private_json(manifest_path, manifest)
            write_private_json(root / "split_manifest.json", split_manifest(data, outers, []))
            return summary
        except Exception as error:
            manifest.update(status="selection_failed", error_type=type(error).__name__, error=str(error))
            write_private_json(manifest_path, manifest)
            raise


def execute_evaluation(data, run_id, gate, progress=None):
    """Step 6 only: requires all five completed, unchanged selection checkpoints."""
    assert_gate(data, gate)
    root = _run_root(run_id)
    with _lock(root):
        manifest_path = root / "run.json"
        if not manifest_path.exists():
            raise ContractError("Evaluation requires completed selection checkpoints.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        _check_manifest(data, gate, manifest)
        if manifest["status"] == "evaluation_complete":
            path = _public_path(run_id, "evaluation")
            if sha256(path) != manifest["evaluation_public_sha256"]:
                raise ContractError("Stored evaluation aggregate changed.")
            return json.loads(path.read_text(encoding="utf-8"))
        if manifest["status"] != "selection_complete" or len(manifest["folds"]) != 5:
            raise ContractError("Outer evaluation is blocked until every selection completes.")
        # Validate every artifact before opening any outer predictions.
        selected = [_load_selection(root, e) for e in sorted(manifest["folds"], key=lambda e: e["fold"])]
        manifest.update(status="evaluation_running", outer_results_opened=True)
        write_private_json(manifest_path, manifest)
        try:
            names = ["fixed_LR", "fixed_RF", "fixed_baseline_selector", "refined_selector", "population_prior"]
            predictions = {name: np.full(len(data), np.nan) for name in names}
            flags = {name: np.zeros(len(data), dtype=bool) for name in names if name != "population_prior"}
            fold_of = np.full(len(data), -1)
            by_subject = {}
            for saved in selected:
                outer = saved.outer
                fold_of[list(outer.test)] = outer.fold
                for name, procedure in saved.procedures.items():
                    values = procedure.population.predict(data, outer.test)
                    predictions[name][list(outer.test)] = values
                    flags[name][list(outer.test)] = procedure.cutoff.flags(values)
                peer_y = data.labels(outer.train)
                predictions["population_prior"][list(outer.test)] = (peer_y.sum() + 1) / (len(peer_y) + 2)
                for subject in outer.forbidden_groups:
                    by_subject[subject] = saved.procedures["refined_selector"]
            if (fold_of < 0).any() or any(not np.isfinite(p).all() for p in predictions.values()):
                raise ContractError("New-user evaluation coverage did not reconcile.")
            y, groups = data.labels(), data.groups()
            new_metrics = {name: report_metrics(y, values, groups, flags.get(name)) for name, values in predictions.items()}
            h, _, elapsed = clock_parts(data.frame())
            rule = h.isin(range(6)).to_numpy() | data.frame()["Category_L1"].eq("Social").to_numpy() | (elapsed > 10)
            new_metrics["fixed_rule"] = decisions(y, rule)
            new_frame = pd.DataFrame({"row_position": np.arange(len(data)), "row_key": data.keys, "participant": groups, "outer_fold": fold_of, "label": y, **predictions, **{name + "_flag": value for name, value in flags.items()}})
            new_frame.to_csv(private_path(root / "predictions_new_user.csv"), index=False)

            daily_rows, daily_values, daily_flags, units, states = [], {name: [] for name in data.protocol.config["known_user"]["variants"]}, {name: [] for name in data.protocol.config["known_user"]["variants"]}, [], []
            for subject in sorted(set(groups)):
                procedure = by_subject[subject]
                for day in day_splits(data, subject):
                    state = fit_personal_state(data, day, procedure.population)
                    result = predict_personal_day(data, day, procedure.population, state)
                    daily_rows.extend(day.test)
                    units.extend([f"{subject}|{day.cutoff_ms}"] * len(day.test))
                    for name, value in result.values.items():
                        daily_values[name].extend(map(float, value))
                        daily_flags[name].extend(map(bool, procedure.cutoff.flags(value)))
                    states.append(asdict(state))
            if len(daily_rows) != len(set(daily_rows)):
                raise ContractError("Daily evaluation duplicated rows.")
            rows = np.asarray(daily_rows, dtype=int)
            # Preserve the same explicit row sequence for every daily method.
            yy, gg = data._labels[rows].copy(), data._frame.iloc[rows]["pid"].astype(str).to_numpy()
            known_metrics = {name: report_metrics(yy, value, gg, daily_flags[name], units) for name, value in daily_values.items()}
            daily_frame = pd.DataFrame({"row_position": rows, "participant": gg, "person_day": units, "label": yy, **daily_values, **{name + "_flag": value for name, value in daily_flags.items()}})
            daily_frame.to_csv(private_path(root / "predictions_known_user.csv"), index=False)
            write_private_json(root / "personal_states.json", states)
            if progress:
                progress("Stored frozen predictions; computing paired participant uncertainty")
            primary = paired_difference(y, predictions["refined_selector"], predictions["fixed_baseline_selector"], groups, data.protocol, "participant_balanced_AP")
            secondary = paired_difference(yy, daily_values["personal_rate"], daily_values["global_plus_daily_personal_offset"], gg, data.protocol, "participant_balanced_Brier")
            if gate.code_sha256 != code_fingerprint():
                raise ContractError("Code changed during evaluation.")
            summary = {"run_id": run_id, "phase": "evaluation_complete", "protocol_sha256": data.protocol.digest, "code_sha256": gate.code_sha256, "fixture": data.fixture, "new_user": new_metrics, "known_user": known_metrics, "primary_contrast": primary, "secondary_prespecified_contrast": secondary, "known_user_coverage": {"rows": len(rows), "people": len(set(gg)), "participant_days": len(states), "personal_state_status_counts": dict(Counter(s["status"] for s in states))}, "interpretation": "Retrospective internal evaluation of the frozen procedure; bootstrap is conditional on stored predictions, not full refitting."}
            public = _public_path(run_id, "evaluation")
            _write_public(public, summary)
            manifest.update(status="evaluation_complete", evaluation_public_sha256=sha256(public))
            write_private_json(manifest_path, manifest)
            return summary
        except Exception as error:
            manifest.update(status="evaluation_failed", error_type=type(error).__name__, error=str(error))
            write_private_json(manifest_path, manifest)
            raise
