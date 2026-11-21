# Frozen evaluation protocol v1

**NudgeWell HW5 — Step 3 — 17 November 2026**

[protocol.json](protocol.json) is the authoritative machine-readable contract. [protocol.sha256](protocol.sha256) seals its bytes. [protocol_preflight.json](protocol_preflight.json) records configuration and data checks, not model-performance or leakage-test results. No HW5 model has been fitted at this checkpoint.

## What this experiment answers

The primary question is whether a bounded LR/RF refinement procedure improves **participant-balanced average precision (AP)** over an inner-selected fixed LR/RF baseline. The secondary question is whether daily personal-offset adaptation improves probability accuracy over a smoothed personal-rate reference. Both are retrospective internal evaluations on a previously explored dataset. Neither tests the benefit of real prompts or establishes an untouched external-test result.

The protocol preserves the binary target `answer <= 5 and remaining_minutes > 5`. It fixes the choices that were left open in [the baseline review](baseline_review.md): inputs, candidate order, splits, calibration, cutoffs, peer availability, daily updates, fallbacks, contrasts and uncertainty. Implementation follows this contract; the old submissions remain unchanged.

## Inputs and the change from HW4

The main corrected baseline uses **15 inputs**: four cyclic clock features, log-transformed elapsed session time, nine current-app genre indicators and one app-context-unavailable indicator. The only alternative pack contains the five time/session inputs. Both packs are fixed in advance; choosing between them is part of inner validation.

| Input block | Construction and evidence | Treatment |
|---|---|---|
| Clock: 4 | Convert millisecond UTC `esm_time` to the row's IANA `timezone`; use integer local hour and Monday-zero weekday to compute two sine/cosine pairs. The conversion agrees with released hour, weekday and local timestamp on all unique rows. | Include; reconstruct rather than trust redundant released encodings. |
| Elapsed session: 1 | `log1p((esm_time-unlock_time)/60000)`. The untransformed duration agrees with `session_minutes` on all 5,627 unique rows to absolute tolerance 1e-6 minutes. | Include; timestamps are available when the prompt occurs. |
| Current-app genre: 9 | Fixed one-hot mapping from `Category_L1`. On 4,924 rows where both names are recorded, `package_name` equals `app_at_prompt`; every recorded category has a recorded app-at-prompt name. Released genre bits agree with the categories on every row. | Include as static metadata of the app open at the prompt. This relies on the released field semantics and local consistency checks, not inspection of the original collector. |
| App context unavailable: 1 | One when the category is missing or outside the fixed category vocabulary; otherwise zero. All genre indicators are zero when unavailable. | Include. The current file has 703 missing categories: 700 also lack the app-at-prompt name, and 3 have an app name without category metadata. Do not equate this flag with missing app name. |
| Session/today app totals, counts/switches, interactions, sensor/activity and previous-session summaries | Their full collection windows or upstream construction are not established by the retained evidence. | Exclude from v1, including indicators derived from excluded sensor fields. No automatic unfreezing when a feature looks promising. |
| Outcomes, demographics, IDs, package names and raw timestamps/timezone | Outcomes define/resolve labels; IDs and timestamps support grouping/audit; demographics can identify people. | Never classifier inputs. Raw timestamps/timezone may only construct the declared features and evaluation boundaries. |

This is a conservative 15-feature refinement scope, not a claim that all 34 removed HW4 inputs leak the outcome. App categorization is assumed to be a static lookup available from the current app; deployment would need its own implementation check. The unchanged historical 49-feature figures remain historical. The corrected fixed baselines and refined procedure use the same eligible rows and declared feature vocabulary. Differences from old LOPO results combine evaluation/input repairs and cannot be attributed to tuning alone.

The existing three-signal rule can be recomputed because current-app genre is retained: local night 00:00–05:59, social app, or elapsed session over ten minutes. It is a fixed decision benchmark. It is not assessed as a calibrated probability forecast.

## New-user selection and final evaluation

