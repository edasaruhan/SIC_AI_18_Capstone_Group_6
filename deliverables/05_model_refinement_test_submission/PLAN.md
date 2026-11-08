# NudgeWell model refinement and test submission plan

Prepare a reproducible refinement report for **Thursday 12 November 2026**. Finish the results and report on **Wednesday 11 November** and keep 12 November for verification and submission. Dates and suggested cutoffs use Europe/Istanbul time; the submission hour has not been specified.

The recommended order is to repair evaluation, establish strong simple baselines, run a bounded search, evaluate personalization, and test a fixed prompt policy. A small temporal experiment is optional before a firm cutoff. Report measured improvements and negative results; completing the assignment does not depend on beating a benchmark.

This is an implementation plan. The audit findings below are verified; the proposed experiments have not yet been run. Preserve the submitted Homework 4 files as the historical record.

## 1 Current evidence and priorities

The working analysis is [`hw4_pipeline.py`](../04_data_preparation_model_exploration/code/hw4_pipeline.py). The submitted aggregate results are in [`results_real.json`](../04_data_preparation_model_exploration/build/results/results_real.json). The Mac can run the existing quick pipeline and a Jupyter kernel with the pinned Python 3.11 environment.

| Finding | Verified evidence | Consequence for this milestone |
|---|---|---|
| The effective sample is small | 5,627 unique check-ins, 718 positives, 37 participants; positive prevalence 12.76% | Keep models and search spaces small. Use participant-aware evaluation and intervals |
| Old prevalence figures are outdated for the cleaned data | 14.9% describes the released file with duplicates; the cleaned file is 12.76% positive | Use cleaned denominators in every new table and figure |
| Simple rules remain competitive | The combined night/social/long-session rule has 21.82% precision and 41.78% recall while flagging 24.44% of cleaned check-ins | Treat this as a required comparator, not an incidental illustration |
| Higher overall AUC can hide weak moment selection | Known-user personal RF has pooled AUC 0.8429, versus 0.8271 for a constant personal base rate; personal RF within-person mean AUC is 0.5872 | Separate pooled discrimination from ranking moments within a person |
| Calibration deserves attention | Old global LR Brier score is 0.2227; several models use class weights | Test unweighted fitting and training-only sigmoid calibration. Use reliability plots as well as Brier scores |
| App-duration provenance needs checking | `app_total_duration_session` exceeds elapsed session time in 97 rows from three participants; it is also the top old RF permutation feature | Audit units and the aggregation window before relying on it. This anomaly is a warning, not proof of target leakage |
| Timing boundaries need repair | Of 63 sessions with multiple check-ins, one crosses the old 70/30 boundary; one old training outcome is unresolved at the first test prompt; 34 participant splits divide a local day | Split on whole local days and purge unresolved training outcomes and shared boundary sessions |
| Personalization support is uneven | Before day 8, 36 people have at least 5 and 10 check-ins, 33 have 20, 26 have 40, and only one has 80 | Use a matched 0/5/10/20-label comparison; treat 40 as secondary and omit an aggregate 80-label curve |
| Some metric denominators are small | Three participants have a single binary class overall; 12 have a single class in the old chronological test slice | Keep these users in prediction and policy evaluation. Report how many people are eligible for within-person AUC |

The counts from the fresh timing audit use raw check-in counts before label-availability purging. Recompute eligibility after applying the final cutoff rules. The audit also confirmed millisecond timestamps, no missing prompt/unlock/lock timestamps, and `remaining_minutes = (lock_time - esm_time) / 60000` to numerical tolerance.

### Problems to fix before comparing refinements

