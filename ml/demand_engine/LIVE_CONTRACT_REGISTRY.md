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
| Structural historical prior | horizon-specific | `ml/CURRENT_MODEL.md` | **CURRENT SOURCE OF TRUTH** |

## Contract rules

1. **No implicit aliases.** Training and inference should record the exact versioned object or feature version used.
2. **No in-place semantic mutation.** A change to feature meaning creates a new version, e.g. `live-trajectory-v1.2`, instead of silently changing `v1.1`.
3. **Point-in-time first.** A source snapshot must satisfy `source_snapshot_captured_at <= as_of_at` and `as_of_at < kickoff_at`.
4. **Evidence is append-only.** Later source backfills create new evidence rows rather than rewriting earlier training evidence.
5. **Readiness is separate from data existence.** `missing_snapshot`, `insufficient_signal`, `ready`, and `not_due` must not be collapsed into one boolean upstream of modelling.
6. **Public ticket inventory is a demand proxy, not confirmed paid sales.** This semantic must survive into model features, evaluation and product wording.
7. **Historical prior and live correction remain separable.** The incremental value of proprietary live evidence must always be measurable against the same structural prior.

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

## Current evidence maturity

After the first exact-checkpoint materialization on 2026-10-15:

| Horizon | Materialized rows | Training-eligible |
|---|---:|---:|
| T-30 | 1 | **0** |
| T-14 | 5 | **3** |
| T-7 | 9 | **3** |
| T-3 | 6 | **2** |
| T-1 | 10 | **5** |

This is infrastructure readiness, **not** evidence that an early-horizon live correction is ready for promotion.

## Next contract

The next planned contract is the **Structural Prior adapter** in Phase B of `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`. It will expose the horizon-specific historical champion through one stable interface without retraining or redefining the prior inside the live engine.