Use five outer participant folds. Within each outer training universe, use three participant folds for selection; within an inner training universe, use three further participant folds for calibration-score generation. Assign participants by a deterministic SHA-256 ordering and round-robin placement, with stage-specific namespaces and seed 42. Fold membership uses participant IDs, never outcomes. Save actual memberships only in the ignored run directory.

For each outer fold:

1. Generate raw inner-held-out probabilities for 32 predeclared structural candidates: 8 LR configurations and 8 RF configurations, each with the two input packs. Model preprocessing is fitted inside each base fit. Cache identical fits; do not rerun them under different labels.
2. Select the structural candidate with greatest participant-balanced AP across the assembled inner-held-out predictions. Exact/near ties within 1e-12 use the stored candidate order. The fixed-baseline selector similarly chooses between the unchanged fixed LR and RF settings on the main 15-input pack. Record both fixed anchors as secondary references.
3. For the chosen refined structure, assess identity versus sigmoid calibration on the inner validation folds. Each sigmoid fit uses cross-fitted probabilities generated wholly inside that fold's inner training universe. Its fitting labels do not overlap its assessment fold. Choose sigmoid only if assembled participant-balanced validation Brier improves by more than 1e-6; otherwise choose identity. Inner scores are selection diagnostics, not unbiased final-performance estimates.
4. Fit the final calibrator using the selected structure's cross-fitted probabilities inside the entire outer training universe. Refit the base model on that universe. Apply the frozen procedure once to the outer test people. The fixed anchors and fixed-baseline selector use identity calibration.

The sigmoid is `expit(a*logit(clip(p)) + b)`, with a nonnegative slope. The objective, regularization, parameter bounds and optimizer are fixed in JSON. A failed or one-class calibration fit falls back to identity with a recorded status. A base fit with one class returns its smoothed training prevalence. Unexpected fit failures invalidate that candidate for the outer selection; if no valid candidate remains, stop rather than change the search. Fixed-baseline failures stop the run. Do not suppress convergence warnings globally.

Fitting a calibrator and choosing whether to retain it are separate operations. All selection remains inside outer training. Outer people never enter any upstream fit, prior, calibration-score generation, feature choice or threshold selection. Reusing the old `global_oof[others]` calibration path is prohibited.

## Decisions at a fixed validation cutoff

For each learned procedure, set its cutoff to the unweighted 0.75 quantile of its assembled permitted inner-held-out probabilities, using NumPy `method="higher"`. Use `score >= cutoff`. Fit this cutoff before outer application; the operating target is a predeclared **25% validation alert-share diagnostic**. Ties and distribution changes can produce a different actual share; record it without retuning the cutoff. This is not a hard capacity guarantee or a three-prompts-per-day policy.

The fixed rule uses its literal conditions. The constant population-prior reference is reported for probability metrics, without inventing a capacity-ranked alert policy. Do not choose any cutoff from outer labels, outer scores, the evaluated rule share or later known-user outcomes.

## Known-user daily comparison

Each participant reuses the refined outer-fold population procedure trained without that participant's entire outer fold. This fixed **peer archive** can include other participants' records from later real calendar dates. The claim is retrospective personal adaptation to an available reference archive; it is not prospective common-calendar deployment.

Fix each participant's **evaluation timezone to the timezone at their first chronological prompt**, breaking timestamp ties by original file order. One participant has two recorded timezones; a first-observed reference avoids selecting a day convention from later history or dropping that person. Prediction clock features still use the row's recorded timezone. Evaluation days and cutoffs use the fixed first-observed timezone, so a travel day is not necessarily midnight in the current phone timezone.

Anchor day one at midnight of that participant's first prompt in this reference timezone. The first seven calendar days, including a partial first day, are warmup. On each observed day from day eight onward, make one personal update at reference-zone midnight. History must satisfy both `esm_time < cutoff` and **`lock_time < cutoff`**. The strict lock rule is conservative even for labels that might be logically known earlier. Days follow the reference timezone's calendar/DST boundaries, not fixed 24-hour millisecond increments. Missing required metadata, an unknown timezone or a session with inconsistent unlock/lock timestamps is a data-contract error. Test timezone changes explicitly; they must not silently move the reference clock.

