# Homework 2 · Literature, Data & Technology Review

**NudgeWell · Group 6 · due 12 October 2026**

Start with the report. The supplement presents the same analysis visually, including an interactive version of the check-in question that the study's participants answered.

| File | What it is |
|---|---|
| [`NudgeWell_Group6_Literature_Data_Technology_Review.pdf`](NudgeWell_Group6_Literature_Data_Technology_Review.pdf) | **The report** (19 pages). Part 1: Literature Review (14 studies in four themes). Part 2: Data Research (AwareMind analysis, data quality, KVKK ethics). Part 3: Technology Review (comparison tables). APA 7 references after each part |
| `NudgeWell_Group6_Literature_Data_Technology_Review.docx` | The report as a Word file |
| `NudgeWell_Group6_Literature_Data_Technology_Review_Supplement.html` | **Interactive supplement.** [Open it in the browser](https://raw.githack.com/edasaruhan/SIC_AI_18_Capstone_Group_6/main/deliverables/02_literature_data_technology_review/NudgeWell_Group6_Literature_Data_Technology_Review_Supplement.html), or download the file and open it offline. GitHub itself shows HTML files as code |
| [`NudgeWell_Group6_Literature_Data_Technology_Review_Supplement.pdf`](NudgeWell_Group6_Literature_Data_Technology_Review_Supplement.pdf) | A static 7-page copy of the supplement |
| [`figures/`](figures/) | The five figures in Part 2 |
| [`../../notebooks/01_awaremind_eda.ipynb`](../../notebooks/01_awaremind_eda.ipynb) | The analysis notebook behind every statistic in Part 2 and in the supplement |
| [`build/`](build/) | How the documents were made: `report.md` (the report text), `build_report.py` and `render_docx.ps1` (Word file and PDF), `build_supplement.py` (supplement), `eda_summary.json` (every statistic), `CITATION_LOG.md` and `references_verified.json` (how each of the 38 sources was checked) |

The supplement's "Supplementary analysis" (what people did after each answer from 1 to 10) is not in the report. It comes from the same notebook.

## Rebuilding (optional)

This needs Python with pandas, matplotlib, python-docx and Jupyter; Microsoft Word for the table of contents and the report PDF; and Microsoft Edge for the supplement PDF. The AwareMind files must first be placed in `data/raw/awaremind/` (see [data/README.md](../../data/README.md)).

From the repository root:

```bash
cd notebooks
jupyter nbconvert --to notebook --execute --inplace 01_awaremind_eda.ipynb
cd ../deliverables/02_literature_data_technology_review/build
python -I build_report.py
powershell -NoProfile -ExecutionPolicy Bypass -File render_docx.ps1 -InputPath ../NudgeWell_Group6_Literature_Data_Technology_Review.docx -OutputPdf ../NudgeWell_Group6_Literature_Data_Technology_Review.pdf
python -I build_supplement.py --pdf
```
