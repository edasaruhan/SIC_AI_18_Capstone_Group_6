"""Checks for the final-showcase page. Synthetic only: no research data or fitted model.

Run from the repository root with the HW6 environment:
    python -B -m unittest discover -s deliverables/06_deployment/showcase/demo_web/tests -v
"""

import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import unittest

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import fixture_v2  # noqa: E402
import serve_showcase as showcase  # noqa: E402
from nudgewell_hw6.bundle import load_bundle, time_features  # noqa: E402
from nudgewell_hw6.demo import DEMO_VERSION  # noqa: E402
from nudgewell_hw6.loopback import loopback_client  # noqa: E402

KEY = "k" * 40


def recorded():
    text = (HERE / "day.js").read_text(encoding="utf-8")
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


class IllustrativeFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = TemporaryDirectory()
        cls.directory = Path(cls.scratch.name) / "bundle"
        fixture_v2.write_v2_bundle(cls.directory)
        cls.bundle = load_bundle(cls.directory, expected_version=fixture_v2.VERSION)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def score(self, hours, weekdays, minutes):
        return self.bundle.probabilities(time_features(np.asarray(hours), np.asarray(weekdays),
                                                       np.asarray(minutes, dtype=float)))

    def test_version_is_separate_from_the_hw6_fixture(self):
        self.assertNotEqual(fixture_v2.VERSION, DEMO_VERSION)
        manifest = json.loads((self.directory / "manifest.json").read_text())
        self.assertEqual((manifest["model_version"], manifest["validation_cutoff"]),
                         (fixture_v2.VERSION, fixture_v2.CUTOFF))

    def test_risk_rises_with_session_length_at_every_hour(self):
        minutes = [0, 2, 5, 10, 20, 40, 90]
        for hour in range(24):
            values = self.score([hour] * len(minutes), [1] * len(minutes), minutes)
            self.assertTrue(np.all(np.diff(values) > 0), hour)

    def test_late_evening_is_higher_than_morning_and_weekday_has_no_effect(self):
        for minutes in (3, 15, 30):
            night, morning = self.score([22, 9], [1, 1], [minutes, minutes])
            self.assertGreater(night, morning)
        week = self.score([23] * 7, list(range(7)), [20.0] * 7)
        self.assertLess(np.ptp(week), 1e-12)


class ScriptedDayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = TemporaryDirectory()
        directory = Path(cls.scratch.name) / "bundle"
        fixture_v2.write_v2_bundle(directory)
        cls.app = showcase.build_app(directory, KEY)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def test_day_shows_each_policy_outcome(self):
        with loopback_client(self.app) as client:
            rows, _ = showcase.run_day(client, KEY)
        decisions = [r["decision"] for r in rows]
        self.assertEqual(decisions.count("delivered"), 3)
        self.assertEqual(decisions.count("cooldown"), 1)
        self.assertEqual(decisions.count("daily_cap"), 1)
        self.assertEqual(sum(r["timer_fires"] for r in rows), 6)

    def test_recorded_fallback_matches_the_live_api(self):
        # Probabilities may differ in the last bits between Windows and macOS runtimes, so they
        # are compared within the page's own drift threshold. Everything else must match exactly.
        with loopback_client(self.app) as client:
            fresh = json.loads(json.dumps(showcase.recorded_payload(*showcase.run_day(client, KEY)),
                                          ensure_ascii=False))
        saved = recorded()
        stale = "day.js is stale: run serve_showcase.py --record"
        for old, new in zip(saved["checkins"], fresh["checkins"]):
            self.assertAlmostEqual(old["response"].pop("probability_high_gap"),
                                   new["response"].pop("probability_high_gap"), delta=1e-9, msg=stale)
        self.assertEqual(saved, fresh, stale)

    def test_page_and_policy_endpoints(self):
        with loopback_client(self.app) as client:
            page = client.get("/").raise_for_status().text
            self.assertIn(f'content="{KEY}"', page)
            self.assertNotIn(showcase.KEY_PLACEHOLDER, page)
            self.assertEqual(client.get("/health").json(), {"ready": True})
            self.assertEqual(client.get("/day.js").status_code, 200)
            body = {"times": ["20:30"], "candidates": [True], "elapsed_minutes": [22.0]}
            self.assertEqual(client.post("/showcase/policy", json=body).status_code, 401)
            ok = client.post("/showcase/policy", json=body, headers={"X-API-Key": KEY})
            self.assertEqual(ok.json()["decisions"], ["delivered"])
            unsorted = {"times": ["21:00", "20:00"], "candidates": [True, True], "elapsed_minutes": [1.0, 1.0]}
            self.assertEqual(client.post("/showcase/policy", json=unsorted,
                                         headers={"X-API-Key": KEY}).status_code, 422)


class OfflinePageTests(unittest.TestCase):
    def test_page_loads_nothing_from_the_network_and_keeps_the_label(self):
        page = (HERE / "index.html").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"""(src|href)\s*=\s*["'](https?:)?//""", page))
        self.assertNotIn("@import", page)
        self.assertIn("Temsili, elle ayarlanmış model", page)
        self.assertIn(showcase.KEY_PLACEHOLDER, page)


if __name__ == "__main__":
    unittest.main()
