# Beyond Ticketing — Pre-Live Baseline Optimization v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / a2 STAGE 1 / NO PRODUCTION CHANGE**

Canonical parent instruction:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

## Purpose

This is the first implementation step of:

**a2 — Historical / Structural Prior optimization**

The goal is to test whether the current Structural Prior can be improved before b2/c2 and before freezing Pre-Live Model v2.

This harness deliberately evaluates **one change at a time** so a result has a clear causal interpretation.

It does not automatically combine winning ideas, retune production or promote a model.

## Frozen incumbent

The incumbent remains the current per-horizon Structural Prior runtime:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

Input artifact:

`ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz`

Manifest:

`ml/artifacts/structural_prior_runtime_v1/manifest.json`

The experiment checks the input SHA256 against the manifest before fitting anything.

## Evaluation protocol

### Development selection

Train:

- 2021/22;
- 2022/23.

Select candidate on:

- 2023/24.

Selection metric:

- MAE.

No 2024/25 or 2025/26 result is allowed to choose the stage-1 candidate.

### Explicit tie handling

If multiple candidates have development MAE equal within `1e-9`, select the earliest candidate in the predeclared order:

1. incumbent;
2. feature-group ablations in declared order;
3. recency challengers in declared order;
4. model-family challengers in declared order.

This avoids arbitrary lexical tie-breaking and prefers the incumbent when it is statistically/numerically indistinguishable from a challenger.

The artifact stores:

- `development_best_mae`;
- `development_tie_ids`;
- exact tie-break rule.

### Rolling reference holdouts

After the candidate is selected on 2023/24, evaluate unchanged:

1. 2024/25, training through 2023/24;
2. 2025/26, training through 2024/25.

Only two models are scored on each reference holdout:

- exact incumbent;
- the candidate selected on 2023/24 development.

If the incumbent wins development, only the incumbent is needed.

This is deliberate. The reference holdouts are **not** a secondary tournament and must not be used to rescue a challenger that lost development selection.

These seasons are already exposed historical reference evidence. They are not fresh untouched validation and cannot automatically promote anything.

## Incumbent integrity gate

Before any challenger comparison, the harness fits the exact incumbent and asserts the known frozen reference MAE for every holdout.

For T-7/T-3/T-1 it also asserts the known 2023/24 development MAE.

If the incumbent does not reproduce, the workflow fails rather than comparing against a different baseline silently.

## Candidate families

### 1. Incumbent

Exact current runtime.

### 2. Feature-group ablation

Drop exactly one numeric feature group while preserving:

- the same baseline formula;
- the same incumbent estimator;
- the same training seasons;
- uniform sample weights.

Groups:

- `calendar_timing`;
- `home_history`;
- `current_season`;
- `opponent_demand`;
- `pair_history`;
- `sporting_form`;
- `table_context`;
- `rest_congestion`;
- `capacity`.

The direct baseline column used by a horizon is protected from stage-1 ablation because removing it would change the baseline formulation rather than only feature contribution.

The resolved exact columns are written to the JSON artifact per horizon.

### Feature completeness gate

The declared feature groups cover the full current 80-column numeric contract before horizon-specific `base/full` filtering.

At runtime, if a numeric model feature exists that is neither:

- assigned to a declared group; nor
- the protected direct baseline column,

the experiment fails.

This is intentional: new features cannot be silently omitted from the contribution audit.

### 3. Recency weighting

Keep the exact incumbent features/model and change only sample weights by training season.

Policies:

- `uniform` — incumbent;
- `linear_075` — linear weights from 0.75 for the oldest training season to 1.0 for the newest;
- `exp_050` — weight `0.50 ^ season_distance`.

`exp_075` is intentionally excluded from v1 because with the two-season development training window it resolves to exactly the same weights as `linear_075` (`0.75`, `1.0`). Two candidates that are not identifiable during selection must not be allowed to diverge only later when additional holdout-training seasons exist.

The exact resolved season weights are persisted for every fit.

### 4. Model-family challengers

Keep the incumbent baseline, feature mode and uniform weights; change only estimator policy.

Stage-1 challengers:

- `rf_absolute_leaf3`
  - RandomForestRegressor;
  - 300 trees;
  - `criterion=absolute_error`;
  - `min_samples_leaf=3`;
  - `max_features=0.8`;
  - seed 42.
- `extra_leaf5`
  - ExtraTreesRegressor;
  - 500 trees;
  - `min_samples_leaf=5`;
  - `max_features=0.8`;
  - seed 42.
- `hist_absolute_31`
  - HistGradientBoostingRegressor;
  - `loss=absolute_error`;
  - learning rate 0.04;
  - 300 iterations;
  - max 31 leaf nodes;
  - min 10 samples per leaf;
  - L2 = 1.0;
  - seed 42.

This first harness intentionally uses pinned scikit-learn-only challengers so the experiment can establish a clean comparison framework before optional CatBoost/LightGBM/XGBoost expansion.

## Target

Like the incumbent, candidates learn a capacity-normalized residual around the horizon-specific baseline:

`target_residual = attendance / capacity - baseline / capacity`

Prediction:

`prediction = clip(baseline + predicted_residual * capacity, 0, capacity)`

## Required scorecard

Every development candidate stores:

- n;
- MAE;
- median absolute error;
- bias;
- WAPE;
- p90 absolute error;
- MAE improvement versus incumbent;
- worst single-event degradation versus incumbent;
- best single-event improvement;
- event improvement rate;
- event equal rate;
- home-club MAE breakdown where `n >= 5`;
- training rows;
- numeric feature count;
- exact season sample weights.

For the development-selected candidate on each holdout, persist additionally the exact worst/best event identity and values:

- `match_key`;
- home club;
- away club;
- actual attendance;
- candidate prediction;
- incumbent prediction;
- candidate absolute error;
- incumbent absolute error;
- degradation/improvement versus incumbent.

This prevents a lower average MAE from hiding a severe single-event regression.

## Candidate interpretation

Per horizon:

- `INCUMBENT_SELECTED_ON_DEVELOPMENT` — development does not justify changing the incumbent;
- `POSITIVE_BOTH_REFERENCE_HOLDOUTS` — the development-selected candidate improves both exposed reference holdouts and mean holdout MAE;
- `POSITIVE_MEAN_MIXED_REFERENCE_HOLDOUTS` — positive mean holdout result but not both seasons;
- `NOT_PROVEN_ON_REFERENCE_HOLDOUTS` — selected challenger fails to improve mean reference holdout MAE.

These labels describe historical evidence. They are deliberately **not named as promotion decisions**.

Regardless of label:

`promotion_allowed = false`

Stage 1 is research/challenger evidence only.

## Important interpretation rule

An ablation winner means a feature group may be noisy under the current model/protocol. It does not mean the underlying information is useless forever.

A recency winner means the current historical evidence benefits from that weighting under this protocol. It does not justify tuning decay against the exposed holdouts.

A model-family winner means the estimator is promising under the exact frozen feature/baseline contract. It does not justify immediate production promotion.

A lower mean MAE is not sufficient by itself if tail degradation becomes unacceptable. Tail behavior must be diagnosed before any champion freeze.

## Files

Implementation:

`ml/pre_live_baseline_optimization_v1.py`

Unit checks:

`ml/test_pre_live_baseline_optimization_v1.py`

CI:

`.github/workflows/pre-live-baseline-optimization-v1.yml`

Result artifact:

`pre-live-baseline-optimization-v1-<run_id>`

The final CI result must be persisted under `ml/results/` with run ID, artifact ID/hash, JSON hash, exact per-horizon result and decision before the roadmap advances.
