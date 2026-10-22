"""Draw the concept note's two figures.

Usage (from anywhere):  python -I make_figures.py
Writes ../figures/fig1_architecture.png and ../figures/fig2_gantt.png (300 dpi, 16 cm wide).

Figure 1 is the system architecture: the offline training pipeline (A) and the six on-device components (B).
Figure 2 is the 4-week Gantt chart. PLAN below is the single source for its tasks, owners and dates;
keep the task-distribution matrix (Table 7 in concept_note.md) in step with it.
"""
from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE.parent / "figures"
CM = 1 / 2.54
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 7, "svg.fonttype": "none"})

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"

# Owners in roster order; categorical slots 1-5 of the dataviz reference palette
# (validated: adjacent CVD dE >= 9.1, normal-vision >= 19.6; three slots are below 3:1 contrast,
# so every bar also carries the owner's name in its row label).
OWNERS = {
    "Kara": ("Yusuf Ersel Kara", "#2a78d6"),
    "Maral": ("Bahadır Maral", "#eb6834"),
    "Eryılmaz": ("Çağla Eryılmaz", "#1baf7a"),
    "Menteşe": ("Fatih Mehmet Menteşe", "#eda100"),
    "Öcal": ("Damla Nur Öcal", "#e87ba4"),
}

START = date(2026, 10, 26)  # Monday of week 1
WEEKS = [(START + timedelta(weeks=i), START + timedelta(weeks=i, days=6)) for i in range(4)]


def d(month, day):
    return date(2026, month, day)


# (stage, task, lead's surname, partner's surname or None, first day, last day)
PLAN = [
    ("1. Data preparation", "Licence request to the AwareMind authors", "Maral", None, d(10, 26), d(10, 28)),
    ("1. Data preparation", "TCN and GRU design", "Maral", None, d(10, 27), d(11, 1)),
    ("1. Data preparation", "Leakage audit, cleaning, EDA, features", "Eryılmaz", None, d(10, 26), d(11, 1)),
    ("1. Data preparation", "Target and class-balance analysis", "Kara", None, d(10, 26), d(11, 1)),
    ("1. Data preparation", "Eşik walkthrough, prompt-card design", "Öcal", "Maral", d(10, 26), d(11, 1)),
    ("1. Data preparation", "Pool of short alternative activities", "Menteşe", None, d(10, 26), d(11, 1)),
    ("2. Model development", "TCN and GRU, global variant", "Maral", "Kara", d(11, 2), d(11, 8)),
    ("2. Model development", "Random forest reproduction, XGBoost", "Kara", None, d(11, 2), d(11, 5)),
    ("2. Model development", "LOPO and day-forward splits, baselines", "Eryılmaz", None, d(11, 2), d(11, 8)),
    ("2. Model development", "Preference screens, usage reading, storage", "Öcal", None, d(11, 2), d(11, 8)),
    ("2. Model development", "Prompt and reason templates, consent text", "Menteşe", None, d(11, 2), d(11, 8)),
    ("3. Training and evaluation", "Personal and combined models, learning curve", "Maral", None, d(11, 9), d(11, 15)),
    ("3. Training and evaluation", "Calibration, prompt-budget simulation", "Maral", "Kara", d(11, 11), d(11, 15)),
    ("3. Training and evaluation", "Bootstrap intervals, fairness analysis", "Kara", None, d(11, 11), d(11, 15)),
    ("3. Training and evaluation", "History inputs from earlier check-ins", "Eryılmaz", None, d(11, 9), d(11, 11)),
    ("3. Training and evaluation", "Trigger, cooldown, one-tap dismissal", "Öcal", None, d(11, 9), d(11, 15)),
    ("3. Training and evaluation", "Optional one sec response analysis", "Menteşe", None, d(11, 9), d(11, 15)),
    ("4. Deployment and delivery", "Export to LiteRT / ONNX", "Maral", None, d(11, 16), d(11, 18)),
    ("4. Deployment and delivery", "SHAP reasons", "Kara", None, d(11, 16), d(11, 18)),
    ("4. Deployment and delivery", "On-device integration, tests, demo video", "Öcal", "Maral", d(11, 18), d(11, 22)),
    ("4. Deployment and delivery", "End-to-end scenario tests, demo script", "Menteşe", None, d(11, 18), d(11, 22)),
    ("4. Deployment and delivery", "Ethics checklist, data and ethics sections", "Eryılmaz", None, d(11, 16), d(11, 20)),
    ("4. Deployment and delivery", "Final report, presentation, delivery check", "Maral", None, d(11, 19), d(11, 22)),
]
MILESTONES = [("M1", d(11, 1)), ("M2", d(11, 8)), ("M3", d(11, 15)), ("M4", d(11, 22))]


# ---------- Figure 1: architecture ----------

def box(ax, x, y, w, h, fill, edge, lw=1.0, ls="-", r=0.25):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls))


