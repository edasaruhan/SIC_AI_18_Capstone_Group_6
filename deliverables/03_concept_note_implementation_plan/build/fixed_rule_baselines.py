"""How much of the high-gap signal do simple fixed rules capture? (Concept note, Background 3.4 / Table 3.)

Descriptive statistics only; no model is trained (the AwareMind licence is still unconfirmed).
Usage (from anywhere):  python -I fixed_rule_baselines.py
Reads ../../../data/raw/awaremind/full_data_all_feature.csv, writes fixed_rule_baselines.json next to this script.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
CSV = HERE.parents[2] / "data" / "raw" / "awaremind" / "full_data_all_feature.csv"
OUT = HERE / "fixed_rule_baselines.json"

df = pd.read_csv(CSV, low_memory=False)
# Same definition as the paper and notebooks/01_awaremind_eda.ipynb: leaning toward stopping, yet > 5 more minutes of use.
df["high_gap"] = ((df.answer < 5.5) & (df.remaining_minutes > 5)).astype(int)
N, K = len(df), int(df.high_gap.sum())
assert N == 5772 and K == 859, "data changed: expected 5,772 check-ins and 859 high-gap moments"

night = df.esm_hour.between(0, 5)                 # midnight to 6 am, participant's local time
social = df.Category_L1.eq("Social")
long_session = df.session_minutes > 10            # time since unlock at the check-in
daily_3h = df.screen_time_minutes > 180           # 3 h/day was the study's inclusion threshold
rules = {
    "it is night (midnight to 6 am)": night,
    "a social-media app is open": social,
    "the session has lasted more than 10 minutes": long_session,
    "more than 3 hours of screen time today": daily_3h,
    "any of the first three": night | social | long_session,
}

rows = []
for name, flag in rules.items():
    flagged, hits = int(flag.sum()), int(df.high_gap[flag].sum())
    rows.append({"rule": name, "flagged_pct": round(flagged / N * 100, 1),
                 "precision_pct": round(hits / flagged * 100, 1), "recall_pct": round(hits / K * 100, 1)})
    print(f"{name:45s} flagged {rows[-1]['flagged_pct']:5.1f}% | precision {rows[-1]['precision_pct']:5.1f}% | recall {rows[-1]['recall_pct']:5.1f}%")

per_day = df.groupby(["pid", "date_4am"]).size()
summary = {
    "checkins": N, "high_gap": K, "base_rate_pct": round(K / N * 100, 1),
    "checkins_per_participant_day_mean": round(float(per_day.mean()), 1),
    "rules": rows,
    "note": "Rates are over check-in moments, which AwareMind sampled within sessions; not over every minute of use.",
}
OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("wrote", OUT)
