# Beyond Ticketing — T-7 Robust Estimator v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / a2 STAGE 3 / NO PRODUCTION CHANGE**

Parent evidence:

- `ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`;
- `ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`.

## Why this experiment exists

Stage 1 found a material T-7 MAE lead for `model-hist_absolute_31`.

Stage 2 showed that a constant incumbent/Hist31 blend does not solve the tail problem under development-only MAE selection: development chooses `alpha=1.0`.

Therefore the next question is model-level robustness:

> Can a more strongly regularized robust booster retain a material part of Hist31's MAE advantage while reducing severe event-level regressions before prediction, rather than patching them post hoc?

## Frozen dimensions

This experiment changes only estimator shape / regularization.

Frozen:

- horizon: T-7;
- baseline: `baseline_season`;
- feature mode: current T-7 `base` contract;
- categorical handling: same one-hot pipeline as incumbent/stage 1;
- numeric imputation: same median + missing indicator pipeline;
- target: capacity-normalized residual;
- season weights: uniform;
- random seed: 42;
- development/reference split;
- incumbent benchmark assertions.

## Candidate contract

Ten predeclared challengers are evaluated on 2023/24 development.

### Exact stage-1 lead

`hist31-leaf10-l2-1`

- HistGradientBoostingRegressor;
- loss `absolute_error`;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- min samples leaf 10;
- L2 1.0.

### Stronger structural regularization

Predeclared HistGradientBoosting variants vary only:

- max leaf nodes: 15 or 31;
- min samples leaf: 10 / 20 / 30;
- L2: 1 / 5 / 10.

Exact IDs/configs are persisted in the machine-readable artifact.

### Simpler absolute-error GradientBoosting alternatives

- `gbr-absolute-depth2-leaf8`;
- `gbr-absolute-depth1-leaf12`.

These keep a shallow tree structure and optimize absolute error directly.

## Selection protocol

Development train:

- 2021/22;
- 2022/23.

Candidate selection:

- 2023/24 only;
- primary metric MAE;
- exact tie within `1e-9` -> earlier predeclared candidate order.

The stage-1 Hist31 candidate is declared first. Therefore a numerically identical regularized variant does not replace it on an exact tie.

## Reference protocol

After one candidate is selected on development, only:

- exact incumbent;
- the selected candidate

are scored on:

1. 2024/25, training through 2023/24;
2. 2025/26, training through 2024/25.

Reference holdouts do not select regularization.

Evidence remains:

`EXPOSED_HISTORICAL_REFERENCE_SEASONS`

`promotion_allowed = false`

## Required scorecard

Development for every candidate:

- MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- event improvement rate;
- worst-event degradation;
- declared order and exact hyperparameters.

Selected reference candidate additionally:

- exact worst-event identity;
- mean/p90/max revision versus incumbent;
- worst degradation as share of capacity;
- tail reduction versus stage-1 full Hist31;
- both reference-season MAE deltas.

## Interpretation

Potential signals:

- `STAGE1_HIST31_REMAINS_DEVELOPMENT_WINNER`;
- `REGULARIZED_WINNER_IMPROVES_BOTH_AND_REDUCES_TAIL`;
- `REGULARIZED_WINNER_POSITIVE_MEAN_AND_REDUCES_TAIL`;
- `REGULARIZED_WINNER_POSITIVE_MEAN_TAIL_NOT_SOLVED`;
- `REGULARIZED_WINNER_NOT_PROVEN_ON_REFERENCES`.

No label automatically promotes production.

## Engineering files

Implementation:

`ml/t7_robust_estimator_v1.py`

Tests:

`ml/test_t7_robust_estimator_v1.py`

Workflow:

`.github/workflows/t7-robust-estimator-v1.yml`

Evidence artifact:

`t7-robust-estimator-v1-<run_id>`

A successful run must be persisted under `ml/results/` with exact run/head/artifact hashes before roadmap advancement.
