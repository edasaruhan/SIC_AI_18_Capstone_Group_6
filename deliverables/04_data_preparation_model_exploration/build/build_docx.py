"""Build the corrected milestone-4 report (.docx) in the team draft's visual style.

usage: python -I build_docx.py <results.json> <sim_seeds.json> <sim_results.json> <out.docx>
Numbers come from the json files written by code/hw4_pipeline.py and build/sim_*.py; code excerpts are
read from code/hw4_pipeline.py, so the report and the code cannot drift apart.
"""

import ast
import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

R = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
SS = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))["summary"]
SR = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
OUT = Path(sys.argv[4])
HERE = Path(__file__).resolve().parent
FIG = HERE.parent / "figures"
CODE = (HERE.parent / "code" / "hw4_pipeline.py").read_text(encoding="utf-8")
D, G, P = R["data"], R["global"], R["personal"]
A = P["approaches"]

NAVY, BODY, GREY, SUBHEAD = "1B365D", "222222", "555555", "004D99"
FONT, MONO = "Times New Roman", "Consolas"


# ------------------------------------------------------------------ number helpers
def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def ci2(c):
    return f"{c[0]:.2f}–{c[1]:.2f}"


def thousands(n):
    return f"{n:,}"


def neg(text):
    """Typographic minus sign for negative numbers."""
    return re.sub(r"(?<![\w])-(?=\d)", "−", text)


WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}


# ------------------------------------------------------------------ document setup
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Cm(2.5))
zoom = doc.settings.element.find(qn("w:zoom"))
if zoom is not None and zoom.get(qn("w:percent")) is None:
    zoom.set(qn("w:percent"), "100")  # the default template omits this required attribute
cp = doc.core_properties
cp.title = "NudgeWell: Data Preparation / Feature Engineering and Model Exploration"
cp.author = "SIC AI Cohort 18, Group 6"
cp.subject = "Milestone 4"


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def spacing(p, before=0, after=120, line=None):
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(before / 20), Pt(after / 20)
    if line:
        pf.line_spacing = line / 240


TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|//.+?//)")


def add_runs(p, text, size=11, color=BODY, bold=False, italic=False):
    """Mini markup: **bold**, //italic//, `code`."""
    for part in TOKEN.split(text):
        if not part:
            continue
        b, i, mono = bold, italic, False
        if part.startswith("**") and part.endswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("//") and part.endswith("//"):
            part, i = part[2:-2], True
        elif part.startswith("`") and part.endswith("`"):
            part, mono = part[1:-1], True
        r = p.add_run(part)
        r.font.name = MONO if mono else FONT
        r.font.size = Pt(size - 1 if mono else size)
        r.font.color.rgb = RGBColor.from_string("2B2B2B" if mono else color)
        r.bold, r.italic = b, i
    return p


def para(text, kind="body"):
    if kind == "body":
        p = doc.add_paragraph()
        spacing(p, 0, 120, 276)
        add_runs(p, text)
    elif kind == "bullet":
        p = doc.add_paragraph(style="List Bullet")
        spacing(p, 0, 60, 276)
        add_runs(p, text)
    elif kind == "part":
        p = doc.add_paragraph()
        spacing(p, 360, 160)
        p.paragraph_format.keep_with_next = True
        add_runs(p, text, size=16, color=NAVY, bold=True)
    elif kind == "section":
        p = doc.add_paragraph()
        spacing(p, 280, 80)
        p.paragraph_format.keep_with_next = True
        add_runs(p, text, size=12.5, color=NAVY, bold=True)
    elif kind == "sub":
        p = doc.add_paragraph()
        spacing(p, 200, 40)
        p.paragraph_format.keep_with_next = True
        add_runs(p, text, size=11, color=SUBHEAD, bold=True, italic=True)
    elif kind == "caption":
        p = doc.add_paragraph()
        spacing(p, 0, 200)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, text, size=9.5, color=GREY, italic=True)
    elif kind == "tablecap":
        p = doc.add_paragraph()
        spacing(p, 160, 60)
        p.paragraph_format.keep_with_next = True
        add_runs(p, text, size=9.5, color=GREY, italic=True)
    elif kind == "ref":
        p = doc.add_paragraph()
        spacing(p, 0, 100, 264)
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.9)
        add_runs(p, text, size=10.5)
    else:
        raise ValueError(kind)
    return p


def set_table_borders(tbl, inside_h=True):
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    # schema order: top, left, bottom, right, insideH, insideV
    for edge, val, sz in [
        ("top", "single", "6"),
        ("left", "none", None),
        ("bottom", "single", "6"),
        ("right", "none", None),
        ("insideH", "single" if inside_h else "none", "4"),
        ("insideV", "none", None),
    ]:
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), val)
        if sz:
            e.set(qn("w:sz"), sz)
            e.set(qn("w:space"), "0")
            e.set(qn("w:color"), "D0D5DD")
        borders.append(e)
    tblPr.insert_element_before(
        borders,
        "w:shd",
        "w:tblLayout",
        "w:tblCellMar",
        "w:tblLook",
        "w:tblCaption",
        "w:tblDescription",
        "w:tblPrChange",
    )


def fix_widths(tbl, widths_cm):
    tbl.autofit = False  # writes <w:tblLayout w:type="fixed"/>
    grid = tbl._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths_cm):
        gc.set(qn("w:w"), str(int(w * 567)))
    for row in tbl.rows:
        for cell, w in zip(row.cells, widths_cm):
            cell.width = Cm(w)


def data_table(headers, rows, widths, caption=None, size=9):
    if caption:
        para(caption, "tablecap")
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t)
    fix_widths(t, widths)
    trPr = t.rows[0]._tr.get_or_add_trPr()
    hdr = OxmlElement("w:tblHeader")
    hdr.set(qn("w:val"), "true")
    trPr.append(hdr)
    for j, h in enumerate(headers):
        c = t.rows[0].cells[j]
        shade(c, NAVY)
        p = c.paragraphs[0]
        spacing(p, 40, 40)
        add_runs(p, h, size=min(10, size + 1), color="FFFFFF", bold=True)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            c = t.rows[i].cells[j]
            shade(c, "F4F6F9" if i % 2 == 1 else "FFFFFF")
            p = c.paragraphs[0]
            spacing(p, 30, 30, 252)
            add_runs(p, val, size=size, bold=(j == 0 and val.startswith("**")))
        cant = OxmlElement("w:cantSplit")
        t.rows[i]._tr.get_or_add_trPr().append(cant)
    tail = doc.add_paragraph()
    spacing(tail, 80, 160)
    return t


