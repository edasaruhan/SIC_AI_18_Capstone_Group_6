# Homework 4 · Data Preparation / Feature Engineering and Model Exploration

**NudgeWell · Group 6 · submitted 31 October 2026**

This is the instructor's template, filled in. Part I covers data preparation and feature engineering in six sections; Part II covers model exploration in four.

| File | What it is |
|---|---|
| [`NudgeWell_Group6_Data_Preparation_Model_Exploration.pdf`](NudgeWell_Group6_Data_Preparation_Model_Exploration.pdf) | **The report** (13 pages). See the section list below |
| `NudgeWell_Group6_Data_Preparation_Model_Exploration.docx` | The same report as a Word file |
| [`code/hw4_pipeline.py`](code/hw4_pipeline.py) | **The whole analysis in one script**: duplicate removal, leakage guard, 49 features, both evaluation regimes and every number in the report |
| [`figures/`](figures/) | Figures 1–7 |
| [`build/`](build/) | How the report was made. See the file list below |
| [`requirements.txt`](requirements.txt) | Python dependencies for the analysis and report builders |

**Part I covers:**
- overview and the high-gap label;
- data collection, data-use terms and the other datasets considered;
- data cleaning: 145 duplicate rows, missing values, skew and leakage control;
- exploratory analysis: night, app category and differences between people;
- 49 features in five groups;
- data transformation, with the feature code.

**Part II covers:**
- candidate models: logistic regression, random forest, XGBoost, LightGBM, and the temporal model planned for the next milestone;
- training: leave-one-participant-out for new users, and a chronological 70/30 split per person for known users;
- evaluation against a fixed rule, a personal intercept and the chance level of each regime, with 95% confidence intervals;
- code excerpts and pipeline checks on synthetic data;
- APA 7 references.

**Main results** (5,627 unique check-ins):
- **New users:** ROC-AUC 0.56–0.62. A three-signal rule (night, social media or a session longer than 10 minutes) scores 0.60 and is more precise at the same alert rate.
- **Known users:** the global model plus one number per person reaches ROC-AUC 0.84, the same as a personal random forest. Ranking a person's own moments stays near 0.60 for every approach.

**The `build/` folder holds:**
- `make_figures.py`: Figures 1–7, drawn from the results;
- `build_docx.py`: writes the Word file; the numbers come from `results/` and the code excerpts from `code/hw4_pipeline.py`;
- `render_docx.ps1`: produces the PDF through Word;
- `sim_seeds.py` and `sim_checks.py`: the pipeline checks on synthetic data (Table 6);
- `results/`: aggregate results as JSON, with no participant codes.

## Rebuilding (optional)

You need:
- Python 3.11 with numpy, pandas, scipy, scikit-learn 1.8, xgboost 3.2, lightgbm 4.7, matplotlib and python-docx;
- Microsoft Word, to make the PDF;
- the AwareMind file in `data/raw/awaremind/`. It is not included; see [data/README.md](../../data/README.md).

From the repository root:

```bash
cd deliverables/04_data_preparation_model_exploration
python -m pip install -r requirements.txt
python -I code/hw4_pipeline.py ../../data/raw/awaremind/full_data_all_feature.csv run
python -I build/make_figures.py run/results.json run/predictions.csv figures
cp run/results.json build/results/results_real.json
cd build
python -I build_docx.py results/results_real.json results/sim_seeds.json results/sim_results.json ../NudgeWell_Group6_Data_Preparation_Model_Exploration.docx
powershell -NoProfile -ExecutionPolicy Bypass -File render_docx.ps1 -InputPath ../NudgeWell_Group6_Data_Preparation_Model_Exploration.docx -OutputPdf ../NudgeWell_Group6_Data_Preparation_Model_Exploration.pdf
```

The `run/` folder holds held-out scores for every check-in (`predictions.csv`). It is ignored by git and must stay out of the repository.

The synthetic checks (`sim_seeds.py`, `sim_checks.py`) need the project's synthetic data generator, which is not in this repository.
