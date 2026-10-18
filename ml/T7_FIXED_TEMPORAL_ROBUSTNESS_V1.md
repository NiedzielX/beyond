# Beyond Ticketing — T-7 Fixed Temporal Robustness v1

Last updated: **2026-10-18**

Status: **ACTIVE AUDIT / FIXED CONFIG / NO TUNING / NO PRODUCTION CHANGE**

## Purpose

Audit the strongest current T-7 challenger:

`hist31-leaf20-l2-1`

without changing its hyperparameters, features, baseline or preprocessing.

This follows:

- Stage 3 robust estimator result;
- Stage 4 external model-family tournament, where CatBoost/LightGBM/XGBoost did not beat the Stage-3 HGB development winner.

The question is no longer "which model wins?".

The question is:

> **Does the fixed T-7 challenger remain directionally useful across rolling seasons, clubs and tail diagnostics strongly enough to justify freezing it as the historical T-7 candidate for Pre-Live v2?**

## Fixed candidate

`hist31-leaf20-l2-1`

Exact settings:

- HistGradientBoostingRegressor;
- absolute-error loss;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- min samples leaf 20;
- L2 1.0;
- seed 42;
- current T-7 base feature mode;
- `baseline_season`;
- capacity-normalized residual target;
- same incumbent preprocessing.

No parameter is selected in this audit.

## Rolling folds

1. train 2021/22 -> score 2022/23;
2. train 2021/22–2022/23 -> score 2023/24;
3. train through 2023/24 -> score 2024/25;
4. train through 2024/25 -> score 2025/26.

Evidence labels are explicit:

- 2022/23 = additional pre-selection historical fold;
- 2023/24 = development selection season from Stage 3;
- 2024/25 and 2025/26 = already exposed reference seasons.

This audit does not create a new untouched validation set.

## Exact reproduction gates

The fixed challenger must reproduce canonical Stage-3 MAE with `atol=1e-9`:

- 2023/24: `2317.3395349341495`;
- 2024/25: `1650.9668467458935`;
- 2025/26: `1773.7952605857984`.

Any mismatch fails CI.

## Diagnostics

Per fold report:

- incumbent and challenger MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- event improvement rate;
- exact best/worst event;
- revision magnitude versus incumbent;
- degradation quantiles p50/p75/p90/p95/p99/max;
- rates of harmful degradation >500 / >1000 / >2000 / >3000 seats;
- home-club MAE consistency for clubs with >=10 events;
- paired event-level bootstrap of MAE improvement.

Bootstrap:

- 10,000 paired samples per fold;
- deterministic seed;
- same event index used for incumbent and candidate AE;
- report 95% percentile interval and probability that mean improvement >0.

Bootstrap is diagnostic historical uncertainty only. It does not turn exposed data into fresh validation.

## Outcome rule

No automatic promotion gate is encoded.

The audit must be interpreted from:

- number of rolling folds with positive MAE improvement;
- minimum/mean fold improvement;
- paired uncertainty;
- club-season consistency;
- large harmful regression frequency;
- worst-event degradation.

`promotion_allowed = false`

Production T-7 stays unchanged until an explicit later freeze/promotion decision.

## Files

Implementation:

`ml/t7_fixed_temporal_robustness_v1.py`

Tests:

`ml/test_t7_fixed_temporal_robustness_v1.py`

Workflow:

`.github/workflows/t7-fixed-temporal-robustness-v1.yml`
