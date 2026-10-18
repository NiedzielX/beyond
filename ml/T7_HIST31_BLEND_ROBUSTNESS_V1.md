# Beyond Ticketing — T-7 Hist31 Blend Robustness v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / a2 STAGE 2 / NO PRODUCTION CHANGE**

Parent evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

## Question

Stage 1 found a material T-7 lead for `model-hist_absolute_31`:

- development improvement: **+97.36 MAE**;
- 2024/25 improvement: **+105.55 MAE**;
- 2025/26 improvement: **+32.06 MAE**;
- mean reference improvement: **+68.81 MAE**.

But full Hist31 also produced severe single-event regressions:

- 2024/25 worst degradation: **+3,685.74**;
- 2025/26 worst degradation: **+4,233.11**.

This experiment asks:

> Can a fixed blend retain meaningful T-7 MAE improvement while reducing harmful event-level degradation?

## Frozen components

Incumbent:

`structural-prior-runtime-v1-t7-gbr-base`

Stage-1 challenger:

`model-hist_absolute_31`

Hist31 configuration remains exactly:

- same T-7 baseline and features as incumbent;
- HistGradientBoostingRegressor;
- absolute-error loss;
- learning rate 0.04;
- 300 iterations;
- max 31 leaf nodes;
- min samples leaf 10;
- L2 = 1.0;
- seed 42;
- uniform season weights.

No Hist31 hyperparameter changes are allowed in this blend experiment.

Stage-1 result JSON dependency:

`55ea6ee19309771b54e0b0336ecaa2871de19d95d2bf4360400ff76e4c2ddc79`

## Blend contract

For fixed alpha:

`blend(alpha) = (1-alpha) * incumbent + alpha * Hist31`

Predeclared alphas:

- `0.00` — incumbent only;
- `0.25`;
- `0.50`;
- `0.75`;
- `1.00` — full Hist31.

No other alpha may be created after reference holdout results are seen.

## Selection protocol

Development train:

- 2021/22;
- 2022/23.

Selection season:

- 2023/24.

Primary selection metric:

- MAE.

Tie rule:

- candidates within `1e-9` MAE are tied;
- choose lower alpha, i.e. prefer more incumbent on an exact tie.

After alpha is frozen, score unchanged on:

1. 2024/25, training component models through 2023/24;
2. 2025/26, training component models through 2024/25.

Reference holdouts **cannot choose alpha**.

## Required scorecard

For every development alpha:

- MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- MAE improvement vs incumbent;
- event improvement rate;
- worst-event degradation;
- best-event improvement.

For the selected alpha on reference holdouts additionally persist:

- exact worst-event identity;
- actual attendance;
- incumbent prediction;
- selected blend prediction;
- incumbent AE;
- selected AE;
- worst degradation;
- worst degradation as share of capacity;
- mean/p90/max absolute revision vs incumbent;
- full-Hist31 diagnostics from the same refit;
- tail reduction versus frozen stage-1 full-Hist31 worst degradation.

## Interpretation

Possible descriptive outcomes:

- `INCUMBENT_SELECTED_ON_DEVELOPMENT`;
- `FULL_HIST31_SELECTED_NO_BLEND_ROBUSTNESS_GAIN`;
- `BLEND_RETAINS_REFERENCE_UPLIFT_AND_REDUCES_TAIL`;
- `BLEND_POSITIVE_MEAN_AND_REDUCES_TAIL`;
- `BLEND_NOT_PROVEN_ROBUST`.

These are historical research labels, not production promotion states.

Regardless of result:

`promotion_allowed = false`

A successful blend may become a candidate for a later explicit T-7 champion freeze/promotion step. It does not overwrite the current runtime automatically.

## CI/CD

Implementation:

`ml/t7_hist31_blend_robustness_v1.py`

Tests:

`ml/test_t7_hist31_blend_robustness_v1.py`

Workflow:

`.github/workflows/t7-hist31-blend-robustness-v1.yml`

Full evidence artifact:

`t7-hist31-blend-robustness-v1-<run_id>`

Before any roadmap advancement, persist the successful run under `ml/results/` with:

- run ID;
- tested head SHA;
- artifact ID;
- artifact ZIP SHA256;
- result JSON SHA256;
- selected alpha;
- development ranking;
- both reference scorecards;
- exact tail result;
- explicit decision.
