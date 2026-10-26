# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-26**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/CURRENT_MODEL.md`;
4. `ml/PROGRESS_TRACKING.md`;
5. `ml/MAE_RESEARCH_ROADMAP_V4.md`;
6. `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`;
7. `ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`;
8. `ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`;
9. `ml/P7_LONG168_RESULT_2026-10-25.md`;
10. `ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`;
11. `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`;
12. `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`;
13. `ml/TICKETING_SCHEDULE_WATCHDOG_2026-10-25.md`.

Do not reconstruct frozen experiments from memory. Query machine state fresh.

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Primary decision metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction: `ΔMAE < 0`.

T-168 counts, labels, support-ready targets, snapshot counts, odds rows and prediction rows are evidence-enablers, not the objective.

Production remains:

`live_adjustment = 0`

## Immediate execution order

`protect acquisition/PIT evidence -> keep P9 prospective scheduler healthy -> collect immutable P9 T-48/T-24 predictions -> score P7/P9 only on genuine outcomes -> continue Long72/P4a/P11 frozen accumulation -> derive business minimum meaningful ΔMAE -> choose next challenger by expected prospective MAE impact`

## Current canonical state

### P9 historical v1

- genuine T-168 gate: **9/9 events / 9 clubs**;
- design precommitted before evaluation;
- historical result: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`;
- T-24 comparator/support-ready: **11 / 0**;
- T-48 comparator/support-ready: **9 / 0**;
- attendance labels were not opened by the learner;
- no historical challenger MAE was produced;
- do not retrospectively repair/backfill the cohort.

Canonical status sources:

- `public.p9_learner_gate_status_v1()`;
- `public.p9_historical_cohort_status_v1()`;
- `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`.

Do not use legacy `public.p9_booking_curve_readiness_v1()` as the learner/precommit source of truth.

### P9 prospective v1

Frozen contract:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Automation:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Schedule:

`7,37 * * * *`

The scheduler is deployed and has passed an end-to-end CI execution on main after deployment of `p9_booking_curve_prospective_v1` Edge Function.

Current evidence at bootstrap update:

- prediction events: **0**;
- prediction rows: **0**;
- scored events: **0**;
- production activation false.

Zero is expected before the first frozen prediction windows. First T-48 window begins **2026-10-28 17:00 UTC** for Cracovia–Motor.

### P7 prospective

- frozen fingerprint unchanged;
- current live ledger at 2026-10-26: **16 prediction rows / 3 events / 0 scored events**;
- no tuning; collection/scoring only.

### Long72

Last verified frozen evidence:

- 4 genuine scored events;
- anchor event-balanced MAE **6942.59**;
- challenger MAE **6824.16**;
- point gain **118.43 / 1.71%**;
- not promotion evidence.

### P4a

Last verified:

- labeled READY **4/9**;
- 3 distinct spacing values;
- variance gate PASS;
- event-count gate FAIL.

### P11 odds

Fresh 2026-10-26 readiness:

- status `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs **4 / 4**;
- >=3 bookmaker events **4**;
- T-24 / T-72 / T-168 coverage **3 / 3 / 0**;
- model precommitted false;
- never backfill closing odds.

### Ticketing acquisition

- multi-source safety net remains live;
- current league home-club source coverage last verified **18/18**;
- completed matches remain visible in panel/event history;
- preserve PIT timestamps and fail closed on hidden/ambiguous inventory.

### Panel

Canonical P9 dashboard contract:

`public.dashboard_p9_mae_status_v1`

Panel repo:

`NiedzielX/BeyondTicketingPanel`

Model Lab now has a dedicated P9 MAE lifecycle panel separating:

- readiness;
- historical `NOT_EVALUABLE` state;
- prospective prediction/scoring coverage;
- incumbent MAE;
- challenger MAE;
- ΔMAE;
- production guardrails.

## Hard rules

- never relax a research gate just to obtain a result;
- never call backfilled history prospective;
- never tune a challenger after opening its evaluation outcomes;
- `NOT_EVALUABLE` is neither a win nor a loss;
- do not promote from point gain alone;
- keep `live_adjustment=0` until explicit reviewed promotion.
