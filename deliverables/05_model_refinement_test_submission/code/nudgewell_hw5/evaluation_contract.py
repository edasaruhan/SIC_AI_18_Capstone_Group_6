"""Scoped fitting, cross-fit provenance and immutable decision boundaries.

These primitives are shared with the future experiment runner. Selection/search
and real-data performance evaluation do not run from this module.
"""

from collections import Counter
from dataclasses import dataclass
import warnings

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data_contract import ContractError, row_positions, validate_feature_matrix
from .splits import FitScope, assert_scope, assert_group_split, assert_day_split


class CandidateFitError(RuntimeError):
    def __init__(self, message, warning_records=(), attempts=1):
        super().__init__(message)
        self.warning_records = tuple(warning_records)
        self.attempts = attempts


def probabilities(scores):
    a = np.asarray(scores, dtype=float)
    if a.ndim != 1 or not np.isfinite(a).all() or ((a < 0) | (a > 1)).any():
        raise ContractError("Probabilities must be a finite one-dimensional [0,1] array.")
    return a


def participant_weights(groups, multiplicities=None):
    groups = np.asarray(groups, dtype=str)
    counts = Counter(groups)
    if multiplicities is None:
        multiplicities = {g: 1 for g in counts}
    if set(multiplicities) - set(counts) or any(not isinstance(v, (int, np.integer)) or v < 0 for v in multiplicities.values()):
        raise ContractError("Invalid participant bootstrap multiplicities.")
    return np.array([multiplicities.get(g, 0) / counts[g] for g in groups], dtype=float)


@dataclass(frozen=True)
class FittedBase:
    _pipeline: object
    constant: float | None
    training_rows: tuple
    forbidden_groups: frozenset
    pack: str
    status: str
    warning_records: tuple

    def predict(self, data, rows):
        rows = row_positions(len(data), rows)
        x = data.features(rows, self.pack)
        validate_feature_matrix(x, data.protocol, self.pack)
        if self.constant is not None:
            return np.full(len(rows), self.constant, dtype=float)
        if not rows:
            return np.empty(0, dtype=float)
        return probabilities(self._pipeline.predict_proba(x)[:, 1])


def fit_base(data, scope, estimator, family="LR", pack="main_context"):
    assert_scope(data, scope)
    p = data.protocol.config
    if family not in ("LR", "RF") or pack not in p["features"]["packs"]:
        raise ContractError("Unknown estimator family or feature pack.")
    y = data.labels(scope.rows)
    if len(np.unique(y)) < 2:
        constant = float((y.sum() + 1) / (len(y) + 2))
        return FittedBase(None, constant, scope.rows, scope.forbidden_groups, pack, "empty_training" if not len(y) else "one_class_training", ())
    x = data.features(scope.rows, pack)
    validate_feature_matrix(x, data.protocol, pack)
    steps = [("imputer", SimpleImputer(strategy="median", keep_empty_features=True))]
    if family == "LR":
        steps.append(("scaler", StandardScaler()))
    steps.append(("classifier", clone(estimator)))
    pipeline = Pipeline(steps)
    records = []
    retried = False
    for attempt in range(2):
        caught = []
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                pipeline.fit(x, y)
        except Exception as error:
            records.extend((w.category.__name__, str(w.message)) for w in caught)
            raise CandidateFitError("Base fit failed: " + type(error).__name__, records, attempt + 1) from None
        records.extend((w.category.__name__, str(w.message)) for w in caught)
        nonconvergent = any(issubclass(w.category, ConvergenceWarning) for w in caught)
        if not nonconvergent:
            return FittedBase(pipeline, None, scope.rows, scope.forbidden_groups, pack, "retried_convergence" if retried else "ok", tuple(records))
        if family != "LR" or attempt or "max_iter" not in pipeline["classifier"].get_params():
            break
        pipeline.set_params(classifier__max_iter=10000)
        retried = True
    raise CandidateFitError("Base fit remained nonconvergent after the declared retry.", records, attempt + 1)


@dataclass(frozen=True)
class PredictionBlock:
    target_rows: tuple
    training_rows: tuple