Compare the following on identical rows, without tuning against the evaluated person's later outcomes:

- **Global:** frozen calibrated population score.
- **Personal rate:** `(k + 10*peer_prior)/(n+10)`, using only resolved own history. `peer_prior=(peer_positives+1)/(peer_rows+2)` and excludes the whole outer test fold.
- **Global plus daily personal offset:** add an intercept delta to the population logit, with zero-centered normal prior of standard deviation 1. Fit on resolved own history only; do not refit the peer model. Delta is zero with no history; a failed fit returns zero with a status. Bounds, optimizer and clipping are fixed in JSON.

One-class personal histories still yield a smoothed rate and a finite regularized offset; do not drop them or train an invalid personal classifier. History is cumulative without a sliding window or decay. Any shared session between history and the day's evaluation rows is a contract error; fail that run and investigate the data rather than use future-row knowledge to repair history silently. All methods use the same eligible evaluation rows.

Reuse the global procedure's already frozen cutoff for the personal-rate and offset decision diagnostics. Personalization changes actual alert shares; do not re-match them using future scores. Primary adaptation evidence is probability quality. Report within-person and within-person-day ranking separately, since a daily offset may change between-day ranking even though it preserves ordering within one day, apart from clipping/ties.

## Metrics, comparisons and uncertainty

Participant-balanced pooled AP gives each person total row weight one (`weight_i=1/n_person`). It is not macro-averaged per-person AP. Report ordinary pooled AP/AUC separately, within-person AUC/AP for people with both classes, and the number of people/rows represented. Single-class people stay in Brier, log loss, decision and balanced pooled-AP metrics. An all-negative AP set is recorded as zero with a status; undefined AUC is null. Do not replace undefined AUC with 0.5. Precision with zero alerts is zero with a zero-alert status.

The **primary contrast** is refined selector minus fixed-baseline selector in participant-balanced AP over all outer-held-out predictions. The **prespecified secondary adaptation contrast** is personal-rate minus personal-offset participant-balanced Brier over all eligible day-forward rows; positive values mean improvement. Other tables are descriptive/supporting, without a post-hoc winner claim.

Use 2,000 paired participant bootstrap resamples, seed 20261116, and a 95% percentile interval. Each drawn copy has total weight one; multiplicities must not disappear when a person is sampled twice. Recompute both methods' metrics on the same draws before taking differences. This measures conditional variability of the stored predictions and does not refit the full selection procedure. Report valid/undefined counts and small-sample limits. Never obtain a paired interval by subtracting separate marginal interval endpoints.

Also report probability/decision metrics, ten-bin fixed-width reliability data, row/participant/day coverage and train versus inner-validation versus outer diagnostics. Do not describe an inner-selected result or resubstitution diagnostic as independent test performance. An interval including zero supports uncertainty about improvement; a negative result remains a valid outcome.

## Freeze, outputs and the next step

The protocol includes source/data hashes and pinned numerical-library versions. Every future run records the protocol hash, code hashes, environment and warnings. Private fold memberships, exact timestamps, participant records, row predictions and fitted models go only under ignored `../run/`. Public artifacts contain aggregate results only.

Revalidate without training from the repository root:

```powershell
python deliverables/05_model_refinement_test_submission/build/validate_protocol.py --csv ../Capstone_Digital_Addiction/data/raw/awaremind/full_data_all_feature.csv
```

A sealed protocol cannot be silently rewritten. A necessary change gets a separate version, rationale and hash. If it follows inspection of outer results, label the resulting analysis exploratory; do not replace the original confirmatory procedure or its recorded results.

**Next is Step 4:** implement the data contract, feature construction, fold/day boundaries and the risk-focused acceptance tests declared in JSON. The preflight validates the specification and input consistency. It does not prove the as-yet-unwritten model implementation is leak-free. Run those implementation tests before real model fitting. The absent original assignment template remains a later report-format limitation, not a reason to change these experimental choices after seeing results.