1. **Indirect contamination of population calibration.** `personal_regime()` fits a population offset from `global_oof[others]`. Those scores were produced by LOPO models whose training sets include the target participant, including their later outcomes. For target participant G, regenerate every tuning and calibration score inside the universe that excludes G. The direct global prediction for G already excludes G; the problem is the reused calibration inputs. This affects the old intercept-based comparison, not every old model result.
2. **Evaluation-distribution threshold selection.** The old alert comparison computes a quantile of the evaluation predictions. This does not directly use evaluation labels, but it does use the evaluation score distribution to impose its budget. Keep that result as a descriptive ranking comparison; fit a deployable threshold on training/validation scores and freeze it before evaluation.
3. **Incomplete timing checks.** The feature-name guard catches explicit outcome columns, but cannot establish that an app aggregate was calculated before the prompt. Add provenance and temporal boundary checks.
4. **Historical scope differences.** The concept note promised continuous-gap regression, first-week/day-forward evaluation, 10x weighting for combined RF, and TCN/GRU experiments. Homework 4 instead reports binary classification, a 70/30 check-in split and combined weight 5. Explain these changes explicitly. AUC cannot be compared to the paper's MAE or R².

## 2 Scope for 12 November

### Required work

- Correct participant isolation, chronological splits, outcome availability, calibration and threshold selection.
- Reproduce the old outputs separately, then evaluate unchanged baselines under the corrected protocol so protocol effects can be separated from model improvements.
- Tune logistic regression, random forest and XGBoost within a fixed compute budget. Retain the existing LightGBM configuration as a fixed comparator; a fourth large search is unnecessary.
- Compare population probability, personal base rate, global scores, global scores with personal offset, personal RF and combined RF on identical eligible rows.
- Run a small, predefined feature ablation and calibration comparison.
- Evaluate a fixed threshold and a chronological prompt-budget replay.
- Produce the filled Word template, reproducible code, aggregate results, figures, run metadata and a clear account of limitations.

### Optional work with a cutoff

One compact TCN and a simple history-feature comparator may be included if the core evaluation passes by **10 November at 12:00** and the pilot works within two hours of implementation plus two hours of compute. Stop new model development by **10 November at 18:00**. A working optional experiment must use the same evaluation contract; a validation-only pilot must be labelled as such.

### Work deferred from this submission

Full TCN/GRU architecture searches, dual-target training, continuous-gap paper reproduction, neural fine-tuning, ONNX/LiteRT export, Android integration, SHAP integration and a new secondary dataset are outside the critical path. Record these as outstanding concept-note commitments. The assignment makes deployment conditional; explain its current status rather than claiming an on-device system exists.

Follow the current [`data/README.md`](../../data/README.md) coursework-only handling policy. Keep raw data, row-level predictions, participant manifests and trained artifacts local. Record the discrepancy with the older concept note's permission wording, and confirm reuse permission before publishing weights or deploying a trained model. This plan does not authorize contacting anyone or submitting coursework.

## 3 Freeze the evaluation contract

Write `build/protocol.json` before running the new outer evaluations. It must contain the dataset SHA-256, duplicate rule, label definition, feature sets, splitter version, candidate configurations, selection metric, seeds, calibration procedure, threshold rule, policy settings and reporting rules. Freeze this file in Git. Changes after results are inspected require a new protocol version and an explicit exploratory label.

### Target and feature availability

- Keep Homework 4's target: `answer <= 5 AND remaining_minutes > 5`.
- Remove exact duplicate rows before creating splits or histories.
- Exclude all direct outcomes, identifiers and demographic columns from classifier inputs.
- Use demographics only for aggregate descriptive error checks; verify category encodings before attaching labels.
- Keep timestamps and session IDs available to the splitter, history builder and audit, but never feed them as raw model features.
- Use `lock_time < prediction_cutoff` as the conservative rule for when an earlier label becomes available. Avoid deriving an earlier availability time from the outcome itself.
- Fit imputers, scalers, feature selection, class-weight calculations and calibration within the permitted training universe. No full-dataset fitting or synthetic oversampling across splits.

### New-user evaluation

For each of the 37 held-out participants G:

1. Exclude every row of G from population fitting, feature selection, hyperparameter selection, population priors and calibration.
2. Tune using three participant-grouped inner folds on the other 36 participants. Use the same inner assignments for all candidates.
3. Select one candidate per family from inner results only. Generate training-only out-of-fold scores for calibration and threshold fitting; never reuse an OOF array generated across all 37 people.
4. Refit the selected base model on the permitted background participants and score G. If a calibration ensemble is used, preserve its fold-specific fitted models and apply the same ensemble definition to threshold fitting and evaluation.
5. Store the prediction and provenance locally. Every row of G receives one outer prediction per declared model procedure.

