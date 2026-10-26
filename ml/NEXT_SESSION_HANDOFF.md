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

Canonical plan:

`ml/EXECUTION_PLAN_CURRENT.md`

## 2. Immediate execution order

1. keep P9 automated preflight + scheduler/gateway healthy before every immutable T-48/T-24 window;
2. watch event 448 for its first genuine ticketing snapshot and event 452 for later sporting-round coverage;
3. collect immutable P9 predictions only inside precommitted windows;
4. score P7/P9 only after genuine attendance outcomes arrive;
5. continue Long72/P4a/P11 frozen accumulation without retuning;
6. derive business minimum meaningful ΔMAE;
7. choose any new challenger by expected incremental prospective MAE reduction.

## 3. P9 historical v1 — CLOSED / NOT EVALUABLE

Canonical gate:

- T-168: **9/9 events / 9 clubs**;
- `design_precommitted=true`;
- `full_window_gate_open=true`.

Frozen result:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Support:

- T-24: **0/11 support-ready**;
- T-48: **0/9 support-ready**;
- attendance labels remained unopened;
- no historical learner MAE result was produced.

Root cause is historical incumbent-ledger coverage, not booking-curve coverage. Never repair it retrospectively.

Read:

`ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`

## 4. P9 prospective v1 — ACTIVE / HIGHEST TIME-CRITICAL LANE

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen learner:

`PIT booking-curve similarity -> k=5 prior curves -> same-incumbent-family PIT residuals -> median residual -> incumbent correction`

Rules:

- T-48 / T-24 only;
- minimum 3 residual-bearing references;
- no fit/search/tuning;
- no target attendance at prediction time;
- no late bootstrap;
- persistence window = exact cutoff through cutoff + 90m;
- primary metric = prospective event-balanced MAE.

Automation:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Schedule:

`7,37 * * * *`

Gateway:

`supabase/functions/p9_booking_curve_prospective_v1`

Current evidence:

- prediction events: **0**;
- prediction rows: **0**;
- scored events: **0**;
- `production_activation_allowed=false`;
- `live_adjustment=0`.

Zero is expected before the first frozen window.

First windows:

- Cracovia–Motor T-48: **2026-10-28 17:00 UTC**;
- Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**.

If a window produces no prediction because frozen support is insufficient, record it. Do not relax the rule.

## 5. Automated P9 preflight — LIVE

Function:

`public.p9_prospective_preflight_v1(10)`

Repo:

`supabase/sql/p9_prospective_preflight_v1.sql`

It is service-role-only, target-free and production-safe. For every future target it checks cutoff-eligible booking snapshots and PIT incumbents at both T-48/T-24 and returns:

- `READY`;
- `WATCH_*`;
- `CRITICAL_*` within 48h of cutoff;
- `WINDOW_OPEN`;
- `CAPTURED`;
- `MISSED_WINDOW`.

The P9 gateway exposes it only through main-branch GitHub OIDC. The P9 workflow runs it before prediction capture and writes the result to the GitHub job summary. WATCH/CRITICAL emits warnings but does not abort the whole job.

Fresh live 10-day preflight on 2026-10-26:

- critical: **0**;
- watch: **0**;
- all six near-term targets are READY at T-48 and T-24:
  - 443 Cracovia–Motor;
  - 446 Wisła Płock–Piast;
  - 6 Lech–Wisła Kraków;
  - 444 GKS–Widzew;
  - 445 Zagłębie–Korona;
  - 447 Raków–Pogoń.

## 6. First-window Structural Prior safeguard — FIXED

Event 443 Cracovia–Motor originally had snapshots but no target incumbent because sporting shadow carried a round-date placeholder one day after the verified kickoff.

Resolver patch:

`supabase/sql/structural_prior_fixture_date_tolerance_2026_10_26.sql`

Rule:

1. exact Warsaw date first;
2. fallback only for one unique exact aliased home/away pair within ±3 days;
3. zero/multiple candidates fail closed.

Structural Prior Materializer run `40358782359` succeeded and persisted:

- event 443 prior ID **40**;
- horizon T-7;
- P50 **10632.32**;
- capacity **15016**;
- `point_in_time_validated=true`;
- created **2026-10-26 16:25 UTC**;
- before P9 T-48 cutoff **2026-10-28 17:00 UTC**.

The P9 incumbent exporter independently enforces both source `as_of_at` and `created_at` before the analogous cutoff.

## 7. Capacity gaps 447/603 — RESOLVED

Verified current capacities added to:

`supabase/sql/structural_prior_current_capacities_2026_v1.sql`

