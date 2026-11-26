"""Serialize and load the frozen fold-zero logistic procedure."""

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from onnx import TensorProto, checker, helper, numpy_helper
import onnxruntime as ort


BASE = Path(__file__).resolve().parents[2]
RUN = BASE / "run"
BUNDLE = RUN / "fold-0"
VERSION = "hw5-v1-fold-0-refined-hw6-v1"
CANDIDATE = "time_session__lr_C10_balanced"
FEATURES = (
    "hour_sin", "hour_cos", "weekday_sin", "weekday_cos", "log_session_minutes",
)


def time_features(local_hour, local_weekday, elapsed_minutes):
    """Use the same operation order as the frozen HW5 feature builder."""
    hour = 2 * np.pi * np.asarray(local_hour, dtype=np.float64) / 24
    day = 2 * np.pi * np.asarray(local_weekday, dtype=np.float64) / 7
    return np.stack((np.sin(hour), np.cos(hour), np.sin(day), np.cos(day),
                     np.log1p(elapsed_minutes)), axis=-1)


def export_graph(medians, means, scales, weights, intercept, slope, offset, cutoff, *, version=VERSION):
    """Represent sklearn preprocessing, binary LR and HW5 calibration in float64."""
    arrays = {
        "medians": medians, "means": means, "scales": scales,
        "weights": np.asarray(weights).reshape(5, 1),
        "intercept": intercept, "slope": slope, "offset": offset,
        "minimum": 1e-6, "maximum": 1 - 1e-6, "one": 1.0,
    }
    initializers = [
        numpy_helper.from_array(np.asarray(values, dtype=np.float64), name)
        for name, values in arrays.items()
    ]
    steps = [
        ("IsNaN", ["features"], "missing"),
        ("Where", ["missing", "medians", "features"], "filled"),
        ("Sub", ["filled", "means"], "centered"),
        ("Div", ["centered", "scales"], "scaled"),
        ("MatMul", ["scaled", "weights"], "weighted"),
        ("Add", ["weighted", "intercept"], "base_logit"),
        ("Sigmoid", ["base_logit"], "base_probability"),
        ("Clip", ["base_probability", "minimum", "maximum"], "clipped"),
        ("Sub", ["one", "clipped"], "complement"),
        ("Div", ["clipped", "complement"], "odds"),
        ("Log", ["odds"], "log_odds"),
        ("Mul", ["log_odds", "slope"], "adjusted"),
        ("Add", ["adjusted", "offset"], "calibrated_logit"),
        ("Sigmoid", ["calibrated_logit"], "probability_high_gap"),
    ]
    graph = helper.make_graph(
        [helper.make_node(op, inputs, [output]) for op, inputs, output in steps],
        version,
        [helper.make_tensor_value_info("features", TensorProto.DOUBLE, ["rows", 5])],
        [helper.make_tensor_value_info("probability_high_gap", TensorProto.DOUBLE, ["rows", 1])],
        initializers,
    )
    model = helper.make_model(graph, ir_version=10, opset_imports=[helper.make_opsetid("", 17)])
    helper.set_model_props(model, {"validation_cutoff": repr(float(cutoff))})
    checker.check_model(model, full_check=True)
    return model.SerializeToString()


def session_for(model):
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    return ort.InferenceSession(model, sess_options=options, providers=["CPUExecutionProvider"])


@dataclass(frozen=True)
class Bundle:
    session: ort.InferenceSession
    cutoff: float

    def probabilities(self, features):
        values = self.session.run(["probability_high_gap"], {"features": features})[0]
        if values.shape != (len(features), 1) or not np.all(np.isfinite(values) & (values >= 0) & (values <= 1)):
            raise ValueError("The model returned invalid probabilities.")
        return values[:, 0]

    def flags(self, values):
        return np.asarray(values) >= self.cutoff


def load_bundle(directory, *, expected_version=VERSION):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_bytes())
    model = (directory / "model.onnx").read_bytes()
    cutoff = manifest["validation_cutoff"]
    if (manifest["model_version"] != expected_version or manifest["feature_order"] != list(FEATURES)
            or type(cutoff) not in (float, int) or not math.isfinite(cutoff)
            or not 0 <= cutoff <= 1 or sha256(model).hexdigest() != manifest["onnx_sha256"]):
        raise ValueError("Bundle schema or model digest differs from its manifest.")
    try:
        session = session_for(model)
        metadata = session.get_modelmeta()
        if metadata.graph_name != expected_version:
            raise ValueError("The graph version differs from the expected bundle.")
        if metadata.custom_metadata_map.get("validation_cutoff") != repr(float(cutoff)):
            raise ValueError("The manifest cutoff differs from the model metadata.")
        bundle = Bundle(session, float(cutoff))
        bundle.probabilities(np.zeros((1, len(FEATURES)), dtype=np.float64))
    except Exception as error:
        raise ValueError("The runtime could not load the verified model bytes.") from error
    return bundle


def write_bundle(directory, model, manifest):
    """Publish the verified pair together inside its local directory."""
    directory = Path(directory)
    encoded = (json.dumps(manifest, indent=2, allow_nan=False) + "\n").encode("utf-8")
    directory.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=directory.parent) as scratch:
        staged = Path(scratch) / "bundle"
        staged.mkdir()
        (staged / "model.onnx").write_bytes(model)
        (staged / "manifest.json").write_bytes(encoded)
        try:
            staged.rename(directory)
        except OSError:
            if (not directory.is_dir() or (directory / "model.onnx").read_bytes() != model
                    or (directory / "manifest.json").read_bytes() != encoded):
                raise
