# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-25**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md` — **latest operational truth: main vs active branch vs live Supabase**;
2. `ml/EXECUTION_PLAN_CURRENT.md` — exact next work order;
3. `ml/PROGRESS_TRACKING.md` — latest canonical status snapshot;
4. `ml/MAE_RESEARCH_ROADMAP_V4.md` — canonical literature-grounded strategy;
5. `ml/results/P10B_POOLED_VS_PRELIVE_V3_V1_2026-10-23.md` and `ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md` when touching pooled/global research;
6. `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md` before changing P9 representation or fitting a learner;
7. `ml/P11_MATCH_ATTRACTIVENESS_CONTEXT_V1_PLAN.md` plus the P11 v2 files listed below when touching market/commercial context;
8. `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md` for P4/P5;
9. `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` for P7;
10. `ml/CURRENT_MODEL.md`, `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`, `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`, `ml/MODEL_PROMOTION_GOVERNANCE_V1.md` as relevant.

Do not start from Roadmap v3. Do not rebuild frozen historical benchmarks merely to recover context.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Repository state

Canonical repo:

`NiedzielX/beyond`

Active development branch:

`ml/p9-p11-execution-2026-10-24`

This branch contains the current P11a v2 implementation slice. Do not recreate it on another branch before comparing/merging it.

Important P11 v2 files on that branch:

- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`;
- `ml/EXECUTION_PLAN_2026-10-24.md`.

## Live Supabase state

Project:

`adchzwqboeekhokapxqi`

P11a v2 live DB contract exists:

- `private.p11_market_odds_observations_v2`;
- `public.p11_market_capture_inputs_v2(integer)`;
- `public.insert_p11_market_odds_capture_v2(jsonb)`;
- `public.p11_market_context_as_known_v2(bigint,timestamptz)`;
- `public.p11_market_odds_readiness_v2()`.

Edge Function:

`p11_odds_capture_v2` — **ACTIVE, version 2**.

It performs its own GitHub Actions OIDC verification and therefore is deployed with platform `verify_jwt=false`.

The live Supabase environment is temporarily ahead of `main` for P11 v2 source. Reconcile the active branch before changing/deploying this function again.

No P11 genuine odds capture has been inserted yet.

The function expects secret:

`THE_ODDS_API_KEY`

Do not put the value in repo files. Configure/verify it in Supabase Edge Function secrets before first genuine capture.

## Fresh central readiness — 2026-10-25 10:18 UTC

Always re-read live state with:

`public.ml_research_readiness_v1()`

Recorded checkpoint:

### Long72

- reproducible rows: `90`;
- genuine scored events: `0`;
- latest `as_of_at`: `2026-10-24T16:20:02.672Z`.

### P7 Long168

- independent events >72h: **8/9**;
- rows >72h: `110`;
- start trigger: **false**.

Important: event 6 was expected to enter the <=168h window on 2026-10-24, but readiness remains 8/9 on 2026-10-25.

**Next P7 action is diagnosis, not model execution.**

Check event 6 snapshots/window/export/readiness. Only execute P7 when canonical readiness itself says 9/9.

### P4a

- 5 READY independent events;
- event IDs `10,16,21,22,23`;
- 0 genuine labels;
- primary feature `previous_home_match_days`;
- target-free values `13,36,15,14,15`;
- gate `>=9 labeled + >=3 distinct labeled values` — closed.

### P9

- 168h: **4/9** events / 4 clubs;
- 72h: 7 events / 5 clubs;
- 48h: 10 events / 6 clubs;
- 24h: 13 events / 8 clubs;
- learnable model precommitted: false;
- `P9_BOOKING_CURVE_168_START = false`.

Do not fit the first P9 learner yet.

### P11a v2

`public.p11_market_odds_readiness_v2()`:

- provider: `the-odds-api-v4`;
- provider selected: true;
- genuine PIT 1X2 events: `0`;
- raw v2 rows: `0`;
- model precommitted: false;
- status `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`.

This is intentional. Never insert synthetic/backfilled closing odds.

## P10 / P10b — CLOSED for this architecture

P10 v1:

- local HGB MAE `2120.93`;
- pooled HGB MAE `2057.46`;
- `ΔMAE=-63.47`;
- 95% CI `[-106.29,-23.20]`;
- status `POINT_GAIN_UNCERTAINTY_LIMITED`.

P10b against actual frozen Pre-Live v3:

- Pre-Live v3 MAE `1919.92`;
- pooled MAE `2067.43`;
- challenger-incumbent `ΔMAE=+147.51`;
- relative degradation `+7.68%`;
- 95% CI `[+82.97,+210.67]`;
- status `NO_RESEARCH_GAIN`.

Do not retune P10/P10b. Any future pooling work requires a materially new mechanism and a new precommit.

## P9 — Booking Curve / Trajectory Shape

Concept:

`PIT inventory path -> normalized trajectory -> historical curve similarity -> pickup distribution -> remaining-demand estimate -> structural residual challenger`

Hard rules:

- no target observation after `as_of_at`;
- no target-future canonical point;
- no self-event reference;
- reference event completed before target cutoff;
- public inventory is a demand proxy, not confirmed paid sales.

At 9 genuine full-168h completed references, freeze the learner contract before model-result comparison.

## P11 — Match Attractiveness / Commercial Context

Priority:

1. PIT odds / outcome uncertainty / stakes / rivalry;
2. price / promotion;
3. lineup / star strength / verified absences;
4. weather / media/social attention.

P11a v2 design:

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

1. **diagnose why P7 is still 8/9 and why event 6 is not counted**;
2. reconcile/merge `ml/p9-p11-execution-2026-10-24` to `main`;
3. configure/verify `THE_ODDS_API_KEY` in Supabase secrets;
4. run one manual P11a v2 capture and audit it; keep schedule off;
5. keep P9 capture running toward 9 full-168h events;
6. derive the business minimum meaningful MAE threshold;
7. keep P4a/Long72 frozen evidence collection unchanged.

The old ChatGPT Beyond readiness automations are intentionally disabled. Do not enable them implicitly.