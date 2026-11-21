# HW5 baseline review and proposed evaluation contract

**NudgeWell, Group 6 — Step 2 — 16 November 2026**

The HW4 results support a weak new-user classifier and substantial differences in risk between people. They do not establish a reliable personalized intervention system. The personal-offset calibration has an indirect held-out-participant dependency; the alert comparison uses evaluation-score quantiles; and the personal split does not enforce day, session or outcome-availability boundaries. Repair these comparisons before measuring refinement gains.

This review reconciles existing evidence and proposes decisions for Step 3. It does **not** freeze the protocol, fit models, generate new model-performance estimates or complete the assignment. HW1–4 are unchanged.

## Sources, verification and limits

Paths below are relative to this file. Line references refer to the source at branch checkpoint `1edafe600db4bfe28ccd8eb376b0604753d2a927`; file hashes and function ranges are recorded in [baseline_evidence.json](baseline_evidence.json).

| ID | Source | Use |
|---|---|---|
| C | [HW4 pipeline](../../04_data_preparation_model_exploration/code/hw4_pipeline.py) | Actual cleaning, feature construction, fitting, calibration, splitting and metrics |
| J | [Saved real-data results](../../04_data_preparation_model_exploration/build/results/results_real.json) | Historical metric values, coverage, uncertainty and descriptive aggregates |
| H | [HW4 README](../../04_data_preparation_model_exploration/README.md) | Submitted scope and reproduction instructions |
| P | [HW5 workflow](../PLAN.md) | Prior audit, bounded scope and Steps 2–3 |
| R | [HW5 requirements and continuation handoff](../README.md) | Section mapping and exact next deliverable |
| D | [Data card](../../../data/README.md) | Target, exclusions and handling policy |
| V | [Verification script](verify_baseline.py) and [aggregate evidence](baseline_evidence.json) | Reconciliation against the local released CSV; no model imports or fitting |

The Mac's ignored `.local/model-refinement/data-audit.json` and retained HW5 DOCX template were unavailable on this PC. The section requirements here therefore rely on R; they were not rechecked against the original template. A local copy of the released CSV and its dictionary exists outside this Git checkout. V checks only aggregate counts and the old split; it does not copy raw data. The dictionary describes `session_minutes` as time up to the prompt, but does not specify collection cutoffs for every app/interaction aggregate. Its overview says 83 columns; the actual CSV has 92.

No historical prediction file was available. Model metrics and confidence intervals below are **transcribed from J and traced to C**, not independently reproduced from predictions. V verifies data denominators, class coverage, saved confusion-table arithmetic and source hashes. A corrected model rerun remains future work.

## 1. Historical starting point

### Data and estimands

The target remains `answer <= 5 and remaining_minutes > 5` (C:88–94). Exact duplicate removal precedes feature construction. Local count checks agree with `J.data`: 5,772 released rows, 145 exact duplicates, **5,627 unique check-ins**, **718 positives**, **37 participants**, prevalence **12.7599%**. The earlier release-level 14.8822% includes duplicated records and is not the cleaned prevalence.

C:97–113 constructs 49 main inputs and excludes named outcomes/identifiers; demographics are added only for sensitivity analysis. Medians/scaling are fitted inside model pipelines (C:125–163), which is worth preserving. The exclusion assertion checks names, not the provenance of the values already stored in a permitted column.

- **New-user historical regime:** fixed-setting leave-one-participant-out (LOPO); each base model excludes the scored participant from fitting (C:248–254, 593–608). Pooled metrics use all 5,627 rows from 37 people. Within-person means use **34 people with both classes**; the three all-negative people remain in pooled metrics.
- **Known-user historical regime:** each participant's first `floor(0.7*n)` timestamp-sorted rows train and the rest test (C:257–264, 291–345). Every listed approach uses **1,705 test rows**, **219 positives**, **37 people**, prevalence **12.8446%**. Within-person metrics use **25 people with both classes**. This is a static row split, not seven-day warmup/daily retraining.
- C:167–172 computes the field named `pr_auc` with `average_precision_score`. Call it **average precision (AP)**. It is not trapezoidal PR-curve area. Within-person AP is the equal-person mean over the eligible two-class people (C:175–189, 205–225); it is not pooled AP or the proposed participant-balanced pooled AP.

### New users: saved fixed-setting LOPO results

All values are historical, rounded to four decimals. J path for each row: `global[model_name].{roc_auc,pr_auc,brier,within_roc_auc,within_pr_auc,within_n}`. C locations: models 125–163; LOPO 248–254; summaries 167–225; call site 593–608.