def arrow(ax, start, end, color=INK2, lw=1.1):
    ax.annotate("", xy=end, xytext=start,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, shrinkA=0, shrinkB=0, mutation_scale=9))


COMPONENTS = [
    # number, title, subtitle, bullets, fill, edge
    (1, "Sensing", "Android app built on Eşik",
     ["usage events (UsageStatsManager)", "time of day, app category", "session length, screen time today",
      "taps, scrolls, physical activity"], "#e3eefb", "#2a78d6"),
    (2, "Feature builder", "same code as in training",
     ["only signals known before the prompt", "'not recorded' flag for missing apps",
      "history of earlier check-ins", "log-scaled, standardized durations"], "#e2f5ec", "#1baf7a"),
    (3, "On-device model", "LiteRT or ONNX Runtime",
     ["compact TCN, under 1 MB", "estimates the gap and the|calibrated high-gap probability",
      "personal recalibration on the phone"], "#ebe8fa", "#6250d6"),
    (4, "Policy and explanation", "decides whether to prompt",
     ["prompt only above the threshold", "at most 3 prompts a day, cooldown",
      "one-line reason from top features", "stays quiet when unsure"], "#fdf3d9", "#c98500"),
    (5, "Prompt card", "Jetpack Compose",
     ["small card over the current app", "one alternative the user chose",
      "one tap to dismiss ('Continue')", "'Stop'/'Continue' kept as feedback"], "#fde9e1", "#eb6834"),
    (6, "Privacy and safety", "KVKK; Yeşilay referral",
     ["opt-in consent; adults (18+) only", "data stay on the phone (Room)",
      "view or delete all data any time", "'Get support': YEDAM and 115"], "#fbe4ea", "#e34948"),
]


def component(ax, x, y, w, h, spec):
    num, title, subtitle, bullets, fill, edge = spec
    box(ax, x, y, w, h, fill, edge, lw=1.1)
    top = y + h - 0.32
    ax.text(x + 0.25, top, str(num), fontsize=13, fontweight="bold", color=edge, va="top", ha="left")
    ax.text(x + 0.85, top - 0.02, title, fontsize=8.2, fontweight="bold", color=INK, va="top", ha="left")
    ax.text(x + 0.85, top - 0.48, subtitle, fontsize=6.6, style="italic", color=INK2, va="top", ha="left")
    line = 0
    for b in bullets:  # a "|" inside a bullet continues it on an indented line
        for j, part in enumerate(b.split("|")):
            ax.text(x + 0.3, top - 1.12 - line * 0.47, ("•  " if j == 0 else "    ") + part, fontsize=6.6,
                    color=INK, va="top", ha="left")
            line += 1


def architecture():
    W, H = 16.0, 12.6
    fig = plt.figure(figsize=(W * CM, H * CM), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    # A. offline lane
    box(ax, 0.15, 10.0, 15.7, 2.45, "#f4f4f2", MUTED, lw=0.9, ls=(0, (4, 3)), r=0.3)
    ax.text(0.45, 12.18, "A.  Offline, before deployment (laptop or Colab)", fontsize=7.6, fontweight="bold",
            color=INK, va="top")
    steps = [("AwareMind data", "5,772 check-ins, 37 adults;", "with the authors' permission"),
             ("Leakage audit, features", "outcome columns removed;", "time-ordered per person"),
             ("Train and evaluate", "RF, XGBoost, TCN, GRU;", "LOPO and day-forward splits"),
             ("Calibrate and export", "threshold, budget, cooldown;", "model file for the phone")]
    gap, x0 = 0.6, 0.45
    sw = (15.55 - x0 - 3 * gap) / 4
    for i, (t, l1, l2) in enumerate(steps):
        x = x0 + i * (sw + gap)
        box(ax, x, 10.25, sw, 1.38, "white", INK2, lw=0.8, r=0.18)
        ax.text(x + sw / 2, 11.43, t, fontsize=7.2, fontweight="bold", color=INK, ha="center", va="top")
        ax.text(x + sw / 2, 11.0, l1, fontsize=6.4, color=INK2, ha="center", va="top")
        ax.text(x + sw / 2, 10.68, l2, fontsize=6.4, color=INK2, ha="center", va="top")
        if i < 3:
            arrow(ax, (x + sw + 0.06, 10.94), (x + sw + gap - 0.06, 10.94))

    # B. runtime on the phone
    box(ax, 0.15, 0.15, 15.7, 9.25, "#fcfcfb", MUTED, lw=0.9, r=0.3)
    ax.text(0.45, 9.17, "B.  On the phone, at run time: no usage data leaves the device", fontsize=7.6,
            fontweight="bold", color=INK, va="top")
    cw, cg, cx0 = 4.6, 0.75, 0.45
    xs = [cx0 + i * (cw + cg) for i in range(3)]
    top_y, bot_y, ch = 4.95, 0.45, 3.65
    component(ax, xs[0], top_y, cw, ch, COMPONENTS[0])
    component(ax, xs[1], top_y, cw, ch, COMPONENTS[1])
    component(ax, xs[2], top_y, cw, ch, COMPONENTS[2])
    component(ax, xs[2], bot_y, cw, ch, COMPONENTS[3])
    component(ax, xs[1], bot_y, cw, ch, COMPONENTS[4])
    component(ax, xs[0], bot_y, cw, ch, COMPONENTS[5])

    mid_top, mid_bot = top_y + ch / 2, bot_y + ch / 2
    arrow(ax, (xs[0] + cw + 0.05, mid_top), (xs[1] - 0.05, mid_top))      # 1 -> 2
    arrow(ax, (xs[1] + cw + 0.05, mid_top), (xs[2] - 0.05, mid_top))      # 2 -> 3
    arrow(ax, (xs[2] + cw / 2, top_y - 0.05), (xs[2] + cw / 2, bot_y + ch + 0.05))  # 3 -> 4
    arrow(ax, (xs[2] - 0.05, mid_bot), (xs[1] + cw + 0.05, mid_bot))      # 4 -> 5
    arrow(ax, (xs[1] - 0.05, mid_bot), (xs[0] + cw + 0.05, mid_bot))      # 5 -> 6 (local log)
    # model file from the offline lane into component 3
    mx = x0 + 3 * (sw + gap) + sw / 2
    arrow(ax, (mx, 10.2), (mx, top_y + ch + 0.05), color="#6250d6", lw=1.2)
    ax.text(mx + 0.15, 9.72, "model file", fontsize=6.4, style="italic", color="#6250d6", va="center")

    FIG_DIR.mkdir(exist_ok=True)
    out = FIG_DIR / "fig1_architecture.png"
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)
    print("wrote", out)


