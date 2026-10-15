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
| Structural Prior materialized store | `v1` | `private.structural_prior_forecasts_v1` | **CURRENT CONTRACT; NO CURRENT GLOBAL P50 ROWS YET** |
| Structural Prior resolver | `v1` | `public.get_structural_prior_v1` / `ml/demand_engine/structural_prior.py` | **CURRENT** |

## Contract rules

1. **No implicit aliases.** Training and inference should record the exact versioned object or feature version used.
2. **No in-place semantic mutation.** A change to feature meaning creates a new version instead of silently changing a prior contract.
3. **Point-in-time first.** Source evidence must exist at or before the target `as_of_at`, and the target must precede kickoff.
4. **Evidence is append-only.** Later source backfills or model-spec changes create new evidence rows rather than rewriting earlier lineage.
5. **Readiness is separate from data existence.** `missing_snapshot`, `insufficient_signal`, `ready`, and `not_due` must not be collapsed upstream of modelling.
6. **Public ticket inventory is a demand proxy, not confirmed paid sales.** This semantic survives into features, evaluation and product wording.
7. **Historical prior and live correction remain separable.** The incremental value of proprietary live evidence must always be measured against the same Structural Prior.
8. **Model domain is explicit.** A historical model cannot be used outside its validated competition scope merely because compatible-looking input fields exist.

## Version lineage

### Live feature semantics

- `live-trajectory-v1` — first canonical PIT trajectory contract: 6h/24h/72h/7d velocity, acceleration, sector movement, quality telemetry and capacity/public-seat-map normalization.
- `live-trajectory-v1.1` — **CURRENT**. Adds empirically calibrated material release semantics: `max(50 seats, 0.5% of first observed inventory)`; sector coverage changes remain separate from release activity.

### Horizon readiness

- `private.ticketing_horizon_checkpoint_readiness_v1` — legacy nearest-snapshot contract. May select a snapshot after the intended business checkpoint. **Do not use for new modelling.** Preserved only for reproducibility.
- `private.ticketing_horizon_readiness_v2` — exact-cutoff PIT readiness using live-trajectory-v1.
- `private.ticketing_horizon_readiness_v2_1` — **CURRENT** exact-cutoff readiness using live-trajectory-v1.1.

### Feature evidence

- `private.live_trajectory_feature_snapshots_v1` — **CURRENT** append-only feature evidence table for training and inference lineage.
- `private.current_live_trajectory_feature_snapshots_v1` — latest materialized evidence projection without deleting historical evidence rows.

### Structural Prior

The Structural Prior is the latest already-due validated historical checkpoint carried forward until the next checkpoint becomes due. It never looks ahead to a future horizon.

Current horizon specs:

| Horizon | Model spec | Family | Feature contract | Validated competition |
|---|---|---|---|---|
| T-30 | `global-v2-verified-capacity-occupancy-t30` | GradientBoostingRegressor | `global-pit-v2+verified-capacity-v1` | Ekstraklasa |
| T-14 | `global-v2-verified-capacity-occupancy-t14` | HistGradientBoostingRegressor | `global-pit-v2+verified-capacity-v1` | Ekstraklasa |
| T-7 | `global-v2-verified-capacity-occupancy-t7` | GradientBoostingRegressor | `global-pit-v2+verified-capacity-v1` | Ekstraklasa |
| T-3 | `global-v2.3-verified-capacity-importance-t3` | HistGradientBoostingRegressor | `global-pit-v2+verified-capacity-v1+match-importance-v1` | Ekstraklasa |
| T-1 | `global-v2.3-verified-capacity-importance-t1` | HistGradientBoostingRegressor | `global-pit-v2+verified-capacity-v1+match-importance-v1` | Ekstraklasa |

Resolver states include:

- `not_due` — before T-30;
- `out_of_domain` — current champion is not validated for the event competition;
- `missing_prior` — a valid model spec is due, but its current P50 has not yet been materialized;
- `ready` — exact materialized current prior exists and passes lineage/PIT checks.

**No legacy fallback is allowed.** In particular, stored Lech v1.3/v0.3 forecasts must not be presented as the current multi-club global champion.

Current scope limitation: the validated five-season historical champions were evaluated on **Ekstraklasa**. UEFA events therefore remain `out_of_domain` until a suitable model is validated for that domain.

Structural Prior v1 is currently a **P50-first contract**. P10/P90 remain optional and must not be fabricated from legacy intervals; probabilistic live forecasting is Phase D.

## Current live evidence maturity

After the first exact-checkpoint materialization on 2026-10-15:

| Horizon | Materialized rows | Training-eligible |
|---|---:|---:|
| T-30 | 1 | **0** |
| T-14 | 5 | **3** |
| T-7 | 9 | **3** |
| T-3 | 6 | **2** |
| T-1 | 10 | **5** |

This is infrastructure readiness, **not** evidence that an early-horizon learned live correction is ready for promotion.

## Next contract / runtime task

Structural Prior **adapter semantics are implemented**, but the current global historical champion still needs an executable runtime/materializer that writes genuine P50 rows into `private.structural_prior_forecasts_v1`.

Therefore the immediate next task is **Phase B / Step 6b — current global Structural Prior runtime/materialization**, starting with T-30/T-14. Only after real current-prior rows exist should Step 7 trajectory-gap work consume the prior.