| Model name in J | Pooled ROC-AUC | Pooled AP | Brier ↓ | Within-person AUC | Within-person AP | Within coverage |
|---|---:|---:|---:|---:|---:|---:|
| LR | 0.6160 | 0.1775 | 0.2227 | 0.6229 | 0.2526 | 34/37 |
| RF | 0.5984 | 0.1563 | 0.1929 | 0.6298 | 0.2357 | 34/37 |
| XGB | 0.5743 | 0.1541 | 0.1972 | 0.6113 | 0.2389 | 34/37 |
| LGBM | 0.5574 | 0.1506 | 0.1882 | 0.6019 | 0.2309 | 34/37 |
| RF + demographics | 0.5573 | 0.1547 | 0.1757 | 0.6303 | 0.2493 | 34/37 |
| LR + demographics | 0.5242 | 0.1436 | 0.2225 | 0.6343 | 0.2529 | 34/37 |
| Fixed rule (night, social or > 10 min) | 0.5994 | 0.1654 | 0.2653* | 0.5699 | 0.1839 | 34/37 |

*The rule's Brier value is the arithmetic score of a 0/1 decision, not evidence of calibrated probabilities. It should be presented as a decision reference, not selected as a probability model. The demographics rows are historical sensitivity checks, not proposed main inputs. The largest observed AUC here does not establish statistically reliable superiority among model families.

### Known users: saved results on matching old test rows

J path for each row: `personal.approaches[model_name]` with the same metric keys. C locations: 291–345, including base-rate shrinkage (312), personal offset (315–321), personal trees/fallback (322–333) and weighted combined RF (334–338).

| Model name in J | Pooled ROC-AUC | Pooled AP | Brier ↓ | Within-person AUC | Within-person AP | Within coverage |
|---|---:|---:|---:|---:|---:|---:|
| Own base rate | 0.8271 | 0.5070 | 0.0836 | 0.5000 | 0.1995 | 25/37 |
| Global (zero-shot) | 0.5980 | 0.1520 | 0.1931 | 0.6022 | 0.3102 | 25/37 |
| Global + personal intercept | 0.8371 | 0.5396 | 0.0824 | 0.6022 | 0.3102 | 25/37 |
| Personal RF | 0.8429 | 0.5581 | 0.0856 | 0.5872 | 0.3617 | 25/37 |
| Personal XGBoost | 0.8126 | 0.3651 | 0.1087 | 0.6106 | 0.3743 | 25/37 |
| Combined RF | 0.7440 | 0.4054 | 0.1699 | 0.6154 | 0.3719 | 25/37 |

A constant score per person achieves pooled AUC 0.8271 while providing no within-person ranking (AUC 0.5). Much of the high pooled performance can therefore come from separating people with different base rates. The personal RF's saved within-person difference versus the global RF is **−0.0150**, with historical participant-bootstrap interval **[−0.1027, 0.0704]**; it improves for **10/25** eligible people (`J.personal.personal_minus_global_within_roc`; C:352–371). This does not support a demonstrated improvement in moment ranking. That contrast has its own paired interval; other models' marginal intervals are not paired difference intervals.

The personal intercept is a single constant log-odds shift per person. A strictly monotone shift preserves within-person ordering, consistent with the identical historical within-person scores. Improved pooled scores or Brier alone must not be described as improved selection of that person's moments. Check clipping/ties explicitly in the new implementation.

### Fixed-rule and other reusable evidence

The rule is night 00:00–05:59 **or** social-media app **or** session longer than ten minutes (C:600–604). `J.at_alert_rate["Fixed rule"]` records TP=300, FP=1,075, FN=418, TN=3,834: **21.8182% precision**, **41.7827% recall**, **24.4358% flagged**. These are full cleaned-file historical decisions, not results for the 1,705-row personal subset or a future daily policy.

The learned-model same-alert-share comparisons (C:609–624) are descriptive only; see I2 below. The fixed-model five-fold demographics comparison (C:631–645; `J.groupkfold5`) is not nested tuning. Summed individual permutation importances are negative for the interaction block (`J.permutation_importance_by_group["recent interaction"] = -0.008006`; C:663–683). This motivates a predeclared feature-block comparison; it is not an executed block-removal experiment or proof that removing interactions helps.

## 2. Finite issue list and required changes

### I1 — Confirmed indirect calibration dependency

