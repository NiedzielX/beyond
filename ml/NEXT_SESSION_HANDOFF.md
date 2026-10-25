# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-25 11:45 Europe/Warsaw**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

This document is the operational handoff between ChatGPT/Codex sessions. It records what is on `main`, what is still on the active development branch, what is already live in Supabase, and the exact current work order.

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Current phase: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

No research result activates production automatically.

---

## 2. Immediate execution priority

The current priority order is:

`branch reconciliation -> source/workflow on main -> first genuine manual P11 capture -> capture audit -> P9a freeze audit -> outcome-sync diagnostic`

P11 is time-sensitive because genuine pre-match market odds are perishable PIT evidence. They must be captured while genuinely knowable; they may not be reconstructed later from closing odds and treated as historical PIT observations.

At the latest check, `public.p11_market_capture_inputs_v2(14)` returned four relevant local events:

- event 23 — Śląsk Wrocław vs Wieczysta Kraków — `2026-10-25 11:15 UTC`;
- event 21 — Jagiellonia Białystok vs Wisła Płock — `2026-10-25 13:45 UTC`;
- event 22 — Legia Warszawa vs Lech Poznań — `2026-10-25 16:30 UTC`;
- event 6 — Lech Poznań vs Wisła Kraków — `2026-10-31 16:30 UTC`.

The first P11 capture must remain **manual and audited**. No automatic schedule is enabled.

---

## 3. Repository / environment state

### Canonical repository

`NiedzielX/beyond`

### Main branch

`main`

`main` contains the canonical Roadmap v4, Governance v2, frozen research contracts, current handoff and execution plan.

### Active development branch

`ml/p9-p11-execution-2026-10-24`

Fresh comparison on 2026-10-25:

- status: **diverged**;
- branch is **32 commits ahead** of `main`;
- branch is **14 commits behind** `main`.

Do not force-push, blindly merge, or recreate the implementation. The intended reconciliation sequence is:

1. merge current `main` into the active branch;
2. resolve/verify while preserving the active P9a/P11a implementation;
3. run CI/tests;
4. open/merge the active branch back to `main`.

Important P9a files on the active branch:

- `ml/p9a_booking_curve_freeze_v1.py`;
- `ml/test_p9a_booking_curve_freeze_v1.py`;
- `supabase/sql/p9a_booking_curve_freeze_v1.sql`;
- `supabase/functions/p9a_booking_curve_export_v1/index.ts`;
- `.github/workflows/p9a-booking-curve-freeze-v1.yml`.

Important P11a v2 files on the active branch:

- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

### Supabase project

Project ref:

`adchzwqboeekhokapxqi`

Already live:

#### P9a

- `public.export_p9a_booking_curve_inputs_v1(integer)`;
- `public.export_p9a_booking_curve_labels_v1(bigint[])` — labels remain separated and must not be opened casually;
- Edge Function `p9a_booking_curve_export_v1` — ACTIVE v1.

#### P11a v2

- `private.p11_market_odds_observations_v2`;
- `public.p11_market_capture_inputs_v2(integer)`;
- `public.insert_p11_market_odds_capture_v2(jsonb)`;
- `public.p11_market_context_as_known_v2(bigint,timestamptz)`;
- `public.p11_market_odds_readiness_v2()`;
- Edge Function `p11_odds_capture_v2` — **ACTIVE v2**;
- function-level platform JWT verification intentionally disabled because the function validates GitHub Actions OIDC itself;
- automatic odds schedule: **off**.

Important correction: the P11 Edge Function no longer needs deployment. The missing operational step is the first genuine provider capture.

---

## 4. Fresh readiness checkpoint — 2026-10-25 10:39 UTC

Canonical source:

`select public.ml_research_readiness_v1();`

### Long72

- reproducible prediction rows: **90**;
- genuine scored events: **0**;
- latest reproducible `as_of_at`: `2026-10-24T16:20:02.672Z`;
- first genuine score gate: closed.

### P7 Long168

- independent eligible events: **8/9**;
- rows >72h: **110**;
- start gate: closed.

The earlier assumption that event 6 would become the ninth event simply after entering the T-168 window was incorrect.

**Resolved cause:** the frozen Long168 exporter requires the event to be completed and to have genuine `actual_attendance`. A valid T-168 snapshot alone is insufficient.

Therefore event 6 — Lech Poznań vs Wisła Kraków, kickoff `2026-10-31 16:30 UTC` — can only become the ninth P7 event after:

1. the match is completed;
2. genuine attendance outcome is available upstream;
3. the frozen exporter/readiness function recognizes it under the unchanged contract.

Do not weaken this rule. Do not run P7 at 8/9.

### P4a fixture context

- READY independent events: **5**;
- genuine labeled READY events: **0**;
- previous-home-spacing distinct target-free values: **4**;
- research gate: `>=9 labeled events + >=3 distinct labeled values`;
- gate: closed.

P4a remains frozen.

### P9 full-168h booking curve

- 168h: **4/9 events / 4 clubs**;
- 72h: **7 events / 5 clubs**;
- 48h: **10 events / 6 clubs**;
- 24h: **13 events / 8 clubs**;
- `P9_BOOKING_CURVE_168_START=false`.

Do not fit the first learnable full-168h P9 residual model yet.

### P9a target-free freeze infrastructure

Live checked state:

- T-24: **18 target / 19 reference events**;
- T-48: **15 target / 19 reference events**;
- `target_values_used=false`;
- `post_cutoff_target_snapshots_exported=false`;
- `production_change=false`.

The harness freezes representation/reference/snapshot identities, excludes self-event references, requires references to be completed before target cutoff and keeps labels separate.

It does **not** train/select a learner.

### P11a v2

