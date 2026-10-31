"""Figures for the corrected milestone-4 report, in the milestone-2 chart style.

usage: python -I make_figures.py <results.json> <predictions.csv> <figures_dir>
"""

import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve

res = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
pred = pd.read_csv(sys.argv[2])
FIG = Path(sys.argv[3])
FIG.mkdir(parents=True, exist_ok=True)
D = res["data"]
HG = D["high_gap_rate"] * 100

# milestone-2 chart tokens
SURFACE = "#ffffff"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, GRAY, GREEN = "#2a78d6", "#eb6834", "#c3c2b7", "#7a9e3e"
mpl.rcParams.update(
    {
        "font.family": "Segoe UI",
        "font.size": 8.5,
        "axes.titlesize": 9.5,
        "axes.titleweight": "semibold",
        "axes.titlecolor": INK,
        "axes.labelcolor": INK2,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2,
        "axes.edgecolor": BASELINE,
        "axes.linewidth": 0.8,
        "axes.facecolor": SURFACE,
        "figure.facecolor": SURFACE,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "grid.linestyle": "-",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.facecolor": SURFACE,
    }
)


def wilson(k, n, z=1.96):
    k, n = np.asarray(k, float), np.asarray(n, float)
    p = k / n
    den = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return c - h, c + h


def rounded_bars(ax, positions, values, color, horizontal=False, thickness=0.6, radius_px=4):
    ax.figure.canvas.draw()
    inv = ax.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform([(0, 0), (radius_px, radius_px)])
    rx, ry = abs(x1 - x0), abs(y1 - y0)
    colors = list(color) if isinstance(color, (list, tuple, np.ndarray)) else [color] * len(values)
    for pos, val, c in zip(positions, values, colors):
        if val <= 0:
            continue
        if horizontal:
            box, square = ((0, pos - thickness / 2), val, thickness), (
                (0, pos - thickness / 2),
                max(val - rx, 0),
                thickness,
            )
        else:
            box, square = ((pos - thickness / 2, 0), thickness, val), (
                (pos - thickness / 2, 0),
                thickness,
                max(val - ry, 0),
            )
        ax.add_patch(
            FancyBboxPatch(
                *box,
                boxstyle=f"round,pad=0,rounding_size={rx}",
                mutation_aspect=ry / rx,
                facecolor=c,
                edgecolor="none",
                linewidth=0,
            )
        )
        ax.add_patch(Rectangle(*square, facecolor=c, edgecolor="none", linewidth=0))


def hour_label(h):
    return "12 am" if h == 0 else f"{h} am" if h < 12 else "12 pm" if h == 12 else f"{h - 12} pm"


