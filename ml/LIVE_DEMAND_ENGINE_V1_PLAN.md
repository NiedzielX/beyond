# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-15 20:30 UTC**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C — Learned Live Correction: BLOCKED ON EVIDENCE**

| Phase | Step | Scope | Status |
|---|---:|---|---|
| A — Foundation | 1 | Canonical LiveTrajectoryFeatureStore | **DONE** |
| A — Foundation | 2 | Exact-cutoff checkpoint/readiness integration | **DONE** |
| A — Foundation | 3 | Robust release / anomaly semantics | **DONE** |
| A — Foundation | 4 | Append-only PIT live feature evidence store | **DONE** |
| A — Foundation | 5 | Versioned live contract registry | **DONE** |
| B — Shadow Forecasting | 6a | StructuralPrior adapter + model-domain guard | **DONE** |
| B — Shadow Forecasting | 6b | Executable Structural Prior runtime + genuine P50 materialization at T-30/T-14/T-7/T-3/T-1 | **DONE** |
| B — Shadow Forecasting | 7 | Expected trajectory / trajectory gap | **DONE** |
| B — Shadow Forecasting | 8 | Persist Structural Prior shadow revisions | **DONE** |
| B — Shadow Forecasting | 9 | First detection + revision audit | **DONE** |
| B — Shadow Forecasting | 10 | Promotion gate / shadow-only enforcement | **DONE** |
| C — Learned Correction | 11–14 | Train / evaluate residual live correction | **BLOCKED ON EVIDENCE** |
| D — Probabilistic | 15–17 | Calibrated P10/P50/P90 | TODO |
| E — Recommendations | 18–20 | Recommendation / intervention layer | LATER |

## Purpose

Continuously answer:

1. **Where is this match expected to finish?**
2. **Is current demand evolving better or worse than it should?**
3. **Did we detect the divergence early enough for the club to act?**

Core product equation:

`Live Forecast(t) = Structural Prior(t) + Live Trajectory Correction(t)`

Current Phase-B implementation keeps:

`Live Trajectory Correction(t) = 0`

until the learned correction passes evidence and governance gates.

Trajectory observation equation:

`Trajectory Gap(t) = Observed normalized public-inventory progress - Expected reference progress`

Public ticket inventory remains a **demand proxy, not confirmed paid sales**.

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong intervention / correction;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final forecast / calibration.

## Phase A — Foundation — DONE

Canonical live contract:

`live-trajectory-v1.1`

Includes:

- point-in-time public inventory;
- 6h / 24h / 72h / 7d velocity;
- acceleration;
- inventory/capacity normalization where valid;
- sector absorption/release and coverage changes;
- snapshot quality and gap telemetry;
- release/anomaly semantics;
- exact-cutoff checkpoint readiness.

Canonical evidence store:

`private.live_trajectory_feature_snapshots_v1`

Current evidence:

| Horizon | Training-eligible | Total stored |
|---|---:|---:|
| T-30 | **0** | 1 |
| T-14 | **3** | 5 |
| T-7 | **3** | 9 |
| T-3 | **4** | 9 |
| T-1 | **5** | 10 |

This is enough for infrastructure validation, not for promotion of a learned correction.

## Phase B — Shadow Forecasting — DONE

### Step 6 — genuine Structural Prior — DONE across all five horizons

Current executable model specs:

- T-30: `structural-prior-runtime-v1-t30-extra-full`;
- T-14: `structural-prior-runtime-v1-t14-hist-base`;
- T-7: `structural-prior-runtime-v1-t7-gbr-base`;
- T-3: `structural-prior-runtime-v1-t3-hist-full`;
- T-1: `structural-prior-runtime-v1-t1-hist-full`.

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Five-season validated historical input:

- **1,530 matches**;
- **7,650 PIT snapshots**;
- DB-native backfill complete;
- current validated domain: **Ekstraklasa**.

The automatic materializer, registry, resolver and gateway support all five checkpoints. No silent fallback to old Lech v1.3/v0.3 is allowed.

Latest verified orchestrator run after the five-horizon rollout:

`private.live_forecast_orchestrator_runs_v1.id = 18`

- active events: **12**;
- processed: **12**;
- `missing_prior`: **0**;
- skipped: **0**;
- errors: **0**;
- checkpoint rows materialized: **34**.

