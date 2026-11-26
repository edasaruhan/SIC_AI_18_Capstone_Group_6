"""Exercise simulated delivery boundaries with synthetic events."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

from replay_policy import delivery_decisions


class PolicyReplayTests(unittest.TestCase):
    def test_cooldown_and_cap_in_showcase_order(self):
        entries = [(minute * 60_000, 1, True) for minute in (0, 10, 30, 60, 90)]
        self.assertEqual(list(delivery_decisions(entries)),
                         ["delivered", "cooldown", "delivered", "delivered", "daily_cap"])

    def test_midnight_resets_cap_and_preserves_exact_elapsed_cooldown(self):
        events = [(m * 60_000, day, True) for m, day in
                  ((1350, 1), (1380, 1), (1435, 1), (1440, 2), (1465, 2))]
        self.assertEqual(list(delivery_decisions(events)),
                         ["delivered", "delivered", "delivered", "cooldown", "delivered"])

    def test_people_with_no_candidates_keep_their_rows(self):
        self.assertEqual(list(delivery_decisions([(0, 1, False), (60_000, 1, False)])),
                         ["not_flagged", "not_flagged"])
