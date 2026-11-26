"""Synthetic export, API, monitoring and artifact integrity tests."""

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
import numpy as np
from scipy.special import expit, logit

from nudgewell_hw6.api import create_app
from nudgewell_hw6.bundle import FEATURES, VERSION, export_graph, load_bundle, time_features, write_bundle

from nudgewell_hw6.demo import ABOVE, BELOW, DEMO_VERSION, MEDIANS, MEANS, SCALES, WEIGHTS, write_demo_bundle


KEY = "test-only-key-not-used-for-any-local-server"
HEADERS = {"X-API-Key": KEY}
EXAMPLE = {"local_hour": 9, "local_weekday": 1, "elapsed_minutes": 2.0}


class DeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = export_graph(MEDIANS, MEANS, SCALES, WEIGHTS, -0.1, 0.8, -0.7, .35)
        cls.manifest = {
            "model_version": VERSION, "feature_order": list(FEATURES),
            "validation_cutoff": .35, "onnx_sha256": sha256(cls.model).hexdigest(),
        }

    def setUp(self):
        self.scratch = TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.folder = Path(self.scratch.name) / "bundle"
        write_bundle(self.folder, self.model, self.manifest)

    def client(self):
        return TestClient(create_app(self.folder, KEY))

    def test_graph_matches_reference_including_missing(self):
        rows = np.vstack((time_features(0, 0, 0), time_features(23, 6, 11), np.full(5, np.nan)))
        z = ((np.where(np.isnan(rows), MEDIANS, rows) - MEANS) / SCALES) @ WEIGHTS - .1
        reference = expit(.8 * logit(np.clip(expit(z), 1e-6, 1 - 1e-6)) - .7)
        np.testing.assert_allclose(load_bundle(self.folder).probabilities(rows), reference, rtol=0, atol=1e-12)

    def test_cutoff_boundary_is_inclusive(self):
        bundle = load_bundle(self.folder)
        p = bundle.cutoff
        self.assertEqual(bundle.flags([np.nextafter(p, 0), p, np.nextafter(p, 1)]).tolist(),
                         [False, True, True])

    def test_immutable_bundle_can_be_reused(self):
        write_bundle(self.folder, self.model, self.manifest)
        self.assertEqual((self.folder / "model.onnx").read_bytes(), self.model)
        with self.assertRaises(OSError):
            write_bundle(self.folder, self.model, self.manifest | {"validation_cutoff": 0.4})

    def test_valid_prediction_and_readiness(self):
        with self.client() as client:
            self.assertEqual(client.get("/health").json(), {"ready": True})
            response = client.post("/v1/predict", json=EXAMPLE, headers=HEADERS)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            bundle = load_bundle(self.folder)
            expected = bundle.probabilities(time_features(9, 1, 2.0).reshape(1, -1))[0]
            self.assertEqual(data["model_version"], VERSION)
            self.assertEqual(data["probability_high_gap"], expected)
            self.assertEqual(data["candidate_alert"], expected >= bundle.cutoff)

    def test_demo_uses_its_own_bundle_identity(self):
        demo = Path(self.scratch.name) / "demo"
        write_demo_bundle(demo)
        with TestClient(create_app(demo, KEY, expected_version=DEMO_VERSION)) as client:
            self.assertEqual(client.get("/health").json(), {"ready": True})
            for event, expected in ((BELOW, False), (ABOVE, True)):
                response = client.post("/v1/predict", json=event, headers=HEADERS)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["model_version"], DEMO_VERSION)
                self.assertIs(response.json()["candidate_alert"], expected)
        with TestClient(create_app(demo, KEY)) as client:
            self.assertEqual(client.get("/health").status_code, 503)
        with TestClient(create_app(self.folder, KEY, expected_version=DEMO_VERSION)) as client:
            self.assertEqual(client.get("/health").status_code, 503)

    def test_prediction_and_metrics_require_key(self):
        with self.client() as client:
            self.assertEqual(client.post("/v1/predict", json=EXAMPLE).status_code, 401)
            self.assertEqual(client.get("/metrics").status_code, 401)
            self.assertEqual(client.get("/metrics", headers={"X-API-Key": "wrong"}).status_code, 401)

    def test_no_default_or_short_key(self):
        for value in ("", "password"):
            with self.subTest(key_length=len(value)), self.assertRaises(ValueError):
                create_app(self.folder, value)

    def test_invalid_inputs_return_generic_error(self):
        cases = [{"local_hour": 24}, {"local_hour": "9"}, {"local_hour": True},
                 {"local_weekday": -1}, {"elapsed_minutes": -1.0}, {"elapsed_minutes": None},
                 {"elapsed_minutes": True}, {"answer": 4}]
        with self.client() as client:
            for values in cases:
                with self.subTest(values=values):
                    bad = client.post("/v1/predict", json=EXAMPLE | values, headers=HEADERS)
                    self.assertEqual(bad.status_code, 422)
                    self.assertEqual(bad.json(), {"detail": "Invalid check-in input."})
            for body in ('{"local_hour":0}', '{"local_hour":0,"local_weekday":0,"elapsed_minutes":1e400}', '{'):
                with self.subTest(body=body):
                    bad = client.post("/v1/predict", content=body,
                                      headers=HEADERS | {"Content-Type": "application/json"})
                    self.assertEqual(bad.status_code, 422)

    def test_missing_bundle_fails_closed(self):
        (self.folder / "model.onnx").unlink()
        with self.client() as client:
            self.assertEqual(client.get("/health").status_code, 503)
            self.assertEqual(client.post("/v1/predict", json=EXAMPLE, headers=HEADERS).status_code, 503)

    def test_changed_model_fails_closed(self):
        (self.folder / "model.onnx").write_bytes(self.model + b"changes")
        with self.client() as client:
            self.assertEqual(client.get("/health").json(), {"ready": False})

    def test_changed_schema_fails_closed(self):
        path = self.folder / "manifest.json"
        path.write_text(json.dumps(self.manifest | {"feature_order": list(reversed(FEATURES))}),
                        encoding="utf-8")
        with self.client() as client:
            self.assertEqual(client.get("/health").status_code, 503)

    def test_changed_cutoff_fails_closed(self):
        path = self.folder / "manifest.json"
        path.write_text(json.dumps(self.manifest | {"validation_cutoff": .36}), encoding="utf-8")
        with self.client() as client:
            self.assertEqual(client.get("/health").status_code, 503)

    def test_monitoring_returns_only_expected_aggregates(self):
        with self.client() as client:
            initial = client.get("/metrics", headers=HEADERS).json()
            self.assertEqual(initial["prediction_requests"], 0)
            self.assertIsNone(initial["p95_success_ms"])
            successful = client.post("/v1/predict", json=EXAMPLE, headers=HEADERS).json()
            client.post("/v1/predict", json=EXAMPLE)
            client.post("/v1/predict", json={}, headers=HEADERS)
            metrics = client.get("/metrics", headers=HEADERS).json()
            self.assertEqual(set(metrics), set(initial))
            self.assertEqual(metrics["prediction_requests"], 3)
            self.assertEqual(metrics["prediction_status_counts"], {"200": 1, "401": 1, "422": 1})
            self.assertEqual(metrics["candidate_alert_rate"], float(successful["candidate_alert"]))
            self.assertEqual(metrics["latency_window_size"], 1)
            self.assertGreater(metrics["p95_success_ms"], 0)