@dataclass(frozen=True)
class CrossFitScores:
    rows: tuple
    values: tuple
    blocks: tuple

    def subset(self, rows):
        wanted = set(rows)
        if not wanted.issubset(self.rows):
            raise ContractError("Requested scores were not cross-fitted.")
        mapping = dict(zip(self.rows, self.values))
        selected = tuple(r for r in self.rows if r in wanted)
        blocks = tuple(PredictionBlock(tuple(r for r in b.target_rows if r in wanted), b.training_rows) for b in self.blocks if wanted & set(b.target_rows))
        return CrossFitScores(selected, tuple(mapping[r] for r in selected), blocks)


def heldout_scores(data, model, rows):
    rows = row_positions(len(data), rows)
    if set(data.groups(rows)) & set(data.groups(model.training_rows)):
        raise ContractError("Held-out scores include a fitting participant.")
    return CrossFitScores(rows, tuple(map(float, model.predict(data, rows))), (PredictionBlock(rows, model.training_rows),))


def apply_calibration(data, scores, calibration):
    """Carry calibration dependencies into scores used for cutoff selection."""
    dependencies = set(calibration.fitting_rows) | set(calibration.dependency_rows)
    if set(data.groups(dependencies)) & set(data.groups(scores.rows)):
        raise ContractError("Calibrator fitting and score-assessment participants overlap.")
    blocks = tuple(PredictionBlock(b.target_rows, tuple(sorted(set(b.training_rows) | dependencies))) for b in scores.blocks)
    return CrossFitScores(scores.rows, tuple(map(float, calibration.transform(scores.values))), blocks)


def combine_scores(data, parts):
    mapping, blocks = {}, []
    for part in parts:
        if set(mapping) & set(part.rows):
            raise ContractError("Duplicate held-out rows when combining scores.")
        if len(part.rows) != len(probabilities(part.values)):
            raise ContractError("Score values do not match their rows.")
        mapping.update(zip(part.rows, part.values))
        blocks.extend(part.blocks)
    rows = row_positions(len(data), mapping)
    return CrossFitScores(rows, tuple(mapping[r] for r in rows), tuple(blocks))


def assert_scores(data, scores, scope, assessment_rows=()):
    assert_scope(data, scope)
    if scores.rows != scope.rows or len(scores.values) != len(scores.rows):
        raise ContractError("Cross-fitted scores do not match fitting rows.")
    probabilities(scores.values)
    assessment = row_positions(len(data), assessment_rows)
    assessment_groups = set(data.groups(assessment))
    if set(scope.rows) & set(assessment) or set(data.groups(scope.rows)) & assessment_groups:
        raise ContractError("Calibration fitting and assessment participants overlap.")
    covered = []
    allowed = set(scope.allowed_rows)
    forbidden = set(scope.forbidden_groups) | assessment_groups
    for block in scores.blocks:
        tr = row_positions(len(data), block.training_rows)
        te = row_positions(len(data), block.target_rows)
        if tr != block.training_rows or te != block.target_rows or not set(te).issubset(scores.rows):
            raise ContractError("Invalid score provenance rows.")
        if not set(tr).issubset(allowed) or set(data.groups(tr)) & forbidden:
            raise ContractError("Indirect forbidden-participant dependency in calibration scores.")
        if set(data.groups(tr)) & set(data.groups(te)):
            raise ContractError("Scores are not participant-held-out.")
        covered.extend(te)
    if sorted(covered) != list(scores.rows):
        raise ContractError("Cross-fitted provenance has duplicate or missing rows.")


def cross_fit(data, scope, folds, estimator_factory, family="LR", pack="main_context"):
    assert_scope(data, scope)
    mapping, blocks = {}, []
    for split in folds:
        assert_group_split(data, split)
        if split.universe != scope.rows or not scope.forbidden_groups.issubset(split.forbidden_groups):
            raise ContractError("Cross-fit split lost its parent fitting boundary.")
        model = fit_base(data, split.fit_scope(), estimator_factory(), family, pack)
        values = model.predict(data, split.test)
        if set(mapping) & set(split.test):
            raise ContractError("Duplicate cross-fit predictions.")
        mapping.update(zip(split.test, map(float, values)))
        blocks.append(PredictionBlock(split.test, model.training_rows))
    if set(mapping) != set(scope.rows):
        raise ContractError("Cross-fitting omitted permitted rows.")
    scores = CrossFitScores(scope.rows, tuple(mapping[r] for r in scope.rows), tuple(blocks))
    assert_scores(data, scores, scope)
    return scores


