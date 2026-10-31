# Data

**No data files are stored in this repository.** This card describes the data the project uses and how to obtain it.

## AwareMind: "Intention-Behavior Gap in Smartphone Usage" (primary)

| | |
|---|---|
| **Source** | OSF project [osf.io/x6yzs](https://osf.io/x6yzs/) by J. Zheng and E. K. Choe. Paper: https://doi.org/10.48550/arXiv.2609.08909 (MobileHCI 2026) |
| **Files we use** | `full_data_all_feature.csv` (4.3 MB), its data dictionary `full_data_all_feature_dictonary.md`, and `app_categorization_dictionary.md` |
| **Content** | 5,772 in-session check-ins from 37 US adults, 92 columns, July–October 2025. During a session, the AwareMind Android app asked "I should ___ using my phone now" (1 = stop … 10 = continue) and logged use until the screen locked. 145 rows are exact copies of another row, all from one participant, so the file holds 5,627 unique check-ins |
| **Target** | `intention_behavior_gap` = `remaining_scaled` − `answer`. Homework 4 uses a binary label: answer 5 or lower and more than 5 further minutes of use |
| **Licence** | OSF lists **no licence**. The paper's CC BY 4.0 licence covers the article, not the data. We use the data for coursework analysis only, including the exploratory models of Homework 4, and will obtain written permission from the authors before any model is published or deployed |

### To reproduce our analysis

1. Download the three files above from OSF into `data/raw/awaremind/`. That folder is listed in `.gitignore`, so the data cannot be committed by accident.
2. Run `notebooks/01_awaremind_eda.ipynb` from the `notebooks/` folder (Homework 2).
3. Run `deliverables/04_data_preparation_model_exploration/code/hw4_pipeline.py` (Homework 4); see that folder's README.

### Handling rules

- Never commit raw or processed data files.
- Share only aggregated results: no participant codes, app package names or exact timestamps.
- Target leakage: the survey answer, the `remaining_*` columns, `lock_time` and the undocumented `temp_scaled` reveal the target, so they are never model inputs.
- Duplicates: drop the 145 exact duplicate rows before analysis (Homework 2 still used all 5,772 rows).
- Demographics: the 15 demographic columns are constant within a person and unique for each participant, so they act as identifiers. Keep them out of cross-user models.
- Evaluation: leave-one-participant-out splits for new users; chronological splits within each person for personalization.

## Other datasets considered

- **one sec** ([osf.io/bmjat](https://osf.io/bmjat/); Haliburton et al., 2024): app-opening intervention logs from 1,039 users. Reserved for an optional intervention-response analysis; it has no intention labels.
- **Child Mind Institute Problematic Internet Use** (Kaggle): rejected, because its labels are per person and it has no phone sessions.
