# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — canonical accuracy-first development rules;
3. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — current forecasting state;
4. [`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`](ml/D2_PROSPECTIVE_ACCUMULATION_V1.md) — active scheduled prospective scoring/readiness contract;
5. [`ml/results/D2_PROSPECTIVE_READINESS_V1_2026-10-19.md`](ml/results/D2_PROSPECTIVE_READINESS_V1_2026-10-19.md) — canonical tracked-event readiness snapshot and evidence classes;
6. [`ml/results/D2_PROSPECTIVE_SCORE_V1_INITIAL_2026-10-19.md`](ml/results/D2_PROSPECTIVE_SCORE_V1_INITIAL_2026-10-19.md) — first green prospective scorer run;
7. [`ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`](ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md) — first chronological d2 holdout;
8. [`ml/artifacts/d2_event5_holdout_v1/manifest.json`](ml/artifacts/d2_event5_holdout_v1/manifest.json) — canonical holdout evidence manifest;
9. [`ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`](ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md) — frozen Stage-2 result;
10. [`ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`](ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json) — frozen d2 candidate;
11. [`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`](ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md) — Stage-1 expert evidence;
12. [`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json) — sealed Pre-Live v2 lineage;
13. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — canonical roadmap;
14. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — live-engine roadmap;
15. [`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`](ml/C1_V8_PROSPECTIVE_SHADOW_V1.md) — frozen C1 comparator;
16. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Do not use a new outcome to rescue, retune or redefine an already-frozen model or policy.

## Canonical architecture

Frozen Pre-Live v2:

`history + proven current-season regime -> frozen pre-live anchor`

Frozen live candidate:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

Frozen components:

- Pre-Live v2: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- Stage-1 expert: `ridge-a10`;
- Stage-2 policy: `P2-observation-maturity`;
- d2 package: `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

## Current development state

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> Stage 1 FROZEN -> Stage 2 FROZEN -> EVENT 5 HOLDOUT COMPLETE -> PROSPECTIVE ACCUMULATION + READINESS ACTIVE / SCHEDULED`

Production remains unchanged:

`live_adjustment = 0`

## First chronological holdout — event 5

Event:

- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 canonical final-24h d2 rows.

Event 5 was excluded from Stage-1 training/selection and Stage-2 policy selection.

Canonical run:

`39310995137`

Artifact ID:

`12215538287`

Artifact ZIP SHA256:

`2857f1cb8a0bff9b0cac41bc36520ae840df91ef1400d0b6c4c7b90938b9c867`

### Holdout scorecard

| Forecast | Latest error | Window MAE |
|---|---:|---:|
| Frozen Pre-Live v2 | 9,832.52 | 9,832.52 |
| **Raw frozen Ridge** | **6,652.81** | **6,170.35** |
| Frozen P2 governed Ridge | **6,652.81** | 7,263.16 |
| persisted C1 v8 PRIOR/policy | 7,669.07 | 7,669.07* |

`*` C1 and d2 window sampling differ slightly; latest-row comparison is directly aligned.

D2 latest-error reduction vs Frozen v2:

**3,179.71 seats / 32.34%**

Raw Ridge window-MAE reduction vs Frozen v2:

**3,662.17 seats / 37.24%**

P2 window-MAE reduction vs Frozen v2:

**2,569.36 seats / 26.13%**

D2 latest error beats the persisted C1 v8 policy by:

**1,016.26 seats**

## Important prospective diagnostic: b2

Underlying Structural T-1 base:

`29,737.93`

Frozen Pre-Live v2 after b2:

`27,574.48`

b2 correction:

`-2,163.45 seats`

Against the actual `37,407` attendance:

- Structural T-1 base error: `7,669.07`;
- Frozen Pre-Live v2 error: `9,832.52`.

So on this first fresh holdout, b2 moved the pre-live anchor in the wrong direction and worsened the error by `2,163.45 seats`.

This is a **warning to monitor prospectively, not permission to retune from one event**.

## Stage-2 P2 behavior on the holdout

P2 reliability stayed frozen:

- observation 1 -> `0.25`;
- observation 2 -> `0.60`;
- observation 3+ -> `1.00`, subject to the frozen time cap.

On event 5 P2 was conservative early and therefore had worse window MAE than raw Ridge, but at the mature final observation reliability was `1.0`, so P2 and Ridge produced the same latest forecast.

No P2 changes are allowed from this result.

## Active phase — prospective accumulation + readiness

Operational workflow:

`.github/workflows/d2-prospective-score-v1.yml`

It now contains two deliberately separate data contracts:

1. frozen `v7-*` exports for model scoring/reconstruction;
2. additive `d2-readiness` feed for tracked-event readiness and missing-truth visibility.

The additive readiness feed does **not** change the frozen scoring exports and never estimates attendance from ticket inventory.

Canonical readiness run:

- run `39322049864`;
- main SHA `1c56d81f12da2a67981fe8063461df6b5612f96c`;
- artifact ID `12219724931`;
- artifact ZIP SHA256 `3a5978c1c76d5012e7e8a4d124730c4aae452e9968c0fe2d2463cc48a207f964`;
- readiness feed: **21 tracked Ekstraklasa events**;
- frozen scorer: still `10 events / 34 live rows`;
- frozen model-scoring status: `NO_NEW_ELIGIBLE_EVENTS`.

### Readiness evidence classes

Frozen Stage-2 cutoff:

`2026-10-19T19:11:01Z`

- `DELAYED_LABEL_HOLDOUT`: kickoff at/before cutoff. Useful diagnostic evidence after truth arrives, but does **not** count as genuine forward promotion evidence.
- `TRUE_POST_FREEZE_PROSPECTIVE`: kickoff after cutoff. This is the only class that may count toward production-promotion sample requirements.

Never combine these classes into one headline prospective sample size.

### Completed events currently blocked on trusted attendance outcome

| Event | Match | Final-24h snapshots | Evidence class |
|---|---|---:|---|
| 15 | GKS Katowice vs Pogoń Szczecin | 96 | delayed-label |
| 18 | Cracovia vs Legia Warszawa | 51 | delayed-label |
| 11 | Górnik Zabrze vs Piast Gliwice | 96 | delayed-label |
| 19 | KGHM Zagłębie Lubin vs Jagiellonia Białystok | 96 | delayed-label |
| 20 | Wisła Płock vs Radomiak Radom | 96 | delayed-label |

All five are currently `BLOCKED_MISSING_OUTCOME`. Do not derive the truth label from inventory.

### First tracked true post-freeze events

- event 10 — Pogoń Szczecin vs Radomiak Radom — 24 Oct;
- event 16 — Wisła Kraków vs Raków Częstochowa — 24 Oct;
- event 23 — Śląsk Wrocław vs Wieczysta Kraków — 25 Oct;
- event 21 — Jagiellonia Białystok vs Wisła Płock — 25 Oct;
- event 22 — Legia Warszawa vs Lech Poznań — 25 Oct;
- event 6 — Lech Poznań vs Wisła Kraków — 31 Oct.

At the canonical readiness snapshot they are correctly `FUTURE_NOT_DUE`.

## Trusted outcome pipeline

The outcome sync is already deployed and runs hourly at minute `17`.

It only accepts trusted rows from `ml_home_attendance_history_v2`, matched exactly by club + kickoff, after a 3-hour post-match grace period, and never overwrites an existing outcome.

If a completed event remains `BLOCKED_MISSING_OUTCOME`, the correct next action is to improve/restore trusted truth-source coverage — not estimate attendance from the seat map.

## Prospective scoring governance

The scorer is evidence-only. It does **not**:

- add prospective outcomes to Ridge training;
- retune P2;
- update the registry automatically;
- commit model state;
- promote production.

When a new completed eligible event appears, the workflow scores it under the frozen package and uploads immutable evidence. A separate reviewed evidence cycle must persist the result and register the event as exposed.

For every new event preserve separate diagnostics for:

1. Structural T-1 base;
2. Frozen Pre-Live v2 / b2;
3. raw frozen `ridge-a10`;
4. frozen P2 governed Ridge;
5. persisted C1 comparator where genuine pre-outcome evidence exists.

Do not silently add new outcomes to training.

A new b2/Ridge/P2 challenger or retraining cycle may begin only as a separately versioned experiment after materially more independent evidence supports a specific failure hypothesis.

## Chronos / TSFM

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same exposed development/holdout evidence.

## Production boundary

No production promotion follows from one holdout or from delayed-label evidence.

Frozen Pre-Live v2, Ridge and P2 remain research components.

Frozen C1 v8 remains unchanged.

`live_adjustment = 0`

## Engineering rule

> **A holdout validates a frozen decision; it does not become tuning data retroactively. Only true post-freeze events count as genuine forward evidence.**
