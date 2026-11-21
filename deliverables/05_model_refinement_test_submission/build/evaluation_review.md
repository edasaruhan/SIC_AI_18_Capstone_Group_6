# HW5 frozen evaluation

**NudgeWell, Group 6 · Step 6 · 21 November 2026**

The refined procedure showed **no clear gain in new-user ranking**. Its participant-balanced average precision fell from 0.1727 to 0.1558, a difference of **−0.0169** with a paired 95% interval of **[−0.0652, +0.0222]**. Daily personalization gave a small probability accuracy gain over the personal base rate, reducing participant-balanced Brier loss by **0.00159** with a paired interval of **[0.00048, 0.00275]**. [Aggregate evaluation](results/hw5-v1-step5-20261117_evaluation.json) · [Paired contrasts](../figures/step6_paired_contrasts.png)

## Evaluation design and coverage

The runner applied the five saved v1.0.0 procedures to their held-out participants. Their training, preprocessing, candidate selection, calibration and alert cutoffs came from the permitted outer-training data. All 51 synthetic tests passed before evaluation. The new-user analysis covers **5,627 check-ins, 718 positives and 37 participants**. The daily analysis covers **3,772 check-ins, 484 positives and 423 participant-days** from the same 37 participants after the seven-calendar-day warmup. The global score, personal base rate and daily offset use identical daily rows. Each update uses own outcomes that resolved strictly before the day cutoff. All 423 daily state fits succeeded. [Frozen protocol](protocol.json) · [Verification](results/hw5-v1-step5-20261117_verification.json)

This is a retrospective internal evaluation of the existing cohort. The fixed peer archive excludes the evaluated person's outer fold and includes peer outcomes that resolved at or after the target cutoff on 418 of 423 days. The strict day cutoff governs the evaluated person's own history. Participants receive equal total weight in the balanced metrics. Both 95% intervals use 2,000 paired participant resamples of the saved predictions, with the fitted procedures held fixed. They reflect variation across evaluated participants conditional on those fits. [Frozen protocol](protocol.json) · [Independent evidence review](independent_review.md)

## New-user results

| Procedure | Pooled AP | Balanced AP ↑ | Pooled ROC-AUC | Within-person ROC-AUC | Balanced Brier ↓ | Balanced log loss ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Fixed baseline selector | 0.1716 | 0.1727 | 0.6009 | 0.6325 | 0.2410 | 0.6767 |
| Fixed random forest | 0.1663 | 0.1697 | 0.5867 | 0.6325 | 0.2180 | 0.6278 |
| Refined selector | 0.1558 | 0.1558 | 0.5407 | 0.6389 | 0.1163 | 0.3960 |
| Excluded-fold prevalence | 0.1125 | 0.1149 | 0.4311 | 0.5000 | 0.1169 | 0.3982 |

The fixed baseline selected logistic regression in all five folds. The refined selector chose the five time/session inputs and sigmoid calibration in every fold, with logistic regression in four folds and random forest in one. The refined procedure had lower Brier and log losses than the fixed models, with values close to the prevalence reference. These are descriptive comparisons of the complete procedures, which differ in candidate selection, feature pack and calibration. The prespecified ranking contrast remains uncertain. Pooled ranking compares across people and folds, while within-person ROC-AUC averages the rankings of eligible people's own check-ins. Within-person coverage is **34 of 37 participants**. The prevalence reference assigns one probability per fold, so its within-person AUC is 0.5 and its pooled AUC reflects differences between folds. [Aggregate evaluation](results/hw5-v1-step5-20261117_evaluation.json) · [New-user precision, recall and reliability](../figures/step6_new_user.png)

### Training and selection diagnostics

These are ranges across the five outer training universes. The training column scores the rows used to fit the final procedure in each fold. The inner validation column scores inner-held-out rows and also informs selection. The held-out scores above aggregate the outer predictions across all folds. The refined inner diagnostics below use the chosen calibration map for each fold. Structural selection used uncalibrated inner AP. [Selection trace](results/hw5-v1-step5-20261117_selection.json)

| Procedure | Training balanced AP | Inner validation balanced AP | Training balanced Brier | Inner validation balanced Brier |
|---|---:|---:|---:|---:|
| Fixed baseline selector | 0.1782–0.2166 | 0.1436–0.1911 | 0.2284–0.2367 | 0.2341–0.2411 |
| Refined selector | 0.1926–0.2069 | 0.1210–0.1334 | 0.0941–0.1210 | 0.0970–0.1306 |

