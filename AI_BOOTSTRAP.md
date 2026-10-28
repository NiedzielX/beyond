# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-28 18:05 UTC**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md`;
2. this file's **Current canonical state** below;
3. `ml/EXECUTION_PLAN_CURRENT.md`;
4. `ml/CURRENT_MODEL.md`;
5. `ml/PROGRESS_TRACKING.md`;
6. `ml/MAE_RESEARCH_ROADMAP_V4.md`;
7. `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`;
8. `ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`;
9. `ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`;
10. `ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`.

Always query machine state fresh. Do not reconstruct frozen experiments from memory.

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Primary metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired: `ΔMAE < 0`.

Readiness, snapshot counts, odds rows, support counts and prediction rows are experiment prerequisites, not model success.

Production remains:

`live_adjustment = 0`

## Immediate execution order

1. Protect every genuine P9 T-48/T-24 window.
2. Collect/score P9 and P7 without changing frozen rules.
3. Protect Form5 T-24 forward evidence starting **2026-10-29 17:00 UTC**.
4. Continue Long72/P11/P4a forward accumulation without retuning.
5. Keep event448 inventory as unknown until the provider exposes real sectors.
6. Do not reopen rejected Ticketing/Hype hypotheses on the same outcomes.
7. Rank new work by expected incremental prospective MAE reduction.

## Current canonical state

### P9 historical v1 — CLOSED

- T-168 gate: **9/9 events / 9 clubs**;
- design precommitted before evaluation;
- result: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`;
- T-24 support-ready: **0/11**;
- T-48 support-ready: **0/9**;
- attendance labels remained unopened by the learner;
- no historical challenger MAE exists.

Do not retrospectively repair/backfill this cohort.

Canonical sources:

- `public.p9_learner_gate_status_v1()`;
- `public.p9_historical_cohort_status_v1()`;
- `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`.

### P9 prospective v1 — ACTIVE

Frozen contract:

`PIT booking-curve similarity -> fixed k=5 prior curves -> same-incumbent-family PIT residuals -> median residual -> incumbent correction`

Rules remain:

- T-48/T-24 only;
- k=5;
- minimum 3 residual-bearing references;
- no fit/search/tuning;
- no target attendance at prediction time;
- no late bootstrap;
- immutable persistence through cutoff +90m;
- primary metric = prospective event-balanced MAE.

Workflow:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Schedule:

`11,26,41,56 * * * *`

#### First genuine attempt — event443 Cracovia–Motor T-48

Cutoff: **2026-10-28 17:00 UTC**.

Attempt persisted: **17:00:42.692 UTC**.

Result:

`PIT_SUPPORT_INSUFFICIENT`

Details:

- target incumbent family: `d2_long72_forward_predictions_v1`;
- selected neighbors: `[3,23,4,21,20]`;
- usable same-family residuals: **2**, minimum **3**;
- usable refs: `23,21`;
- no prediction;
- no scored event;
- production OFF.

This is a valid fail-closed, not a win/loss. Do not relax the gate after one attempt.

Current dashboard/preflight state at this bootstrap update:

- attempt events: **1**;
- support-insufficient attempts: **1**;
- prediction-ready attempts: **0**;
- prediction rows: **0**;
- scored events: **0**;
- prospective ΔMAE: unavailable;
- preflight critical: **0**;
- preflight watch: **0**.

#### P9 support observability

Service-role diagnostic:

`public.p9_family_support_preflight_v1(integer)`

At T-48 the current genuine outcome-backed reference pools are approximately:

- D2/Long72 family: **5** residual-ready events;
- Structural Prior family: **9** residual-ready events.

This is **global family-pool size, not selected-neighbour support**. Frozen P9 still requires >=3 same-family residuals among its five nearest booking curves.

The diagnostic also applies the same **6h Long72 staleness rule** as the frozen builder and marks whether an upcoming target's incumbent family can still change before cutoff.

#### P9 PIT safety fixes — 2026-10-28

1. Immutable attempt registry is now source of truth for whether a window was captured.
   - prediction -> `CAPTURED`;
   - valid support fail -> `CAPTURED_PIT_SUPPORT_INSUFFICIENT`;
   - no target incumbent -> `CAPTURED_NO_TARGET_INCUMBENT`;
   - `PREDICTION_READY` without persisted prediction -> `CRITICAL_PREDICTION_PERSISTENCE_GAP`;
   - `MISSED_WINDOW` only when neither prediction nor immutable attempt exists after +90m.

2. Reference outcomes must now satisfy:

   `reference.confirmed_at <= target_as_of_at`

   An outcome confirmed after the target cutoff is treated as unavailable and reduces support under the existing min-3 rule.

   Regression workflow:

   `.github/workflows/p9-prospective-pit-regression.yml`

   Latest PIT regression and normal P9 end-to-end runs on main are green.

Near-term windows:

- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**.

Do not precompute nearest neighbors outside the immutable window.

### P7 prospective — ACTIVE

Historical frozen point result:

- anchor MAE **7409.79**;
- challenger MAE **6339.99**;
- point gain **1069.80 / 14.44%**;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Prospective scoring remains outcome-driven only. No retuning.

### Long72 — FROZEN / LOW PRIORITY

Current scored evidence:

- **5** genuine events;
- anchor event-balanced MAE **6082.40**;
- package MAE **6039.39**;
- improvement **43.01 / 0.71%**;
- event improvement rate **60%**;
- worst event degradation **3633.23**;
- 24–48h band worsens MAE by ~**105**;
- 48–72h band improves MAE by ~**191**.

Workflow:

`.github/workflows/d2-long72-forward-prospective-v1.yml`

Schedule hardened on 2026-10-28 because GitHub's nominal hourly cron dropped/delayed cycles:

`2,17,32,47 * * * *`

Frozen package/model is unchanged. Persistence remains idempotent and production OFF.

### Form5 prospective challenger — PRECOMMITTED / READY FOR FIRST T-24

Precommit:

`ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen:

