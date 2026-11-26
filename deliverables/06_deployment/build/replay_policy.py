"""Replay the HW3 delivery rules over the frozen HW5 new-user candidate flags."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

HW6 = Path(__file__).resolve().parents[1]
HW5 = HW6.parent / "05_model_refinement_test_submission"
ROOT = HW6.parents[1]
sys.path.insert(0, str(HW5 / "code"))

from nudgewell_hw5.data_contract import load_dataset, load_protocol, sha256

RUN_ID = "hw5-v1-step5-20261117"
DAILY_CAP = 3
COOLDOWN_MINUTES = 30
COOLDOWN_MS = COOLDOWN_MINUTES * 60_000


def delivery_decisions(checkins):
    """Classify time-ordered (UTC ms, reference date, candidate) events for one person."""
    observed_day = None
    delivered_today = 0
    last_delivery = None
    for prompt_ms, day, candidate in checkins:
        if day != observed_day:
            observed_day = day
            delivered_today = 0
        if not candidate:
            yield "not_flagged"
        elif delivered_today == DAILY_CAP:
            yield "daily_cap"
        elif last_delivery is not None and prompt_ms - last_delivery < COOLDOWN_MS:
            yield "cooldown"
        else:
            delivered_today += 1
            last_delivery = prompt_ms
            yield "delivered"


def load_verified_inputs(csv):
    data = load_dataset(csv, load_protocol())
    results = HW5 / "build" / "results"
    evaluation_path = results / f"{RUN_ID}_evaluation.json"
    verification = json.loads((results / f"{RUN_ID}_verification.json").read_bytes())
    archive = HW5 / "run" / RUN_ID / "predictions_new_user.csv"
    if (verification["run_id"] != RUN_ID or verification["protocol_sha256"] != data.protocol.digest
            or sha256(evaluation_path) != verification["evaluation_sha256"]
            or sha256(archive) != verification["private_artifact_sha256"][archive.name]):
        raise ValueError("The replay requires the verified HW5 release, evaluation and candidate archive.")
    saved = pd.read_csv(archive, usecols=["row_position", "row_key", "participant", "label",
                                        "refined_selector_flag"], dtype={"participant": str})
    if (not np.array_equal(saved["row_position"], np.arange(len(data)))
            or tuple(saved["row_key"]) != data.keys
            or not np.array_equal(saved["participant"], data.groups())
            or not np.array_equal(saved["label"], data.labels())
            or not pd.api.types.is_bool_dtype(saved["refined_selector_flag"])):
        raise ValueError("Frozen candidate flags do not align with the release.")
    frame = data.frame()
    frame["label"] = data.labels().astype(bool)
    frame["refined"] = saved["refined_selector_flag"]
    frame["rule"] = (frame["esm_hour"].between(0, 5) | frame["Category_L1"].eq("Social")
                     | (frame["esm_time"] - frame["unlock_time"]).gt(600_000))
    evaluation = json.loads(evaluation_path.read_bytes())
    new_user = evaluation["new_user"]
    for method, outcome in (("refined", new_user["refined_selector"]["decisions"]),
                            ("rule", new_user["fixed_rule"])):
        if (int(frame[method].sum()) != outcome["tp"] + outcome["fp"]
                or int((frame[method] & frame["label"]).sum()) != outcome["tp"]):
            raise ValueError("Candidate totals differ from the frozen evaluation.")
    return frame, verification


def simulate(frame):
    chronological = frame.sort_values("esm_time", kind="stable")
    rows_by_person = []
    for _, part in chronological.groupby("pid", sort=False):
        part = part.copy()
        zone = str(part["timezone"].iloc[0])
        part["reference_day"] = pd.to_datetime(part["esm_time"], unit="ms", utc=True).dt.tz_convert(zone).dt.date
        for method in ("refined", "rule"):
            events = part[["esm_time", "reference_day", method]].itertuples(index=False, name=None)
            part[method + "_decision"] = list(delivery_decisions(events))
        rows_by_person.append(part)
    return pd.concat(rows_by_person, ignore_index=True)


def summarize(frame, method):
    decision = frame[method + "_decision"]
    delivered = decision.eq("delivered")
    reached = int((delivered & frame["label"]).sum())
    positives = int(frame["label"].sum())
    days = frame.groupby(["pid", "reference_day"], sort=False).ngroups
    count = int(delivered.sum())
    return {
        "participants": int(frame["pid"].nunique()),
        "observed_participant_days": days,
        "sampled_checkins": len(frame),
        "positive_labels": positives,
        "candidate_flags": int(frame[method].sum()),
        "delivered_prompts": count,
        "delivered_per_observed_participant_day": count / days,
        "days_with_delivery": frame.loc[delivered].groupby(["pid", "reference_day"]).ngroups,
        "cooldown_suppressions": int(decision.eq("cooldown").sum()),
        "daily_cap_suppressions": int(decision.eq("daily_cap").sum()),
        "positive_labels_reached": reached,
        "positive_labels_missed": positives - reached,
        "negative_label_deliveries": count - reached,
        "deliveries_when_answer_at_least_6": int((delivered & frame["answer"].ge(6)).sum()),
    }


def replay(csv):
    frame, verification = load_verified_inputs(csv)
    results = simulate(frame)
    methods = {"refined_fixed_cutoffs": "refined", "fixed_three_signal_rule": "rule"}
    overall = {
        "source_run": RUN_ID,
        "hw5_evaluation_sha256": verification["evaluation_sha256"],
        "scope": "Retrospective replay on sampled check-ins. Delivery and interruption effects are unobserved.",
        "calendar_day": "First observed timezone per participant. Denominator includes observed days with zero deliveries.",
        "policy": {"daily_cap": DAILY_CAP, "cooldown_minutes": COOLDOWN_MINUTES,
                   "cooldown_crosses_midnight": True, "cap_takes_precedence": True},
        "methods": {name: summarize(results, method) for name, method in methods.items()},
    }
    age = pd.cut(results["Age"], [17, 29, 44, 64], labels=["18–29", "30–44", "45–64"])
    strata = {
        "age_band": age.astype("string").fillna("outside bands or missing"),
        "gender_release_code": results["Gender_encoded"].astype("string").fillna("missing"),
    }
    internal = {
        "source_run": RUN_ID,
        "scope": "Internal aggregate subgroup denominators. Gender codes are used as released.",
        "strata": {
            name: {
                str(group): {label: summarize(part, method) for label, method in methods.items()}
                for group, part in results.groupby(groups, sort=True)
            }
            for name, groups in strata.items()
        },
    }
    return overall, internal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()
    public = HW6 / "build" / "results" / "hw6_policy_replay.json"
    private = HW6 / "run" / "policy_replay_subgroups.json"
    if subprocess.run(["git", "check-ignore", "-q", "--", str(private)], cwd=ROOT).returncode:
        raise RuntimeError("The internal subgroup output must be in the ignored run directory.")
    overall, internal = replay(args.csv)
    for destination, result in ((public, overall), (private, internal)):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(overall["methods"], indent=2))


if __name__ == "__main__":
    main()
