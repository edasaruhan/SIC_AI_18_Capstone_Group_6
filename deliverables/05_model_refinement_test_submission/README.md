# Homework 5 Model Refinement and Test Submission

**NudgeWell · Group 6 · Samsung Innovation Campus**  
**Completed report · 21 November 2026**

The seven-page report follows the instructor's original template. It contains the matched held-out results, three figures, and three commented code excerpts. [PDF report](NudgeWell_HW5_Model_Refinement_and_Test_Submission.pdf) · [Word report](NudgeWell_HW5_Model_Refinement_and_Test_Submission.docx)

The refined procedure showed no clear gain in new-user ranking. The daily offset modestly improved probability accuracy relative to the personal base rate and preserved the global model's within-day ranking. The work is a retrospective coursework evaluation. [Aggregate results](build/results/) · [Independent review](build/independent_review.md)

## Reproduce the package

Use a Git checkout so runs can record the source commit. From the repository root, install the [pinned Python 3.11 dependencies](requirements.txt). Run the synthetic gate with `python -m unittest discover -s deliverables/05_model_refinement_test_submission/tests -v`. The [experiment guide](code/EXPERIMENTS.md) documents selection and evaluation with a local copy of the dataset.

The bundled figures and metrics can be rebuilt from the verified aggregates. Rebuilding the Word report also requires the original instructor template. On Windows, Microsoft Word exports the final PDF.

```powershell
python deliverables/05_model_refinement_test_submission/build/export_step6.py --run-id hw5-v1-step5-20261117
python deliverables/05_model_refinement_test_submission/build/build_hw5_report.py --template 'path/to/Model Refinement_Template.docx'
& deliverables/05_model_refinement_test_submission/build/render_docx.ps1
```

Raw data, participant manifests, row-level predictions and fitted models stay local. The project uses the released data for coursework analysis. Written permission is required before publishing or deploying a fitted model. [Data handling](../../data/README.md)

## Continuation checkpoint — 16 November 2026

**Step 2 is complete:** read [the baseline review](build/baseline_review.md), its [aggregate verification evidence](build/baseline_evidence.json), and the [reproducible count/split checker](build/verify_baseline.py). Historical model metrics were reconciled to the saved JSON and source; no models were trained. A bounded check of the local CSV confirms the old split crosses a midnight local day for 36 people and a 04:00-adjusted local day for 34, resolving the earlier ambiguous “34 local days” wording. The calibration dependency and evaluation-quantile cutoff require repair; feature provenance remains unresolved.

The Mac's ignored template/audit files were not included in the Git sync; the review states what could be verified locally and what remains unavailable. The original Step 1 requirement mapping and Step 2 task brief below are retained as source context.

## Frozen protocol checkpoint — 17 November 2026

**Step 3 is complete:** [protocol.json](build/protocol.json) is frozen as v1.0.0, with a [plain-language explanation](build/protocol_notes.md), [SHA-256 seal](build/protocol.sha256), and [75 passing specification/data preflight checks](build/protocol_preflight.json). No HW5 models were fitted. The frozen design has 15 main inputs, a five-input comparison pack, five outer participant folds, three inner folds, bounded LR/RF selection, training-only calibration/cutoffs, and a matched daily personalization comparison after seven warmup days. Evaluation days use each participant's first-observed timezone; predictor clocks use each row's timezone. One participant's timezone changes are retained under that explicit rule.

The Step 3 preflight checks the contract and data consistency; it is retained as a historical snapshot. Additions to the protocol after the freeze need a separate version and result lineage. Private manifests, row predictions and fitted models belong only in the ignored HW5 `run/` folder.

## Data/split implementation checkpoint — 17 November 2026

**Step 4 is complete:** [the implementation guide](code/README.md) describes the data/split contract, scoped fitting and calibration-provenance interfaces under `code/nudgewell_hw5/`. [35 synthetic boundary tests](tests/test_contract.py) pass, including the indirect calibration dependency, future-label mutations, strict lock cutoffs, session boundaries, training-only preprocessing, fixed cutoffs, timezone/DST and degenerate histories. [Aggregate verification evidence](build/step4_validation.json) reconciles 5,627 unique rows into 1,855 warmup and 3,772 day-forward evaluation rows across 37 people/423 days. All 5 outer, 15 inner and 45 calibration splits are constructed. Private memberships are ignored. No models were fitted on the released data, and the frozen protocol/seal remain unchanged.