# ---------------------------------------------------------------- Figure 1: hour of day
hour = pd.DataFrame(D["hourly"]).T
hour.index = hour.index.astype(int)
hour = hour.sort_index()
hour["pct"] = hour["k"] / hour["n"] * 100
lo, hi = wilson(hour["k"], hour["n"])
fig, ax = plt.subplots(figsize=(6.5, 2.6), layout="constrained")
ax.fill_between(hour.index, lo * 100, hi * 100, color=BLUE, alpha=0.10, linewidth=0)
ax.plot(hour.index, hour.pct, color=BLUE, linewidth=2, solid_joinstyle="round", solid_capstyle="round")
ax.plot(hour.index, hour.pct, "o", color=BLUE, markersize=5.5, markeredgecolor=SURFACE, markeredgewidth=1.5)
ax.axhline(HG, color=INK2, linewidth=0.8)
ax.text(12, HG + 1.0, f"all hours {HG:.1f}%", ha="center", va="bottom", color=INK2)
peak = int(hour.pct.idxmax())
ax.annotate(
    f"{hour_label(peak)}: {hour.pct.max():.0f}% (n = {int(hour.loc[peak, 'n'])})",
    xy=(peak, hour.pct.max()),
    xytext=(peak + 1.6, hour.pct.max() + 4),
    color=INK2,
    arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8),
)
ax.set_xlim(-0.5, 23.5)
ax.set_ylim(0, hi.max() * 100 * 1.05)
ax.set_xticks(range(0, 24, 3))
ax.set_xticklabels([hour_label(h) for h in range(0, 24, 3)])
ax.yaxis.grid(True)
ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.set_title("High-gap moments by hour of day (band: 95% confidence interval)", loc="left")
ax.set_xlabel("hour of the check-in (participant's local time)")
ax.set_ylabel("% high-gap moments")
fig.savefig(FIG / "fig1_by_hour.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 2: app category
names = {
    "Message": "Messaging",
    "Social": "Social media",
    "Work & Study": "Work & study",
    "Browser": "Browser",
    "Daily Life": "Daily life",
    "Media": "Media & video",
    "System tool": "System tools",
    "Game": "Games",
    "To exclude": "Calls, camera, launcher",
    "Not recorded": "App not recorded",
}
technical = {"To exclude", "Not recorded"}
cat = pd.DataFrame(D["categories"]).T
cat["pct"] = cat["k"] / cat["n"] * 100
cat = cat.sort_values("pct")
fig, ax = plt.subplots(figsize=(6.5, 3.1), layout="constrained")
yy = np.arange(len(cat))
ax.set_ylim(-0.6, len(cat) - 0.4)
ax.set_xlim(0, cat.pct.max() * 1.2)
ax.set_yticks(yy)
ax.set_yticklabels([f"{names.get(i, i)}  (n = {int(n):,})" for i, n in zip(cat.index, cat.n)])
ax.tick_params(axis="y", length=0)
ax.xaxis.grid(True)
ax.set_axisbelow(True)
ax.spines["bottom"].set_visible(False)
ax.tick_params(axis="x", length=0)
rounded_bars(
    ax,
    yy,
    cat.pct.values,
    [GRAY if i in technical else BLUE for i in cat.index],
    horizontal=True,
    thickness=0.62,
)
for y_, v in zip(yy, cat.pct):
    ax.text(v + 0.35, y_, f"{v:.1f}%", va="center", color=INK2)
ax.legend(
    handles=[Patch(color=BLUE, label="app category"), Patch(color=GRAY, label="not an app genre")],
    loc="lower right",
    handlelength=1.0,
)
fig.suptitle(
    f"High-gap moments by the app in use at the check-in (all apps: {HG:.1f}%)",
    x=0.01,
    ha="left",
    fontsize=9.5,
    fontweight="semibold",
    color=INK,
)
ax.set_xlabel("% high-gap moments (pooled over people)")
fig.savefig(FIG / "fig2_by_app_category.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 3: per participant
rate = np.array(D["per_person_rate"])
n = np.array(D["per_person_n"])
k = np.round(rate * n)
lo, hi = wilson(k, n)
fig, ax = plt.subplots(figsize=(6.5, 2.7), layout="constrained")
x = np.arange(len(rate))
ax.vlines(x, lo * 100, hi * 100, color=GRAY, linewidth=1.2)
ax.plot(
    x, rate * 100, "o", color=BLUE, markersize=5.5, markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3
)
ax.axhline(HG, color=INK2, linewidth=0.8)
ax.text(0, HG + 1.5, f"all check-ins pooled {HG:.1f}%", va="bottom", color=INK2)
med = D["per_person_rate_median"] * 100
ax.axhline(med, color=INK2, linewidth=0.8, linestyle=(0, (3, 3)))
ax.text(len(rate) - 1, med - 1.5, f"median participant {med:.1f}%", ha="right", va="top", color=INK2)
ax.annotate(
    f"{rate[-1] * 100:.0f}%",
    xy=(x[-1], rate[-1] * 100),
    xytext=(x[-1] - 2.2, rate[-1] * 100 - 3),
    color=INK2,
    va="center",
)
ax.set_xlim(-1, len(rate))
ax.set_ylim(0, 100)
ax.set_xticks([])
ax.yaxis.grid(True)
ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.set_title("Each participant's share of high-gap moments", loc="left")
ax.set_xlabel(f"{len(rate)} participants, sorted (whiskers: 95% confidence interval)", labelpad=8)
ax.set_ylabel("% high-gap moments")
fig.savefig(FIG / "fig3_per_participant.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 4: ROC and PR, new users (LOPO)
y = pred["y"].values
curves = [
    ("LR", "Logistic regression", BLUE, "-"),
    ("XGB", "XGBoost", INK2, "-"),
    ("LGBM", "LightGBM", GREEN, "-"),
    ("RF", "Random forest", ORANGE, "-"),
    ("RF + demographics", "Random forest + demographics", ORANGE, (0, (2, 2))),
]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 3.0), layout="constrained")
for key, label, col, ls in curves:
    s = pred[f"global::{key}"].values
    fpr, tpr, _ = roc_curve(y, s)
    p, r, _ = precision_recall_curve(y, s)
    a1.plot(fpr, tpr, color=col, linestyle=ls, linewidth=1.6, label=f"{label} ({roc_auc_score(y, s):.2f})")
    a2.plot(
        r, p, color=col, linestyle=ls, linewidth=1.6, label=f"{label} ({average_precision_score(y, s):.2f})"
    )
rule = res["at_alert_rate"]["Fixed rule"]
fpr_rule = rule["fp"] / (rule["fp"] + rule["tn"])
a1.plot([fpr_rule], [rule["recall"]], "s", color=INK, markersize=5, label="Fixed rule (one point)")
a2.plot([rule["recall"]], [rule["precision"]], "s", color=INK, markersize=5, label="Fixed rule (one point)")
a1.plot([0, 1], [0, 1], color=BASELINE, linewidth=0.8)
a2.axhline(y.mean(), color=BASELINE, linewidth=0.8)
a2.text(
    0.99,
    y.mean() - 0.012,
    f"chance = prevalence {y.mean():.3f}",
    ha="right",
    va="top",
    color=MUTED,
    fontsize=7.5,
)
a1.set_title("ROC curve (pooled ROC-AUC)", loc="left")
a2.set_title("Precision-recall curve (PR-AUC)", loc="left")
a1.set_xlabel("false-positive rate")
a1.set_ylabel("true-positive rate (recall)")
a2.set_xlabel("recall")
a2.set_ylabel("precision")
a2.set_ylim(0, 0.7)
for a in (a1, a2):
    a.grid(True)
    a.set_axisbelow(True)
    a.legend(loc="lower right" if a is a1 else "upper right", fontsize=7)
fig.savefig(FIG / "fig4_roc_pr_new_users.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 5: known users, same test rows
P = res["personal"]["approaches"]
order = [
    "Global (zero-shot)",
    "Personal RF",
    "Personal XGBoost",
    "Combined RF",
    "Own base rate",
    "Global + personal intercept",
]
labels = [
    "Global\nzero-shot",
    "Personal\nRF",
    "Personal\nXGBoost",
    "Combined\nRF",
    "Own\nbase rate",
    "Global +\nintercept",
]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 3.0), layout="constrained")
for a, metric, title, ref, ref_label in [
    (a1, "roc_auc", "Pooled ROC-AUC\n(all test rows together; whiskers: 95% CI)", 0.5, "chance 0.50"),
    (
        a2,
        "within_roc_auc",
        "Within-person ROC-AUC\n(each person's own moments, averaged)",
        0.5,
        "chance 0.50",
    ),
]:
    vals = [P[o][metric] for o in order]
    cis = [P[o][metric + "_ci"] for o in order]
    xx = np.arange(len(order))
    cols = [GRAY] * (len(order) - 1) + [BLUE]
    a.set_ylim(0.4, 1.0)
    a.set_xlim(-0.6, len(order) - 0.4)
    a.bar(xx, np.array(vals) - 0.4, bottom=0.4, color=cols, width=0.6)
    a.vlines(xx, [c[0] for c in cis], [c[1] for c in cis], color=INK2, linewidth=1)
    for x_, v, c in zip(xx, vals, cols):
        a.text(
            x_,
            0.415,
            f"{v:.2f}",
            ha="center",
            va="bottom",
            color=SURFACE if c == BLUE else INK,
            fontsize=7.5,
            fontweight="semibold",
        )
    a.axhline(ref, color=INK2, linewidth=0.8, linestyle=(0, (3, 3)))
    a.set_xticks(xx)
    a.set_xticklabels(labels, fontsize=7)
    a.set_title(title, loc="left", fontsize=8.5)
    a.yaxis.grid(True)
    a.set_axisbelow(True)
    a.tick_params(axis="x", length=0)
