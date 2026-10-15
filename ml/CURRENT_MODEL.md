# Beyond Ticketing — Current Model State

Last verified: **2026-10-15**

This file is the canonical short-form source of truth for the current forecasting model. Update it whenever a challenger becomes the new historical champion candidate, the training/evaluation dataset changes materially, or a live-model contract becomes canonical.

## North star

Build the best possible leakage-safe **live forecasting system** for final attendance / ticket demand and its evolution toward kickoff, with explicit priority on early actionable horizons where clubs still have time to react.

The product must combine:

- a structural historical prior — what this match should do;
- live ticketing trajectory — what it is actually doing now;
- trajectory correction — what the difference implies for the final outcome.

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong intervention / correction;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final forecast / calibration checkpoint.

T-3/T-1 remain important accuracy checkpoints, but the system must not optimise them at the expense of T-30/T-14 actionability.

## Current historical dataset

- seasons: **2021/22–2025/26**;
- matches: **1,530**;
- clubs: multi-club Ekstraklasa population across five seasons;
- point-in-time horizons: **T-30 / T-14 / T-7 / T-3 / T-1**;
- historical feature snapshots: **7,650**;
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

## Current historical model families

- T-30: Gradient Boosting occupancy-residual model with verified historical stadium capacity;
- T-14: HistGradientBoosting occupancy-residual model with verified historical stadium capacity;
- T-7: Gradient Boosting occupancy-residual model with verified historical stadium capacity;
- T-3: HistGradientBoosting occupancy-residual model with verified capacity + match-importance interactions;
- T-1: HistGradientBoosting occupancy-residual model with verified capacity + match-importance interactions.

These remain **historical champion candidates**, not automatically promoted production models.

## Historical predictive feature families that currently matter

Group-permutation evidence on 2025/26 shows useful signal from:

1. timing / seasonality;
2. opponent demand / opponent draw;
3. historical home attendance;
4. sporting state / form / table context;
5. verified stadium capacity / occupancy;
6. club identity, with smaller incremental importance than the families above.

Verified capacity is a first-class predictive data layer. Match-importance interactions add further value close to kickoff, but they are horizon-dependent and fail the development gate at T-30/T-14/T-7.

## Current historical promotion / rejection decisions

- verified capacity: **promote as historical challenger spec at T-30, T-14, T-7**;
- verified capacity + match-importance: **promote at T-3 and T-1**;
- verified capacity + match-importance: **reject at T-30, T-14 and T-7 because it fails the development gate**;
- horizon-specific contracts remain the preferred approach.

## Live Demand Engine — Foundation status

**Phase A — Foundation is implementation-complete pending the registry PR merge.**

Completed foundation contracts:

1. canonical point-in-time `LiveTrajectoryFeatureStore`;
2. exact-cutoff horizon readiness;
3. empirically calibrated release / anomaly semantics;
4. append-only point-in-time feature evidence materialization;
5. explicit version registry for current live contracts.

### Canonical live contracts

Human-readable registry:

`ml/demand_engine/LIVE_CONTRACT_REGISTRY.md`

Current versions:

| Contract | Current version / object |
|---|---|
| Live trajectory feature semantics | `live-trajectory-v1.1` |
| DB live feature function | `public.get_live_trajectory_features_v1_1_asof` |
| Horizon readiness | `private.ticketing_horizon_readiness_v2_1` |
| Feature evidence store | `private.live_trajectory_feature_snapshots_v1` |
| Current evidence projection | `private.current_live_trajectory_feature_snapshots_v1` |
| Single feature materializer | `private.materialize_live_trajectory_feature_snapshot_v1` |
| Due-checkpoint materializer | `private.materialize_due_live_trajectory_checkpoints_v1` |
| DB contract registry | `private.current_live_model_contracts_v1` |

Legacy `private.ticketing_horizon_checkpoint_readiness_v1` is **not canonical** for new modelling because nearest-snapshot semantics can select evidence captured after the intended business checkpoint. It remains available only for reproducibility.

## Live feature semantics

Current `live-trajectory-v1.1` includes:

- point-in-time snapshot cutoff;
- inventory level / index;
- optional capacity normalization;
- public-seat-map normalization;
- 6h / 24h / 72h / 7d net movement and velocity;
- velocity acceleration / deceleration;
- sector absorption and re-availability;
- sector entry / exit coverage changes;
- raw / clean snapshot counts;
- stale / duplicate / invalid-snapshot protection;
- recent-7d data-gap readiness;
- calibrated material release detection.

Material matched-sector release threshold:

`max(50 seats, 0.5% of first observed inventory)`

This threshold was calibrated from observed multi-club transitions rather than chosen only by intuition. Small seat re-availability/toggle noise remains distinct from material release activity. Sector coverage changes remain a separate signal.

Public ticket inventory is treated as a **demand proxy, not confirmed paid ticket sales**.

## Point-in-time live evidence store

Current append-only evidence table:

`private.live_trajectory_feature_snapshots_v1`

Initial exact-checkpoint materialization produced **31 evidence rows** with:

- **0** source-snapshot leakage violations;
- **0** `as_of_at >= kickoff_at` violations;
- **0** point-in-time validation failures;
- **0** feature-version mismatches;
- idempotent replay preserving the same row count.

Current evidence maturity:

| Horizon | Materialized rows | Training-eligible |
|---|---:|---:|
| T-30 | 1 | **0** |
| T-14 | 5 | **3** |
| T-7 | 9 | **3** |
| T-3 | 6 | **2** |
| T-1 | 10 | **5** |

This means the **infrastructure is ready, but the learned live correction is not**. In particular:

- T-30 has no training-eligible exact-checkpoint evidence yet;
- T-14 has only 3 training-eligible exact-checkpoint rows;
- no early-horizon live model should be promoted from such small samples.

Prospective collection therefore continues while the live architecture progresses in shadow mode.

## First early-horizon prospective case

Jagiellonia Białystok vs Crystal Palace:

- kickoff: **2026-12-10**;
- RoboTicket candidate: `5190`;
- mapped `ticket_event_id=24`;
- collection activated approximately 56 days before kickoff;
- formal T-30 cutoff is still in the future, so T-30 remains correctly `not_due` until that point.

## Next implementation phase

After Phase A is merged, move to **Phase B — Shadow Forecasting**.

Next concrete step:

**Phase B / Step 6 — StructuralPrior adapter**

The adapter must expose the current horizon-specific historical champion through one stable interface without retraining or redefining the prior inside the live engine.

Then:

7. initial expected-trajectory / trajectory-gap references;
8. shadow forecast persistence on eligible snapshots;
9. first-detection and revision persistence;
10. keep live correction shadow-only until sufficient completed evidence exists.

## Parallel modelling priorities

1. Continue improving the **T-30 / T-14 structural historical prior** under the frozen chronological dev/holdout protocol.
2. Continue collecting T-30/T-14 proprietary live trajectory evidence.
3. Build the live trajectory correction only when completed evidence supports credible evaluation.
4. Add calibrated P10/P50/P90 after point and trajectory contracts are stable.
5. Weather / Hype remain challengers only if they add point-in-time-safe out-of-sample uplift.

## Evaluation rule

Every challenger must use the same point-in-time contract and must not use 2024/25 or 2025/26 to choose its model family or hyperparameters.

For live models, the same completed event/checkpoint must be used to compare:

1. structural historical prior error;
2. structural prior + live correction error.

A more complex model is not better unless it reduces unseen-match error or improves earlier reliable detection under the same protocol.

No inference should be made from tiny live-event samples simply because a signal looks intuitive.

## Evidence files

- `ml/results/BEYOND_GLOBAL_FORECAST_V2_BENCHMARK_2026-10-14.md`
- `ml/results/beyond_global_forecast_v2_benchmark.json`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_1_CHALLENGERS_2026-10-14.md`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_2_VERIFIED_CAPACITY_2026-10-14.md`
- `ml/results/BEYOND_GLOBAL_FORECAST_V2_3_CAPACITY_IMPORTANCE_COMBO_2026-10-15.md`
- `ml/data/STADIUM_CAPACITY_HISTORY_V1.md`
- `ml/NORTH_STAR.md`
- `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`
- `ml/demand_engine/LIVE_CONTRACT_REGISTRY.md`
- `ml/CORE_PRODUCT_STATUS.md`