The Step 4 evidence is retained as a dated snapshot; the subsequent integration gate below covers the current implementation.

## Bounded selection checkpoint — 17 November 2026

**Step 5 is complete:** [the selector/runner guide](code/EXPERIMENTS.md) documents the exact candidate factory, scoped cache, nested calibration, immutable cutoffs, private checkpoints and separate selection/evaluation commands. [51 unit/integration tests passed](build/step5_validation.json) before real-data fitting. The validation-side run `hw5-v1-step5-20261117` completed **160 candidate evaluations and 540 successful base-fit jobs**, with no failed jobs. [Aggregate traces](build/results/hw5-v1-step5-20261117_selection.json) preserve all candidates and stage diagnostics; [the run review](build/step5_run_review.json) verifies source/artifact hashes and that outer evaluation is unopened. Fitted models and row scores remain in the ignored run directory.

## Frozen evaluation checkpoint · 21 November 2026

**Step 6 is complete.** All 51 tests passed before the five saved procedures were applied. The new-user evaluation covers 5,627 check-ins across 37 held-out participants. The matched daily evaluation covers 3,772 check-ins across 423 participant-days. The new-user balanced AP difference was −0.0169 (paired 95% interval −0.0652 to +0.0222). The daily offset lowered balanced Brier loss by 0.00159 versus the personal base rate (paired 95% interval 0.00048 to 0.00275). Row coverage, history, saved cutoffs, metrics and both paired intervals were verified from the private prediction files. [Evaluation review and figures](build/evaluation_review.md) · [Aggregate metrics CSV](build/results/hw5-v1-step5-20261117_metrics.csv) · [Verification evidence](build/results/hw5-v1-step5-20261117_verification.json)

## Independent review checkpoint · 21 November 2026

**Step 7 is complete.** An independent reviewer traced participant isolation, nested calibration, saved cutoffs and the daily history boundary. It reproduced the paired intervals and reconciled the aggregate tables. The review found no material leakage or numerical error in the completed v1 run. The lead added the matched day manifest inside the ignored run directory and clarified that the daily probability gain is an average against the personal base rate. The review records four code discrepancies that did not affect this run. [Independent evidence review and dispositions](build/independent_review.md)

## Requirement categories

| Label | Meaning |
|---|---|
| **Assignment** | An explicit template prompt. Answer it with actual work or an accurate explanation of what was done. |
| **Conditional** | The template says **“If applicable”** for Feature Selection and Model Deployment, and **“if applicable”** for snippets within Model Application. Retain the heading and explain applicability. Code Implementation separately requires commented snippets for both phases. |
| **Concept commitment** | A broader promise in Homework 3. Explain changes in scope; do not silently turn every promise into a Homework 5 requirement or claim it was delivered. |
| **Method recommendation** | A project-specific way to produce defensible evidence, drawn from the existing plan/audit. Exact folds, models, search budgets and metrics are not prescribed by the instructor. Freeze these choices in the protocol before new experiments. |

“May include” in Refinement Techniques gives examples, not a requirement to try every algorithm or ensemble. “Any additional” tuning and “any changes” to cross-validation ask for an account of actual work; they do not prescribe a search method or require a change for its own sake. The template specifies no separate competition upload, external test dataset, minimum score, page count or PDF requirement. Any additional course rules would need separate evidence.

## Evidence register

Paths in this document are relative to the repository root unless stated otherwise. Links resolve from this README. Source identifiers below point to the files used for each checklist item.