For held-out participant **g**, the base RF predictions `global_oof[g]` come from a fit on everyone except g (C:248–254). However, `personal_regime` fits `a0 = fit_offset(global_oof[others], y[others])` (C:315–318). A peer **h**'s score in that array came from a LOPO model excluding h, which **included g**, including g's later labels. Thus `g labels → peer h's training fit → peer h's OOF score → a0 → g's personal predictions` is an indirect dependency. The personal-history fit does not remove it.

**Consequence:** do not claim participant-isolated calibration for the historical personal-offset result. This defect is in that calibration path; the uncalibrated new-user LOPO base fit itself does exclude g. Its numerical effect has not been measured here.

**Repair/test:** generate calibration scores entirely inside the permitted peer-training universe, excluding g before any upstream fit. Mutating all of g's labels must leave the peer model, peer prior and population calibrator unchanged; mutating g's future labels must leave earlier personal predictions unchanged. Only resolved past labels may affect the personal component.

### I2 — Confirmed use of evaluation-score distributions for cutoffs

C:609 sets `alert` from the fixed rule's share on the evaluated file. C:613 then uses `s >= np.quantile(s, 1 - alert)` over the learned model's evaluation scores. This does not directly use evaluation **labels** to choose the cutoff, but does use evaluation covariates/scores and the evaluation rule share. It is a retrospective matched-alert ranking comparison, not a cutoff fitted before new data arrive. Ties can also prevent an exact target share in another run.

**Repair/test:** freeze an operating target and select the cutoff from training/validation scores only. Save it before outer application and report the actual outer alert share. Adding/removing or changing other evaluation rows must not change the stored cutoff or a given row's decision when its own score is unchanged.

### I3 — Confirmed absence of timing/session guards; day-count wording clarified

C:257–264 sorts by prompt time and slices rows. It does not require completed outcomes, whole days or disjoint sessions. The local deterministic audit confirms **one shared train/test boundary session** and **one training outcome not resolved before the first test prompt** (`lock_time >= first_test_esm_time`). Both measurements are aggregate counts, not new predictive results.

The earlier P/R wording says the split cuts a local day for 34 people without specifying the boundary. V reconciles the definitions:

| Definition of a day | Participants whose adjacent train/test rows share that day |
|---|---:|
| Local midnight (`esm_local` date; also released `date`) | 36/37 |
| Local 04:00 boundary (`date_4am`; independently reconstructed) | 34/37 |
| UTC midnight | 33/37 |

Thus **34 is reproduced for 04:00-adjusted local days; 36 is the midnight calendar-day count**. The unavailable Mac audit's exact definition cannot be inspected. Use the specified definition with every count; do not carry forward “34 calendar-day splits.”

**Repair/test:** freeze timezone/day semantics; use seven calendar days of warmup and whole-day evaluation, require `lock_time < day_cutoff` for historical labels, and purge shared boundary sessions from training. A late lock, same boundary session, equal cutoff timestamp or future-label mutation must not affect earlier fits/predictions.

### I4 — Unresolved feature provenance; anomaly confirmed, leakage unproven

The local audit reproduces `J.data.app_duration_exceeds_elapsed`: **97 rows across 3 people** satisfy `app_total_duration_session > time_since_unlock + 1` (C:546–555). It also reproduces missingness of **703 app categories**, **700 app-duration values** and **127 activity values**. The dictionary does not establish whether each session/today/interaction aggregate ends at the prompt, at lock or later; generic units and short descriptions do not settle this.

**Repair/test:** create a per-input availability/unit/window inventory before selecting main inputs. Prefer explicit pre-prompt timestamp/context and earlier-completed-session features; exclude unresolved app totals/switch counts, cumulative screen time, interactions or sensor windows unless provenance establishes availability. Exclude associated indicators if their source timing is unresolved. Keep the unchanged 49-feature results as historical evidence. Test the schema against outcomes, IDs, demographics and disallowed future-derived fields; do not call this a proof of leakage or silently substitute features in historical tables.

### I5 — Comparison and uncertainty gaps, not evidence of tuning gains

HW4 has fixed settings, no inner hyperparameter search and no new training/validation/outer-test comparison (`make_models`, C:125–163; J schema). Within-person metrics omit single-class people by definition (C:175–189). Personal base-rate shrinkage uses the pooled historical training rate (C:294, 312); the peer/archive availability convention was not a prospective calendar evaluation. Historical group-bootstrap intervals (C:192–225) are useful context but do not supply a paired uncertainty estimate for every proposed refinement.

