# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-19**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering it.

## Cold-start rule

Read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
2. `ml/CURRENT_MODEL.md`;
3. `ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`;
4. `ml/artifacts/d2_event5_holdout_v1/manifest.json`;
5. `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
6. `ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`;
7. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
8. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
9. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
10. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
11. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
12. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

> **Keep the frozen d2 package unchanged and accumulate genuinely prospective event-level evidence. Score each new completed eligible event append-only and preserve component diagnostics. Do not retrain from event 5.**

## Canonical sequence

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> Stage 1 FROZEN -> Stage 2 FROZEN -> EVENT 5 HOLDOUT COMPLETE -> PROSPECTIVE ACCUMULATION ACTIVE`

## Frozen architecture

Pre-live:

`history + proven current-season regime -> Frozen Pre-Live v2`

Live:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

Frozen components:

- Pre-Live v2: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- Stage-1 expert: `ridge-a10`;
- Stage-2 policy: `P2-observation-maturity`;
- d2 package: `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

Do not change these from event-5 evidence.

## Historical workstreams

### a2

`CLOSED FOR CURRENT HISTORICAL DATA`

T-7 base:

`hist31-leaf20-l2-1`

### b2

`CLOSED / FROZEN INTO PRE-LIVE V2`

Frozen non-zero policies:

- T-7: `ewma50-resid-k6-cap05-min3`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

Event 5 produced a fresh warning that the T-1 b2 correction can move a high-demand match in the wrong direction. This is prospective diagnostic evidence only; one event is insufficient to retune or reopen b2.

### c2 historical

`SUFFICIENTLY EVALUATED / NO HISTORICAL CONTEXT EXTENSION`

Historical contract:

`NO_CONTEXT_ALL_HORIZONS`

## d2 Stage 1 — FROZEN EXPERT

Expert:

`ridge-a10`

Development latest MAE:

`3320.39` vs Frozen-v2 `4128.01`

Worst development event degradation:

`4326.90 seats`

## d2 Stage 2 — FROZEN POLICY

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Policy:

`P2-observation-maturity`

Development result:

- latest MAE: `3240.99`;
- latest uplift vs Frozen v2: `887.02 seats / 21.49%`;
- window MAE: `3657.65`;
- worst latest-event degradation: `1081.72`;
- 75% reduction in worst degradation vs raw Ridge.

Frozen reliability:

- observation 1 -> `0.25`;
- observation 2 -> `0.60`;
- observation 3+ -> `1.00`;
- time cap >18h `0.75`, >12h<=18h `0.90`, <=12h `1.00`;
- final reliability = minimum of observation and time weights.

## Event 5 — FIRST CHRONOLOGICAL HOLDOUT COMPLETE

Canonical result:

`ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`

Manifest:

`ml/artifacts/d2_event5_holdout_v1/manifest.json`

Run:

`39310995137`

Artifact ID:

`12215538287`

Match:

Lech Poznań vs Korona Kielce

Actual attendance:

`37,407`

### Holdout errors

- Frozen Pre-Live v2 latest/window: `9832.52`;
- raw frozen Ridge latest: `6652.81`;
- raw Ridge window: `6170.35`;
- frozen P2 latest: `6652.81`;
- frozen P2 window: `7263.16`;
- persisted C1 v8 policy/latest: `7669.07`.

D2 latest reduced Frozen-v2 error by:

`3179.71 seats / 32.34%`

D2 latest beat persisted C1 v8 policy by:

`1016.26 seats`

## Critical event-5 component diagnostic

Structural T-1 base:

`29737.93`

Frozen Pre-Live v2 after b2:

`27574.48`

b2 correction:

`-2163.45 seats`

Actual:

`37407`

Therefore:

- Structural base error: `7669.07`;
- Frozen-v2 error: `9832.52`.

On this holdout, b2 worsened the anchor by `2163.45 seats`.

Mandatory interpretation:

> **Record this as a prospective b2 failure signal. Do not tune b2 from one event. If the same failure repeats over materially more independent prospective events, create a separately versioned b2/Pre-Live challenger.**

## P2 behavior on event 5

P2 deliberately shrank the first two useful Ridge corrections, so its window MAE was worse than raw Ridge on this event.

At observations 3 and 4 reliability was `1.0`; latest P2 = latest raw Ridge.

Do not change P2 because of this event.

## Active next phase — prospective accumulation

For each new eligible completed event, score the frozen package without retraining and persist separately:

1. Structural T-1 base;
2. Frozen Pre-Live v2 including b2;
3. raw frozen Ridge;
4. frozen P2 governed Ridge;
5. persisted pre-outcome C1 comparator where available.

Also persist:

- latest error;
- trajectory/window error;
- b2 correction magnitude/direction;
- Ridge correction magnitude;
- P2 reliability trajectory;
- data-quality warnings;
- whether each component improved or worsened the previous layer.

Do not silently add new event outcomes to training.

## Reopening / retraining rule

A new model/policy version may begin only when materially more independent prospective evidence establishes a specific failure hypothesis.

Potential hypothesis to monitor, not yet tune:

`b2 negative same-season residual correction may overreact on high-demand Lech matches.`

Event 5 alone is insufficient evidence.

## Chronos / TSFM

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the exposed development/holdout set.

## Frozen C1 v8

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Keep unchanged as prospective comparator.

## Production boundary

Production remains:

`live_adjustment = 0`

No production promotion from one holdout.

## Non-negotiable CI/CD

`code -> tests -> CI -> artifact -> hashes -> result doc -> decision -> canonical docs`

## One-line instruction

> **Event 5 is complete and may never be used for silent retuning. Keep `d2-stage2-p2-observation-maturity-2026-10-19-v1` frozen, score future completed events append-only with component-level diagnostics, monitor the b2 failure signal, and only open a new versioned challenger after materially more independent prospective evidence. Production remains unchanged.**