| ID | Existing source | Relevant content |
|---|---|---|
| T | [`.local/model-refinement/Model_Refinement_Template.docx`](../../.local/model-refinement/Model_Refinement_Template.docx) | Assignment authority: six Model Refinement sections, six Test Submission sections, Conclusion and References. Text checked against the retained two-page preview. Local and ignored by Git. |
| P | [`deliverables/05_model_refinement_test_submission/PLAN.md`](PLAN.md) | Existing project audit, workflow, proposed protocol and bounded experiment matrix. Proposals are not results. |
| A | [`.local/model-refinement/data-audit.json`](../../.local/model-refinement/data-audit.json) | Existing timing, boundary, missingness and class-coverage audit. Local and ignored; cite aggregate findings in the report rather than relying on reviewers having this file. |
| R | [`README.md`](../../README.md) | Project purpose, submission history and current coursework data-use policy. |
| H | [`deliverables/04_data_preparation_model_exploration/README.md`](../04_data_preparation_model_exploration/README.md) | Historical evaluation regimes, report inventory and reproduction instructions. |
| C | [`deliverables/04_data_preparation_model_exploration/code/hw4_pipeline.py`](../04_data_preparation_model_exploration/code/hw4_pipeline.py) | Actual cleaning, 49 inputs, fixed classifiers, splits, metrics, personalization and inference. Source locations below refer to this version. |
| J | [`deliverables/04_data_preparation_model_exploration/build/results/results_real.json`](../04_data_preparation_model_exploration/build/results/results_real.json) | Saved real-data historical aggregates. `pr_auc` is computed with `average_precision_score`, so describe it as average precision (AP), not trapezoidal PR area. |
| N | [`deliverables/03_concept_note_implementation_plan/build/concept_note.md`](../03_concept_note_implementation_plan/build/concept_note.md) | Objectives O1–O6, methodology §§4.1–4.6, milestones and earlier commitments. |
| D | [`data/README.md`](../../data/README.md) | Target, data provenance, exclusions, privacy and current data-use policy. |
| F4 | [`deliverables/04_data_preparation_model_exploration/figures/fig4_roc_pr_new_users.png`](../04_data_preparation_model_exploration/figures/fig4_roc_pr_new_users.png) | Historical LOPO ROC/PR curves. |
| F5 | [`deliverables/04_data_preparation_model_exploration/figures/fig5_known_users_same_rows.png`](../04_data_preparation_model_exploration/figures/fig5_known_users_same_rows.png) | Historical known-user pooled versus within-person performance. |
| F6 | [`deliverables/04_data_preparation_model_exploration/figures/fig6_same_alert_rate.png`](../04_data_preparation_model_exploration/figures/fig6_same_alert_rate.png) | Historical evaluation-quantile alert comparison; not a validated operational cutoff. |
| F7 | [`deliverables/04_data_preparation_model_exploration/figures/fig7_permutation_importance.png`](../04_data_preparation_model_exploration/figures/fig7_permutation_importance.png) | Historical permutation importance; not a completed feature-selection experiment. |

### Verified starting point and limits on reuse

| Existing finding | Evidence checked | Consequence for this homework |
|---|---|---|
| 5,772 released rows minus 145 exact duplicates = **5,627 unique rows**, **718 positives**, **37 participants**, prevalence **12.76%** | C `load` (lines 94–101); J `data.rows_*`, `duplicate_rows`, `participants`, `high_gap_n`, `high_gap_rate`; A agrees | Reuse as historical counts and reconcile them in the new pipeline. Earlier 14.9% describes the duplicated release. |
| Fixed night/social/session-over-10-min rule: **21.82% precision**, **41.78% recall**, **24.44% flagged** | C `describe` and rule construction (438–448, 557–564, 600–604); J `data.rules["Any of the first three"]`, `at_alert_rate["Fixed rule"]` | Reuse as the cleaned historical rule benchmark. Evaluate the same fixed rule again on the new eligible rows. |
| Historical new-user ROC-AUC: LR **0.6160**, RF **0.5984**, XGB **0.5743**, LGBM **0.5574** | C `make_models`, `lopo`; J `global` | Weak generalization motivates refinement. These are fixed-setting LOPO results, not nested tuned-model estimates. |
| Personal RF pooled ROC-AUC **0.8429**, own base rate **0.8271**, personal RF within-person mean ROC-AUC **0.5872** | J `personal.approaches`; C `personal_regime`, `per_person` | A high pooled score can reflect differences between people. The old personal test has 1,705 rows, but within-person AUC covers only 25 people with both classes. |
| Old population calibration uses `fit_offset(global_oof[others], y[others])` | C `lopo` (253–260), `personal_regime` (315–320) | For participant g, a peer's OOF model omitted that peer but could train on g, including g's later labels. The calibrator therefore indirectly depends on g. Generate calibration scores wholly inside g's permitted training universe before claiming isolated performance. |
| Old learned alert cutoff is `np.quantile(s, 1 - alert)` over evaluation scores | C 609–624; J `at_alert_rate`; F6 | This uses the evaluation score distribution, even without its labels. Retain as a descriptive ranking comparison only. Select a deployable threshold from validation and report actual evaluation alert share. |
| Old 70/30 split cuts a local day for 34 people; one session crosses the boundary; one training outcome is unresolved at first testing | A named boundary fields; C `chrono_split` (263–272) sorts by `esm_time` and cuts rows without day/session/outcome-availability checks | Reuse the audit finding; add executable boundary tests. Do not call the old split day-forward evaluation. These counts were not independently recomputed in Step 1. |
| App session-duration aggregate exceeds elapsed session time in **97 rows across 3 people** | J `data.app_duration_exceeds_elapsed`; C 546–555; P audit | Investigate units, windows and pre-prompt availability. An anomaly is not proof of leakage. Exclude unresolved features from the main analysis until justified. |
| There are 49 main features and no hyperparameter search in the historical runner | C feature lists/build (42–126), `make_models` (139–179), `main`; J `n_features`, `features` | Reuse transformations and settings as starting evidence. The name-based leakage assertion does not prove that every derived input was available before prediction. |