The primary new-user tuning score is **participant-balanced average precision**: concatenate inner held-out predictions and weight each participant's rows to total weight one. This includes negative-only participants as potential false alerts without letting large participants dominate. Also report ordinary pooled AP and within-person AUC; do not call weighted AP a within-person ranking measure.

If the complete 37-fold search is projected to exceed four hours after a timed pilot, switch before inspecting performance to a documented **five-outer-fold, three-inner-fold grouped evaluation**. Use it for every model in that comparison. Do not screen hyperparameters on all participants and then present fixed-parameter LOPO scores as nested evaluation.

The peer cohort is treated as a previously collected offline training cohort. Within-person time order is enforced, but this is not a claim of prospective deployment over a shared global calendar.

### Known-user evaluation

Use a day-forward simulation instead of the old row-count split:

1. Define a local day using the released `date_4am` convention after validating its relationship to the local prompt timestamps. Count **elapsed calendar days**, not simply seven observed dates.
2. Use the first seven local calendar days as initial history. Starting on day 8, predict the next day's check-ins using only labels resolved before that day's cutoff.
3. Purge training rows whose sessions appear in the evaluation day, including a session that crosses the day boundary. Earlier unresolved sessions cannot provide labels or outcome-history inputs.
4. Refit permitted personal models or update their offsets at the daily cutoff. Keep population models trained on other participants frozen for this simulation.
5. Score each eligible check-in once. Earlier test-day outcomes may enter training on later days after they resolve; describe this as daily updating, not a static untouched holdout.
6. Choose hyperparameters and shrinkage rules on the background participants using analogous forward simulations. Never tune them on G's future days. Run an all-user population-only fallback where the personal history is too short or single-class.

One participant has only one observed check-in during their first seven calendar days. Keep that person and apply the fallback. Do not silently change their warmup to seven observed days. A seven-observed-day sensitivity analysis may be reported separately if time permits.

### Prior exposure to the dataset

All participants have already appeared in EDA and Homework 4. Describe the new results as internally evaluated, retrospective coursework experiments with a frozen refinement protocol. Nested isolation reduces tuning bias but does not turn an already explored dataset into a new independent test set. An external/prospective dataset would be needed for that claim.

## 4 Implementation sequence and acceptance checks

### Step A Preserve the baseline and make runs traceable

Create a separate Homework 5 folder. Reuse audited feature definitions where appropriate, but do not edit old reports or overwrite their results. Keep a copy of the reference DOCX under local `guidelines/` or `.local/`; avoid leaving the only copy in WhatsApp's temporary directory.

Each run must record the Git commit, Python/package versions, platform, dataset hash, config hash, seed, fold schedule, runtime and warnings. Save checkpoints per outer participant/fold so a run can resume after switching computers. Use one level of parallelism; keep individual tree fits to two threads when folds run concurrently. Measure the first outer fold before committing to the full runtime.

**Done when:** a clean checkout plus local data can reproduce a baseline command, and raw data/predictions/checkpoints are confirmed ignored by Git.

### Step B Add tests that target the actual risks

Use tiny fixtures created inside the tests; the missing older synthetic simulator is not a dependency.

- A held-out participant cannot occur in any fitting, tuning or population-calibration manifest.
- Changing G's future labels must leave G's earlier predictions unchanged. For a frozen zero-shot model, changing any of G's labels must leave every prediction unchanged. This catches indirect calibration contamination.
- No label with `lock_time >= cutoff` enters a daily training set or history.
- Train and evaluation sessions are disjoint at the cutoff; same-session outcomes remain unavailable.
- A sequence contains only earlier observations from the same person. Padding is masked and does not cross a person boundary.
- A fitted threshold remains unchanged when evaluation labels or evaluation score distributions are altered.
- No outcome/identifier/demographic column can enter the model matrix. Scaling and imputation fit on training rows only.
- One-class histories, empty eligible histories, zero alerts, no positives and missing app data return defined fallbacks and denominators.
- Check-in counts reconcile through duplicate removal, purging, warmup and evaluation. Every model in a comparison uses the same rows.

