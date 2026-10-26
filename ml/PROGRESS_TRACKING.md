# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-26**

Status: **CANONICAL TRACKING SNAPSHOT**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`.

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Readiness counts are leading indicators only.

## Current status

| Item | Status | Current decision |
|---|---|---|
| Multi-source ticketing coverage | ✅ **18/18 LEAGUE HOME CLUBS** | preserve acquisition/PIT evidence; hidden inventory stays fail closed |
| Panel ingestion coverage | ✅ LIVE | tracked / buffering / schedule-gap / recent completed visible |
| Long72 prospective evidence | 🟢 **4 scored events** | 1.71% point gain only; preserve freeze; no retuning |
| P7 historical tournament | ✅ FROZEN / EXPOSED | 14.44% point gain; never retune |
| P7 prospective | 🟢 **16 rows / 3 events / 0 scores** | collect/score only |
| P9 historical T-168 | ✅ **9/9 / 9 clubs** | gate complete; not a model-success metric |
| P9 historical learner | ⚪ **NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT** | 0 support-ready at T-24/T-48; no MAE result; do not repair retrospectively |
| P9 prospective | 🟢 **SCHEDULED / CI VERIFIED** | collect immutable T-48/T-24 predictions and later score genuine outcomes |
| P9 prospective evidence | 🟡 **0 predictions / 0 scored** | expected before first frozen window on 2026-10-28 |
| P4a previous-home spacing | 🟡 **4/9 labeled / 3 distinct** | event-count gate still closed |
| P11a PIT odds | 🟢 **4 events / 4 clubs** | T-24/T-72/T-168 = 3/3/0; keep collecting; no model yet |
| P11b price context | 🟢 AS-KNOWN LIVE | no inferred promotion |
| P11c verified absences | 🟡 DATA_BOUND | continue collection |
| P11d weather | ✅ CLOSED / NO UPLIFT | do not repeat same mechanism |
| P11d media attention | 🟡 PROSPECTIVE COLLECTING | wait for genuine coverage |
| Governance | 🟡 BUSINESS ΔMAE PENDING | derive independently from operational value |
| P12 / new features | 🟡 DEFERRED | rank later by expected incremental prospective MAE reduction |

## P9 historical closure

The old `8/9` state is obsolete.

Canonical gate:

- T-168 events / clubs: **9 / 9**;
- `design_precommitted=true`;
- `full_window_gate_open=true`.

Frozen historical support diagnostic:

- T-24 comparator targets: **11**;
- T-24 support-ready: **0**;
- T-48 comparator targets: **9**;
- T-48 support-ready: **0**;
- learner attendance labels opened: false;
- learner result produced: false.

Status:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Root cause is missing genuine historical PIT incumbent rows from the exact target incumbent source family among selected curve-neighbors. Booking-curve coverage itself is not the blocker.

Read:

`ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`

## P9 prospective — active

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Workflow:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Schedule:

`7,37 * * * *`

The Supabase Edge Function `p9_booking_curve_prospective_v1` is deployed and the workflow has passed an end-to-end run on main:

- GitHub OIDC authorization;
- target-free/reference export;
- frozen builder path;
- scoring path;
- production-safety assertions.

Current state:

- prediction events: **0**;
- prediction rows: **0**;
- scored events: **0**;
- `production_activation_allowed=false`;
- `live_adjustment=0`.

First T-48 window:

**2026-10-28 17:00 UTC — Cracovia vs Motor**.

No late bootstrap. If support is insufficient inside a real frozen window, record the failure; do not relax the rule.

## P7 prospective

Frozen fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Fresh state:

- prediction rows: **16**;
- independent events: **3**;
- scored events: **0**;
- one fixed model fingerprint;
- production activation false.

Next action: collect/score only.

## Long72

Last verified frozen n=4 evidence:

- events `[10,16,21,23]`;
- anchor event-balanced MAE **6942.59**;
- challenger event-balanced MAE **6824.16**;
- point gain **118.43 / 1.71%**;
- event improvement rate **75%**;
- worst event degradation **3633.23**.

Not promotion evidence.

## P4a

- labeled READY events: **4/9**;
- distinct labeled previous-home-spacing values: **3**;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move the gate.

## P11a odds

Fresh 2026-10-26 readiness:

- status `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs **4 / 4**;
- events with >=3 bookmakers **4**;
- T-24 / T-72 / T-168 coverage **3 / 3 / 0**;
- model precommitted false;
- production false.

Continue append-only capture. Never backfill closing odds.

## Panel / MAE lifecycle

Canonical dashboard view:

`public.dashboard_p9_mae_status_v1`

Panel repo:

`NiedzielX/BeyondTicketingPanel`

Model Lab has a dedicated P9 lifecycle widget that distinguishes:

1. readiness;
2. historical evaluability;
3. prospective prediction coverage;
4. scored evidence;
5. incumbent/challenger event-balanced MAE;
6. ΔMAE;
7. production safety.

Dashboard TypeScript check and production build are green after the integration.

## Immediate order

1. keep ticketing/PIT acquisition healthy;
2. preserve P9 scheduler before first real window;
3. collect immutable P9 predictions;
4. score P7/P9 only on genuine outcomes;
5. continue Long72/P4a/P11 frozen accumulation;
6. derive business minimum meaningful ΔMAE;
7. select the next challenger only by expected prospective MAE impact.

## Closed loops

Do not reopen without a materially new mechanism:

- original P7 tournament;
- P9 historical cohort;
- P10/P10b;
- P5a;
- P6 historical Long72 incremental signal;
- P8 calibration;
- existing weather mechanism;
- old estimator sweeps;
- post-hoc tuning.