@dataclass(frozen=True)
class CalibrationMap:
    kind: str
    a: float
    b: float
    status: str
    fitting_rows: tuple
    dependency_rows: tuple
    forbidden_groups: frozenset

    def transform(self, values):
        values = probabilities(values)
        if self.kind == "identity":
            return values.copy()
        return expit(self.a * logit(np.clip(values, 1e-6, 1 - 1e-6)) + self.b)


def identity_map(scope, status="identity"):
    return CalibrationMap("identity", 1.0, 0.0, status, (), (), scope.forbidden_groups)


def fit_calibration(data, scores, scope, assessment_rows=()):
    assert_scores(data, scores, scope, assessment_rows)
    dependencies = set(scope.rows)
    for block in scores.blocks:
        dependencies.update(block.training_rows)

    def fallback(status):
        # A data-dependent fallback still inspected these labels/scores.
        return CalibrationMap("identity", 1.0, 0.0, status, scope.rows, tuple(sorted(dependencies)), scope.forbidden_groups)

    y = data.labels(scope.rows)
    if len(np.unique(y)) < 2:
        return fallback("empty_identity" if not len(y) else "one_class_identity")
    z = logit(np.clip(probabilities(scores.values), 1e-6, 1 - 1e-6))
    w = participant_weights(data.groups(scope.rows))
    w /= w.sum()
    cfg = data.protocol.config["calibration"]["parameters"]

    def objective(v):
        a, b = v
        linear = a * z + b
        residual = expit(linear) - y
        value = np.dot(w, np.logaddexp(0, linear) - y * linear) + 1e-4 * ((a - 1) ** 2 + b**2)
        gradient = np.array([np.dot(w, residual * z) + 2e-4 * (a - 1), np.dot(w, residual) + 2e-4 * b])
        return value, gradient

    try:
        fitted = minimize(objective, cfg["initial"], jac=True, method="L-BFGS-B", bounds=[cfg["a_bounds"], cfg["b_bounds"]], options={k: cfg[k] for k in ("maxiter", "ftol", "gtol")})
    except (ValueError, FloatingPointError):
        return fallback("optimizer_failure_identity")
    if not fitted.success or not np.isfinite(fitted.x).all():
        return fallback("optimizer_failure_identity")
    return CalibrationMap("sigmoid", float(fitted.x[0]), float(fitted.x[1]), "ok", scope.rows, tuple(sorted(dependencies)), scope.forbidden_groups)


@dataclass(frozen=True)
class FittedCutoff:
    value: float
    validation_rows: tuple

    def flags(self, values):
        return probabilities(values) >= self.value


def fit_cutoff(data, scores, scope):
    assert_scores(data, scores, scope)
    if not scores.rows:
        raise ContractError("Cannot fit a cutoff without validation scores.")
    cfg = data.protocol.config["decisions"]
    value = np.quantile(scores.values, cfg["quantile"], method=cfg["quantile_method"])
    return FittedCutoff(float(value), scores.rows)


@dataclass(frozen=True)
class PopulationPredictor:
    model: FittedBase
    calibration: CalibrationMap
    scope: FitScope

    def validate(self, data):
        assert_scope(data, self.scope)
        if self.model.training_rows != self.scope.rows or self.model.forbidden_groups != self.scope.forbidden_groups:
            raise ContractError("Population model differs from the declared archive.")
        if not self.scope.forbidden_groups.issubset(self.calibration.forbidden_groups):
            raise ContractError("Population calibrator lost participant exclusions.")
        dependencies = set(self.calibration.fitting_rows) | set(self.calibration.dependency_rows)
        if not dependencies.issubset(self.scope.rows) or set(data.groups(dependencies)) & set(self.scope.forbidden_groups):
            raise ContractError("Population calibration has an indirect forbidden dependency.")

    def predict(self, data, rows):
        self.validate(data)
        return self.calibration.transform(self.model.predict(data, rows))


@dataclass(frozen=True)
class PersonalState:
    subject: str
    cutoff_ms: int
    history_rows: tuple
    peer_prior: float
    personal_rate: float
    delta: float
    status: str