**Done when:** these tests pass and the corrected unchanged baselines complete. Treat this as a prerequisite for tuning, not a report appendix to write later.

### Step C Audit and compare a small set of feature blocks

For each app-use column, document units, aggregation window, available-at-prompt evidence and whether the Android prototype could produce it. Compare values with elapsed time without silently clipping or reinterpreting units.

Use these feature configurations:

| Set | Definition | Purpose |
|---|---|---|
| F0 | The old 49 features | Historical reproduction and sensitivity reference |
| F1 | All old features whose pre-prompt availability passes the audit | Main evaluation set |
| F2 | F1 without the ten tap/text/scroll interaction fields | Tests a lower-permission sensing option |
| F3 | F1 plus simple earlier-check-in summaries | Tests whether history helps without a neural network |

If provenance remains unresolved for the seven app-use aggregates (`app_duration`, session app duration/count/switch fields, and daily app duration/count/switch fields), exclude those fields from F1. Removing all seven leaves 42 features; removing only the three durations leaves 46. Record the actual decision per column. Do not choose which uncertainty to tolerate by looking at outer scores.

F3 is optional: previous check-in feature values, time since the previous check-in, and a short mean of earlier feature values, with a history-length indicator. Current-row values must be excluded from historical summaries. Keep outcome-based history to the separately declared personalization methods so its information advantage is explicit.

Evaluate F1/F2 in the inner selection process. F0 remains a labelled sensitivity analysis if its provenance is unresolved. If F3 is attempted, register it before outer results are opened. Do not search arbitrary combinations of the 49 columns; do not select the top features using old full-dataset importance and call that independent selection.

### Step D Fit fixed baselines and bounded refinements

Required baselines are the training-population prevalence, a shrunk personal prevalence where labels are available, the combined fixed rule, and the old fixed LR/RF/XGB/LightGBM configurations under the corrected protocol.

Use the following bounded classification searches, with seed 42 for deterministic configuration sampling:

| Family | Search | Maximum configurations per feature set |
|---|---|---|
| Logistic regression | `C` in 0.01, 0.1, 1, 10; class weight none or balanced; training-fold median imputation and standardization | 8 |
| Random forest | 200 trees; depth 3, 6 or unrestricted; minimum leaf size 5, 15 or 30; max features sqrt or 0.5; class weight none or balanced | 12 sampled combinations |
| XGBoost | 200 trees; depth 2, 3 or 4; learning rate 0.03 or 0.1; minimum child weight 5 or 15; subsample 0.7 or 1; positive weight 1 or training-fold negative/positive ratio | 12 sampled combinations |
| LightGBM | Existing Homework 4 configuration, including its existing number of trees | 1 fixed comparator |

The 32 searched configurations require about 3,552 inner fits for one feature set with 37 outer participants and three inner folds, plus refits, calibration and fixed comparators. F1/F2 double the searched fit count; time the pilot and apply the four-hour budget. If needed, halve both tree searches to six configurations before evaluation, or choose the five-fold grouped fallback. Record this once, before outer metrics are inspected.

Within each outer training universe, choose by participant-balanced AP. Use a fixed tie rule: if scores differ by less than 0.005 AP, prefer fewer features, then LR over a tree ensemble, then shallower trees. This is a pragmatic selection rule, not a significance threshold. The final evaluated procedure must include family/feature selection inside the outer loop; showing separate family results is secondary, not permission to pick an outer-score winner and claim an unbiased final estimate for it.

**Done when:** each baseline and selected procedure has valid outer predictions, configuration traces, train/validation diagnostics and no fitting failures hidden by blanket warning suppression.

### Step E Evaluate probability calibration and personalization

