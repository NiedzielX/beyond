# Structural Prior Runtime v1 — early-horizon benchmark

Status: **historical champion candidate / runtime recovery**  
Date: **2026-10-15**

## Protocol

Selection uses **2023/24 only** after training on 2021/22–2022/23. 2024/25 and 2025/26 are untouched holdouts.

The feature layer is rebuilt point-in-time from the validated five-season canonical inputs:

- 1,530 matches;
- 7,650 horizon snapshots;
- T-30 / T-14 / T-7 / T-3 / T-1;
- attendance history may carry across seasons;
- sporting state resets every season;
- a match enters historical state only after `kickoff + 3h`;
- the known closed-door zero-attendance match is retained as historical truth but excluded from demand training;
- verified historical stadium capacity is available for every target.

Target architecture:

`occupancy_residual = attendance / capacity - baseline / capacity`

Prediction:

`P50 = baseline + predicted_occupancy_residual * capacity`

Final prediction is clipped to `[0, verified_capacity]`.

## Frozen early-horizon winners

| Horizon | Baseline | Feature set | Estimator | Dev 2023/24 MAE | 2024/25 MAE | 2025/26 MAE |
|---|---|---|---|---:|---:|---:|
| T-30 | current-season home mean with PIT fallback | full PIT + importance interactions | ExtraTrees, 500 trees, leaf=3, max_features=0.8 | **2,559.7** | **1,889.4** | **1,846.3** |
| T-14 | rolling-3 home attendance | base PIT | HistGradientBoosting absolute-error | **2,340.0** | **1,748.5** | **1,870.4** |

T-30 holdout diagnostics:

- 2024/25: median AE **1,173.3**, WAPE **14.81%**, bias **+538.6**;
- 2025/26: median AE **1,186.2**, WAPE **13.56%**, bias **+44.9**.

T-14 holdout diagnostics:

- 2024/25: median AE **883.3**, WAPE **13.73%**, bias **-99.4**;
- 2025/26: median AE **1,231.0**, WAPE **13.75%**, bias **-361.0**.

## Comparison with previous verified-capacity champion

Previous v2.2:

| Horizon | 2024/25 | 2025/26 |
|---|---:|---:|
| T-30 | 1,998.7 | 1,994.6 |
| T-14 | 1,869.8 | 1,960.3 |

Runtime v1:

| Horizon | 2024/25 | 2025/26 |
|---|---:|---:|
| T-30 | **1,889.4** | **1,846.3** |
| T-14 | **1,748.5** | **1,870.4** |

The new runtime candidate therefore improves both early horizons on both untouched seasons.

## Development-only search decisions

T-30:

- verified-capacity occupancy residual was better on development than attendance residual, ratio residual and direct occupancy;
- `baseline_season` was better on development than rolling-3 / rolling-5 / long-run mean alternatives;
- full PIT features + ExtraTrees leaf=3 beat the focused HistGBR / ExtraTrees / RandomForest development challengers;
- removing the physical capacity clip worsened both holdouts after the spec had already been frozen.

T-14:

- base PIT features + HistGradientBoosting remained the development winner after the focused estimator expansion;
- importance interactions did not justify replacing the base feature set at this horizon.

## Decision

- **T-14:** promote as the preferred historical champion candidate for the Structural Prior runtime.
- **T-30:** promote as the preferred current historical candidate because it cleanly improves v2.2, but continue model R&D. It is still above the strategic `<1700 MAE` target.
- No live ticketing feature is used in these numbers. This benchmark measures the Structural Prior only.
- No production/live P50 is materialized by this report. Runtime inference/materialization remains the next Step 6b task.

## Reproducibility note

Code:

- `ml/features/structural_prior_feature_store_v1.py`
- `ml/structural_prior_runtime_benchmark_v1.py`

The builder expects the validated canonical 2021/22–2024/25 and 2025/26 match inputs. The complete 2021/22–2024/25 canonical layer is not yet fully present in the current Supabase project, so the DB backfill remains an operational prerequisite for DB-native rebuilds. The benchmark itself was reproduced from the validated canonical CSV evidence used in the historical research pipeline.