Latest `public.p11_market_odds_readiness_v2()` state:

- provider: `the-odds-api-v4`;
- provider selected: true;
- genuine PIT 1X2 events: **0**;
- clubs with PIT 1X2: **0**;
- events with >=3 bookmakers: **0**;
- model precommitted: false;
- raw v2 rows: **0**;
- status: `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`;
- `production_change=false`.

No synthetic or closing-odds backfill has been inserted.

---

## 5. P11a v2 contract already implemented

Provider:

**The Odds API v4** / `soccer_poland_ekstraklasa` / pre-match `h2h` (1X2).

Raw capture is bookmaker-level and append-only.

Persisted lineage includes:

- local ticket event ID;
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

Mapping fails closed unless:

- both teams resolve through verified aliases;
- home/away identity matches exactly at canonical club-key level;
- kickoff is within 5,400 seconds;
- only one provider event matches.

No fuzzy guessing is allowed.

`p11_market_context_as_known_v2`:

1. uses only the latest capture batch genuinely known by requested `as_of_at` and before kickoff;
2. de-vigs each bookmaker independently;
3. takes median bookmaker probabilities;
4. renormalizes consensus to one;
5. exposes home/draw/away probabilities, favorite probability and normalized outcome entropy.

Semantic guard:

`outcome_uncertainty != expected_match_quality`

Expected match quality requires a separate signal/precommit.

### P11 security / workflow

The Edge Function validates GitHub Actions OIDC itself:

- issuer: GitHub Actions token issuer;
- audience: `beyond-p11-odds-capture`;
- repository: `NiedzielX/beyond`;
- ref: `refs/heads/main`.

The workflow therefore allows genuine capture from `main` only.

Required external secret:

`THE_ODDS_API_KEY`

Do not store it in the repository or GitHub workflow source.

---

## 6. Exact current work order

### Step 1 — reconcile GitHub now

Merge `main` into `ml/p9-p11-execution-2026-10-24`, preserve both implementation slices, run CI/tests, then merge the active branch back to `main`.

### Step 2 — first genuine P11 capture

After P11 source/workflow is present on `main`:

1. verify/configure `THE_ODDS_API_KEY` in Supabase Edge Function secrets;
2. dispatch the P11 workflow manually with capture enabled;
3. inspect `localEvents`, `providerEvents`, `matchedEvents`, `insertedQuotes`;
4. inspect every event result;
5. verify bookmaker count, kickoff delta, provider quota and payload hashes;
6. add only verified provider aliases if mapping fails;
7. verify raw append-only rows;
8. verify `p11_market_context_as_known_v2` and readiness;
9. keep schedule off until the capture is accepted.

Do not fit/precommit the odds model from zero or unaudited observations.

### Step 3 — P9a main freeze audit

After source is on `main`:

1. run T-24 and T-48 target-free freeze audits;
2. persist/check manifest SHA and frozen identities;
3. confirm `target_values_opened=false`;
4. confirm `model_training_performed=false`;
5. keep learner blocked until a separate learner/comparator precommit.

### Step 4 — Long72 / P4a outcome sync diagnostic

Because both still have zero genuine labels/scores, inspect:

- `ticket_event_outcomes` / actual attendance availability for completed events;
- upstream outcome sync/cron health;
- prospective score attachment after actual attendance appears.

Do not retune the frozen packages from first labels.

### Step 5 — keep P7 frozen

No more P7 diagnostic work is needed for the current 8/9 state. Wait for event 6 to be completed and genuine attendance to arrive. Run the frozen executor only if canonical readiness becomes 9/9.

### Step 6 — keep full P9 collecting

Current 168h reference coverage: 4/9.

Allowed before the gate:

- coverage/readiness reporting;
- leakage/lineage tests;
- freeze-manifest tooling;
- representation audits.

Blocked before gate + learner precommit:

- learner selection;
- hyperparameter selection;
- opening result comparisons for the first learnable full-window challenger.

### Step 7 — governance business threshold

Minimum practically meaningful `ΔMAE` remains intentionally undefined.

Do not invent 100 seats, 3%, or derive a threshold from challenger results. It must come from downstream operational/business decisions.

---

## 7. Closed loops stay closed

Do not reopen without a materially new mechanism:

- P10/P10b pooled-HGB tuning;
- old estimator-only sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple club/opponent calibration;
- post-hoc calibration on already inspected evidence.

---

## 8. Never do these

- do not backfill closing odds as if they were historical PIT observations;
- do not insert synthetic odds into P11 v2;
- do not classify in-play quotes as pre-match evidence;
- do not fuzzy-match ambiguous provider fixtures;
- do not enable the P11 schedule before the first manual capture is audited;
- do not use future target trajectory points in P9/P9a;
- do not call the P9a target-free freeze a trained model;
- do not open P9a labels merely because the export contract exists;
- do not lower P7/P9/P4 gates because data is slow;
- do not reopen P10/P10b with a hyperparameter sweep;
- do not claim historical exposed research as prospective evidence;
- do not change `live_adjustment` from zero without reviewed promotion.

---

## 9. Cold-start command for the next AI session

> Read `AI_BOOTSTRAP.md`, `ml/NEXT_SESSION_HANDOFF.md`, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md` and `ml/MAE_RESEARCH_ROADMAP_V4.md`. Query readiness fresh. Preserve all frozen contracts. Current priority is to reconcile `main` with `ml/p9-p11-execution-2026-10-24`, get P11/P9a source onto `main`, perform and audit the first genuine manual P11 capture, then verify P9a freeze manifests and inspect the zero-label outcome sync. P7 remains frozen at 8/9 until event 6 is completed and genuine attendance is available. Full P9 remains data-bound at 4/9.