def box(text, fill="EBF3FA", size=10.5):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    fix_widths(t, [16.0])
    c = t.rows[0].cells[0]
    shade(c, fill)
    p = c.paragraphs[0]
    spacing(p, 60, 60, 276)
    add_runs(p, text, size=size)
    tail = doc.add_paragraph()
    spacing(tail, 0, 120)


def code_block(src):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    fix_widths(t, [16.0])
    c = t.rows[0].cells[0]
    shade(c, "F8F9FA")
    lines = src.rstrip("\n").split("\n")
    first = True
    for line in lines:
        p = c.paragraphs[0] if first else c.add_paragraph()
        first = False
        spacing(p, 0, 20, 240)
        r = p.add_run(line if line else " ")
        r.font.name, r.font.size = MONO, Pt(8.5)
        r.font.color.rgb = RGBColor.from_string("2B2B2B")
    tail = doc.add_paragraph()
    spacing(tail, 0, 120)


def figure(name, caption, width_cm=16.0):
    p = doc.add_paragraph()
    spacing(p, 160, 80)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(FIG / name), width=Cm(width_cm))
    para(caption, "caption")


def source_of(*names):
    """Exact source of top-level functions / assignments from hw4_pipeline.py."""
    tree = ast.parse(CODE)
    lines = CODE.split("\n")
    out = []
    for node in tree.body:
        nm = getattr(node, "name", None) or (node.targets[0].id if isinstance(node, ast.Assign) else None)
        if nm in names:
            start = node.lineno - 1
            while (
                start > 0
                and lines[start - 1].lstrip().startswith("#")
                and not lines[start - 1].startswith("# ---")
            ):
                start -= 1
            out.append("\n".join(lines[start : node.end_lineno]))
    return "\n\n".join(out)


def page_number_footer():
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for kind, text in [("begin", None), (None, " PAGE "), ("end", None)]:
        r = p.add_run()
        r.font.name, r.font.size = FONT, Pt(9)
        r.font.color.rgb = RGBColor.from_string(GREY)
        if kind:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), kind)
            r._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            r._r.append(it)


page_number_footer()

# ------------------------------------------------------------------ numbers used in the text
night, wn, ws = D["night"], D["within_night"], D["within_social"]
cats = {k: v["k"] / v["n"] for k, v in D["categories"].items()}
top1, top3, top10 = D["share_of_high_gap_top1_top3_top10"]
const_brier = D["high_gap_rate"] * (1 - D["high_gap_rate"])
hour3 = D["hourly"]["3"]
rules = D["rules"]
MODELS = ["LR", "RF", "XGB", "LGBM"]
MODEL_NAME = {"LR": "logistic regression", "RF": "the random forest", "XGB": "XGBoost", "LGBM": "LightGBM"}
SIM_LABELS = [
    ("LR", "Logistic regression"),
    ("RF", "random forest"),
    ("XGB", "XGBoost"),
    ("LGBM", "LightGBM"),
]
best = max(MODELS, key=lambda m: G[m]["roc_auc"])
at = R["at_alert_rate"]
gk = R["groupkfold5"]
pmg = P["personal_minus_global_within_roc"]
nul, dfl = SS["null"], SS["default"]
ws_lo = neg(f"{ws['ci'][0] * 100:.1f}")
pmg_mean, pmg_lo, pmg_hi = neg(f"{pmg['mean']:.2f}"), neg(f"{pmg['ci'][0]:.2f}"), neg(f"{pmg['ci'][1]:+.2f}")

# ------------------------------------------------------------------ title block
p = doc.add_paragraph()
spacing(p, 0, 80)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(p, "Data Preparation / Feature Engineering and Model Exploration", size=20, color=NAVY, bold=True)
p = doc.add_paragraph()
spacing(p, 40, 160)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(
    p,
    "Project Title: NudgeWell: In-Session Intention–Behavior Gap Prediction for Digital Well-Being",
    size=13,
    color=NAVY,
    bold=True,
)
p = doc.add_paragraph()
spacing(p, 0, 40)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(
    p,
    "Team Members (Group 6): Yusuf Ersel Kara • Bahadır Maral • Çağla Eryılmaz • Fatih Mehmet Menteşe • Damla Nur Öcal",
    size=11,
    color=NAVY,
    bold=True,
)
p = doc.add_paragraph()
spacing(p, 40, 360)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(
    p,
    "Samsung Innovation Campus (SIC) AI, Cohort 18 · Digital Addiction Capstone, in partnership with Yeşilay",
    size=10,
    color=GREY,
    italic=True,
)
p.add_run().add_break()
add_runs(p, "Instructor: Eda Nur Saruhan", size=10, color=GREY, italic=True)

# ================================================================== PART I
para("Part I: Data Preparation & Feature Engineering", "part")
para("1. Overview", "section")
para(
    "The data preparation and feature engineering phase is the analytical foundation of NudgeWell. Total screen time "
    "is a weak marker of harm: in a four-week logging study of 340 Android users, intense phone use alone did not "
    "predict negative well-being, and the two usage profiles linked with lower well-being were both marked by "
    "night-time sessions (Katevas et al., 2018). NudgeWell therefore looks at one specific moment inside a session, "
    "the in-session intention–behavior gap (IBG): the person reports that they should stop using the phone but keeps "
    "going (Zheng & Choe, 2026b)."
)
para(
    f"This phase turns the AwareMind check-ins into a feature table that a phone could compute at the moment of a "
    f"check-in. Three constraints shape it: (1) only information recorded before the prompt may enter a model; "
    f"(2) missing values and heavy-tailed durations must be handled without discarding informative check-ins; and "
    f"(3) people differ strongly: {pct(D['icc']['gap_continuous'], 0)} of the variance of the continuous gap lies "
    f"between participants (ICC = {f2(D['icc']['gap_continuous'])}), so new users and known users have to be "
    f"evaluated separately."
)
box(
    "**Phase objective:** NudgeWell frames the task as in-session binary classification. A check-in is a //high-gap "
    "moment// when the stated intention is 5 or lower on the 1–10 scale (1 = stop, 10 = continue) and the person keeps "
    "using the phone for more than 5 minutes after answering. These are the thresholds of Zheng and Choe (2026b), who "
    "call them arbitrary and also analyse the gap as a continuous score. A model may use only what is known when the "
    "prompt appears."
)

