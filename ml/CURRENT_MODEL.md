# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-19**

This is the canonical short-form model state.

Read first in a cold session:

1. `AI_BOOTSTRAP.md`;
2. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
3. this file;
4. `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
5. `ml/results/D2_PROSPECTIVE_SCORE_V1_INITIAL_2026-10-19.md`;
6. `ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`;
7. `ml/artifacts/d2_event5_holdout_v1/manifest.json`;
8. `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
9. `ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`;
10. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
11. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Current architecture:

`history + current-season regime -> Frozen Pre-Live v2`

then:

`Frozen Pre-Live v2 + P2 reliability * frozen Ridge live residual -> d2 forecast`

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> Stage 1 FROZEN -> Stage 2 FROZEN -> EVENT 5 HOLDOUT COMPLETE -> PROSPECTIVE ACCUMULATION ACTIVE / SCHEDULED`

Current active workstream:

**Frozen scheduled prospective scoring on new independent completed events with component-level diagnostics.**

---

# Production boundary

Production Structural Prior remains unchanged:

| Horizon | Production runtime | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | 1,889.4 | 1,846.3 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | 1,748.5 | 1,870.4 |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | 1,777.7 | 1,802.3 |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | 1,661.7 | 1,775.1 |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | 1,651.7 | 1,742.8 |

Production bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

No research evidence below is an automatic production promotion.

---

# Frozen Pre-Live v2

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Historical contract:

| Horizon | Historical base | b2 regime | c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,691.40** |
| T-3 | Structural Prior | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | **1,682.63** |
| T-1 | Structural Prior | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,661.52** |

Freeze reproduces 20/20 historical horizon-season cells exactly at tolerance `1e-9`.

Historical a2/b2/c2 remain closed for the currently exposed historical dataset.

---

# Frozen d2 package

## Stage 1 expert

`ridge-a10`

Frozen contract:

- target `target_live_delta_occupancy`;
- Ridge `alpha=10.0`;
- median imputation within training fold;
- missing indicators;
- standardization;
- event-balanced weights;
- event-level LOEO development;
- raw correction capped at +/-10pp occupancy.

Development latest MAE:

`3320.39` vs Frozen-v2 `4128.01`

Development worst latest-event degradation:

`4326.90 seats`

## Stage 2 policy

Frozen package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Policy:

`P2-observation-maturity`

Reliability:

- observation 1 -> `0.25`;
- observation 2 -> `0.60`;
- observation 3+ -> `1.00`;
- >18h time cap `0.75`;
- >12h <=18h cap `0.90`;
- <=12h cap `1.00`;
- final reliability = minimum of observation and time weights.

Stage-2 development result:

| Metric | Frozen v2 | Raw Ridge | P2 |
|---|---:|---:|---:|
| Latest MAE | 4,128.01 | 3,320.39 | **3,240.99** |
| Window MAE | 4,128.01 | **3,619.19** | 3,657.65 |
| Worst degradation | 0 | 4,326.90 | **1,081.72** |

P2 was the only policy passing all predeclared Stage-2 gates.

Do not retune Ridge or P2 from event 5.

---

# First chronological holdout — COMPLETE

Canonical result:

`ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`

Manifest:

`ml/artifacts/d2_event5_holdout_v1/manifest.json`

Run:

`39310995137`

Artifact ID:

`12215538287`

Artifact ZIP SHA256:

`2857f1cb8a0bff9b0cac41bc36520ae840df91ef1400d0b6c4c7b90938b9c867`

Event:

**Lech Poznań vs Korona Kielce**, actual attendance `37,407`.

Event 5 was absent from Stage-1 training/selection and Stage-2 policy selection.

## Holdout errors

| Forecast | Latest error | Window MAE |
|---|---:|---:|
| Frozen Pre-Live v2 | 9,832.52 | 9,832.52 |
| **Raw frozen Ridge** | **6,652.81** | **6,170.35** |
| Frozen P2 governed Ridge | **6,652.81** | 7,263.16 |
| Persisted C1 v8 PRIOR/policy | 7,669.07 | 7,669.07* |

`*` C1 and d2 window sampling are not identical; latest-row comparison is directly aligned.

D2 latest improvement vs Frozen v2:

`+3179.71 seats / 32.34%`

D2 latest improvement vs persisted C1 v8 policy:

`+1016.26 seats`

Raw Ridge window improvement vs Frozen v2:

`+3662.17 seats / 37.24%`

P2 window improvement vs Frozen v2:

`+2569.36 seats / 26.13%`

## P2 behavior on event 5

P2 shrank the first two Ridge corrections:

- obs1 reliability `0.25`;
- obs2 `0.60`.

At obs3 and obs4 reliability = `1.0`, so final P2 equals raw Ridge.

On this event the conservative early shrinkage worsened trajectory-window MAE relative to raw Ridge, but still materially improved Frozen v2.

This does not reopen P2 tuning.

---

# Fresh prospective b2 warning

Event-5 Structural T-1 base:

`29737.93`

Frozen Pre-Live v2 after b2:

`27574.48`

b2 correction:

`-2163.45 seats`

Actual attendance:

`37407`

Errors:

- Structural base: `7669.07`;
- Frozen Pre-Live v2: `9832.52`.

So on the first fresh holdout b2 worsened the pre-live anchor by `2163.45 seats`.

Current status of this observation:

`PROSPECTIVE_FAILURE_SIGNAL_ONLY`

Do not retune or reopen b2 from one event.

Potential hypothesis to monitor prospectively:

> **The same-season residual layer may overreact negatively for some high-demand Lech matches.**

Only if this repeats across materially more independent events may a new separately versioned b2/Pre-Live challenger be opened.

---

# Chronos / TSFM

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama/NeuralProphet on the exposed development/holdout evidence.

---

# Frozen C1 v8

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Event-5 prospective persisted decision:

`PRIOR / insufficient_disagreement`

Keep C1 v8 unchanged as comparator.

---

# Prospective scorer — ACTIVE / SCHEDULED

Contract:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

Workflow:

`.github/workflows/d2-prospective-score-v1.yml`

Registry:

`ml/artifacts/d2_prospective_registry_v1.json`

Schedule:

`05:23 UTC daily`

Initial end-to-end evidence:

- run `39312944826`;
- main SHA `5ce2e8e7bfd5b197510108f441c11a75257fd0c8`;
- artifact ID `12215847975`;
- artifact ZIP SHA256 `ca470b8f18eddabb8c9f4664baff75a776bb6e64d3e50379f6836c22f3b795cc`;
- exporter state `10 events / 34 live rows`;
- result `NO_NEW_ELIGIBLE_EVENTS`;
- new candidate IDs `[]`;
- blocked IDs `[]`.

This proves operationally that:

- frozen Ridge training remains exact 9/30;
- event 5 is registry-protected and not re-used as unseen;
- prospective outcomes never enter Ridge training automatically;
- P2 is not retuned;
- no-new-event runs are valid green runs;
- evidence artifacts and hashes are produced.

The workflow is evidence-only and has read-only repository contents permission. It cannot commit, mutate the registry, retrain or promote production automatically.

A newly scored event must be reviewed/persisted in a separate evidence cycle and explicitly registered as exposed.

---

# Active next phase — frozen prospective accumulation

For every new eligible completed event, score without retraining:

1. Structural T-1 base;
2. Frozen Pre-Live v2 including b2;
3. raw frozen Ridge;
4. frozen P2 governed Ridge;
5. persisted pre-outcome C1 comparator where available.

Persist at event and trajectory level:

- latest/window errors;
- component-by-component incremental error change;
- b2 correction direction/magnitude;
- Ridge correction direction/magnitude;
- P2 reliability trajectory;
- data-quality warnings;
- source/run/artifact lineage.

Do not fold future event outcomes into training until a separately versioned retraining cycle is explicitly declared.

---

# Reopening / retraining boundary

A new challenger cycle requires materially more independent prospective evidence supporting a specific failure hypothesis.

One positive or negative event is insufficient.

Production promotion also requires materially more independent prospective events and acceptable aggregate/tail behavior.

## Current development decision

**Keep `d2-stage2-p2-observation-maturity-2026-10-19-v1` frozen. The scheduled prospective scorer is active and currently has no new eligible event beyond registered event 5. Review/persist each future scored event separately, keep component diagnostics, and do not change b2/Ridge/P2 until a separately versioned evidence-based cycle is justified. Production remains unchanged.**
