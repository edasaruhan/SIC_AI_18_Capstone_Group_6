"""Illustrative hand-set parameters for the final showcase page.

No weight here was fitted to the AwareMind release. The signs only follow the
published aggregate direction (higher gap at night and as a session goes on;
Zheng & Choe 2026 and our HW2 summary). Weekday has no effect. The HW6
synthetic fixture v1 in ``code/nudgewell_hw6/demo.py`` stays unchanged.
"""

from hashlib import sha256
from pathlib import Path
import sys

import numpy as np

HW6 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HW6 / "code"))

from nudgewell_hw6.bundle import FEATURES, export_graph, write_bundle  # noqa: E402

VERSION = "showcase-illustrative-v2"
CUTOFF = 0.30
# Feature order: hour_sin, hour_cos, weekday_sin, weekday_cos, log_session_minutes.
# The hour terms peak at about 22:20; the session term rises with log1p(minutes).
WEIGHTS = np.asarray([-0.25, 0.55, 0.0, 0.0, 0.45])
INTERCEPT = -2.6
# Identity preprocessing and calibration keep the hand-set logit readable.
MEDIANS = np.zeros(len(FEATURES))
MEANS = np.zeros(len(FEATURES))
SCALES = np.ones(len(FEATURES))
SLOPE, OFFSET = 1.0, 0.0


def write_v2_bundle(directory):
    graph = export_graph(MEDIANS, MEANS, SCALES, WEIGHTS, INTERCEPT, SLOPE, OFFSET, CUTOFF,
                         version=VERSION)
    write_bundle(directory, graph, {
        "model_version": VERSION,
        "feature_order": list(FEATURES),
        "validation_cutoff": CUTOFF,
        "onnx_sha256": sha256(graph).hexdigest(),
    })