para("2. Data Collection", "section")
para(
    "NudgeWell uses the AwareMind dataset (Zheng & Choe, 2026a, 2026b). The authors' Android app logged phone use and, "
    "during sessions, asked “Reflecting on my phone usage, I should [ ] using my phone now”, answered on a 1–10 slider "
    "(1 = stop, 10 = continue), at most 16 times a day. The 37 participants were US adults (22 women, 15 men; aged "
    "18–64, mean 42.1) who used an Android phone at least three hours a day and wanted to cut down. Of 48 people "
    "recruited, 6 dropped out for technical reasons and 5 were excluded for answering “continue” to more than 95% of "
    "the prompts."
)
dr, dpp, rpp = D["date_range"], D["days_per_person"], D["rows_per_person"]
para(
    f"Data were collected between 2 July and 6 October 2025; each participant took part for at least two weeks "
    f"({dpp[0]}–{dpp[2]} days, median {dpp[1]:.0f}). The released file has {thousands(D['rows_released'])} check-in rows "
    f"and 92 columns from {thousands(D['sessions'])} sessions. After exact duplicates are removed (Section 3) it holds "
    f"{thousands(D['rows_unique'])} check-ins, {rpp[0]}–{rpp[2]} per participant (median {rpp[1]:.0f})."
)
para(
    "**Data use.** The OSF project carries no licence. We analyse the file for coursework only, do not redistribute it "
    "and keep it out of the public repository. Our concept note commits us to written reuse permission from the "
    "authors; until it is granted, the models in this report are exploratory and will not be published or deployed. "
    "The code also runs on a synthetic stand-in with the same 92 columns, built only from statistics printed in the "
    "paper (Part II, Section 4)."
)
para("**Scope and corpus justification.** Two other public resources were considered:")
para(
    "**Child Mind Institute (CMI) Problematic Internet Use** (Child Mind Institute, n.d.): questionnaire scores, "
    "physical-activity measures and wrist-worn accelerometer data from young people in the Healthy Brain Network study. "
    "Its label is a per-person severity score derived from the Parent-Child Internet Addiction Test. It has no "
    "session-level phone data and no in-the-moment intention, so it cannot train a model that acts during a session.",
    "bullet",
)
para(
    "**one sec** (Haliburton et al., 2024): usage logs from 1,039 users of a friction app over an average of 13.4 weeks, "
    "recording attempts to open target apps behind a short friction. It does not record whether the person wanted to "
    "stop.",
    "bullet",
)
para(
    "**AwareMind** (primary; Zheng & Choe, 2026a): the only public dataset that pairs a person's in-the-moment "
    "intention with what they did next, together with context recorded before the prompt (app category, time, "
    "session history, recent interactions and physical activity).",
    "bullet",
)

para("3. Data Cleaning", "section")
para(
    "We audited all 92 columns of the released file. Four issues needed handling: duplicate rows, missing values, "
    "heavy-tailed durations and information recorded after the prompt."
)
para("Duplicate rows", "sub")
para(
    f"{D['duplicate_rows']} rows are exact copies of another row: the same prompt identifier and identical values in "
    f"all 92 columns. All of them belong to one participant, whose {2 * D['duplicate_rows']} rows are "
    f"{D['duplicate_rows']} check-ins recorded twice. We remove the copies, which leaves "
    f"{thousands(D['rows_unique'])} unique check-ins. The paper's count of 5,772 includes them: with them the "
    f"high-gap share is {pct(D['high_gap_rate_released'])}, without them {pct(D['high_gap_rate'])}. Every number "
    f"below uses the de-duplicated data."
)
para("Handling missing values", "sub")
mis = D["missing"]
para(
    f"Missingness was audited on the {thousands(D['rows_unique'])} unique check-ins. Rows are kept rather than "
    f"deleted; deleting them would drop {pct((mis['app_category'] + mis['activity']) / D['rows_unique'], 0)} of the "
    f"data at most."
)
para(
    f"**Foreground app** (`package_name`, `Category_L1`): missing in {mis['app_category']} check-ins "
    f"({pct(mis['app_category'] / D['rows_unique'])}); the dataset does not record why. The app-category indicators "
    f"stay 0 and a flag `app_missing` = 1 is added. The three app-duration features are missing in "
    f"{mis['app_durations']} rows; they are filled with the training-fold median inside the model pipeline, so no "
    f"information from test participants is used.",
    "bullet",
)
para(
    f"**Physical activity** (`activity_type`): missing in {mis['activity']} check-ins "
    f"({pct(mis['activity'] / D['rows_unique'])}). The five activity indicators stay 0 and a flag "
    f"`activity_missing` = 1 is added.",
    "bullet",
)
mt = D["median_taps_short_vs_long_sessions"]
para(
    f"**Interaction counts** (taps, scrolls, text edits): no missing values; {pct(mis['zero_interaction_share'])} of "
    f"check-ins have no recorded interaction. The paper analyses interactions “in the last minute” before the prompt. "
    f"The data dictionary does not state the window, but the counts do not grow with session length (median taps: "
    f"{mt[0]:.0f} in sessions shorter than 30 seconds, {mt[1]:.0f} in sessions longer than 10 minutes), so we treat "
    f"them as recent-activity counts and do not divide them by session length.",
    "bullet",
)
para("Outliers and skew", "sub")
para(
    f"The time a person keeps using the phone after answering is heavily right-skewed: median "
    f"{D['remaining_median_min']:.1f} minutes, maximum {D['remaining_max_min']:.1f} minutes (about 11 hours). The "
    f"binary label only compares it with 5 minutes, so it needs no capping. The dataset's continuous outcome caps it at "
    f"128 minutes ({pct(D['remaining_over_128_share'])} of check-ins) and log-transforms it "
    f"(`remaining_log = log10(min(minutes, 128) + 1)`); we keep that definition for the continuous gap. Heavy-tailed "
    f"predictors (durations, counts and scroll distances) are transformed with log(1 + x), which leaves tree models "
    f"unchanged and stabilises the linear model."
)
para("Leakage control", "sub")
para(
    "Variables measured after the prompt would make the task trivial and cannot exist on a phone at prediction time. "
    "Table 1 lists everything that is removed. A guard in the pipeline stops the run if any outcome or identifier "
    "column re-enters the feature table."
)
data_table(
    ["Audit category", "Removed variables", "Reason"],
    [
        [
            "**Outcomes measured after the prompt**",
            "`answer`, `remaining_time`, `remaining_minutes`, `remaining_capped`, "
            "`remaining_log`, `remaining_scaled`, `temp_scaled`, `intention_behavior_gap`, `lock_time`",
            "Define or reveal the label; unknown when the prompt appears.",
        ],
        [
            "**Exact copies**",
            "`session_length_till_esm` and `time_since_unlock` (both `session_minutes` in milliseconds); "
            "`screen_time_so_far` (copy of `screen_time_minutes`)",
            "Redundant; copies split importance between them.",
        ],
        [
            "**Identifiers and bookkeeping**",
            "`pid`, `PID`, `host`, `esm_id_full`, `session_id_combined`, "
            "`session_index`, `package_name`, `app_at_prompt`",
            "Let a model memorise people or sessions; package names " "are replaced by app categories.",
        ],
        [
            "**Raw timestamps**",
            "`date`, `date_4am`, `unlock_time`, `esm_time`, `esm_local`, `unlock_local`, `timezone`",
            "Replaced by cyclic hour and weekday.",
        ],
        [
            "**Static demographics (not leakage)**",
            "`Age`, `Gender_encoded`, `Education_encoded`, `Race_*` (5), " "`Employment_*` (7)",
            "Constant within a person and unique for each of the 37 participants, so in a "
            "cross-user model they act as participant identifiers. Excluded from the main models and tested separately "
            "(Part II, Section 3).",
        ],
    ],
    [3.3, 6.9, 5.8],
    caption="Table 1: Variables removed before modelling.",
)
ex = D["app_duration_exceeds_elapsed"]
para(
    f"We also checked whether any kept feature runs past the prompt. In {ex['rows']} check-ins (three participants, "
    f"almost all from one) the time spent in the current app during the session is longer than the time since "
    f"unlock; the excess is unrelated to how long the person kept going, so we treat it as a device timing quirk, not "
    f"leakage. The guard was also tested on synthetic data with nothing to find, where every model scored at chance "
    f"(Part II, Section 4)."
)

