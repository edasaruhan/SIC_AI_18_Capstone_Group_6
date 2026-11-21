"""Fill the instructor's HW5 DOCX with the verified results."""

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path
from textwrap import dedent

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Inches, Pt, RGBColor


BUILD = Path(__file__).resolve().parent
HW5 = BUILD.parent
RUN = "hw5-v1-step5-20261117"
OUTPUT = HW5 / "NudgeWell_HW5_Model_Refinement_and_Test_Submission.docx"
CODE = HW5 / "code" / "nudgewell_hw5"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def element(name, **attributes):
    item = OxmlElement("w:" + name)
    for key, value in attributes.items():
        item.set(qn("w:" + key), str(value))
    return item


def add_link(p, label, url):
    link = element("hyperlink")
    link.set(qn("r:id"), p.part.relate_to(url, RT.HYPERLINK, is_external=True))
    run = element("r")
    props = element("rPr")
    props.append(element("color", val="2A568C"))
    props.append(element("u", val="single"))
    txt = element("t")
    txt.text = label
    run.append(props)
    run.append(txt)
    link.append(run)
    p._p.append(link)


class Report:
    def __init__(self, template):
        self.doc = Document(template)
        self.headings = deque()
        for paragraph in self.doc.paragraphs:
            props = paragraph._p.pPr
            if props is not None and props.find(qn("w:outlineLvl")) is not None:
                self.headings.append(paragraph)
            paragraph._p.getparent().remove(paragraph._p)
        sec = self.doc.sections[0]
        self.width = (sec.page_width - sec.left_margin - sec.right_margin) / Inches(1)
        sec.footer_distance = Inches(.31)
        styles = self.doc.styles
        parameters = [
            ("Normal", 12, False, 0, 6),
            ("Report subtitle", 12, False, 0, 6),
            ("Report subheading", 12, True, 8, 4),
            ("Report caption", 10, False, 3, 7),
        ]
        for name, size, bold, before, after in parameters:
            s = styles[name] if name in styles else styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            if name != "Normal":
                s.base_style = styles["Normal"]
            s.font.name, s.font.size, s.font.bold = "Times New Roman", Pt(size), bold
            s.font.color.rgb = RGBColor(0, 0, 0)
            p = s.paragraph_format
            p.space_before, p.space_after = Pt(before), Pt(after)
            p.line_spacing = 1.0
            p.widow_control = True
        styles["Report subheading"].paragraph_format.keep_with_next = True
        for name, font, size in [("Report cell", "Times New Roman", 10.5), ("Code excerpt", "Consolas", 9),
                                  ("Report note", "Times New Roman", 10.5)]:
            s = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            s.base_style = styles["Normal"]
            s.font.name, s.font.size = font, Pt(size)
            s.paragraph_format.space_after = Pt(0 if name in {"Report cell", "Code excerpt"} else 5)
            s.paragraph_format.line_spacing = 1.06
        styles["Code excerpt"].paragraph_format.left_indent = Inches(.10)
        styles["Code excerpt"].paragraph_format.right_indent = Inches(.10)
        footer = sec.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = footer.add_run("NudgeWell   |   HW5   |   ")
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor.from_string("536274")
        footer._p.append(element("fldSimple", instr="PAGE"))
        props = self.doc.core_properties
        props.title = "NudgeWell Model Refinement and Test Submission"
        props.subject = "Samsung Innovation Campus AI Capstone Homework 5"
        props.author = "NudgeWell Group 6"

    def p(self, text, style=None):
        return self.doc.add_paragraph(text, style)

    def h(self, text, *, template_heading=True, new_page=False):
        if template_heading:
            paragraph = self.headings.popleft()
            if paragraph.text != text:
                raise ValueError(f"Expected template heading {text!r}, got {paragraph.text!r}")
            self.doc.sections[0]._sectPr.addprevious(paragraph._p)
            paragraph.paragraph_format.keep_with_next = True
        else:
            paragraph = self.p(text, "Report subheading")
        if new_page:
            paragraph.paragraph_format.page_break_before = True
        return paragraph

    def caption(self, text, keep_next=False):
        p = self.p(text, "Report caption")
        p.paragraph_format.keep_with_next = keep_next
        return p

    def table(self, title, headers, rows, widths, numeric=()):
        total = sum(widths)
        widths = [width * self.width / total for width in widths]
        self.caption(title, keep_next=True)
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for column, width in zip(t.columns, widths):
            column.width = Inches(width)
        borders = element("tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            borders.append(element(side, val="single", sz="5", color="D9D9D9"))
        t._tbl.tblPr.append(borders)
        margins = element("tblCellMar")
        for side, twips in (("top", 58), ("bottom", 58), ("left", 105), ("right", 105)):
            margins.append(element(side, w=twips, type="dxa"))
        t._tbl.tblPr.append(margins)
        for idx, values in enumerate([headers, *rows]):
            row = t.rows[0] if idx == 0 else t.add_row()
            trp = row._tr.get_or_add_trPr()
            trp.append(element("cantSplit"))
            if idx == 0:
                trp.append(element("tblHeader"))
            for j, (cell, value, width) in enumerate(zip(row.cells, values, widths)):
                cell.width = Inches(width)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if idx == 0:
                    cell._tc.get_or_add_tcPr().append(element("shd", fill="EAF0F6"))
                p = cell.paragraphs[0]
                p.style = self.doc.styles["Report cell"]
                if j in numeric:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run(str(value)).bold = idx == 0
        spacer = self.doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(2)
        spacer.paragraph_format.line_spacing = Pt(2)

    def picture(self, name, caption, alt):
        p = self.doc.add_paragraph()
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pic = p.add_run().add_picture(str(HW5 / "figures" / name), width=Inches(self.width))
        pic._inline.docPr.set("descr", alt)
        self.caption(caption)

    def excerpt(self, filename, start, end, title, comment):
        lines = (CODE / filename).read_text(encoding="utf-8").splitlines()
        snippet = dedent("\n".join(lines[start - 1:end]))
        caption = self.caption(f"{title}   |   ", keep_next=True)
        add_link(caption, f"{filename}, lines {start}–{end}", f"code/nudgewell_hw5/{filename}")
        for line in ("# " + comment, *snippet.splitlines()):
            p = self.p(line, "Code excerpt")
            p.paragraph_format.keep_with_next = True
            p._p.get_or_add_pPr().append(element("shd", fill="F1F5F9"))
        p.paragraph_format.keep_with_next = False
        p.paragraph_format.space_after = Pt(7)


def fixed(num, digits=4):
    return f"{num:.{digits}f}"


def metric_row(label, result):
    values = [result[k] for k in ["pooled_AP", "participant_balanced_AP", "pooled_ROC_AUC"]]
    values.append(result["within_person"]["mean_ROC_AUC"])
    values += [result[k] for k in ["participant_balanced_Brier", "participant_balanced_log_loss"]]
    return [label, *(fixed(v) for v in values)]


def run_report(template):
    result_file = BUILD / "results" / f"{RUN}_evaluation.json"
    result = read_json(result_file)
    selection = read_json(BUILD / "results" / f"{RUN}_selection.json")
    verify = read_json(BUILD / "results" / f"{RUN}_verification.json")
    test = read_json(BUILD / "step5_validation.json")
    sealed = (BUILD / "protocol.sha256").read_text().split()[0]
    assert sha256(result_file) == verify["evaluation_sha256"]
    assert sha256(BUILD / "protocol.json") == result["protocol_sha256"] == selection["protocol_sha256"] == sealed
    assert test["passed"] and test["tests_run"] == 51
    nw, day = result["new_user"], result["known_user"]
    b, r = nw["fixed_baseline_selector"], nw["refined_selector"]
    g, pr, po = day["global"], day["personal_rate"], day["global_plus_daily_personal_offset"]
    primary, secondary = result["primary_contrast"], result["secondary_prespecified_contrast"]
    historical = read_json(HW5.parent / "04_data_preparation_model_exploration"
                           / "build" / "results" / "results_real.json")
    fmt_interval = lambda contrast, digits: " to ".join(f"{x:+.{digits}f}".replace("-", "−")
                                                      for x in contrast["interval"])
    report = Report(template)
    p, h, table = report.p, report.h, report.table

    h("Machine Learning Project Documentation")
    p("NudgeWell · Samsung Innovation Campus AI Capstone · Homework 5", "Report subtitle")
    p("Group 6 · Yusuf Ersel Kara, Bahadır Maral, Çağla Eryılmaz,\nFatih Mehmet Menteşe and Damla Nur Öcal", "Report subtitle")
    h("Model Refinement")
    h("1. Overview")
    p("We evaluated whether a refined model could rank high-gap check-ins for new users and whether past check-ins could improve probability estimates for known users. A high-gap check-in is one where the participant answered 5 or lower and used the phone for more than five further minutes. The predictors describe context at the check-in time (Zheng & Choe, 2026).")
    p(f"The refined procedure scored {fixed(r['participant_balanced_AP'])} on participant-balanced average precision (AP), compared with {fixed(b['participant_balanced_AP'])} for the fixed baseline. The interval spans zero. The daily offset yielded a small improvement in probability accuracy over the personal base rate.")
    h("2. Model Evaluation")
    hist = historical["global"]
    table("Table 1. Homework 4 historical leave-one-participant-out results", ["Model", "Pooled AP", "Pooled ROC-AUC", "Pooled Brier"],
          [(label, fixed(hist[k]["pr_auc"]), fixed(hist[k]["roc_auc"]), fixed(hist[k]["brier"]))
           for k, label in [("LR", "Logistic regression"), ("RF", "Random forest"), ("XGB", "XGBoost"), ("LGBM", "LightGBM")]],
          [2.68, 1.25, 1.48, 1.47], {1, 2, 3})
    p("Homework 4 showed modest discrimination for new users in its Figure 4 ROC and precision–recall curves. Its personal calibration could reuse information about the held-out person through scores fitted for peers. It also set alert thresholds from the evaluation scores, and its chronological row split could admit labels that were still unresolved at the test boundary.")
    h("3. Refinement Techniques")
    p("Homework 5 uses nested participant folds for selection, fits calibration inside permitted groups and saves alert thresholds before the outer evaluation. The daily procedure compares a fixed global model, a smoothed personal base rate and a daily log-odds offset fitted from resolved personal history. The change in folds and inputs makes the Homework 4 results useful as historical context. The direct comparison uses a fixed baseline rerun under Homework 5.")

    h("4. Hyperparameter Tuning", new_page=True)
    table("Table 2. Frozen search space and fixed reference", ["Family", "Search settings", "Fixed reference"],
          [("Logistic regression", "L2, C in {0.01, 0.1, 1, 10}, with or without balanced class weights.", "C = 1, balanced weights"),
           ("Random forest", "100 trees, depth in {3, 6}, minimum leaf size in {1, 5}, with or without balanced class weights.", "Depth 6, minimum leaf size 1, balanced weights")],
          [1.38, 3.63, 1.87])
    p("Each model setting was paired with both feature packs, yielding 32 structural candidates per outer fold. We selected the candidate with the highest participant-balanced AP on the assembled raw inner validation scores. Each participant had equal total weight. The fixed baseline used the same selection rule between the two fixed references on 15 inputs. Logistic regression won in all five folds.")
    p("The refined choices were logistic regression with C = 10 in three folds, logistic regression with C = 0.1 in one and a depth-3 forest with minimum leaf size 1 in one. All used balanced class weights. There were 160 candidate evaluations and 540 successful base fit jobs. The held-out tests assess the joint effects of feature selection, tuning and calibration.")
    h("5. Cross-Validation")
    p("We assigned people to five outer folds using the frozen label-blind split rule. Within each outer training set, three inner participant folds supplied validation scores for candidate selection. For the chosen candidate, each inner validation fold's sigmoid was fitted on scores from three cross-fitting folds confined to its inner training set. We kept sigmoid calibration when it lowered participant-balanced validation Brier loss. All five outer folds retained it (Varma & Simon, 2006).")
    p("We refitted the chosen base model on the full permitted outer training set and fitted its final sigmoid on raw inner out-of-fold scores. The alert cutoff used the 75th percentile of the corresponding inner validation probabilities. The daily simulation started after seven local calendar days, with each person's first observed timezone defining their day boundary. A history row qualified only if its prompt and lock were strictly before that day's cutoff.")
    h("6. Feature Selection")
    p("The five-input pack uses four cyclic encodings of local hour and weekday plus elapsed session time. The 15-input pack adds nine current-app category indicators and a missing-category flag. All five refined choices used the smaller pack. The selection result is conditional on this candidate grid. It does not isolate the value of app context in an otherwise identical model.")
    p("We excluded answers, remaining-use fields, identifiers and demographics from predictors. Interaction counts and daily app-use aggregates were also excluded because their timing relative to the prompt was uncertain. The 15-input model treats app category as context for the app open at the prompt, an assumption based on the release metadata.")

    h("Test Submission", new_page=True)
    h("1. Overview")
    p("The frozen protocol was recorded before we inspected the outer results. After 51 tests passed, we applied the five saved procedures to participants excluded from all upstream model and calibration fits. The held-out predictions come from nested cross-validation on the AwareMind cohort. This is a retrospective internal evaluation.")
    table("Table 3. Evaluation populations after data preparation", ["Population", "Check-ins", "Positives", "People", "Participant-days"],
          [("New users, outer held out", f"{r['rows']:,}", r["positives"], r["people"], "—"),
           ("Known users, after warmup", f"{po['rows']:,}", po["positives"], po["people"], result["known_user_coverage"]["participant_days"])],
          [2.78, 1.03, .83, .73, 1.51], {1, 2, 3, 4})
    h("2. Data Preparation for Testing")
    p("We removed 145 exact duplicates from 5,772 released rows, giving 5,627 check-ins and a positive rate of 12.76%. Current-app category was missing in 703 rows. The wider pack marks that gap explicitly, and both packs retain those rows. Elapsed time comes from the difference between unlock and prompt. A lock is used to resolve the target and determine history eligibility.")
    p("The model input order matches the fitted feature pack. The base pipeline fits median imputation within its training scope and standardizes inputs for logistic regression. Both then apply their saved transformations to evaluation rows. The daily comparison starts after 1,855 warmup rows. It omits one earlier unresolved lock from the relevant day's history and uses identical test rows for the three daily variants.")
    h("3. Model Application")
    p("Each held-out check-in receives a score from its fold's saved preprocessing, classifier and calibration map. The saved validation cutoff converts that score into an alert flag. The fixed rule flags check-ins between 00:00 and 05:59 local time, in a social app or more than ten minutes into a session.")
    report.excerpt("runner.py", 237, 240, "Applying the frozen procedure", "Score the held-out fold and apply its saved cutoff.")
    p("For known users, we compare the global score with two uses of resolved own history. The personal base rate shrinks the person's observed positive rate toward the smoothed prevalence in the other folds using ten prior check-ins. The offset shifts the global log odds by an intercept fitted with a zero-centered normal prior of standard deviation one. An empty history uses the peer prior and a zero offset. All 423 daily fits succeeded.")

    h("4. Test Metrics", new_page=True)
    p("Average precision (AP) measures precision over recall levels. ROC-AUC measures ranking, Brier loss measures squared probability error and log loss penalizes confident errors. The participant-balanced metrics make each person's total row weight equal. Single-class groups remain in pooled metrics and are excluded when computing within-group AUC.")
    names = [("Fixed baseline", b), ("Fixed random forest", nw["fixed_RF"]),
             ("Refined procedure", r), ("Fold prevalence", nw["population_prior"])]
    metrics_header = ["Procedure", "Pooled\nAP", "Balanced\nAP", "Pooled\nAUC", "Within-person\nAUC", "Balanced\nBrier", "Balanced\nlog loss"]
    metrics_widths = [1.57, .68, .87, .68, 1.13, .97, .98]
    table("Table 4. New-user held-out results on 5,627 matched check-ins", metrics_header,
          [metric_row(label, item) for label, item in names], metrics_widths, set(range(1, 7)))
    def stage_range(name, stage, metric):
        v = [f["stage_diagnostics"][name][stage][metric] for f in selection["folds"]]
        return f"{min(v):.4f}–{max(v):.4f}"
    stage_rows = []
    for name, stage in [("Training", "training_resubstitution_optimistic"),
                        ("Inner validation", "inner_validation_selection_diagnostic")]:
        stage_rows.append([name, *(stage_range(m, stage, metric) for m in
                                   ("fixed_baseline_selector", "refined_selector") for metric in
                                   ("participant_balanced_AP", "participant_balanced_Brier"))])
    stage_rows.append(["Outer evaluation", fixed(b["participant_balanced_AP"]), fixed(b["participant_balanced_Brier"]),
                       fixed(r["participant_balanced_AP"]), fixed(r["participant_balanced_Brier"])])
    table("Table 5. Training, inner validation and outer evaluation", ["Stage", "Fixed\nbalanced AP", "Fixed\nBrier", "Refined\nbalanced AP", "Refined\nBrier"],
          stage_rows, [1.48, 1.35, 1.35, 1.35, 1.35], {1, 2, 3, 4})
    p("Training and inner validation cells show ranges across five folds. Training scores reuse fitted rows and inner validation scores informed selection. Outer scores pool held-out predictions across all folds. The refined inner diagnostics use the selected sigmoid. The AP criterion for selecting the structure uses the raw inner scores.", "Report note")
    report.picture("step6_new_user.png", "Figure 1. New-user precision, recall and probability reliability. Markers show the saved operating points.",
                   "New-user precision-recall curves and reliability bins for the fixed and refined procedures.")
    p(f"The prespecified balanced AP difference was {primary['point_difference']:+.4f} ({fmt_interval(primary, 4)} paired 95% interval). The refined procedure lowered Brier and log loss descriptively, with values close to the fold prevalence reference. Within-person AUC uses 34 of 37 people. Pooled AUC also compares scores across people and folds.")

    h("Daily Personalization", template_heading=False, new_page=True)
    table("Table 6. Daily comparison on 3,772 matched check-ins", metrics_header,
          [metric_row(label, item) for label, item in [("Global model", g), ("Personal base rate", pr), ("Daily personal offset", po)]],
          metrics_widths, set(range(1, 7)))
    p(f"The prespecified Brier reduction versus the personal base rate was {secondary['point_difference']:.5f} ({fmt_interval(secondary, 5)} paired 95% interval). Brier loss fell for 20 people and rose for 17. The personal base rate already ranks well across people and gives each check-in on a given person-day the same score.")
    report.picture("step6_daily_personalization.png", "Figure 2. Ranking and reliability for the three matched daily procedures.",
                   "Daily personalized scores rank strongly when pooled. The offset and global scores have equal within-day ROC-AUC.")
    p(f"The daily offset preserved all observed within-day rankings and ties. Mean within-day AUC was {fixed(po['within_person_day']['mean_ROC_AUC'])} for both the global and offset models and {fixed(pr['within_person_day']['mean_ROC_AUC'])} for the personal base rate. That comparison uses 150 of 423 participant-days with both labels. The within-person AUC across days uses 29 of 37 people and fell from {fixed(g['within_person']['mean_ROC_AUC'])} to {fixed(po['within_person']['mean_ROC_AUC'])} after the offset.")
    report.picture("step6_paired_contrasts.png", "Figure 3. Both prespecified contrasts with paired participant bootstrap intervals.",
                   "The interval for new-user AP crosses zero. The interval for daily Brier reduction stays above zero.")
    p("Both intervals use 2,000 paired participant resamples with the fitted procedures held fixed. The peer archive excludes the evaluated fold and contains peer outcomes at or after the target cutoff on 418 of 423 days. The strict cutoff applies to the evaluated person's own history.", "Report note")

    h("Decisions at the Saved Cutoffs", template_heading=False, new_page=True)
    operations = [("New: fixed baseline", b["decisions"]), ("New: refined", r["decisions"]),
                  ("New: fixed rule", nw["fixed_rule"]), ("Daily: global", g["decisions"]),
                  ("Daily: personal rate", pr["decisions"]), ("Daily: offset", po["decisions"])]
    table("Table 7. Observed alerts and classification outcomes",
          ["Procedure", "TP", "FP", "FN", "TN", "Precision", "Recall", "Alert share"],
          [[label, *(f"{m[k]:,}" for k in ("tp", "fp", "fn", "tn")),
            *(f"{m[k]:.2%}" for k in ("precision", "recall", "actual_alert_share"))] for label, m in operations],
          [1.73, .49, .55, .49, .63, 1, .9, 1.09], set(range(1, 8)))
    p("The refined procedure raised fewer alerts and had lower recall than the fixed learned baseline. At their respective operating points, the fixed rule had higher precision and recall than either model. All daily variants shared the same global cutoff within each fold. The offset raised 26 fewer false alerts and caught one fewer positive than the base rate. The 25% alert target applies to inner validation.")
    h("5. Model Deployment")
    p("The completed work runs offline in Python and produces binary-risk probabilities, alert flags and aggregate diagnostics. The concept note's continuous-gap regression benchmark, neural models, Android integration, prompt budgeting and user study remain future project work. A device build would require a verified input pipeline, permission to deploy the fitted models and testing of inference and user-facing interventions.")
    h("6. Code Implementation")
    p("The refinement path generates calibration-fit scores inside the inner training scope and applies the fitted calibration map to its separate validation fold.")
    report.excerpt("selector.py", 88, 94, "Nested calibration during refinement",
                   "Fit on permitted scores and apply to the separate validation block.")
    p("During test application the daily split marks the labels available at the start of a day. The masked history feeds the offset fit, and the day's test rows supply all three predictions. See the frozen prediction excerpt under Model Application.")
    report.excerpt("splits.py", 163, 165, "Label availability for daily testing",
                   "Only own rows with a completed lock before this cutoff enter history.")

    h("Conclusion", new_page=True)
    p("The refined procedure produced more accurate probability levels than the fixed learned baseline on the observed check-ins, while the prespecified comparison found no clear gain in new-user ranking. The daily offset modestly reduced mean probability error relative to the smoothed personal base rate. Its within-day ordering came from the global model. Participant results varied, and the offset's cross-day within-person ranking was weaker than the global model's in this sample.")
    p("The independent review traced the outer participant exclusions, nested calibration, saved alert cutoffs and daily label timing. It reconciled the metrics and paired intervals to the saved outputs and found no material leakage or numerical error affecting the run. The evaluated cohort is small, the data were previously explored and the reference archive uses later peer outcomes. These conditions limit claims about a new cohort, prospective performance and intervention effectiveness.")
    h("Reproducibility", template_heading=False)
    p("From the repository root, set the path to the local release CSV and choose an unused run ID. The protocol records seed 42 for assignments and fitting and seed 20261116 for the paired bootstrap. The runner checks code and artifact fingerprints and runs the test gate before applying checkpoints.")
    for line in [
        '$hw5Path = "deliverables/05_model_refinement_test_submission"',
        '$hw5Csv = "path/to/full_data_all_feature.csv"',
        '$hw5Run = "hw5-v1-reproduction"',
        'python "$hw5Path/code/run_refinement.py" --csv $hw5Csv --run-id $hw5Run --phase select',
        'python "$hw5Path/code/run_refinement.py" --csv $hw5Csv --run-id $hw5Run --phase evaluate',
    ]:
        p(line, "Code excerpt")
    p("Tested software was Python 3.11.9, scikit-learn 1.8.0, NumPy 2.2.6, pandas 2.3.3 and SciPy 1.16.3. Row predictions, fitted checkpoints and private histories are kept in the ignored run directory.", "Report note")
    h("References")
    refs = [
        ("Zheng, J., & Choe, E. K. (2026). To stop or not to stop: Exploring the intention-behavior gaps in smartphone usage. arXiv.", "Paper", "https://doi.org/10.48550/arXiv.2609.08909"),
        ("Zheng, J., & Choe, E. K. (2026). AwareMind data and dictionaries [Data and materials]. Open Science Framework.", "Data repository", "https://osf.io/x6yzs/"),
        ("Varma, S., & Simon, R. (2006). Bias in error estimation when using cross-validation for model selection. BMC Bioinformatics, 7, 91.", "Article", "https://doi.org/10.1186/1471-2105-7-91"),
        ("Scikit-learn developers. (n.d.). Scikit-learn 1.8 documentation.", "Average precision", "https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.average_precision_score.html"),
        ("NumPy developers. (n.d.). NumPy 2.2 reference.", "Quantile and the higher method", "https://numpy.org/doc/2.2/reference/generated/numpy.quantile.html"),
        ("NudgeWell Group 6. HW5 evaluation protocol v1.0.0, verified evaluation aggregates, and independent review. Project repository companion files.", None, None),
    ]
    for text, label, url in refs:
        para = p(text + (" " if label else ""), "Report note")
        if label:
            add_link(para, label, url)
    if report.headings:
        raise ValueError(f"Unfilled section starting at {report.headings[0].text!r}")
    report.doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path, help="Path to the original instructor DOCX.")
    run_report(parser.parse_args().template)
