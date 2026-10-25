# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-25 11:45 Europe/Warsaw**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md` — **latest operational truth: main vs active branch vs live Supabase**;
2. `ml/EXECUTION_PLAN_CURRENT.md` — exact next work order;
3. `ml/PROGRESS_TRACKING.md` — latest canonical status snapshot;
4. `ml/MAE_RESEARCH_ROADMAP_V4.md` — canonical literature-grounded strategy;
5. `ml/results/P10B_POOLED_VS_PRELIVE_V3_V1_2026-10-23.md` and `ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md` when touching pooled/global research;
6. `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md` plus P9a files before changing booking-curve representation/freeze logic;
7. `ml/P11_MATCH_ATTRACTIVENESS_CONTEXT_V1_PLAN.md` plus P11 v2 files before changing market/commercial context;
8. `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md` for P4/P5;
9. `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` for P7;
10. `ml/CURRENT_MODEL.md`, `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`, `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`, `ml/MODEL_PROMOTION_GOVERNANCE_V1.md` as relevant.

Do not start from Roadmap v3. Do not rebuild frozen historical benchmarks merely to recover context.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Immediate operational order

Current execution order is:

`reconcile active branch with main -> merge P9a/P11a source to main -> first genuine manual P11 capture -> audit -> P9a freeze audit -> Long72/P4a outcome-sync diagnostic`

P11 is time-sensitive because genuine pre-match odds are perishable PIT evidence. Do not delay a valid capture merely to work on a data-bound frozen experiment.

## Repository state

Canonical repo:

`NiedzielX/beyond`

Active development branch:

`ml/p9-p11-execution-2026-10-24`

Fresh comparison on 2026-10-25:

- active branch is **32 commits ahead** of `main`;
- active branch is **14 commits behind** `main`;
- status: diverged.

This branch contains both P9a freeze tooling and P11a v2 capture. Do not recreate either implementation.

Required reconciliation:

1. bring canonical `main` changes into the active branch;
2. preserve active P9a/P11a implementation files;
3. run CI/tests;
4. merge the active branch back to `main`.

### P9a branch files

- `ml/p9a_booking_curve_freeze_v1.py`;
- `ml/test_p9a_booking_curve_freeze_v1.py`;
- `supabase/sql/p9a_booking_curve_freeze_v1.sql`;
- `supabase/functions/p9a_booking_curve_export_v1/index.ts`;
- `.github/workflows/p9a-booking-curve-freeze-v1.yml`.

### P11a v2 branch files

- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

## Live Supabase state

Project:

`adchzwqboeekhokapxqi`

### P9a live

- `public.export_p9a_booking_curve_inputs_v1(integer)`;
- `public.export_p9a_booking_curve_labels_v1(bigint[])` — labels remain separate; do not call casually;
- Edge Function `p9a_booking_curve_export_v1` — ACTIVE v1.

Latest target-free export:

- T-24: `18` target events / `19` reference events;
- T-48: `15` target events / `19` reference events;
- `target_values_used=false`;
- `post_cutoff_target_snapshots_exported=false`;
- `production_change=false`.

P9a freezes representation/reference identities only. It does not train/select a learner and does not authorize label opening.

### P11a v2 live

- DB capture/consensus/readiness contract is live;
- Edge Function `p11_odds_capture_v2` — **ACTIVE v2**;
- function validates GitHub Actions OIDC itself;
- raw genuine odds rows: `0` at latest check;
- automatic schedule: off.

Important correction: P11 deployment is already done. The missing step is the first genuine provider capture.

Required external secret:

`THE_ODDS_API_KEY`

Do not put its value in repo files. Verify/configure it in Supabase Edge Function secrets before first genuine capture.

## Fresh central readiness — 2026-10-25 10:39 UTC

Always re-read live state with:

`public.ml_research_readiness_v1()`

### Long72

- reproducible rows: `90`;
- genuine scored events: `0`;
- latest `as_of_at`: `2026-10-24T16:20:02.672Z`.

### P7 Long168

- independent eligible events: **8/9**;
- rows >72h: `110`;
- start trigger: false.

The earlier assumption that event 6 would unlock P7 after merely entering the T-168 window was incorrect.

Resolved contract behavior:

- Long168 requires a completed event;
- Long168 requires genuine `actual_attendance`;
- a T-168 snapshot alone is insufficient.