fig.savefig(FIG / "fig5_known_users_same_rows.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 6: same alert rate, fixed rule vs best model
best = max(["LR", "RF", "XGB", "LGBM"], key=lambda m: res["global"][m]["roc_auc"])
fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.6), layout="constrained")
for a, key, title in [
    (axes[0], "Fixed rule", "Fixed rule (night, social or > 10 min)"),
    (
        axes[1],
        best,
        {"LR": "Logistic regression", "RF": "Random forest", "XGB": "XGBoost", "LGBM": "LightGBM"}[best],
    ),
]:
    c = res["at_alert_rate"][key]
    m = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
    a.imshow(
        m / m.sum(), cmap=mpl.colors.LinearSegmentedColormap.from_list("b", [SURFACE, BLUE]), vmin=0, vmax=0.8
    )
    for i in range(2):
        for j in range(2):
            a.text(
                j,
                i,
                f"{m[i, j]:,}",
                ha="center",
                va="center",
                color=INK if m[i, j] / m.sum() < 0.45 else SURFACE,
                fontsize=10,
            )
    a.set_xticks([0, 1])
    a.set_xticklabels(["no alert", "alert"])
    a.set_yticks([0, 1])
    a.set_yticklabels(["not high-gap", "high-gap"])
    a.set_title(
        f"{title}\nflags {c['flagged'] * 100:.1f}%: precision {c['precision'] * 100:.1f}%, recall {c['recall'] * 100:.1f}%",
        loc="left",
        fontsize=8,
    )
    for s in a.spines.values():
        s.set_visible(False)
    a.tick_params(length=0)
