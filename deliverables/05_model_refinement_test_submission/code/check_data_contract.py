"""Run synthetic boundary tests, then reconcile the release without modelling."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

from nudgewell_hw5.data_contract import HOME, ROOT, ContractError, load_dataset, load_protocol, write_private_json
from nudgewell_hw5.splits import calibration_splits, day_splits, inner_splits, outer_splits, split_manifest


def test_ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_ids(item)
        else:
            yield item.id()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()
    protocol = load_protocol()
    suite = unittest.defaultTestLoader.discover(str(HOME / "tests"))
    names = list(test_ids(suite))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    if not result.wasSuccessful():
        print(stream.getvalue(), file=sys.stderr)
        raise SystemExit("Synthetic boundary tests failed; real-data checks were not run.")
    data = load_dataset(args.csv, protocol)
    outers = outer_splits(data)
    nested_private, fold_summary = [], []
    inner_count = calibration_count = 0
    for outer in outers:
        private = {"outer_fold": outer.fold, "inner": []}
        public = {"outer_fold": outer.fold, "fit_people": len(set(data.groups(outer.train))), "test_people": len(set(data.groups(outer.test))), "fit_rows": len(outer.train), "test_rows": len(outer.test), "inner_folds": []}
        for inner in inner_splits(data, outer):
            inner_count += 1
            cals = calibration_splits(data, outer, inner)
            calibration_count += len(cals)
            private["inner"].append({"fold": inner.fold, "train": list(inner.train), "test": list(inner.test), "excluded_people": sorted(inner.forbidden_groups), "calibration": [{"fold": c.fold, "train": list(c.train), "test": list(c.test), "excluded_people": sorted(c.forbidden_groups)} for c in cals]})
            public["inner_folds"].append({"fold": inner.fold, "fit_people": len(set(data.groups(inner.train))), "validation_people": len(set(data.groups(inner.test))), "fit_rows": len(inner.train), "validation_rows": len(inner.test)})
        nested_private.append(private)
        fold_summary.append(public)
    days = tuple(day for subject in sorted(set(data.groups())) for day in day_splits(data, subject))
    evaluated = [r for day in days for r in day.test]
    if len(evaluated) != len(set(evaluated)):
        raise ContractError("A real row entered more than one daily evaluation.")
    context = data.frame()["Category_L1"]
    row_partition = {
        "released": data.counts["released_rows"],
        "exact_duplicates_removed": data.counts["released_rows"] - len(data),
        "unique": len(data),
        "feature_exclusions": 0,
        "known_user_warmup_rows": len(data) - len(evaluated),
        "known_user_evaluation_rows": len(evaluated),
        "known_user_evaluation_people": len(set(d.subject for d in days)),
        "known_user_evaluated_days": len(days),
        "unresolved_history_row_day_exclusions": sum(len(d.unresolved_prior) for d in days),
        "unique_unresolved_history_rows": len(set(r for d in days for r in d.unresolved_prior)),
    }
    frozen = json.loads((HOME / "build/protocol_preflight.json").read_text(encoding="utf-8"))
    expected = frozen["known_user_boundary_feasibility"]
    if (len(evaluated), len(days), row_partition["known_user_evaluation_people"]) != (expected["rows"], expected["observed_days"], expected["people"]):
        raise ContractError("Implemented daily coverage differs from frozen preflight.")
    if sum(len(s.test) for s in outers) != len(data):
        raise ContractError("Outer evaluation row coverage does not reconcile.")
    payload = split_manifest(data, outers, days)
    payload["nested"] = nested_private
    write_private_json(HOME / "run/step4/split_manifest.json", payload)
    code_paths = sorted((HOME / "code").rglob("*.py")) + sorted((HOME / "tests").rglob("*.py"))
    output = {
        "step": 4,
        "date_local": "2026-11-17",
        "protocol_sha256": protocol.digest,
        "frozen_protocol_unchanged": True,
        "synthetic_boundary_tests": {"run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped), "passed": True, "ids": names},
        "source_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in code_paths},
        "release_counts": data.counts,
        "row_reconciliation": row_partition,
        "feature_packs": {name: len(columns) for name, columns in protocol.config["features"]["packs"].items()},
        "missing_category_encoded_without_dropping_rows": int(context.isna().sum()),
        "nested_split_counts": {"outer": len(outers), "inner": inner_count, "calibration": calibration_count},
        "outer_aggregate_geometry": fold_summary,
        "private_manifest": "deliverables/05_model_refinement_test_submission/run/step4/split_manifest.json",
        "real_data_model_fits": 0,
        "real_data_predictions_or_performance_estimates_created": False,
        "scope": "Implemented data/feature, split, scoped-fit/calibration-provenance, history, preprocessing and cutoff primitives. Tests fit tiny synthetic models only.",
        "remaining_before_full_experiments": ["Implement the bounded candidate selector and orchestration in Step 5.", "Test selected calibration/cutoff fallback orchestration and complete aggregate metrics/bootstrap/figure generation when implemented.", "Independently review integrated model-selection/evaluation data flow before final report claims."],
    }
    (HOME / "build/step4_validation.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {result.testsRun} synthetic tests; {len(data)} unique rows; 5/15/45 nested splits.")
    print(f"Daily evaluation: {len(evaluated)} rows, {len(set(d.subject for d in days))} people, {len(days)} days; no real-data model fits.")
    print("Private memberships written only to the ignored HW5 run directory; aggregate evidence written to build/step4_validation.json.")


if __name__ == "__main__":
    main()