para("4. Exploratory Data Analysis (EDA)", "section")
para(
    f"Five findings shape the modelling choices (all on {thousands(D['rows_unique'])} unique check-ins; “pooled” "
    f"means all check-ins counted together):"
)
para(
    f"**Prevalence.** {D['high_gap_n']} check-ins ({pct(D['high_gap_rate'])}) are high-gap moments. In "
    f"{pct(D['answer_10_share'])} of check-ins people answered 10 (“continue”).",
    "bullet",
)
para(
    f"**Night.** Between midnight and 06:00 the pooled share is {pct(night['rate'])} (n = {night['n']}) against "
    f"{pct(night['rest_rate'])} at other hours, peaking at 3 am ({pct(hour3['k'] / hour3['n'], 0)}, n = {hour3['n']}; "
    f"Figure 1). The effect holds within people: compared with their own daytime check-ins, participants' night-time "
    f"share is {wn['mean'] * 100:.1f} percentage points higher on average (95% CI {wn['ci'][0] * 100:.1f}–"
    f"{wn['ci'][1] * 100:.1f}; higher at night for {wn['higher']} of the {wn['n']} participants with at least five "
    f"check-ins in both).",
    "bullet",
)
para(
    f"**App category.** Pooled shares are highest for social media ({pct(cats['Social'])}), media and video "
    f"({pct(cats['Media'])}) and browsers ({pct(cats['Browser'])}), and lowest for messaging ({pct(cats['Message'])}), "
    f"work and study apps ({pct(cats['Work & Study'])}) and system tools ({pct(cats['System tool'])}) (Figure 2). Within "
    f"people the differences shrink: a participant's social-media check-ins are {ws['mean'] * 100:.1f} points above "
    f"their other check-ins on average (95% CI {ws_lo} to {ws['ci'][1] * 100:.1f}; higher for only "
    f"{ws['higher']} of {ws['n']} participants). Part of the pooled difference therefore reflects //who// uses social "
    f"media rather than what social media does.",
    "bullet",
)
para(
    f"**Differences between people.** The share of high-gap moments ranges from 0% to "
    f"{pct(max(D['per_person_rate']), 0)} per participant (median {pct(D['per_person_rate_median'])}; Figure 3); "
    f"{WORDS.get(D['people_without_high_gap'], D['people_without_high_gap'])} participants have none. The intraclass correlation is "
    f"{f2(D['icc']['gap_continuous'])} for the continuous gap, {f2(D['icc']['answer'])} for the stated intention and "
    f"{f2(D['icc']['high_gap_binary'])} for the binary label. Women had a higher share than men "
    f"({pct(D['gender_rates']['women'])} vs {pct(D['gender_rates']['men'])}).",
    "bullet",
)
para(
    f"**Concentration.** One participant ({pct(D['top1_rows_and_rate'][1], 0)} high-gap) contributes {pct(top1)} of "
    f"all high-gap moments; the top three contribute {pct(top3)} and the top ten {pct(top10)}. Without that participant "
    f"the pooled share is {pct(D['rate_without_top1'])}. Pooled percentages therefore mix who is in the data with "
    f"what happens within a person, so we report within-person comparisons where possible and evaluate models per "
    f"participant.",
    "bullet",
)
figure(
    "fig1_by_hour.png",
    width_cm=15.0,
    caption=f"Figure 1: High-gap share by hour of the check-in (participant's local time), with 95% "
    f"Wilson confidence band; {thousands(D['rows_unique'])} unique check-ins.",
)
figure(
    "fig2_by_app_category.png",
    width_cm=15.0,
    caption="Figure 2: High-gap share by the app in use at the check-in, pooled over "
    "participants. “Calls, camera, launcher” is the dataset's “To exclude” group.",
)
figure(
    "fig3_per_participant.png",
    width_cm=15.0,
    caption=f"Figure 3: Each participant's share of high-gap moments, sorted, with 95% "
    f"confidence intervals. The pooled share ({pct(D['high_gap_rate'])}) is well above the median participant "
    f"({pct(D['per_person_rate_median'])}).",
)

