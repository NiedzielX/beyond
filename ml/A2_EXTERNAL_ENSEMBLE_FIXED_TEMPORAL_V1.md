# a2 External/Ensemble Fixed-Temporal Robustness Audit v1

Last updated: **2026-10-21**

Status: **ACTIVE FIXED-CONFIG ROBUSTNESS AUDIT**

Parent result:

`ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`

## Objective

Replay the exact T-30/T-7/T-1 ensemble contracts selected by the all-horizon closure audit through a stronger rolling temporal audit.

There is **no tuning or selection in this audit**.

## Exact frozen contracts

### T-30

Members / weights:

- current a2 base `0.75`;
- HGB hist31 `0.00`;
- CatBoost depth6 `0.00`;
- LightGBM leaves15 `0.00`;
- XGBoost depth3 `0.25`.

### T-7

Members / weights:

- current a2 / HGB hist31 `0.25`;
- CatBoost depth4 `0.25`;
- LightGBM leaves15 `0.50`;
- XGBoost depth3 `0.00`.

### T-1

Members / weights:

- current a2 base `0.00`;
- HGB hist31 `0.25`;
- CatBoost depth4 `0.50`;
- LightGBM leaves15 `0.25`;
- XGBoost depth3 `0.00`.

Changing a member, weight, feature contract, baseline, target or hyperparameter creates a new challenger and is not permitted in this audit.

## Rolling folds

1. train `2021/22` -> test `2022/23` — additional pre-selection historical fold;
2. train `2021/22 + 2022/23` -> test `2023/24` — original development selection season;
3. train through `2023/24` -> test `2024/25` — exposed reference;
4. train through `2024/25` -> test `2025/26` — exposed reference.

The exact closure-run MAEs for folds 2-4 are hard reproduction gates at tolerance `1e-9`.

## Metrics

Per fold:

- current a2 MAE;
- fixed ensemble MAE;
- MAE improvement;
- median AE / p90 AE / bias;
- event improvement rate;
- worst-event degradation;
- paired bootstrap probability and 95% interval;
- harmful-regression counts above 500/1000/2000/3000 seats;
- revision magnitude;
- club-season consistency for cells with at least 10 events.

## Decision gate

A horizon passes this audit only if the **exact frozen candidate has positive MAE improvement in all four rolling folds**.

Possible decisions:

- `ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`;
- `ROBUSTNESS_REJECT_NOT_ALL_ROLLING_FOLDS_POSITIVE`.

This is deliberately stricter than the closure audit. The purpose is to reject small or unstable gains before they can become a new historical candidate.

A pass still does **not** mutate Frozen Pre-Live v2. It only qualifies that horizon for a separately versioned next historical / Pre-Live challenger cycle.

## Production boundary

Always:

- Frozen Pre-Live v2 unchanged;
- b2 unchanged;
- c2 unchanged;
- frozen Ridge/P2 unchanged;
- `production_change = false`;
- production `live_adjustment = 0`.

## Interpretation

> **The closure audit selected the contracts. This audit only asks whether those exact contracts are temporally robust.**
