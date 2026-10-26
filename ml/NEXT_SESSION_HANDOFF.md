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

Canonical current plan:

`ml/EXECUTION_PLAN_CURRENT.md`

## 2. Immediate execution order

1. protect ticketing acquisition and all PIT evidence lanes;
2. keep P9 scheduler/gateway and target-incumbent readiness healthy before every immutable T-48/T-24 window;
3. resolve future verified-capacity / fixture-round metadata gaps without inventing values;
4. collect immutable P9 predictions only inside precommitted windows;
5. score P7/P9 only after genuine attendance outcomes arrive;
6. continue Long72/P4a/P11 frozen accumulation without retuning;
7. derive business minimum meaningful ΔMAE;
8. choose any new challenger by expected incremental prospective MAE reduction.

## 3. P9 historical v1 — CLOSED / NOT EVALUABLE

Live canonical gate:

- T-168: **9/9 events / 9 clubs**;
- `design_precommitted=true`;
- `full_window_gate_open=true`;
- target-free manifests registered: 2.

Frozen result:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Support:

- T-24: 11 comparator targets, **0 support-ready**;
- T-48: 9 comparator targets, **0 support-ready**;
- attendance labels remained unopened;
- no learner MAE result was produced.

Root cause is historical incumbent-ledger coverage, not booking-curve coverage. Do not backfill historical incumbents and call them PIT.

Read:

`ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`

Canonical machine sources:

- `public.p9_learner_gate_status_v1()`;
- `public.p9_historical_cohort_status_v1()`.

Do not use legacy `public.p9_booking_curve_readiness_v1()` for learner/precommit truth.

## 4. P9 prospective v1 — ACTIVE / HIGHEST TIME-CRITICAL LANE

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen learner:

`PIT booking-curve similarity -> k=5 prior curves -> same-incumbent-family PIT residuals -> median residual -> incumbent correction`

Rules:

- T-48 / T-24 only;
- k=5;
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

The `p9_booking_curve_prospective_v1` Edge Function is deployed. End-to-end GitHub OIDC -> Supabase -> target-free export -> freeze -> builder -> scoring -> safety assertions has passed on `main`.

Current state:

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

If a window produces no prediction because frozen support is insufficient, record that fact. Do not relax the rule.

## 5. P9 first-window safeguard — FIXED 2026-10-26

Pre-window audit found event **443 Cracovia–Motor** had healthy booking snapshots but no target incumbent.

Root cause:

- verified ticketing kickoff: **2026-10-30 17:00 UTC**;
- `sporting_league_matches_shadow.event_date`: **2026-10-31** round-date placeholder;
- old Structural Prior resolver required exact Warsaw date;
- result: `missing_fixture_round` -> no Structural Prior -> future P9 risk `NO_TARGET_INCUMBENT`.

Live resolver and repo source were hardened:

`supabase/sql/structural_prior_fixture_date_tolerance_2026_10_26.sql`

Rule:

1. exact Warsaw date first;
2. otherwise exact aliased home/away pair may fall back only if exactly one matching fixture exists within ±3 days;
3. zero or multiple nearby fixtures fail closed.

No ticket-event kickoff is changed. Club matching remains exact through verified aliases.

Structural Prior Materializer workflow now watches this patch and was rerun successfully:

- workflow run: `40358782359`;
- validate: success;
- materialize: success;
- event 443 Structural Prior ID: **40**;
- horizon: **T-7**;
- P50: **10632.324992331794**;
- capacity: **15016**;
- `point_in_time_validated=true`;
- generated/persisted: **2026-10-26 16:25 UTC**;
- P9 T-48 cutoff: **2026-10-28 17:00 UTC**;
- persisted before P9 T-48: **true**.

The materializer rebuilt features at `target_as_of_at=2026-10-23 17:00 UTC`. The current feature builder explicitly filters historical/current attendance before the cutoff and reconstructs sporting state only from completed fixtures strictly before the PIT local date. `backfilled_pit_forecast=true` therefore describes late materialization relative to the Structural Prior's own T-7 horizon, not use of future feature data.

For P9, this row genuinely exists before the P9 T-48 decision cutoff. `export_p9_prospective_incumbent_catalog_v1` additionally requires both source `as_of_at <= analogous_cutoff_at` and `created_at <= analogous_cutoff_at`.

The live forecast orchestrator immediately processed event 443 after persistence.

Other first-window targets already have PIT-validated Structural Priors:

