# Beyond Ticketing — Current Model State

Last verified: **2026-10-14**

This file is the canonical short-form source of truth for the current forecasting model. Update it whenever a challenger becomes the new historical champion candidate or the training/evaluation dataset changes materially.

## North star

Build the best possible leakage-safe model for final attendance / ticket demand and its evolution toward kickoff.

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
| T-3 | Global v2 proxy-occupancy | **1,835.6** | **1,843.4** |
| T-1 | Global v2 proxy-occupancy | **1,835.5** | **1,804.6** |

Current single lowest holdout MAE: **T-7 verified capacity = 1,799.2 on 2024/25**.  
Current best 2025/26 MAE: **T-1 proxy occupancy = 1,804.6**.

## Current model families

- T-30: Gradient Boosting occupancy-residual model with verified historical stadium capacity;
- T-14: HistGradientBoosting occupancy-residual model with verified historical stadium capacity;
- T-7: Gradient Boosting occupancy-residual model with verified historical stadium capacity;
- T-3: HistGradientBoosting occupancy-residual model using the leakage-safe historical max-attendance capacity proxy;
- T-1: HistGradientBoosting occupancy-residual model using the leakage-safe historical max-attendance capacity proxy.

These are **historical champion candidates**, not automatically promoted production models.

## Predictive feature families that currently matter

Group-permutation evidence on 2025/26 shows useful signal from:

1. timing / seasonality;
2. opponent demand / opponent draw;
3. historical home attendance;
4. sporting state / form / table context;
5. club identity, with smaller incremental importance than the families above.

Verified stadium capacity is now also a first-class predictive data layer. It improved the frozen Global v2 model on development and on both holdout seasons at all five horizons.

## Occupancy modelling

Two capacity contracts have been tested:

1. `capacity_proxy` = maximum eligible historical home attendance observed before the target `as_of_at`;
2. `verified_capacity` = season/venue-specific stadium capacity, including explicit mid-season venue switches.

Verified capacity clearly dominates at T-30, T-14 and T-7. At T-3/T-1 the result versus the existing proxy-occupancy challenger is mixed across the two holdouts, so the proxy contract remains the current best predictive spec there until a combined challenger resolves the inconsistency.

## Current promotion / rejection decisions

- verified capacity: **promote as historical challenger spec at T-30, T-14, T-7**;
- verified capacity: improves Global v2 at T-3/T-1 but does **not** cleanly dominate the current proxy-occupancy winners across both holdouts;
- match-importance/interactions remain useful evidence but are no longer the current winner at T-30/T-14 after the capacity experiment;
- T-7 is now upgraded from original Global v2 to verified-capacity occupancy.

## Next experiments, in order

1. **Verified capacity + match-importance interactions** — one pre-registered combined challenger; do not hand-pick per season.
2. **Live ticketing trajectory** — inventory level, velocity, acceleration, sector movement and release-quality signals on top of the stronger historical baseline.
3. **Probabilistic forecast** — calibrated P10/P50/P90 using quantile loss and empirical coverage.
4. **Weather** — only issuance-time-correct historical weather forecasts; no realized-weather leakage.
5. **Hype** — only after enough point-in-time historical/prospective evidence exists.

## Evaluation rule

Every challenger must use the same point-in-time contract and must not use 2024/25 or 2025/26 to choose its model family or hyperparameters.

A more complex model is not better unless it reduces unseen-match error under the same protocol.

## Evidence files

- `ml/results/BEYOND_GLOBAL_FORECAST_V2_BENCHMARK_2026-10-14.md`
- `ml/results/beyond_global_forecast_v2_benchmark.json`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_1_CHALLENGERS_2026-10-14.md`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_2_VERIFIED_CAPACITY_2026-10-14.md`
- `ml/data/STADIUM_CAPACITY_HISTORY_V1.md`
- `ml/NORTH_STAR.md`
- `ml/CORE_PRODUCT_STATUS.md`
