"""Hand-set test parameters shared by the API tests and showcase."""

from hashlib import sha256

import numpy as np

from .bundle import FEATURES, export_graph, write_bundle


DEMO_VERSION = "hw6-synthetic-fixture-v1"
CUTOFF = .35
WEIGHTS = np.asarray([0.11, -0.19, 0.25, 0.2, -0.07])
MEDIANS = np.full(5, 0.25)
MEANS = np.full(5, 0.1)
SCALES = np.full(5, 0.8)
BELOW = {"local_hour": 0, "local_weekday": 0, "elapsed_minutes": 0.0}
ABOVE = {"local_hour": 9, "local_weekday": 1, "elapsed_minutes": 2.0}


def write_demo_bundle(directory):
    graph = export_graph(
        MEDIANS, MEANS, SCALES, WEIGHTS, -.1, .8, -.7, CUTOFF, version=DEMO_VERSION,
    )
    write_bundle(directory, graph, {
        "model_version": DEMO_VERSION,
        "feature_order": list(FEATURES),
        "validation_cutoff": CUTOFF,
        "onnx_sha256": sha256(graph).hexdigest(),
    })