For population calibration, use a sigmoid transformation as the primary method and identity as the comparator. Fit on group-held-out scores generated entirely within the outer training universe. Choose identity versus sigmoid using further training-only calibration validation and Brier loss; never score a fitted calibrator on its own calibration labels to select it. Use a documented cross-fitted ensemble or a separate grouped calibration partition consistently through threshold fitting and evaluation. Defer isotonic calibration because small calibration sets make it an unnecessary additional degree of freedom for this deadline. Calibration data must be independent of each underlying base-model fit, as described in the [scikit-learn calibration guide](https://scikit-learn.org/stable/modules/calibration.html).

For the day-forward task, compare on identical rows:

1. Population prevalence and shrunk personal prevalence.
2. Frozen calibrated global model.
3. The same global model plus a regularized personal log-odds offset, using resolved earlier labels only.
4. Personal RF, falling back to the shrunk rate when the training history has one class.
5. Combined RF, mixing the frozen peer training cohort with resolved local history. Compare personal weights 1, 5 and 10 on background-user forward validation only, then freeze the rule for G.

Choose personal-rate prior strength from 5, 10 and 20 pseudo-observations, and offset prior standard deviation from 0.25, 0.5, 1 and 2. Use background-participant day-forward validation and mean per-participant Brier loss to select these inexpensive settings. Tune personal/combined tree choices by participant-balanced AP on the analogous background forward predictions. Freeze all these choices before evaluating G. Prevent Newton updates from producing non-finite offsets; use bounded optimization or damping and a tested fallback. Keep fixed scores and offsets separate in saved metadata so the information source is inspectable.

For adaptation curves, freeze the personal update after the first **n = 0, 5, 10, 20** resolved labels from the initial seven days. Use the same post-week-one evaluation rows for every n. Use a common eligible participant set across those n values, expected to contain at most 33 participants before purging. Report a separate all-37-user result with fallback. Add n = 40 only as a secondary matched comparison with its own denominator, expected at most 26. Do not draw an aggregate n = 80 curve from one eligible participant. The learning-curve experiment freezes adaptation; distinguish it from the daily-updating main experiment.

**Done when:** the report can show whether personal calibration improves probability quality or alert usefulness, and whether a personal RF adds within-person ranking beyond a constant personal rate.

### Step F Apply a frozen prompt policy

Estimate the combined fixed rule's alert share on training/validation opportunities in each outer training universe. On independent or cross-fitted calibrated validation scores, choose a threshold that approaches that budget without exceeding it; define deterministic handling of ties. Freeze the numeric threshold before scoring the outer participant. The test alert share may differ from the validation target; report that difference rather than moving the threshold.

Report two distinct analyses:

- **Fixed-threshold evaluation:** precision, recall, alert share, confusion counts and false alerts. This is the deployable decision rule.
- **Equal-alert-count ranking diagnostic:** top-k selection using an evaluation score distribution may be shown only as a retrospective diagnostic, clearly separate from the frozen-threshold result.

Replay each person's evaluation opportunities in timestamp order with the primary **three prompts per local day and 30-minute cooldown**. Reset the budget at the declared local-day boundary. Apply the same budget and cooldown to the fixed-rule baseline. Exclude a prediction if its prerequisite history is unavailable; record the reason and apply the same opportunity mask to all compared methods.

Report prompts per observed person-day, precision, recall, high-gap moments reached, and the fraction of prompts where the person reported wanting to continue (`answer > 5`). The answer is permitted here as a retrospective evaluation outcome, never as an input. Report the number of observed opportunities and days; the public check-ins do not represent every phone-use moment or a real intervention trial. Add one predeclared sensitivity of two prompts/day and a 60-minute cooldown if time permits; do not use it to replace a disappointing primary result.

## 5 Metrics and rules for interpreting improvements

| Question | Required measures | Reporting rule |
|---|---|---|
| Can the model generalize to a new user? | Participant-balanced AP, ordinary pooled AP, pooled ROC-AUC | Keep the balanced-AP selection metric fixed. Do not select by headline pooled AUC afterward |
| Does it rank a person's moments? | Mean within-person ROC-AUC and AP; participant counts and prevalence; random-score AP reference on identical rows | Exclude one-class people only from undefined AUC calculations; keep their errors in the other measures |
| Are probabilities useful? | Brier, log loss, reliability diagram with bin counts; mean prediction versus observed prevalence | Brier alone is not a pure calibration measure; inspect the reliability plot |
| Does the prompt rule help? | Precision, recall, alert share, prompts/day and false-prompt measures | Compare on identical opportunities with thresholds fixed before evaluation |
| Is personalization useful? | Matched change versus personal base rate and frozen global model | Report differences and participant coverage, not just each model's separate headline score |
| Is the result stable? | Paired participant bootstrap intervals, per-person distribution, dominant-participant sensitivity | Resample participants with all their rows; do not bootstrap individual check-ins as independent |

Use 2,000 paired participant bootstrap replicates for the principal contrasts, seed 2026. The same resampled people must be used for both models. Report intervals for the **difference**, not a conclusion inferred from overlap between separate intervals. These intervals summarize variation across the observed participant predictions; they do not fully capture model-selection uncertainty or establish transportability.

The top participant accounts for 19.64% of positives, the top three for 37.05%, and the top ten for 73.26%. Show a prespecified sensitivity excluding the highest-positive contributor from metric aggregation; retain the primary model fits, identify it as an aggregation sensitivity, and do not use it for selection. A separately retrained cohort-removal analysis is optional and must be labelled distinctly.

For demographic summaries, verify the dictionary's currently incomplete gender encoding before use. Include participant and positive-event counts and suppress tiny identifying breakdowns. Treat age/gender results as exploratory descriptions of 37 adults, not evidence of demographic fairness or validity for Türkiye.

**Decision rule:** a positive paired point difference with an interval including zero is suggestive, not established improvement. A higher pooled AUC with unchanged within-person ranking is mainly a between-person gain. A negative result still satisfies refinement if the protocol and experiments are complete. The old 21.82% precision and 41.78% recall are historical references; the actual policy comparison uses a freshly evaluated baseline on the same new rows.

## 6 Optional temporal experiment

Register this optional design and F3 in the initial protocol; the later go/no-go decision depends on test correctness and remaining runtime, not a disappointing outer score. Start implementation only after Steps A–E are working and the 10 November gate is met. Prefer the simple F3 history summaries first. If they and the sequence tests work:

- Use one causal TCN with 16 earlier check-ins, two small causal convolution blocks, roughly 16 hidden channels, dropout 0.2, and fewer than 50,000 parameters verified in the run log.
- Keep a separate current-feature branch. History consists of earlier features and elapsed-time indicators, plus padding masks; do not add earlier answers or outcomes in this first experiment.
- Fit imputation and scaling on training participants only. For a strict cold-start task, earlier held-out-user features are available as unlabeled history; their outcomes are not.
- Cap training at 50 epochs, early-stopping patience five on a participant-held-out inner validation set, learning rate 0.001, and seeds 42, 43 and 44. Fix the architecture; no architecture search.
- Run a validation pilot and benchmark runtime first. Include a final nested/grouped comparison only if it can finish under the same frozen evaluation rules by the cutoff. Otherwise describe the pilot honestly and defer a comparative claim.
- Add GRU only after the submission. Do not call the TCN-only experiment completion of the original TCN-and-GRU commitment.

This branch tests a hypothesis about temporal information; the dataset's size makes success uncertain. It cannot displace the required calibrated tabular and policy results.

## 7 Files to create during implementation

All paths below are proposed; only this plan currently exists in the Homework 5 directory.

```text
deliverables/05_model_refinement_test_submission/
  PLAN.md
  README.md
  requirements.txt
  code/
    data_contract.py      # cleaning, availability checks, feature sets
    splits.py             # grouped nesting and local day-forward schedule
    models.py             # bounded tabular configurations and personal offset
    evaluate.py           # cross-fitting, calibration, metrics, paired contrasts
    policy.py             # frozen threshold, daily budget and cooldown
    run_refinement.py     # CLI, manifests, resume and run metadata
  tests/
    test_isolation.py
    test_time_and_history.py
    test_policy_and_fallbacks.py
  build/
    protocol.json
    make_figures.py
    build_report.py
    report.md
    results/              # aggregate-only JSON and summary CSV
  figures/
  run/                    # ignored: manifests, predictions, fitted artifacts
  NudgeWell_Group6_Model_Refinement_Test_Submission.docx
```

Add the new `run/` directory to `.gitignore` **before** generating any row-level outputs. The old ignore rule covers Homework 4 only. Keep any newly added instructor template under a local ignored directory unless the team intentionally decides to version it. Use portable paths based on the repository root, and keep the Python environment outside Git.

The eventual CLI should support commands equivalent to `--stage audit`, `--stage baseline`, `--stage refine`, `--stage personalize`, `--stage policy` and `--stage report`, with a config path, output directory and resume option. These are interfaces to implement, not commands currently available.

Use a working branch such as `codex/model-refinement`, commit completed code/configuration stages, push before switching computers, and pull the same branch on the other machine. Push aggregate evidence and source; keep participant-level run files local. To resume on the PC, either rerun the deterministic job from its manifests or transfer ignored outputs privately; Git alone will not transfer them. Do not run two jobs writing to the same output directory.

## 8 Map evidence into the instructor template

| Template section | Content to supply | Concrete evidence |
|---|---|---|
| Model Refinement 1 Overview | Binary target, core question, scope and changes from the concept note | Data contract and protocol |
| 2 Model Evaluation | Corrected baseline weaknesses, pooled versus within-person results | Baseline table and participant performance plot |
| 3 Refinement Techniques | Audited feature sets, regularization, personal offset and calibration | Ablation and method comparison table |
| 4 Hyperparameter Tuning | Exact spaces, candidate budgets, inner scores, selection rule and runtime | Search summary plus a short executable code excerpt |
| 5 Cross-Validation | Outer participant exclusion, inner selection, daily updating and prior exposure | Split diagram and isolation tests |
| 6 Feature Selection | Pre-prompt audit and F1/F2 comparison; F3 only if completed | Availability table and ablation result |
| Test Submission 1 Overview | Frozen evaluation procedure and model application | Protocol hash and run metadata |
| 2 Data Preparation for Testing | Deduplication, warmup, local days, label purging and missingness | Count reconciliation table |
| 3 Model Application | Fitted preprocessing, calibration, offset and threshold applied in order | Inference code excerpt with no participant records |
| 4 Test Metrics | Outer metrics, validation diagnostics, paired differences and policy measures | Main results, reliability diagram and policy table |
| 5 Model Deployment | Current offline status, sensing gaps, permission status and deferred integration | Explicit status statement; no fabricated deployment |
| 6 Code Implementation | Representative split, fit, calibration and replay code | Source-linked snippets generated from the actual scripts |
| Conclusion and References | What improved, what failed, what remains unresolved | Frozen results and primary-source citations |

Aim for roughly **10–14 readable pages**, adjusted to the content rather than padded. Required figures are a split diagram, a PR comparison, a calibration plot, a pooled/within-person comparison, the matched adaptation curve and a prompt-policy comparison. Use tables for the candidate budgets, feature availability and final metrics. Optional temporal figures enter only if the experiment finishes.

The authoritative submission format in this request is the supplied Word template. Build the DOCX and render every page for inspection. A PDF can be supplied if the course requires it; macOS rendering has already worked for the template, so the old Word/PowerShell script is not the only possible review route. Check font substitutions, clipping, table breaks, captions, source citations and consistency between figures and JSON. Keep validation renders local.

## 9 Schedule and cutoffs

The schedule assumes about **26–32 focused hours** plus background compute. It is a planning estimate, not a measured implementation duration. Keep the ordering if the working hours shift.

| Date | Work | Deliverable and stop rule |
|---|---|---|
| Sun 8 Nov | Complete the audit and plan; retain the template; choose scope | This plan and the issue list. No new performance claims |
| Mon 9 Nov morning | Implement contracts, manifests, whole-day splits and contamination tests | Isolation tests pass; protocol draft freezes the search and metrics |
| Mon 9 Nov afternoon and evening | Corrected fixed baselines; timed nested-search pilot; implement calibration and resume | Baseline results plus runtime estimate. If the four-hour projection fails, reduce the predeclared search or use grouped outer folds before viewing scores |
| Tue 10 Nov morning | Complete tabular tuning and daily personalization; establish matched adaptation eligibility | Core outer predictions and valid personal comparisons |
| Tue 10 Nov by 12:00 | Decide whether the optional temporal pilot is feasible | Skip it if the core is incomplete. No extension of this gate to chase a better score |
| Tue 10 Nov by 18:00 | Finish any optional pilot and freeze all model/config choices | End new model development. Preserve completed negative results |
| Wed 11 Nov morning | Policy replay, paired intervals, feature/coverage summaries and required plots | Final aggregate evidence; stop model changes except correctness fixes |
| Wed 11 Nov afternoon and evening | Fill the template, build and inspect all pages; verify report numbers against JSON | Complete DOCX and reproducible source committed and synchronized. Target a readable first complete report by 18:00, final checks later that evening |
| Thu 12 Nov | Verify final file, links, branch status and submission requirements | Submission buffer. No new experiments; submission itself remains a separate user/team action |

If time slips, cut in this order: GRU and paper-reproduction work already deferred; then the TCN pilot; then F3 history summaries; then optional sensitivities. Preserve correct evaluation, required baselines, bounded tuning, calibration, the main personalization comparison, primary policy replay and a complete report. If needed, reduce search configurations or the number of outer grouped folds before running them, and report the change. Never simplify by mixing participants or tuning on evaluation results.

The original concept note names Bahadır for modelling/personalization/policy, Ersel for tree baselines/evaluation, Çağla for data/splits, Fatih for testing/content and Damla for Android. These are existing roles, not confirmed availability for this deadline. The core plan must remain executable by Bahadır with coding assistance; teammate review can improve it without becoming a dependency. No messages or assignments have been sent.

## 10 Submission acceptance checklist

- [ ] Target, cleaned counts, feature provenance and data hash are frozen.
- [ ] Population training and calibration fully exclude the evaluated participant.
- [ ] Day-forward fits contain only resolved labels and disjoint boundary sessions.
- [ ] Corrected fixed baselines and refinements share the same opportunities.
- [ ] Search, calibration, feature and family selection happen inside evaluation boundaries.
- [ ] Numeric thresholds are frozen before evaluation; budget/cooldown are implemented and tested.
- [ ] All one-class users remain represented through defined fallbacks and denominators.
- [ ] Pooled, within-person, calibration and policy findings are distinguished.
- [ ] Main differences have paired participant intervals; unsupported improvement claims are removed.
- [ ] All completed experiments, including failures, are listed with runtime and configuration.
- [ ] No claim of untouched external testing, intervention effectiveness, paper reproduction or deployment exceeds the work performed.
- [ ] The filled template includes every required section and real source-linked code excerpts.
- [ ] The final document has been rendered and every page visually checked.
- [ ] No raw records, participant identifiers, timestamps, private predictions or model checkpoints are staged for Git.
- [ ] Another computer can obtain the source, install dependencies and reproduce the aggregate results with its local dataset.

## 11 Sources and audit locations

- [Submitted Homework 4 results](../04_data_preparation_model_exploration/build/results/results_real.json), [analysis implementation](../04_data_preparation_model_exploration/code/hw4_pipeline.py), and [Homework 4 README](../04_data_preparation_model_exploration/README.md).
- [Original concept note and implementation commitments](../03_concept_note_implementation_plan/build/concept_note.md) and [current data handling policy](../../data/README.md).
- Local reference: `.local/model-refinement/Model_Refinement_Template.docx`; rendered and inspected as a two-page template. Local timing audit: `.local/model-refinement/data-audit.json`. These files stay local and are not required to read this plan.
- [AwareMind paper, model design in Section 4.3](https://arxiv.org/html/2609.08909v1#S4.SS3): confirms regression, LOPO, daily personal updates after week one and combined weighting. It supplies context, not directly comparable binary-classification targets.
- [scikit-learn nested evaluation example](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html): supports separation of model selection and evaluation.
- [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html): supports independent calibration inputs and reliability-curve interpretation.
- [scikit-learn 1.8 metrics documentation](https://scikit-learn.org/1.8/modules/model_evaluation.html): definitions and implementation reference for the installed analysis version.