para("5. Feature Engineering", "section")
para(
    f"From the columns that pass the audit we build {R['n_features']} features in five groups (Table 2). Every "
    f"feature is computed from information available at the moment the prompt appears."
)
data_table(
    ["Feature group", "Engineered variables", "Rationale"],
    [
        [
            "**Time (10)**",
            "Sine and cosine of hour and weekday; weekend and workday flags; morning, afternoon, evening "
            "and night indicators",
            "Cyclic encoding keeps 23:59 next to 00:01. Night is the strongest within-person signal.",
        ],
        [
            "**Current session (5)**",
            "Session length so far; time in the current app (this visit and this session); distinct "
            "apps and app switches in the session",
            "How long and how fragmented the session has been.",
        ],
        [
            "**Earlier use today (8)**",
            "Screen time today; number and mean length of earlier sessions; length of the "
            "previous session and time since it ended; time in the current app today; distinct apps and app switches today",
            "Heavy-use days and quick re-opening of the phone.",
        ],
        [
            "**Recent interaction (10)**",
            "Taps, text edits, and scroll counts and distances in four directions",
            "Passive scrolling versus active typing; the paper found opposite effects for scrolling and text editing.",
        ],
        [
            "**App and activity (16)**",
            "Nine app-category indicators; five activity indicators (still, walking, running, "
            "cycling, in a vehicle); `app_missing` and `activity_missing`",
            "What the person is doing and whether they are " "moving; missingness is made explicit.",
        ],
    ],
    [3.3, 7.2, 5.5],
    caption="Table 2: Feature groups (counts in brackets).",
)
para(
    "Demographics are kept out of the main feature set because they identify participants (Table 1); Part II, "
    "Section 3 shows what happens when they are added."
)

para("6. Data Transformation", "section")
para("**Log transform.** Durations, counts and scroll distances: log(1 + x), applied row by row.", "bullet")
para(
    "**Imputation.** The three app-duration features: median of the training fold, learned inside the model "
    "pipeline.",
    "bullet",
)
para(
    "**Scaling.** Standardisation (z-scores) only for logistic regression, fitted inside each training fold; the tree "
    "models need none.",
    "bullet",
)
para(
    "**Categorical variables.** App category, physical activity and time period are one-hot indicators, as released. "
    "No ordinal codes are used: the coding key of `Education_encoded` is not documented, and age is a continuous "
    "variable (the data have no age bands).",
    "bullet",
)
para("The feature-building step of our pipeline (`code/hw4_pipeline.py`):")
code_block(source_of("build_features"))

# ================================================================== PART II
para("Part II: Model Exploration", "part")
para("1. Model Selection", "section")
para(
    f"This milestone compares tabular baselines. The project's main model, a compact temporal convolutional network "
    f"(TCN; Bai et al., 2018) that reads each person's earlier check-ins in time order, is developed in the next "
    f"milestone, as set out in our concept note; the baselines below define the bar it must clear. Candidates were "
    f"judged on four criteria: (1) capacity for non-linear interactions; (2) behaviour under class imbalance "
    f"({pct(D['high_gap_rate'])} positives); (3) size and speed on a phone, because keeping behavioural data on the "
    f"device supports the data-minimisation principle of Law No. 6698 on the Protection of Personal Data (Law No. 6698, "
    f"2016); and (4) whether the model can be adapted to one person without sending data off the phone."
)
data_table(
    ["Model", "Strengths", "Weaknesses", "On-device use"],
    [
        [
            "**Logistic regression (L2)**",
            "Interpretable coefficients; tiny; stable probabilities",
            "Only additive effects unless interactions are added",
            "A few hundred bytes of weights",
        ],
        [
            "**Random forest** (Breiman, 2001)",
            "Captures interactions; insensitive to scaling; out-of-bag error estimate",
            "Cannot be updated incrementally; larger than a linear model",
            "100 trees of depth ≤ 6: about 9,000 nodes, under "
            "1 MB; inference only, so personal updates need retraining",
        ],
        [
            "**XGBoost** (Chen & Guestrin, 2016)",
            "Regularised gradient boosting; strong on tabular data; handles " "missing values natively",
            "Overfits small samples unless depth and learning rate are limited",
            "Similar to the random forest; inference only",
        ],
        [
            "**LightGBM** (Ke et al., 2017)",
            "Fast histogram-based boosting with leaf-wise trees; handles missing values " "natively",
            "Leaf-wise growth overfits small data without a depth limit",
            "Similar to the random forest; " "inference only",
        ],
        [
            "**Temporal convolutional network** (next milestone)",
            "Uses the order of earlier check-ins",
            "More tuning; must beat the baselines on the same splits",
            "LiteRT or ONNX Runtime Mobile; personal " "re-calibration on the device",
        ],
    ],
    [3.6, 4.3, 4.0, 4.1],
    caption="Table 3: Candidate models.",
)
para(
    "Size and speed on a phone are targets (under 5 MB, under 10 ms per prediction) to be measured on a device in "
    "the next milestone; they are not measured here."
)

