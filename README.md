# NudgeWell · Group 6

**Samsung Innovation Campus (SIC) AI, Cohort 18 · Digital Addiction Capstone, in partnership with Yeşilay**
Instructor: Eda Nur Saruhan

NudgeWell evaluates high-gap prediction on previously collected check-ins and serves a verified reference model on desktop. A high-gap check-in combines a survey answer of 5 or lower with more than five minutes of further phone use. The AwareMind release contains 5,772 check-ins from 37 US adults, of which 5,627 are unique. Eşik, an earlier Android prototype, illustrates the intended phone interaction separately.

HW5 found no clear new-user ranking gain from refinement. A daily personal offset modestly improved probability accuracy over a personal base rate. HW6 verifies export and local serving for one global HW5 fold. The showcase can run the same API through a data-free synthetic fixture. [Final handoff and showcase](deliverables/06_deployment/showcase/SUBMISSION.md)

## Homework submissions

| # | Homework | Due | Start here | Also in the folder |
|---|---|---|---|---|
| 1 | **Idea Proposal** | 24 Sep 2026 | [1-page proposal (PDF)](deliverables/01_idea_proposal/NudgeWell_Group6_Idea_Proposal_1page.pdf) | Pitch deck in English and Turkish (PDF and PPTX), speaker notes, the proposal as a Word file |
| 2 | **Literature, Data & Technology Review** | 12 Oct 2026 | [Report (PDF, 19 pages)](deliverables/02_literature_data_technology_review/NudgeWell_Group6_Literature_Data_Technology_Review.pdf) | [Interactive supplement](https://htmlpreview.github.io/?https://github.com/edasaruhan/SIC_AI_18_Capstone_Group_6/blob/main/deliverables/02_literature_data_technology_review/NudgeWell_Group6_Literature_Data_Technology_Review_Supplement.html) (opens in the browser) and its [PDF copy](deliverables/02_literature_data_technology_review/NudgeWell_Group6_Literature_Data_Technology_Review_Supplement.pdf); figures; analysis notebook; build sources |
| 3 | **Concept Note & Implementation Plan** | 20 Oct 2026 | [Concept note and plan (PDF, 17 pages)](deliverables/03_concept_note_implementation_plan/NudgeWell_Group6_Concept_Note_Implementation_Plan.pdf) | The document as a Word file; architecture diagram and Gantt chart; build sources |
| 4 | **Data Preparation / Feature Engineering and Model Exploration** | – | [Report (PDF, 13 pages)](deliverables/04_data_preparation_model_exploration/NudgeWell_Group6_Data_Preparation_Model_Exploration.pdf) | The report as a Word file; seven figures; [the analysis script](deliverables/04_data_preparation_model_exploration/code/hw4_pipeline.py) behind every number; build sources and aggregate results |
| 5 | **Model Refinement and Test Submission** | 12 Nov 2026 | [Report (PDF, 7 pages)](deliverables/05_model_refinement_test_submission/NudgeWell_HW5_Model_Refinement_and_Test_Submission.pdf) | [Word report](deliverables/05_model_refinement_test_submission/NudgeWell_HW5_Model_Refinement_and_Test_Submission.docx), frozen protocol, evaluation code and tests, figures, and aggregate results |
| 6 | **Deployment** | – | [Report (PDF)](deliverables/06_deployment/NudgeWell_Group6_HW6_Deployment.pdf) | [Word report](deliverables/06_deployment/NudgeWell_Group6_HW6_Deployment.docx), local serving code, tests, and aggregate export and benchmark evidence |

Each homework folder has its own README that lists every file.

## Team

| Name | GitHub |
|---|---|
| Yusuf Ersel Kara | [@erselk](https://github.com/erselk) |
| Bahadır Maral | [@Thynatos](https://github.com/Thynatos) |
| Çağla Eryılmaz | [@caglaery](https://github.com/caglaery) |
| Fatih Mehmet Menteşe | [@fatihh240](https://github.com/fatihh240) |
| Damla Nur Öcal | – |

## Repository layout

For Python and Jupyter setup and the workflow for switching between PC and Mac, see [Development setup](DEVELOPMENT.md).

```
deliverables/
├── 01_idea_proposal/                       Homework 1
├── 02_literature_data_technology_review/   Homework 2
│   ├── figures/                            the five figures in Part 2 of the report
│   └── build/                              report text, build scripts, statistics, citation log
├── 03_concept_note_implementation_plan/    Homework 3
│   ├── figures/                            architecture diagram and Gantt chart
│   └── build/                              document text, build and figure scripts, fixed-rule check
├── 04_data_preparation_model_exploration/  Homework 4
│   ├── code/                               the analysis script behind every number
│   ├── figures/                            Figures 1–7
│   └── build/                              figure and Word-file scripts, synthetic-data checks, results
├── 05_model_refinement_test_submission/   Homework 5
│   ├── code/                               participant-aware selection and evaluation
│   ├── tests/                              synthetic unit and integration checks
│   ├── figures/                            three evaluation figures
│   └── build/                              frozen protocol, aggregate results, and report scripts
└── 06_deployment/                          Homework 6
    ├── code/                               HW5 model export and loopback serving
    ├── tests/                              serialization, API, and integrity checks
    └── build/                              aggregate evidence and report scripts
notebooks/
└── 01_awaremind_eda.ipynb                  analysis behind every statistic in Homework 2
data/
└── README.md                               dataset card (the data files are not included)
```

## Data and privacy

The AwareMind data files are **not** in this repository. OSF lists no licence for them, so we use them for coursework analysis only, including the exploratory models of Homework 4, and will ask the authors for written permission before any model is published or deployed. To reproduce the analysis, download the files from [osf.io/x6yzs](https://osf.io/x6yzs/) into `data/raw/awaremind/` (ignored by git), then run the notebook from `notebooks/` (Homework 2) or the Homework 4 script; see [data/README.md](data/README.md).

Everything published here is aggregated: no participant codes, app package names or exact timestamps.

## Main source

Zheng, J., & Choe, E. K. (2026). *To stop or not to stop: Exploring the intention-behavior gaps in smartphone usage* (arXiv:2609.08909) [Preprint, MobileHCI 2026]. arXiv. https://doi.org/10.48550/arXiv.2609.08909
