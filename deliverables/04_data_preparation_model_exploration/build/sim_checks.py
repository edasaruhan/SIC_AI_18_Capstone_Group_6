"""Pipeline checks on the SYNTHETIC stand-in (they test the code, not people).

usage: python -I sim_checks.py <simulator_dir> <real_csv> <work_dir>

1. Makes a NULL-mode synthetic file (no planted effects, no person-level variance).
2. Runs the feature set and split of the team's first draft (5-fold participant split;
   personal random forest on the people with >= 1 high-gap moment in both slices) on the
   default and the NULL synthetic files, for comparison.
3. Runs the corrected pipeline (code/hw4_pipeline.py --quick) on both files.
4. Trains the corrected models on the synthetic file only and scores the real file.
Writes <work_dir>/sim_results.json.
"""

import json
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
sim_dir, real_csv, work = map(Path, sys.argv[1:4])
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))
import hw4_pipeline as hp  # noqa: E402

# Columns the first draft dropped before modelling (its Section 4 code).
DRAFT_DROP = [
    "answer",
    "remaining_scaled",
    "intention_behavior_gap",
    "remaining_time",
    "remaining_minutes",
    "remaining_capped",
    "remaining_log",
    "temp_scaled",
    "lock_time",
    "session_length_till_esm",
    "screen_time_so_far",
    "pid",
    "PID",
    "host",
    "esm_id_full",
    "session_id_combined",
    "app_at_prompt",
    "package_name",
    "date",
    "date_4am",
    "unlock_time",
    "esm_time",
    "esm_local",
    "unlock_local",
    "timezone",
    "time_period_nan",
    "genre_To exclude",
    "high_gap",
    "activity_name",
    "Category_L1",
    "is_synthetic",
]


def draft_features(df_raw):
    """The first draft's feature code: everything not dropped, demographics included,
    session-length 'intensity' rates and median imputation on the whole file."""
    df = df_raw.copy()
    df["high_gap"] = ((df["answer"] < 5.5) & (df["remaining_minutes"] > 5)).astype(int)
    df["sin_hour"] = np.sin(2 * np.pi * df["esm_hour"] / 24.0)
    df["cos_hour"] = np.cos(2 * np.pi * df["esm_hour"] / 24.0)
    sess_min = df["session_minutes"].clip(lower=0.1)
    scrolls = df["scroll_down_count"].fillna(0) + df["scroll_up_count"].fillna(0)
    df["scroll_intensity"] = scrolls / sess_min
    df["tap_intensity"] = df["tap_count"].fillna(0) / sess_min
    X = df[[c for c in df.columns if c not in DRAFT_DROP]].copy()
    for col in X.columns:
        if X[col].dtype == "object" or pd.api.types.is_string_dtype(X[col]):
            X[col] = pd.Categorical(X[col]).codes
        else:
            med = X[col].median()
            X[col] = X[col].fillna(0 if pd.isna(med) else med)
    return X, df["high_gap"].values, df["pid"].values


work.mkdir(parents=True, exist_ok=True)
default_csv = sim_dir / "out" / "SYNTHETIC_awaremind_sim_seed2410.csv"
null_dir = work / "sim_null"
simulator = [sys.executable, "-I", str(sim_dir / "simulate_awaremind.py")]
subprocess.run(
    simulator + ["--null", "--seed", "2410", "--out", str(null_dir)],
    check=True,
    capture_output=True,
)
null_csv = next(null_dir.glob("SYNTHETIC_*_null.csv"))
out = {}

for label, csv in [("synthetic_default", default_csv), ("synthetic_null", null_csv)]:
    raw = pd.read_csv(csv, low_memory=False)
    X, y, pids = draft_features(raw)
    models = hp.make_models()
    draft = {}
    feature_sets = [
        ("draft features (incl. demographics)", list(X.columns)),
        (
            "draft features minus demographics",
            [c for c in X.columns if c not in hp.DEMOGRAPHICS],
        ),
    ]
    for feats_label, cols in feature_sets:
        for name in ["LR", "RF", "XGB", "LGBM"]:
            rocs, prs = [], []
            for tr, te in GroupKFold(n_splits=5).split(X, y, pids):
                model = clone(models[name]).fit(X.iloc[tr][cols], y[tr])
                s = model.predict_proba(X.iloc[te][cols])[:, 1]
                rocs.append(roc_auc_score(y[te], s))
                prs.append(average_precision_score(y[te], s))
            draft[f"{name} | {feats_label}"] = {
                "roc_auc": [float(np.mean(rocs)), float(np.std(rocs))],
                "pr_auc": [float(np.mean(prs)), float(np.std(prs))],
            }
    # The draft's personal random forest: chronological 70/30, people with >= 1 high-gap
    # moment in both slices.
    esm = raw["esm_time"].values
    pr_list, prev_list = [], []
    for p in np.unique(pids):
        idx = np.flatnonzero(pids == p)
        idx = idx[np.argsort(esm[idx], kind="stable")]
        k = int(0.7 * len(idx))
        tr, te = idx[:k], idx[k:]
        if y[tr].sum() >= 1 and y[te].sum() >= 1 and y[tr].sum() < len(tr):
            model = clone(models["RF"]).fit(X.iloc[tr], y[tr])
            s = model.predict_proba(X.iloc[te])[:, 1]
            pr_list.append(average_precision_score(y[te], s))
            prev_list.append(y[te].mean())
    draft["personal RF (draft selection)"] = {
        "n_people": len(pr_list),
        "pr_auc_mean": float(np.mean(pr_list)),
        "test_prevalence_mean": float(np.mean(prev_list)),
    }
    # The corrected pipeline, quick mode.
    run_dir = work / label
    subprocess.run(
        [
            sys.executable,
            "-I",
            str(code_dir / "hw4_pipeline.py"),
            str(csv),
            str(run_dir),
            "--quick",
        ],
        check=True,
        capture_output=True,
    )
    corrected = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    keep = ("roc_auc", "pr_auc", "within_roc_auc")
    out[label] = {
        "rows": int(len(raw)),
        "high_gap_rate": float(y.mean()),
        "draft": draft,
        "corrected_global": {
            k: {m: v[m] for m in keep} for k, v in corrected["global"].items()
        },
        "corrected_personal": {
            k: {m: v[m] for m in keep}
            for k, v in corrected["personal"]["approaches"].items()
        },
        "icc": corrected["data"]["icc"],
        "night": corrected["data"]["night"],
    }
    print(label, "done", flush=True)

# Sim -> real: train on the synthetic file only, score every real check-in.
_, sim = hp.load(default_csv)
_, real = hp.load(real_csv)
Xs, ys = hp.build_features(sim).values, sim["high_gap"].values
Xr, yr, gr = hp.build_features(real).values, real["high_gap"].values, real["pid"].values
out["sim_to_real"] = {}
for name, m in hp.make_models().items():
    s = clone(m).fit(Xs, ys).predict_proba(Xr)[:, 1]
    pp = hp.per_person(yr, s, gr)
    out["sim_to_real"][name] = {
        "roc_auc": float(roc_auc_score(yr, s)),
        "pr_auc": float(average_precision_score(yr, s)),
        "within_roc_auc": float(pp[:, 0].mean()),
        "within_n": int(len(pp)),
    }
print(json.dumps(out["sim_to_real"], indent=1))
(work / "sim_results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print("wrote", work / "sim_results.json")
