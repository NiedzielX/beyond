# Beyond Ticketing — Current Model State

Last verified: **2026-10-15**

This file is the canonical short-form source of truth for the current forecasting model and Live Demand Engine implementation state.

## North star

Build the best possible leakage-safe **live forecasting system** for final attendance / ticket demand and its evolution toward kickoff.

The product combines:

- **Structural Prior** — what this match should do from historical/context evidence;
- **Live Ticketing Trajectory** — what the current match is actually doing;
- **Live Correction** — what the divergence implies for the final outcome.

Early actionability is first-class. Model development must not optimise T-1/T-3 at the expense of T-30/T-14.

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong intervention / correction;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final forecast / calibration checkpoint.

## Current historical dataset

- seasons: **2021/22–2025/26**;
- matches: **1,530**;
- competition used for current historical validation: **Ekstraklasa**;
- PIT horizons: **T-30 / T-14 / T-7 / T-3 / T-1**;
- PIT feature snapshots: **7,650**;
- verified historical stadium-capacity coverage: **100%**;
- model selection: **2023/24 only** after training on 2021/22–2022/23;
- untouched holdouts: **2024/25 + 2025/26**;
- one verified closed-door zero-attendance match remains historical truth but is excluded from normal demand-model training.

Exact Structural Prior Runtime v1 input hashes are pinned in:

`ml/data/STRUCTURAL_PRIOR_RUNTIME_V1_INPUT_MANIFEST.md`

## Current best validated historical specification by horizon

| Horizon | Current best spec | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| **T-30** | **Structural Prior Runtime v1 — ExtraTrees + full PIT + verified-capacity occupancy residual** | **1,889.4** | **1,846.3** |
| **T-14** | **Structural Prior Runtime v1 — HistGBR + base PIT + verified-capacity occupancy residual** | **1,748.5** | **1,870.4** |
| T-7 | Global v2 verified-capacity occupancy | **1,799.2** | **1,848.0** |
| T-3 | Global v2.3 verified-capacity + match-importance | **1,701.4** | **1,686.4** |
| T-1 | Global v2.3 verified-capacity + match-importance | **1,684.3** | **1,682.0** |

Combined two-holdout MAE for the new early-horizon runtime candidates:

- T-30: **~1,867.8**;
- T-14: **~1,809.4**.

Current single lowest holdout MAE remains **T-1 = ~1,682.0 on 2025/26**.

## Structural Prior Runtime v1 — early-horizon decision

### T-30

Frozen spec:

- model spec ID: `structural-prior-runtime-v1-t30-extra-full`;
- estimator: `ExtraTreesRegressor`;
- 500 trees;
- `min_samples_leaf=3`;
- `max_features=0.8`;
- baseline: current-season home attendance mean with PIT fallback (`baseline_season`);
- feature mode: full PIT including validated importance interactions;
- target: verified-capacity occupancy residual;
- final P50 clipped to `[0, verified_capacity]`.

Development 2023/24 MAE: **2,559.7**.

Holdouts:

- 2024/25: **1,889.4** MAE;
- 2025/26: **1,846.3** MAE.

This cleanly improves the previous v2.2 T-30 result (`1,998.7 / 1,994.6`) but remains above the strategic **<1,700 MAE** target. T-30 R&D therefore continues.

### T-14

Frozen spec:

- model spec ID: `structural-prior-runtime-v1-t14-hist-base`;
- estimator: `HistGradientBoostingRegressor` with absolute-error loss;
- `learning_rate=0.05`, `max_iter=180`, `max_leaf_nodes=15`, `min_samples_leaf=10`, `l2_regularization=1`;
- baseline: PIT home rolling-3 attendance (`baseline_r3`);
- feature mode: base PIT without the importance-interaction family;
- target: verified-capacity occupancy residual;
- final P50 clipped to `[0, verified_capacity]`.

Development 2023/24 MAE: **2,340.0**.

Holdouts:

- 2024/25: **1,748.5** MAE;
- 2025/26: **1,870.4** MAE.

This improves the previous v2.2 T-14 result (`1,869.8 / 1,960.3`) on both untouched seasons and becomes the preferred T-14 historical champion candidate.

## Current historical model families

- T-30: ExtraTrees verified-capacity occupancy-residual model with full PIT demand/context features;
- T-14: HistGradientBoosting verified-capacity occupancy-residual model with base PIT features;
- T-7: Gradient Boosting verified-capacity occupancy-residual model;
- T-3: HistGradientBoosting verified-capacity occupancy residual + match-importance interactions;
- T-1: HistGradientBoosting verified-capacity occupancy residual + match-importance interactions.

Horizon-specific contracts remain intentional. A feature family or model that helps one horizon is not assumed to help another.

## Structural Prior feature semantics

`ml/features/structural_prior_feature_store_v1.py` rebuilds the five-season PIT layer with these rules:

- historical attendance can carry across seasons;
- current-season attendance state is separate from long-run history;
- sporting state, form and table state reset each season;
- a completed match enters state only after `kickoff + 3h`;
- exact home/opponent pair history is PIT-only;
- opponent-draw history is PIT-only;
- verified historical capacity uses season-specific venue maps and explicit mid-season venue switches;
- every target has T-30/T-14/T-7/T-3/T-1 snapshots before kickoff;
- the target match never enters its own feature state.

The current builder produces:

- **1,530 matches**;
- **7,650 snapshots**;
- **7,198 training-eligible snapshots**;
- **0 missing verified capacities**;
- **0 as-of-at / kickoff violations**.

## Live Demand Engine — implementation status

### Phase A — Foundation: **DONE**

Completed:

1. canonical `LiveTrajectoryFeatureStore`;
2. exact-cutoff readiness;
3. calibrated release / anomaly semantics;
4. append-only PIT live-feature evidence store;
5. explicit live contract registry.

Current canonical live contracts are documented in:

`ml/demand_engine/LIVE_CONTRACT_REGISTRY.md`

### Phase B — Shadow Forecasting: **ACTIVE**

**Step 6 — Structural Prior**

- **6a adapter / model-domain guard: DONE**;
- **6b executable runtime: ACTIVE**.

Completed in 6b:

- reproducible five-season PIT historical feature builder;
- exact canonical input hashes;
- executable T-30/T-14 runtime implementation;
- frozen season-blocked benchmark;
- T-30/T-14 historical champion candidates improved on both holdouts.

Remaining before Step 6 is closed:

1. connect the runtime to a current-event PIT feature-row builder;
2. fit on the approved historical seasons and generate a genuine current P50 for an eligible future Ekstraklasa event;
3. persist that P50 in `private.structural_prior_forecasts_v1` with exact model/feature/input lineage;
4. update current DB Structural Prior specs to the new T-30/T-14 model IDs;
5. finish the missing 2021/22–2024/25 Supabase historical backfill for DB-native rebuilds.

**Do not start Step 7 trajectory-gap logic by pretending a prior exists.** Step 7 consumes only a genuine current Structural Prior row.

## Structural Prior domain guard

Current five-season historical champions are validated on **Ekstraklasa**.

The resolver returns:

- `not_due` before T-30;
- `out_of_domain` for competitions outside the validated scope;
- `missing_prior` when a current spec is due but no genuine materialized P50 exists;
- `ready` only when the exact current model/feature/checkpoint lineage exists.

No silent fallback to Lech v1.3/v0.3 is allowed.

## Live evidence maturity

Current append-only live feature evidence:

| Horizon | Materialized rows | Training-eligible |
|---|---:|---:|
| T-30 | 1 | **0** |
| T-14 | 5 | **3** |
| T-7 | 9 | **3** |
| T-3 | 6 | **2** |
| T-1 | 10 | **5** |

This is enough to build infrastructure but **not** enough to promote a learned live correction.

A first genuine T-30+ collection case is active for Jagiellonia Białystok vs Crystal Palace, but that UEFA event is currently `out_of_domain` for the Ekstraklasa Structural Prior. It remains useful for live-trajectory evidence collection, not for pretending the current historical champion has been validated on UEFA matches.

## Next implementation sequence

1. **NOW — finish Phase B / Step 6b current-event Structural Prior runtime + P50 materialization.**
2. Continue T-30 historical R&D toward **<1,700 MAE** in parallel; do not block runtime integration on that research goal.
3. Step 7 — expected trajectory / trajectory gap against the genuine Structural Prior.
4. Step 8 — persist shadow live forecasts.
5. Step 9 — first-detection and forecast-revision history.
6. Step 10 — keep live correction shadow-only until completed-event evidence is sufficient.
7. Phase C — learned live residual correction.
8. Phase D — calibrated P10/P50/P90.
9. Phase E — recommendations / intervention learning.

## Evaluation rule

Every historical challenger must preserve the same chronological contract:

- selection on 2023/24 only;
- 2024/25 and 2025/26 are untouched holdouts;
- all features are point-in-time;
- no target outcome in its own state;
- same completed event/checkpoint for baseline-vs-model comparison.

Every future live challenger must compare, on the same event/checkpoint:

1. Structural Prior error;
2. Structural Prior + live correction error.

No model is promoted because it looks intuitive or wins on a tiny prospective sample.

## Evidence files

- `ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md`
- `ml/data/STRUCTURAL_PRIOR_RUNTIME_V1_INPUT_MANIFEST.md`
- `ml/features/structural_prior_feature_store_v1.py`
- `ml/structural_prior_runtime_benchmark_v1.py`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_BENCHMARK_2026-10-14.md`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_2_VERIFIED_CAPACITY_2026-10-14.md`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_3_CAPACITY_IMPORTANCE_COMBO_2026-10-15.md`
- `ml/data/STADIUM_CAPACITY_HISTORY_V1.md`
- `ml/NORTH_STAR.md`
- `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`
- `ml/demand_engine/LIVE_CONTRACT_REGISTRY.md`