para("2. Model Training", "section")
para("Two evaluation regimes answer two different questions:")
para(
    f"**A. New users (global).** Leave-one-participant-out (LOPO) cross-validation, the protocol of Zheng and Choe "
    f"(2026b): each participant is scored by a model trained on the other 36. We report pooled metrics over all "
    f"held-out check-ins with 95% confidence intervals from a bootstrap over participants, and the within-person "
    f"ROC-AUC (how well the model ranks one person's own check-ins), averaged over the {G['LR']['within_n']} "
    f"participants who have both classes.",
    "bullet",
)
para(
    f"**B. Known users (personal).** Each participant's check-ins are put in time order; the first 70% are used for "
    f"training and the last 30% for testing, for all 37 participants. Every approach is scored on the same "
    f"{thousands(P['n_test_rows'])} test check-ins: (i) the person's own base rate, their training-slice share shrunk "
    f"toward the population rate; (ii) the global model with no personal data; (iii) the global model plus a personal "
    f"intercept, one number per person fitted on the training slice; (iv) a personal random forest and (v) a personal "
    f"XGBoost model, each trained only on the person's own data; and (vi) a combined random forest trained on everyone "
    f"else plus the person's training slice, weighted five times.",
    "bullet",
)
para(
    "No participant is excluded on the basis of the outcome. Within-person metrics can only be computed for "
    "participants whose test slice contains both classes; they are reported for that group with its own chance "
    "level."
)
para("Hyperparameters and class imbalance", "sub")
para("**Logistic regression:** L2 penalty, C = 1.0, class_weight = 'balanced', max_iter = 2000.", "bullet")
para(
    "**Random forest:** n_estimators = 100, max_depth = 6, min_samples_split = 10, class_weight = 'balanced'.",
    "bullet",
)
para(
    f"**XGBoost:** n_estimators = 100, max_depth = 4, learning_rate = 0.05, scale_pos_weight = negatives / positives "
    f"of the training fold (about {(1 - D['high_gap_rate']) / D['high_gap_rate']:.1f}).",
    "bullet",
)
para(
    "**LightGBM:** n_estimators = 100, max_depth = 5, num_leaves = 31, learning_rate = 0.05, class_weight = "
    "'balanced'.",
    "bullet",
)
para(
    f"All settings were fixed before testing; nothing was tuned on test participants. Class weighting counters the "
    f"{pct(D['high_gap_rate'])} prevalence but inflates the predicted probabilities, so the Brier scores below are "
    f"reported for transparency; calibration (Platt scaling or isotonic regression; Niculescu-Mizil & Caruana, 2005) "
    f"is planned for the next milestone."
)

para("3. Model Evaluation", "section")
para(
    f"ROC-AUC measures ranking, with 0.5 as chance. PR-AUC focuses on the high-gap class; its chance level equals the "
    f"prevalence of the rows being evaluated, not a fixed number (Saito & Rehmsmeier, 2015). The Brier score measures "
    f"probability error; predicting the prevalence for everyone gives {f3(const_brier)}. We also compare the models "
    f"with the fixed rule from our concept note, which alerts when it is night, a social-media app is open or the "
    f"session has lasted more than 10 minutes, at the same alert rate ({pct(R['alert_rate'])} of check-ins)."
)


def grow(name, label):
    g, a = G[name], at[name if name in at else "Fixed rule"]
    return [
        label,
        f"{f2(g['roc_auc'])} ({ci2(g['roc_auc_ci'])})",
        f2(g["pr_auc"]),
        "—" if name.startswith("Fixed rule") else f3(g["brier"]),
        f"{f2(g['within_roc_auc'])} ({ci2(g['within_roc_auc_ci'])})",
        f"{pct(a['precision'])} / {pct(a['recall'])}",
    ]


rule_key = [k for k in G if k.startswith("Fixed rule")][0]
data_table(
    [
        "Model",
        "Pooled ROC-AUC (95% CI)",
        f"PR-AUC (chance {f3(D['high_gap_rate'])})",
        f"Brier (constant {f3(const_brier)})",
        "Within-person ROC-AUC (95% CI)",
        f"Precision / recall at {pct(R['alert_rate'])} alerts",
    ],
    [
        grow(rule_key, "**Fixed rule** (no training)"),
        grow("LR", "**Logistic regression**"),
        grow("RF", "**Random forest**"),
        grow("XGB", "**XGBoost**"),
        grow("LGBM", "**LightGBM**"),
        grow("RF + demographics", "**Random forest + demographics**"),
        grow("LR + demographics", "**Logistic regression + demographics**"),
    ],
    [3.4, 2.7, 2.0, 1.9, 2.7, 3.3],
    size=8.5,
    caption="Table 4: New users (leave-one-participant-out, 37 folds, 5,627 check-ins).",
)
para(
    f"**Modest signal for new users.** The best model, {MODEL_NAME[best]}, reaches a pooled ROC-AUC of "
    f"{f2(G[best]['roc_auc'])} (95% CI {ci2(G[best]['roc_auc_ci'])}); "
    + ", ".join(f"{MODEL_NAME[m]} {f2(G[m]['roc_auc'])}" for m in MODELS if m != best)
    + f". Within a person, all four rank high-gap moments above chance "
    f"({f2(min(G[m]['within_roc_auc'] for m in MODELS))}–{f2(max(G[m]['within_roc_auc'] for m in MODELS))}; above 0.5 "
    f"for {pct(min(G[m]['within_share_above_half'] for m in MODELS), 0)}–"
    f"{pct(max(G[m]['within_share_above_half'] for m in MODELS), 0)} of participants).",
    "bullet",
)
para(
    f"**A simple rule does as well.** The three-signal rule has about the same pooled ROC-AUC as the random forest "
    f"({f2(G[rule_key]['roc_auc'])}) and, at its own alert rate, higher precision and recall "
    f"({pct(at['Fixed rule']['precision'])} and {pct(at['Fixed rule']['recall'])}) than the best model "
    f"({pct(at[best]['precision'])} and {pct(at[best]['recall'])}; Figure 6). For new users these baselines do not yet "
    f"justify a learned model; the temporal model has to beat this rule (concept note, objective O4).",
    "bullet",
)
para(
    f"**Demographics act as identifiers.** Adding the 15 demographic columns lowers the pooled ROC-AUC (random forest "
    f"{f2(G['RF']['roc_auc'])} → {f2(G['RF + demographics']['roc_auc'])}; logistic regression "
    f"{f2(G['LR']['roc_auc'])} → {f2(G['LR + demographics']['roc_auc'])}) while the within-person ROC-AUC stays the "
    f"same. When included, they take {pct(R['gini_share_demographics'], 0)} of the forest's Gini importance, led by "
    f"age, education and retirement. Under a 5-fold participant split, the same forest scores "
    f"{f2(gk['RF']['roc_auc'][0])} ± {f2(gk['RF']['roc_auc'][1])} without them and "
    f"{f2(gk['RF + demographics']['roc_auc'][0])} ± {f2(gk['RF + demographics']['roc_auc'][1])} with them.",
    "bullet",
)
para(
    f"**Calibration.** Every model has a Brier score above the constant prediction ({f3(const_brier)}) because of class "
    f"weighting; probabilities must be calibrated before they drive a decision.",
    "bullet",
)
figure(
    "fig4_roc_pr_new_users.png",
    "Figure 4: New users (leave-one-participant-out): ROC and precision-recall curves of "
    "the pooled held-out predictions; the legend gives the pooled AUCs. The square marks the fixed rule. Chance is "
    "the diagonal (ROC) and the prevalence line (PR).",
)


