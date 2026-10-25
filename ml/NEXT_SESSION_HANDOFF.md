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

Canonical repository:

`NiedzielX/beyond`

Active development branch:

`ml/p9-p11-execution-2026-10-24`

This branch contains the P11a v2 implementation slice and must not be recreated from scratch.

Important files:

- `ml/EXECUTION_PLAN_2026-10-24.md`;
- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

Supabase project:

`adchzwqboeekhokapxqi`

Important: the live Supabase environment is temporarily ahead of `main` for P11a v2.

Already live:

- `private.p11_market_odds_observations_v2`;
- `public.p11_market_capture_inputs_v2(integer)`;
- `public.insert_p11_market_odds_capture_v2(jsonb)`;
- `public.p11_market_context_as_known_v2(bigint,timestamptz)`;
- `public.p11_market_odds_readiness_v2()`;
- Edge Function `p11_odds_capture_v2` — **ACTIVE, version 2**.

Do not deploy a different P11 function from memory. Reconcile/merge this branch first.

---

## 3. Fresh readiness checkpoint — 2026-10-25 10:18 UTC

Canonical source:

`select public.ml_research_readiness_v1();`

### Long72

- reproducible prediction rows: **90**;
- genuine scored events: **0**;
- latest reproducible `as_of_at`: `2026-10-24T16:20:02.672Z`.

### P7 Long168

- independent events with valid rows >72h: **8/9**;
- rows >72h: **110**;
- start gate: **closed**.

Event 6 (Lech Poznań vs Wisła Kraków, kickoff `2026-10-31 16:30Z`) was expected to enter the <=168h window on 2026-10-24, but canonical P7 readiness is still 8/9 on 2026-10-25.

**Do not assume P7 automatically unlocked. First investigate why event 6 is not counted.**

Check:

1. event 6 snapshots after T-168;
2. Long168 exporter eligibility/window rule;
3. requested snapshot/as-of selection;
4. exporter/readiness freshness and exclusions;
5. execute only if canonical readiness reaches 9/9.

Do not lower the threshold.

### P4a fixture context

- sidecar rows: **90**;
- READY rows: **88**;
- independent READY events: **5** — IDs `10,16,21,22,23`;
- genuine labeled READY events: **0**;
- primary feature: `previous_home_match_days`;
- values: `13,36,15,14,15`;
- gate `>=9 labeled + >=3 distinct labeled values` — closed.

### P9 booking curve

- 168h: **4/9 events / 4 clubs**;
- 72h: **7 events / 5 clubs**;
- 48h: **10 events / 6 clubs**;
- 24h: **13 events / 8 clubs**.

`P9_BOOKING_CURVE_168_START = false`.

Do not fit the first learnable P9 residual model yet.

### P11a odds v2

`public.p11_market_odds_readiness_v2()`:

- provider: `the-odds-api-v4`;
- provider selected: true;
- genuine PIT 1X2 events: **0**;
- raw v2 table rows: **0**;
- model precommitted: false;
- status `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`.

This is correct. No synthetic/backfilled odds were inserted.

---

## 4. P11a v2 architecture already implemented

Provider target:

**The Odds API v4** / `soccer_poland_ekstraklasa` / pre-match `h2h`.

Raw bookmaker-level quotes are preserved append-only with provider event ID, capture batch UUID, actual capture timestamp, provider timestamps, decimal prices, payload SHA, mapping method, club keys and kickoff delta.

Mapping fails closed unless verified aliases match, home/away orientation matches, kickoff is within 5,400 seconds and exactly one provider event matches.

`p11_market_context_as_known_v2` de-vigs each bookmaker, takes median probabilities across the latest capture batch known at the requested cutoff and renormalizes to one.

Semantic guard:

`outcome_uncertainty != expected_match_quality`

The Edge Function verifies GitHub Actions OIDC itself for repository `NiedzielX/beyond`, ref `refs/heads/main`, audience `beyond-p11-odds-capture`.

Required external secret:

`THE_ODDS_API_KEY`

Do not store it in repo. Configure/verify it in Supabase Edge Function secrets before the first genuine capture.

The workflow remains manual only. Keep schedule off until the first capture is audited.

---

## 5. Closed research results

P10 v1:

- local MAE `2120.93`;
- pooled MAE `2057.46`;
- `ΔMAE=-63.47`;
- 95% CI `[-106.29,-23.20]`;
- status `POINT_GAIN_UNCERTAINTY_LIMITED`.

P10b against frozen Pre-Live v3:

- incumbent `1919.92`;
- pooled `2067.43`;
- challenger-incumbent `ΔMAE=+147.51`;
- 95% CI `[+82.97,+210.67]`;
- 0/4 folds and 0/5 horizons improved;
- status `NO_RESEARCH_GAIN`.

Do not retune P10/P10b.

---

## 6. Governance v2

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

`ROBUST_RESEARCH_ADVANCE` is blocked until a business-derived minimum meaningful MAE improvement is predeclared. Do not infer it from observed model results.

---

## 7. Exact next-session work order

1. **Diagnose P7 event 6** — find why readiness is still 8/9.
2. **Reconcile/merge this branch to `main`** preserving all P11a v2 files.
3. **Configure/verify `THE_ODDS_API_KEY`** in Supabase secrets.
4. **Run one manual P11a v2 capture** from `main` and audit mapping, bookmaker count, quota, payload hashes, raw rows and consensus. Keep schedule off.
5. **Keep P9 collecting** toward 9 full-168h references; only harden representation/lineage before gate.
6. **Derive business minimum meaningful MAE threshold** independently of model results.
7. **Keep P4a/Long72 frozen evidence collection unchanged**.

---

## 8. Never do these

- no closing-odds backfill as historical PIT;
- no synthetic odds in P11 v2;
- no target-future trajectory points in P9;
- no lowering P7/P9/P4 gates;
- no reopening P10/P10b with tuning;
- no production change;
- do not enable the old ChatGPT Beyond readiness automations — user explicitly disabled them.

## 9. Cold-start command

> Read `AI_BOOTSTRAP.md`, `ml/NEXT_SESSION_HANDOFF.md`, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md` and `ml/MAE_RESEARCH_ROADMAP_V4.md`. Query `public.ml_research_readiness_v1()` fresh. Then compare `main` with `ml/p9-p11-execution-2026-10-24`. First resolve P7 event 6 readiness and finish P11a v2 merge/first genuine capture while P9 continues accumulating data.
