# NudgeWell homework workflow with AI agents

Complete the supplied **Model Refinement and Test Submission** template using real experiments, reproducible code and a clear explanation of what changed from Homework 4. The submission is due **12 November 2026**. This plan follows the work step by step; the deadline does not define the steps.

The main workflow is:

**Understand the assignment → establish the starting point → agree on evaluation → implement and test → compare refinements → evaluate the frozen procedure → review the evidence → write the report → verify the submission.**

The project audit and template review are already complete. Reuse that work rather than asking every agent to rediscover the project. Model-refinement implementation and new experiments remain to be done.

## How we work together

Use this chat as the **lead agent**. It keeps the shared decisions, integrates code, coordinates other agents, runs the final experiment and checks that the report matches the evidence. You provide course-specific information, resolve substantive scope questions and review the final explanation. Routine coding, debugging, plotting and document formatting can proceed without repeated approval requests.

Use specialist agents for bounded tasks:

| Role | Responsibility | Handoff |
|---|---|---|
| Lead agent | Requirements, shared protocol, integration and final consistency | One authoritative protocol, experiment runner and report |
| Data and evaluation agent | Feature availability, splitting, label timing and leakage tests | Data audit, split code, tests and review findings |
| Modelling agent | Fixed baselines, bounded tuning and refinement comparisons | Model code, configuration lists, validation traces and interpretation |
| Review and document agent | Independent evidence review, then template filling and layout checks | Findings tied to files, completed DOCX and verified figures |

These are responsibilities, not a requirement to create four separate chats. An agent can be reused for later tasks. With four execution slots, keep the lead plus at most three specialists active. A reviewer should not be the only person checking their own modelling implementation.

All implementation belongs under `deliverables/05_model_refinement_test_submission/`. Preserve Homework 1–4. Give agents different files to edit, establish shared interfaces first, and use one authoritative job to write experiment results. Parallelize preparation and review; avoid running duplicate large training jobs or editing the same report simultaneously.

## Shared context for every agent

Attach this context to each task, then add the specific prompt from the relevant step:

> Work on the NudgeWell Samsung Innovation Campus homework in `/Users/thynatos/Documents/IC`. Read this plan, the relevant existing code, and `data/README.md`. Use the existing Python 3.11 `.venv`. The target is `answer <= 5 and remaining_minutes > 5`. Remove exact duplicates: the current file has 5,627 unique rows, 718 positives and 37 participants. Preserve submitted Homework 1–4. Use participant-aware evaluation and earlier resolved labels for personal history. Fit preprocessing, feature selection, tuning, calibration and thresholds inside the permitted training data. Do not invent metrics or describe planned work as completed. Keep raw data, participant manifests, row-level predictions and fitted artifacts local and ignored by Git. Return changed files, commands, evidence, limitations and the next handoff. Do not submit coursework or contact anyone.

## Step 1 Turn the template into a checklist

**Agent task:** map each assignment section to a concrete question and the evidence needed to answer it. Use the local retained template at `.local/model-refinement/Model_Refinement_Template.docx`. The earlier review established that deployment and feature selection are conditional where the template says “if applicable.”

**Deliverable:** a short requirements checklist in the Homework 5 README, using the mapping near the end of this plan. Clearly separate template requirements, existing project commitments and optional experiments.

**Prompt:**

> Convert the Model Refinement template into an evidence checklist for NudgeWell. For each section, state the question we must answer, the existing evidence we can reuse, the new experiment or explanation needed, and the resulting table, figure or code excerpt. Separate assignment requirements from optional project extensions. Reuse the completed template review; do not start training.

**Complete when:** every section has an evidence source or a specific task that will produce one. No section depends on fabricated deployment, a new external test dataset, or an assumed improvement.

**Your role:** add any instructor feedback or submission-format rule that is not in the template. The agent can otherwise proceed from the supplied requirements.

## Step 2 Establish what Homework 4 already proves

**Agent task:** read the existing pipeline and aggregate results, prepare the starting comparison table, and turn the audit findings into actionable fixes.

The key findings already established are:

