# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-18**

This is the canonical short-form model state.

Read first in a cold session:

1. `AI_BOOTSTRAP.md`;
2. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
3. this file;
4. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
5. `ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md`.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Architecture:

`history + current-season regime + context -> Pre-Live v2`

then:

`frozen Pre-Live v2 + continuous live trajectory -> d2 Continuous Live Updater`

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 ACTIVE`

Current active workstream:

**d2 — continuous live updater against frozen Pre-Live v2**.

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

No historical candidate described below is an automatic production promotion.

---

# Frozen historical Pre-Live v2 candidate

Status: **SEALED / REPRODUCIBLE / HISTORICAL CANDIDATE ONLY**.

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Canonical manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

Manifest SHA256:

`44c911d1ac8b1bf6870ed31e1a636b9b8374d8c8da2d57ba3b4fb5b4aaba4d3c`

Canonical seal evidence:

`ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md`

Seal run:

`39166115174`

Artifact ID:

`12150457295`

Artifact ZIP SHA256:

`c2b7440ae84a96c474992ecbb07c4bb43f319a9e021fc370a82f439b6edd5dd1`

Freeze gate:

- 5/5 unit tests PASS;
- historical input SHA PASS;
- **20/20 exact horizon-season MAE reproduction cells PASS at tolerance `1e-9`**;
- freshly generated manifest is byte-for-byte identical to committed manifest;
- manifest SHA lock PASS.

## Frozen per-horizon contract

| Horizon | Historical base | b2 regime | historical c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,691.40** |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | **1,682.63** |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,661.52** |

Reference mean = mean historical MAE across exposed 2024/25 and 2025/26 references.

The full-precision four-fold scorecard and all source/evidence hashes live in the canonical manifest.

---

# a2 — Historical / Structural Prior

Status: **CLOSED FOR CURRENT HISTORICAL DATA**.

Final historical base state:

- T-30: retained Structural Prior;
- T-14: retained Structural Prior;
- T-7: `hist31-leaf20-l2-1`;
- T-3: retained Structural Prior;
- T-1: retained Structural Prior.

T-7 fixed audit improves all four rolling folds, mean **+104.66 MAE** vs its production incumbent.

Unresolved-horizon multi-fold tournament retained incumbents at T-30/T-14/T-3/T-1.

Persistent cross-season club calibration was rejected under two materially different fixed formulations.

Do not restart a2 grids on the same exposed references without materially new data or hypothesis.

---

# b2 — Current-season regime

Status: **CLOSED FOR CURRENT HISTORICAL DATA / FROZEN INTO PRE-LIVE V2**.

Successful b2 hypothesis:

> use same-season actual-vs-own-model residual state to detect whether a club is currently running above/below expected demand.

Critical PIT rule:

`prior kickoff + 3h <= current forecast as_of`

Frozen policies:

- T-30: `NO_ADJUSTMENT`;
- T-14: `NO_ADJUSTMENT`;
- T-7: `ewma50-resid-k6-cap05-min3`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

All non-zero policies activate only after **3 earlier completed same-season home matches**.

Final fixed four-fold temporal audit:

| Horizon | Mean MAE improvement | Minimum fold improvement |
|---|---:|---:|
| T-7 | **+51.47** | +7.15 |
| T-3 | **+70.44** | +21.18 |
| T-1 | **+69.54** | +24.66 |

Known limitations remain explicit:

- max observed harmful event regression: **+2,760.55 seats**;
- event improvement rate is below 50% in several folds;
- club-level heterogeneity remains material;
- correction cap is +/-5% verified capacity.

Do not retune b2 against the same historical references.

---

# c2 — Historical match context

Status: **SUFFICIENTLY EVALUATED / NO HISTORICAL CONTEXT EXTENSION FROZEN**.

Canonical result:

`ml/results/CONTEXT_EXTENSION_V2_2026-10-18.md`

Context Extension v2 evaluated PIT-safe:

- sequence-aware winning/unbeaten/losing form and points acceleration;
- current-table stakes/pressure;
- sequence + stakes interaction;
- all incrementally over the frozen a2+b2 stack.

Result:

- T-30: `NO_CONTEXT`;
- T-14: `NO_CONTEXT`;
- T-7: `NO_CONTEXT`;
- T-3: `NO_CONTEXT` because folds disagreed;
- T-1: development selected `sequence_stakes`, but it worsened both references; mean reference delta **-36.97 MAE**.

Historical c2 freeze:

`NO_CONTEXT_ALL_HORIZONS`

This does not mean context has no value.

Forward-only context remains prospective research/shadow:

- verified rivalry / derby;
- verified absences;
- media attention / mention acceleration;
- future hype/search/social signals when valid sources exist.

Do not backfill those features into five-season history using later knowledge.

---

# d2 — Continuous Live Updater

Status: **ACTIVE DEVELOPMENT WORKSTREAM**.

Objective:

> learn incremental live revisions relative to the immutable frozen Pre-Live v2 candidate rather than continuing to mutate the historical baseline during live-model development.

Primary target direction:

`live_delta = actual_attendance - frozen_pre_live_v2_p50`

Capacity-normalized alternative should also be compared.

Final candidate:

`d2_p50 = frozen_pre_live_v2_p50 + predicted_live_delta`

Start with **one continuous model** using time-to-kickoff instead of fragmenting small live evidence into separate T-30/T-14/T-7/T-3/T-1 models.

## Reuse existing live/C1 infrastructure

Already available:

- public ticket inventory snapshots;
- PIT trajectory position / expected progress;
- 6h / 24h / 72h / 7d velocity where available;
- acceleration;
- sector-level trajectory aggregates;
- release / replenishment and sector-coverage diagnostics;
- Roboticket price observations;
- grouped event-level modelling/evaluation code;
- frozen C1 v8 prospective shadow pipeline.

## d2 evaluation contract

- training unit may be event x as-of timestamp;
- independent validation unit is the event;
- all rows from one event stay in one fold;
- primary small-N validation = LOEO;
- event-balanced weights or equivalent are mandatory;
- no random snapshot split;
- live features must exist at exact as-of;
- source Pre-Live prediction must identify freeze ID `pre-live-v2-historical-candidate-2026-10-18-v1` or an explicitly documented fallback;
- primary metric = event-level final attendance MAE vs frozen Pre-Live v2;
- also report median AE, bias, event improvement rate and worst-event degradation;
- continuous time-to-kickoff behavior must be reported, not only one checkpoint.

## Relationship to frozen C1 v8

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Do not silently retune or overwrite C1 v8 while d2 is developed.

C1 v8 remains useful prospective evidence and an expert/policy benchmark; d2 may reuse its data contract and infrastructure but must be versioned separately.

---

# Pre-Live / live governance boundary

The frozen historical Pre-Live v2 candidate is an immutable anchor for d2 experiments.

If a2/b2/c2 source files or evidence change, the current freeze manifest hash no longer describes that lineage and a new explicit freeze version is required.

Historical reference seasons are exposed. Fresh prospective evidence is still required before production promotion.

Production remains unchanged:

`live_adjustment = 0`

---

# Engineering governance

Full rules:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

Non-negotiable:

- MAE primary; tail and bias mandatory;
- event is independent evaluation unit;
- all state must exist at exact forecast as-of;
- no random snapshot split;
- exact data/model/feature versions;
- code + tests + CI + artifact + result doc + decision;
- hard reproduction gates where canonical values exist;
- exposed references cannot rescue development failures;
- no silent retuning;
- CI green != production promotion.

## Current development decision

**Build d2 against frozen Pre-Live v2. Keep production and C1 v8 unchanged. Continue forward-only context collection prospectively in parallel.**
