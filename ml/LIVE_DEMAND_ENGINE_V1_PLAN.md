# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-19**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector / Price-area Decision Support MVP: IMPLEMENTED**  
> **Pre-Live v2 historical candidate: FROZEN + SEALED**  
> **d2 Stage 0: DONE**  
> **d2 Stage 1: DONE / ridge-a10 FROZEN**  
> **d2 Stage 2: DONE / P2-observation-maturity FROZEN**  
> **d2 Event 5 chronological holdout: COMPLETE**  
> **d2 prospective accumulation: ACTIVE**

Canonical documents:

- `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
- `ml/CURRENT_MODEL.md`;
- `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
- `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
- `ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`;
- `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
- `AI_BOOTSTRAP.md`.

## Frozen architecture

Pre-live:

`history + proven current-season regime -> Frozen Pre-Live v2`

Live:

`final_forecast(t) = frozen_pre_live_v2(t) + P2_reliability(t) * ridge_delta(t)`

Frozen IDs:

- Pre-Live v2: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- Stage-1 expert: `ridge-a10`;
- Stage-2 package: `d2-stage2-p2-observation-maturity-2026-10-19-v1`;
- Stage-2 policy: `P2-observation-maturity`.

## Production boundary

Production remains:

`live_adjustment = 0`

Structural Prior remains production incumbent.

Frozen Pre-Live v2 and d2 are research candidates.

Frozen C1 v8 remains:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Do not retune C1 v8 as part of d2.

---

# d2 Stage 0 — COMPLETE

Exact Frozen-v2 compatibility established on:

- 9 events;
- 30 final-24h rows;
- exact frozen anchor lineage.

Status:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

---

# d2 Stage 1 — COMPLETE / FROZEN

Expert:

`ridge-a10`

Frozen contract:

- target `target_live_delta_occupancy`;
- Ridge alpha `10.0`;
- median imputation inside training fold;
- missing indicators;
- standardization;
- event-balanced weights;
- raw correction cap +/-10pp occupancy.

Development:

- Frozen-v2 latest MAE `4128.01`;
- Ridge latest MAE `3320.39`;
- Ridge window MAE `3619.19`;
- worst degradation `4326.90`.

Chronos-2 / Bolt-small did not improve plain Ridge.

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

---

# d2 Stage 2 — COMPLETE / FROZEN

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Policy:

`P2-observation-maturity`

Frozen reliability:

- observation 1 `0.25`;
- observation 2 `0.60`;
- observation 3+ `1.00`;
- >18h cap `0.75`;
- >12h <=18h cap `0.90`;
- <=12h cap `1.00`.

Development result:

- latest MAE `3240.99`;
- latest uplift vs Frozen `887.02 / 21.49%`;
- window MAE `3657.65`;
- worst degradation `1081.72`;
- 75% reduction in worst degradation vs raw Ridge.

Only P2 passed all predeclared gates.

---

# Event 5 first chronological holdout — COMPLETE

Canonical result:

`ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`

Run:

`39310995137`

Artifact ID:

`12215538287`

Event:

Lech Poznań vs Korona Kielce, actual `37,407`.

## Holdout layer scorecard

| Layer | Latest error | Window MAE |
|---|---:|---:|
| Structural T-1 base | 7,669.07 | n/a |
| Frozen Pre-Live v2 | 9,832.52 | 9,832.52 |
| **Raw frozen Ridge** | **6,652.81** | **6,170.35** |
| Frozen P2 | **6,652.81** | 7,263.16 |
| persisted C1 v8 policy | 7,669.07 | 7,669.07* |

`*` C1 window sampling differs slightly from canonical d2 final-24h rows.

D2 latest improvement vs Frozen v2:

`3179.71 seats / 32.34%`

D2 latest improvement vs persisted C1 v8 policy:

`1016.26 seats`

## Holdout interpretation

Positive:

- the live Ridge layer materially corrected a severe Pre-Live v2 miss;
- frozen d2 latest outperformed the persisted C1 v8 decision on this event;
- P2 reached reliability `1.0` on mature observations as designed.

Risk/diagnostic:

- final d2 still underpredicted by `6652.81 seats`;
- P2's early conservatism worsened trajectory-window MAE versus raw Ridge on this event;
- frozen b2 moved the pre-live anchor down by `2163.45 seats`, worsening its error by the same amount versus Structural T-1 base.

No tuning follows from these observations.

---

# Prospective accumulation — ACTIVE NOW

Contract:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

The live-engine workstream is now an evidence-collection system around a frozen package.

For each new eligible completed event, compute and persist:

## A. Structural base

- T-1 base p50;
- latest absolute error.

## B. Frozen Pre-Live v2 / b2

- b2 correction seats/fraction;
- prior same-season home-match count;
- Frozen-v2 p50;
- absolute error;
- incremental error change vs Structural base.

## C. Raw frozen Ridge

Per observation:

- raw predicted live delta;
- clipped/governed delta;
- revised forecast;
- absolute error.

At event level:

- latest error;
- event-balanced window MAE;
- improvement/degradation vs Frozen v2.

## D. Frozen P2

Per observation:

- observation index;
- time-to-kickoff;
- reliability;
- applied live delta;
- revised forecast;
- absolute error.

At event level:

- latest error;
- window MAE;
- incremental contribution vs raw Ridge and Frozen v2.

## E. Frozen C1 v8 comparator

Use only real persisted pre-outcome evidence.

Never reconstruct C1 after the outcome and call it prospective.

---

# Continuous-time behavior

The live engine remains continuous over time-to-kickoff.

Named T-30/T-14/T-7/T-3/T-1 points are evaluation checkpoints, not separate live-model moments.

Every meaningful forecast revision should retain:

- as-of timestamp;
- source snapshot IDs;
- Frozen-v2 lineage;
- Ridge model ID;
- P2 policy ID;
- proposed raw correction;
- P2 reliability;
- applied correction;
- forecast before/after;
- quality/release/coverage warnings.

---

# Inventory interpretation

Public availability is a proxy, not confirmed paid sales.

The live engine must distinguish where possible:

- genuine demand movement;
- ticket releases;
- sector openings/closures;
- coverage changes;
- scrape/data anomalies.

Do not interpret every decrease/increase as pure demand.

---

# Prospective failure hypotheses to monitor

## H1 — b2 negative overreaction

Event 5 signal:

- Structural T-1 base `29737.93`;
- Frozen-v2 `27574.48`;
- b2 correction `-2163.45`;
- actual `37407`.

Status:

`ONE PROSPECTIVE SIGNAL / NOT PROVEN`

Track across future events. Do not retune now.

## H2 — P2 early conservatism cost

Event 5 showed useful early Ridge corrections were shrunk by P2.

Status:

`ONE HOLDOUT OBSERVATION / NOT A SYSTEMATIC FAILURE`

Track raw Ridge vs P2 error by observation maturity prospectively.

---

# Accuracy evaluation

For every prospective event report:

- latest AE per layer;
- window MAE per live layer;
- bias;
- max live revision;
- b2 incremental effect;
- Ridge incremental effect;
- P2 incremental effect;
- reliability trajectory;
- quality warnings.

Across accumulated events report:

- mean/median latest AE;
- event-balanced window MAE;
- bias;
- p90/worst event;
- event improvement rate;
- cumulative component contribution.

---

# Reopening / retraining gate

Do not mutate the frozen package event by event.

A new versioned challenger requires:

1. materially more independent prospective events;
2. repeated interpretable failure mode;
3. hypothesis declared before tuning;
4. frozen d2 retained as benchmark;
5. new explicit train/development/forward split;
6. honest labeling of already-exposed prospective events.

---

# Production promotion

One event-5 holdout is insufficient.

Promotion requires materially more prospective evidence, positive aggregate uplift, acceptable tail risk, no unresolved systematic failure, a frozen reproducible package and explicit reviewed approval.

Until then:

`live_adjustment = 0`

## Immediate live-engine instruction

> **Keep `d2-stage2-p2-observation-maturity-2026-10-19-v1` frozen. Build/operate append-only prospective scoring for new completed events, persist Structural -> b2 -> Ridge -> P2 -> genuine C1 diagnostics separately, monitor the event-5 b2/P2 signals without tuning them, and only open a new versioned challenger after materially more independent evidence.**
