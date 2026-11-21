# Bounded selector and experiment runner — Step 5

The runner uses the unchanged [frozen v1 protocol](../build/protocol.json). Its default `select` phase fits and selects procedures using outer-training participants only. The separate `evaluate` phase is Step 6; it applies all five saved procedures to their outer test people and runs the prescribed daily personal comparison.

## Completed checkpoint — 17 November 2026

[All 51 synthetic tests passed](../build/step5_validation.json) before the released-data search started. Run `hw5-v1-step5-20261117` completed all five selections: **160 structural-candidate evaluations, 540 base-fit jobs, zero failed jobs and zero constant fallbacks**. [The aggregate selection trace](../build/results/hw5-v1-step5-20261117_selection.json) retains every candidate; [the run review](../build/step5_run_review.json) checks fingerprints, five checkpoints and the unopened outer-evaluation boundary.

All five selected the time/session feature pack. Folds 1, 4 and 5 selected LR with C=10/balanced weights; fold 2 selected RF with depth 3/minimum leaf 1/balanced weights; fold 3 selected LR with C=0.1/balanced weights. Sigmoid calibration was retained in every fold. These are **inner-selected choices, not evidence of a held-out gain**. The retained sklearn `penalty` argument emitted its pinned-version deprecation warning; warnings were recorded, and no fit failed or needed a convergence retry.

Five fitted selection checkpoints are stored under the ignored `run/hw5-v1-step5-20261117/` directory. Step 6 applied those five procedures and completed the daily comparison. [Evaluation review and verification](../build/evaluation_review.md)

## Commands

From the repository root with the pinned Python 3.11 environment:

```powershell
python deliverables/05_model_refinement_test_submission/code/run_refinement.py --csv ../Capstone_Digital_Addiction/data/raw/awaremind/full_data_all_feature.csv --run-id hw5-v1-step5-20261117 --phase select
```

Every invocation runs the synthetic unit/integration gate before released-data fitting. Use `--tests-only` with the same required arguments to run only the gate. There is no command-line switch to shorten the frozen search, replace estimators or skip tests.

An interrupted selection with unchanged code, protocol, dataset and environment can resume by adding `--resume`. Completed outer folds are loaded only after their artifact fingerprints are checked. Reusing a completed run ID validates the saved outputs and returns them without refitting. Changed source or artifacts require investigation; the runner never silently overwrites an unrelated checkpoint. A lock prevents concurrent writers for one run ID.

When Step 6 is requested, the evaluation command uses the same run ID with `--phase evaluate`. It is blocked until all five selections are complete and unchanged. All artifacts are verified before any outer predictions are created. The frozen procedure does not add candidates or retune decisions after evaluation.

## Selection implementation

| Module | Responsibility |
|---|---|
| [models.py](nudgewell_hw5/models.py) | Construct only the 16 declared LR/RF configurations crossed with the two declared feature packs; cache exact fitting scopes and record attempts/warnings/failures. |
| [selector.py](nudgewell_hw5/selector.py) | Execute the 32-structure inner search, fixed-anchor comparison, nested calibration decision, validation-fixed cutoffs and final outer-training refits. It does not predict outer rows or read outer labels. |
| [metrics.py](nudgewell_hw5/metrics.py) | Separate pooled and participant-balanced metrics, probability/decision metrics, reliability bins, coverage and the two prespecified paired participant contrasts. |
| [runner.py](nudgewell_hw5/runner.py) | Enforce the test gate, checkpoint each outer procedure privately, validate source/data/environment fingerprints, and keep selection/evaluation phases distinct. |
| [run_refinement.py](run_refinement.py) | Command-line entry point with progress and aggregate gate evidence. |
| [test_integration.py](../tests/test_integration.py) | Full synthetic selection/evaluation round trip, actual LR/RF-grid fold and mutation/failure/resume/tamper cases. |

Within each outer training universe, selection evaluates exactly 32 structures on the three inner participant folds. Participant-balanced pooled AP chooses the structure using the protocol's stored order for ties. The fixed-baseline selector compares only the fixed LR/RF anchors on 15 inputs, favoring LR in a tie. Candidate failures are recorded; a fixed-anchor failure stops the run. An unexpected failure while generating the selected candidate's calibration scores also stops the run rather than introducing a new procedure.

Identity versus sigmoid calibration is assessed on inner validation people. Every sigmoid fit receives scores generated entirely inside that inner training universe. If any inner map fails or is inapplicable, sigmoid is ineligible. Otherwise it is retained only when the Brier gain exceeds the frozen tolerance. A failed final sigmoid fit restores both identity application and the raw inner-validation cutoff. Cutoffs always come from permitted assembled inner-held-out scores, never outer scores or labels.

The cache is scoped to one dataset and outer selector. Its key contains actual fitting rows, permitted rows, exclusions and the exact candidate. Failed fits are cached without retaining exception tracebacks. Base-fit jobs, actual estimator attempts, retries, fallback jobs, cache hits, warning categories and runtimes are recorded. No second process writes experiment results for the same run.

Training diagnostics are explicitly optimistic. Inner scores are selection diagnostics and cannot establish an improvement on new people. Only the Step 6 outer evaluation can estimate the performance of the full selected procedure. The old 49-feature LOPO metrics are historical context and are not interchangeable with these corrected 5/15-feature nested results.

## Output locations and privacy

- `build/step5_validation.json`: test IDs, pass count, protocol fingerprint and tested code hashes.
- `build/results/<run-id>_selection.json`: aggregate inner/training diagnostics, all declared candidate results, selected configurations, calibration statuses and fit counts.
- `run/<run-id>/`: ignored, private protocol snapshot, Git/environment/code state, test gate, row/fold memberships, selected fitted models, candidate score vectors and checkpoint hashes.
- `build/results/<run-id>_evaluation.json`: created only by Step 6; aggregate final metrics and paired uncertainty.
- `run/<run-id>/predictions_*.csv` and personal-state records: created only by Step 6 and kept private.

Fitted coefficients, trees, calibration parameters, row-level scores, participant IDs and exact timestamps are not serialized into the public selection summary. Checkpoints use locally produced joblib files; fingerprints are verified before loading. These are intended-workflow integrity checks, not a security boundary against deliberate forgery of both artifacts and their manifests.

The evaluation implementation reports both pooled and participant-balanced AP/Brier/log loss, within-person coverage, decisions and ten fixed reliability bins. Its public curve data use fixed score grids rather than individual prediction thresholds. Paired bootstrap samples preserve participant multiplicity and use the same draws for both methods, with 2,000 replicates and the frozen seed. Tiny synthetic round-trip tests exercise those paths before any real outer evaluation.

## Review boundary

The integrated tests cover candidate-grid fidelity, exact tie behavior, outer-label/feature invariance, no outer prediction during selection, calibration failures, one-class data, fixed-anchor failures, cached failure/retry accounting, safe resumption, stale gates, tampered artifacts, hand-calculated metric estimands and private/public output separation.

The Step 4 evidence remains a dated snapshot of its earlier source hashes. [The data/split guide](README.md) and the new Step 5 gate together describe the current implementation. Source changes after a gate invalidate that gate. If a correctness issue is found after outer results are opened, preserve result lineage and follow the protocol's amendment/exploratory rules; do not silently rerun a changed search and report it as the original frozen evaluation.