T-1 is deployed but the first current T-1 cutoff is not naturally due until **2026-10-16 15:30 UTC**. Do not pre-materialize future PIT evidence.

### Step 7 — expected trajectory / trajectory gap — DONE

Implementation:

`ml/demand_engine/trajectory_gap.py`

DB:

- `private.trajectory_gap_observations_v1`;
- `private.trajectory_gap_reference_pool_v1`.

Initial v1 is intentionally descriptive:

- Structural Prior is the mandatory final-demand anchor;
- attendance P50 is not converted 1:1 to public inventory;
- expected progress comes from other PIT-valid live trajectories at the same canonical horizon;
- target event and future evidence are excluded;
- minimum reference pool: **3 events / 2 clubs**;
- status: `UNDERPERFORMING / ON_TRACK / OUTPERFORMING / INSUFFICIENT_SIGNAL`;
- confidence is explicit.

### Step 8 — shadow revisions — DONE

Implementation:

`ml/demand_engine/structural_prior_shadow.py`

New-stack rows use:

- Structural Prior P50 as historical P50;
- live adjustment **0**;
- final P50 = Structural Prior P50;
- P10/P90 `NULL` until calibration;
- `live-trajectory-v1.1` lineage;
- `trajectory-gap-v1` lineage and reason codes;
- source Structural Prior horizon rather than the legacy nearest-checkpoint labeler.

### Step 9 — first detection / revision history — DONE

DB:

- `private.trajectory_first_detection_v1`;
- trigger `private.capture_first_trajectory_divergence_v1()`;
- view `private.structural_shadow_revision_history_v1`.

Only PIT-valid `UNDERPERFORMING` or `OUTPERFORMING` states create first detection.

After outcome arrival each revision is scored as:

- `IMPROVED`;
- `WORSENED`;
- `UNCHANGED`;
- or `PENDING_OUTCOME` before the match is resolved.

### Step 10 — promotion gate — DONE as governance

Single source of truth:

`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`

Live Ticketing evidence gate remains:

- **20 independent completed matches**;
- positive uplift;
- challenger MAE below incumbent;
- frozen evidence package;
- mandatory human review;
- `auto_activation_allowed = false`.

Crossing the gate never changes production P50 automatically.

## Phase C — Learned Live Correction — BLOCKED ON EVIDENCE

Future target:

`live_target_residual = actual_attendance - structural_prior_p50`

Candidate predictors may include:

- trajectory level gap;
- normalized inventory position;
- 6h / 24h / 72h / 7d velocity;
- acceleration;
- release/coverage-change signals;
- signal quality and source coverage;
- horizon interactions;
- Structural Prior occupancy/context.

Every challenger must compare on the **same completed event/checkpoint**:

1. Structural Prior error;
2. Structural Prior + live correction error.

Primary metrics:

- MAE;
- WAPE;
- bias;
- event-improvement rate;
- early-warning lead time.

No learned correction is promoted while the completed-event evidence base remains too small.

## Phase D — Probabilistic

Only after the point forecast stack is stable:

- calibrated P10/P50/P90;
- pinball loss;
- P10–P90 coverage;
- horizon-specific calibration;
- no fake intervals in Phase B.

## Phase E — Recommendations

Later layer:

- translate validated trajectory divergence into intervention options;
- persist intervention timing;
- measure whether actions changed the subsequent trajectory;
- never infer causal uplift from an unobserved counterfactual.

## Immediate sequence

1. **Verify the first naturally due T-1 production materialization after 2026-10-16 15:30 UTC.**
2. Continue prospective evidence collection on the completed five-horizon Phase-B stack.
3. Continue T-30 Structural Prior R&D toward **<1,700 MAE** in parallel.
4. Start Phase C training only when evidence governance permits it.
5. Phase D calibration after point-model stability.

## Reproducibility

Key files:

- `AI_BOOTSTRAP.md`;
- `ml/CURRENT_MODEL.md`;
- `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
- `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
- `ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md`;
- `ml/results/LIVE_DEMAND_ENGINE_PHASE_B_2026-10-15.md`;
- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/current_structural_prior_features.py`;
- `ml/demand_engine/trajectory_gap.py`;
- `ml/demand_engine/structural_prior_shadow.py`;
- `ml/demand_engine/sql/phase_b_shadow_contracts_v1.sql`;
- `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.