- Raków Częstochowa: **5500**;
- Korona Kielce: **15550**.

Materializer run `40359572478` succeeded and orchestrator processed:

- event 447 Raków–Pogoń — prior ID **45**, P50 **5049.53**, capacity **5500**, PIT-validated;
- event 603 Korona–Radomiak — prior ID **46**, P50 **12016.93**, capacity **15550**, PIT-validated.

The previous `missing_capacity` state is obsolete.

## 8. Remaining data watches

### Event 452 Pogoń–Śląsk

- ticketing is tracked and has snapshots;
- Structural Prior remains `missing_fixture_round`;
- sporting shadow was freshly fetched on 2026-10-26 but currently exposes future rounds 13–14 only;
- leave fail-closed until the later round appears upstream.

Do not insert a round manually.

### Event 448 Wisła Kraków–Cracovia

- ticket event is tracked;
- current status `TRACKED_NO_SNAPSHOT`;
- zero canonical/raw inventory snapshots observed so far;
- do not interpret hidden/not-yet-visible inventory as zero.

Let discovery/watchdog continue and allow P9 preflight to surface it when the event enters the active horizon.

## 9. Panel / MAE visibility — LIVE AND SECURITY-HARDENED

Browser-facing P9 data uses:

- `public.dashboard_p9_mae_lifecycle_cache_v1`;
- `public.dashboard_p9_mae_lifecycle_v1`;
- `public.dashboard_p9_mae_status_v1`.

The panel separates historical NOT_EVALUABLE state, prospective prediction coverage, scored events, incumbent/challenger MAE, ΔMAE, event-level downside and production guards.

`P9MaeStatusPanel` is visible in Forecast Accuracy and Model Lab. Dashboard CI is green.

Repo SQL:

`supabase/sql/dashboard_p9_mae_lifecycle_v1.sql`

## 10. P7 prospective

Historical frozen result:

- anchor MAE **7409.79**;
- challenger MAE **6339.99**;
- point gain **1069.80 / 14.44%**;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Prospective lane:

- model `gbr-l1-depth2-n50-lr003`;
- fingerprint `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- **16 immutable rows / 3 independent events / 0 scored**;
- collect/score only.

## 11. Long72

Last verified n=4:

- events `[10,16,21,23]`;
- anchor MAE **6942.59**;
- package MAE **6824.16**;
- point improvement **118.43 / 1.71%**;
- event improvement rate **75%**;
- worst event degradation **3633.23**.

No retuning/promotion.

## 12. P4a

Last verified:

- labeled READY **4/9**;
- 3 distinct previous-home-spacing values;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move the gate.

## 13. P11

Fresh odds readiness:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs **4 / 4**;
- >=3 bookmaker events **4**;
- T-24 / T-72 / T-168 **3 / 3 / 0**;
- model precommitted false;
- production false.

Continue append-only capture; never backfill closing odds.

## 14. Governance / known debt

Business minimum meaningful ΔMAE is still intentionally unset until independently derived from operational decisions.

P12/new feature families remain behind active prospective evidence protection.

Unrelated pre-existing Supabase security debt still includes:

- `public.dashboard_ticketing_fixture_coverage_v1` SECURITY DEFINER view;
- `public.export_historical_runtime_v1()` callable as SECURITY DEFINER by anon/authenticated;
- `public.get_structural_prior_v1(...)` callable as SECURITY DEFINER by anon/authenticated;
- intentional RLS-protected research tables with no browser policies.

The new P9 preflight itself is service-role-only and does not add browser exposure.

## 15. Cold-start command

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/CURRENT_MODEL.md`, `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`, `supabase/sql/p9_prospective_preflight_v1.sql`, `supabase/sql/structural_prior_fixture_date_tolerance_2026_10_26.sql`, `supabase/sql/dashboard_p9_mae_lifecycle_v1.sql` and both P9 precommits. Query live status fresh. Historical P9 is 9/9 but NOT_EVALUABLE; never repair it retrospectively. P9 prospective scheduler/gateway/preflight are live. Fresh 10-day preflight is 0 critical / 0 watch with six targets READY. First T-48 is 2026-10-28 17:00 UTC. Event 443 has prior 40 before cutoff; capacity gaps for 447/603 are resolved with priors 45/46. Watch event 448 for a genuine snapshot and event 452 for upstream fixture-round data. P7 has 16 rows / 3 events / 0 scores. Long72 has 4 scores. P4a is 4/9. P11 is collecting. Keep production unchanged and optimize toward prospective event-balanced MAE.
