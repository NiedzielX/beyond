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
- development model selection: **2023/24**;
- untouched holdouts: **2024/25 + 2025/26**;
- one known closed-doors match remains valid historical data but is excluded from demand-model training.

## Current best validated historical specification by horizon

| Horizon | Current best spec | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| T-30 | Global v2 + match-importance/interactions | **2,143.6** | **2,090.8** |
| T-14 | Global v2 + match-importance/interactions | **1,909.5** | **1,969.1** |
| T-7 | Global v2 | **1,936.1** | **1,982.9** |
| T-3 | Global v2 occupancy target | **1,835.6** | **1,843.4** |
| T-1 | Global v2 occupancy target | **1,835.5** | **1,804.6** |

Current strongest point result: **T-1 MAE 1,804.6 on 2025/26**.

## Current model families

- T-30: Gradient Boosting residual model + importance/interactions;
- T-14: HistGradientBoosting residual model + importance/interactions;
- T-7: Gradient Boosting residual model using the original Global v2 feature contract;
- T-3: HistGradientBoosting occupancy-residual model;
- T-1: HistGradientBoosting occupancy-residual model.

These are **historical champion candidates**, not automatically promoted production models.

## Predictive feature families that currently matter

Group-permutation evidence on 2025/26 shows useful signal from:

1. timing / seasonality;
2. opponent demand / opponent draw;
3. historical home attendance;
4. sporting state / form / table context;
5. club identity, with smaller incremental importance than the families above.

The current model therefore appears to learn transferable demand behaviour rather than only memorising club IDs.

## Current occupancy approach

The first occupancy challenger uses a leakage-safe `capacity_proxy` equal to the maximum eligible historical home attendance observed before the target `as_of_at`.

This improved T-14, T-3 and T-1, but it is still only a proxy. The next high-priority experiment is to replace it with verified historical stadium-capacity data and rerun the same benchmark.

## Current promotion / rejection decisions

- match-importance/interactions: **promote as historical challenger spec at T-30, T-14, T-1**;
- match-importance/interactions: **reject at T-7 and T-3** because holdout behaviour was mixed;
- occupancy target: **promote as historical challenger spec at T-14, T-3, T-1**;
- occupancy target: **reject at T-30 and T-7** because it failed the development gate;
- T-7 therefore remains on the original Global v2 contract.

## Next experiments, in order

1. **Verified stadium capacity / occupancy ratio** — replace the max-attendance proxy with real point-in-time capacity history.
2. **Live ticketing trajectory** — inventory level, velocity, acceleration, sector movement and release-quality signals on top of the stronger global baseline.
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
- `ml/NORTH_STAR.md`
- `ml/CORE_PRODUCT_STATUS.md`
