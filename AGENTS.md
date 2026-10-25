# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Read `ml/NEXT_SESSION_HANDOFF.md`.
3. Read `ml/EXECUTION_PLAN_CURRENT.md`.
4. Read `ml/PROGRESS_TRACKING.md` for the latest canonical state.
5. Read `ml/MAE_RESEARCH_ROADMAP_V4.md` for strategy.
6. Query `public.ml_research_readiness_v1()` fresh before acting on any data gate.
7. Compare `main` with active branch `ml/p9-p11-execution-2026-10-24` before touching P11a v2.
8. Never rebuild frozen history merely to recover context.
9. Never store secrets/tokens/service-role keys in repo files.

## Core principle

> **The objective is lower true out-of-sample MAE, not model complexity.**

Current phase: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Repository / live-state warning

The live Supabase environment is currently temporarily ahead of `main` for P11a v2.

Active branch:

`ml/p9-p11-execution-2026-10-24`

It contains:

- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

Live Supabase project:

`adchzwqboeekhokapxqi`

Already live:

- P11 v2 DB table/RPCs;
- Edge Function `p11_odds_capture_v2`, ACTIVE v2.

Do not redeploy from memory or create a parallel implementation. Reconcile/merge the active branch first.

## Validation / evidence

Historical/global:

- strict expanding temporal folds;
- complete `match_key` blocking across all horizons;
- no future-season leakage;
- persist exact identities/manifest SHA.

Live/context:

- `ticket_event` is the independent unit;
- strict forward-event validation by kickoff;
- tied kickoffs cannot train one another;
- no random snapshot split as headline evidence;
- freeze target-free identities/features before labels/model-result selection whenever prospective evidence is possible.

## Governance v2

Use `ml/research_advance_governance_v2.py`.

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

A positive point estimate alone is not a robust advance. Robust advancement requires a predeclared business-derived minimum meaningful MAE improvement plus precision, stability and evidence-integrity gates.

Do not infer the meaningful threshold from the experiment being judged.

## Fresh readiness checkpoint recorded 2026-10-25

Always query fresh before acting, but current recorded state is:

- Long72: `90` reproducible rows / `0` genuine scored events;
- P7 Long168: **8/9** independent events — gate closed;
- P4a: `5` READY / `0` labels — gate closed;
- P9 full 168h: **4/9** — gate closed;
- P11a v2 genuine odds events: `0`.

### P7 diagnostic first

Event 6 was expected to enter the <=168h Long168 window, but readiness is still 8/9 on 2026-10-25.

Do **not** run the P7 model because the clock passed. Investigate event 6 snapshot/window/export/readiness first. Execute only after canonical readiness itself returns 9/9.

## P10 / P10b — frozen closeout

P10 v1:

- local HGB `2120.93`;
- pooled HGB `2057.46`;
- `ΔMAE=-63.47`;
- status `POINT_GAIN_UNCERTAINTY_LIMITED`.

P10b against actual frozen Pre-Live v3:

- incumbent `1919.92`;
- pooled `2067.43`;
- challenger-incumbent `ΔMAE=+147.51`;
- 95% CI `[+82.97,+210.67]`;
- 0/4 folds and 0/5 horizons improved;
- status `NO_RESEARCH_GAIN`.

Do **not** retune P10/P10b after these results. A future pooling experiment requires a materially new mechanism and a new precommit.

## P9 booking curves

Use existing trajectory infrastructure; do not duplicate it.

Hard rules:

- no target snapshot after `as_of_at`;
- no future target canonical point;
- no self-event historical reference;
- reference event completed before target cutoff;
- public inventory is a demand proxy, not confirmed sales.

Current full-168h coverage: **4/9** genuine completed reference events.

Do not fit the first learnable P9 residual challenger before the gate. At 9/9, freeze the learner contract before opening model-result comparisons.

## P11a market odds v2

Provider target:

`the-odds-api-v4` / `soccer_poland_ekstraklasa` / pre-match `h2h`.

Architecture:

- append-only raw bookmaker-level 1X2 quotes;
- provider event + capture batch lineage;
- verified alias mapping;
- kickoff tolerance 5,400 seconds;
- ambiguous mappings fail closed;
- actual capture timestamp is authoritative;
- source payload SHA-256;
- de-vig each bookmaker first;
- median bookmaker consensus, then renormalize;
- as-known lookup uses only batches captured by requested cutoff and pre-kickoff.

Semantic guard:

`outcome_uncertainty != expected_match_quality`

Current state:

- DB contract live;
- Edge Function ACTIVE v2;
- genuine raw rows `0`;
- model precommitted `false`;
- automated schedule off.

Required secret:

`THE_ODDS_API_KEY`

Configure/verify it in Supabase secrets; never commit it.

First capture must be manual and audited before any schedule is enabled.

Never backfill closing odds into earlier PIT cutoffs.

## P4a / Long72

P4a remains frozen/data-bound:

- 5 READY events;
- 0 labels;
- gate `>=9` labeled + `>=3` distinct labeled spacing values;
- fixed previous-home-spacing challenger.

Long72 remains immutable forecast-before-label evidence. Inspect the first genuine score when it appears, but do not retune the package from it.

## Closed loops

Do not reopen without materially new evidence/mechanism:

- estimator-only tuning;
- estimator uncertainty re-analysis on same sample;
- simple structural/live shrinkage;
- historical Long72 incremental-value loop;
- simple club/opponent post-hoc calibration;
- fixed P10/P10b pooled-HGB direct replacement;
- blind model or weight sweeps.

## Immediate development order

1. diagnose event 6 / P7 still 8/9;
2. reconcile and merge `ml/p9-p11-execution-2026-10-24`;
3. configure/verify `THE_ODDS_API_KEY`;
4. run one manual P11a v2 capture and audit it; keep schedule off;
5. keep P9 genuine 168h curve capture running;
6. derive the business minimum meaningful MAE threshold;
7. keep P4a/Long72 evidence collection unchanged.

The old ChatGPT Beyond readiness automations are intentionally disabled. Do not enable them implicitly.

No research result activates production automatically.