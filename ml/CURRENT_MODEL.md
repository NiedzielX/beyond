# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-19**

This is the canonical short-form model state.

Read first in a cold session:

1. `AI_BOOTSTRAP.md`;
2. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
3. this file;
4. `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
5. `ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`;
6. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
7. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Current architecture:

`history + current-season regime -> Frozen Pre-Live v2`

then:

`Frozen Pre-Live v2 + P2 reliability * frozen Ridge live residual -> d2 forecast`

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> d2 Stage 1 DONE -> d2 Stage 2 FROZEN -> EVENT 5 HOLDOUT ACTIVE`

Current active workstream:

**One-pass chronological holdout evaluation on event 5 Lech Poznań–Korona Kielce.**

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

No research candidate below is an automatic production promotion.

---

# Frozen Pre-Live v2 historical candidate

Status: **SEALED / REPRODUCIBLE / HISTORICAL CANDIDATE ONLY**.

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Canonical manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

Frozen contract:

| Horizon | Historical base | b2 regime | c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,691.40** |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | **1,682.63** |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,661.52** |

Freeze gate reproduces 20/20 horizon-season MAE cells exactly at tolerance `1e-9`.

---

# Historical workstreams

## a2 — CLOSED FOR CURRENT HISTORICAL DATA

Final historical bases:

- T-30: Structural Prior;
- T-14: Structural Prior;
- T-7: `hist31-leaf20-l2-1`;
- T-3: Structural Prior;
- T-1: Structural Prior.

T-7 fixed audit improves 4/4 rolling folds, mean **+104.66 MAE**.

## b2 — CLOSED / FROZEN INTO PRE-LIVE V2

Same-season own-model residual regime is frozen for T-7/T-3/T-1 and activates only after at least 3 earlier completed same-season home matches.

Four-fold mean gains:

- T-7: **+51.47**;
- T-3: **+70.44**;
- T-1: **+69.54**.

## c2 historical — CLOSED FOR CURRENT DATA

Historical contract:

`NO_CONTEXT_ALL_HORIZONS`

No tested c2 extension survived the frozen protocol. Forward-only rivalry, verified absences and hype/media remain prospective research.

---

# d2 Stage 0 — COMPLETE

Status:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

Development lineage:

- 9 events;
- 30 final-24h rows;
- exact Frozen-v2 anchor on every row.

Diagnostic event MAE on this replay set:

- legacy Structural Prior: `3968.73`;
- Frozen Pre-Live v2: `4128.01`.

---

# d2 Stage 1 — COMPLETE / FROZEN EXPERT

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Frozen expert:

`ridge-a10`

Contract:

- target: `target_live_delta_occupancy`;
- Ridge `alpha=10.0`;
- median imputation within train fold;
- missing indicators;
- standardization;
- event-balanced weights;
- event-level LOEO;
- raw correction capped at +/-10pp occupancy.

Stage-1 development metrics:

| Metric | Frozen v2 | Ridge | Improvement |
|---|---:|---:|---:|
| Latest-row MAE | 4,128.01 | **3,320.39** | **+807.62 / 19.56%** |
| Window MAE | 4,128.01 | **3,619.19** | **+508.83 / 12.33%** |

Worst latest-event degradation:

`+4326.90 seats`

---

# d2 Stage 2 — COMPLETE / FROZEN

Canonical result:

`ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`

Frozen manifest:

`ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`

Frozen package ID:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Selected policy:

`P2-observation-maturity`

Canonical run:

`39308629738`

Artifact ID:

`12214478156`

Artifact ZIP SHA256:

`b4ae9183f398a8cd13542390ce05734f050697e903d34242d793b28854bf9296`

## P2 metrics

| Metric | Frozen v2 | Raw Ridge | Frozen P2 |
|---|---:|---:|---:|
| Latest-row MAE | 4,128.01 | 3,320.39 | **3,240.99** |
| Window MAE | 4,128.01 | **3,619.19** | 3,657.65 |
| Worst latest-event degradation | 0 | 4,326.90 | **1,081.72** |
| p90 latest-event degradation | 0 | 1,683.09 | **1,034.05** |

P2:

- improves latest MAE vs Frozen v2 by **887.02 seats / 21.49%**;
- improves latest MAE vs raw Ridge by another **79.40 seats / 2.39%**;
- retains **92.44%** of raw Ridge window uplift;
- reduces worst latest-event degradation by **75%**;
- is the only policy passing all predeclared gates.

## Frozen reliability policy

Observation-index reliability:

- observation 1: `0.25`;
- observation 2: `0.60`;
- observation 3+: `1.00`.

Time-to-kickoff cap:

- >18h: `0.75`;
- >12h and <=18h: `0.90`;
- <=12h: `1.00`.

Final:

`reliability = min(observation_index_weight, time_weight)`

Do not retune this policy on event 5.

---

# Chronos / TSFM

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Chronos-2 and Bolt-small improved Frozen v2 but lost to plain Ridge. Do not fine-tune or add Lag-Llama/NeuralProphet on the same exposed development lineage.

---

# Reserved chronological holdout — ACTIVE

Event:

- ID `5`;
- **Lech Poznań vs Korona Kielce**;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 final-24h live rows.

This event was excluded from Stage-1 and Stage-2 selection.

Score once:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen P2 governed Ridge;
4. frozen C1 v8 where contract-compatible.

No retuning after opening the holdout.

---

# Relationship to frozen C1 v8

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Keep unchanged as comparator.

---

# Post-holdout roadmap

After event 5:

- persist the result regardless of outcome;
- keep the d2 package frozen during the prospective evidence window;
- score each new eligible completed event append-only;
- do not silently retrain on new outcomes;
- start a separately versioned retraining cycle only when materially more independent events exist;
- require more genuinely prospective evidence before production promotion.

---

# Engineering governance

Non-negotiable:

- event is the independent evaluation unit;
- strict PIT semantics;
- no random snapshot split;
- exact model/policy/data versions;
- code + tests + CI + artifact + result doc + decision;
- no silent retuning;
- a holdout validates a frozen package and does not become tuning data retroactively;
- CI green != production promotion.

## Current development decision

**Stage 2 is frozen as `d2-stage2-p2-observation-maturity-2026-10-19-v1`. Score event 5 exactly once, persist the result without retuning, then continue append-only prospective validation. Production and C1 v8 remain unchanged.**