- Cleaned prevalence is **12.76%**, rather than the duplicated release's 14.9%.
- The fixed night/social/long-session rule achieved **21.82% precision and 41.78% recall**, flagging 24.44% of cleaned check-ins in the old analysis.
- The personal RF's pooled AUC was **0.8429**, while a constant personal rate achieved **0.8271**. Its within-person mean AUC was **0.5872**. Pooled AUC alone cannot establish good moment selection.
- The old personal population calibrator indirectly reuses held-out-person information through `global_oof[others]`; regenerate calibration scores inside each outer training universe.
- The old alert comparison selects a quantile of evaluation scores. Retain it only as a descriptive ranking diagnostic; a deployable cutoff must come from validation.
- The old split cuts through a local day for 34 participants. One session crosses its train/test boundary and one training outcome is unresolved at first testing.
- A key app-duration aggregate exceeds elapsed session time in 97 rows. Verify units and aggregation windows; this is an anomaly to investigate, not proof of leakage.

**Deliverable:** `build/baseline_review.md`, with the old results explicitly labelled as historical and an issue checklist linked to code locations.

**Prompt:**

> Using Homework 4's saved results and code, write the starting-point review for this homework. Separate trustworthy historical findings, comparisons needing a corrected rerun, and unresolved feature provenance. Explain the calibration path and threshold issue precisely. Identify what should be preserved and what must change. Do not present an anomaly as confirmed leakage or rerun the full analysis unnecessarily.

**Complete when:** we have a defensible baseline narrative and a finite list of fixes. The reviewed code and saved JSON, rather than memory or a previous chat summary, support every number.

## Step 3 Specify how experiments will be judged

**Lead task:** write `build/protocol.json` before new evaluation results are inspected. This is the common contract that keeps agents' experiments comparable.

Recommended homework scope:

- Keep binary classification as the main target, continuing Homework 4.
- Evaluate logistic regression and random forest as the core tuned models. Add XGBoost as the third family once the runner works; retain fixed LightGBM only if it adds useful comparison.
- Include population prevalence, personal base rate and the fixed rule as appropriate baselines.
- Treat calibration and one simple personal-offset comparison as refinements relevant to the project.
- Use an audited feature set and a small predefined feature-block comparison.

For new users, a practical default is **five outer participant-grouped folds and three inner grouped folds**. Inner folds choose features, parameters and model family; outer folds evaluate that complete selection procedure. The old LOPO results remain historical context. Explain the new nested strategy in the template's cross-validation section. If we elect to retain nested LOPO instead, choose that before opening the new results and apply it consistently.

For known-user comparisons, use whole local days: initial seven calendar days as warmup, then daily predictions using only labels resolved before the day's cutoff. Keep peer models trained on other participants. Purge unresolved outcomes and shared boundary sessions. This simulates daily updating, not a static holdout. Keep a defined fallback for small or one-class histories.

Primary tuning score: participant-balanced average precision, giving each participant total row weight one. Report ordinary pooled AP, ROC-AUC, within-person AUC where defined, and probability quality separately. For calibration, use training-only validation and Brier loss, supported by reliability plots. Thresholds must be fixed from validation before evaluation.

Record data/configuration hashes, seeds, fold definitions, candidate lists, preprocessing, calibration, threshold selection, metrics and tie rules. All participants have already appeared in exploration; describe the evaluation as retrospective internal validation, not an untouched external test.

**Prompt:**

> Write the shared experimental protocol for the minimum complete homework. Make the target, participant boundaries, personal-history timing, candidate models, selection metric, calibration procedure and final evaluation explicit. Use nested grouped validation for new users and a separate day-forward comparison for known users. Explain changes from Homework 4 and the concept note. Resolve ambiguous choices in the protocol before experiments; keep optional extensions separate.

**Complete when:** a data agent and a modelling agent could independently implement their parts without choosing different splits or metrics.

**Your role:** review the research question and scope: can we explain why these refinements are appropriate, and how their evaluation answers the homework? This is a substantive learning checkpoint, not a request to approve every implementation detail.

## Step 4 Implement the corrected data and evaluation code

**Agent task:** implement cleaning, feature construction, participant splits, day-forward splits and evaluation isolation. Reuse sound existing code, but preserve the old pipeline.