Event 6 — Lech Poznań vs Wisła Kraków, kickoff `2026-10-31 16:30 UTC` — can only become the ninth event after the match and genuine attendance outcome are available.

Do not run more P7 diagnostic/model work now. Keep the contract frozen and execute only if canonical readiness reaches 9/9.

### P4a

- 5 READY independent events;
- 0 genuine labels;
- primary feature `previous_home_match_days`;
- 4 distinct target-free values;
- gate `>=9 labeled + >=3 distinct labeled values` — closed.

### P9 full-168h

- 168h: **4/9** events / 4 clubs;
- 72h: 7 events / 5 clubs;
- 48h: 10 events / 6 clubs;
- 24h: 13 events / 8 clubs;
- learnable model precommitted: false;
- `P9_BOOKING_CURVE_168_START=false`.

Do not fit the first full-window P9 learner yet.

### P11a v2

`public.p11_market_odds_readiness_v2()`:

- provider: `the-odds-api-v4`;
- provider selected: true;
- genuine PIT 1X2 events: `0`;
- raw v2 rows: `0`;
- model precommitted: false;
- status `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`.

Current capture inputs include event 21 (Jagiellonia–Wisła Płock), event 22 (Legia–Lech), event 23 (Śląsk–Wieczysta) on 2026-10-25 and event 6 (Lech–Wisła Kraków) on 2026-10-31.

Never insert synthetic/backfilled closing odds.

## P10 / P10b — CLOSED for this architecture

P10 v1:

- local HGB MAE `2120.93`;
- pooled HGB MAE `2057.46`;
- `ΔMAE=-63.47`;
- 95% CI `[-106.29,-23.20]`;
- status `POINT_GAIN_UNCERTAINTY_LIMITED`.

P10b against frozen Pre-Live v3:

- Pre-Live v3 MAE `1919.92`;
- pooled MAE `2067.43`;
- challenger-incumbent `ΔMAE=+147.51`;
- relative degradation `+7.68%`;
- status `NO_RESEARCH_GAIN`.

Do not retune P10/P10b. Future pooling work requires a materially new mechanism and a new precommit.

## P9 hard rules

Concept:

`PIT inventory path -> normalized trajectory -> historical curve similarity -> pickup distribution -> remaining-demand estimate -> structural residual challenger`

Hard rules:

- no target observation after `as_of_at`;
- no target-future canonical point;
- no self-event reference;
- reference event completed before target cutoff;
- public inventory is a demand proxy, not confirmed paid sales.

P9a is a target-free T-24/T-48 freeze/audit layer. After branch merge, run/verify the main audit and require:

- `target_values_opened=false`;
- `model_training_performed=false`;
- future target snapshots not used;
- labels remain separate.

Do not confuse P9a with opening the full-168h learner, which remains blocked at 4/9.

## P11 hard rules

P11a v2:

- provider target: The Odds API v4;
- sport key: `soccer_poland_ekstraklasa`;
- pre-match `h2h` only;
- raw bookmaker-level append-only storage;
- deterministic verified-alias + kickoff mapping;
- fail closed on ambiguous fixture mapping;
- source payload SHA;
- de-vig each bookmaker first, then median consensus and renormalization;
- `outcome_uncertainty` is normalized 1X2 entropy;
- do not call it expected match quality.

First capture must be manual and audited. Keep automated schedule off until accepted.

## Governance v2

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

Robust advancement requires a predeclared business-derived minimum meaningful MAE improvement plus precision, stability and evidence-integrity gates.

Do not infer the threshold from the experiment being judged.

## Immediate development order

1. reconcile `ml/p9-p11-execution-2026-10-24` with current `main` while preserving P9a/P11a;
2. merge P9a/P11a source/workflows onto `main` after CI;
3. verify/configure `THE_ODDS_API_KEY`;
4. run exactly one genuine manual P11 capture and audit it; keep schedule off;
5. run/verify P9a target-free T-24/T-48 main freeze audit; do not open labels/train;
6. inspect Long72/P4a upstream actual-attendance/outcome sync because genuine labels remain zero;
7. keep full-168h P9 capture running toward 9 events;
8. keep P7 frozen at 8/9 until event 6 is completed and genuine attendance is available;
9. derive the business minimum meaningful MAE threshold.

The old ChatGPT Beyond readiness automations are intentionally disabled. Do not enable them implicitly.