## Daily personalization

| Procedure | Pooled AP | Balanced AP ↑ | Pooled ROC-AUC | Within-person ROC-AUC | Within-day ROC-AUC | Balanced Brier ↓ | Balanced log loss ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Global model | 0.1456 | 0.1462 | 0.5236 | 0.6430 | 0.6340 | 0.1159 | 0.3952 |
| Personal base rate | 0.5614 | 0.5538 | 0.8365 | 0.4097 | 0.5000 | 0.0836 | 0.2867 |
| Daily personal offset | 0.5776 | 0.5714 | 0.8472 | 0.5624 | 0.6340 | 0.0820 | 0.2805 |

The personal base rate ranks well across people and assigns a constant score to each person's check-ins on a given day. The offset changes the probability level for that person-day while keeping the global within-day order, including ties, on all 423 observed days. Both the global and offset procedures have within-day AUC **0.6340**. Across all evaluation days for the same person, the offset's mean AUC falls from **0.6430 to 0.5624** relative to the global scores. The prespecified gain is in probability accuracy versus the personal base rate. As a descriptive check, the offset lowered mean Brier loss for **20 of 37 participants** and raised it for **17**. Within-person ranking uses **29 of 37 people**, and within-day ranking uses **150 of 423 participant-days** from those 29 people. Every matched row contributes to pooled probability and decision metrics, including single-class groups. [Aggregate evaluation](results/hw5-v1-step5-20261117_evaluation.json) · [Daily ranking and reliability](../figures/step6_daily_personalization.png)

## Decisions at the saved cutoffs

The fitted cutoffs targeted 25% of inner validation rows. Actual alert shares vary with the evaluation scores, including when the same global cutoff is applied to all daily variants. The fixed rule applies directly to the new-user rows. [Aggregate metrics CSV](results/hw5-v1-step5-20261117_metrics.csv)

| Regime and procedure | TP | FP | FN | TN | Precision | Recall | Alert share |
|---|---:|---:|---:|---:|---:|---:|---:|
| New users, fixed baseline | 261 | 1,185 | 457 | 3,724 | 18.05% | 36.35% | 25.70% |
| New users, refined | 176 | 763 | 542 | 4,146 | 18.74% | 24.51% | 16.69% |
| New users, fixed rule | 300 | 1,075 | 418 | 3,834 | 21.82% | 41.78% | 24.44% |
| Daily, global model | 108 | 531 | 376 | 2,757 | 16.90% | 22.31% | 16.94% |
| Daily, personal base rate | 356 | 727 | 128 | 2,561 | 32.87% | 73.55% | 28.71% |
| Daily, personal offset | 355 | 701 | 129 | 2,587 | 33.62% | 73.35% | 28.00% |

The refined new-user procedure produced fewer alerts and substantially lower recall than the fixed baseline. At its own operating point of 24.44% alerts, the fixed rule had higher precision and recall than either learned procedure at its saved cutoff. In the daily comparison, the offset reduced false positives by 26 and caught one fewer positive than the base rate. [Aggregate evaluation](results/hw5-v1-step5-20261117_evaluation.json)

## Reproduction and handoff

The verification script checks the protocol and artifact hashes, prediction row matches, saved cutoff decisions, allowed history and both paired intervals from the existing private prediction files. The export script reads the verified aggregate results to produce the CSV and figures. The precision–recall figure uses the fixed score grid and marks the saved operating points. AP in the tables uses all stored scores. [Verifier](verify_step6.py) · [Exporter](export_step6.py) · [Verification evidence](results/hw5-v1-step5-20261117_verification.json)

From the repository root, using the pinned Python environment and the existing local run:

```powershell
python deliverables/05_model_refinement_test_submission/build/verify_step6.py --csv ../Capstone_Digital_Addiction/data/raw/awaremind/full_data_all_feature.csv --run-id hw5-v1-step5-20261117
python deliverables/05_model_refinement_test_submission/build/export_step6.py --run-id hw5-v1-step5-20261117
```

The independent reviewer reconciled all 49 exported metric rows, verified the leakage boundaries and recorded the code discrepancies that apply to future runs. [Independent evidence review](independent_review.md)
