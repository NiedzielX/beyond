# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-28 20:35 UTC**

Status: **CURRENT SOURCE OF TRUTH**

Canonical research strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`.

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons, with PIT-safe, reproducible evidence.**

Primary decision metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction: `ΔMAE < 0`.

Readiness counters, snapshot counts, support counts, odds rows and prediction rows are experiment prerequisites only. They are not model success.

Production remains unchanged:

`live_adjustment = 0`

No research lane may activate production automatically.

## Research decision rules

1. Prefer genuine prospective evidence over historical reconstruction whenever historical PIT cannot be proven.
2. Never relax a gate merely to obtain a result.
3. Never tune a challenger after opening the target outcomes used to judge it.
4. `NOT_EVALUABLE` and fail-closed support outcomes are valid research outcomes; they are neither wins nor losses.
5. Keep frozen lanes separately auditable; never merge evidence from differently precommitted learners into one result.
6. Promotion requires meaningful prospective MAE gain plus acceptable event-level downside.
7. Rejected hypotheses stay closed on the same outcomes unless genuinely new precommitted evidence justifies reopening them.
8. Preserve `live_adjustment=0` until an explicit production decision is approved.

## Priority 0 — protect data and evidence integrity

- Keep multi-source ticketing acquisition, fixture watchdog, raw buffering and promotion healthy.
- Preserve original `captured_at`; never manufacture booking-curve history.
- Never backfill odds, forecasts, booking curves or outcomes and call them prospective.
- Hidden/unknown inventory is never zero.
- Preserve immutable prediction/attempt ledgers and PIT lineage.
- Keep production disabled for every research lane.

## Priority 1 — P9 v1: collect genuine immutable attempts

Historical P9 v1 is closed:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Historical state:

- T-168: **9/9 events / 9 clubs**;
- T-24 support-ready: **0/11**;
- T-48 support-ready: **0/9**;
- attendance labels remained unopened;
- no historical challenger MAE exists.

Do not repair historical P9 retrospectively.

### First genuine prospective attempt — event443 Cracovia–Motor T-48

Exact cutoff: **2026-10-28 17:00 UTC**.

Attempt persisted at **17:00:42 UTC**.

Result:

`PIT_SUPPORT_INSUFFICIENT`

Current v1 lifecycle:

- attempt events: **1**;
- attempt rows: **1**;
- support-insufficient attempts: **1**;
- prediction rows: **0**;
- scored events: **0**;
- production activation: false;
- `live_adjustment=0`.

This was a correct fail-closed, not a missed window and not a model loss. Do not relax the minimum 3-reference gate and do not retro-predict event443.

### Near-term v1 windows

Current preflight:

- critical: **0**;
- watch: **1**;
- only watch: event448 Wisła Kraków–Cracovia = `WATCH_NO_SNAPSHOT`.

Next relevant cutoffs:

- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC** — READY;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC** — READY;
- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC** — READY;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC** — READY;
- event445 Zagłębie–Korona T-48: **2026-10-31 17:00 UTC** — READY;
- event447 Raków–Pogoń T-48: **2026-10-31 19:30 UTC** — READY.

Immediate rule: protect every window and record the exact reason whenever v1 emits no prediction.

## Priority 2 — P9 Family Fallback v2: run separately, never retroactively

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_FAMILY_FALLBACK_V2.md`

Purpose: address a target-free incumbent-family coverage failure without changing the exact P9a neighbors or minimum support gate.

Frozen v2 rule:

1. use the exact v1 target-family decision and exact five neighbors;
2. if v1 family already has >=3 refs, v2 emits nothing (`V1_COVERED`);
3. only when v1 selected D2 and D2 has <3 refs may Structural be checked on the same five neighbors;
4. fallback requires a valid PIT Structural target incumbent and >=3 Structural residual refs;
5. otherwise fail closed;
6. no target labels, no search, no retroactive event443 prediction.

Current v2 state:

- attempts: **0**;
- predictions: **0**;
- scored events: **0**;
- production OFF.

First meaningful v2 evidence will come only from a genuine post-precommit window.

## Priority 3 — Form5 prospective challenger: protect first T-24 evidence

Precommit:

`ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen design:

- source exactly `TheSportsDB v1 shadow`;
- immutable prospective T-24 snapshots only;
- comparator = true immutable baseline;
- LOCO primary / LOEO secondary;
- ridge alpha **30**;
- correction cap **±25%**;
- global gate **8 events / 5 clubs / >=2 distinct values**;
- per-fold minimum **5 train events / 4 clubs / non-zero x_sd**;
- production OFF.

Current state:

- completed eligible events: **0/8**;
- future stream: **13 events / 12 clubs / 9 distinct values**;
- first qualifying T-24: event443 on **2026-10-29 17:00 UTC**.

Do not use older/manual Form5 values for this v1.

## Priority 4 — P7 prospective: score only after genuine outcomes

Historical frozen result:

- anchor MAE **7409.79**;
- challenger MAE **6339.99**;
- point gain **1069.80 / 14.44%**;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Current prospective state:

- **53 immutable prediction rows / 6 events**;
- scored events: **0**.

No tuning. Score only after genuine outcomes arrive.

## Priority 5 — P11 odds: continue append-only PIT collection

Current readiness:

- status `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs: **6 / 6**;
- >=3 bookmakers: **6 events**;
- T-24 coverage: **5**;
- T-72 coverage: **5**;
- T-168 coverage: **0**;
- model precommitted: false;
- production false.

