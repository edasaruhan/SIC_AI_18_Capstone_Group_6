"""NudgeWell, milestone 4: data preparation, feature engineering and model exploration.
SIC AI Cohort 18, Group 6.

Runs on the AwareMind file (Zheng & Choe, 2026; OSF x6yzs; no licence attached, so it
is not redistributed) or on the project's SYNTHETIC stand-in (same 92 columns):

    python -I hw4_pipeline.py <full_data_all_feature.csv> <out_dir> [--quick]

Writes <out_dir>/results.json (aggregate numbers only, no participant ids) and
<out_dir>/predictions.csv (held-out scores, for the figures).
--quick skips the slow extras.
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import expit, logit
from sklearn.base import clone
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

# fmt: off
# ----------------------------------------------------------------------- 1. columns
# Measured after the prompt: they define or reveal the label, never model inputs.
OUTCOME = ["answer", "remaining_time", "remaining_minutes", "remaining_capped",
           "remaining_log", "remaining_scaled", "temp_scaled",
           "intention_behavior_gap", "lock_time"]
# Identifiers, bookkeeping and raw timestamps (memorise people or sessions).
IDENTIFIERS = ["pid", "PID", "host", "esm_id_full", "session_id_combined",
               "session_index", "package_name", "app_at_prompt", "date", "date_4am",
               "unlock_time", "esm_time", "esm_local", "unlock_local", "timezone",
               "is_synthetic"]
# Static person attributes: not leakage, but unique for each of the 37 people, so
# they act as participant identifiers in cross-user models. Sensitivity analysis only.
DEMOGRAPHICS = ["Age", "Gender_encoded", "Education_encoded", "Race_Asian",
                "Race_black", "Race_native", "Race_others", "Race_white",
                "Employment_full_time", "Employment_part_time", "Employment_student",
                "Employment_self_employed", "Employment_retired",
                "Employment_homemaker", "Employment_others"]

TIME = ["hour_sin", "hour_cos", "weekday_sin", "weekday_cos", "esm_is_weekend",
        "esm_is_workday", "time_period_morning", "time_period_afternoon",
        "time_period_evening", "time_period_night"]
SESSION = ["session_minutes", "app_duration", "app_total_duration_session",
           "unique_apps_in_session", "app_switches_in_session"]
TODAY = ["screen_time_minutes", "prev_session_count_today",
         "prev_session_avg_duration_today", "last_session_duration",
         "interval_after_last_session", "app_total_duration_today",
         "unique_apps_today", "app_switches_today"]
INTERACTION = ["tap_count", "text_edit_count"] + [
    f"scroll_{d}_{k}" for d in ("down", "up", "left", "right")
    for k in ("count", "distance")]
GENRES = ["genre_Social", "genre_Media", "genre_Browser", "genre_Game",
          "genre_Message", "genre_Work & Study", "genre_Daily Life",
          "genre_System tool", "genre_To exclude"]
ACTIVITY = ["activity_still", "activity_walking", "activity_running",
            "activity_on_bicycle", "activity_in_vehicle"]
CONTEXT = GENRES + ACTIVITY + ["app_missing", "activity_missing"]
FEATURES = TIME + SESSION + TODAY + INTERACTION + CONTEXT
GROUP_OF = {**{c: "time" for c in TIME},
            **{c: "current session" for c in SESSION},
            **{c: "earlier use today" for c in TODAY},
            **{c: "recent interaction" for c in INTERACTION},
            **{c: "app and activity" for c in CONTEXT},
            **{c: "demographics" for c in DEMOGRAPHICS}}
# fmt: on
# Heavy-tailed durations, counts and distances: log(1 + x). Trees are unaffected;
# it stabilises the linear model.
LOG1P = SESSION[:3] + TODAY + INTERACTION


def load(path):
    """Read the file, drop exact duplicate rows and add the label."""
    raw = pd.read_csv(path, low_memory=False)
    df = raw.drop_duplicates().reset_index(drop=True)
    # High-gap: wanted to stop (answer 1-5 of 10) but used the phone > 5 more minutes.
    df["high_gap"] = ((df["answer"] <= 5) & (df["remaining_minutes"] > 5)).astype(int)
    return raw, df


def build_features(df, demographics=False):
    """One row per check-in, using only what is known when the prompt appears."""
    X = pd.DataFrame(index=df.index)
    angle_h = 2 * np.pi * df["esm_hour"] / 24  # cyclic: 23:59 sits next to 00:01
    angle_d = 2 * np.pi * df["esm_weekday"] / 7
    X["hour_sin"], X["hour_cos"] = np.sin(angle_h), np.cos(angle_h)
    X["weekday_sin"], X["weekday_cos"] = np.sin(angle_d), np.cos(angle_d)
    for c in TIME[4:] + SESSION + TODAY + INTERACTION + GENRES + ACTIVITY:
        X[c] = df[c].astype(float)
    X["app_missing"] = df["Category_L1"].isna().astype(float)  # not recorded
    X["activity_missing"] = df["activity_type"].isna().astype(float)  # not recorded
    X[LOG1P] = np.log1p(X[LOG1P].clip(lower=0))
    if demographics:
        X[DEMOGRAPHICS] = df[DEMOGRAPHICS].astype(float)
    # Leakage guard: fails if an outcome or identifier column ever enters the table.
    assert not set(X.columns) & set(OUTCOME + IDENTIFIERS), "leakage guard"
    return X[FEATURES + (DEMOGRAPHICS if demographics else [])]


class BalancedXGB(XGBClassifier):
    """XGBoost with scale_pos_weight = negatives / positives of the training fold."""

    def fit(self, X, y, **kw):
        y = np.asarray(y)
        self.set_params(scale_pos_weight=float((y == 0).sum() / max((y == 1).sum(), 1)))
        return super().fit(X, y, **kw)


def make_models(seed=42):
    """Fixed before testing (no tuning). Missing app durations: training-fold median
    (XGBoost and LightGBM handle missing values natively)."""
    return {
        "LR": make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000),
        ),
        "RF": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                min_samples_split=10,
                class_weight="balanced",
                random_state=seed,
                n_jobs=-1,
            ),
        ),
        "XGB": BalancedXGB(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            eval_metric="logloss",
            random_state=seed,
            n_jobs=-1,
        ),
        "LGBM": LGBMClassifier(
            n_estimators=100,
            max_depth=5,
            num_leaves=31,
            learning_rate=0.05,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1,
            verbose=-1,
        ),
    }


# ----------------------------------------------------------------------- 2. metrics
def pooled(y, s):
    return {
        "roc_auc": roc_auc_score(y, s),
        "pr_auc": average_precision_score(y, s),
        "brier": brier_score_loss(y, np.clip(s, 0, 1)),
    }


def per_person(y, s, groups):
    """ROC-AUC and PR-AUC inside each person who has both classes
    (how well a score ranks that person's own moments)."""
    out = []
    for g in np.unique(groups):
        m = groups == g
        if 0 < y[m].sum() < m.sum():
            out.append(
                (
                    roc_auc_score(y[m], s[m]),
                    average_precision_score(y[m], s[m]),
                    y[m].mean(),
                )
            )
    return np.array(out)


def boot(fn, y, s, groups, reps=1000, seed=0):
    """95% interval from resampling participants with replacement."""
    rng = np.random.default_rng(seed)
    ids = np.unique(groups)
    idx = {g: np.flatnonzero(groups == g) for g in ids}
    vals = []
    for _ in range(reps):
        take = np.concatenate([idx[g] for g in rng.choice(ids, len(ids))])
        if 0 < y[take].sum() < len(take):
            vals.append(fn(y[take], s[take]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def summarise(y, s, groups, reps=1000):
    r = pooled(y, s)
    r["roc_auc_ci"] = boot(roc_auc_score, y, s, groups, reps)
    r["pr_auc_ci"] = boot(average_precision_score, y, s, groups, reps)
    pp = per_person(y, s, groups)
    r["within_n"] = int(len(pp))
    r["within_roc_auc"] = float(pp[:, 0].mean())
    r["within_roc_auc_ci"] = [
        float(v)
        for v in np.percentile(
            [
                np.random.default_rng(i).choice(pp[:, 0], len(pp)).mean()
                for i in range(reps)
            ],
            [2.5, 97.5],
        )
    ]
    r["within_pr_auc"] = float(pp[:, 1].mean())
    r["within_prevalence"] = float(pp[:, 2].mean())
    r["within_share_above_half"] = float((pp[:, 0] > 0.5).mean())
    return r


def random_pr_level(y, groups, people, reps=300, seed=0):
    """Mean within-person PR-AUC of random scores on exactly these people's rows
    (the fair chance level)."""
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(reps):
        vals.append(
            np.mean(
                [
                    average_precision_score(
                        y[groups == g], rng.random((groups == g).sum())
                    )
                    for g in people
                ]
            )
        )
    return float(np.mean(vals))


# ------------------------------------------------------------ 3. evaluation regimes
def lopo(model, X, y, groups):
    """New users: each participant is scored by a model trained on everyone else."""
    oof = np.zeros(len(y))
    for g in np.unique(groups):
        te = groups == g
        oof[te] = clone(model).fit(X[~te], y[~te]).predict_proba(X[te])[:, 1]
    return oof


def chrono_split(df, frac=0.7):
    """Known users: in time order, each person's first 70% of check-ins train,
    the last 30% test."""
    train = np.zeros(len(df), bool)
    for _, idx in df.groupby("pid").indices.items():
        order = idx[np.argsort(df["esm_time"].values[idx], kind="stable")]
        train[order[: int(frac * len(order))]] = True
    return train


def fit_offset(s, y, a0=0.0, tau=None, iters=50):
    """Intercept a in p = expit(a + logit(s)) by Newton steps; an optional
    normal prior N(a0, tau^2) shrinks it toward a0 when a person has few check-ins."""
    z = logit(np.clip(s, 1e-4, 1 - 1e-4))
    a = a0
    for _ in range(iters):
        p = expit(a + z)
        g = np.sum(y - p) - (0 if tau is None else (a - a0) / tau**2)
        h = -np.sum(p * (1 - p)) - (0 if tau is None else 1 / tau**2)
        a -= g / h
    return a


def personal_regime(
    df,
    X,
    y,
    groups,
    global_oof,
    base_model,
    reps=1000,
    combined_weight=5.0,
    xgb_model=None,
):
    """Same test rows (last 30% of every participant) for every approach."""
    train = chrono_split(df)
    test = ~train
    prior = y[train].mean()
    names = [
        "Own base rate",
        "Global (zero-shot)",
        "Global + personal intercept",
        "Personal RF",
        "Personal XGBoost",
        "Combined RF",
    ]
    preds = {
        k: np.full(len(y), np.nan)
        for k in names
        if xgb_model is not None or "XGB" not in k
    }
    for g in np.unique(groups):
        tr, te = (groups == g) & train, (groups == g) & test
        others = groups != g
        k, n = y[tr].sum(), tr.sum()
        rate = (k + 10 * prior) / (n + 10)  # shrunk toward the population rate
        preds["Own base rate"][te] = rate
        preds["Global (zero-shot)"][te] = global_oof[te]
        a0 = fit_offset(
            global_oof[others], y[others]
        )  # population calibration of the global score
        a = fit_offset(global_oof[tr], y[tr], a0=a0, tau=1.0)  # one number per person
        preds["Global + personal intercept"][te] = expit(
            a + logit(np.clip(global_oof[te], 1e-4, 1 - 1e-4))
        )
        for name, model in [
            ("Personal RF", base_model),
            ("Personal XGBoost", xgb_model),
        ]:
            if model is None:
                continue
            if 0 < k < n:
                preds[name][te] = (
                    clone(model).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
                )
            else:  # nothing to learn from: fall back to the rate
                preds[name][te] = rate
        fit_rows = others | tr
        w = np.where(tr[fit_rows], combined_weight, 1.0)
        m = clone(base_model)
        m.fit(X[fit_rows], y[fit_rows], **{m.steps[-1][0] + "__sample_weight": w})
        preds["Combined RF"][te] = m.predict_proba(X[te])[:, 1]
    out = {
        "n_test_rows": int(test.sum()),
        "test_prevalence": float(y[test].mean()),
        "approaches": {},
    }
    for name, p in preds.items():
        out["approaches"][name] = summarise(y[test], p[test], groups[test], reps)
    people = [
        g
        for g in np.unique(groups[test])
        if 0 < y[test & (groups == g)].sum() < (test & (groups == g)).sum()
    ]
    out["random_within_pr_auc"] = random_pr_level(y[test], groups[test], people)
    pr, gl = per_person(y[test], preds["Personal RF"][test], groups[test]), per_person(
        y[test], global_oof[test], groups[test]
    )
    d = pr[:, 0] - gl[:, 0]
    out["personal_minus_global_within_roc"] = {
        "mean": float(d.mean()),
        "ci": [
            float(v)
            for v in np.percentile(
                [
                    np.random.default_rng(i).choice(d, len(d)).mean()
                    for i in range(reps)
                ],
                [2.5, 97.5],
            )
        ],
        "wilcoxon_p": float(stats.wilcoxon(d).pvalue),
        "personal_better": int((d > 0).sum()),
        "n": int(len(d)),
    }
    out["base_rate_stability_r"] = float(
        np.corrcoef(
            [y[train & (groups == g)].mean() for g in np.unique(groups)],
            [y[test & (groups == g)].mean() for g in np.unique(groups)],
        )[0, 1]
    )
    return out, preds, test


# -------------------------------------------------------- 4. descriptive statistics
def icc1(values, groups):
    d = pd.DataFrame({"y": values, "g": groups})
    k, n = d.g.nunique(), len(d)
    grp = d.groupby("g")["y"].agg(["mean", "size"])
    msb = (grp["size"] * (grp["mean"] - d.y.mean()) ** 2).sum() / (k - 1)
    msw = ((d.y - d.groupby("g")["y"].transform("mean")) ** 2).sum() / (n - k)
    n0 = (n - (grp["size"] ** 2).sum() / n) / (k - 1)
    return float((msb - msw) / (msb + (n0 - 1) * msw))


def within_difference(df, flag, reps=5000, min_n=5):
    """Mean of (rate when flag) - (rate otherwise) inside each person who has
    at least min_n check-ins in both groups."""
    t = df.groupby(["pid", flag])["high_gap"].agg(["mean", "size"]).unstack()
    t = t[(t[("size", True)] >= min_n) & (t[("size", False)] >= min_n)]
    d = (t[("mean", True)] - t[("mean", False)]).values
    ci = np.percentile(
        [np.random.default_rng(i).choice(d, len(d)).mean() for i in range(reps)],
        [2.5, 97.5],
    )
    return {
        "mean": float(d.mean()),
        "ci": [float(v) for v in ci],
        "higher": int((d > 0).sum()),
        "n": int(len(d)),
        "wilcoxon_p": float(stats.wilcoxon(d).pvalue),
    }


def wilson(k, n, z=1.96):
    p = k / n
    c = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    m = (p + z * z / (2 * n)) / (1 + z * z / n)
    return m - c, m + c


def describe(raw, df):
    y = df["high_gap"]
    night = df["esm_hour"].between(0, 5)
    dup = raw[raw.duplicated(keep="first")]
    per = (
        df.groupby("pid")["high_gap"]
        .agg(["sum", "size", "mean"])
        .sort_values("sum", ascending=False)
    )
    days = (
        pd.to_datetime(df["date"])
        .groupby(df["pid"])
        .agg(lambda s: (s.max() - s.min()).days + 1)
    )
    hourly = df.groupby("esm_hour")["high_gap"].agg(["sum", "size"])
    cats = (
        df.assign(cat=df["Category_L1"].fillna("Not recorded"))
        .groupby("cat")["high_gap"]
        .agg(["sum", "size"])
    )
    rules = {
        "Night (00:00-05:59)": night,
        "Social-media app open": df["genre_Social"].astype(bool),
        "Session longer than 10 min": df["session_minutes"] > 10,
        "Screen time today over 3 h": df["screen_time_minutes"] > 180,
    }
    rules["Any of the first three"] = (
        rules["Night (00:00-05:59)"]
        | rules["Social-media app open"]
        | rules["Session longer than 10 min"]
    )
    inter = INTERACTION
    return {
        "rows_released": int(len(raw)),
        "rows_unique": int(len(df)),
        "duplicate_rows": int(len(dup)),
        "duplicate_people": int(dup["pid"].nunique()),
        "participants": int(df["pid"].nunique()),
        "sessions": int(df["session_id_combined"].nunique()),
        "rows_per_person": [
            int(per["size"].min()),
            float(per["size"].median()),
            int(per["size"].max()),
        ],
        "days_per_person": [int(days.min()), float(days.median()), int(days.max())],
        "date_range": [
            str(pd.to_datetime(df["date"]).min().date()),
            str(pd.to_datetime(df["date"]).max().date()),
        ],
        "high_gap_n": int(y.sum()),
        "high_gap_rate": float(y.mean()),
        "high_gap_rate_released": float(
            ((raw["answer"] <= 5) & (raw["remaining_minutes"] > 5)).mean()
        ),
        "answer_10_share": float((df["answer"] == 10).mean()),
        "answer_le5_share": float((df["answer"] <= 5).mean()),
        "remaining_median_min": float(df["remaining_minutes"].median()),
        "remaining_max_min": float(df["remaining_minutes"].max()),
        "remaining_over_128_share": float((df["remaining_minutes"] > 128).mean()),
        "night": {
            "n": int(night.sum()),
            "rate": float(y[night].mean()),
            "rest_rate": float(y[~night].mean()),
        },
        "paper_night_22_06_rate": float(
            y[(df["esm_hour"] >= 22) | (df["esm_hour"] < 6)].mean()
        ),
        "afternoon_12_18_rate": float(y[df["esm_hour"].between(12, 17)].mean()),
        "hourly": {
            int(h): {
                "k": int(r["sum"]),
                "n": int(r["size"]),
                "ci": list(map(float, wilson(r["sum"], r["size"]))),
            }
            for h, r in hourly.iterrows()
        },
        "categories": {
            c: {"k": int(r["sum"]), "n": int(r["size"])} for c, r in cats.iterrows()
        },
        "icc": {
            "gap_continuous": icc1(df["intention_behavior_gap"], df["pid"]),
            "answer": icc1(df["answer"], df["pid"]),
            "high_gap_binary": icc1(y, df["pid"]),
        },
        "per_person_rate": sorted(map(float, per["mean"])),
        "per_person_n": [int(v) for v in per.sort_values("mean")["size"]],
        "per_person_rate_median": float(per["mean"].median()),
        "people_without_high_gap": int((per["sum"] == 0).sum()),
        "share_of_high_gap_top1_top3_top10": [
            float(per["sum"].head(k).sum() / y.sum()) for k in (1, 3, 10)
        ],
        "top1_rows_and_rate": [int(per["size"].iloc[0]), float(per["mean"].iloc[0])],
        "rate_without_top1": float(
            df.loc[df["pid"] != per.index[0], "high_gap"].mean()
        ),
        "gender_rates": {
            "women": float(y[df["Gender_encoded"] == 0].mean()),
            "men": float(y[df["Gender_encoded"] == 1].mean()),
        },
        "within_night": within_difference(df.assign(f=night), "f"),
        "within_social": within_difference(
            df.assign(f=df["genre_Social"].astype(bool)), "f"
        ),
        "missing": {
            "app_category": int(df["Category_L1"].isna().sum()),
            "app_durations": int(df["app_duration"].isna().sum()),
            "activity": int(df["activity_type"].isna().sum()),
            "interaction_cells": int(df[inter].isna().sum().sum()),
            "zero_interaction_share": float(
                df[
                    [
                        "tap_count",
                        "text_edit_count",
                        "scroll_down_count",
                        "scroll_up_count",
                        "scroll_left_count",
                        "scroll_right_count",
                    ]
                ]
                .eq(0)
                .all(axis=1)
                .mean()
            ),
        },
        "median_taps_short_vs_long_sessions": [
            float(df.loc[df["session_minutes"] <= 0.5, "tap_count"].median()),
            float(df.loc[df["session_minutes"] > 10, "tap_count"].median()),
        ],
        "app_duration_exceeds_elapsed": {
            "rows": int(
                (df["app_total_duration_session"] > df["time_since_unlock"] + 1).sum()
            ),
            "people": int(
                df.loc[
                    df["app_total_duration_session"] > df["time_since_unlock"] + 1,
                    "pid",
                ].nunique()
            ),
        },
        "rules": {
            k: {
                "flagged": float(v.mean()),
                "precision": float(y[v].mean()),
                "recall": float(y[v].sum() / y.sum()),
            }
            for k, v in rules.items()
        },
    }


# -------------------------------------------------------------------------- 5. main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("out_dir")
    ap.add_argument(
        "--quick",
        action="store_true",
        help="skip importance and the demographics extras",
    )
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw, df = load(args.csv)
    y, groups = df["high_gap"].values, df["pid"].values
    X = build_features(df).values
    res = {"data": describe(raw, df), "n_features": len(FEATURES), "features": FEATURES}
    reps = 300 if args.quick else 1000
    print(
        f"{len(raw)} rows -> {len(df)} unique; {len(FEATURES)} features; "
        f"high-gap {y.mean():.3f}",
        flush=True,
    )

    # New users (leave-one-participant-out)
    models = make_models()
    oof = {name: lopo(m, X, y, groups) for name, m in models.items()}
    if not args.quick:
        Xd = build_features(df, demographics=True).values
        oof["RF + demographics"] = lopo(models["RF"], Xd, y, groups)
        oof["LR + demographics"] = lopo(models["LR"], Xd, y, groups)
    rule = (
        df["esm_hour"].between(0, 5)
        | df["genre_Social"].astype(bool)
        | (df["session_minutes"] > 10)
    ).values
    res["global"] = {name: summarise(y, s, groups, reps) for name, s in oof.items()}
    res["global"]["Fixed rule (night, social or > 10 min)"] = summarise(
        y, rule.astype(float), groups, reps
    )
    alert = rule.mean()  # same alert rate as the rule
    res["alert_rate"] = float(alert)
    res["at_alert_rate"] = {}
    for name, s in list(oof.items()) + [("Fixed rule", rule.astype(float))]:
        flag = s >= np.quantile(s, 1 - alert) if name != "Fixed rule" else rule
        tp, fp = int((flag & (y == 1)).sum()), int((flag & (y == 0)).sum())
        fn, tn = int((~flag & (y == 1)).sum()), int((~flag & (y == 0)).sum())
        res["at_alert_rate"][name] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "flagged": float(flag.mean()),
            "precision": tp / max(tp + fp, 1),
            "recall": tp / (tp + fn),
        }
    print(
        "global done",
        {k: round(v["roc_auc"], 3) for k, v in res["global"].items()},
        flush=True,
    )

    # 5-fold participant split, with and without demographics (same random forest)
    if not args.quick:
        Xd = build_features(df, demographics=True).values
        res["groupkfold5"] = {}
        for name, XX in [("RF", X), ("RF + demographics", Xd)]:
            rocs, prs = [], []
            for tr, te in GroupKFold(n_splits=5).split(XX, y, groups):
                s = clone(models["RF"]).fit(XX[tr], y[tr]).predict_proba(XX[te])[:, 1]
                rocs.append(roc_auc_score(y[te], s)), prs.append(
                    average_precision_score(y[te], s)
                )
            res["groupkfold5"][name] = {
                "roc_auc": [float(np.mean(rocs)), float(np.std(rocs))],
                "pr_auc": [float(np.mean(prs)), float(np.std(prs))],
            }
        rf = clone(models["RF"]).fit(Xd, y)[-1]
        imp = pd.Series(rf.feature_importances_, index=FEATURES + DEMOGRAPHICS)
        res["gini_share_demographics"] = float(imp[DEMOGRAPHICS].sum())
        res["gini_top3_with_demographics"] = (
            imp.sort_values(ascending=False).head(3).round(3).to_dict()
        )

    # Known users (chronological 70/30), every approach scored on the same test rows
    res["personal"], ppreds, test = personal_regime(
        df, X, y, groups, oof["RF"], models["RF"], reps, xgb_model=models["XGB"]
    )
    print(
        "personal done",
        {k: round(v["roc_auc"], 3) for k, v in res["personal"]["approaches"].items()},
        flush=True,
    )

    # Which features does the main model use? Permutation importance, held-out people.
    if not args.quick:
        names = FEATURES
        drops = np.zeros(len(names))
        for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
            m = clone(models["RF"]).fit(X[tr], y[tr])
            pi = permutation_importance(
                m, X[te], y[te], scoring="roc_auc", n_repeats=5, random_state=0
            )
            drops += pi.importances_mean / 5
        imp = pd.Series(drops, index=names).sort_values(ascending=False)
        res["permutation_importance_top15"] = [
            {"feature": f, "group": GROUP_OF[f], "auc_drop": float(v)}
            for f, v in imp.head(15).items()
        ]
        res["permutation_importance_by_group"] = (
            imp.groupby(lambda f: GROUP_OF[f])
            .sum()
            .sort_values(ascending=False)
            .to_dict()
        )

    pd.DataFrame(
        {
            "y": y,
            "test_chrono": test,
            **{f"global::{k}": v for k, v in oof.items()},
            **{f"personal::{k}": v for k, v in ppreds.items()},
        }
    ).to_csv(out / "predictions.csv", index=False)
    (out / "results.json").write_text(
        json.dumps(res, indent=1, default=float), encoding="utf-8"
    )
    print("wrote", out / "results.json")


if __name__ == "__main__":
    main()