def prow(name, label):
    a = A[name]
    return [
        label,
        f"{f2(a['roc_auc'])} ({ci2(a['roc_auc_ci'])})",
        f2(a["pr_auc"]),
        f3(a["brier"]),
        f"{f2(a['within_roc_auc'])} ({ci2(a['within_roc_auc_ci'])})",
        f2(a["within_pr_auc"]),
    ]


data_table(
    [
        "Approach",
        "Pooled ROC-AUC (95% CI)",
        f"PR-AUC (chance {f3(P['test_prevalence'])})",
        "Brier",
        "Within-person ROC-AUC (95% CI)",
        f"Within-person PR-AUC (chance {f2(P['random_within_pr_auc'])})",
    ],
    [
        prow("Own base rate", "**Own base rate** (one number, no model)"),
        prow("Global (zero-shot)", "**Global random forest** (no personal data)"),
        prow("Global + personal intercept", "**Global + personal intercept**"),
        prow("Personal RF", "**Personal random forest** (own data only)"),
        prow("Personal XGBoost", "**Personal XGBoost** (own data only)"),
        prow("Combined RF", "**Combined random forest** (others + own ×5)"),
    ],
    [3.6, 2.7, 1.9, 1.5, 2.8, 3.5],
    size=8.5,
    caption=f"Table 5: Known users (first 70% of each participant's check-ins for training, last 30% for testing; "
    f"{thousands(P['n_test_rows'])} test check-ins). Within-person metrics cover the "
    f"{A['Personal RF']['within_n']} participants whose test slice has both classes.",
)
figure(
    "fig5_known_users_same_rows.png",
    width_cm=14.5,
    caption="Figure 5: Known users: every approach scored on the "
    "same last 30% of each participant's check-ins. Left: pooled ROC-AUC (finding the right people); right: "
    "within-person ROC-AUC (finding the right moments). Whiskers: 95% bootstrap intervals over participants.",
)
para(
    f"**Knowing the person is the big gain.** One number per person, their own share of high-gap moments in the "
    f"training slice, lifts the pooled ROC-AUC from {f2(A['Global (zero-shot)']['roc_auc'])} (global model) to "
    f"{f2(A['Own base rate']['roc_auc'])}. People's rates are stable over time: the correlation between a person's "
    f"share in the first 70% and the last 30% of their check-ins is {f2(P['base_rate_stability_r'])}.",
    "bullet",
)
para(
    f"**Global model + personal intercept ≈ personal model.** Adding that one number to the global model gives a "
    f"pooled ROC-AUC of {f2(A['Global + personal intercept']['roc_auc'])} and a PR-AUC of "
    f"{f2(A['Global + personal intercept']['pr_auc'])}, close to a forest trained on the person's own data "
    f"({f2(A['Personal RF']['roc_auc'])} and {f2(A['Personal RF']['pr_auc'])}) and above a personal XGBoost model "
    f"({f2(A['Personal XGBoost']['roc_auc'])} and {f2(A['Personal XGBoost']['pr_auc'])}), and it needs no training on "
    f"the phone.",
    "bullet",
)
para(
    f"**Ranking a person's own moments is equally hard for every approach.** The within-person ROC-AUC is "
    f"{f2(A['Global (zero-shot)']['within_roc_auc'])} for the global model, {f2(A['Personal RF']['within_roc_auc'])} "
    f"for the personal forest and {f2(A['Personal XGBoost']['within_roc_auc'])} for the personal XGBoost model "
    f"(personal forest minus global: {pmg_mean}, 95% CI {pmg_lo} to {pmg_hi}; the personal forest is better for "
    f"{pmg['personal_better']} of {pmg['n']} participants). With two to four weeks of data, personal data tells us "
    f"//who// is at risk, not yet //when//.",
    "bullet",
)
para(
    f"**Chance levels differ by regime.** The participants with both classes in their test slice have a mean "
    f"prevalence of {f3(A['Personal RF']['within_prevalence'])}, and random scores on exactly their rows give a "
    f"within-person PR-AUC of {f2(P['random_within_pr_auc'])}. PR-AUC values from different regimes can therefore "
    f"only be compared against their own chance level.",
    "bullet",
)
figure(
    "fig6_same_alert_rate.png",
    f"Figure 6: Confusion matrices when the fixed rule and the best model each flag "
    f"{pct(R['alert_rate'])} of check-ins (new users, leave-one-participant-out).",
    width_cm=13.5,
)
figure(
    "fig7_permutation_importance.png",
    width_cm=15.0,
    caption="Figure 7: Random forest without demographics: drop in ROC-AUC when one "
    "feature is shuffled, measured on held-out participants (5-fold participant split, 5 shuffles). Session "
    "durations, the previous session and night carry most of the signal; recent-interaction features add none for "
    "unseen people.",
)
para("What this means for the next milestone", "sub")
para(
    f"The temporal model must beat two baselines on the same splits: the fixed rule at its alert rate (precision "
    f"{pct(at['Fixed rule']['precision'])}, recall {pct(at['Fixed rule']['recall'])}) for new users, and the global "
    f"model with a personal intercept for known users (pooled ROC-AUC {f2(A['Global + personal intercept']['roc_auc'])}).",
    "bullet",
)
para(
    "Personalisation should start as a per-person intercept on top of a global model: one number, updated on the "
    "phone as check-ins accumulate. A separately trained personal model adds nothing measurable with this amount of "
    "data.",
    "bullet",
)
para(
    "Probabilities must be calibrated before a decision threshold and a daily prompt budget are fixed.",
    "bullet",
)
para(
    f"**Limitations.** 37 US adults followed for {dpp[0]}–{dpp[2]} days; one participant contributes "
    f"{pct(top1, 0)} of all high-gap moments; the binary label uses thresholds the dataset authors call arbitrary; and "
    f"the results are exploratory until reuse permission is granted.",
    "bullet",
)

