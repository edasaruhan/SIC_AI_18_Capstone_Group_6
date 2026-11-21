"""Bounded inner-only selection, with no access to outer test labels/scores."""

from dataclasses import dataclass

import numpy as np

from .data_contract import ContractError
from .evaluation_contract import (CandidateFitError, CrossFitScores, PopulationPredictor, apply_calibration, assert_scores, combine_scores, fit_calibration, fit_cutoff, heldout_scores, identity_map, metric_summary)
from .models import CandidateFactory, FitCache
from .metrics import report_metrics
from .splits import assert_group_split, inner_splits, calibration_splits


@dataclass(frozen=True)
class Procedure:
    candidate_id: str
    population: PopulationPredictor
    cutoff: object
    validation_scores: CrossFitScores


@dataclass(frozen=True)
class SelectionResult:
    outer: object
    procedures: dict
    candidate_scores: dict
    public: dict
    fit_jobs: tuple


def _scores(data, scope, folds, candidate, cache):
    parts = [heldout_scores(data, cache.get(s.fit_scope(), candidate), s.test) for s in folds]
    result = combine_scores(data, parts)
    assert_scores(data, result, scope)
    return result


def _summary(data, rows, values, cutoff=None):
    return metric_summary(data.labels(rows), values, data.groups(rows), cutoff)


def select_outer(data, outer, cache=None, progress=None):
    assert_group_split(data, outer)
    factory = CandidateFactory(data.protocol)
    cache = cache or FitCache(data, factory)
    if cache.data is not data:
        raise ContractError("A fit cache cannot cross datasets.")
    inner = inner_splits(data, outer)
    scope = outer.fit_scope()
    cfg = data.protocol.config
    tolerance = cfg["selection"]["AP_tie_tolerance_absolute"]
    all_scores, traces, best, best_ap = {}, [], None, -np.inf
    anchors = {c.id for c in factory.anchors.values()}
    for index, candidate in enumerate(factory.candidates):
        try:
            scores = _scores(data, scope, inner, candidate, cache)
        except CandidateFitError as error:
            traces.append({"candidate": factory.describe(candidate), "status": "invalid", "error": str(error)})
            if candidate.id in anchors:
                raise CandidateFitError("A fixed anchor failed; selection aborted.", error.warning_records, error.attempts) from None
            continue
        diagnostics = _summary(data, scores.rows, scores.values)
        all_scores[candidate.id] = scores
        traces.append({"candidate": factory.describe(candidate), "status": "valid", "inner_selection_diagnostic": diagnostics})
        if diagnostics["AP"] > best_ap + tolerance:
            best, best_ap = candidate, diagnostics["AP"]
        if progress and (index + 1) % 8 == 0:
            progress(f"outer {outer.fold + 1}: {index + 1}/32 structural candidates checked")
    if best is None:
        raise CandidateFitError("No valid frozen candidate remains.")
    if not anchors.issubset(all_scores):
        raise CandidateFitError("A required fixed anchor is missing.")

    lr, rf = factory.anchors["LR"], factory.anchors["RF"]
    lr_ap = _summary(data, scope.rows, all_scores[lr.id].values)["AP"]
    rf_ap = _summary(data, scope.rows, all_scores[rf.id].values)["AP"]
    fixed_choice = rf if rf_ap > lr_ap + tolerance else lr
    raw_selected = all_scores[best.id]
    identity_brier = _summary(data, scope.rows, raw_selected.values)["balanced_Brier"]
    mapped_parts, calibration_trace = [], []
    sigmoid_eligible = True
    for split in inner:
        try:
            calibration_scores = _scores(data, split.fit_scope(), calibration_splits(data, outer, split), best, cache)
        except CandidateFitError as error:
            # These are required fits of the selected structural candidate.
            raise CandidateFitError("Selected candidate failed calibration-score generation; abort without reselecting.", error.warning_records, error.attempts) from None
        calibration = fit_calibration(data, calibration_scores, split.fit_scope(), split.test)
        calibration_trace.append({"inner_fold": split.fold, "status": calibration.status})
        if calibration.kind != "sigmoid" or calibration.status != "ok":
            sigmoid_eligible = False
        raw_part = raw_selected.subset(split.test)
        mapped_parts.append(apply_calibration(data, raw_part, calibration))
    mapped = combine_scores(data, mapped_parts)
    assert_scores(data, mapped, scope)
    sigmoid_brier = _summary(data, scope.rows, mapped.values)["balanced_Brier"] if sigmoid_eligible else None
    requested_sigmoid = sigmoid_eligible and identity_brier - sigmoid_brier > cfg["calibration"]["improvement_tolerance"]
    if requested_sigmoid:
        final_map = fit_calibration(data, raw_selected, scope)
        effective_sigmoid = final_map.kind == "sigmoid" and final_map.status == "ok"
    else:
        final_map = identity_map(scope, "identity_not_improved" if sigmoid_eligible else "identity_ineligible")
        effective_sigmoid = False
    # A final sigmoid failure must also restore the identity-validation cutoff.
    validation = mapped if effective_sigmoid else raw_selected
    procedures = {}
    for name, candidate in [("fixed_LR", lr), ("fixed_RF", rf)]:
        raw = all_scores[candidate.id]
        model = cache.get(scope, candidate)
        population = PopulationPredictor(model, identity_map(scope), scope)
        population.validate(data)
        procedures[name] = Procedure(candidate.id, population, fit_cutoff(data, raw, scope), raw)
    selected_population = PopulationPredictor(cache.get(scope, best), final_map, scope)
    selected_population.validate(data)
    procedures["refined_selector"] = Procedure(best.id, selected_population, fit_cutoff(data, validation, scope), validation)
    procedures["fixed_baseline_selector"] = procedures["fixed_LR"] if fixed_choice.family == "LR" else procedures["fixed_RF"]
    stage_diagnostics = {}
    for name, procedure in procedures.items():
        stage_diagnostics[name] = {
            "training_resubstitution_optimistic": report_metrics(data.labels(scope.rows), procedure.population.predict(data, scope.rows), data.groups(scope.rows), procedure.cutoff.flags(procedure.population.predict(data, scope.rows))),
            "inner_validation_selection_diagnostic": report_metrics(data.labels(scope.rows), procedure.validation_scores.values, data.groups(scope.rows), procedure.cutoff.flags(procedure.validation_scores.values)),
        }
    public = {
        "outer_fold": outer.fold,
        "training_rows": len(scope.rows),
        "training_people": len(set(data.groups(scope.rows))),
        "outer_people_excluded_from_all_selection": len(outer.forbidden_groups),
        "candidates_declared": len(factory.candidates),
        "valid_candidates": len(all_scores),
        "selected_refined": factory.describe(best),
        "selected_fixed_baseline": factory.describe(fixed_choice),
        "calibration": {"identity_validation_Brier": identity_brier, "sigmoid_validation_Brier": sigmoid_brier, "eligible": sigmoid_eligible, "requested_sigmoid": bool(requested_sigmoid), "effective_map": final_map.kind, "final_status": final_map.status, "inner_statuses": calibration_trace},
        "candidate_trace": traces,
        "stage_diagnostics": stage_diagnostics,
        "fit_counts": cache.summary(),
        "outer_predictions_created": False,
        "interpretation": "Training/inner-selection diagnostics only; no outer-test performance or improvement claim.",
    }
    return SelectionResult(outer, procedures, all_scores, public, tuple(cache.jobs))
