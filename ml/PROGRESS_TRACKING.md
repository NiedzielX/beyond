# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-21**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

This file answers three questions for every new session:

1. **Where are we now?**
2. **What is frozen and must not be retuned?**
3. **What is the next active work?**

Canonical detailed state remains in `ml/CURRENT_MODEL.md`. This tracker is the concise execution view.

---

# 1. North star

> **Reduce attendance-forecast MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Production remains unchanged:

`live_adjustment = 0`

---

# 2. Current overall status

## Track A — FINAL24 prospective validation

Status: **FROZEN / VALIDATION ACTIVE**

Package:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Key IDs:

- Pre-Live v2: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- Stage-1 expert: `ridge-a10`;
- Stage-2 package: `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

Rule:

**Do not mutate Track A from new outcomes.**

## Track B — Pre-Live v3 research anchor

Status: **FROZEN RESEARCH CANDIDATE**

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Historical package improvement vs v2:

`1934.04 -> 1924.64` mean MAE across the 20-cell rolling matrix

`+9.39 / +0.49%`

V3 changes only T-30 and T-7. T-14/T-3/T-1 retain exact v2 contracts.

## Track B — early-live 24–72h package

Status: **FROZEN HISTORICAL RESEARCH PACKAGE / PROSPECTIVE SCORING NEXT**

Package ID:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

Scope:

`24 < hours_to_kickoff <= 72`

Composition:

- anchor: frozen T-3 checkpoint hold;
- Stage-1 expert: `inventory-linear-extrapolation`;
- correction cap: `±0.10` occupancy;
- Stage-2 policy: `P2-observation-maturity`.

Development performance:

- anchor MAE: **3707.14**;
- frozen package MAE: **3012.63**;
- improvement: **+694.51 / +18.73%**;
- event improvement rate: **61.54%**;
- worst event degradation: **1488.34**;
- bias: **+917.05**.

Band performance:

- 24–48h: **+954.58 / +25.75%** MAE improvement;
- 48–72h: **+664.71 / +14.47%** MAE improvement.

Evidence class:

`historical_exposed_research`

No genuine post-freeze prospective evidence yet.

---

# 3. Milestone tracker

| Milestone | Status | Decision / output |
|---|---|---|
| Pre-Live v2 freeze | ✅ DONE | Track-A anchor frozen |
| d2 final24 Stage 1 | ✅ DONE | `ridge-a10` selected |
| d2 final24 Stage 2 | ✅ DONE | `P2-observation-maturity` frozen |
| a2 external-model closure | ✅ DONE | robust ensembles found at T-30/T-7/T-1 |
| Pre-Live v3 regime revalidation | ✅ DONE | only T-30/T-7 advance |
| Pre-Live v3 fixed-temporal audit | ✅ DONE | T-30/T-7 positive 4/4 |
| Pre-Live v3 freeze | ✅ DONE | v3 research anchor sealed |
| v2-v3 final24 equivalence | ✅ DONE | exact `0.0` seat anchor delta |
| long-horizon export | ✅ DONE | additive `v8-long168` |
| long-horizon coverage audit | ✅ DONE | 72h selected as max learned window |
| long72 data + anchor freeze | ✅ DONE | 14 events / 130 rows frozen |
| long72 Stage 1 | ✅ DONE | `inventory-linear-extrapolation` lead |
| long72 Stage 2 | ✅ DONE | P2 selected and frozen |
| long72 prospective scoring | 🔄 ACTIVE NEXT | append-only future-event evidence |
| 72–168h learned model | ⏸ BLOCKED BY DATA ONLY | wait for `N>=9` independent events |
| production activation | ⛔ NOT READY | requires materially more prospective evidence |

---

# 4. Data / evidence tracking

## Frozen long72 data contract

Result:

`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`

Dataset:

- 14 events;
- 130 PIT-safe rows in 0–72h;
- model-selection slice 24–72h: 80 rows / 13 events;
- 48–72h: 35 rows / 10 events.

Dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Contract SHA256:

`0083b82be7de4599574b90ed0af44e1accd1a993c1d07b7f263bfbf01f3a1a27`

Anchor rule:

- `0<h<=24` -> T-1 checkpoint;
- `24<h<=72` -> T-3 checkpoint;
- no future checkpoint use.

## Long-horizon coverage

Additive export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Coverage at audit time:

- 14 eligible labeled events;
- 240 PIT-safe 6h rows inside final 168h;
- 13 events with data >24h;
- 10 events with data >48h;
- 8 events with data >72h.

Predeclared learned-model floor:

`N = 9 independent events`

Therefore:

- 72h = READY;
- 168h = diagnostic-only until `N>=9`.

---

# 5. Frozen long72 package details

Stage-2 result:

`ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`

Workflow run:

`39644319080`

Artifact ID:

`12366826274`

Stage-1 artifact ID:

`12365399256`

P2 reliability:

- observation #1 -> `0.25`;
- observation #2 -> `0.60`;
- observation #3+ -> `1.00`;
- `60<h<=72` time weight -> `0.75`;
- `48<h<=60` -> `0.90`;
- `24<h<=48` -> `1.00`;
- applied reliability = `min(observation_weight, time_weight)`.

Final forecast:

`anchor_p50 + reliability * inventory_delta_occupancy * capacity`

Historical stability diagnostics:

- original exposed subset: **+103.55 MAE improvement**;
- later exposed subset: **+1640.04 MAE improvement**.

Both are already exposed historical evidence.

Important alternative:

`P4-data-quality` had lower historical tail degradation but was not selected because the predeclared selector ranked eligible policies by overall MAE first.

Do not switch to P4 post hoc.

---

# 6. Active next work — prospective long72 scoring

Status: **ACTIVE NEXT**

Goal:

Score the frozen long72 package honestly on newly completed events with valid 24–72h trajectories.

For every new eligible event preserve:

1. frozen T-3 anchor;
2. raw inventory extrapolation forecast;
3. frozen P2 forecast;
4. event/as-of identities;
5. source snapshot / PIT lineage;
6. final attendance only once available.

Report append-only:

- event MAE;
- aggregate event-balanced MAE;
- uplift vs anchor;
- bias;
- event improvement rate;
- worst event degradation;
- 24–48h and 48–72h bands separately.

Rules:

- **no tuning from prospective outcomes**;
- do not change P2 weights;
- do not change correction cap;
- do not swap expert/model;
- do not backfill a forecast after seeing attendance;
- keep delayed/exposed vs genuinely post-freeze evidence explicit.

### Exit condition

Do not define a fixed arbitrary number of events as a blocker for ongoing R&D.

Production/promotion decision requires materially more genuine prospective evidence and acceptable aggregate/tail behavior. Research may continue in parallel.

---

# 7. Parallel work that may continue now

These do **not** need to wait for prospective long72 outcomes:

- prospective scoring infrastructure / immutable forecast persistence;
- source/data-quality hardening;
- PIT-safe context ingestion;
- long168 coverage accumulation;
- monitoring when 72–168h reaches `N>=9`;
- dashboard / research observability;
- reproducibility / CI / lineage improvements.

Do not retune the frozen long72 package on the same 13 development events.

---

# 8. Hard boundaries

## Do not change without creating a new challenger/version

- Pre-Live freeze contract;
- target definition;
- anchor mapping;
- long72 Stage-1 expert;
- correction cap;
- P2 reliability weights;
- event split / evidence class;
- feature semantics.

## Production boundary

Always until explicit reviewed promotion:

- Track-A final24 unchanged;
- Pre-Live v3 research-only;
- long72 P2 research-only;
- production `live_adjustment = 0`.

---

# 9. Immediate work order

1. **Implement/finalize append-only prospective long72 scoring.**
2. Persist frozen forecasts independently of final attendance where possible.
3. Score each new completed eligible event without retuning.
4. Keep Track-A final24 prospective validation running in parallel.
5. Monitor long168 coverage until `N>=9` for the 72–168h band.
6. Continue PIT-safe context/data-quality R&D without blocking on event count.
7. Do not activate production yet.

## One-line handoff

> **Historical optimization is frozen. Final24 and long72 packages are both immutable. The active milestone is honest append-only prospective scoring of the frozen 24–72h package, while production remains unchanged.**