Use `esm_time` and `lock_time` for timing checks. A conservative history rule is `lock_time < prediction_cutoff`. IDs and timestamps can drive grouping and audits without becoming model inputs. Audit the app-use aggregates for pre-prompt availability; exclude unresolved columns from the main feature set and document the reason.

**Required tests:**

- The evaluated participant cannot enter population fitting, tuning or calibration.
- Changing that participant's future labels cannot change earlier predictions.
- No unresolved outcome or same boundary session enters earlier training.
- Imputation and scaling fit only on training rows.
- Outcome fields, identifiers and demographics cannot enter the classifier inputs.
- Evaluation labels or score distributions cannot change a previously fitted threshold.
- One-class histories, no positives, missing fields and zero alerts have defined behavior.
- Models in a comparison receive the same eligible evaluation rows.

Use small fixtures created inside tests; the older synthetic generator is absent from the repo. Add the new Homework 5 `run/` directory to `.gitignore` before generating private outputs.

**Deliverable:** data/split modules, the meaningful tests above, and an aggregate count-reconciliation report.

**Prompt:**

> Implement the data and split portions of the agreed protocol under Homework 5. Correct the known calibration isolation and timing risks without changing old submitted work. Add tests that would fail if future labels or the evaluated participant entered fitting. Audit feature timing and record unresolved columns. Use tiny local fixtures, then run a small integration check on the real file. Return the evidence that the boundaries hold.

**Complete when:** tests pass, counts reconcile, and a small model can run through the corrected pipeline. Review failures here before adding more models.

## Step 5 Run baselines and bounded refinement experiments

**Modelling task:** establish validation behavior of the fixed baselines, then implement a small comparison matrix. Use the same runner, folds and metric definitions for every method. Keep outer evaluation unavailable for choosing additional experiments.

| Experiment | Concrete change | Question answered |
|---|---|---|
| Baseline | Existing fixed LR/RF settings plus simple references | What does the corrected procedure achieve before tuning? |
| Hyperparameters | LR: four C values × two class-weight settings; RF: eight fixed sampled settings varying depth, minimum leaf size and class weighting | Does controlled tuning improve validation behavior? |
| Boosting | Optional eight XGBoost settings with shallow trees and bounded learning rates | Is a third algorithm useful beyond the core models? |
| Feature blocks | Audited full set versus removing tap/text/scroll fields | Can a simpler input set preserve or improve performance? |
| Calibration | Identity versus training-only sigmoid calibration | Are predicted probabilities more reliable? |
| Personalization | Frozen global score, personal base rate, and regularized personal offset | Does a small amount of personal information improve predictions beyond base-rate differences? |

Fix candidate lists and seeds in the protocol. With five outer folds, three inner folds and 16 LR/RF configurations, one feature-set search involves about 240 inner fits plus calibration/refits; optional boosting and a second feature set add to that budget. This is a bounded homework comparison, not an open-ended search for a high score.

Fit calibrators on held-out scores within the permitted training universe. A fitted calibrator's own calibration labels cannot also serve as independent evidence for selecting it. The evaluation agent should check the actual data flow.

**Deliverable:** model/configuration code, validation traces, warnings, runtime and a record of the complete selection procedure. Record failed or negative experiments too.

**Prompt:**

> Implement and run the predefined refinement matrix using the shared protocol. Start with fixed baselines and the LR/RF search; add the declared optional comparisons only if the runner is correct. Keep feature, parameter, family, calibration and threshold choices inside training validation. Save configurations and validation evidence. Do not change the experiment list in response to outer evaluation scores or claim that larger pooled AUC alone means better moment selection.

**Complete when:** every intended refinement has a rationale, a reproducible configuration and validation evidence. Freeze the complete selection procedure before final evaluation. Exact fitted parameters may differ by outer fold; the frozen object is the procedure for choosing them.

## Step 6 Apply the frozen procedure and evaluate

**Lead task:** run the complete nested procedure and collect outer predictions, then run the declared day-forward personal comparison. Generate reportable results from saved predictions and metadata.

