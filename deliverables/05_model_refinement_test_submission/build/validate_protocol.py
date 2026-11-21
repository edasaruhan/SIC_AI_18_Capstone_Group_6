"""Validate and seal the HW5 specification; no estimators are imported or fitted."""

import argparse
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fold_groups(groups, namespace, n_splits, seed=42):
    """Label-blind, specified UTF-8 hash ordering followed by round robin."""
    groups = sorted(set(map(str, groups)))
    ordered = sorted(
        groups,
        key=lambda g: (
            hashlib.sha256(f"{seed}|{namespace}|{g}".encode("utf-8")).hexdigest(),
            g,
        ),
    )
    return {g: i % n_splits for i, g in enumerate(ordered)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, default=Path(__file__).with_name("protocol.json"))
    args = ap.parse_args()
    p = json.loads(args.protocol.read_text(encoding="utf-8"))
    seal = args.protocol.with_suffix(".sha256")
    protocol_hash = digest(args.protocol)
    if seal.exists() and seal.read_text(encoding="utf-8").split()[0] != protocol_hash:
        raise SystemExit("Protocol differs from its seal. Create a documented new version; do not replace the v1 seal.")
    checks = {}

    def check(name, value):
        checks[name] = bool(value)

    check("frozen_v1", p["status"] == "frozen" and p["version"] == "1.0.0")
    check("no_training_at_freeze", p["freeze"]["hw5_model_fits_before_freeze"] == 0)
    check("python_version", list(sys.version_info[:2]) == p["environment"]["python_major_minor"])
    versions = {}
    for package, expected in p["environment"]["exact_packages"].items():
        versions[package] = importlib.metadata.version(package)
        check("version." + package, versions[package] == expected)
    for name, source in p["sources"].items():
        file = ROOT / source["path"]
        check("source." + name, file.exists() and digest(file) == source["sha256"])
    check("raw_hash", digest(args.csv) == p["data"]["raw_sha256"])
    for name, expected in p["data"]["dictionary_sha256"].items():
        file = args.csv.parent / name
        check("dictionary." + name, file.exists() and digest(file) == expected)

    check("input_packs", {k: len(v) for k, v in p["features"]["packs"].items()} == {"time_session": 5, "main_context": 15})
    declared = [x["name"] for x in p["features"]["ordered_definitions"]]
    check("input_order", declared == p["features"]["packs"]["main_context"] and len(set(declared)) == 15)
    check("no_forbidden_inputs", not (set(declared) & set(p["features"]["forbidden_raw_classifier_columns"])))
    base = p["models"]["ordered_base_candidates"]
    check("candidate_counts", len(base) == 16 and sum(x["family"] == "LR" for x in base) == 8 and sum(x["family"] == "RF" for x in base) == 8)
    check("candidate_ids_unique", len({x["id"] for x in base}) == len(base))
    lr_grid = {(x["parameters"]["C"], x["parameters"]["class_weight"]) for x in base if x["family"] == "LR"}
    rf_grid = {(x["parameters"]["max_depth"], x["parameters"]["min_samples_leaf"], x["parameters"]["class_weight"]) for x in base if x["family"] == "RF"}
    check("LR_grid", lr_grid == {(c, w) for c in [0.01, 0.1, 1.0, 10.0] for w in [None, "balanced"]})
    check("RF_grid", rf_grid == {(d, leaf, w) for d in [3, 6] for leaf in [1, 5] for w in [None, "balanced"]})
    structures = p["models"]["ordered_structural_candidates"]
    check("structural_grid", len(structures) == 32 and {(x["base_id"], x["feature_pack"]) for x in structures} == {(x["id"], pack) for x in base for pack in p["features"]["packs"]})
    check("structure_ids_unique", len({x["id"] for x in structures}) == 32)
    anchors = p["models"]["fixed_anchor_ids"]
    by_id = {x["id"]: x for x in base}
    check("fixed_anchors", by_id[anchors["LR"]]["parameters"] == {"C": 1.0, "class_weight": "balanced"} and by_id[anchors["RF"]]["parameters"] == {"max_depth": 6, "min_samples_leaf": 1, "class_weight": "balanced"})
    check("fold_geometry", p["splits"]["outer_folds"] == 5 and p["splits"]["inner_folds"] == 3 and p["splits"]["calibration_folds"] == 3)
    check("calibration_assessment_separated", p["calibration"]["assessment"] == "inner_validation_with_calibrator_fit_wholly_inside_inner_training")
    check("cutoff_fixed_in_training", p["decisions"]["cutoff_source"] == "assembled_inner_held_out_scores" and p["decisions"]["evaluation_refit_allowed"] is False)
    check("daily_contract", p["known_user"]["local_day_start"] == "00:00" and p["known_user"]["warmup_calendar_days"] == 7 and p["known_user"]["history_lock_operator"] == "<")
    check("peer_archive_excludes_outer_fold", p["known_user"]["population_model_source"] == "refined_procedure_from_persons_outer_fold_training_universe")
    check("paired_participant_bootstrap", p["uncertainty"]["reps"] == 2000 and p["uncertainty"]["unit"] == "participant" and p["uncertainty"]["paired"])
    check("private_run_ignored", "deliverables/05_model_refinement_test_submission/run/" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())

    raw = pd.read_csv(args.csv, low_memory=False)
    df = raw.drop_duplicates().reset_index(drop=True)
    y = ((df["answer"] <= 5) & (df["remaining_minutes"] > 5)).astype(int)
    counts = {"released_rows": len(raw), "unique_rows": len(df), "positive_rows": int(y.sum()), "participants": int(df["pid"].nunique()), "columns": len(raw.columns)}
    check("expected_counts", counts == p["data"]["expected_counts"])
    required = p["data"]["required_columns"]
    check("required_columns", set(required).issubset(df.columns))
    check("valid_target", df["answer"].notna().all() and df["answer"].between(1, 10).all() and df["remaining_minutes"].notna().all() and np.isfinite(df["remaining_minutes"]).all() and (df["remaining_minutes"] >= 0).all())
    time_columns = ["esm_time", "unlock_time", "lock_time"]
    check("finite_timestamps", np.isfinite(df[time_columns].to_numpy(dtype=float)).all())
    check("valid_timestamp_order", ((df["unlock_time"] <= df["esm_time"]) & (df["esm_time"] <= df["lock_time"])).all())
    elapsed = (df["esm_time"] - df["unlock_time"]) / 60000
    check("elapsed_matches_release", np.isclose(elapsed, df["session_minutes"], rtol=0, atol=1e-6).all())
    check("identity_metadata_present", df[["pid", "session_id_combined", "timezone"]].notna().all().all())
    timezone_counts = df.groupby("pid")["timezone"].nunique()
    check("timezone_reference_rule", p["known_user"]["evaluation_timezone"] == "timezone_at_first_chronological_prompt_stable_file_order_ties")
    grouped_sessions = df.groupby(["pid", "session_id_combined"])
    check("session_unlock_consistent", grouped_sessions["unlock_time"].nunique().eq(1).all())
    check("session_lock_consistent", grouped_sessions["lock_time"].nunique().eq(1).all())
    cats = p["features"]["app_categories"]
    check("category_vocabulary", df["Category_L1"].dropna().isin(cats).all())
    check("genres_match_categories", all((df["genre_" + c].astype(bool) == df["Category_L1"].eq(c)).all() for c in cats))
    overlap = df["package_name"].notna() & df["app_at_prompt"].notna()
    check("recorded_package_is_prompt_app", df.loc[overlap, "package_name"].eq(df.loc[overlap, "app_at_prompt"]).all())
    check("recorded_categories_have_prompt_app", not (df["Category_L1"].notna() & df["app_at_prompt"].isna()).any())
    check("recorded_categories_have_package", not (df["Category_L1"].notna() & df["package_name"].isna()).any())
    context = {"recorded_app_name_pairs": int(overlap.sum()), "category_missing": int(df["Category_L1"].isna().sum()), "prompt_app_missing": int(df["app_at_prompt"].isna().sum()), "category_missing_with_known_prompt_app": int((df["Category_L1"].isna() & df["app_at_prompt"].notna()).sum())}

    utc = pd.to_datetime(df["esm_time"], unit="ms", utc=True)
    hour_ok = weekday_ok = local_ok = True
    for zone, idx in df.groupby("timezone").groups.items():
        local = utc.loc[idx].dt.tz_convert(zone)
        hour_ok &= bool(np.array_equal(local.dt.hour.to_numpy(), df.loc[idx, "esm_hour"].to_numpy()))
        weekday_ok &= bool(np.array_equal(local.dt.dayofweek.to_numpy(), df.loc[idx, "esm_weekday"].to_numpy()))
        local_ok &= bool(np.array_equal(local.dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy(), df.loc[idx, "esm_local"].astype(str).str[:19].str.replace("T", " ", regex=False).to_numpy()))
    check("timezone_hour_matches", hour_ok)
    check("timezone_weekday_matches", weekday_ok)
    check("timezone_local_time_matches", local_ok)

    # Count fold geometry; no private membership leaves memory.
    g = df["pid"].astype(str)
    outer = fold_groups(g, "outer", 5)
    fold_counts = []
    for f in range(5):
        test = g.map(outer).eq(f)
        train_groups = set(g[~test])
        inner = fold_groups(train_groups, f"outer={f}/inner", 3)
        row = {"outer_fold": f, "test_people": int(g[test].nunique()), "test_rows": int(test.sum()), "test_positives": int(y[test].sum()), "inner_folds": []}
        check(f"outer.{f}.disjoint", not (set(g[test]) & train_groups))
        for j in range(3):
            val_groups = {person for person, fold in inner.items() if fold == j}
            fit_groups = train_groups - val_groups
            cal = fold_groups(fit_groups, f"outer={f}/inner={j}/calibration", 3)
            check(f"outer.{f}.inner.{j}.geometry", bool(val_groups) and len(fit_groups) >= 3 and set(cal.values()) == {0, 1, 2} and not (val_groups & fit_groups))
            val = g.isin(val_groups)
            row["inner_folds"].append({"fold": j, "validation_people": len(val_groups), "fit_people": len(fit_groups), "validation_rows": int(val.sum()), "validation_positives": int(y[val].sum())})
        fold_counts.append(row)

    # Feasibility counts for the specified clock/history rules, without fitting.
    eligible_people = eligible_rows = evaluated_days = overlap_errors = 0
    for _, part in df.groupby("pid"):
        zone = part.sort_values("esm_time", kind="stable")["timezone"].iloc[0]
        local = pd.to_datetime(part["esm_time"], unit="ms", utc=True).dt.tz_convert(zone)
        first = local.min().normalize()
        first_test_day = first + pd.DateOffset(days=7)
        days = sorted(set(local[local >= first_test_day].dt.normalize()))
        eligible_people += int(bool(days))
        for day in days:
            end = day + pd.DateOffset(days=1)
            cut_ms = day.tz_convert("UTC").value // 1_000_000
            te = (local >= day) & (local < end)
            tr = (part["esm_time"] < cut_ms) & (part["lock_time"] < cut_ms)
            overlap_errors += int(bool(set(part.loc[tr, "session_id_combined"]) & set(part.loc[te, "session_id_combined"])))
            eligible_rows += int(te.sum())
            evaluated_days += 1
    check("day_forward_sessions_disjoint", overlap_errors == 0)
    check("day_forward_nonempty", eligible_people > 0 and eligible_rows > 0)

    failed = [k for k, value in checks.items() if not value]
    if failed:
        raise SystemExit("Protocol preflight failed: " + ", ".join(failed))
    result = {
        "scope": "Configuration, source/data consistency and boundary feasibility only; no model fits or performance estimates.",
        "protocol_sha256": protocol_hash,
        "frozen_date_local": p["freeze"]["date_local"],
        "checks": checks,
        "all_checks_pass": True,
        "versions": versions,
        "data_counts": counts,
        "app_metadata_counts": context,
        "people_with_multiple_recorded_timezones": int(timezone_counts.gt(1).sum()),
        "outer_fold_aggregate_geometry": fold_counts,
        "known_user_boundary_feasibility": {"people": eligible_people, "rows": eligible_rows, "observed_days": evaluated_days, "shared_history_evaluation_session_errors": overlap_errors},
        "implementation_acceptance_tests_passed": False,
        "implementation_test_status": "Not implemented at Step 3; required before model runs.",
    }
    args.protocol.with_name("protocol_preflight.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not seal.exists():
        seal.write_text(protocol_hash + "  " + args.protocol.name + "\n", encoding="utf-8")
    print(f"PASS: {len(checks)} protocol/data checks; 32 candidates; no model fitting. SHA256 {protocol_hash}")


if __name__ == "__main__":
    main()