- event 446 Wisła Płock–Piast;
- event 6 Lech–Wisła Kraków;
- event 444 GKS Katowice–Widzew.

Known later metadata gaps:

- event 447 Raków–Pogoń: `missing_capacity`;
- event 603 Korona–Radomiak: `missing_capacity`;
- event 452 Pogoń–Śląsk: `missing_fixture_round` because the later round is not yet present in sporting shadow.

Treat these as acquisition/metadata reliability tasks, not learner-design failures.

## 6. Panel / MAE visibility — LIVE AND SECURITY-HARDENED

Browser-facing P9 data uses a safe cache pattern; browser does not execute private-reading research functions directly.

Contract:

- `public.dashboard_p9_mae_lifecycle_cache_v1`;
- `public.dashboard_p9_mae_lifecycle_v1`;
- `public.dashboard_p9_mae_status_v1`.

The panel separates historical readiness/NOT_EVALUABLE, prospective predictions, scored events, incumbent/challenger MAE, ΔMAE, event-level downside and production guards.

Security verification:

- anon can read safe cache/view;
- anon cannot call the private-reading P9 prospective summary directly;
- P9 status view is `security_invoker`, not SECURITY DEFINER;
- Supabase security advisor no longer flags the P9 MAE view.

Reproducible SQL:

`supabase/sql/dashboard_p9_mae_lifecycle_v1.sql`

Panel repo:

`NiedzielX/BeyondTicketingPanel`

`P9MaeStatusPanel` is visible in Forecast Accuracy and Model Lab. Dashboard CI is green.

## 7. P7 prospective

Frozen historical result:

- anchor MAE **7409.79**;
- challenger MAE **6339.99**;
- point gain **1069.80 / 14.44%**;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Prospective lane:

- model `gbr-l1-depth2-n50-lr003`;
- fingerprint `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- **16 immutable rows / 3 independent events / 0 scored**;
- no tuning; collect/score only.

## 8. Long72

Last verified n=4:

- events `[10,16,21,23]`;
- anchor event-balanced MAE **6942.59**;
- package MAE **6824.16**;
- point improvement **118.43 / 1.71%**;
- event improvement rate **75%**;
- worst event degradation **3633.23**.

Not promotion evidence. Do not retune.

## 9. P4a

Last verified:

- labeled READY **4/9**;
- 3 distinct previous-home-spacing values;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move this gate.

## 10. P11

Fresh odds readiness:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs **4 / 4**;
- >=3 bookmaker events **4**;
- T-24 / T-72 / T-168 coverage **3 / 3 / 0**;
- model precommitted false;
- production false.

Continue append-only capture; never backfill closing odds.

## 11. Ticketing acquisition

Current league source coverage last verified **18/18**.

Preserve:

- fixture watchdog;
- RoboTicket discovery/private candidate buffer/promotion;
- Stellis collectors;
- original `captured_at` on promotion;
- hidden/unknown availability != zero;
- completed-match visibility in panel.

## 12. Governance

Business minimum meaningful ΔMAE is intentionally unset until independently derived from operational decisions.

P12/new feature families stay behind active prospective evidence protection. Rank new hypotheses by expected incremental prospective MAE impact, not novelty.

## 13. Known debt not introduced by P9 work

Supabase advisor still reports unrelated pre-existing items including:

- `public.dashboard_ticketing_fixture_coverage_v1` SECURITY DEFINER view;
- older SECURITY DEFINER functions callable by anon/authenticated;
- intentional private RLS tables without browser policies;
- several unindexed foreign keys.

Do not conflate those with the P9 lifecycle path.

## 14. Cold-start command

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/CURRENT_MODEL.md`, `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`, `supabase/sql/structural_prior_fixture_date_tolerance_2026_10_26.sql`, `supabase/sql/dashboard_p9_mae_lifecycle_v1.sql` and both P9 precommits. Query live status fresh. Historical P9 is 9/9 but NOT_EVALUABLE; never repair it retrospectively. P9 prospective scheduler/gateway are deployed and E2E green. The first T-48 window is 2026-10-28 17:00 UTC. Event 443 Cracovia–Motor now has PIT-validated Structural Prior ID 40 persisted before that cutoff after a fail-closed round-date-placeholder resolver fix; events 446, 6 and 444 already have valid priors. Next reliability gaps are verified capacities for events 447/603 and later round metadata for event 452. P7 has 16 rows / 3 events / 0 scores. Long72 has 4 scores. P4a is 4/9. P11 is collecting. Keep production unchanged and optimize toward prospective event-balanced MAE.
