"""Exercise the complete frozen selector/runner on small synthetic data."""

from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "code"))
sys.path.insert(0, str(HOME / "tests"))
from test_contract import ToyClassifier, frame
from nudgewell_hw5.data_contract import ContractError, fixture_dataset, load_protocol, sha256
from nudgewell_hw5.evaluation_contract import CandidateFitError, FittedBase, identity_map, participant_weights
from nudgewell_hw5.metrics import paired_difference, report_metrics
from nudgewell_hw5.models import Candidate, CandidateFactory, FitCache
from nudgewell_hw5.runner import code_fingerprint, execute_evaluation, execute_selection, fixture_gate
from nudgewell_hw5.selector import select_outer
from nudgewell_hw5.splits import FitScope, outer_splits


class ConstantClassifier(ClassifierMixin, BaseEstimator):
    def __init__(self, value=0.5):
        self.value = value

    def fit(self, x, y):
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, x):
        return np.tile([1 - self.value, self.value], (len(x), 1))


def fast_factory(candidate):
    return ConstantClassifier()


@contextmanager
def private_run():
    root = HOME / "run"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root, prefix="integration-") as path:
        directory = Path(path).resolve()
        assert directory.is_relative_to(root.resolve())
        run_id = directory.name
        public = [HOME / "build/results" / (run_id + "_" + phase + ".json") for phase in ["selection", "evaluation"]]
        assert all(not p.exists() for p in public)
        try:
            yield run_id, directory
        finally:
            for p in public:
                assert p.parent.resolve() == (HOME / "build/results").resolve()
                p.unlink(missing_ok=True)


class SelectorIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = load_protocol()
        cls.raw = frame()
        cls.data = fixture_dataset(cls.raw, cls.protocol)

    def test_factory_is_exact_frozen_grid(self):
        factory = CandidateFactory(self.protocol)
        self.assertEqual(len(factory.candidates), 32)
        for c in factory.candidates:
            estimator = factory.estimator(c)
            params = estimator.get_params()
            expected = factory.describe(c)["parameters"]
            for key, value in expected.items():
                self.assertEqual(params[key], value)
        bad = replace(factory.candidates[0], pack="unfrozen")
        with self.assertRaisesRegex(ContractError, "registry"):
            factory.estimator(bad)

    def test_cache_is_scope_sensitive_and_counts_retries(self):
        outer = outer_splits(self.data)[0]
        factory = CandidateFactory(self.protocol)
        c = factory.candidates[0]
        cache = FitCache(self.data, fixture_estimator=lambda c: ToyClassifier(warning_mode="retry"))
        fitted = cache.get(outer.fit_scope(), c)
        self.assertIs(cache.get(outer.fit_scope(), c), fitted)
        self.assertEqual(cache.summary()["base_fit_jobs"], 1)
        self.assertEqual(cache.summary()["estimator_fit_attempts"], 2)
        self.assertEqual(cache.summary()["cache_hits"], 1)
        different = replace(outer.fit_scope(), forbidden_groups=frozenset())
        self.assertIsNot(cache.get(different, c), fitted)
        failed = FitCache(self.data, fixture_estimator=lambda c: ToyClassifier(warning_mode="always"))
        for _ in range(2):
            with self.assertRaises(CandidateFitError):
                failed.get(outer.fit_scope(), c)
        self.assertEqual(failed.summary()["failed_jobs"], 1)
        self.assertEqual(failed.summary()["estimator_fit_attempts"], 2)
        self.assertGreater(failed.summary()["warning_counts"]["ConvergenceWarning"], 0)

    def test_ties_use_declared_order_and_identity(self):
        outer = outer_splits(self.data)[0]
        selected = select_outer(self.data, outer, FitCache(self.data, fixture_estimator=fast_factory))
        self.assertEqual(selected.procedures["refined_selector"].candidate_id, self.protocol.config["models"]["ordered_structural_candidates"][0]["id"])
        self.assertEqual(selected.public["selected_fixed_baseline"]["family"], "LR")
        self.assertFalse(selected.public["calibration"]["requested_sigmoid"])
        self.assertEqual(selected.procedures["refined_selector"].population.calibration.kind, "identity")
        self.assertEqual(selected.public["candidates_declared"], 32)

    def test_all_negative_selector_retains_rows_and_uses_fallbacks(self):
        raw = self.raw.copy()
        raw["answer"] = 8
        data = fixture_dataset(raw, self.protocol)
        outer = outer_splits(data)[0]
        selected = select_outer(data, outer, FitCache(data, fixture_estimator=fast_factory))
        self.assertEqual(selected.public["valid_candidates"], 32)
        self.assertFalse(selected.public["calibration"]["eligible"])
        self.assertEqual(selected.public["fit_counts"]["estimator_fit_attempts"], 0)
        self.assertGreater(selected.public["fit_counts"]["constant_fallback_jobs"], 0)
        for procedure in selected.procedures.values():
            self.assertEqual(procedure.validation_scores.rows, outer.train)
        self.assertEqual(selected.public["stage_diagnostics"]["refined_selector"]["inner_validation_selection_diagnostic"]["participant_balanced_AP"], 0)

    def test_selector_never_reads_outer_labels_or_predicts_outer_rows(self):
        outer = outer_splits(self.data)[0]
        original_labels = type(self.data).labels
        original_predict = FittedBase.predict
        allowed = set(outer.train)
        calls = []
        def labels(data, rows=None):
            self.assertIsNotNone(rows)
            self.assertTrue(set(rows).issubset(allowed))
            calls.append(tuple(rows))
            return original_labels(data, rows)
        def predict(model, data, rows):
            self.assertTrue(set(rows).issubset(allowed))
            return original_predict(model, data, rows)
        with patch.object(type(self.data), "labels", labels), patch.object(FittedBase, "predict", predict):
            selected = select_outer(self.data, outer, FitCache(self.data, fixture_estimator=fast_factory))
        self.assertTrue(calls)
        self.assertFalse(selected.public["outer_predictions_created"])

    def test_outer_label_and_feature_mutations_do_not_change_selection(self):
        outer = outer_splits(self.data)[0]
        first = select_outer(self.data, outer, FitCache(self.data, fixture_estimator=fast_factory))
        changed = self.raw.copy()
        changed.loc[list(outer.test), "answer"] = 3
        changed.loc[list(outer.test), "unlock_time"] = changed.loc[list(outer.test), "esm_time"] - 600000000
        changed.loc[list(outer.test), "session_minutes"] = 10000
        other = fixture_dataset(changed, self.protocol)
        second = select_outer(other, outer, FitCache(other, fixture_estimator=fast_factory))
        for name in first.procedures:
            a, b = first.procedures[name], second.procedures[name]
            self.assertEqual(a.candidate_id, b.candidate_id)
            self.assertEqual(a.validation_scores.values, b.validation_scores.values)
            self.assertEqual(a.cutoff, b.cutoff)
            self.assertEqual(a.population.calibration, b.population.calibration)

    def test_final_calibration_failure_restores_raw_validation_cutoff(self):
        import nudgewell_hw5.selector as selector
        outer = outer_splits(self.data)[0]
        actual = selector.fit_calibration
        def fail_final(data, scores, scope, assessment_rows=()):
            if scope.rows == outer.train:
                return identity_map(scope, "optimizer_failure_identity")
            return actual(data, scores, scope, assessment_rows)
        with patch.object(selector, "fit_calibration", fail_final):
            selected = select_outer(self.data, outer, FitCache(self.data, fixture_estimator=lambda c: ConstantClassifier(0.9)))
        self.assertTrue(selected.public["calibration"]["requested_sigmoid"])
        self.assertEqual(selected.public["calibration"]["effective_map"], "identity")
        self.assertEqual(selected.procedures["refined_selector"].cutoff.value, 0.9)
        self.assertTrue(all(v == 0.9 for v in selected.procedures["refined_selector"].validation_scores.values))

    def test_one_inner_map_failure_makes_sigmoid_ineligible(self):
        import nudgewell_hw5.selector as selector
        outer = outer_splits(self.data)[0]
        actual = selector.fit_calibration
        count = []
        def fail_first(data, scores, scope, assessment_rows=()):
            count.append(scope.rows)
            if len(count) == 1:
                return identity_map(scope, "optimizer_failure_identity")
            return actual(data, scores, scope, assessment_rows)
        with patch.object(selector, "fit_calibration", fail_first):
            selected = select_outer(self.data, outer, FitCache(self.data, fixture_estimator=lambda c: ConstantClassifier(0.9)))
        self.assertFalse(selected.public["calibration"]["eligible"])
        self.assertFalse(selected.public["calibration"]["requested_sigmoid"])
        self.assertEqual(len(count), 3)

    def test_invalid_candidate_is_recorded_but_fixed_anchor_failure_aborts(self):
        outer = outer_splits(self.data)[0]
        first_id = CandidateFactory(self.protocol).candidates[0].id
        selected = select_outer(self.data, outer, FitCache(self.data, fixture_estimator=lambda c: ToyClassifier(warning_mode="error") if c.id == first_id else ConstantClassifier()))
        self.assertEqual(selected.public["valid_candidates"], 31)
        self.assertEqual(selected.public["candidate_trace"][0]["status"], "invalid")
        anchor = CandidateFactory(self.protocol).anchors["LR"].id
        with self.assertRaisesRegex(CandidateFitError, "fixed anchor"):
            select_outer(self.data, outer, FitCache(self.data, fixture_estimator=lambda c: ToyClassifier(warning_mode="error") if c.id == anchor else ConstantClassifier()))

    def test_actual_frozen_estimators_run_one_complete_synthetic_outer_fold(self):
        # No estimator substitution or shortened candidate list on this path.
        selected = select_outer(self.data, outer_splits(self.data)[0])
        self.assertEqual(len(selected.public["candidate_trace"]), 32)
        self.assertEqual(selected.public["valid_candidates"], 32)
        self.assertTrue(selected.public["fit_counts"]["estimator_fit_attempts"] > 0)

    def test_metric_estimands_match_hand_calculation(self):
        y = [1, 0, 0, 0, 0, 1]
        p = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
        groups = ["a", "a", "b", "b", "b", "b"]
        metric = report_metrics(y, p, groups)
        self.assertAlmostEqual(metric["participant_balanced_AP"], 19 / 24)
        self.assertAlmostEqual(metric["pooled_AP"], 2 / 3)
        weights = np.array([0.5, 0.5, 0.25, 0.25, 0.25, 0.25])
        self.assertAlmostEqual(metric["participant_balanced_Brier"], np.dot(weights, (np.array(y) - p)**2) / 2)
        edge = report_metrics([0, 1], [0, 1], ["a", "b"])
        self.assertEqual(edge["reliability"][0]["rows"], 1)
        self.assertEqual(edge["reliability"][-1]["rows"], 1)
        self.assertEqual(edge["within_person"]["eligible_units"], 0)

    def test_paired_bootstrap_and_sign_are_prespecified(self):
        same = paired_difference([0, 1], [0.2, 0.8], [0.2, 0.8], ["a", "b"], self.protocol, "participant_balanced_AP")
        self.assertEqual(same["interval"], [0, 0])
        self.assertEqual(same["finite_replicates"], 2000)
        improved = paired_difference([0, 1], [1, 0], [0, 1], ["a", "b"], self.protocol, "participant_balanced_Brier")
        self.assertEqual(improved["point_difference"], 1)
        self.assertEqual(improved["interval"], [1, 1])

    def test_gate_rejects_stale_code_or_fixture_authorization_for_release(self):
        gate = fixture_gate(self.data)
        with private_run() as (run_id, root):
            with self.assertRaisesRegex(ContractError, "stale"):
                execute_selection(self.data, run_id, replace(gate, code_sha256={}), fixture_estimator=fast_factory)
            self.assertFalse((root / "run.json").exists())
        with self.assertRaisesRegex(ContractError, "Fixture gate"):
            execute_selection(replace(self.data, fixture=False), "must-not-start", gate)

    def test_evaluation_requires_all_five_completed_selections(self):
        with private_run() as (run_id, root):
            gate = fixture_gate(self.data)
            with patch("nudgewell_hw5.runner.select_outer", side_effect=CandidateFitError("injected interruption")):
                with self.assertRaises(CandidateFitError):
                    execute_selection(self.data, run_id, gate, fixture_estimator=fast_factory)
            with self.assertRaisesRegex(ContractError, "until every selection"):
                execute_evaluation(self.data, run_id, gate)

    def test_partial_selection_resumes_without_refitting_completed_fold(self):
        with private_run() as (run_id, root):
            gate = fixture_gate(self.data)
            def interrupted(data, outer, cache, progress):
                if outer.fold == 1:
                    raise CandidateFitError("synthetic interruption")
                return select_outer(data, outer, cache, progress)
            with patch("nudgewell_hw5.runner.select_outer", interrupted):
                with self.assertRaises(CandidateFitError):
                    execute_selection(self.data, run_id, gate, fixture_estimator=fast_factory)
            original_hash = sha256(root / "outer_0.joblib")
            calls = []
            def resumed(data, outer, cache, progress):
                calls.append(outer.fold)
                return select_outer(data, outer, cache, progress)
            with patch("nudgewell_hw5.runner.select_outer", resumed):
                result = execute_selection(self.data, run_id, gate, fixture_estimator=fast_factory, resume=True)
            self.assertEqual(calls, [1, 2, 3, 4])
            self.assertEqual(sha256(root / "outer_0.joblib"), original_hash)
            self.assertEqual(result["phase"], "selection_complete")

    def test_full_runner_roundtrip_is_private_and_idempotent(self):
        with private_run() as (run_id, root):
            gate = fixture_gate(self.data)
            selected = execute_selection(self.data, run_id, gate, fixture_estimator=fast_factory)
            self.assertFalse(selected["outer_predictions_created"])
            self.assertFalse((root / "predictions_new_user.csv").exists())
            with patch("nudgewell_hw5.runner.select_outer", side_effect=AssertionError("duplicate fit")):
                self.assertEqual(execute_selection(self.data, run_id, gate, fixture_estimator=fast_factory), selected)
            artifact = root / "outer_0.joblib"
            original = artifact.read_bytes()
            try:
                artifact.write_bytes(original + b"tampered")
                with self.assertRaisesRegex(ContractError, "altered"):
                    execute_evaluation(self.data, run_id, gate)
            finally:
                artifact.write_bytes(original)
            evaluated = execute_evaluation(self.data, run_id, gate)
            self.assertEqual(evaluated["new_user"]["refined_selector"]["rows"], len(self.data))
            self.assertEqual(evaluated["known_user_coverage"]["people"], 15)
            self.assertEqual(evaluated["primary_contrast"]["point_difference"], 0)
            self.assertEqual(evaluated, execute_evaluation(self.data, run_id, gate))
            public = json.dumps(evaluated)
            for subject in set(self.data.groups()):
                self.assertNotIn(subject, public)
                self.assertNotIn(subject, json.dumps(selected))
            self.assertTrue((root / "predictions_new_user.csv").exists())
            self.assertTrue((root / "predictions_known_user.csv").exists())


if __name__ == "__main__":
    unittest.main()
