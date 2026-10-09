# Beyond ML Benchmark Harness

This directory is the evaluation gate for Beyond forecasting models.

## Goal

A challenger is not promoted because it is newer or more complex. It must improve the same no-leakage walk-forward benchmark used by the incumbent and must not degrade the untouched holdout.

## Current protocol — benchmark v0.1

- Club: Lech Poznań.
- Target: final match attendance.
- Development seasons: `2022/2023`, `2023/2024`.
- Untouched holdout seasons: `2024/2025`, `2025/2026`.
- Capacity-constrained attendance rows are excluded.
- Attendance-history features are shifted so only already completed matches are visible.
- Sporting context is pre-match only.
- A model for a test season is trained only on matches before that season starts.
- CatBoost configuration is selected using development MAE only. Holdout results are read only after selection.

## Models in v0.1

1. Rolling-5 attendance baseline.
2. Opponent historical attendance baseline.
3. Existing Beyond historical model: sklearn `GradientBoostingRegressor` (v1.3 early-seasonality feature set).
4. CatBoost challenger.

## Promotion criteria

The first gate is the untouched holdout. A challenger should not be promoted if it improves one headline percentage while materially worsening MAE/WAPE or introducing a large directional bias.

For future probabilistic models the gate will also include pinball loss and P10–P90 coverage.

## v0.1 decision

CatBoost is **not promoted**. On the untouched 32-match holdout it reaches MAE `5,918` vs `5,318` for the incumbent and has a much larger negative bias (`-4,867` vs `-2,338`). It does improve the share inside ±10% (`37.5%` vs `31.25%`), but this is not enough to justify replacement.

The next modelling priority is not another generic tabular algorithm. Existing Beyond research already produced a stronger horizon-specific historical baseline (v1.7, T30/T7). The live pipeline should consume that baseline and then measure the incremental value of proprietary ticket-inventory signals: inventory index, velocity, acceleration, sector movement, anomaly filtering and signal readiness.

## Data contract

The historical dataset itself is intentionally not committed here. Run the harness against the approved enriched historical dataset used by the Lech demand studies. Benchmark outputs belong in `ml/results/`.
