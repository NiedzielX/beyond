# Beyond ML Benchmark Harness

> **New session / agent:** read [`../AI_BOOTSTRAP.md`](../AI_BOOTSTRAP.md) first. Do not rerun frozen historical benchmarks merely to recover context.
>
> **Current model source of truth:** [`CURRENT_MODEL.md`](./CURRENT_MODEL.md) — current dataset, winner per horizon, MAE, accepted/rejected challengers and current Demand Engine state.
>
> **Core architecture / governance:** [`CORE_PRODUCT_STATUS.md`](./CORE_PRODUCT_STATUS.md) — forecasting-core architecture, evidence gates, canonical ML questions and implementation gaps.

This directory is the evaluation gate for Beyond forecasting models.

## Goal

A challenger is not promoted because it is newer or more complex. It must improve the same no-leakage point-in-time benchmark used by the incumbent and must not degrade the untouched holdout.

## Current global benchmark

The active historical research benchmark is multi-club:

- five Ekstraklasa seasons: 2021/22–2025/26;
- 1,530 matches;
- 7,650 point-in-time feature snapshots;
- horizons: T-30 / T-14 / T-7 / T-3 / T-1;
- development model selection: 2023/24;
- untouched holdouts: 2024/25 and 2025/26.

See:

- [`CURRENT_MODEL.md`](./CURRENT_MODEL.md)
- [`results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md`](./results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md)
- [`LIVE_DEMAND_ENGINE_V1_PLAN.md`](./LIVE_DEMAND_ENGINE_V1_PLAN.md)

## Re-run rule

Do not rebuild the feature store or rerun historical benchmarks to rediscover the current state. Trust persisted results unless a trigger in [`../AI_BOOTSTRAP.md`](../AI_BOOTSTRAP.md) applies.

Typical valid triggers are:

- model implementation/hyperparameter change;
- feature-contract change;
- historical input/hash change;
- source-data correction;
- benchmark-protocol change;
- intentional challenger evaluation;
- explicit reproduction request.

## Historical benchmark v0.1 — retained for lineage

The original benchmark was Lech-only and is retained as model lineage, not as the current research state.

- Club: Lech Poznań.
- Target: final match attendance.
- Development seasons: `2022/2023`, `2023/2024`.
- Untouched holdout seasons: `2024/2025`, `2025/2026`.
- Capacity-constrained attendance rows are excluded.
- Attendance-history features are shifted so only already completed matches are visible.
- Sporting context is pre-match only.
- A model for a test season is trained only on matches before that season starts.
- CatBoost configuration is selected using development MAE only. Holdout results are read only after selection.

### Models in v0.1

1. Rolling-5 attendance baseline.
2. Opponent historical attendance baseline.
3. Existing Beyond historical model: sklearn `GradientBoostingRegressor` (v1.3 early-seasonality feature set).
4. CatBoost challenger.

### v0.1 decision

CatBoost was **not promoted**. On the untouched 32-match holdout it reached MAE `5,918` vs `5,318` for the incumbent and had a much larger negative bias (`-4,867` vs `-2,338`).

That result remains useful historical lineage, but it has been superseded by the five-season Global Forecast / Structural Prior benchmark.

## Promotion criteria

A challenger should not be promoted if it improves one headline percentage while materially worsening MAE/WAPE, bias, stability across seasons/clubs, or uncertainty calibration.

For probabilistic models the gate also includes pinball loss and P10–P90 empirical coverage.

## Data contract

Raw historical datasets are not treated as model outputs. Training and inference must use versioned, point-in-time feature contracts. Benchmark outputs belong in `ml/results/`.
