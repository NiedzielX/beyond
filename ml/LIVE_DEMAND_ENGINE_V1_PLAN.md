# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-18**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v2+v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector / Price-area Decision Support MVP: IMPLEMENTED**  
> **Current model-quality priority — strict historical unseen-event validation, then b -> c -> d -> a tuning**

| Phase | Scope | Status |
|---|---|---|
| A — Foundation | Canonical live trajectory / PIT evidence / registry | **DONE** |
| B — Shadow Forecasting | Structural Prior, trajectory gap, shadow revisions, audit | **DONE** |
| C0 — Provisional live decision layer | Continuation logic / sector decisions | **DONE / RUNNING** |
| C1-alpha | Frozen v2+v8 package + prospective pre-outcome evidence + scoring | **LIVE** |
| C1 — Promoted Learned Live Correction | Production promotion after sufficient fresh evidence | **EVIDENCE-GATED** |
| D — Probabilistic | Calibrated P10/P50/P90 | TODO |
| E0 — Sector / Price-area Decision Support | Sector trajectory, no-action projection, pricing scenarios, dashboard | **IMPLEMENTED** |
| E1 — Learned Pricing / Intervention | Learned elasticity / intervention uplift | **EVIDENCE-GATED** |

Canonical state:

- `ml/CURRENT_MODEL.md`;
- `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
- `AI_BOOTSTRAP.md`;
- `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
- `ml/SECTOR_DECISION_PRICING_V1.md`;
- `ml/NORTH_STAR.md`.

## Product purpose

Beyond must continuously answer:

1. where the event is likely to finish;
2. whether live evidence is strong enough to revise the Structural Prior;
3. which sectors / price areas are underperforming or outperforming;
4. what happens if the current trajectory continues;
5. what pricing action should be considered;
6. eventually, what happened after the club acted.

## Forecasting architecture

Target conceptual stack:

`Historical Structural Prior -> Current-season adjustment -> Match context -> Live trajectory -> Reliability / correction -> Final forecast`

The five official horizons remain:

- T-30;
- T-14;
- T-7;
- T-3;
- T-1.

But these are primarily **evaluation / reporting checkpoints**. The live system should be able to revise its internal estimate after any meaningful new snapshot when the signal is reliable.

## Production forecasting state

Promoted production live adjustment remains:

`live_adjustment = 0`

C1 v8 remains separate `EXPERIMENTAL_SHADOW` evidence and does not write production forecast values.

## Structural Prior

All five horizons are executable and frozen:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

Historical reference performance is maintained in `ml/CURRENT_MODEL.md`.

Do not rebuild this layer first. It is the strongest and most mature forecasting component.

## C1-alpha development evidence

Development set:

- 9 completed in-domain Ekstraklasa events;
- 206 PIT-valid full-trajectory rows;
- 30 regularized PIT-valid final-24h rows.

Key results:

- Prior on the development subset: **3,968.7 MAE**;
- v2 live expert: **2,929.3 MAE**;
- v8 development replay: **2,713.3 window / 1,998.1 latest-row MAE**;
- non-deployable Prior/Live oracle: **1,867.9 MAE**.

These are development results only and are not fresh unseen-event validation.

## Frozen C1-alpha package

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Frozen expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Rule:

- one observation: LIVE only if disagreement >= `0.20` capacity;
- >=2 observations: LIVE only if disagreement >= `0.10` and live slope to date > 0;
- otherwise PRIOR.

Scheduled inference must never fit this package.

## Prospective C1 v8 runtime — LIVE

Workflow:

`.github/workflows/c1-shadow-v8-inference.yml`

Cadence:

`9,24,39,54 * * * *`

Current verified state on 2026-10-18:

- prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- validation state: `AWAITING_FIRST_PROSPECTIVE_SCORE`.

Therefore there is still **no confirmed prospective live MAE**.

## New validation priority — BEFORE more model complexity

Run two strict tests using completed events with usable live evidence.

### 1. Leave-One-Event-Out

For each test event:

- exclude it from fitting and tuning;
- reconstruct only features available at the historical forecast timestamp;
- evaluate Structural Prior, live expert/C1 and final selection policy;
- report MAE, bias and event-level degradation.

### 2. Chronological walk-forward

At every step:

- train/tune only on events that occurred earlier;
- score later events;
- never use future outcomes or future snapshots.

These tests are the best historical approximation of unseen deployment quality. They do not replace prospective validation.

## Development roadmap after validation

### B1 — Stronger current-season adjustment

- recent home-match baseline;
- current-season above/below historical club norm;
- recency-weighted evidence;
- automatic update after completed matches.

### C2 — Richer match context

Add/test point-in-time-safe:

- opponent attractiveness / strength;
- future-fixture attractiveness;
- fixture cannibalization;
- home-fixture congestion;
- both-team form / league position;
- squad injuries / suspensions / key-player availability where reliable historical PIT reconstruction exists.

### D1 — Continuous live demand correction

- collect from earliest observable sales state;
- maintain velocity / acceleration / availability index continuously;
- include sector and price-area movement;
- use release / coverage anomaly flags;
- revise forecast after meaningful new snapshots;
- keep official horizons for evaluation rather than as the only inference points.

### A2 — Structural Prior tuning last

- feature contribution / ablation;
- remove unstable/noisy features;
- test stronger recent-season weighting;
- retain incumbent unless paired out-of-sample evidence improves it.

Canonical details:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`

## E0 sector / price-area decision support — IMPLEMENTED

Current implemented flow:

`sector state -> trajectory gap -> no-action projection -> real price-area mapping -> pricing scenario -> guarded recommendation`

Implemented:

- sector trajectory and status;
- no-action public-availability projection;
- Roboticket price-area capture where available;
- mixed-price sector split;
- assumption-based price scenarios;
- guarded `DECREASE / HOLD / INCREASE / MONITOR` recommendations;
- RLS-safe dashboard caches and UI.

Pricing maturity remains:

`ASSUMPTION_BASED_SCENARIO`

No automatic price changes:

`auto_price_change_allowed = false`

No learned elasticity or causal uplift claim is allowed yet.

Club decision / execution persistence is intentionally deferred for now. Demo intervention outcomes must be explicitly simulated.

## C1 promotion

The 20-independent-completed-match rule remains a later promotion gate.

Promotion requires enough genuinely prospective independent completed events, positive uplift vs Structural Prior, acceptable degradation/tail risk, frozen reproducible package, human review and explicit promotion.

No automatic production promotion exists.

## Immediate implementation sequence

1. **Implement strict LOEO + chronological walk-forward evaluation of the current model.**
2. Strengthen current-season adjustment.
3. Add future-fixture cannibalization and richer match context.
4. Move live demand correction toward continuous snapshot-driven revision.
5. Tune Structural Prior only after the above layers are evaluated.
6. Keep C1 v8 frozen and collect prospective outcomes in parallel.
7. Keep E0 pricing assumption-based and human-reviewed.
8. Keep production `live_adjustment = 0` until explicit promotion.

## Product target

> **Beyond should combine historical expectation, current-season reality, match context and continuously observed live demand to estimate where the event will finish — then translate that demand signal into safe sector and price-area decisions before kickoff.**