The old five-fold grouped demographics comparison (`J.groupkfold5`; C 631–645) is a fixed-model sensitivity analysis, not nested selection. Old importance estimates (C 663–683; J `permutation_importance_*`) cannot establish the performance of a selected subset. Existing synthetic-check summaries are historical too; H states that their generator is absent from the repository. They do not replace new boundary tests.

## Model Refinement checklist

### MR1 Overview

- **Instructor asks — Assignment:** Briefly explain the refinement phase and its role in improving model performance (T, Model Refinement §1).
- **NudgeWell should explain:** The binary high-gap target, weak new-user performance, the difference between identifying people and ranking their moments, and the specific weaknesses refinement will address.
- **Reuse:** R project description; H main results; J `global` and `personal`; N Objectives and §4.1.
- **New work needed:** A short rationale tied to the frozen protocol. **Method recommendation:** compare fixed and tuned LR/RF, calibration and a simple personal offset; keep candidate lists bounded. These experiments are pending.
- **Support:** One compact table: weakness → proposed change → metric/evaluation that can test it.
- [ ] **Complete when:** The research question, target, chosen changes and scope are stated without promising an improvement or treating a planned model as completed.

### MR2 Model Evaluation

- **Instructor asks — Assignment:** Summarize initial results, identify improvement areas, and reference exploration metrics and visualizations (T §2).
- **NudgeWell should explain:** Historical LOPO results and known-user results separately; pooled versus within-person discrimination; class imbalance; calibration, timing and threshold limitations.
- **Reuse:** C `pooled`, `summarise`, `lopo`, `personal_regime`; J `global`, `personal`, `data.rules`; F4–F6. Use the verified starting-point table above and P's audit instead of restarting exploration.
- **New work needed:** Produce `deliverables/05_model_refinement_test_submission/build/baseline_review.md` from the existing evidence. Later, rerun fixed baselines under the corrected protocol so changes in evaluation are separated from changes in the model.
- **Support:** Historical comparison table with AP, ROC-AUC, Brier, within-person AUC and coverage; F4/F5 with historical captions. Add a separate corrected-baseline table later.
- [ ] **Complete when:** Every starting number traces to J, weaknesses trace to code/audit evidence, and old versus corrected results have distinct labels and denominators.

### MR3 Refinement Techniques

- **Instructor asks — Assignment:** Describe techniques actually used; hyperparameter adjustment, different algorithms and ensembles are examples (T §3).
- **NudgeWell should explain:** Why each implemented change addresses an observed weakness and whether its measured effect supports retaining it. Evaluation repairs establish a valid comparison; they are not themselves evidence of predictive improvement.
- **Reuse:** C `make_models` and `fit_offset`; J historical comparisons; P Steps 3–5.
- **New work needed:** Implement and evaluate the predeclared comparison matrix after protocol agreement. **Method recommendation:** fixed versus tuned LR/RF, identity versus training-only sigmoid calibration, and global score versus personal base rate/regularized offset on matched rows. Boosting is an optional extension; no extra ensemble is mandated.
- **Support:** Experiment table with configuration ID, rationale, eligible rows, validation result and final held-out result; retain failed or negative comparisons.
- [ ] **Complete when:** Every claimed refinement has executed code, a saved configuration and comparable evidence; no pending variant appears as an outcome.