fig.savefig(FIG / "fig6_same_alert_rate.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 7: permutation importance
if "permutation_importance_top15" in res:
    imp = pd.DataFrame(res["permutation_importance_top15"]).iloc[::-1]
    gcol = {
        "time": BLUE,
        "current session": ORANGE,
        "earlier use today": INK2,
        "recent interaction": "#7a9e3e",
        "app and activity": GRAY,
    }
    pretty = {
        "hour_sin": "hour of day (sine)",
        "hour_cos": "hour of day (cosine)",
        "weekday_sin": "weekday (sine)",
        "weekday_cos": "weekday (cosine)",
        "app_total_duration_session": "time in current app, this session",
        "last_session_duration": "length of previous session",
        "time_period_night": "night (22:00-06:00)",
        "app_duration": "time in current app, this visit",
        "interval_after_last_session": "time since previous session",
        "genre_Work & Study": "work & study app",
        "screen_time_minutes": "screen time today",
        "app_total_duration_today": "time in current app, today",
        "unique_apps_today": "distinct apps today",
        "session_minutes": "session length so far",
        "tap_count": "taps (recent)",
        "app_switches_in_session": "app switches, this session",
        "genre_System tool": "system-tool app",
        "prev_session_avg_duration_today": "mean earlier session length today",
        "prev_session_count_today": "earlier sessions today",
        "unique_apps_in_session": "distinct apps, this session",
        "genre_Social": "social-media app",
        "genre_Media": "media & video app",
        "genre_Message": "messaging app",
        "esm_is_workday": "workday",
        "esm_is_weekend": "weekend",
        "app_switches_today": "app switches today",
        "text_edit_count": "text edits (recent)",
        "activity_still": "phone still",
        "app_missing": "app not recorded",
    }
    fig, ax = plt.subplots(figsize=(6.5, 3.3), layout="constrained")
    yy = np.arange(len(imp))
    ax.set_ylim(-0.6, len(imp) - 0.4)
    ax.set_xlim(0, max(imp.auc_drop.max() * 1.25, 0.005))
    ax.set_yticks(yy)
    ax.set_yticklabels([pretty.get(f, f) for f in imp.feature])
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    rounded_bars(
        ax,
        yy,
        imp.auc_drop.clip(lower=0).values,
        [gcol[g] for g in imp.group],
        horizontal=True,
        thickness=0.62,
    )
    for y_, v in zip(yy, imp.auc_drop):
        ax.text(max(v, 0) + imp.auc_drop.max() * 0.02, y_, f"{v:.3f}", va="center", color=INK2, fontsize=7.5)
    ax.legend(
        handles=[Patch(color=c, label=g) for g, c in gcol.items()],
        loc="lower right",
        handlelength=1.0,
        fontsize=7.5,
    )
    fig.suptitle(
        "Random forest: drop in ROC-AUC when a feature is shuffled (held-out participants)",
        x=0.01,
        ha="left",
        fontsize=9.5,
        fontweight="semibold",
        color=INK,
    )
    ax.set_xlabel("mean drop in ROC-AUC (5 participant folds x 5 shuffles)")
    fig.savefig(FIG / "fig7_permutation_importance.png")
    plt.close(fig)

print("figures written to", FIG)
