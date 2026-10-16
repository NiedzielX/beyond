# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-16**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Before doing Beyond forecasting, ML, dashboard, Growth or recommendation work, read in this order:

1. `ml/CURRENT_MODEL.md` — canonical current model/product state;
2. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md` — current C1 prospective runtime/governance;
3. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — implementation roadmap;
4. `ml/C1_MODEL_TOURNAMENT_V1.md` — C1-alpha validation rules;
5. latest `ml/results/C1_ALPHA_*.md` evidence;
6. `ml/SECTOR_DECISION_PRICING_V1.md`;
7. `ml/NORTH_STAR.md`;
8. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
9. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
10. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Critical product direction

Beyond is a **live demand decision system**, not primarily a campaign tool or a single attendance model.

Primary flow:

`Structural Prior -> Live Trajectory -> Expert Reliability -> Sector Gap -> No-action Projection -> Pricing Scenario -> Recommendation -> Execution -> Outcome`

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## Production state

All Structural Prior horizons T-30/T-14/T-7/T-3/T-1 are executable and frozen.

Production remains:

`live_adjustment = 0`

Do not write C1 v8 into production forecast values without an explicit promotion decision.

## C1-alpha development state

Development evidence:

- 9 completed in-domain Ekstraklasa events;
- 206 PIT-valid full-trajectory rows;
- 30 regularized PIT-valid final-24h rows.

Key results:

- v2 final-24h live expert: **2,929.3 MAE** vs Prior **3,968.7**;
- non-deployable Prior/Live oracle: **1,867.9 MAE**;
- v3-v5 gating/stacking stayed around 3.05k–3.11k;
- v6 T-24-only was rejected;
- v7 showed that large prior/live disagreement plus live-trajectory direction is the useful reliability pattern;
- v8 fixed PIT-safe policy produced **2,713.3 window MAE** and **1,998.1 latest-row MAE** in development replay.

v8 is not independently validated because its fixed thresholds were designed after v7 on those same 9 events.

## Frozen C1 v8 package — already done

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Frozen v2 expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Policy:

- 1 observation: LIVE only if prior/live disagreement >= **20 pp capacity**;
- >=2 observations: LIVE only if disagreement >= **10 pp** and live slope to date > 0;
- otherwise PRIOR.

Artifact SHA256:

`df31af5effcda2d2f1e58265c7e954cc04edf0e90b48501403eb4e4afd94edf2`

Training-contract SHA256:

`0a3edde223d8b6e64652f3fc8f79228998ac0d93a90fdaa9fc48311f98dee304`

Artifact commit:

`9bcf8fe83f85ee7e47a555e975352b8438ea4e3d`

Frozen training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Do not retune or automatically retrain this package during prospective validation.

## Prospective shadow pipeline — already live

Operational spec:

`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`

Scheduler:

`.github/workflows/c1-shadow-v8-inference.yml`

Cadence:

`9,24,39,54 * * * *`

The runtime:

- authenticates through main-only GitHub OIDC;
- accepts only naturally due, PIT-valid `T-1` Structural Prior candidates inside final 24h;
- reconstructs at most four 6h representatives from snapshots already available at run time;
- loads the frozen v2 artifact and never fits;
- applies frozen v8;
- writes append-only pre-outcome decisions;
- scores only decisions that already existed before an outcome was known.

Pre-outcome evidence:

`private.c1_shadow_v8_predictions_v1`

Post-outcome scores:

`private.c1_shadow_v8_event_scores_v1`

The scorer never reconstructs a missed historical decision after the result arrives.

## Current prospective evidence

Initial live state on 2026-10-16:

- prospective prediction rows: **0**;
- prospective scored events: **0**;
- inference + persistence + scorer main workflow: **green**;
- zero evidence is intentional because the next matches were still T-3 during deployment.

No original development events were backfilled.

The next meaningful C1 checkpoint is the first non-zero pre-outcome decision created after a genuine T-1 prior becomes naturally due. The next one after that is its score once actual attendance is confirmed.

## C1 promotion governance

The 20-independent-completed-match rule is a later promotion gate, not a training-start gate.

During prospective validation do not:

- change 10 pp / 20 pp / positive-slope thresholds;
- automatically retrain the v2 expert;
- add new completed events into the frozen package silently;
- backfill missed decisions after outcomes;
- use future timestamps to force T-1;
- overwrite prior prospective evidence;
- call the original v8 replay fresh validation.

Any retrain requires an explicit new package version, artifact, event set and governance decision.

## Dynamic pricing / E0 — continue in parallel

Pricing remains a first-class intervention.

MVP output should include:

- `HOLD / INCREASE / DECREASE`;
- proposed price/scenario;
- projected availability/sell-through impact;
- projected revenue proxy;
- confidence;
- reason codes;
- assumption/model version.

Before learned elasticity exists, label this as assumption-based scenario analysis.

Never change a club's production price automatically:

`auto_price_change_allowed = false`

## Immediate work order

1. keep the frozen v2+v8 package unchanged and collect the first genuine T-1 prospective evidence;
2. expose read-only shadow status/evidence for operations/dashboard;
3. score each prospective event only from already-persisted decisions;
4. keep production Structural Prior/orchestrator unchanged with `live_adjustment=0`;
5. continue sector trajectory/no-action and E0 pricing work in parallel;
6. continue T-30 R&D separately.

## One-line cold-start instruction

> **Do not start another C1 tournament and do not retrain v8. The v2+v8 package is already frozen and running as `EXPERIMENTAL_SHADOW`; prediction and post-outcome scoring paths are live, current prospective evidence count is 0, and the next valid action is to collect the first naturally due T-1 decision while production remains `live_adjustment=0`.**
