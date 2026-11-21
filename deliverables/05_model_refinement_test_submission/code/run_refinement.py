"""Run tests, then select (Step 5) or evaluate saved procedures (Step 6)."""

import argparse
import json

from nudgewell_hw5.data_contract import HOME, load_protocol, load_dataset
from nudgewell_hw5.runner import execute_evaluation, execute_selection, run_test_gate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--phase", choices=["select", "evaluate"], default="select")
    parser.add_argument("--resume", action="store_true", help="Resume only matching partial selection checkpoints.")
    parser.add_argument("--tests-only", action="store_true")
    args = parser.parse_args()
    protocol = load_protocol()
    print("Running synthetic unit/integration tests before released-data fitting...", flush=True)
    gate = run_test_gate(protocol)
    report = {"passed": True, "tests_run": gate.tests_run, "protocol_sha256": gate.protocol_sha256, "code_sha256": gate.code_sha256, "test_ids": list(gate.test_ids), "scope": "Synthetic integration gate; no released-data model fit during tests."}
    (HOME / "build/step5_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {gate.tests_run} tests", flush=True)
    if args.tests_only:
        return
    data = load_dataset(args.csv, protocol)
    progress = lambda message: print(message, flush=True)
    if args.phase == "select":
        result = execute_selection(data, args.run_id, gate, progress=progress, resume=args.resume)
    else:
        result = execute_evaluation(data, args.run_id, gate, progress=progress)
    print(f"Completed {result['phase']}. Aggregates: build/results/{args.run_id}_{'selection' if args.phase == 'select' else 'evaluation'}.json", flush=True)


if __name__ == "__main__":
    main()
