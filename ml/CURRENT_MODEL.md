# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-19**

This is the canonical short-form model state.

Read first in a cold session:

1. `AI_BOOTSTRAP.md`;
2. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
3. this file;
4. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
5. `ml/D2_STAGE2_RELIABILITY_GATING_V1.md`;
6. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
7. `ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md`.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Current architecture:

`history + current-season regime -> Frozen Pre-Live v2`

then:

`Frozen Pre-Live v2 + reliability * frozen Ridge live residual -> d2 forecast`

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> d2 Stage 1 DONE -> d2 Stage 2 ACTIVE`

Current active workstream:

**d2 Stage 2 — reliability / tail-risk governance around the frozen Stage-1 Ridge research lead.**

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

Do not reopen on the same exposed references without materially new data or hypothesis.

## b2 — CLOSED / FROZEN INTO PRE-LIVE V2

Same-season own-model residual regime is frozen for T-7/T-3/T-1 and activates only after at least 3 earlier completed same-season home matches.

Four-fold mean gains:

- T-7: **+51.47**;
- T-3: **+70.44**;
- T-1: **+69.54**.

Known max harmful historical event regression: **+2,760.55 seats**.

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

Diagnostic event-level anchor MAE on this specific replay set:

- legacy Structural Prior: `3968.73`;
- Frozen Pre-Live v2: `4128.01`.

This small live-specific comparison does not reopen historical b2.

---

# d2 Stage 1 — COMPLETE

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Research lead:

`ridge-a10`

Frozen Stage-1 model contract:

- target: `target_live_delta_occupancy`;
- Ridge `alpha=10.0`;
- numeric live features from existing PIT-safe C1/d2 contract;
- median imputation within training fold;
- missing indicators;
- standardization;
- event-balanced sample weights;
- final raw correction clipped to +/-10pp occupancy;
- event-level LOEO selection.

## Stage-1 metrics

| Metric | Frozen v2 | Ridge | Improvement |
|---|---:|---:|---:|
| Latest-row MAE | 4,128.01 | **3,320.39** | **+807.62 / 19.56%** |
| Event-balanced window MAE | 4,128.01 | **3,619.19** | **+508.83 / 12.33%** |

Latest event improvement rate:

`6/9 = 66.7%`

Mean absolute revision:

`1,737.45 seats`

Critical risk:

`worst latest-event degradation = +4,326.90 seats`

Interpretation:

> Stage 1 proves useful live signal, but raw Ridge is not safe enough for promotion because tail risk remains large.

Canonical run:

`39256585339`

Artifact ID:

`12187853899`

Artifact ZIP SHA256:

`c494ba609f3c9ee376e8285a9af975cc78d813337bd219fbaf94c7a9a336c6de`

---

# Chronos / Time-Series Foundation Models

Stage 1 tested zero-shot:

- `amazon/chronos-2`;
- `amazon/chronos-bolt-small`.

Both used only causal public `available_share_of_capacity` trajectory as TSFM input. Final attendance never entered the TSFM context.

Latest MAE:

- plain Ridge: **3,320.39**;
- Ridge + Chronos-2: 3,428.25;
- Ridge + Bolt-small: 3,428.08.

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Close this Stage-1 challenger. Do not fine-tune Chronos or add Lag-Llama/NeuralProphet on the same 9-event development lineage.

---

# d2 Stage 2 — ACTIVE

Canonical contract:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

Objective:

> **Keep a meaningful share of Ridge's average MAE uplift while materially reducing worst-event degradation.**

Preferred architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

Stage 2 governs the frozen Ridge expert. It does not retune Ridge itself.

Allowed compact policy families:

1. Frozen-v2 only;
2. raw Ridge;
3. observation-maturity gate;
4. disagreement/correction-magnitude shrinkage;
5. data-quality gate;
6. compact combined reliability policy.

Candidate reliability signals must be PIT-safe and may include:

- observation count / span;
- hours to kickoff;
- trajectory stability;
- velocity / acceleration;
- Ridge/Frozen-v2 disagreement;
- proposed correction magnitude;
- release/replenishment flags;
- coverage-change flags;
- unexplained inventory increases;
- data gaps / signal-quality state.

Stage-2 development boundary remains exactly the original 9 events / 30 rows.

---

# Reserved chronological holdout — event 5

New append-only completed event:

- ID: `5`;
- match: **Lech Poznań vs Korona Kielce**;
- kickoff: `2026-10-18T15:30:00Z`;
- actual attendance: `37,407`;
- capacity: `43,269`;
- final-24h live rows: `4`.

This event was excluded from Stage-1 selection.

Mandatory governance:

> **Do not use event 5 to choose Stage-2 thresholds, features or policy. Freeze Stage 2 first, then score event 5 once.**

After freeze, compare on event 5:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen Stage-2 governed Ridge;
4. frozen C1 v8 where compatible.

No retuning after opening the holdout.

---

# Relationship to frozen C1 v8

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Keep C1 v8 frozen. It remains a prospective comparator and infrastructure source, not a model to silently retune into d2.

---

# Post-holdout roadmap

After event 5:

- persist the result regardless of outcome;
- score the frozen d2 candidate on each new eligible completed event;
- keep prospective evidence append-only;
- do not silently retrain using new outcomes;
- start a separately versioned retraining cycle only when enough independent events exist;
- require materially more prospective evidence before production promotion.

---

# Engineering governance

Full rules:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

Non-negotiable:

- MAE primary, tail and bias mandatory;
- event is independent evaluation unit;
- strict PIT semantics;
- no random snapshot split;
- exact model/feature/policy/data versions;
- code + tests + CI + artifact + result doc + decision;
- no silent retuning;
- new holdouts validate frozen decisions and do not become tuning data retroactively;
- CI green != production promotion.

## Current development decision

**Freeze Stage-1 `ridge-a10`. Build Stage-2 reliability/tail-risk governance only on the original 9-event/30-row development set. Do not tune on Lech–Korona event 5. Freeze Stage 2 first, then score event 5 once. Keep production and C1 v8 unchanged.**