### MR4 Hyperparameter Tuning

- **Instructor asks — Assignment:** Detail any additional tuning, insights gained and performance impact (T §4).
- **NudgeWell should explain:** Homework 4 used fixed settings. State the new search space, search procedure, metric, constraints, selection rule and selected settings, or accurately state that no additional tuning was done.
- **Reuse:** C `make_models`: LR `C=1`, balanced weights; RF 100 trees, depth 6, minimum split 10; fixed XGB/LGBM settings. P Step 5 proposes bounded searches.
- **New work needed:** **Method recommendation for the chosen scope:** four LR C values × two weight settings and eight predefined RF configurations. Freeze actual values/seeds before running. Keep preprocessing, family/feature choice and calibration selection inside permitted validation. Save per-fold choices and traces.
- **Support:** Search-space and selected-configuration table plus validation score/rank table; commented search excerpt.
- [ ] **Complete when:** Another person can reconstruct the candidate list and selection, validation drove choices, and the measured impact is reported even if tuning does not help. A search is recommended here, not an instructor-specified grid size.

### MR5 Cross-Validation

- **Instructor asks — Assignment:** Describe changes to cross-validation and explain their rationale (T §5).
- **NudgeWell should explain:** Old fixed-model LOPO and per-person chronological 70/30; why tuning needs an inner selection layer; why known-user history needs resolved labels and day/session boundaries.
- **Reuse:** C `lopo`, `chrono_split`, `personal_regime`; A boundary/coverage audit; H evaluation summary; P Steps 3–4.
- **New work needed:** **Method recommendation:** specify five outer participant-grouped folds and three inner grouped folds for new-user selection, or explicitly choose nested LOPO before experiments. For the planned known-user comparison, use seven calendar days of warmup followed by daily evaluation with `lock_time < prediction_cutoff`, participant-isolated peer fitting/calibration, and session/unresolved-outcome purging. Record timezone/day rules, fallback behavior and coverage. All adaptive choices remain within training data.
- **Support:** Split diagram, aggregate fold/day counts, and tests for participant isolation and future-label invariance. Private membership manifests stay local.
- [ ] **Complete when:** The written protocol and executable splits agree; tests establish the boundaries; reasons for changes are explicit. Describe this as retrospective internal validation because the dataset was already explored.

### MR6 Feature Selection

- **Instructor asks — Conditional:** If applicable, describe selection methods and their performance effects (T §6).
- **NudgeWell should explain:** Separate outcome/identifier exclusions, feature-availability decisions, importance analysis and predictive subset selection. Importance alone is not evidence that removal improves performance.
- **Reuse:** C `OUTCOME`, `IDENTIFIERS`, `DEMOGRAPHICS`, `FEATURES`, `build_features`; J `features`, `permutation_importance_by_group`, `app_duration_exceeds_elapsed`; F7; D exclusions.
- **New work needed:** Audit the timing/provenance of session, daily app-use and interaction aggregates. **Method recommendation:** compare the audited input set with the same set minus tap/text/scroll fields inside validation. Historical negative interaction-group importance motivates this hypothesis but does not validate it. If no predictive subset selection is performed, say so and explain safety exclusions without inventing an ablation effect.
- **Support:** Feature-block inclusion/exclusion table with availability rationale; subset-performance table only if an experiment actually runs.
- [ ] **Complete when:** Every main input is justified or excluded as unresolved, any subset choice uses training validation, and claimed effects have measured evidence; otherwise the conditional section accurately records no additional selection.

## Test Submission checklist

### TS1 Overview

- **Instructor asks — Assignment:** Outline preparation for deployment **or** evaluation on a test dataset (T, Test Submission §1).
- **NudgeWell should explain:** How the frozen procedure is applied to held-out participants/days, what is fitted beforehand and what evidence is collected. A new external dataset is not necessary to explain internal evaluation.
- **Reuse:** P Step 6; H two historical regimes; C `main` and prediction output; D data scope.
- **New work needed:** Define the evaluation contract and freeze the selection procedure before inspecting new outer results. If a separate instructor test file is later supplied, specify its interface and preserve it until final application.
- **Support:** Flow diagram: training → inner validation/selection → refit → held-out application → aggregate evaluation; run metadata table.
- [ ] **Complete when:** The report identifies exactly what “test” means, when choices were frozen and how held-out evidence was produced, without implying an untouched external test or competition upload.

