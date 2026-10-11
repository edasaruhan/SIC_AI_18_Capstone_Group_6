# NudgeWell · Group 6

**Samsung Innovation Campus (SIC) AI, Cohort 18 · Digital Addiction Capstone, in partnership with Yeşilay**
Instructor: Eda Nur Saruhan

NudgeWell predicts the **intention–behavior gap** within a single phone session: the moment a person feels they should stop using their phone but keeps going. When the prediction is confident, an opt-in Android prototype offers one short alternative that the user chose in advance; otherwise it stays quiet. The model is built on the public AwareMind dataset (Zheng & Choe, 2026): 5,772 in-session check-ins from 37 US adults.

## Homework submissions

| # | Homework | Due | Start here | Also in the folder |
|---|---|---|---|---|
| 1 | **Idea Proposal** | 24 Sep 2026 | [1-page proposal (PDF)](deliverables/01_idea_proposal/NudgeWell_Group6_Idea_Proposal_1page.pdf) | Pitch deck in English and Turkish (PDF and PPTX), speaker notes, the proposal as a Word file |
| 2 | **Literature, Data & Technology Review** | 12 Oct 2026 | [Report (PDF, 19 pages)](deliverables/02_literature_data_technology_review/NudgeWell_Group6_Literature_Data_Technology_Review.pdf) | [Interactive supplement](https://htmlpreview.github.io/?https://github.com/edasaruhan/SIC_AI_18_Capstone_Group_6/blob/main/deliverables/02_literature_data_technology_review/NudgeWell_Group6_Literature_Data_Technology_Review_Supplement.html) (opens in the browser) and its [PDF copy](deliverables/02_literature_data_technology_review/NudgeWell_Group6_Literature_Data_Technology_Review_Supplement.pdf); figures; analysis notebook; build sources |

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

```
deliverables/
├── 01_idea_proposal/                       Homework 1
└── 02_literature_data_technology_review/   Homework 2
    ├── figures/                            the five figures in Part 2 of the report
    └── build/                              report text, build scripts, statistics, citation log
notebooks/
└── 01_awaremind_eda.ipynb                  analysis behind every statistic in Homework 2
data/
└── README.md                               dataset card (the data files are not included)
```

## Data and privacy

The AwareMind data files are **not** in this repository. OSF lists no licence for them, so we use them for coursework analysis only and will ask the authors for written permission before model training or publication. To reproduce the analysis, download the files from [osf.io/x6yzs](https://osf.io/x6yzs/) into `data/raw/awaremind/` (ignored by git) and run the notebook from `notebooks/`; see [data/README.md](data/README.md).

Everything published here is aggregated: no participant codes, app package names or exact timestamps.

## Main source

Zheng, J., & Choe, E. K. (2026). *To stop or not to stop: Exploring the intention-behavior gaps in smartphone usage* (arXiv:2609.08909) [Preprint, MobileHCI 2026]. arXiv. https://doi.org/10.48550/arXiv.2609.08909
