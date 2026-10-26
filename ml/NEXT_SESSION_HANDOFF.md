# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-26**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction: `ΔMAE < 0`.

Readiness metrics are not model success.

Production remains:

`live_adjustment = 0`

## 2. Immediate execution order

1. protect ticketing acquisition and all PIT evidence lanes;
2. keep P9 prospective scheduler healthy before every frozen T-48/T-24 window;
3. collect immutable P9 predictions only inside the precommitted windows;
4. score P7/P9 only after genuine attendance outcomes arrive;
5. continue Long72/P4a/P11 frozen accumulation without retuning;
6. derive business minimum meaningful ΔMAE;
7. choose any new challenger by expected incremental prospective MAE reduction.

Canonical current plan:

`ml/EXECUTION_PLAN_CURRENT.md`

## 3. P9 historical v1 — CLOSED / NOT EVALUABLE

The old 8/9 status is obsolete.

Live canonical gate:

- T-168: **9/9 events / 9 clubs**;
- `design_precommitted=true`;
- `full_window_gate_open=true`;
- target-free manifests registered: 2.

Frozen historical result:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Support diagnostic:

- T-24: 11 comparator targets, **0 support-ready**;
- T-48: 9 comparator targets, **0 support-ready**;
- attendance labels remained unopened;
- no learner MAE result was produced.

Root cause:

The fixed learner requires at least 3 curve-neighbors with genuine historical residuals from the exact same incumbent source family at the analogous PIT cutoff. Historical incumbent ledger coverage is insufficient even though the booking curves themselves exist.

Do not backfill historical incumbents and call them PIT.

Read:

`ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`

Canonical machine sources:

- `public.p9_learner_gate_status_v1()`;
- `public.p9_historical_cohort_status_v1()`.

Do not use `public.p9_booking_curve_readiness_v1()` for learner/precommit truth.

## 4. P9 prospective v1 — ACTIVE / HIGHEST TIME-CRITICAL LANE

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen learner remains:

`PIT booking-curve similarity -> fixed k=5 prior curves -> same-incumbent-family PIT residuals -> median residual -> incumbent correction`

Rules remain fixed:

- T-48 / T-24 only;
- k=5;
- minimum 3 residual-bearing references;
- no fit/search/tuning;
- no target attendance available at prediction time;
- no late bootstrap;
- valid persistence window: cutoff through cutoff + 90m;
- primary metric: prospective event-balanced MAE.

Automation:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Schedule:

`7,37 * * * *`

The previously missing Supabase Edge Function `p9_booking_curve_prospective_v1` was deployed on 2026-10-26. The GitHub workflow was rerun and passed all steps end-to-end:

- GitHub OIDC;
- reference-outcomes export;
- target-free T-48/T-24 export;
- P9a freeze/builder path;
- score path;
- final production-safety assertions.

Current prospective state at handoff:

- prediction events: **0**;
- prediction rows: **0**;
- scored events: **0**;
- `production_activation_allowed=false`;
- `live_adjustment=0`.

This zero is expected before the first precommitted windows.

First windows:

- Cracovia–Motor T-48: **2026-10-28 17:00 UTC**;
- Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**.

If a valid window produces no prediction because support remains insufficient, record that fact. Do not relax the frozen rule.

Only consider P9 v2 after prospective v1 has had a fair opportunity to accumulate genuine PIT incumbent history and still shows structural support starvation.

## 5. Panel / MAE visibility

Supabase canonical read-only view:

`public.dashboard_p9_mae_status_v1`

It separates:

- historical 9/9 readiness;
- historical `NOT_EVALUABLE` status and support counts;
- prospective prediction events/rows;
- scored events;
- incumbent event-balanced MAE;
- challenger event-balanced MAE;
- ΔMAE;
- event improvement rate / worst degradation;
- production guardrails.

Panel repo:

`NiedzielX/BeyondTicketingPanel`

A dedicated `P9MaeStatusPanel` is wired into Model Lab so generic readiness is no longer the P9 source of truth.

## 6. P7 prospective

Historical P7 result remains frozen/exposed:

- anchor MAE 7409.79;
- challenger MAE 6339.99;
- point gain 1069.80 / 14.44%;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Prospective lane remains frozen:

- model `gbr-l1-depth2-n50-lr003`;
- fingerprint `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- **16 immutable prediction rows / 3 independent events / 0 scored events** as of 2026-10-26;
- no tuning; collect/score only.

## 7. Long72

Last verified frozen n=4 evidence:

- events `[10,16,21,23]`;
- anchor event-balanced MAE **6942.59**;
- package MAE **6824.16**;
- point improvement **118.43 / 1.71%**;
- event improvement rate **75%**;
- worst event degradation **3633.23**.

Not promotion evidence. Do not retune.

## 8. P4a

Last verified:

- labeled READY **4/9**;
- 3 distinct previous-home-spacing values;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move this gate.

## 9. P11

Fresh odds readiness 2026-10-26:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs **4 / 4**;
- >=3 bookmaker events **4**;
- T-24 / T-72 / T-168 coverage **3 / 3 / 0**;
- model precommitted false;
- production false.

Continue append-only capture; never backfill closing odds.

## 10. Ticketing acquisition

Current league ticketing source coverage last verified **18/18**.

Preserve:

- fixture watchdog;
- RoboTicket discovery/private candidate buffer/promotion;
- Stellis collectors;
- original `captured_at` on promotion;
- hidden/unknown availability != zero;
- completed-match visibility in panel.

## 11. Governance

Business minimum meaningful ΔMAE is still intentionally unset until independently derived from operational decisions.

P12/new feature families stay behind active prospective evidence protection. New hypotheses should be ranked by expected incremental prospective MAE impact, not novelty.

## 12. Cold-start command

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/CURRENT_MODEL.md`, `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md` and both P9 precommits. Query live status fresh. Historical P9 is 9/9 but NOT_EVALUABLE due to zero same-family PIT support; do not repair it. P9 prospective scheduler is deployed and CI-verified, with first T-48 window on 2026-10-28 17:00 UTC. P7 prospective has 16 rows / 3 events / 0 scores. Long72 has 4 scores. P4a is 4/9. P11 is collecting. Keep production unchanged and optimize all work toward prospective event-balanced MAE.