### TS2 Data Preparation for Testing

- **Instructor asks — Assignment:** Explain preparation of the test dataset and special considerations (T §2).
- **NudgeWell should explain:** Exact duplicate removal, target construction, eligible rows, missingness, input availability, group/time boundaries and applying training-fitted transformations to evaluation rows.
- **Reuse:** C `load`, `build_features`, `make_models`; J `data`, `features`; A timing audit; D handling policy. Historical missingness includes 703 app categories, 700 app-duration entries and 127 activity entries.
- **New work needed:** Implement a Homework 5 data contract and corrected splits; reconcile released, unique, training, purged and evaluation counts. Preserve missingness indicators; fit medians/scalers on training only. Test outcome/ID/demographic exclusion, missing fields, one-class histories and session boundaries. Add the Homework 5 private run directory to `.gitignore` before producing private outputs.
- **Support:** Count/missingness reconciliation table, feature-schema table and concise cleaning/preprocessing excerpt.
- [ ] **Complete when:** Counts reconcile, transformations have no evaluation fit, exclusions have reasons, models being compared receive identical eligible rows, and no private data appear in shared artifacts.

### TS3 Model Application

- **Instructor asks — Assignment, with conditional snippets:** Describe applying the trained model to test data; include snippets if applicable (T §3).
- **NudgeWell should explain:** The fitted feature order, imputer/scaler, classifier, calibrator and validation-selected threshold in application order; known-user fallback and update timing where used.
- **Reuse:** C `lopo` fit/predict pattern, `make_models` pipelines, `personal_regime` prediction paths and `main` output. These illustrate historical application, not a corrected Homework 5 run.
- **New work needed:** One inference path used by the new runner, with no test-time fitting of transformations, calibration or thresholds. Save row-level predictions and fitted artifacts privately and aggregate metadata publicly. Test that evaluation labels or score distributions cannot change a fitted cutoff.
- **Support:** Commented excerpt from actual Homework 5 inference, plus an aggregate output schema/example without participant records. Share this excerpt with TS6.
- [ ] **Complete when:** The executed path matches the described order, prediction provenance is saved, and changing future/evaluation labels cannot change earlier predictions or fitted decisions.

### TS4 Test Metrics

- **Instructor asks — Assignment:** Present test metrics and compare them with training and validation metrics (T §4).
- **NudgeWell should explain:** Generalization, ranking, probability quality and decisions as distinct properties; distinguish resubstitution training diagnostics, inner-validation selection scores and outer held-out estimates. Never compare historical LOPO and new nested results as a clean tuning effect.
- **Reuse:** C `pooled`, `per_person`, `boot`, `summarise`; J `global`, `personal`, `at_alert_rate`; F4–F6 as historical context only. The existing JSON does not supply the new training/inner-validation/test comparison.
- **New work needed:** **Method recommendation:** participant-balanced AP as the primary selection score (each participant total weight one); pooled AP and ROC-AUC; within-person AUC with eligible-person counts; Brier/log loss and reliability; precision, recall, confusion counts and actual alert share at validation-fixed cutoffs. Save training and validation diagnostics too. Use participant-level paired uncertainty for the main baseline/refinement comparison. Include single-class users in probability/decision metrics even when AUC is undefined; define no-positive/zero-alert behavior.
- **Support:** Stage-by-stage metric table on clearly identified populations; matched corrected-baseline/refinement table; PR and reliability plots; confusion table and paired difference interval. A binary fixed rule is a decision benchmark, not a calibrated probability forecast.
- [ ] **Complete when:** All reported metrics trace to saved predictions/aggregates, stages and denominators are explicit, comparisons use matching rows, and uncertainty/undefined cases are reported without manufacturing a gain.

### TS5 Model Deployment

- **Instructor asks — Conditional:** If applicable, describe real-world deployment/integration steps (T §5).
- **NudgeWell should explain:** The inspected implementation is offline Python modelling/evaluation. The concept note's Android/Eşik architecture is planned integration, not proof of a deployed NudgeWell model.
- **Reuse:** C imports, `main` and outputs; R project description; N §4.6, Architecture, O5/O6 and M4; D current data-use policy.
- **New work needed:** A concise applicability/status statement and remaining integration work. Export, device latency/size tests, Android wiring and real intervention testing are broader work unless deliberately added later. Do not claim permission was obtained or deployment occurred without evidence.
- **Support:** Status table: offline pipeline demonstrated / export, device inference and field efficacy not evidenced here. No device screenshot or fabricated integration code is needed.
- [ ] **Complete when:** Actual status and future work are separated, the conditional heading is answered, and no unsupported deployment, privacy-performance or intervention-effectiveness claim remains.

