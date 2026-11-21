"""Small synthetic challenges to the frozen data/fit boundaries."""

from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "code"))
from nudgewell_hw5.data_contract import (ContractError, HOME as CONTRACT_HOME, ROOT, PROTOCOL_SHA256, build_features, fixture_dataset, load_protocol, private_path, validate_feature_matrix, write_private_json)
from nudgewell_hw5.splits import (DaySplit, FitScope, assert_day_split, assert_group_split, assert_scope, calibration_splits, day_splits, fold_groups, group_splits, inner_splits, outer_splits, peer_scope)
from nudgewell_hw5.evaluation_contract import (CandidateFitError, CrossFitScores, FittedCutoff, MatchedPredictions, PopulationPredictor, apply_calibration, assert_scores, combine_scores, cross_fit, fit_base, fit_calibration, fit_cutoff, fit_personal_state, heldout_scores, identity_map, metric_summary, participant_weights, predict_personal_day)


def row(pid, utc, label=0, session=None, zone="America/New_York", category="Social", unlock=None, lock=None):
    stamp = pd.Timestamp(utc)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    ms = int(stamp.value // 1_000_000)
    local = stamp.tz_convert(zone)
    result = {"pid": pid, "session_id_combined": session or f"{pid}-{ms}", "answer": 3 if label else 8, "remaining_minutes": 10.0, "esm_time": ms, "unlock_time": ms - 120000 if unlock is None else unlock, "lock_time": ms + 600000 if lock is None else lock, "timezone": zone, "esm_local": local.strftime("%Y-%m-%d %H:%M:%S"), "esm_hour": local.hour, "esm_weekday": local.dayofweek, "Category_L1": category, "app_at_prompt": "synthetic.app" if category is not None else None, "package_name": "synthetic.app" if category is not None else None, "Age": 123, "tap_count": 1000000, "screen_time_minutes": 999999}
    result["session_minutes"] = (ms - result["unlock_time"]) / 60000
    for c in ["Social", "Media", "Browser", "Game", "Message", "Work & Study", "Daily Life", "System tool", "To exclude"]:
        result["genre_" + c] = c == category
    return result


def frame(people=15):
    return pd.DataFrame([row(f"fixture-{g:02}", pd.Timestamp("2025-01-01T17:30:00Z") + pd.Timedelta(days=d, hours=g % 4), (g + d) % 2, category="Social" if d % 2 else "Browser") for g in range(people) for d in [0, 2, 6, 7, 8, 9]])


class ToyClassifier(ClassifierMixin, BaseEstimator):
    """The fitted score visibly depends on both fitting labels and features."""
    def __init__(self, warning_mode="none", max_iter=2000):
        self.warning_mode = warning_mode
        self.max_iter = max_iter

    def fit(self, x, y):
        if self.warning_mode == "error":
            raise RuntimeError("synthetic failure")
        if self.warning_mode == "warn":
            warnings.warn("synthetic diagnostic", UserWarning)
        if self.warning_mode == "always" or (self.warning_mode == "retry" and self.max_iter < 10000):
            warnings.warn("synthetic convergence", ConvergenceWarning)
        self.classes_ = np.array([0, 1])
        self.rate_ = float((np.sum(y) + 1) / (len(y) + 2))
        self.feature_mean_ = np.mean(x, axis=0)
        return self

    def predict_proba(self, x):
        score = np.clip(self.rate_ + 0.02 * np.tanh(np.asarray(x)[:, 0]), 0.01, 0.99)
        return np.column_stack([1 - score, score])


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = load_protocol()

    def setUp(self):
        self.raw = frame()
        self.data = fixture_dataset(self.raw, self.protocol)

    def population(self, data, outer=None):
        outer = outer or outer_splits(data)[0]
        scope = outer.fit_scope()
        model = fit_base(data, scope, ToyClassifier())
        return PopulationPredictor(model, identity_map(scope), scope), outer

    def test_protocol_and_source_seal(self):
        self.assertEqual(self.protocol.digest, PROTOCOL_SHA256)
        original = self.protocol.config
        original["splits"]["seed"] = -1
        self.assertEqual(self.protocol.config["splits"]["seed"], 42)
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local, prefix="hw5-seal-test-") as name:
            directory = Path(name).resolve()
            self.assertTrue(directory.is_relative_to(local.resolve()))
            target = directory / "protocol.json"
            target.write_bytes((HOME / "build/protocol.json").read_bytes() + b" ")
            target.with_suffix(".sha256").write_text(PROTOCOL_SHA256 + "  protocol.json\n")
            with self.assertRaisesRegex(ContractError, "frozen"):
                load_protocol(target)

    def test_deduplication_preserves_file_order_and_label_boundary(self):
        raw = pd.concat([self.raw.iloc[[4, 2]], self.raw.iloc[[4]]], ignore_index=True)
        raw.loc[1, "answer"] = 5
        raw.loc[1, "remaining_minutes"] = 5
        data = fixture_dataset(raw, self.protocol)
        self.assertEqual(len(data), 2)
        self.assertEqual(data.frame()["esm_time"].tolist(), raw["esm_time"].iloc[:2].tolist())
        self.assertEqual(data.labels()[1], 0)
        raw.loc[1, "remaining_minutes"] = 5.0001
        self.assertEqual(fixture_dataset(raw, self.protocol).labels()[1], 1)

    def test_missing_or_invalid_contract_fields_stop(self):
        cases = [("answer", np.nan), ("answer", 11), ("remaining_minutes", -1), ("lock_time", np.inf), ("timezone", "not/a/timezone"), ("pid", None), ("session_id_combined", None), ("Category_L1", "unfrozen"), ("esm_hour", 99), ("session_minutes", 999)]
        for name, value in cases:
            with self.subTest(field=name, invalid=str(value)):
                bad = self.raw.copy()
                bad[name] = bad[name].astype(object)
                bad.loc[0, name] = value
                with self.assertRaises((ContractError,)):
                    fixture_dataset(bad, self.protocol)
        with self.assertRaisesRegex(ContractError, "required columns"):
            fixture_dataset(self.raw.drop(columns="lock_time"), self.protocol)

    def test_inconsistent_session_is_rejected(self):
        bad = self.raw.copy()
        bad.loc[1, "session_id_combined"] = bad.loc[0, "session_id_combined"]
        with self.assertRaisesRegex(ContractError, "session"):
            fixture_dataset(bad, self.protocol)

    def test_missing_and_unmapped_inference_context_is_explicit(self):
        raw = self.raw.iloc[:2].copy()
        raw.loc[raw.index[0], "Category_L1"] = None
        raw.loc[raw.index[1], "Category_L1"] = "new unseen category"
        x = build_features(raw, self.protocol)
        self.assertTrue(x["app_context_missing"].eq(1).all())
        self.assertTrue(x.filter(like="genre_").eq(0).all().all())

    def test_features_do_not_read_outcomes_or_identifiers(self):
        before = build_features(self.raw, self.protocol)
        poisoned = self.raw.copy()
        for c in ["answer", "remaining_minutes", "lock_time", "Age", "tap_count", "screen_time_minutes"]:
            poisoned[c] = np.nan
        poisoned["pid"] = "must-not-be-a-feature"
        pd.testing.assert_frame_equal(before, build_features(poisoned, self.protocol))
        inference = poisoned.drop(columns=["answer", "remaining_minutes", "lock_time", "pid", "Age"])
        pd.testing.assert_frame_equal(before, build_features(inference, self.protocol))

    def test_feature_order_and_forbidden_columns_are_enforced(self):
        x = self.data.features()
        self.assertEqual(x.shape[1], 15)
        self.assertEqual(self.data.features(pack="time_session").shape[1], 5)
        for bad in [x.assign(answer=1), x.iloc[:, ::-1], x.drop(columns="hour_sin")]:
            with self.assertRaisesRegex(ContractError, "feature order"):
                validate_feature_matrix(bad, self.protocol, "main_context")

    def test_nested_splits_exclude_every_parent_test_person(self):
        outers = outer_splits(self.data)
        self.assertEqual(len(outers), 5)
        self.assertEqual(sorted(r for s in outers for r in s.test), list(range(len(self.data))))
        for outer in outers:
            for inner in inner_splits(self.data, outer):
                self.assertTrue(outer.forbidden_groups.issubset(inner.forbidden_groups))
                for cal in calibration_splits(self.data, outer, inner):
                    self.assertFalse(set(self.data.groups(cal.train)) & inner.forbidden_groups)
                    self.assertEqual(set(cal.universe), set(inner.train))

    def test_split_assignment_is_label_and_row_order_blind(self):
        changed = self.raw.copy()
        changed["answer"] = 11 - changed["answer"]
        other = fixture_dataset(changed.iloc[::-1], self.protocol)
        first = [set(self.data.groups(s.test)) for s in outer_splits(self.data)]
        second = [set(other.groups(s.test)) for s in outer_splits(other)]
        self.assertEqual(first, second)
        with self.assertRaisesRegex(ContractError, "fold count"):
            fold_groups(["only-one"], "outer", 5)

    def test_folds_match_frozen_preflight_assignment(self):
        spec = importlib.util.spec_from_file_location("frozen_preflight", HOME / "build/validate_protocol.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        groups = self.data.groups()
        self.assertEqual(fold_groups(groups, "outer", 5), module.fold_groups(groups, "outer", 5))

    def test_fit_rejects_outer_people_even_when_row_universe_is_broad(self):
        outer = outer_splits(self.data)[0]
        bad = FitScope(tuple(range(len(self.data))), tuple(range(len(self.data))), outer.forbidden_groups)
        with self.assertRaisesRegex(ContractError, "Forbidden participant"):
            fit_base(self.data, bad, ToyClassifier())
        corrupt = replace(outer, train=tuple(sorted(outer.train + outer.test[:1])))
        with self.assertRaises(ContractError):
            assert_group_split(self.data, corrupt)

    def test_train_only_preprocessing_and_evaluation_feature_invariance(self):
        outer = outer_splits(self.data)[0]
        model = fit_base(self.data, outer.fit_scope(), ToyClassifier())
        changed = self.raw.copy()
        for r in outer.test:
            changed.loc[r, "unlock_time"] = changed.loc[r, "esm_time"] - 600000000
            changed.loc[r, "session_minutes"] = 10000
        other = fixture_dataset(changed, self.protocol)
        refit = fit_base(other, outer.fit_scope(), ToyClassifier())
        np.testing.assert_array_equal(model._pipeline["imputer"].statistics_, refit._pipeline["imputer"].statistics_)
        np.testing.assert_array_equal(model._pipeline["scaler"].mean_, refit._pipeline["scaler"].mean_)
        np.testing.assert_array_equal(model._pipeline["scaler"].var_, refit._pipeline["scaler"].var_)
        before = model._pipeline["scaler"].mean_.copy()
        model.predict(other, outer.test)
        np.testing.assert_array_equal(before, model._pipeline["scaler"].mean_)

    def test_all_missing_training_feature_keeps_its_column(self):
        outer = outer_splits(self.data)[0]
        original = type(self.data).features
        def missing(data, rows=None, pack="main_context"):
            x = original(data, rows, pack)
            x["hour_sin"] = np.nan
            return x
        with patch.object(type(self.data), "features", missing):
            fitted = fit_base(self.data, outer.fit_scope(), ToyClassifier())
            self.assertEqual(fitted._pipeline["imputer"].statistics_[0], 0)
            self.assertEqual(fitted._pipeline["scaler"].n_features_in_, 15)
            self.assertTrue(np.isfinite(fitted.predict(self.data, outer.test)).all())

    def test_scoped_sklearn_pipeline_runs_on_tiny_fixture(self):
        outer = outer_splits(self.data)[0]
        model = fit_base(self.data, outer.fit_scope(), LogisticRegression(C=1, class_weight="balanced", max_iter=2000))
        self.assertTrue(np.isfinite(model.predict(self.data, outer.test)).all())
        self.assertEqual(model.training_rows, outer.train)

    def test_single_class_and_empty_base_fallbacks(self):
        raw = self.raw.copy()
        raw["answer"] = 8
        data = fixture_dataset(raw, self.protocol)
        scope = outer_splits(data)[0].fit_scope()
        fitted = fit_base(data, scope, ToyClassifier(warning_mode="error"))
        self.assertEqual(fitted.status, "one_class_training")
        self.assertAlmostEqual(fitted.constant, 1 / (len(scope.rows) + 2))
        empty = fit_base(data, FitScope((), ()), ToyClassifier(warning_mode="error"))
        self.assertEqual(empty.constant, 0.5)

    def test_warning_retry_and_failure_behavior(self):
        scope = outer_splits(self.data)[0].fit_scope()
        warned = fit_base(self.data, scope, ToyClassifier(warning_mode="warn"))
        self.assertTrue(warned.warning_records)
        retry = fit_base(self.data, scope, ToyClassifier(warning_mode="retry"))
        self.assertEqual(retry.status, "retried_convergence")
        self.assertEqual(retry._pipeline["classifier"].max_iter, 10000)
        for mode in ["always", "error"]:
            with self.subTest(mode=mode), self.assertRaises(CandidateFitError):
                fit_base(self.data, scope, ToyClassifier(warning_mode=mode))

    def test_old_global_oof_others_dependency_is_rejected(self):
        all_rows = tuple(range(len(self.data)))
        contaminated = cross_fit(self.data, FitScope(all_rows, all_rows), tuple(group_splits(self.data, all_rows, "old-whole-population", 3)), ToyClassifier)
        excluded = str(self.data.groups()[0])
        peers = tuple(i for i, g in enumerate(self.data.groups()) if g != excluded)
        selected = contaminated.subset(peers)
        with self.assertRaisesRegex(ContractError, "Indirect forbidden-participant"):
            fit_calibration(self.data, selected, FitScope(peers, peers, frozenset([excluded])))

    def test_clean_calibration_excludes_assessment_upstream_and_is_invariant(self):
        outer = outer_splits(self.data)[0]
        inner = inner_splits(self.data, outer)[0]
        scores = cross_fit(self.data, inner.fit_scope(), calibration_splits(self.data, outer, inner), ToyClassifier)
        fitted = fit_calibration(self.data, scores, inner.fit_scope(), inner.test)
        poisoned = self.raw.copy()
        poison_rows = tuple(sorted(outer.test + inner.test))
        poisoned.loc[list(poison_rows), "answer"] = 3
        poisoned.loc[list(poison_rows), "tap_count"] = -999999
        other = fixture_dataset(poisoned, self.protocol)
        rescored = cross_fit(other, inner.fit_scope(), calibration_splits(other, outer, inner), ToyClassifier)
        refitted = fit_calibration(other, rescored, inner.fit_scope(), inner.test)
        self.assertEqual(scores.values, rescored.values)
        self.assertEqual((fitted.a, fitted.b, fitted.status), (refitted.a, refitted.b, refitted.status))
        self.assertFalse(set(self.data.groups(fitted.dependency_rows)) & inner.forbidden_groups)

    def test_calibration_rejects_self_assessment_or_incomplete_provenance(self):
        outer = outer_splits(self.data)[0]
        scores = cross_fit(self.data, outer.fit_scope(), inner_splits(self.data, outer), ToyClassifier)
        with self.assertRaisesRegex(ContractError, "assessment participants overlap"):
            fit_calibration(self.data, scores, outer.fit_scope(), outer.train[:1])
        with self.assertRaisesRegex(ContractError, "provenance"):
            assert_scores(self.data, replace(scores, blocks=()), outer.fit_scope())

    def test_calibration_fallbacks_are_explicit(self):
        raw = self.raw.copy()
        raw["answer"] = 8
        data = fixture_dataset(raw, self.protocol)
        outer = outer_splits(data)[0]
        scores = cross_fit(data, outer.fit_scope(), inner_splits(data, outer), ToyClassifier)
        self.assertEqual(fit_calibration(data, scores, outer.fit_scope()).status, "one_class_identity")
        outer = outer_splits(self.data)[0]
        scores = cross_fit(self.data, outer.fit_scope(), inner_splits(self.data, outer), ToyClassifier)
        with patch("nudgewell_hw5.evaluation_contract.minimize", return_value=types.SimpleNamespace(success=False, x=np.array([np.nan, np.nan]))):
            self.assertEqual(fit_calibration(self.data, scores, outer.fit_scope()).status, "optimizer_failure_identity")

    def test_calibrated_validation_scores_keep_full_upstream_provenance(self):
        outer = outer_splits(self.data)[0]
        parts = []
        for inner in inner_splits(self.data, outer):
            calibration_scores = cross_fit(self.data, inner.fit_scope(), calibration_splits(self.data, outer, inner), ToyClassifier)
            calibration = fit_calibration(self.data, calibration_scores, inner.fit_scope(), inner.test)
            fitted = fit_base(self.data, inner.fit_scope(), ToyClassifier())
            part = apply_calibration(self.data, heldout_scores(self.data, fitted, inner.test), calibration)
            self.assertTrue(all(set(b.training_rows).issubset(inner.train) for b in part.blocks))
            parts.append(part)
        combined = combine_scores(self.data, parts)
        assert_scores(self.data, combined, outer.fit_scope())
        self.assertEqual(combined.rows, outer.train)
        self.assertTrue(np.isfinite(fit_cutoff(self.data, combined, outer.fit_scope()).value))

    def test_self_calibration_cannot_be_relabelled_as_heldout_scores(self):
        outer = outer_splits(self.data)[0]
        scores = cross_fit(self.data, outer.fit_scope(), inner_splits(self.data, outer), ToyClassifier)
        fitted = fit_calibration(self.data, scores, outer.fit_scope())
        self.assertEqual(fitted.kind, "sigmoid")
        with self.assertRaisesRegex(ContractError, "score-assessment participants overlap"):
            apply_calibration(self.data, scores, fitted)
        with self.assertRaisesRegex(ContractError, "Duplicate held-out"):
            combine_scores(self.data, [scores, scores])

    def test_identity_fallback_does_not_erase_calibration_dependencies(self):
        raw = self.raw.copy()
        raw["answer"] = 8
        data = fixture_dataset(raw, self.protocol)
        outer = outer_splits(data)[0]
        scores = cross_fit(data, outer.fit_scope(), inner_splits(data, outer), ToyClassifier)
        fallback = fit_calibration(data, scores, outer.fit_scope())
        self.assertEqual(fallback.kind, "identity")
        self.assertEqual(fallback.fitting_rows, outer.train)
        with self.assertRaisesRegex(ContractError, "score-assessment participants overlap"):
            apply_calibration(data, scores, fallback)

    def test_cutoff_uses_permitted_validation_only_and_stays_fixed(self):
        outer = outer_splits(self.data)[0]
        scores = cross_fit(self.data, outer.fit_scope(), inner_splits(self.data, outer), ToyClassifier)
        cutoff = fit_cutoff(self.data, scores, outer.fit_scope())
        expected = float(np.quantile(scores.values, 0.75, method="higher"))
        self.assertEqual(cutoff.value, expected)
        fixed_row = cutoff.flags([0.6])[0]
        for other_eval in [[0.0, 0.6], [0.6, 1.0, 0.9], [0.6]]:
            idx = other_eval.index(0.6)
            self.assertEqual(cutoff.flags(other_eval)[idx], fixed_row)
        self.assertEqual(cutoff.value, expected)
        self.assertTrue(FittedCutoff(0.5, ()).flags([0.5])[0])
        with self.assertRaises(ContractError):
            fit_cutoff(self.data, scores, FitScope(outer.test, outer.test, frozenset(self.data.groups(outer.train))))

    def test_future_labels_do_not_change_earlier_personal_predictions(self):
        population, outer = self.population(self.data)
        subject = next(iter(outer.forbidden_groups))
        day = tuple(day_splits(self.data, subject))[0]
        state = fit_personal_state(self.data, day, population)
        before = predict_personal_day(self.data, day, population, state)
        changed = self.raw.copy()
        future = changed.pid.eq(subject) & changed.esm_time.ge(day.cutoff_ms)
        changed.loc[future, "answer"] = 11 - changed.loc[future, "answer"]
        other = fixture_dataset(changed, self.protocol)
        other_day = tuple(day_splits(other, subject))[0]
        after_state = fit_personal_state(other, other_day, population)
        after = predict_personal_day(other, other_day, population, after_state)
        self.assertEqual(state, after_state)
        for name in before.values:
            np.testing.assert_array_equal(before.values[name], after.values[name])
        # Negative control: changing permitted past labels must affect adaptation.
        changed = self.raw.copy()
        changed.loc[list(day.history), "answer"] = 11 - changed.loc[list(day.history), "answer"]
        past = fixture_dataset(changed, self.protocol)
        adapted = fit_personal_state(past, tuple(day_splits(past, subject))[0], population)
        self.assertNotEqual(state.personal_rate, adapted.personal_rate)
        self.assertNotAlmostEqual(state.delta, adapted.delta)

    def test_population_calibrator_with_hidden_person_dependency_fails(self):
        population, outer = self.population(self.data)
        subject = next(iter(outer.forbidden_groups))
        day = tuple(day_splits(self.data, subject))[0]
        contaminated = replace(population.calibration, dependency_rows=outer.test[:1])
        with self.assertRaisesRegex(ContractError, "indirect forbidden dependency"):
            fit_personal_state(self.data, day, replace(population, calibration=contaminated))
        self.assertEqual(peer_scope(self.data, outer, day), outer.fit_scope())

    def test_personal_single_class_empty_and_optimizer_fallback(self):
        population, outer = self.population(self.data)
        subject = next(iter(outer.forbidden_groups))
        day = tuple(day_splits(self.data, subject))[0]
        raw = self.raw.copy()
        raw.loc[list(day.history), "answer"] = 8
        one_class = fixture_dataset(raw, self.protocol)
        state = fit_personal_state(one_class, tuple(day_splits(one_class, subject))[0], population)
        self.assertTrue(np.isfinite(state.delta))
        self.assertGreater(state.personal_rate, 0)
        with patch("nudgewell_hw5.evaluation_contract.minimize", return_value=types.SimpleNamespace(success=False, x=np.array([np.nan]))):
            fallback = fit_personal_state(self.data, day, population)
        self.assertEqual((fallback.delta, fallback.status), (0.0, "optimizer_failure_global"))
        # First prompt unresolved through the first evaluated day: no own labels yet.
        rows = [row("new", "2025-01-01T17:00Z", 0, lock=int(pd.Timestamp("2025-01-09T20:00Z").value // 1_000_000)), row("new", "2025-01-08T17:00Z", 1)]
        small = fixture_dataset(pd.concat([self.raw, pd.DataFrame(rows)], ignore_index=True), self.protocol)
        peers = tuple(i for i, g in enumerate(small.groups()) if g != "new")
        scope = FitScope(peers, peers, frozenset(["new"]))
        pop = PopulationPredictor(fit_base(small, scope, ToyClassifier()), identity_map(scope), scope)
        empty_day = tuple(day_splits(small, "new"))[0]
        empty = fit_personal_state(small, empty_day, pop)
        self.assertEqual((empty.delta, empty.status, empty.history_rows), (0.0, "empty_history", ()))
        self.assertEqual(empty.personal_rate, empty.peer_prior)

    def test_strict_cutoff_equal_late_lock_and_shared_session(self):
        cutoff = int(pd.Timestamp("2025-03-09T05:00Z").value // 1_000_000)
        rows = [row("clock", "2025-03-02T17:30Z"), row("clock", "2025-03-09T04:55Z", lock=cutoff), row("clock", "2025-03-09T04:59Z", session="crossing", unlock=cutoff - 180000, lock=cutoff + 3600000), row("clock", "2025-03-09T05:10Z", session="crossing", unlock=cutoff - 180000, lock=cutoff + 3600000)]
        data = fixture_dataset(pd.DataFrame(rows), self.protocol)
        day = tuple(day_splits(data, "clock"))[0]
        self.assertEqual(day.history, (0,))
        self.assertEqual(day.unresolved_prior, (1, 2))
        self.assertEqual(day.test, (3,))
        bad = FitScope((0, 1), (0, 1), subject="clock", cutoff_ms=cutoff)
        with self.assertRaisesRegex(ContractError, "Unresolved or future"):
            assert_scope(data, bad)
        with self.assertRaises(ContractError):
            assert_day_split(data, replace(day, history=(0, 1)))

    def test_warmup_partial_day_and_midnight_not_4am(self):
        rows = [row("clock", "2025-01-01T23:50Z"), row("clock", "2025-01-08T05:30Z"), row("clock", "2025-01-09T05:30Z")]
        data = fixture_dataset(pd.DataFrame(rows), self.protocol)
        day = tuple(day_splits(data, "clock"))[0]
        self.assertEqual(day.cutoff_ms, int(pd.Timestamp("2025-01-08T05:00Z").value // 1_000_000))
        self.assertEqual(day.test, (1,))
        with self.assertRaisesRegex(ContractError, "midnight"):
            assert_day_split(data, replace(day, cutoff_ms=day.cutoff_ms + 4 * 3600000))

    def test_dst_days_are_23_and_25_hours(self):
        for first, test, hours in [("2025-03-02T17:00Z", "2025-03-09T07:30Z", 23), ("2025-10-26T17:00Z", "2025-11-02T06:30Z", 25)]:
            with self.subTest(hours=hours):
                data = fixture_dataset(pd.DataFrame([row("dst", first), row("dst", test)]), self.protocol)
                day = tuple(day_splits(data, "dst"))[0]
                self.assertEqual((day.end_ms - day.cutoff_ms) / 3600000, hours)

    def test_timezone_change_keeps_reference_and_uses_current_predictor_clock(self):
        rows = [row("travel", "2025-03-02T17:00Z"), row("travel", "2025-03-09T07:30Z", zone="America/Los_Angeles"), row("travel", "2025-03-10T07:30Z", zone="America/Los_Angeles")]
        data = fixture_dataset(pd.DataFrame(rows), self.protocol)
        day = tuple(day_splits(data, "travel"))[0]
        self.assertEqual(day.reference_timezone, "America/New_York")
        self.assertIn(1, day.test)
        x = data.features((1,))
        self.assertAlmostEqual(x["hour_sin"].iloc[0], np.sin(2 * np.pi * 23 / 24))
        with self.assertRaisesRegex(ContractError, "first-observed timezone"):
            assert_day_split(data, replace(day, reference_timezone="America/Los_Angeles"))

    def test_dropping_daily_evaluation_rows_or_reusing_state_fails(self):
        population, outer = self.population(self.data)
        subject = next(iter(outer.forbidden_groups))
        day = tuple(day_splits(self.data, subject))[0]
        with self.assertRaises(ContractError):
            assert_day_split(self.data, replace(day, test=()))
        state = fit_personal_state(self.data, day, population)
        with self.assertRaisesRegex(ContractError, "different history/day"):
            predict_personal_day(self.data, day, population, replace(state, cutoff_ms=state.cutoff_ms + 1))

    def test_matching_and_single_class_metrics(self):
        good = MatchedPredictions((0, 1), {"a": [0.1, 0.2], "b": [0.3, 0.4]})
        good.validate((0, 1), ["a", "b"])
        for bad in [replace(good, rows=(1, 0)), replace(good, values={"a": [0.1], "b": [0.3, 0.4]})]:
            with self.assertRaises(ContractError):
                bad.validate((0, 1), ["a", "b"])
        report = metric_summary([0, 0, 0], [0.1, 0.2, 0.3], ["a", "b", "b"], FittedCutoff(0.9, ()))
        self.assertEqual((report["rows"], report["AP"], report["ROC_AUC"]), (3, 0, None))
        self.assertEqual((report["decisions"]["precision"], report["decisions"]["status"]), (0, "zero_alert"))
        self.assertIsNotNone(report["balanced_Brier"])

    def test_participant_weights_preserve_bootstrap_multiplicity(self):
        groups = ["a", "a", "b", "b", "b"]
        normal = participant_weights(groups)
        self.assertAlmostEqual(normal[:2].sum(), 1)
        self.assertAlmostEqual(normal[2:].sum(), 1)
        sampled = participant_weights(groups, {"a": 2, "b": 1})
        self.assertAlmostEqual(sampled[:2].sum(), 2)
        self.assertAlmostEqual(sampled[2:].sum(), 1)

    def test_private_output_guard_resolves_traversal(self):
        with self.assertRaisesRegex(ContractError, "Private output"):
            write_private_json(HOME / "build/should-not-exist.json", {"private": True})
        with self.assertRaises(ContractError):
            private_path(HOME / "run/../build/private.json")
        target = CONTRACT_HOME / "run/.synthetic-manifest-test.json"
        self.assertFalse(target.exists())
        try:
            write_private_json(target, {"synthetic": True})
            self.assertTrue(target.is_file())
        finally:
            target.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
