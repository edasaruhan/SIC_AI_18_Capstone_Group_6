"""Reconcile saved HW4 aggregates and audit its old split, without fitting models.

Only aggregate evidence is written. Raw rows, participant identifiers, exact
timestamps, predictions and fitted artifacts are never written by this script.
"""

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
HW4 = ROOT / "deliverables/04_data_preparation_model_exploration"
SOURCE = HW4 / "code/hw4_pipeline.py"
RESULTS = HW4 / "build/results/results_real.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_csv(path):
    raw = pd.read_csv(path, low_memory=False)
    df = raw.drop_duplicates().reset_index(drop=True)
    y = ((df["answer"] <= 5) & (df["remaining_minutes"] > 5)).astype(int)
    train = np.zeros(len(df), dtype=bool)
    local = pd.to_datetime(df["esm_local"].astype(str).str[:19], format="mixed")
    days = {
        "local_midnight": local.dt.date,
        "released_date": df["date"].astype(str).str[:10],
        "released_date_4am": df["date_4am"].astype(str).str[:10],
        "local_4am": (local - pd.Timedelta(hours=4)).dt.date,
        "utc_midnight": pd.to_datetime(df["esm_time"], unit="ms", utc=True).dt.date,
    }
    cuts = {key: 0 for key in days}
    shared_sessions = unresolved_rows = unresolved_people = 0
    for idx in df.groupby("pid").indices.values():
        order = idx[np.argsort(df["esm_time"].values[idx], kind="stable")]
        cut = int(0.7 * len(order))
        tr, te = order[:cut], order[cut:]
        train[tr] = True
        for key, day in days.items():
            cuts[key] += int(day.iloc[tr[-1]] == day.iloc[te[0]])
        shared_sessions += len(
            set(df["session_id_combined"].iloc[tr])
            & set(df["session_id_combined"].iloc[te])
        )
        n = int((df["lock_time"].iloc[tr] >= df["esm_time"].iloc[te].min()).sum())
        unresolved_rows += n
        unresolved_people += int(n > 0)
    anomaly = df["app_total_duration_session"] > df["time_since_unlock"] + 1
    return {
        "rows_released": len(raw),
        "columns": len(raw.columns),
        "rows_unique": len(df),
        "duplicate_rows": len(raw) - len(df),
        "participants": int(df["pid"].nunique()),
        "high_gap_n": int(y.sum()),
        "high_gap_rate": float(y.mean()),
        "global_both_classes_participants": int(
            sum(z.nunique() == 2 for _, z in y.groupby(df["pid"]))
        ),
        "n_test_rows": int((~train).sum()),
        "test_positives": int(y[~train].sum()),
        "test_participants": int(df.loc[~train, "pid"].nunique()),
        "test_both_classes_participants": int(
            sum(z.nunique() == 2 for _, z in y[~train].groupby(df.loc[~train, "pid"]))
        ),
        "same_day_split_participants_by_definition": cuts,
        "shared_boundary_sessions": shared_sessions,
        "training_outcomes_unresolved_at_first_test": unresolved_rows,
        "participants_with_unresolved_training_outcome": unresolved_people,
        "app_duration_exceeds_elapsed": {
            "rows": int(anomaly.sum()),
            "people": int(df.loc[anomaly, "pid"].nunique()),
        },
        "missing": {
            "app_category": int(df["Category_L1"].isna().sum()),
            "app_durations": int(df["app_duration"].isna().sum()),
            "activity": int(df["activity_type"].isna().sum()),
        },
        "esm_local_hour_matches_esm_hour": bool((local.dt.hour == df["esm_hour"]).all()),
        "raw_sha256": sha256(path),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("baseline_evidence.json"))
    args = parser.parse_args()
    saved = json.loads(RESULTS.read_text(encoding="utf-8"))
    audit = audit_csv(args.csv)
    checks = {}
    for key in ("rows_released", "rows_unique", "duplicate_rows", "participants", "high_gap_n", "high_gap_rate", "app_duration_exceeds_elapsed"):
        checks[f"data.{key}"] = audit[key] == saved["data"][key]
    checks["data.missing"] = all(
        value == saved["data"]["missing"][key]
        for key, value in audit["missing"].items()
    )
    checks["feature_count"] = len(saved["features"]) == saved["n_features"] == 49
    checks["personal.n_test_rows"] = audit["n_test_rows"] == saved["personal"]["n_test_rows"]
    checks["personal.test_prevalence"] = math.isclose(
        audit["test_positives"] / audit["n_test_rows"], saved["personal"]["test_prevalence"]
    )
    checks["global.within_n"] = all(
        m["within_n"] == audit["global_both_classes_participants"]
        for m in saved["global"].values()
    )
    checks["personal.within_n"] = all(
        m["within_n"] == audit["test_both_classes_participants"]
        for m in saved["personal"]["approaches"].values()
    )
    for name, row in saved["at_alert_rate"].items():
        checks[f"confusion.{name}"] = (
            sum(row[k] for k in ("tp", "fp", "fn", "tn")) == audit["rows_unique"]
            and row["tp"] + row["fn"] == audit["high_gap_n"]
            and math.isclose(row["precision"], row["tp"] / (row["tp"] + row["fp"]))
            and math.isclose(row["recall"], row["tp"] / (row["tp"] + row["fn"]))
            and math.isclose(row["flagged"], (row["tp"] + row["fp"]) / audit["rows_unique"])
        )
    keys = ("roc_auc", "pr_auc", "brier", "within_roc_auc", "within_pr_auc", "within_n")
    historical = {
        section: {name: {key: row[key] for key in keys} for name, row in models.items()}
        for section, models in (
            ("global", saved["global"]),
            ("personal", saved["personal"]["approaches"]),
        )
    }
    functions = {
        node.name: {"start": node.lineno, "end": node.end_lineno}
        for node in ast.parse(SOURCE.read_text(encoding="utf-8")).body
        if isinstance(node, ast.FunctionDef)
    }
    evidence = {
        "review_date": "2026-11-16",
        "scope": "Saved HW4 result reconciliation and deterministic old-split audit; no model fitting or new model evaluation.",
        "source_sha256": {"hw4_pipeline.py": sha256(SOURCE), "results_real.json": sha256(RESULTS)},
        "source_functions": functions,
        "local_data_audit": audit,
        "historical_metrics_from_saved_json": historical,
        "saved_aggregate_checks": checks,
        "all_checks_pass": all(checks.values()),
        "limitations": [
            "The Mac .local/model-refinement/data-audit.json and original HW5 template were unavailable.",
            "Saved prediction files were unavailable; model metrics and intervals were not independently reproduced.",
            "The published dictionary does not establish the collection windows of every derived feature.",
        ],
    }
    if not evidence["all_checks_pass"]:
        raise SystemExit("Saved aggregate reconciliation failed: " + str([k for k, v in checks.items() if not v]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(checks)} aggregate checks; no model fitting. Wrote {args.output}")


if __name__ == "__main__":
    main()