Do not fit or select an attendance model until a genuine horizon coverage audit and precommit are complete.

## Priority 6 — Long72: frozen, low MAE priority, operationally healthy

Current scored sample: **5 events**.

Overall 24–72h:

- anchor MAE **6082.40**;
- package MAE **6039.39**;
- improvement **43.01 / 0.71%**;
- event improvement rate **60%**;
- worst event degradation **3633.23**.

By band:

- 24–48h: **105.08 worse**;
- 48–72h: **191.10 better**.

Do not retune. Long72 is no longer a priority hypothesis unless materially new evidence appears.

Operational heartbeat issue found on 2026-10-28 was closed by triggering Long72 from successful Structural Prior Materializer completion. Keep watching the dependency chain; do not change the frozen package.

## Priority 7 — P4a: genuine label accumulation only

Last verified:

- labeled READY: **4/9**;
- distinct previous-home-spacing values: **3**;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move the gate.

## Priority 8 — rejected / closed research lanes

### Live Ticketing challenger

Current leakage-safe LOCO sample:

- **19 events / 11 clubs**;
- incumbent MAE ~**4704.1**;
- challenger MAE ~**5427.7**;
- uplift **-723.6**.

Decision: **REJECTED**. Do not reopen the old 8-event positive snapshot.

### Sporting Match Stakes

- 19 events / 11 clubs;
- uplift vs incumbent **-255.3**.

Decision: **REJECTED**.

### Match Context timing candidate

- 19 events / 11 clubs;
- uplift vs incumbent **-213.9**.

Decision: **REJECTED**.

### Weather

- historical leave-one-season-out uplift approx **-268.8**.

Decision: **REJECTED for production point forecast**; shadow collection may continue.

### Hype / Attention

Current 24h `media_attention`:

- 10 completed events / 10 clubs;
- distinct values **1**;
- not testable.

`mention_acceleration`:

- 4 completed events / 4 clubs;
- 3 distinct values;
- below 8 / 5 gate.

One pre-specified 48h alternative was tested:

- baseline MAE **4156.0**;
- challenger MAE **4225.4**;
- **69.4 MAE worse**;
- only 2/10 non-zero events.

Decision: **REJECTED_NO_UPLIFT** for the 48h hypothesis. Do not search additional attention windows on the same outcomes.

Read: `ml/HYPE_ATTENTION_RESEARCH_2026-10-27.md`.

## Priority 9 — business minimum meaningful ΔMAE

Canonical framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

This remains unset. Derive it from real operational decisions independently of challenger results.

## Priority 10 — new feature work only after active evidence lanes

Do not start a broad tuning tournament now.

Any new candidate must satisfy all three:

1. genuinely new information not already represented by rejected lanes;
2. PIT-safe source and reproducible lineage;
3. precommitted evaluation design before target outcomes are opened.

Rank candidates by expected incremental **prospective event-balanced MAE** reduction, not novelty.

## Immediate execution order

1. **Protect tomorrow's P9 windows** for event446, event6, event443 T-24 and event444.
2. **Run v1 and v2 separately** at each genuine window; never combine their evidence.
3. **Capture Form5 event443 T-24** at 2026-10-29 17:00 UTC.
4. **Watch event448** for a genuine inventory snapshot; never fabricate zero inventory.
5. **Score P7/P9 only after genuine outcomes** from 30.10–02.11 arrive.
6. Continue P11 append-only capture and P4a label accumulation.
7. Keep Long72 frozen; monitor only operational health.
8. Derive business minimum meaningful ΔMAE.
9. Only then decide whether a new precommitted challenger is worth starting.

## Decision rule for P9 after the next windows

Do not change v1 after one fail-closed attempt.

After several genuine windows:

- if v1 starts emitting predictions, continue unchanged and wait for outcomes;
- if v1 repeatedly fails only because incumbent-family support is sparse while v2 emits valid predictions, evaluate v2 separately after genuine outcomes;
- if both v1 and v2 repeatedly fail, diagnose support structure before designing another learner;
- never lower k/support thresholds merely to obtain coverage.

## Next meaningful MAE milestones

1. first valid immutable P9 v1 prediction;
2. first valid immutable P9 v2 fallback prediction, if v1 support fails;
3. first genuine Form5 eligible T-24 capture;
4. first genuine P7 prospective scored event;
5. first genuine P9 prospective scored event;
6. enough independent scored events to report event-balanced ΔMAE and event-level downside;
7. business minimum meaningful ΔMAE approved;
8. only then any production promotion decision.