**Repair/test:** declare nested participant selection, a peer-only prior, matched evaluation rows and separate probability/decision metrics covering single-class people. Compute paired participant-level differences for the declared main comparison. Define undefined AUC, no positives, zero alerts, all-negative training and empty-history behavior without dropping those people from other metrics. Preserve fixed settings for the corrected baseline; separate protocol-repair effects from tuning effects.

### I6 — Historical evidence cannot choose an untouched test or validate a feature subset

The dataset, model families and held-out importance have already been inspected. Calling a newly partitioned subset “untouched external test” would overstate independence. Old importance and the five-fold demographic sensitivity do not establish the effect of feature selection. C's warnings are globally suppressed (line 36), and the score/offset helpers lack a complete empty/one-class contract.

**Repair/test:** call the new analysis retrospective internal validation; freeze the complete selection procedure before inspecting new outer outcomes. Record failed fits/convergence and fixed fallbacks. Make any feature-subset choice inside inner validation. Do not add variants in response to outer results without marking them exploratory.

## 3. Proposed evaluation-contract decisions for Step 3

These are **recommendations to encode in `build/protocol.json` before experiments**, not frozen settings or completed work.

| Contract item | Recommended decision and remaining choice |
|---|---|
| Question and scope | Does a bounded tabular refinement improve participant-balanced AP and probability quality beyond corrected fixed LR/RF? Separately, does a regularized personal offset help beyond peer/global and personal-rate references? Keep binary target; neural models, device export and prompt-policy replay remain optional. |
| Data and inputs | Deduplicate exact rows; reconcile the counts above. Record file/schema/code hashes. Keep identifiers/timestamps only for grouping/audit. Freeze an explicit availability-audited whitelist and missing-value behavior. The final whitelist remains unresolved pending I4; unsupported inputs are excluded, not presumed safe. |
| New-user split | Five deterministic outer participant-grouped folds and three inner participant-grouped folds within each outer training set. Persist private membership manifests, seed and assignment algorithm. No participant crosses a fit/validation boundary; assert sufficient class coverage or use the declared fallback. LOPO figures remain historical. |
| Core candidates | Fixed HW4 LR/RF anchors, plus 8 LR candidates: `C={0.01,0.1,1,10}` × weights `{None,balanced}`; 8 RF candidates: depth `{3,6}` × minimum leaf `{1,5}` × weights `{None,balanced}`, with 100 trees, minimum split 10 and seed 42. Freeze values/order before execution. Boosting and a feature-block ablation are explicit extensions, not automatic extra searches. |
| Selection and ties | Maximize inner participant-balanced AP: each person's validation rows have total weight one. This is one weighted pooled AP, not the mean of per-person APs. Include single-class people in that weighted score; define all-negative validation behavior. Break exact ties by a stored candidate order favoring the simpler declared procedure. |
| Preprocessing and calibration | Fit medians/scalers within each training partition. Compare identity with a sigmoid calibrator only on independent inner validation. To train that calibrator, generate cross-fitted scores inside the current inner-training universe; never fit and independently assess it on the same calibration labels. Refit the selected procedure inside outer training only. A population calibrator for person g never uses g upstream. |
| Operating cutoff | A concrete proposal is a predeclared 25% validation alert target for a decision diagnostic. Fit its quantile only inside outer training/validation, save it, use a specified `>=` tie rule and report actual outer share. This is not the optional three-prompts/day policy. The target and treatment of ties must be frozen explicitly; do not reuse the evaluated file's 24.4358% rule share as a learned operating target. |
| Known-user days | Recommend local **midnight** calendar days, using the released timezone and millisecond UTC timestamps; validate against `esm_local` and `esm_hour`. Warmup is the first seven calendar days, including a partial first day; begin predictions on day eight. Fit/update once before each evaluated day using own outcomes with `lock_time < cutoff`; purge boundary-session overlap. Preserve negative days and report coverage. A 04:00 boundary is a defensible alternative only if selected before running and named consistently. |
| Peer availability | Explicitly choose reference-archive versus common-calendar prospective availability. For the bounded homework, recommend a participant-excluded fixed peer archive and own-person day-forward history, described as retrospective personal adaptation. This does **not** simulate a system trained only on peers observed before each real calendar date. If that stronger prospective claim is wanted, filter peer outcomes by each cutoff too and record coverage/fallbacks. Never mix these interpretations. |
| Known-user components | Fit peer prior/model/calibrator without g; reuse a frozen population procedure. On g's resolved history compare global score, smoothed personal rate `(k+10*peer_prior)/(n+10)`, and regularized personal offset (`tau=1`). Freeze prior smoothing/clipping and minimum-history rules. No history: use population fallback; one-class history: use finite smoothed/regularized behavior rather than fitting an invalid classifier. Offset priors must use permitted peer evidence only. |
| Matching and uncertainty | Use the same declared eligible rows for every method in a comparison and save reasons/counts for exclusions. Report pooled AP/AUC, participant-balanced AP, within-person AUC/AP with eligible counts, Brier/log loss, reliability, confusion counts, precision/recall and actual share flagged. Keep single-class users in probability/decision metrics. Pair participant resamples across methods and recompute differences; do not subtract independently bootstrapped marginal intervals. |
| Evidence and privacy | Save configurations, seeds, fold/day coverage, warnings, runtimes and train/validation/outer diagnostics separately. Private manifests, row predictions and fitted artifacts stay ignored. Add the HW5 `run/` path to `.gitignore` **before** producing such files. Public output is aggregate only. Existing submissions remain unchanged. |

