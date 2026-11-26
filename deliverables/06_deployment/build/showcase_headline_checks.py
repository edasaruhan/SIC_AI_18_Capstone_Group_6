"""Aggregate-only checks behind the final-showcase slides 2 and 6 (27 Nov 2026).

Needs the local release CSV and the private HW5 run directory, so it runs only on the
data machine. It prints aggregates only: no participant codes, rows or timestamps.
From the repository root, with the HW6 environment:

    python -B deliverables/06_deployment/build/showcase_headline_checks.py         ../Capstone_Digital_Addiction/data/raw/awaremind/full_data_all_feature.csv         deliverables/05_model_refinement_test_submission/run/hw5-v1-step5-20261117         > deliverables/06_deployment/build/results/showcase_headline_checks.json

The fixed rule on the matched daily rows is a descriptive check added after the
frozen HW5 protocol; label it that way wherever it is shown.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "05_model_refinement_test_submission" / "code"))
import json
import sys
import numpy as np
import pandas as pd
from nudgewell_hw5.data_contract import load_dataset, load_protocol
from nudgewell_hw5.runner import clock_parts

CSV = sys.argv[1]
RUN = sys.argv[2]
d = load_dataset(CSV, load_protocol())
f = d.frame()
y = d.labels()
groups = np.asarray(d.groups())
out = {}

# 1. Problem-slide statistic on the 5,627 unique check-ins.
stop, over = (f["answer"] <= 5).to_numpy(), (f["remaining_minutes"] > 5).to_numpy()
out["stop_leaning"] = {"n": int(stop.sum()), "over5": int((stop & over).sum()),
                       "over5_pct": round(100 * over[stop].mean(), 1)}
out["continue_leaning_over5_pct"] = round(100 * over[~stop].mean(), 1)
a1 = (f["answer"] == 1).to_numpy()
out["answer1_over5_pct"] = round(100 * over[a1].mean(), 1)

# 2. Headline robustness on the matched daily rows.
k = pd.read_csv(f"{RUN}/predictions_known_user.csv", dtype={"participant": str})
h, _, elapsed = clock_parts(f)
rule = h.isin(range(6)).to_numpy() | f["Category_L1"].eq("Social").to_numpy() | (elapsed > 10)
k["rule_flag"] = rule[k["row_position"].to_numpy()]
methods = {"global": "global_flag", "personal_rate": "personal_rate_flag",
           "offset": "global_plus_daily_personal_offset_flag", "fixed_rule": "rule_flag"}
top = k.groupby("participant")["label"].mean().idxmax()  # most extreme person, not printed

def summary(frame):
    res = {"rows": len(frame), "positives": int(frame["label"].sum()),
           "prevalence_pct": round(100 * frame["label"].mean(), 1)}
    for name, col in methods.items():
        fl = frame[col].astype(bool)
        tp = int((fl & frame["label"].eq(1)).sum())
        res[name] = {"precision_pct": round(100 * tp / fl.sum(), 1) if fl.sum() else None,
                     "recall_pct": round(100 * tp / frame["label"].sum(), 1),
                     "alert_share_pct": round(100 * fl.mean(), 1)}
    return res

out["daily_all"] = summary(k)
# Public copy: precision only. Row and positive counts here would reveal one person's
# counts by subtraction from the all-people block.
without = summary(k[k["participant"] != top])
out["daily_without_most_extreme_person"] = {name: {"precision_pct": without[name]["precision_pct"]}
                                            for name in methods}
out["daily_without_most_extreme_person"]["prevalence_pct"] = without["prevalence_pct"]
# per-person precision (people with >=1 flag), median across people
med = {}
for name, col in methods.items():
    vals = []
    for _, g in k.groupby("participant"):
        fl = g[col].astype(bool)
        if fl.sum():
            vals.append((fl & g["label"].eq(1)).sum() / fl.sum())
    med[name] = {"median_person_precision_pct": round(100 * float(np.median(vals)), 1), "people": len(vals)}
out["daily_per_person_median"] = med
print(json.dumps(out, indent=1))