### TS6 Code Implementation

- **Instructor asks — Assignment:** Include relevant commented snippets for both refinement and test submission (T §6).
- **NudgeWell should explain:** How selection and evaluation are implemented, focusing on boundaries that make the results credible.
- **Reuse:** C `build_features`, `make_models`, `lopo`, `fit_offset` as starting patterns, with the documented repairs. H gives commands and dependency context, not proof the new workflow has run.
- **New work needed:** Actual Homework 5 modules, a reproducible command, configuration/seed/environment record and risk-focused tests. P proposes `code/data_contract.py`, `code/splits.py`, `code/models.py`, `code/evaluate.py` and `code/run_refinement.py`; these do not yet exist at Step 1.
- **Support:** Two or three short commented excerpts covering training-only refinement/selection and frozen inference/metric application; cite real file/function locations and test output. Reuse TS3's inference excerpt rather than filling the report with duplicate code.
- [ ] **Complete when:** Both phases have readable executed-source excerpts, commands/configuration reproduce the evidence, tests pass, and snippets agree with the actual runner.

## Closing template sections

### Conclusion

- **Instructor asks — Assignment:** Summarize outcomes, challenges and final performance (T, Conclusion).
- **NudgeWell should explain:** Which refinements helped, failed or remain uncertain; limits from sample size, class coverage, provenance, retrospective evaluation and transfer beyond this dataset. Separate predictive performance from intervention benefit.
- **Reuse:** J/H for the historical starting point; A/P for known challenges; N's statement that intervention effects require a separate user study.
- **New work needed:** Write only after corrected experiments and evidence review. Reconcile every conclusion with its metric/table; explain changes from earlier commitments. No final-performance conclusion can be drafted now.
- **Support:** A compact findings/limitations table referring to reviewed TS4 results, including negative findings and coverage.
- [ ] **Complete when:** Every outcome has executed evidence, uncertain differences remain uncertain, and no claim implies paper-benchmark superiority or real-world effectiveness without a matching study.

### References

- **Instructor asks — Assignment:** List external resources, libraries and papers actually referenced (T, References).
- **NudgeWell should explain:** Dataset/paper provenance and the methods/software actually used in this homework.
- **Reuse:** N References; R main source; D data source; C imports; [`deliverables/04_data_preparation_model_exploration/requirements.txt`](../04_data_preparation_model_exploration/requirements.txt); P's nested-validation, calibration and metric documentation links.
- **New work needed:** Verify primary references and installed library versions during implementation/reporting. Include sources for implemented selection/calibration methods. Do not copy unrelated neural-network or Android references solely to suggest completion. This requirements step did not independently re-verify external publications.
- **Support:** Consistent bibliography with in-text citations; small software/version table if useful. APA 7 is the project's existing convention, not a style rule stated in this template.
- [ ] **Complete when:** Each cited method/resource has a correct reference, library versions reflect the executed environment, and references support the work actually described.

## Reconcile the concept note with current implementation

These are **concept commitments**, not extra template requirements. Preserve the earlier submissions and explain the discrepancy in the new report.

