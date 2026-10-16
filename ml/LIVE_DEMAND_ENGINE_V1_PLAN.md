# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-16**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v2+v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector Decision & Dynamic Pricing MVP: ACTIVE IN PARALLEL**

| Phase | Scope | Status |
|---|---|---|
| A — Foundation | Canonical live trajectory / PIT evidence / registry | **DONE** |
| B — Shadow Forecasting | Structural Prior, trajectory gap, shadow revisions, audit | **DONE** |
| C0 — Provisional live decision layer | Continuation logic / sector decisions | **ACTIVE** |
| C1-alpha | Frozen v2+v8 package + prospective pre-outcome evidence + scoring | **LIVE** |
| C1 — Promoted Learned Live Correction | Production promotion after sufficient fresh evidence | **EVIDENCE-GATED** |
| D — Probabilistic | Calibrated P10/P50/P90 | TODO |
| E0 — Sector Decision & Dynamic Pricing | Sector diagnosis, no-action projection, pricing scenarios, dashboard | **ACTIVE** |
| E1 — Learned Pricing / Intervention | Learned elasticity / intervention uplift | **EVIDENCE-GATED** |

Canonical state:

- `ml/CURRENT_MODEL.md`;
- `AI_BOOTSTRAP.md`;
- `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
- `ml/C1_MODEL_TOURNAMENT_V1.md`;
- latest `ml/results/C1_ALPHA_*.md`.

## Product purpose

Beyond must continuously answer:

1. where the event is likely to finish;
2. whether live evidence is strong enough to revise the Structural Prior;
3. which sectors are underperforming / outperforming;
4. what happens if the current trajectory continues;
5. what pricing action should be considered;
6. what happened after the club acted.

Primary decision unit:

`event -> sector -> trajectory -> expert reliability -> no-action projection -> pricing scenario -> recommendation`

## Production forecasting stack

`Structural Prior -> live-trajectory-v1.1 -> trajectory-gap-v1 -> decision layer`

Current promoted learned correction:

`live_adjustment = 0`

v8 remains separate `EXPERIMENTAL_SHADOW` evidence and does not write production forecast values.

## Structural Prior

All five horizons are executable and frozen:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Scheduled inference is load + predict only.

## C1-alpha development evidence

- 9 completed in-domain Ekstraklasa events;
- 206 PIT-valid full-trajectory rows;
- 30 regularized PIT-valid final-24h rows.

Completed ladder:

| Version | Formulation | Main result | Status |
|---|---|---:|---|
| v1 | mixed all-phase trajectory | incumbent remained best | reject |
| v2 | final-24h live expert | **2,929.3 MAE** | retain expert |
| v3 | nested threshold/blend | 3,054.3 | reject |
| v4 | stacked/meta gate | 3,106.8 | reject |
| v5 | stack + hybrid | 3,073.8 | reject |
| v6 | one-row T-24 | 3,873.2 LOEO / 3,989.8 LOCO | reject |
| v7 | reliability diagnostic | disagreement + live direction useful | complete |
| v8 | fixed PIT-safe expert switch | **2,713.3 window / 1,998.1 latest-row** | frozen shadow candidate |

v8 development replay is not fresh validation because the policy was defined after v7 on the same 9 events.

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

Artifact SHA256:

`df31af5effcda2d2f1e58265c7e954cc04edf0e90b48501403eb4e4afd94edf2`

Training-contract SHA256:

`0a3edde223d8b6e64652f3fc8f79228998ac0d93a90fdaa9fc48311f98dee304`

Training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Scheduled inference must never fit this package.

## Prospective C1 v8 runtime — LIVE

Operational spec:

`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`

Workflow:

`.github/workflows/c1-shadow-v8-inference.yml`

Cadence:

`9,24,39,54 * * * *`

The live shadow path now:

1. accepts only naturally due, PIT-valid T-1 events inside final 24h;
2. reconstructs at most four representative 6h observations available by run time;
3. loads the frozen v2 artifact;
4. predicts without fitting;
5. applies the frozen v8 rule;
6. persists an append-only pre-outcome decision;
7. scores completed events only from decisions that were already persisted before outcome.

Pre-outcome store:

`private.c1_shadow_v8_predictions_v1`

Post-outcome score store:

`private.c1_shadow_v8_event_scores_v1`

Input RPC:

`public.get_c1_shadow_v8_inputs_v1(timestamptz)`

Writer RPC:

`public.insert_c1_shadow_v8_predictions_v1(jsonb,timestamptz)`

Scorer RPC:

`public.score_c1_shadow_v8_completed_events_v1(timestamptz)`

Main-only GitHub OIDC gateway:

`c1_shadow_v8_gateway_v1`

## Current prospective state

Initial production-shadow verification on 2026-10-16 is green end-to-end:

- input candidate count: **0**;
- prediction rows persisted: **0**;
- prospective scored events: **0**;
- scorer metrics: null until first prospective completed event.

This is the correct state. The next events were still T-3 during deployment, so no T-1 decision was fabricated and no development event was backfilled.

Next valid checkpoints:

1. first non-zero pre-outcome v8 decision after a genuine T-1 prior becomes naturally due;
2. first post-outcome score after that event completes and attendance is confirmed.

## Prospective validation governance

Do not:

- retune v8 thresholds;
- auto-retrain the frozen v2 expert;
- silently expand the training set;
- backfill missed decisions after outcomes;
- use future timestamps to generate evidence early;
- overwrite existing prospective decisions;
- relabel development replay as prospective evidence.

Any retrain requires an explicit new package version and governance decision.

## C1 promotion

The 20-independent-completed-match rule remains a later promotion gate.

Promotion requires:

- enough genuinely prospective independent completed events;
- positive policy uplift vs Structural Prior;
- acceptable degradation/tail risk;
- frozen reproducible package and immutable evidence;
- human review;
- explicit promotion decision.

No automatic production promotion exists.

## C0 — Provisional decision layer

Continue in parallel:

- continuation/no-action event projection;
- sector diagnosis;
- explicit provisional reason codes;
- dashboard decision support.

Required labels:

- `PROVISIONAL`;
- `SCENARIO`;
- `CURRENT TRAJECTORY CONTINUES`.

## E0 — Sector Decision & Dynamic Pricing MVP

Continue in parallel with prospective C1 collection.

Per sector track:

- current availability;
- absorption/sell-through proxy;
- velocity/acceleration;
- expected vs observed progress;
- trajectory gap;
- status/confidence;
- release/coverage/data-quality flags.

Preferred no-action wording:

**Projected outcome if current trajectory continues**

Dynamic pricing scenarios may compare `-10%`, `-5%`, `HOLD`, `+5%`, `+10%`, but before learned elasticity exists they are assumption-based scenario analysis.

No automatic price changes:

`auto_price_change_allowed = false`

## Immediate implementation sequence

1. collect first naturally due prospective T-1 v8 evidence without modifying the package;
2. expose read-only prospective status/evidence for operations/dashboard;
3. score every newly completed prospective event automatically;
4. keep production `live_adjustment=0`;
5. continue sector/no-action projection and E0 pricing work;
6. continue T-30 R&D separately.

## Product target

> **Beyond should tell the club where the event is going, whether the live trajectory is strong enough to override the Structural Prior, which sectors are falling behind, what is likely to remain unsold if nothing changes, and what price action is worth testing — while learning prospectively from frozen pre-outcome decisions.**
