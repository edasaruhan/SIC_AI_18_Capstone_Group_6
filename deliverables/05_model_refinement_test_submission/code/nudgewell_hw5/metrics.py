"""Aggregate metrics and paired participant uncertainty from saved predictions."""

from collections import Counter

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from .data_contract import ContractError
from .evaluation_contract import participant_weights, probabilities


def _arrays(y, p, groups):
    y, p, groups = np.asarray(y, dtype=int), probabilities(p), np.asarray(groups, dtype=str)
    if y.ndim != 1 or groups.ndim != 1 or len(y) != len(p) or len(groups) != len(y) or not np.isin(y, [0, 1]).all():
        raise ContractError("Metric arrays have mismatched rows or invalid labels.")
    return y, p, groups


def balanced_ap(y, p, weights):
    if not len(y) or weights.sum() == 0:
        return None
    return float(average_precision_score(y, p, sample_weight=weights)) if np.dot(weights, y) else 0.0


def decisions(y, flags):
    y, flags = np.asarray(y), np.asarray(flags, dtype=bool)
    if y.ndim != 1 or flags.ndim != 1 or len(y) != len(flags) or not np.isin(y, [0, 1]).all():
        raise ContractError("Decision rows do not match.")
    tp, fp = int((flags & (y == 1)).sum()), int((flags & (y == 0)).sum())
    return {"tp": tp, "fp": fp, "fn": int((~flags & (y == 1)).sum()), "tn": int((~flags & (y == 0)).sum()), "precision": tp / (tp + fp) if tp + fp else 0.0, "recall": tp / int(y.sum()) if y.sum() else 0.0, "actual_alert_share": float(flags.mean()) if len(flags) else None, "status": "empty" if not len(y) else "zero_alert" if not flags.any() else "ok"}


def _within(y, p, units):
    aucs, aps = [], []
    for unit in sorted(set(units)):
        mask = units == unit
        if len(np.unique(y[mask])) == 2:
            aucs.append(float(roc_auc_score(y[mask], p[mask])))
            aps.append(float(average_precision_score(y[mask], p[mask])))
    return {"eligible_units": len(aucs), "total_units": len(set(units)), "mean_ROC_AUC": float(np.mean(aucs)) if aucs else None, "mean_AP": float(np.mean(aps)) if aps else None}


def report_metrics(y, p, groups, flags=None, day_units=None):
    y, p, groups = _arrays(y, p, groups)
    if not len(y):
        return {"rows": 0, "people": 0, "status": "empty"}
    w = participant_weights(groups)
    clipped = np.clip(p, 1e-6, 1 - 1e-6)
    log_loss = -(y * np.log(clipped) + (1 - y) * np.log1p(-clipped))
    result = {
        "rows": len(y), "people": len(set(groups)), "positives": int(y.sum()),
        "prevalence": float(y.mean()), "status": "no_positive" if not y.sum() else "ok",
        "pooled_AP": float(average_precision_score(y, p)) if y.sum() else 0.0,
        "pooled_ROC_AUC": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        "participant_balanced_AP": balanced_ap(y, p, w),
        "pooled_Brier": float(np.mean((y - p) ** 2)),
        "participant_balanced_Brier": float(np.average((y - p) ** 2, weights=w)),
        "pooled_log_loss": float(log_loss.mean()),
        "participant_balanced_log_loss": float(np.average(log_loss, weights=w)),
        "within_person": _within(y, p, groups),
    }
    edges = np.linspace(0, 1, 11)
    bins = np.minimum(np.searchsorted(edges, p, side="right") - 1, 9)
    result["reliability"] = []
    for i in range(10):
        take = bins == i
        result["reliability"].append({"left": float(edges[i]), "right": float(edges[i + 1]), "rows": int(take.sum()), "positives": int(y[take].sum()), "weight": float(w[take].sum()), "mean_probability": float(np.average(p[take], weights=w[take])) if take.any() else None, "observed_rate": float(np.average(y[take], weights=w[take])) if take.any() else None})
    if flags is not None:
        result["decisions"] = decisions(y, flags)
    if day_units is not None:
        units = np.asarray(day_units, dtype=str)
        if units.ndim != 1 or len(units) != len(y):
            raise ContractError("Person-day metric rows do not match.")
        result["within_person_day"] = _within(y, p, units)
        eligible_people = set()
        for unit in set(units):
            mask = units == unit
            if len(np.unique(y[mask])) == 2:
                eligible_people.update(groups[mask])
        result["within_person_day"]["eligible_people"] = len(eligible_people)
    # Fixed grids avoid publishing individual scores or their exact thresholds.
    result["decision_curve_grid"] = [{"threshold": float(t), **decisions(y, p >= t)} for t in np.linspace(0, 1, 101)]
    return result


def paired_difference(y, first, second, groups, protocol, metric):
    y, first, groups = _arrays(y, first, groups)
    _, second, _ = _arrays(y, second, groups)
    if metric not in ["participant_balanced_AP", "participant_balanced_Brier"]:
        raise ContractError("Unfrozen primary/secondary contrast metric.")
    cfg = protocol.config["uncertainty"]
    if not len(y):
        return {"point_difference": None, "interval": None, "finite_replicates": 0, "undefined_replicates": cfg["reps"]}

    def difference(weights):
        if metric == "participant_balanced_AP":
            return balanced_ap(y, first, weights) - balanced_ap(y, second, weights)
        return float(np.average((y - first) ** 2, weights=weights) - np.average((y - second) ** 2, weights=weights))

    point = difference(participant_weights(groups))
    people = np.array(sorted(set(groups)))
    rng = np.random.default_rng(cfg["seed"])
    values = []
    for _ in range(cfg["reps"]):
        multiplicities = Counter(rng.choice(people, len(people), replace=True))
        values.append(difference(participant_weights(groups, multiplicities)))
    finite = np.asarray(values)[np.isfinite(values)]
    return {"metric": metric, "point_difference": point, "interval": list(map(float, np.percentile(finite, [2.5, 97.5]))) if len(finite) else None, "finite_replicates": len(finite), "undefined_replicates": cfg["reps"] - len(finite), "reps": cfg["reps"], "seed": cfg["seed"], "paired": True, "unit": "participant", "conditional_on_stored_predictions": True}
