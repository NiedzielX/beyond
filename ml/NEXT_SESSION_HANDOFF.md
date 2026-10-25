# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-25 11:20 Europe/Warsaw**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

This document is the operational handoff between ChatGPT/Codex sessions. It records what is on `main`, what is still on the active development branch, what is already live in Supabase, and the exact next work order.

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Current phase: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

No research result activates production automatically.

---

## 2. Repository / environment state

### Canonical repository

`NiedzielX/beyond`

### Main branch

`main`

`main` already contains the canonical MAE Roadmap v4, P9/P10/P10b results, Governance v2, P4a/P7 contracts and P11a v1 DB contract.

### Active development branch

`ml/p9-p11-execution-2026-10-24`

This branch contains the next P11a implementation slice and must not be forgotten or recreated from scratch.

Important files on this branch:

- `ml/EXECUTION_PLAN_2026-10-24.md`;
- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

### Supabase project

Project ref:

`adchzwqboeekhokapxqi`

Important: **the live Supabase environment is temporarily ahead of `main` for P11a v2**.

Already live in Supabase:

- `private.p11_market_odds_observations_v2`;
- `public.p11_market_capture_inputs_v2(integer)`;
- `public.insert_p11_market_odds_capture_v2(jsonb)`;
- `public.p11_market_context_as_known_v2(bigint,timestamptz)`;
- `public.p11_market_odds_readiness_v2()`;
- Edge Function `p11_odds_capture_v2` — **ACTIVE, version 2**, `verify_jwt=false` because the function performs its own GitHub OIDC verification.

The source for this live Edge Function is currently on the active branch above, not yet canonical on `main`.

Do not deploy a different P11 function from memory. Merge/reconcile the branch first.

---

## 3. Fresh readiness checkpoint — 2026-10-25 10:18 UTC

Canonical source:

`select public.ml_research_readiness_v1();`

### Long72

- reproducible prediction rows: **90**;
- genuine scored events: **0**;
- latest reproducible `as_of_at`: `2026-10-24T16:20:02.672Z`;
- first genuine score gate: **closed**.

### P7 Long168

- independent events with valid rows >72h: **8/9**;
- rows >72h: **110**;
- start gate: **closed**.

Important diagnostic:

Event 6 (Lech Poznań vs Wisła Kraków, kickoff `2026-10-31 16:30Z`) was expected to enter the <=168h window on 2026-10-24, but the canonical P7 readiness is still 8/9 on 2026-10-25.

**Do not assume P7 automatically unlocked. First investigate why event 6 is not counted.**

Check in this order:

1. event 6 snapshots after the T-168 boundary;
2. Long168 export eligibility/window rule;
3. requested snapshot/as-of selection;
4. whether the latest exporter/readiness state includes event 6;
5. only if canonical readiness reaches 9/9, execute the already-frozen P7 sequence.

Do not lower the 9-event threshold.

### P4a fixture context

- sidecar rows: **90**;
- READY rows: **88**;
- independent READY events: **5** — IDs `10,16,21,22,23`;
- genuine labeled READY events: **0**;
- primary feature: `previous_home_match_days`;
- target-free values: `13,36,15,14,15`;
- distinct values: **4**;
- research gate: `>=9 labeled + >=3 distinct labeled values` — **closed**.

P4a is frozen. Do not redesign after labels arrive.

### P4b next-opponent

- sidecar rows: **90**;
- READY rows: **0**.

### P9 booking curve

Current completed reference coverage:

- 168h: **4/9 events / 4 clubs**;
- 72h: **7 events / 5 clubs**;
- 48h: **10 events / 6 clubs**;
- 24h: **13 events / 8 clubs**.

`P9_BOOKING_CURVE_168_START = false`.

Do not fit the first learnable P9 residual model yet.

### P11a odds v2

`public.p11_market_odds_readiness_v2()` at 2026-10-25 10:19 UTC:

- provider: `the-odds-api-v4`;
- provider selected: **true**;
- genuine PIT 1X2 events: **0**;
- clubs with PIT 1X2: **0**;
- events with >=3 bookmakers: **0**;
- model precommitted: **false**;
- status: `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`;
- raw v2 table rows: **0**.

This is correct. No synthetic/backfilled closing odds were inserted.

---

## 4. P11a v2 architecture already implemented

Provider target:

**The Odds API v4** / `soccer_poland_ekstraklasa` / pre-match `h2h` (1X2).

### Raw capture contract

Store bookmaker-level quotes append-only, not one arbitrary bookmaker and not only a pre-aggregated average.

Persisted lineage includes:

- local `ticket_event_id`;
- provider event ID;
- provider/bookmaker key;
- capture batch UUID;
- actual `captured_at`;
- provider commence/update timestamps;
- raw decimal home/draw/away prices;
- payload SHA-256;
- mapping method;
- canonical club keys;
- provider/local kickoff delta.

### Mapping

Fail closed unless:

- both provider teams resolve through verified aliases;
- home/away identity matches exactly at canonical club-key level;
- kickoff is within 5,400 seconds;
- only one provider event matches.

