# Beyond Ticketing — T-7 External Model Family v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / a2 STAGE 4 / NO PRODUCTION CHANGE**

Parent evidence:

- `ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`;
- `ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`;
- `ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`.

## Purpose

Stage 3 found the strongest current T-7 MAE challenger:

`hist31-leaf20-l2-1`

Mean reference MAE:

**1,712.38**

Improvement versus production incumbent:

**+77.60 MAE**

Tail remains inconsistent, so before any champion freeze we now test materially different boosting families under the exact same input/modeling contract.

Question:

> Can a different tabular boosting family beat or match the stage-3 HGB challenger on development and deliver a better reference MAE/tail profile without changing features, preprocessing or target definition?

## Frozen dimensions

The following stay fixed:

- horizon: T-7;
- baseline: `baseline_season`;
- feature mode: current T-7 `base` contract;
- categorical encoding: incumbent one-hot encoder;
- numeric preprocessing: median imputation + missing indicators;
- target: capacity-normalized residual;
- season weights: uniform;
- random seed: 42;
- development/reference split;
- incumbent benchmark assertions.

Native categorical handling is intentionally **not** used in this experiment because it would change preprocessing and estimator family simultaneously.

## Runtime versions

Pinned in CI:

- numpy `2.3.5`;
- pandas `2.2.3`;
- scikit-learn `1.8.0`;
- joblib `1.5.3`;
- CatBoost `1.2.10`;
- LightGBM `4.7.0`;
- XGBoost `3.4.1`.

## Candidate contract

Seven candidates total.

### Internal benchmark

`hist31-leaf20-l2-1`

Exact stage-3 winner:

- HistGradientBoostingRegressor;
- absolute-error loss;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- min samples leaf 20;
- L2 1.0.

### CatBoost

Two fixed variants:

- `catboost-mae-depth4-l2-5`;
- `catboost-mae-depth6-l2-5`.

Shared settings:

- loss `MAE`;
- 400 iterations;
- learning rate 0.03;
- L2 leaf regularization 5;
- random strength 0;
- no bootstrap;
- seed 42;
- one thread.

### LightGBM

Two fixed variants:

- `lightgbm-l1-leaves15-l2-5`;
- `lightgbm-l1-leaves31-l2-5`.

Shared settings:

- objective `regression_l1`;
- 400 estimators;
- learning rate 0.03;
- min child samples 20;
- L2 5;
- no row/column subsampling;
- deterministic + force column-wise;
- seed 42;
- one thread.

### XGBoost

Two fixed variants:

- `xgboost-l1-depth2-l2-5`;
- `xgboost-l1-depth3-l2-5`.

Shared settings:

- objective `reg:absoluteerror`;
- eval metric `mae`;
- 400 estimators;
- learning rate 0.03;
- min child weight 5;
- L2 5;
- no row/column subsampling;
- histogram tree method;
- seed 42;
- one thread.

## Selection protocol

Development train:

- 2021/22;
- 2022/23.

Selection season:

- 2023/24.

Primary metric:

- MAE.

Tie rule:

- within `1e-9` MAE choose earlier predeclared candidate order;
- internal stage-3 HGB is declared first, so an exactly tied external model does not replace it.

After one development winner is frozen, only:

- exact production incumbent;
- selected stage-4 candidate

are scored on:

1. 2024/25 with rolling training through 2023/24;
2. 2025/26 with rolling training through 2024/25.

Reference holdouts cannot select family/configuration.

## Scorecard

Development, every candidate:

- MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- improvement rate;
- worst-event degradation;
- exact declared order/family.

Selected candidate on references additionally:

- exact worst event;
- revision magnitude vs incumbent;
- worst degradation as share of capacity;
- comparison against frozen stage-3 MAE and tail per season;
- dependency/runtime versions.

## Interpretation

Potential signals:

- `INTERNAL_STAGE3_HGB_REMAINS_DEVELOPMENT_WINNER`;
- `EXTERNAL_WINNER_BEATS_STAGE3_MAE_AND_TAIL_BOTH_REFERENCES`;
- `EXTERNAL_WINNER_LOWER_MEAN_THAN_STAGE3_TAIL_MIXED`;
- `EXTERNAL_WINNER_IMPROVES_INCUMBENT_BOTH_NOT_STAGE3`;
- `EXTERNAL_WINNER_NOT_PROVEN_ROBUST`.

Regardless of outcome:

`promotion_allowed = false`

Any serious winner must still pass fixed-config broader temporal robustness before an explicit T-7 champion freeze/promotion.

## Engineering files

Implementation:

`ml/t7_external_model_family_v1.py`

Tests:

`ml/test_t7_external_model_family_v1.py`

Workflow:

`.github/workflows/t7-external-model-family-v1.yml`

Evidence artifact:

`t7-external-model-family-v1-<run_id>`