def fit_personal_state(data, day, population):
    assert_day_split(data, day)
    population.validate(data)
    if day.subject not in population.scope.forbidden_groups:
        raise ContractError("The evaluated person entered the population archive.")
    peer_y = data.labels(population.scope.rows)
    peer_prior = float((peer_y.sum() + 1) / (len(peer_y) + 2))
    y = data.labels(day.history)
    rate = float((y.sum() + 10 * peer_prior) / (len(y) + 10))
    if not len(y):
        return PersonalState(day.subject, day.cutoff_ms, (), peer_prior, rate, 0.0, "empty_history")
    z = logit(np.clip(population.predict(data, day.history), 1e-6, 1 - 1e-6))
    cfg = data.protocol.config["known_user"]["personal_offset"]

    def objective(v):
        delta = v[0]
        linear = z + delta
        return (np.sum(np.logaddexp(0, linear) - y * linear) + delta**2 / 2, np.array([np.sum(expit(linear) - y) + delta]))

    try:
        fitted = minimize(objective, [cfg["initial_delta"]], jac=True, method="L-BFGS-B", bounds=[cfg["delta_bounds"]], options={k: cfg[k] for k in ("maxiter", "ftol", "gtol")})
        success = fitted.success and np.isfinite(fitted.x).all()
    except (ValueError, FloatingPointError):
        success = False
    return PersonalState(day.subject, day.cutoff_ms, day.history, peer_prior, rate, float(fitted.x[0]) if success else 0.0, "ok" if success else "optimizer_failure_global")


@dataclass(frozen=True)
class MatchedPredictions:
    rows: tuple
    values: dict

    def validate(self, expected_rows, names):
        if self.rows != tuple(expected_rows) or set(self.values) != set(names):
            raise ContractError("Comparison methods have mismatched rows or names.")
        for values in self.values.values():
            if len(probabilities(values)) != len(self.rows):
                raise ContractError("Comparison methods have mismatched row counts.")


def predict_personal_day(data, day, population, state):
    assert_day_split(data, day)
    if (state.subject, state.cutoff_ms, state.history_rows) != (day.subject, day.cutoff_ms, day.history):
        raise ContractError("Personal state was fitted for a different history/day.")
    global_p = population.predict(data, day.test)
    shifted = global_p.copy() if state.delta == 0 else expit(logit(np.clip(global_p, 1e-6, 1 - 1e-6)) + state.delta)
    result = MatchedPredictions(day.test, {"global": global_p, "personal_rate": np.full(len(day.test), state.personal_rate), "global_plus_daily_personal_offset": shifted})
    result.validate(day.test, data.protocol.config["known_user"]["variants"])
    return result


def metric_summary(y, values, groups, cutoff=None):
    """Guard-level metrics; AP here is participant-balanced pooled AP."""
    y, values, groups = np.asarray(y), probabilities(values), np.asarray(groups, dtype=str)
    if len(y) != len(values) or len(groups) != len(y) or not np.isin(y, [0, 1]).all():
        raise ContractError("Metric rows or labels do not match.")
    if not len(y):
        return {"rows": 0, "status": "empty", "AP": None, "ROC_AUC": None, "balanced_Brier": None}
    w = participant_weights(groups)
    ap = float(average_precision_score(y, values, sample_weight=w)) if y.sum() else 0.0
    result = {"rows": len(y), "people": len(set(groups)), "status": "no_positive" if not y.sum() else "ok", "AP": ap, "ROC_AUC": float(roc_auc_score(y, values)) if len(np.unique(y)) == 2 else None, "balanced_Brier": float(np.average((y - values) ** 2, weights=w))}
    if cutoff is not None:
        flag = cutoff.flags(values)
        tp, fp = int((flag & (y == 1)).sum()), int((flag & (y == 0)).sum())
        result["decisions"] = {"tp": tp, "fp": fp, "fn": int((~flag & (y == 1)).sum()), "tn": int((~flag & (y == 0)).sum()), "precision": tp / (tp + fp) if tp + fp else 0.0, "recall": tp / int(y.sum()) if y.sum() else 0.0, "actual_alert_share": float(flag.mean()), "status": "zero_alert" if not flag.any() else "ok"}
    return result