The independent-calibration rule can add fits beyond P's approximate 240 core inner fits. Record the actual budget after specifying calibration and feature comparison; do not present the old rough estimate as a complete computational count. Choose one main refinement-versus-fixed-baseline contrast before outer evaluation, with participant-resampled uncertainty. Negative results are valid outcomes.

## 4. Implementation acceptance tests

The future HW5 implementation must demonstrate these properties with small fixtures before real model runs. They are requirements here, **not tests already implemented or passed**:

1. **Participant isolation:** remove outer test people before preprocessing, feature/hyperparameter selection, peer-prior estimation and every upstream calibration-score fit. Mutating an excluded person's labels/features cannot change another permitted fit used to score them.
2. **Future-label invariance:** changing labels after a participant's day cutoff cannot change any earlier prediction or personal offset. Apply this to indirect peer-calibration dependencies too.
3. **Availability boundary:** outcomes at or after the cutoff are excluded (`lock_time < cutoff` is strict); a session crossing the boundary never appears on both training and evaluation sides. Check timezone conversion, DST, midnight/04:00 distinction and a partial first day.
4. **Training-fitted transformations:** changing evaluation features cannot change fitted medians/scales, selected inputs, parameters, calibration or the cutoff. Permuting unrelated evaluation rows cannot change a fixed row's decision.
5. **Feature contract:** outcomes, identifiers and demographics are absent from classifier inputs; each allowed derived input has a documented pre-prompt window. Missing/extra columns trigger the documented behavior rather than silent column-order changes.
6. **Small/degenerate samples:** empty history, all-negative/all-positive history, no positives in a validation slice, undefined AUC, tied scores and zero alerts yield finite declared outputs and explicit coverage/status. Clipping/log loss and optimizer failures follow recorded rules.
7. **Comparability:** all methods within a contrast use identical row masks/labels; exclusions reconcile from released to unique to eligible to trained/purged/evaluated counts. Group weighting gives each participant total validation weight one.
8. **Calibration/selection independence:** calibrator-fitting labels and its assessment labels are disjoint; all selection ends inside outer training. The stored cutoff is invariant to outer labels and score distributions.
9. **Paired uncertainty and provenance:** bootstrap draws are shared across compared methods; denominators remain explicit. A report table can be regenerated from saved aggregate outputs without private rows in Git.

## 5. Verification performed and exact next handoff

V reads the local CSV without modifying it, reconstructs the old stable 70/30 mask, verifies aggregate counts and audits boundary definitions. It does not import the model runner. Reproduce from the repository root on this PC:

```powershell
python deliverables/05_model_refinement_test_submission/build/verify_baseline.py --csv ../Capstone_Digital_Addiction/data/raw/awaremind/full_data_all_feature.csv
```

The default output is the adjacent `baseline_evidence.json`, containing aggregate evidence only. Run on Python 3.11 with NumPy/pandas. Compare source hashes before reusing this review against a changed HW4 source. The review's Markdown links and rounded historical table values were checked against the local files/J. Model-performance values and historical intervals remain saved results, not fresh reproductions.

**Step 2 is complete:** the historical evidence, confirmed data-flow defects, unresolved provenance and proposed contract are recorded. **Step 3 next:** resolve the input whitelist, local-day boundary, peer-archive interpretation, threshold target, calibration partitions, fallback details, candidate order and main contrast; encode the resulting procedure in `build/protocol.json`. Only then implement the data/split contract and the acceptance tests, followed by corrected baseline runs and predefined refinements. No coursework has been submitted and no one has been contacted.