# ---------- Figure 2: Gantt chart ----------

def gantt():
    rows = []  # (label, kind, payload)
    stage = None
    for st, task, owner, partner, a, b in PLAN:
        if st != stage:
            rows.append((st, "stage", None))
            stage = st
        who = f"{owner} + {partner}" if partner else owner  # the bar takes the lead's colour
        rows.append((f"{task} ({who})", "task", (owner, a, b)))
    n = len(rows)

    fig = plt.figure(figsize=(16 * CM, 12.9 * CM), dpi=300)
    ax = fig.add_axes([0.385, 0.11, 0.6, 0.79])
    x0, x1 = mdates.date2num(START), mdates.date2num(WEEKS[-1][1] + timedelta(days=1))
    ax.set_xlim(x0, x1)
    ax.set_ylim(n - 0.4, -0.6)

    for i, (a, b) in enumerate(WEEKS):  # week bands and headers
        if i % 2 == 0:
            ax.add_patch(Rectangle((mdates.date2num(a), -0.6), 7, n + 0.2, facecolor="#f4f4f2",
                                   edgecolor="none", zorder=0))
        ax.text(mdates.date2num(a) + 3.5, -1.55, f"Week {i + 1}", ha="center", va="bottom", fontsize=7.4,
                fontweight="bold", color=INK, clip_on=False)
        ax.text(mdates.date2num(a) + 3.5, -0.75, f"{a.day} {a:%b} – {b.day} {b:%b}", ha="center",
                va="bottom", fontsize=6.4, color=INK2, clip_on=False)

    for y, (label, kind, payload) in enumerate(rows):
        if kind == "stage":
            ax.text(-0.005, y, label, transform=ax.get_yaxis_transform(), ha="right", va="center",
                    fontsize=7.2, fontweight="bold", color=INK)
            ax.axhline(y - 0.5, color=GRID, lw=0.6, zorder=1)
            continue
        owner, a, b = payload
        color = OWNERS[owner][1]
        left = mdates.date2num(a)
        ax.barh(y, mdates.date2num(b) + 1 - left, left=left, height=0.62, color=color,
                edgecolor="white", linewidth=0.8, zorder=3)
        ax.text(-0.005, y, label, transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=6.6, color=INK2)

    for name, day in MILESTONES:  # milestone = end of that day
        xm = mdates.date2num(day) + 1
        ax.axvline(xm, color=INK2, lw=0.8, ls=(0, (3, 2)), zorder=2)
        ax.plot([xm], [n - 0.4], marker="D", markersize=6, color=INK, clip_on=False, zorder=5)
        ax.text(xm, n + 0.35, name, ha="center", va="top", fontsize=7, fontweight="bold", color=INK,
                clip_on=False)

    ax.set_yticks([])
    ax.set_xticks([])  # the week headers carry the dates
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)

    handles = [Rectangle((0, 0), 1, 1, color=c) for _, c in OWNERS.values()]
    fig.legend(handles, [full for full, _ in OWNERS.values()], loc="lower center", ncol=5, frameon=False,
               fontsize=6.6, handlelength=1.2, handleheight=0.9, columnspacing=1.4,
               bbox_to_anchor=(0.5, 0.005))

    out = FIG_DIR / "fig2_gantt.png"
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    architecture()
    gantt()