- source exactly `TheSportsDB v1 shadow`;
- immutable prospective T-24 snapshots only;
- comparator = true immutable baseline;
- LOCO primary / LOEO secondary;
- ridge alpha 30;
- correction cap ±25%;
- gate 8 events / 5 clubs / >=2 distinct values;
- no historical snapshot backfill;
- production OFF.

First qualifying cutoff:

- event443 Cracovia–Motor T-24 = **2026-10-29 17:00 UTC**.

Current event443 Form5 observation is already valid before that cutoff:

- `sport.form5 = 4`;
- source `TheSportsDB v1 shadow`;
- exactly 5 completed league matches;
- latest provider fetch **2026-10-28 12:10 UTC**.

Snapshot cron:

`event_context_snapshot_15m` -> `*/15 * * * *`

It was verified healthy across the prior 24h with no failed runs and sub-second nominal start delays. No scheduler hotfix is currently needed.

### P11 odds — ACTIVE

Current readiness:

- status `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs: **6 / 6**;
- events with >=3 bookmakers: **6**;
- T-24 / T-72 / T-168 coverage: **5 / 5 / 0**;
- model precommitted: false;
- production: false.

Continue append-only capture. Never backfill closing odds.

### Rejected current research lanes

#### Live Ticketing challenger

Current leakage-safe sample:

- 19 events / 11 clubs;
- LOCO baseline MAE ~**4704.1**;
- challenger MAE ~**5427.7**;
- challenger worse by ~**723.6**.

Decision: `REJECTED_NO_UPLIFT`.

#### Hype / Attention

- current 24h `media_attention`: 10 completed events / 10 clubs but only **1 distinct value** -> not testable;
- `mention_acceleration`: still below its fixed gate;
- one pre-specified 48h attention alternative was tested and worsened true baseline MAE by **69.4**;
- do not search additional windows on the same outcomes.

Read:

`ml/HYPE_ATTENTION_RESEARCH_2026-10-27.md`

### Ticketing acquisition

- multi-source safety net remains live;
- preserve original PIT timestamps;
- hidden/unknown inventory is never zero;
- event448 Wisła Kraków–Cracovia remains a genuine no-sectors provider watch — do not fabricate inventory.

## Hard rules

- never relax a research gate just to obtain a result;
- never call backfilled history prospective;
- never tune a frozen challenger after opening its evaluation outcomes;
- `NOT_EVALUABLE` is neither a win nor a loss;
- do not promote from point gain alone;
- do not design P9 v2 merely because the first prospective attempt failed closed;
- only consider P9 v2 after repeated genuine prospective support starvation with sufficient new PIT history;
- keep `live_adjustment=0` until explicit reviewed promotion;
- query machine state fresh before acting.