para("4. Code Implementation", "section")
para(
    f"The full pipeline is `code/hw4_pipeline.py` in our repository. It reads the AwareMind file or the synthetic "
    f"stand-in, removes duplicates, builds the {R['n_features']} features, runs both evaluation regimes and writes every "
    f"number in this report to `results.json`; the figures and this document are generated from that file. The key "
    f"parts follow (the feature step is in Part I, Section 6)."
)
code_block(source_of("OUTCOME", "IDENTIFIERS", "load", "lopo", "chrono_split", "fit_offset"))
para(
    "In the personal regime, each participant's intercept is fitted on their own training slice with "
    "`fit_offset(global_scores, labels, a0=population_intercept, tau=1.0)` and applied to the global model's scores on "
    "their test slice; the prior keeps the intercept close to the population value when a person has few check-ins."
)
para("Pipeline checks on synthetic data", "sub")
para(
    "Because the real file cannot be shared, the code was also run on the project's synthetic stand-in "
    "(`simulator/`). It has the same 92 columns but is generated only from statistics printed in the paper, with "
    "effects that can be switched off. Its numbers test the code; they are not findings about people."
)
data_table(
    ["Check", "What it tests", "Result (ROC-AUC, mean ± SD over 6 datasets)"],
    [
        [
            "**NULL mode** (no planted effects)",
            "Nothing to find: a pipeline that scores above chance has a bug or a leak",
            "; ".join(f"{lab} {f2(nul[m]['mean'])} ± {f2(nul[m]['sd'])}" for m, lab in SIM_LABELS),
        ],
        [
            "**Default mode** (effects from the paper)",
            "Planted effects are recovered",
            "; ".join(f"{lab} {f2(dfl[m]['mean'])} ± {f2(dfl[m]['sd'])}" for m, lab in SIM_LABELS),
        ],
        [
            "**Full run** (seed 2410)",
            "Both regimes run end to end without the real file",
            "Completed; all results written to results.json",
        ],
    ],
    [4.0, 5.6, 6.4],
    caption="Table 6: Pipeline checks on synthetic data (5-fold participant split).",
)
sd = SR["synthetic_default"]
para(
    f"The stand-in has less person-level variation than the real data (intraclass correlation of the binary label "
    f"{f2(sd['icc']['high_gap_binary'])} against {f2(D['icc']['high_gap_binary'])}) and no extreme participant, so it "
    f"is suitable for testing the code but not for studying personalisation."
)

# ------------------------------------------------------------------ references
para("References", "part")
refs = [
    "Bai, S., Kolter, J. Z., & Koltun, V. (2018). //An empirical evaluation of generic convolutional and recurrent "
    "networks for sequence modeling// (arXiv:1803.01271). arXiv. https://doi.org/10.48550/arXiv.1803.01271",
    "Breiman, L. (2001). Random forests. //Machine Learning, 45//(1), 5–32. https://doi.org/10.1023/A:1010933404324",
    "Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. In //Proceedings of the 22nd ACM SIGKDD "
    "International Conference on Knowledge Discovery and Data Mining// (pp. 785–794). ACM. "
    "https://doi.org/10.1145/2939672.2939785",
    "Child Mind Institute. (n.d.). //Child Mind Institute — Problematic internet use// [Competition data set]. Kaggle. "
    "Retrieved September 19, 2026, from https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use",
    "Haliburton, L., Grüning, D. J., Riedel, F., Schmidt, A., & Terzimehić, N. (2024). A longitudinal in-the-wild "
    "investigation of design frictions to prevent smartphone overuse. In //Proceedings of the CHI Conference on Human "
    "Factors in Computing Systems// (pp. 1–16). ACM. https://doi.org/10.1145/3613904.3642370",
    "Katevas, K., Arapakis, I., & Pielot, M. (2018). Typical phone use habits: Intense use does not predict negative "
    "well-being. In //Proceedings of the 20th International Conference on Human-Computer Interaction with Mobile Devices "
    "and Services// (pp. 1–13). ACM. https://doi.org/10.1145/3229434.3229441",
    "Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly "
    "efficient gradient boosting decision tree. In //Advances in Neural Information Processing Systems 30// "
    "(pp. 3146–3154). Curran Associates. "
    "https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html",
    "Law No. 6698 on the Protection of Personal Data. (2016). //Official Gazette of the Republic of Türkiye//, No. 29677 "
    "(7 April 2016). English translation retrieved October 11, 2026, from "
    "https://www.kvkk.gov.tr/Icerik/6649/Personal-Data-Protection-Law",
    "Niculescu-Mizil, A., & Caruana, R. (2005). Predicting good probabilities with supervised learning. In //Proceedings "
    "of the 22nd International Conference on Machine Learning// (pp. 625–632). ACM. https://doi.org/10.1145/1102351.1102430",
    "Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating "
    "binary classifiers on imbalanced datasets. //PLOS ONE, 10//(3), e0118432. https://doi.org/10.1371/journal.pone.0118432",
    "Zheng, J., & Choe, E. K. (2026a). //Intention-behavior gap in smartphone usage// [Data set]. OSF. https://osf.io/x6yzs/",
    "Zheng, J., & Choe, E. K. (2026b). //To stop or not to stop: Exploring the intention-behavior gaps in smartphone "
    "usage// (arXiv:2609.08909) [Preprint, MobileHCI 2026]. arXiv. https://doi.org/10.48550/arXiv.2609.08909",
]
for r in refs:
    para(r, "ref")

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("saved", OUT)