| Earlier commitment in N | Actual evidence now | Treatment in Homework 5 |
|---|---|---|
| O1/§4.1: reproduce the paper's continuous-gap RF benchmark and 14.9% prevalence | C/J model only the binary target; cleaned prevalence is 12.76%. Paper MAE/R² and classifier AUC/AP measure different tasks. | Explain target and deduplication changes. Do not claim regression reproduction or superiority from binary metrics. Regression reproduction remains broader work. |
| O2/§4.3: TCN and GRU, dual outputs and sequence history | C implements LR/RF/XGB/LGBM classifiers; no TCN/GRU is implemented in this pipeline. | Neural models are deferred project work. No automatic neural-model requirement for this homework. |
| §4.2/O3: seven-day warmup, daily updating and 5/10/20/40/80-check-in adaptation curves | C uses a static chronological 70/30 split, a personal offset, personal trees and a combined RF with weight 5; the concept note proposed daily combined fitting with weight 10. | State the old departures. A corrected small day-forward comparison is recommended in P; extensive adaptation curves and the full combined-model programme remain optional. |
| O4/§4.5: calibrated validation-fixed decisions, three prompts/day and 30-minute cooldown | C has an offset method, but its population calibration path needs isolation repair; alert quantiles use evaluation scores. No budget/cooldown replay is implemented there. | Training-only calibration and threshold evidence are useful refinements. Full prompt-policy replay/sensitivity analysis is optional and, if added, is offline replay of sampled check-ins, not intervention-effect evidence. |
| O5/§4.6/M4: SHAP explanations, ONNX/LiteRT, Android/Eşik integration, <1 MB and <50 ms | C/J show offline predictions and aggregates, not these integration or device measurements. The concept architecture and Eşik description do not establish NudgeWell deployment. | Answer conditional deployment with the actual status. Export, Android and device targets stay broader commitments. |
| O6: written permission before training; fairness/privacy deliverables | R/D now describe coursework modelling use and permission before publishing/deploying a model. This differs from the earlier pre-training commitment; reviewed files do not establish author permission. Age/gender sensitivity/EDA is not the promised full fairness evaluation. | Acknowledge the policy change without inventing approval. Keep private data and fitted artifacts local. Demographic subgroup evaluation and a prototype ethics checklist are broader work unless chosen; no added permission request is needed for this read-only requirements step. |

## 1 Minimum complete scope for this homework

The **assignment floor** is an honest, evidenced account of actual refinement, initial evaluation, any tuning/CV changes, test preparation/application, training-versus-validation-versus-test metrics, commented code for both phases, conclusions and references. Answer conditional feature selection/deployment accurately. The instructor does not require a particular model family, successful improvement, external dataset or deployed app.

The **recommended bounded NudgeWell scope** from P is corrected participant-aware binary evaluation; fixed LR/RF plus simple prevalence/rule references; a small LR/RF search; training-only calibration and validation-fixed decisions; and a matched, simple known-user base-rate/global/offset comparison with resolved history. Audit inputs and run at most one predefined feature-block comparison if selected. Freeze exact choices in the protocol before experiments. Boosting, TCN/GRU, regression reproduction, extensive personalization curves, prompt-policy simulation and Android integration are extensions, not automatic completion gates.

Finish by filling the retained template from reviewed evidence and visually checking the final DOCX. An additional PDF is needed only if course submission rules require it. Completing this checklist is not equivalent to completing the experiments or final report.

## 2 Evidence we already have

- The complete template and section mapping (T), existing workflow/audit (P/A), project purpose and current data policy (R/D).
- Historical executable cleaning, feature construction, fixed tabular models, participant LOPO and chronological evaluation, metrics and offset implementation (C).
- Saved historical real-data aggregates, counts, baselines and uncertainty summaries (J), with existing figures F4–F7 and the interpretation in H.
- Earlier objectives and scope commitments (N), which explain the current departures rather than prove they were implemented.

## 3 Evidence we still need

- A concise source-linked baseline review/action list; a frozen protocol specifying features, boundaries, selection, calibration, thresholds, coverage and metric definitions.
- Homework 5 data/split/model/inference code, privacy-safe output paths and executable isolation/timing/preprocessing/threshold tests. Resolve feature availability or conservatively exclude unresolved columns.
- Corrected baseline runs and predefined refinement experiments with configurations, validation traces, training diagnostics and private predictions; no such new results exist at Step 1.
- Frozen-procedure held-out results, matching-row comparison tables, uncertainty, calibration/decision plots and review findings with dispositions.
- Evidence-based conclusions, checked references and the completed, visually verified template. No deployment evidence is needed if deployment is inapplicable.

## 4 Historical handoff

The Step 9 walkthrough is complete.

The baseline review reconciled Homework 4's code and saved aggregates. It records the indirect calibration dependency, the evaluation-derived cutoff and the unresolved labels at the chronological split. These findings informed the frozen participant splits, calibration boundaries and daily history rules. [Baseline review](build/baseline_review.md)

The original Step 2 handoff is complete. Its baseline review informed the frozen protocol and the completed evaluations. [Evaluation review](build/evaluation_review.md)
