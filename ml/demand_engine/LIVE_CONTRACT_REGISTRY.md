# Beyond Live Demand Engine — Contract Registry

Last verified: **2026-10-15**

This file is the canonical human-readable registry of active live-model contracts. Versioned historical objects remain available for reproducibility, but new modelling, training and inference work must use the contracts marked **CURRENT** below.

## Current contracts

| Contract | Current version | Canonical object / implementation | Status |
|---|---|---|---|
| Live trajectory feature semantics | `live-trajectory-v1.1` | `ml/demand_engine/live_trajectory_feature_store.py` | **CURRENT** |
| Live trajectory DB feature function | `v1.1` | `public.get_live_trajectory_features_v1_1_asof` | **CURRENT** |
| Horizon readiness | `v2.1` | `private.ticketing_horizon_readiness_v2_1` | **CURRENT** |
| Point-in-time feature evidence store | `v1` | `private.live_trajectory_feature_snapshots_v1` | **CURRENT** |
| Current evidence projection | `v1` | `private.current_live_trajectory_feature_snapshots_v1` | **CURRENT** |
| Feature materializer | `v1` | `private.materialize_live_trajectory_feature_snapshot_v1` | **CURRENT** |
| Due-checkpoint bulk materializer | `v1` | `private.materialize_due_live_trajectory_checkpoints_v1` | **CURRENT** |
| Structural Prior model specs | `v1` | `private.current_structural_prior_model_specs_v1` | **CURRENT** |
| Structural Prior runtime T-30/T-14 | `runtime-v1` | `ml/demand_engine/structural_prior_runtime.py` | **CURRENT HISTORICAL CANDIDATE** |
| Structural Prior materialized store | `v1` | `private.structural_prior_forecasts_v1` | **CURRENT CONTRACT; FIRST CURRENT P50 STILL PENDING** |
| Structural Prior resolver | `v1` | `public.get_structural_prior_v1` / `ml/demand_engine/structural_prior.py` | **CURRENT** |

## Contract rules

1. **No implicit aliases.** Training and inference record the exact versioned model/feature contract used.
2. **No in-place semantic mutation.** A feature or model-semantic change creates a new version.
3. **Point-in-time first.** Source evidence must exist at or before the target `as_of_at`, and the target must precede kickoff.
4. **Evidence is append-only.** Backfills or model changes create new lineage instead of rewriting prior evidence.
5. **Readiness is separate from data existence.** `not_due`, `missing_prior`, `out_of_domain`, `invalid_prior`, and `ready` stay explicit.
6. **Public ticket inventory is a demand proxy, not confirmed paid sales.**
7. **Historical prior and live correction remain separable.** Live uplift is always measured against the same Structural Prior.
8. **Model domain is explicit.** Current historical champions are validated on Ekstraklasa only.
9. **Runtime and adapter specs must stay synchronized.** CI checks T-30/T-14 runtime IDs and feature contracts against the adapter contract.

## Version lineage

### Live feature semantics

- `live-trajectory-v1` — first canonical PIT trajectory contract.
- `live-trajectory-v1.1` — **CURRENT**; calibrated material release semantics: `max(50 seats, 0.5% of first observed inventory)`.

### Horizon readiness

- `private.ticketing_horizon_checkpoint_readiness_v1` — legacy nearest-snapshot contract; lineage only.
- `private.ticketing_horizon_readiness_v2` — first exact-cutoff PIT readiness.
- `private.ticketing_horizon_readiness_v2_1` — **CURRENT** exact-cutoff readiness using live-trajectory-v1.1.

### Feature evidence

- `private.live_trajectory_feature_snapshots_v1` — **CURRENT** append-only live feature evidence.
- `private.current_live_trajectory_feature_snapshots_v1` — latest projection without deleting historical materializations.

### Structural Prior

The Structural Prior is the latest already-due validated historical checkpoint carried forward until the next checkpoint becomes due. It never looks ahead to a future horizon.

Current horizon specs:

| Horizon | Model spec | Family | Feature contract | Validated competition |
|---|---|---|---|---|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | ExtraTreesRegressor | `structural-prior-pit-v1+verified-capacity-v1` | Ekstraklasa |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | HistGradientBoostingRegressor | `structural-prior-pit-v1+verified-capacity-v1` | Ekstraklasa |
| T-7 | `global-v2-verified-capacity-occupancy-t7` | GradientBoostingRegressor | `global-pit-v2+verified-capacity-v1` | Ekstraklasa |
| T-3 | `global-v2.3-verified-capacity-importance-t3` | HistGradientBoostingRegressor | `global-pit-v2+verified-capacity-v1+match-importance-v1` | Ekstraklasa |
| T-1 | `global-v2.3-verified-capacity-importance-t1` | HistGradientBoostingRegressor | `global-pit-v2+verified-capacity-v1+match-importance-v1` | Ekstraklasa |

Early-horizon benchmark evidence:

- T-30: **1,889.4 / 1,846.3 MAE** on 2024/25 / 2025/26;
- T-14: **1,748.5 / 1,870.4 MAE** on 2024/25 / 2025/26.

Evidence: `ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md`.

Resolver states:

- `not_due` — before T-30;
- `out_of_domain` — current champion is not validated for the event competition;
- `missing_prior` — a valid model spec is due, but its current P50 has not been materialized;
- `invalid_prior` — materialized lineage/PIT validation fails;
- `ready` — exact current materialized prior exists and passes all checks.

**No legacy fallback is allowed.** Stored Lech v1.3/v0.3 forecasts must never be presented as the current multi-club Structural Prior.

Structural Prior remains a **P50-first contract**. P10/P90 are optional until the probabilistic phase; legacy intervals must not be fabricated or copied into the new runtime.

## Current live evidence maturity

| Horizon | Materialized live-feature rows | Training-eligible |
|---|---:|---:|
| T-30 | 1 | **0** |
| T-14 | 5 | **3** |
| T-7 | 9 | **3** |
| T-3 | 6 | **2** |
| T-1 | 10 | **5** |

This is infrastructure readiness, not evidence that a learned early-horizon live correction is ready for promotion.

## Immediate next task

Generate and persist the first genuine current Structural Prior P50 for an in-domain future Ekstraklasa fixture using the executable T-30/T-14 runtime, exact PIT features and complete lineage. Only then can Step 7 trajectory-gap logic consume the prior.
