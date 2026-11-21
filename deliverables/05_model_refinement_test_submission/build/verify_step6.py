"""Reconcile frozen Step 6 aggregates with local predictions, without refitting."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from scipy.special import expit, logit
from sklearn.metrics import average_precision_score, roc_auc_score

BUILD = Path(__file__).resolve().parent
sys.path.insert(0, str(BUILD.parent / "code"))
from nudgewell_hw5.data_contract import load_dataset, load_protocol, sha256
from nudgewell_hw5.runner import _run_root, code_fingerprint


def require(condition, description):
    if not condition:
        raise ValueError(description)


def close(actual, expected):
    return np.allclose(actual, expected, rtol=1e-10, atol=1e-12)


def validate_metrics(frame, method, summary, daily=False):
    y, p = frame["label"].to_numpy(), frame[method].to_numpy()
    w = 1 / frame.groupby("participant")["label"].transform("size").to_numpy()
    clipped = np.clip(p, 1e-6, 1 - 1e-6)
    squared = (y - p) ** 2
    log_loss = -np.where(y, np.log(clipped), np.log1p(-clipped))
    expected = {
        "rows": len(frame),
        "people": frame["participant"].nunique(),
        "positives": y.sum(),
        "pooled_AP": average_precision_score(y, p),
        "pooled_ROC_AUC": roc_auc_score(y, p),
        "participant_balanced_AP": average_precision_score(y, p, sample_weight=w),
        "pooled_Brier": squared.mean(),
        "participant_balanced_Brier": np.average(squared, weights=w),
        "pooled_log_loss": log_loss.mean(),
        "participant_balanced_log_loss": np.average(log_loss, weights=w),
    }
    require(all(close(summary[key], value) for key, value in expected.items()),
            f"Metric reconciliation failed for {method}")
    for column, key in [("participant", "within_person")] + (
        [("person_day", "within_person_day")] if daily else []
    ):
        eligible = [g for _, g in frame.groupby(column) if g["label"].nunique() == 2]
        result = summary[key]
        require(result["eligible_units"] == len(eligible) and
                result["total_units"] == frame[column].nunique(), f"Coverage mismatch for {method} / {column}")
        require(close(result["mean_ROC_AUC"], np.mean([
            roc_auc_score(g["label"], g[method]) for g in eligible
        ])), f"Within-group AUC mismatch for {method} / {column}")
        require(close(result["mean_AP"], np.mean([
            average_precision_score(g["label"], g[method]) for g in eligible
        ])), f"Within-group AP mismatch for {method} / {column}")
        if daily and column == "person_day":
            people = {g["participant"].iloc[0] for g in eligible}
            require(len(people) == result["eligible_people"], f"Eligible AUC people mismatch for {method}")
    require(sum(b["rows"] for b in summary["reliability"]) == len(frame) and
            sum(b["positives"] for b in summary["reliability"]) == int(y.sum()) and
            close(sum(b["weight"] for b in summary["reliability"]), frame["participant"].nunique()),
            f"Reliability coverage mismatch for {method}")
    if f"{method}_flag" in frame:
        flags = frame[f"{method}_flag"].to_numpy(dtype=bool)
        tp, fp = int(y[flags].sum()), int(flags.sum() - y[flags].sum())
        require(all(close(summary["decisions"][key], value) for key, value in {
            "tp": tp, "fp": fp, "fn": y.sum() - tp, "tn": len(y) - y.sum() - fp,
            "precision": tp / max(1, tp + fp), "recall": tp / max(1, y.sum()),
            "actual_alert_share": flags.mean(),
        }.items()), f"Confusion counts or decision rates mismatch for {method}")


def reproduce_intervals(new, daily, result, protocol):
    cfg = protocol.config["uncertainty"]
    subjects, row_group, counts = np.unique(new["participant"], return_inverse=True, return_counts=True)
    labels = new["label"].to_numpy()
    a = new["refined_selector"].to_numpy()
    b = new["fixed_baseline_selector"].to_numpy()
    rng = np.random.default_rng(cfg["seed"])
    ap_diff = []
    for _ in range(cfg["reps"]):
        multiplicity = np.bincount(rng.integers(len(subjects), size=len(subjects)), minlength=len(subjects))
        weights = (multiplicity / counts)[row_group]
        ap_diff.append(average_precision_score(labels, a, sample_weight=weights) -
                       average_precision_score(labels, b, sample_weight=weights)
                       if weights @ labels else 0.0)
    ordered = daily.assign(delta=(daily["label"] - daily["personal_rate"]) ** 2 -
                                 (daily["label"] - daily["global_plus_daily_personal_offset"]) ** 2)
    per_subject = ordered.groupby("participant", sort=True)["delta"].mean().to_numpy()
    rng = np.random.default_rng(cfg["seed"])
    draw = rng.integers(len(per_subject), size=(cfg["reps"], len(per_subject)))
    brier_diff = per_subject[draw].mean(axis=1)
    for key, vals in [("primary_contrast", ap_diff), ("secondary_prespecified_contrast", brier_diff)]:
        require(close(np.percentile(vals, [2.5, 97.5]), result[key]["interval"]), f"Interval mismatch for {key}")
        require(result[key]["finite_replicates"] == cfg["reps"] and result[key]["undefined_replicates"] == 0,
                f"Bootstrap coverage mismatch for {key}")


def verify(csv, run_id):
    root = _run_root(run_id)
    protocol = load_protocol()
    data = load_dataset(csv, protocol)
    manifest = json.loads((root / "run.json").read_text(encoding="utf-8"))
    report = BUILD / "results" / f"{run_id}_evaluation.json"
    require(manifest["status"] == "evaluation_complete" and manifest["outer_results_opened"],
            "The real evaluation is not complete")
    require(not manifest["fixture"] and manifest["protocol_sha256"] == protocol.digest
            and manifest["code_sha256"] == code_fingerprint(), "Evaluation source or protocol mismatch")
    require(sha256(report) == manifest["evaluation_public_sha256"], "Evaluation aggregate fingerprint mismatch")
    result = json.loads(report.read_text(encoding="utf-8"))
    new_path, daily_path = (root / f"predictions_{name}_user.csv" for name in ("new", "known"))
    new = pd.read_csv(new_path, dtype={"participant": str}, float_precision="round_trip")
    daily = pd.read_csv(daily_path, dtype={"participant": str}, float_precision="round_trip")
    private_meta = data.frame().reset_index(drop=True)
    require(np.array_equal(new["row_position"], np.arange(len(data))) and tuple(new["row_key"]) == data.keys,
            "Outer prediction rows do not match the complete release")
    for frame in (new, daily):
        rows = frame["row_position"].to_numpy()
        require(frame["row_position"].is_unique and np.array_equal(data.labels()[rows], frame["label"])
                and np.array_equal(data.groups()[rows], frame["participant"]), "Prediction row alignment failed")
    preflight = json.loads((BUILD / "protocol_preflight.json").read_text(encoding="utf-8"))
    coverage = preflight["known_user_boundary_feasibility"]
    require((len(daily), daily["participant"].nunique(), daily["person_day"].nunique())
            == (coverage["rows"], coverage["people"], coverage["observed_days"]), "Daily coverage drifted")

    require({entry["fold"] for entry in manifest["folds"]} == set(range(5)), "Missing frozen fold")
    for entry in manifest["folds"]:
        artifact = root / entry["file"]
        require(sha256(artifact) == entry["sha256"], "Selected procedure fingerprint mismatch")
        saved = joblib.load(artifact)
        test = new["outer_fold"].eq(entry["fold"])
        require(tuple(new.loc[test, "row_position"]) == saved.outer.test, "Outer fold row mismatch")
        require(not (set(new.loc[test, "participant"]) & set(data.groups(saved.outer.train))), "Outer person in training")
        for method, procedure in saved.procedures.items():
            require(np.array_equal(new.loc[test, f"{method}_flag"], new.loc[test, method] >= procedure.cutoff.value),
                    f"Outer decisions differ from the frozen cutoff for {method}")
        eval_daily = daily["row_position"].isin(saved.outer.test)
        cutoff = saved.procedures["refined_selector"].cutoff.value
        for method in protocol.config["known_user"]["variants"]:
            require(np.array_equal(daily.loc[eval_daily, f"{method}_flag"], daily.loc[eval_daily, method] >= cutoff),
                    f"Daily decisions differ from the frozen cutoff for {method}")
        peer_labels = data.labels(saved.outer.train)
        require(close(new.loc[test, "population_prior"], (peer_labels.sum() + 1) / (len(peer_labels) + 2)),
                "Population prior differs from the excluded-fold archive")

    require(close(daily["global"], new["refined_selector"].to_numpy()[daily["row_position"]]),
            "Daily global predictions differ from frozen outer predictions")
    positions_by_person = {str(k): v for k, v in private_meta.groupby("pid").indices.items()}
    frames = dict(tuple(daily.groupby("person_day")))
    states_path = root / "personal_states.json"
    states = json.loads(states_path.read_text(encoding="utf-8"))
    require(len(frames) == len(states), "Daily state count differs")
    for state in states:
        subject, cutoff = state["subject"], state["cutoff_ms"]
        part = private_meta.iloc[positions_by_person[subject]]
        target = frames.pop(f"{subject}|{cutoff}")
        history = part[(part["esm_time"] < cutoff) & (part["lock_time"] < cutoff)]
        require(list(history.index) == state["history_rows"], "History includes late locks or loses resolved rows")
        require(not (set(history["session_id_combined"]) &
                     set(private_meta.iloc[target["row_position"]]["session_id_combined"])), "Session crosses history and target")
        peer_prior = new["population_prior"].iloc[target["row_position"].iloc[0]]
        own_positives = ((history["answer"] <= 5) & (history["remaining_minutes"] > 5)).sum()
        expected_rate = (own_positives + 10 * peer_prior) / (len(history) + 10)
        require(close(peer_prior, state["peer_prior"]) and close(expected_rate, target["personal_rate"]),
                "Smoothed daily personal rate differs from permitted history")
        global_p = target["global"].to_numpy()
        expected_offset = (expit(logit(np.clip(global_p, 1e-6, 1 - 1e-6)) + state["delta"])
                           if state["delta"] else global_p)
        require(close(expected_offset, target["global_plus_daily_personal_offset"]), "Daily offset score mismatch")
    require(not frames and dict(Counter(s["status"] for s in states)) ==
            result["known_user_coverage"]["personal_state_status_counts"], "Daily status mismatch")
    for method, row in result["new_user"].items():
        if method != "fixed_rule":
            validate_metrics(new, method, row)
    rule = (private_meta["esm_hour"].between(0, 5) |
            private_meta["Category_L1"].eq("Social") |
            ((private_meta["esm_time"] - private_meta["unlock_time"]) > 600_000))
    expected_rule = pd.crosstab(new["label"], rule)
    tp, fp, fn, tn = (int(expected_rule.loc[y, f]) for y, f in [(1, True), (0, True), (1, False), (0, False)])
    require(all(close(result["new_user"]["fixed_rule"][key], value) for key, value in {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": tp / (tp + fp),
        "recall": tp / (tp + fn), "actual_alert_share": rule.mean(),
    }.items()), "Fixed rule operating metrics do not reconcile")
    for method, row in result["known_user"].items():
        validate_metrics(daily, method, row, daily=True)
    reproduce_intervals(new, daily, result, protocol)
    require(close(result["primary_contrast"]["point_difference"],
                  result["new_user"]["refined_selector"]["participant_balanced_AP"]
                  - result["new_user"]["fixed_baseline_selector"]["participant_balanced_AP"]),
            "Primary contrast sign or magnitude differs")
    require(close(result["secondary_prespecified_contrast"]["point_difference"],
                  result["known_user"]["personal_rate"]["participant_balanced_Brier"]
                  - result["known_user"]["global_plus_daily_personal_offset"]["participant_balanced_Brier"]),
            "Secondary contrast sign or magnitude differs")
    return {
        "run_id": run_id,
        "protocol_sha256": protocol.digest,
        "evaluation_sha256": sha256(report),
        "private_artifact_sha256": {p.name: sha256(p) for p in (new_path, daily_path, states_path)},
        "rows_checked": {"new_user": len(new), "known_user": len(daily)},
        "participant_days_checked": len(states),
        "paired_replicates_reproduced_per_contrast": protocol.config["uncertainty"]["reps"],
        "verified": [
            "Frozen protocol, source and artifact fingerprints",
            "Complete outer coverage and matched prediction rows",
            "Outer and daily decisions at saved validation cutoffs",
            "Excluded-fold priors, resolved own history and daily offset application",
            "Probability, discrimination, coverage and operating metrics",
            "Prespecified paired bootstrap intervals and contrast signs",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    evidence = verify(args.csv, args.run_id)
    output = BUILD / "results" / f"{args.run_id}_verification.json"
    output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {evidence['rows_checked']} and {evidence['participant_days_checked']} daily states")