No fuzzy guess is allowed on ambiguous fixtures.

### Consensus

`p11_market_context_as_known_v2`:

1. chooses only the latest capture batch known at requested `as_of_at` and strictly before kickoff;
2. de-vigs each bookmaker independently;
3. takes median bookmaker probabilities;
4. renormalizes consensus to sum to one;
5. exposes home/draw/away probabilities, favorite probability and normalized outcome entropy.

Semantic guard:

`outcome_uncertainty != expected_match_quality`

Expected match quality requires a separate signal/precommit.

### Edge Function security

`p11_odds_capture_v2` validates GitHub Actions OIDC itself:

- issuer: GitHub Actions token issuer;
- audience: `beyond-p11-odds-capture`;
- repository: `NiedzielX/beyond`;
- ref: `refs/heads/main`.

The GitHub workflow on the active branch is **manual only**. No schedule has been enabled.

### Required external secret

The Edge Function expects:

`THE_ODDS_API_KEY`

Do not store it in GitHub/repo files.

Its presence still needs to be configured/verified in Supabase Edge Function secrets before the first capture.

---

## 5. Closed research results — do not reopen by tuning

### P10 v1

Pooling helped relative to the exact same weaker local HGB architecture:

- local MAE `2120.93`;
- pooled MAE `2057.46`;
- `ΔMAE=-63.47`;
- 95% CI `[-106.29,-23.20]`;
- 3/3 folds + 5/5 horizons improved;
- status `POINT_GAIN_UNCERTAINTY_LIMITED`.

### P10b

The same pooled architecture lost to the actual frozen Pre-Live v3 champion:

- Pre-Live v3 MAE `1919.92`;
- pooled MAE `2067.43`;
- challenger-incumbent `ΔMAE=+147.51`;
- relative degradation `+7.68%`;
- 95% CI `[+82.97,+210.67]`;
- 0/4 folds improved;
- 0/5 horizons improved;
- status `NO_RESEARCH_GAIN`.

Do not retune P10/P10b. Future pooling requires a materially new mechanism and a new precommit.

---

## 6. Governance v2

Canonical statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

`ROBUST_RESEARCH_ADVANCE` is impossible until a **business-derived minimum meaningful MAE improvement** is predeclared.

Do not invent `100 seats` or `3%` from observed model results.

Business threshold work should derive value from downstream decisions such as staffing, transport, security, catering or other costs affected by attendance error.

---

## 7. Exact next-session work order

### Step 1 — reconcile GitHub first

Start from:

`ml/p9-p11-execution-2026-10-24`

Compare it to `main`. Preserve all P11a v2 files listed above. Merge the branch after CI/review; do not recreate the same implementation on another branch.

### Step 2 — diagnose P7 event 6 before any new P7 modeling

Canonical readiness is unexpectedly still 8/9.

Find why event 6 is not counted after entering the Long168 window. If and only if `ml_research_readiness_v1()` says 9/9, run the frozen P7 executor exactly as precommitted.

### Step 3 — make first genuine P11a capture possible

1. verify/configure `THE_ODDS_API_KEY` in Supabase Edge Function secrets;
2. merge P11 v2 source/workflow to `main`;
3. run workflow manually once;
4. inspect mapping results, bookmaker count, provider quota and inserted raw rows;
5. verify `p11_market_context_as_known_v2` for captured events;
6. keep schedule **off** until the first manual capture is audited.

Do not precommit an odds model from zero events.

### Step 4 — P9 continues collecting

Keep genuine 168h trajectory coverage growing. Allowed work before 9/9:

- coverage/readiness reporting;
- leakage/lineage tests;
- freeze-manifest tooling;
- representation audits.

Not allowed:

- selecting/tuning the first learnable P9 model before the gate and learner precommit.

### Step 5 — define meaningful MAE threshold

Derive a practical minimum MAE improvement from business impact, independently of model scorecards.

### Step 6 — P4a / Long72

When genuine labels appear:

- attach/score only as designed;
- do not retune frozen packages from the first events;
- P4a remains blocked until 9 labeled events and 3 distinct labeled spacing values.

---

## 8. Never do these

- do not backfill closing odds as if they were historical PIT observations;
- do not insert synthetic odds into P11 v2;
- do not use future target trajectory points in P9;
- do not lower P7/P9/P4 gates because data is slow;
- do not reopen P10/P10b with a hyperparameter sweep;
- do not claim historical exposed research as prospective evidence;
- do not change `live_adjustment` from zero without reviewed promotion;
- do not enable the old ChatGPT Beyond readiness automations — they were explicitly disabled by the user.

---

## 9. Cold-start command for the next AI session

> Read `AI_BOOTSTRAP.md`, then `ml/NEXT_SESSION_HANDOFF.md`, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md` and `ml/MAE_RESEARCH_ROADMAP_V4.md`. Check `public.ml_research_readiness_v1()` fresh. Then compare `main` with `ml/p9-p11-execution-2026-10-24`. Do not rebuild or retune closed experiments. First resolve P7 event 6 readiness and finish P11a v2 merge/first genuine capture while P9 continues accumulating data.
