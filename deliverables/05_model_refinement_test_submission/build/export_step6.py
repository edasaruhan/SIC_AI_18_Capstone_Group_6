"""Export Step 6 tables and report figures from verified aggregate JSON."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, PercentFormatter
import numpy as np

BUILD = Path(__file__).resolve().parent
LABELS = {
    "fixed_LR": "Fixed logistic regression",
    "fixed_RF": "Fixed random forest",
    "fixed_baseline_selector": "Fixed baseline",
    "refined_selector": "Refined procedure",
    "population_prior": "Excluded-fold prevalence",
    "fixed_rule": "Fixed three-signal rule",
    "global": "Global model",
    "personal_rate": "Personal base rate",
    "global_plus_daily_personal_offset": "Daily personal offset",
}
BLUE, GREEN, GRAY = "#2A568C", "#087F75", "#697486"
POINT = {"fixed_baseline_selector": (BLUE, "o"), "refined_selector": (GREEN, "s"),
         "global": (GRAY, "^"), "personal_rate": (BLUE, "o"),
         "global_plus_daily_personal_offset": (GREEN, "s")}
METRICS = ("rows", "people", "positives", "prevalence", "pooled_AP", "pooled_ROC_AUC",
           "participant_balanced_AP", "pooled_Brier", "participant_balanced_Brier",
           "pooled_log_loss", "participant_balanced_log_loss")
OPERATING = ("tp", "fp", "fn", "tn", "precision", "recall", "actual_alert_share")
FIXED_METHODS = ("fixed_baseline_selector", "refined_selector")
DAILY_METHODS = ("global", "personal_rate", "global_plus_daily_personal_offset")


def metrics_row(summary):
    record = {key: summary.get(key) for key in METRICS}
    for within in ("within_person", "within_person_day"):
        for key in ("mean_AP", "mean_ROC_AUC", "eligible_units", "total_units", "eligible_people"):
            record[f"{within}_{key}"] = summary.get(within, {}).get(key)
    decision = summary.get("decisions", summary)
    record.update({key: decision.get(key) for key in OPERATING})
    return record


def export_csv(path, selection, evaluation):
    rows = []
    for fold in selection["folds"]:
        for method, stages in fold["stage_diagnostics"].items():
            for stage, summary in stages.items():
                rows.append(dict(regime="new_user", stage=stage, fold=fold["outer_fold"] + 1,
                                 method=method, **metrics_row(summary)))
    for regime in ("new_user", "known_user"):
        for method, summary in evaluation[regime].items():
            metrics = metrics_row(summary)
            if method == "fixed_rule":
                metrics["rows"] = sum(summary[k] for k in ("tp", "fp", "fn", "tn"))
                metrics["positives"] = summary["tp"] + summary["fn"]
                metrics["people"] = evaluation[regime]["refined_selector"]["people"]
                metrics["prevalence"] = metrics["positives"] / metrics["rows"]
            rows.append(dict(regime=regime, stage="outer_held_out" if regime == "new_user" else "day_forward",
                             fold="", method=method, **metrics))
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def format_axis(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dce4ec", linewidth=.7)
    ax.set_axisbelow(True)


def reliability(ax, results, methods, upper):
    ax.plot([0, upper], [0, upper], linestyle="--", color="#8f9caa", linewidth=1.1,
            label="Perfect agreement")
    for method in methods:
        bins = [b for b in results[method]["reliability"] if b["rows"]]
        color, marker = POINT[method]
        ax.plot([b["mean_probability"] for b in bins], [b["observed_rate"] for b in bins],
                label=LABELS[method], color=color, marker=marker, linewidth=1.6, markersize=5)
    ax.set(xlim=(-.02, upper + .025), ylim=(-.02, upper + .025), xlabel="Mean predicted probability",
           ylabel="Observed outcome rate", title="Reliability by probability bin")
    ax.set_xticks(np.linspace(0, upper, 6))
    ax.set_yticks(np.linspace(0, upper, 6))
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    format_axis(ax)


def save(fig, file, caption, *, left=.10, bottom=.24):
    fig.text(.04, .04, caption, fontsize=9, color="#435366", va="bottom")
    fig.subplots_adjust(left=left, right=.97, bottom=bottom, top=.80, wspace=.36)
    fig.savefig(file, dpi=240, facecolor="white")
    plt.close(fig)


def new_user_figure(directory, result):
    data = result["new_user"]
    fig, (ax, cal) = plt.subplots(1, 2, figsize=(11.1, 4.7))
    fig.suptitle("New-user evaluation on held-out participants", x=.04, ha="left", weight="bold", fontsize=17)
    ax.axhline(data["refined_selector"]["prevalence"], ls="--", lw=1, color=GRAY, label="Outcome prevalence")
    for method in FIXED_METHODS:
        metrics = data[method]
        color, marker = POINT[method]
        points = [p for p in metrics["decision_curve_grid"] if p["tp"] + p["fp"]]
        ax.plot([p["recall"] for p in points], [p["precision"] for p in points],
                color=color, lw=1.6, label=LABELS[method])
        decision = metrics["decisions"]
        ax.scatter(decision["recall"], decision["precision"], marker=marker, color=color,
                   s=55, zorder=4, edgecolors="white", linewidths=.8)
    decision = data["fixed_rule"]
    ax.scatter(decision["recall"], decision["precision"], marker="D", color="#9a5528",
               s=32, zorder=4, label="Fixed rule")
    ax.set(xlim=(0, 1.02), ylim=(0, 1.03), xlabel="Recall", ylabel="Precision", title="Precision and recall")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    format_axis(ax)
    reliability(cal, data, FIXED_METHODS, 1)
    save(fig, directory / "step6_new_user.png",
         "5,627 check-ins from 37 participants. Lines on the left use the fixed score grid. Markers show saved cutoffs and the rule.\n"
         "Reliability gives each participant equal total weight. Source: NudgeWell HW5, frozen protocol v1.0.0.")


def known_user_figure(directory, result):
    data = result["known_user"]
    fig, (ax, cal) = plt.subplots(1, 2, figsize=(11.1, 4.7))
    fig.suptitle("Daily personalization on matched check-ins", x=.04, ha="left", weight="bold", fontsize=17)
    metric_values = lambda m: [data[m]["pooled_ROC_AUC"], data[m]["within_person"]["mean_ROC_AUC"],
                               data[m]["within_person_day"]["mean_ROC_AUC"]]
    for method, offset in zip(DAILY_METHODS, (-.19, 0, .19)):
        color, marker = POINT[method]
        ax.scatter(metric_values(method), np.arange(3) + offset, color=color, marker=marker,
                   label=LABELS[method], s=50, zorder=3)
    ax.axvline(.5, color=GRAY, lw=1, linestyle="--")
    ax.set(xlim=(.30, 1.0), ylim=(2.5, -.6), xlabel="ROC-AUC", title="Ranking across and within people")
    ax.set_yticks(range(3), ["Pooled", "Within person", "Within day"])
    format_axis(ax)
    reliability(cal, data, DAILY_METHODS, 1)
    save(fig, directory / "step6_daily_personalization.png",
         "3,772 check-ins from 37 participants. Within-person ranking uses 29 people. Within-day ranking uses 150 participant-days.\n"
         "Colors and symbols apply to both panels. Reliability gives each participant equal total weight. Source: frozen HW5 v1.0.0.",
         left=.135)


def contrast_figure(directory, result):
    fig, axs = plt.subplots(1, 2, figsize=(11.1, 3.35))
    fig.suptitle("Prespecified comparisons and paired uncertainty", x=.04, ha="left", weight="bold", fontsize=17)
    items = [
        ("primary_contrast", "New users", "AP gain over the fixed baseline"),
        ("secondary_prespecified_contrast", "Daily personalization", "Brier reduction vs. personal base rate"),
    ]
    for ax, (key, title, label) in zip(axs, items):
        point = result[key]["point_difference"]
        lower, upper = result[key]["interval"]
        padding = (max(0, upper) - min(0, lower)) * .15
        ax.axvline(0, color=GRAY, linestyle="--", linewidth=1)
        ax.errorbar([point], [0], xerr=[[point-lower], [upper-point]], fmt="o", color=GREEN,
                    capsize=5, linewidth=2, markersize=7)
        ax.set(xlim=(min(lower, 0) - padding, max(upper, 0) + padding), ylim=(-.45, .48),
               yticks=[], title=title, xlabel=label)
        ax.annotate(f"{point:+.4f}  [{lower:+.4f}, {upper:+.4f}]", (point, .20),
                    ha="center", fontsize=10, color="#223344",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 2})
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.ticklabel_format(axis="x", style="plain", useOffset=False)
    save(fig, directory / "step6_paired_contrasts.png",
         "Positive values favor the refinement. Intervals use 2,000 paired participant resamples of saved predictions.\n"
         "Models were kept fixed during resampling. Source: NudgeWell HW5, frozen protocol v1.0.0.",
         bottom=.32)


def main(run_id):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("Invalid experiment run ID")
    root = BUILD / "results"
    evaluation_file = root / f"{run_id}_evaluation.json"
    expected = json.loads((root / f"{run_id}_verification.json").read_text(encoding="utf-8"))
    if hashlib.sha256(evaluation_file.read_bytes()).hexdigest() != expected["evaluation_sha256"]:
        raise ValueError("Aggregate evaluation differs from the verified output")
    evaluation = json.loads(evaluation_file.read_text(encoding="utf-8"))
    selection = json.loads((root / f"{run_id}_selection.json").read_text(encoding="utf-8"))
    if (selection["run_id"] != run_id or evaluation["run_id"] != run_id
            or selection["protocol_sha256"] != evaluation["protocol_sha256"]
            or selection["code_sha256"] != evaluation["code_sha256"]):
        raise ValueError("Selection and evaluation provenance differs")
    export_csv(root / f"{run_id}_metrics.csv", selection, evaluation)
    figures = BUILD.parent / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titleweight": "bold",
                         "axes.labelcolor": "#223344", "text.color": "#223344"})
    new_user_figure(figures, evaluation)
    known_user_figure(figures, evaluation)
    contrast_figure(figures, evaluation)
    print("Wrote aggregate CSV and three figures")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    main(parser.parse_args().run_id)
