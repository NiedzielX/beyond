# Beyond Ticketing — Current Model State

Last verified: **2026-10-15**

This file is the canonical short-form source of truth for the current forecasting model. Update it whenever a challenger becomes the new historical champion candidate or the training/evaluation dataset changes materially.

## North star

Build the best possible leakage-safe model for final attendance / ticket demand and its evolution toward kickoff, with explicit priority on **early actionable horizons** where clubs still have time to react.

## Business horizon priority

For product value, T-30 and T-14 are the highest-priority horizons because they preserve enough lead time for pricing, marketing, CRM, media and activation decisions.

T-3/T-1 remain important as accuracy and calibration checkpoints, but they are not the sole optimisation target.

## Current historical dataset

- seasons: **2021/22–2025/26**;
- matches: **1,530**;
- clubs: multi-club Ekstraklasa population across five seasons;
- point-in-time horizons: **T-30 / T-14 / T-7 / T-3 / T-1**;
- feature snapshots: **7,650**;
- verified stadium-capacity coverage: **100%**;
- development model selection: **2023/24**;
- untouched holdouts: **2024/25 + 2025/26**;
- one known closed-doors match remains valid historical data but is excluded from demand-model training.

## Current best validated historical specification by horizon

| Horizon | Current best spec | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| T-30 | Global v2 verified-capacity occupancy | **1,998.7** | **1,994.6** |
| T-14 | Global v2 verified-capacity occupancy | **1,869.8** | **1,960.3** |
| T-7 | Global v2 verified-capacity occupancy | **1,799.2** | **1,848.0** |
| T-3 | Global v2.3 verified-capacity + match-importance | **1,701.4** | **1,686.4** |
| T-1 | Global v2.3 verified-capacity + match-importance | **1,684.3** | **1,682.0** |

Current combined two-season MAE:

- T-3: **~1,693.9**;
- T-1: **~1,683.1**.

Current single lowest holdout MAE: **T-1 = ~1,682.0 on 2025/26**.

## Current model families

- T-30: Gradient Boosting occupancy-residual model with verified historical stadium capacity;
- T-14: HistGradientBoosting occupancy-residual model with verified historical stadium capacity;
- T-7: Gradient Boosting occupancy-residual model with verified historical stadium capacity;
- T-3: HistGradientBoosting occupancy-residual model with verified capacity + match-importance interactions;
- T-1: HistGradientBoosting occupancy-residual model with verified capacity + match-importance interactions.

These are **historical champion candidates**, not automatically promoted production models.

## Predictive feature families that currently matter

Group-permutation evidence on 2025/26 shows useful signal from:

1. timing / seasonality;
2. opponent demand / opponent draw;
3. historical home attendance;
4. sporting state / form / table context;
5. verified stadium capacity / occupancy;
6. club identity, with smaller incremental importance than the families above.

Verified capacity is a first-class predictive data layer. Match-importance interactions add further value close to kickoff, but they are horizon-dependent and fail the development gate at T-30/T-14/T-7.

## Occupancy modelling

Two capacity contracts have been tested:

1. `capacity_proxy` = maximum eligible historical home attendance observed before the target `as_of_at`;
2. `verified_capacity` = season/venue-specific stadium capacity, including explicit mid-season venue switches.

Verified capacity clearly dominates the frozen Global v2 at T-30, T-14 and T-7. The v2.3 capacity + importance combination becomes the current historical champion candidate at T-3 and T-1.

## Current promotion / rejection decisions

- verified capacity: **promote as historical challenger spec at T-30, T-14, T-7**;
- verified capacity + match-importance: **promote at T-3 and T-1**;
- verified capacity + match-importance: **reject at T-30, T-14 and T-7 because it fails the development gate**;
- horizon-specific contracts remain the preferred approach.

## Ticketing trajectory readiness

Canonical readiness view: `private.ticketing_horizon_checkpoint_readiness_v1`.

Current evidence coverage across 23 tracked events:

| Horizon | Ready events | Completed ready events |
|---|---:|---:|
| T-30 | **1** | **0** |
| T-14 | **7** | **3** |
| T-7 | 9 | 3 |
| T-3 | 11 | 5 |
| T-1 | 10 | 9 |

Important consequence:

- **T-14 retrospective raw trajectory exists, but only 3 completed events currently have a usable checkpoint + outcome. This is not enough to train a credible T-14 ticketing challenger.**
- **T-30 currently has no completed outcome at the required checkpoint.**

Therefore T-30/T-14 ticketing work is currently a **prospective evidence collection programme**, not a model-promotion exercise.

## Next experiments, in order

1. **T-30 / T-14 live ticketing trajectory collection** — inventory level, velocity, acceleration, sector movement, scarcity and release-quality signals. Do not train/promote until sufficient completed evidence exists.
2. **T-30 / T-14 historical-model optimisation** — continue feature engineering only under the same season-blocked dev/holdout protocol. Target: T-30 below ~1.7k, then ~1.5k.
3. **Probabilistic forecast** — calibrated P10/P50/P90 using quantile loss and empirical coverage.
4. **Weather** — only issuance-time-correct historical weather forecasts; no realized-weather leakage.
5. **Hype** — only after enough point-in-time historical/prospective evidence exists.

## Evaluation rule

Every challenger must use the same point-in-time contract and must not use 2024/25 or 2025/26 to choose its model family or hyperparameters.

A more complex model is not better unless it reduces unseen-match error under the same protocol.

For live ticketing trajectory, no inference should be made from tiny event samples simply because the signal looks intuitive.

## Evidence files

- `ml/results/BEYOND_GLOBAL_FORECAST_V2_BENCHMARK_2026-10-14.md`
- `ml/results/beyond_global_forecast_v2_benchmark.json`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_1_CHALLENGERS_2026-10-14.md`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_2_VERIFIED_CAPACITY_2026-10-14.md`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_3_CAPACITY_IMPORTANCE_COMBO_2026-10-15.md`
- `ml/data/STADIUM_CAPACITY_HISTORY_V1.md`
- `ml/NORTH_STAR.md`
- `ml/CORE_PRODUCT_STATUS.md`
