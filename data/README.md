# Data

**No data files are stored in this repository.** This card describes the data the project uses and how to obtain it.

## AwareMind: "Intention-Behavior Gap in Smartphone Usage" (primary)

| | |
|---|---|
| **Source** | OSF project [osf.io/x6yzs](https://osf.io/x6yzs/) by J. Zheng and E. K. Choe. Paper: https://doi.org/10.48550/arXiv.2609.08909 (MobileHCI 2026) |
| **Files we use** | `full_data_all_feature.csv` (4.3 MB), its data dictionary `full_data_all_feature_dictonary.md`, and `app_categorization_dictionary.md` |
| **Content** | 5,772 in-session check-ins from 37 US adults, 92 columns, July–October 2025. During a session, the AwareMind Android app asked "I should ___ using my phone now" (1 = stop … 10 = continue) and logged use until the screen locked |
| **Target** | `intention_behavior_gap` = `remaining_scaled` − `answer` |
| **Licence** | OSF lists **no licence**. The paper's CC BY 4.0 licence covers the article, not the data. We use the data for coursework analysis only and will obtain written permission from the authors before model training or publication |

### To reproduce our analysis

1. Download the three files above from OSF into `data/raw/awaremind/`. That folder is listed in `.gitignore`, so the data cannot be committed by accident.
2. Run `notebooks/01_awaremind_eda.ipynb` from the `notebooks/` folder.

### Handling rules

- Never commit raw or processed data files.
- Share only aggregated results: no participant codes, app package names or exact timestamps.
- Target leakage: the survey answer, the `remaining_*` columns, `lock_time` and the undocumented `temp_scaled` reveal the target, so they are never model inputs.
- Evaluation: leave-one-participant-out splits for new users; chronological splits within each person for personalization.

## Other datasets considered

- **one sec** ([osf.io/bmjat](https://osf.io/bmjat/); Haliburton et al., 2024): app-opening intervention logs from 1,039 users. Reserved for an optional intervention-response analysis; it has no intention labels.
- **Child Mind Institute Problematic Internet Use** (Kaggle): rejected, because its labels are per person and it has no phone sessions.
