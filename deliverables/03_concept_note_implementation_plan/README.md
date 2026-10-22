# Homework 3 · Concept Note and Implementation Plan

**NudgeWell · Group 6 · due 20 October 2026**

This is the instructor's template, filled in. It has two parts: a concept note with seven sections and an implementation plan with six.

| File | What it is |
|---|---|
| [`NudgeWell_Group6_Concept_Note_Implementation_Plan.pdf`](NudgeWell_Group6_Concept_Note_Implementation_Plan.pdf) | **The concept note and implementation plan** (17 pages). See the section list below |
| `NudgeWell_Group6_Concept_Note_Implementation_Plan.docx` | The same document as a Word file |
| [`figures/`](figures/) | Figure 1 (architecture) and Figure 2 (Gantt chart) |
| [`build/`](build/) | How the document was made. See the file list below |

**The concept note covers:**
- project overview (SDG 3, target 3.4);
- six objectives with success criteria;
- background;
- methodology;
- architecture;
- data sources;
- literature review.

**The implementation plan covers:**
- technology stack;
- a four-week timeline, with a Gantt chart and a task-distribution matrix;
- milestones;
- challenges and mitigations;
- ethical considerations;
- APA 7 references.

**The `build/` folder holds:**
- `concept_note.md`: the text;
- `build_sections.py`: fills the template;
- `make_figures.py`: draws both figures, and its task list is the source of the Gantt chart;
- `render_docx.ps1`: produces the PDF through Word;
- `fixed_rule_baselines.py` and `.json`: the fixed-rule check behind Background Table 3.

The statistics in the Background section come from the AwareMind analysis of Homework 2. See the [analysis notebook](../../notebooks/01_awaremind_eda.ipynb) and the [data card](../../data/README.md).

## Rebuilding (optional)

You need:
- Python with matplotlib and python-docx;
- Microsoft Word, to make the PDF;
- the instructor's template, saved as `guidelines/Concept_Note_and_Implementation_Plan_Template.docx` at the repository root. The template is not in this repository.

From the repository root:

```bash
cd deliverables/03_concept_note_implementation_plan/build
python -I make_figures.py
python -I build_sections.py
powershell -NoProfile -ExecutionPolicy Bypass -File render_docx.ps1 -InputPath ../NudgeWell_Group6_Concept_Note_Implementation_Plan.docx -OutputPdf ../NudgeWell_Group6_Concept_Note_Implementation_Plan.pdf
```

`python -I fixed_rule_baselines.py` recomputes Background Table 3. It needs pandas and the AwareMind files in `data/raw/awaremind/`, which are not included here.
