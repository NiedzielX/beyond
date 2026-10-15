# Live Demand Engine — Phase B completion evidence

Date: **2026-10-15**

Status: **Phase B shadow infrastructure complete; learned live correction remains unpromoted.**

## Step 6 — Structural Prior — DONE

- canonical historical dataset: **1,530 Ekstraklasa matches / 5 seasons**;
- five-season PIT feature store: **7,650 rows**;
- current T-30 spec: `structural-prior-runtime-v1-t30-extra-full`;
- T-30 holdout MAE: **1,889.4 / 1,846.3**;
- current T-14 spec: `structural-prior-runtime-v1-t14-hist-base`;
- T-14 holdout MAE: **1,748.5 / 1,870.4**;
- first genuine current Structural Prior:
  - event `6`, Lech Poznań vs Wisła Kraków, 2026-10-31;
  - T-30 cutoff `2026-10-01 16:30:00Z`;
  - P50 **31,832.41**;
  - stadium capacity **43,269**;
  - expected occupancy **73.57%**;
  - persisted as `private.structural_prior_forecasts_v1.id=1`;
  - resolver returns `ready` with exact current model/feature lineage.

## Step 7 — Expected trajectory / trajectory gap — DONE

Implementation:

- `ml/demand_engine/trajectory_gap.py`;
- DB evidence: `private.trajectory_gap_observations_v1`;
- typed reference pool: `private.trajectory_gap_reference_pool_v1`.

Semantics:

- public seat-map inventory is a demand proxy, not confirmed paid sales;
- no 1:1 mapping from Structural Prior attendance P50 into public inventory;
- a genuine `ready` Structural Prior is mandatory as the final-demand anchor;
- expected live progress is descriptive and calculated from other PIT-valid, training-eligible trajectories at the same canonical horizon;
- target event and future reference evidence are excluded;
- minimum descriptive reference diversity: **3 events / 2 clubs**;
- classification against empirical progress IQR:
  - `UNDERPERFORMING`;
  - `ON_TRACK`;
  - `OUTPERFORMING`;
  - `INSUFFICIENT_SIGNAL`;
- confidence remains explicit (`NONE / LOW / MEDIUM / HIGH`).

Current T-14 reference pool available before the event-6 observation:

- events: **3**;
- clubs: **2**;
- progress Q25: **2.01%**;
- median: **2.23%**;
- Q75: **6.19%**;
- confidence if used now: **LOW**.

First event-6 trajectory observation:

- source snapshot: `15278`;
- as-of: `2026-10-15 12:31:03Z`;
- live feature version: `live-trajectory-v1.1`;
- raw / clean snapshots: **754 / 754**;
- signal readiness: `ready`;
- first public availability: **17,683**;
- current public availability: **10,534**;
- observed normalized net absorption: **40.43%**;
- hours to kickoff: **387.98**;
- trajectory status: `INSUFFICIENT_SIGNAL`;
- reason: `outside_reference_checkpoint_window`;
- why: the T-14 reference window starts at 384h before kickoff, while this point is still 387.98h out.

This is an intentional fail-closed result, not a data-quality failure.

## Step 8 — Persist shadow live forecasts — DONE

Implementation:

- `ml/demand_engine/structural_prior_shadow.py`;
- existing RPC `public.insert_demand_engine_shadow_forecast_v1` is reused because it accepts nullable intervals.

Contract:

- historical P50 = genuine Structural Prior P50;
- live adjustment = **0** until a live correction passes promotion governance;
- final P50 = Structural Prior P50;
- P10/P90 remain `NULL` until probabilistic calibration exists;
- source Structural Prior horizon is retained; the legacy nearest-checkpoint labeler is not used;
- payload persists Structural Prior, live feature and trajectory-gap lineage.

First new-stack shadow revision:

- `public.forecast_observations.id=1208`;
- event `6`;
- model version `beyond-demand-engine-v1-structural-prior-shadow`;
- historical model `structural-prior-runtime-v1-t30-extra-full`;
- historical P50 **31,832**;
- live adjustment **0**;
- final P50 **31,832**;
- P10/P90 `NULL`;
- source live version `live-trajectory-v1.1`;
- trajectory gap `INSUFFICIENT_SIGNAL / outside_reference_checkpoint_window`.

## Step 9 — first detection / revision history — DONE

DB contract:

- `private.trajectory_first_detection_v1`;
- trigger `private.capture_first_trajectory_divergence_v1()`;
- view `private.structural_shadow_revision_history_v1`.

Rules:

- first detection is written only for PIT-valid `UNDERPERFORMING` or `OUTPERFORMING` observations;
- `ON_TRACK` and `INSUFFICIENT_SIGNAL` never create a false alert;
- an out-of-order earlier PIT observation can replace a later first-detection timestamp;
- every new-stack shadow forecast already remains append-only in `forecast_observations`;
- revision view exposes revision number, P50 delta, trajectory state and source prior;
- after actual attendance is known it classifies revision effect as `IMPROVED / WORSENED / UNCHANGED`; before outcome it is `PENDING_OUTCOME`.

Current event-6 state:

- first-detection rows: **0** — correct, because there is no validated divergence yet;
- new-stack revisions: **1**;
- revision effect: `PENDING_OUTCOME`.

## Step 10 — live correction promotion gate — DONE as governance

Existing active governance remains the single promotion authority:

`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`

Key rules:

- Live Ticketing promotion evidence gate: **20 independent completed matches**;
- candidate must beat incumbent MAE and have positive uplift;
- frozen candidate package is created only after the evidence gate;
- package starts `ready_for_review`;
- human review is mandatory;
- `auto_activation_allowed = false` at DB level;
- crossing the gate never changes production P50 automatically.

Therefore Step 10 does not introduce a second threshold. The new Step-8 writer is shadow-only and preserves Structural Prior P50 until a future learned correction passes the existing governance.

## What Phase B does and does not mean

Phase B now provides the complete leakage-safe observation stack:

`Structural Prior -> live-trajectory-v1.1 -> trajectory-gap-v1 -> append-only shadow revision -> first detection/revision audit -> promotion governance`

It does **not** mean a learned live correction has been proven. That remains blocked on completed-event evidence.

## Next

1. Continue prospective evidence collection on the new stack.
2. When event 6 enters a canonical T-14 reference window, evaluate its first descriptive trajectory status with the frozen Step-7 rules.
3. Continue T-30 historical R&D toward **<1,700 MAE** in parallel.
4. Phase C: train and evaluate live residual correction only when evidence is sufficient.
5. Phase D: calibrate P10/P50/P90.
