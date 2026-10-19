# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-19**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering it.

## Cold-start rule

Read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
2. `ml/CURRENT_MODEL.md`;
3. `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
4. `ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`;
5. `ml/D2_STAGE2_RELIABILITY_GATING_V1.md`;
6. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
7. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
8. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
9. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
10. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
11. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

> **Score reserved event 5 Lech Poznań–Korona Kielce exactly once against the now-frozen d2 package. Do not retune anything after opening the holdout.**

## Canonical sequence

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> d2 Stage 1 DONE -> d2 Stage 2 FROZEN -> EVENT 5 HOLDOUT ACTIVE`

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

## Historical workstreams

### a2

`CLOSED FOR CURRENT HISTORICAL DATA`

T-7 historical base:

`hist31-leaf20-l2-1`

### b2

`CLOSED / FROZEN INTO PRE-LIVE V2`

Frozen non-zero policies:

- T-7: `ewma50-resid-k6-cap05-min3`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

### c2 historical

`SUFFICIENTLY EVALUATED / NO HISTORICAL CONTEXT EXTENSION`

Historical contract:

`NO_CONTEXT_ALL_HORIZONS`

Do not reopen a2/b2/c2 on the same exposed evidence without materially new data or hypothesis.

## d2 Stage 1 — FROZEN EXPERT

Research expert:

`ridge-a10`

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Development metrics:

- Frozen-v2 latest MAE: `4128.01`;
- Ridge latest MAE: `3320.39`;
- latest improvement: `807.62 seats / 19.56%`;
- window MAE: `3619.19`;
- worst latest-event degradation: `4326.90 seats`.

## d2 Stage 2 — FROZEN

Canonical result:

`ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`

Frozen manifest:

`ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`

Canonical run:

`39308629738`

Artifact ID:

`12214478156`

Selected policy:

`P2-observation-maturity`

Key metrics:

- latest MAE: **`3240.99`**;
- latest improvement vs Frozen v2: **`887.02 seats / 21.49%`**;
- window MAE: `3657.65`;
- window improvement vs Frozen v2: `470.36 seats / 11.39%`;
- worst latest-event degradation: **`1081.72 seats`**;
- worst degradation reduction vs raw Ridge: **75%**;
- retained raw-Ridge window uplift: **92.44%**.

Only P2 passed the frozen 50% latest / 50% window / 25% tail-reduction gates.

## Frozen P2 contract

Observation index:

- observation 1 -> reliability `0.25`;
- observation 2 -> `0.60`;
- observation 3+ -> `1.00`.

Time cap:

- >18h -> `0.75`;
- >12h and <=18h -> `0.90`;
- <=12h -> `1.00`.

Final reliability:

`min(observation_index_weight, time_weight)`

Do not change these thresholds during holdout evaluation.

## Chronos / TSFM

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same exposed Stage-1/Stage-2 data.

## Reserved holdout — ACTIVE NOW

Event:

- ID `5`;
- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 final-24h live rows.

This event was excluded from Stage-1 and Stage-2 selection.

Score exactly once:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen P2 governed Ridge;
4. frozen C1 v8 where contract-compatible.

Persist the result regardless of outcome.

**No threshold, feature, alpha, cap, or policy change after opening event 5.**

## After event 5

- keep the d2 package frozen;
- continue append-only prospective scoring on new completed events;
- do not silently retrain with new outcomes;
- create a separately versioned retraining cycle only when justified by materially more independent events;
- require more prospective evidence before production promotion.

## Frozen C1 v8

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Keep unchanged as comparator.

## Production boundary

Production remains:

`live_adjustment = 0`

No Stage-1/Stage-2/holdout result automatically changes production.

## Non-negotiable CI/CD

`code -> tests -> CI -> artifact -> hashes -> result doc -> decision -> canonical docs`

A holdout validates a frozen decision; it never becomes tuning data retroactively.

## One-line instruction

> **Stage 2 is frozen as `d2-stage2-p2-observation-maturity-2026-10-19-v1`. Open event 5 once, score Frozen v2 vs raw Ridge vs frozen P2 (and C1 v8 where compatible), persist the result without retuning, then continue prospective append-only evidence collection. Keep production unchanged.**
