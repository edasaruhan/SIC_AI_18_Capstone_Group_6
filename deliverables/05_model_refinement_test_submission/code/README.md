# HW5 data and split contract — Step 4

**Implemented and checked on 17 November 2026.** The frozen protocol remains [v1.0.0](../build/protocol.json), SHA-256 `566f08be28187c6c3ddfc7683eae43d1d9fac7caa0f63821fc71a843bb4a7d06`.

## Run the checks

From the repository root, using the pinned Python 3.11 environment:

```powershell
python deliverables/05_model_refinement_test_submission/code/check_data_contract.py --csv ../Capstone_Digital_Addiction/data/raw/awaremind/full_data_all_feature.csv
```

For synthetic tests alone:

```powershell
python -m unittest discover -s deliverables/05_model_refinement_test_submission/tests -v
```

The combined command first runs the tests, then validates the source/data hashes, constructs the real-data features and boundaries, and reconciles coverage. It does not fit a model on the released data or create performance estimates. The tests include a tiny synthetic sklearn LR fit and synthetic estimator/calibration fixtures.

## Interfaces for the next runner

The implementation is a normal Python package under `code/nudgewell_hw5/`; the command's directory supplies the import path.

| Module | Responsibility |
|---|---|
| [data_contract.py](nudgewell_hw5/data_contract.py) | Verify frozen protocol/source/environment fingerprints; validate and deduplicate the released CSV; derive the 5/15 feature packs; enforce exact classifier columns; guard private output paths. |
| [splits.py](nudgewell_hw5/splits.py) | Deterministic participant folds, parent exclusions, fit scopes, reference-timezone calendar days and strictly resolved own history. |
| [evaluation_contract.py](nudgewell_hw5/evaluation_contract.py) | Scoped preprocessing/base fits, cross-fit dependency records, permitted calibration, immutable cutoffs, daily personal state, matched prediction arrays and small metric/weighting helpers. |
| [test_contract.py](../tests/test_contract.py) | Adversarial small fixtures, mutation tests and boundary/error cases. |
| [check_data_contract.py](check_data_contract.py) | Test gate, data-only integration check, aggregate evidence and private memberships. |

`load_protocol()` requires the exact sealed v1 bytes, its retained sources and numerical versions. `load_dataset(csv, protocol)` additionally verifies the raw file and dictionaries. `fixture_dataset()` is explicitly for synthetic tests and bypasses only the released-file hash/size checks; it still enforces schema, labels and timestamp/category consistency. The real runner must use `load_dataset()`.

`Dataset.features(rows, pack)` reconstructs only the frozen inputs. It never reads outcomes or locks. The inference feature builder works without target/participant columns. Unknown inference categories become zero genre indicators plus `app_context_missing=1`; unknown categories in the fixed training release stop loading. Classifier matrices with extra, reordered or missing columns are rejected.

`outer_splits(data)`, `inner_splits(data, outer)` and `calibration_splits(data, outer, inner)` preserve every parent exclusion. Each split supplies a `FitScope`. `fit_base()` checks that scope before fitting its imputer, optional scaler and supplied estimator. The future candidate factory must construct estimators from the frozen candidate list; this module does not choose candidates.

For each inner fold, generate calibration-fitting scores with `cross_fit()` on **that inner training universe** and its calibration folds. Fit the map with `fit_calibration(..., assessment_rows=inner.test)`. Obtain validation predictions with `heldout_scores()` and apply the map with `apply_calibration()`. Combine disjoint folds with `combine_scores()` before `fit_cutoff()`. Every score block retains upstream fitting rows. Filtering an old whole-population OOF array down to peers therefore does not erase the evaluated participant's influence: the guard rejects it. A fitted calibration's identity fallback retains its dependency record too.

`identity_map(scope)` is the separate predeclared identity option, with no data-dependent calibration fit. It must not be substituted for a failed fitted map merely to erase that map's provenance. Later selection/fallback orchestration must follow the protocol and keep its trace.

`PopulationPredictor` binds the model/map to the excluded-fold archive. `day_splits()` fixes each participant's first-observed timezone, uses seven calendar warmup days, and keeps current-row timezones only for predictor clocks. Own history requires both prompt and lock strictly before the day cutoff. Shared boundary sessions and malformed/dropped evaluation masks stop the run. `fit_personal_state()` reads only the scoped peer archive and resolved own history; `predict_personal_day()` returns all three variants on identical rows.

`FittedCutoff.flags()` only applies its stored value. It cannot refit a quantile from evaluation scores. `participant_weights()` preserves bootstrap multiplicities, and `MatchedPredictions.validate()` rejects differing rows/methods. The small `metric_summary()` helper's `AP` is participant-balanced pooled AP. Complete metric/paired-bootstrap orchestration was subsequently implemented and integration-tested in [Step 5](EXPERIMENTS.md); real-data evaluation and figures remain Step 6 work.

These checks are program invariants and provenance records for the intended runner, not a security sandbox against callers deliberately forging objects or mutating private attributes. The integrated selector still needs its own data-flow tests before a full experiment.

## Verification and evidence

[step4_validation.json](../build/step4_validation.json) records **35 passing synthetic tests**, code/test hashes and the local data-only check:

- Released 5,772 rows minus 145 exact duplicates = **5,627 unique rows**. No feature-based row deletion; all 703 missing categories have explicit encodings.
- **5 outer, 15 inner and 45 calibration splits** preserve participant boundaries.
- **1,855 warmup rows + 3,772 daily evaluation rows = 5,627**. Evaluation covers **37 people and 423 observed participant-days**, exactly matching the frozen preflight.
- One prior row/day outcome is unresolved at its cutoff and excluded from history. Strict equality, later locks and crossing sessions are separately challenged in fixtures.
- Tests reject the old indirect `global_oof[others]` path and self-assessed calibration, prove future-label invariance with a past-label negative control, and challenge training-only medians/scales, one-class/empty histories, optimizer failures, convergence retries, zero alerts, DST and timezone changes.

Private row/fold/day memberships and hashes are written to `../run/step4/split_manifest.json`, inside the ignored run directory. Public evidence contains only aggregate geometry/counts and source hashes. No raw rows, participant identifiers, package names, exact timestamps or fitted artifacts are copied into public output.

The frozen Step 3 preflight remains a historical snapshot saying implementation was pending then. This Step 4 evidence is separate; the protocol, seal and retained baseline sources were not rewritten.

**Subsequent checkpoint:** [Step 5 is implemented and its validation-side search is complete](EXPERIMENTS.md), following 51 passing unit/integration tests. That suite includes the Step 4 tests and fixes a nondeterministic past-label negative control by flipping the permitted labels instead of setting a value that could already be present. The original 35-test evidence remains a dated snapshot; the current gate records current code hashes. Next is Step 6's frozen outer/day-forward evaluation.