For the template's “test submission” section, demonstrate model application on held-out evaluation folds/days. If the instructor supplies a separate test dataset, keep it untouched until the trained procedure is finalized and apply the same fitted preprocessing, calibration and threshold to it. Do not invent an external test set or imply a Kaggle-style submission is required by the generic wording.

Report:

- Training and inner-validation diagnostics, clearly distinguished from outer evaluation.
- AP and ROC-AUC, plus within-person discrimination and eligible participant counts.
- Brier/log loss and reliability curves for probabilities.
- Precision, recall, confusion counts and actual alert share at the validation-selected cutoff.
- Paired participant-level uncertainty for the main refinement-versus-baseline comparison.
- Personalization results against the personal base-rate baseline, on identical rows.

Keep single-class users in probability and decision metrics even where their within-person AUC is undefined. Use participant-level resampling rather than treating check-ins as independent. Do not keep testing new variants against these outer results; any later change is a separately labelled exploratory experiment.

**Deliverable:** aggregate result JSON/CSV, figures and a concise interpretation distinguishing supported gains, uncertain differences and negative findings.

**Prompt:**

> Execute the frozen procedure and create the final comparison tables and plots. Verify that every comparison uses matching rows and that all reported numbers can be traced to saved outputs. Explain pooled versus within-person performance and calibration versus ranking. Report paired participant uncertainty and coverage. Label retrospective internal evaluation accurately and preserve disappointing results.

**Complete when:** the evidence answers whether each refinement helped, for whom, and according to which metric.

## Step 7 Ask an independent agent to challenge the evidence

**Reviewer task:** inspect the code, protocol, manifests and tables. The reviewer should attempt to disprove the claims, not simply polish them.

**Prompt:**

> Independently review the Homework 5 implementation and results against the template and frozen protocol. Inspect participant isolation, temporal label availability, calibration inputs, feature selection, model-family selection and threshold fitting. Check metric denominators, one-class fallbacks, paired comparisons and source-to-table consistency. Identify defects with file/line evidence and practical consequences. Separate correctness problems from optional enhancements. Do not modify model choices just to improve a score.

**Deliverable:** actionable review findings and their disposition. The lead fixes correctness problems, reruns affected results and records why. Unaffected results need not be rerun.

**Complete when:** material correctness findings are resolved and the report's claims match what the experiment can support. Review a corrected result again if its calculation changed.

## Step 8 Fill the instructor template from the evidence

**Document task:** follow the supplied headings, replace instructional prompts with the project's actual work, and generate tables/figures from reviewed results. Use the document skill's render-and-inspect workflow.

| Template section | What to write | Evidence |
|---|---|---|
| Model Refinement — Overview | What we tried to improve and why | Target and experiment rationale |
| Model Evaluation | Starting results and weaknesses | Historical review and corrected baseline comparison |
| Refinement Techniques | Changes actually implemented | Experiment matrix and results |
| Hyperparameter Tuning | Search spaces, selection method and outcomes | Saved configurations and validation traces |
| Cross-Validation | Participant grouping, nested selection and personal timing | Protocol, split diagram and tests |
| Feature Selection | Audited inclusion/exclusion and feature-block comparison | Availability audit and ablation results |
| Test Submission — Overview | How the finalized procedure was evaluated | Evaluation contract and saved run metadata |
| Data Preparation for Testing | Deduplication, missingness, timing and fitted preprocessing | Count reconciliation and data code |
| Model Application | Applying the fitted processing/model/calibration in order | Real inference code excerpt |
| Test Metrics | Validation/evaluation comparison and interpretation | Reviewed tables and plots |
| Model Deployment | Actual current status; offline evaluation and remaining integration | Status supported by the repo |
| Code Implementation | Short meaningful excerpts with comments | Actual implemented source |
| Conclusion | What helped, what did not, limitations and next work | Reviewed results |
| References | Papers and libraries actually used | Verified primary sources |

Do not claim deployment, a completed neural model, effectiveness of real interventions, or superiority to the paper's regression benchmark unless that work was actually done. Binary AUC is not comparable to regression MAE or R². The historical concept-note commitments should be acknowledged where scope changed.

**Prompt:**

> Fill the supplied Model Refinement template for NudgeWell using only the reviewed implementation and results. Preserve the template's section order and recognizable formatting. Explain the experiments in a student's clear technical voice. Insert real metrics, figures and source-linked code excerpts; do not invent successful outcomes or completed deployment. Include limitations and accurate references. Render the DOCX and inspect every page, repairing layout defects before delivery.

**Deliverable:** completed DOCX, report/build source, figures and aggregate results. A PDF is an additional output if the course requires one; keep internal rendering images local.

**Complete when:** every template prompt is answered, every number traces to evidence, and the entire document has passed visual inspection.

## Step 9 Make sure you can explain the homework

**Your task with the lead agent:** walk through the completed work in plain language. You should be able to explain:

1. What the target means and why the model inputs cannot reveal its future outcome.
2. Why records from the same participant cannot be randomly mixed across training and testing for the new-user claim.
3. What tuning, feature comparison and calibration changed.
4. Why personal base rate is a necessary baseline and why a high pooled AUC can mislead.
5. Which result supports the conclusion, how uncertain it is, and what did not improve.
6. What is implemented and what remains future work.

**Prompt:**

> Walk me through our completed homework using our actual figures and code. Ask me one understanding question at a time about the target, splits, refinements, metrics and limitations. Help me explain any weak area accurately. Check that the final report reflects our real work and the course's rules for AI assistance.

**Complete when:** the report is understandable to you, the files open correctly, and you are comfortable defending the choices and conclusions. The final course submission remains your/team action.

## What is optional

TCN/GRU experiments, long personalization learning curves, prompt-budget/cooldown simulation, paper regression reproduction, model export and Android integration belong to broader project work. None is automatically required by this template. Add an extension only when it answers a chosen homework question and can use the same valid protocol. Do not add tasks just to make the submission look larger.

If demonstrating the prompt policy, predeclare three prompts per local day and a 30-minute cooldown and compare the fixed rule under the same restrictions. Describe it as an offline replay of sampled check-ins. If adding an adaptation curve, use a matched participant set; the existing audit found at most 33 users with 20 first-week labels and only one with 80, before availability filtering.

## Agent handoffs and parallel work

Use this dependency order:

1. Lead completes the requirement checklist and shared protocol.
2. Data/evaluation agent implements boundaries and tests while modelling agent prepares configuration/model code against the agreed interfaces. A document agent can prepare the template outline with explicitly pending evidence.
3. Lead integrates and runs the experiments through one runner.
4. Independent reviewer checks the integrated code and results.
5. Document agent writes from accepted results; lead cross-checks numbers and the final artifact.
6. You and the lead review the explanation and submission files.

Each handoff should name the files, completed checks, actual results, remaining issues and exact next task. The next agent reads those files rather than treating a predecessor's confident summary as proof. Avoid a chain of agents merely rewriting each other's prose without inspecting evidence.

## Files and synchronization

Proposed implementation files are `code/data_contract.py`, `code/splits.py`, `code/models.py`, `code/evaluate.py` and `code/run_refinement.py`; associated risk-focused tests; `build/protocol.json`; aggregate `build/results/`; figures; and the final report/build sources. These paths describe work to create, not existing completed code.

Use a feature branch for implementation, commit coherent steps, and push before switching computers. The PC must pull the same branch. Raw data and ignored runs stay local; recreate or privately transfer them separately if resuming computation on another machine. Preserve the old submitted artifacts.

## Existing evidence to reuse

- [Homework 4 pipeline](../04_data_preparation_model_exploration/code/hw4_pipeline.py) and [saved aggregate results](../04_data_preparation_model_exploration/build/results/results_real.json).
- [Homework 4 explanation and rebuilding instructions](../04_data_preparation_model_exploration/README.md).
- [Concept note and original project commitments](../03_concept_note_implementation_plan/build/concept_note.md).
- [Current data handling policy](../../data/README.md).
- Local retained template: `.local/model-refinement/Model_Refinement_Template.docx`.
- Local timing audit: `.local/model-refinement/data-audit.json`.
- [Nested evaluation reference](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html), [calibration reference](https://scikit-learn.org/stable/modules/calibration.html), and [installed-version metric definitions](https://scikit-learn.org/1.8/modules/model_evaluation.html).
