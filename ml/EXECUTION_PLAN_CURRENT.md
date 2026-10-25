# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-25 11:45 Europe/Warsaw**

Status: **CURRENT EXECUTION ORDER**

Canonical strategy remains `ml/MAE_RESEARCH_ROADMAP_V4.md`. This file translates that strategy into the next concrete work order.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

## Priority 0 — protect evidence integrity

Before any experiment or code change:

1. read `AI_BOOTSTRAP.md`;
2. read `ml/NEXT_SESSION_HANDOFF.md`;
3. query `public.ml_research_readiness_v1()` fresh;
4. preserve frozen P4a/P7/P9 contracts;
5. do not reopen P10/P10b;
6. do not enable production.

## Priority 1 — reconcile active branch to main

Active branch:

`ml/p9-p11-execution-2026-10-24`

Fresh comparison on 2026-10-25:

- status: diverged;
- active branch: **32 commits ahead**;
- active branch: **14 commits behind**.

Required reconciliation sequence:

1. merge current `main` into the active branch;
2. preserve the P9a and P11a v2 implementation slices;
3. run CI/tests;
4. open/merge active branch back into `main`.

Do not recreate the implementation on a new branch and do not force-push away either history.

### P9a files to preserve

- `ml/p9a_booking_curve_freeze_v1.py`;
- `ml/test_p9a_booking_curve_freeze_v1.py`;
- `supabase/sql/p9a_booking_curve_freeze_v1.sql`;
- `supabase/functions/p9a_booking_curve_export_v1/index.ts`;
- `.github/workflows/p9a-booking-curve-freeze-v1.yml`.

### P11a v2 files to preserve

- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

## Priority 2 — obtain the first genuine P11a PIT observation

This is the most time-sensitive research step because pre-match odds are perishable evidence.

Already live in Supabase:

- P11 v2 DB capture/consensus/readiness contract;
- Edge Function `p11_odds_capture_v2` ACTIVE v2.

Current readiness:

- raw v2 rows: **0**;
- genuine PIT events: **0**;
- events with >=3 bookmakers: **0**;
- model precommitted: false;
- status: `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`.

Current capture candidates returned by `p11_market_capture_inputs_v2(14)` include:

- event 23 — Śląsk Wrocław vs Wieczysta Kraków — `2026-10-25 11:15 UTC`;
- event 21 — Jagiellonia Białystok vs Wisła Płock — `2026-10-25 13:45 UTC`;
- event 22 — Legia Warszawa vs Lech Poznań — `2026-10-25 16:30 UTC`;
- event 6 — Lech Poznań vs Wisła Kraków — `2026-10-31 16:30 UTC`.

Required sequence after the workflow/source is on `main`:

1. verify/configure `THE_ODDS_API_KEY` in Supabase Edge Function secrets;
2. dispatch exactly one manual capture from `main`;
3. inspect local/provider/matched event counts;
4. inspect each event mapping result;
5. verify bookmaker count and complete 1X2 market availability;
6. verify kickoff delta;
7. verify provider quota;
8. verify payload hashes and inserted append-only rows;
9. verify `public.p11_market_context_as_known_v2(...)`;
10. verify `public.p11_market_odds_readiness_v2()`;
11. keep automatic schedule **off** until the manual capture is accepted.

If mapping fails, add only verified aliases. No fuzzy matching.

Do not use closing odds or provider historical backfill as if those quotes had been known at an earlier cutoff.

## Priority 3 — P9a target-free T-24/T-48 freeze audit

P9a export infrastructure is already live:

- `export_p9a_booking_curve_inputs_v1(integer)`;
- `export_p9a_booking_curve_labels_v1(bigint[])` — labels remain separate;
- Edge Function `p9a_booking_curve_export_v1` ACTIVE v1.

Latest live target-free export:

- T-24: **18 target / 19 reference events**;
- T-48: **15 target / 19 reference events**;
- `target_values_used=false`;
- `post_cutoff_target_snapshots_exported=false`;
- `production_change=false`.

After source/workflow is on `main`:

1. run/verify the main T-24 and T-48 target-free freeze audits;
2. persist/check manifest SHA values;
3. verify frozen snapshot/reference/incumbent identities;
4. verify `target_values_opened=false`;
5. verify `model_training_performed=false`;
6. keep learner status blocked until a separate learner/comparator precommit.

P9a is **freeze tooling**, not a trained model.

## Priority 4 — Long72 / P4a outcome-sync diagnostic

Current state:

- Long72: **90** reproducible rows, **0** genuine scored events;
- P4a: **5** READY independent events, **0** genuine labels.

Before assuming a scoring bug, inspect:

1. `ticket_event_outcomes` / actual attendance availability for completed events;
2. upstream outcome sync / cron health;
3. prospective score attachment after actual attendance appears;
4. whether completed matches have genuine outcomes in the expected source tables.

Do not retune frozen Long72/P4a packages from the first labels.

P4a remains blocked until:

`>=9 labeled events AND >=3 distinct labeled previous_home_match_days values`.

## Priority 5 — P7 stays frozen at 8/9

The earlier expectation that event 6 would unlock P7 merely after entering T-168 was incorrect.

Resolved contract behavior:

- the frozen Long168 exporter requires an event to be completed;
- it also requires genuine `actual_attendance`;
- a T-168 snapshot alone is insufficient.

Event 6 — Lech Poznań vs Wisła Kraków, kickoff `2026-10-31 16:30 UTC` — can become the ninth P7 event only after the match and genuine attendance outcome are available.

Therefore:

- no more P7 diagnostic/model work now;
- do not lower the 9-event gate;
- do not modify the frozen exporter;
- when canonical readiness genuinely becomes 9/9, execute the already-frozen P7 sequence exactly as precommitted.

## Priority 6 — P9 full-168h accumulation + harness hardening

Current 168h reference coverage: **4/9**.

Keep collecting.

Allowed before gate:

- target-free representation tests;
- leakage tests;
- reference-pool lineage audit;
- coverage/readiness reporting;
- deterministic freeze-manifest tooling.

Blocked before gate + learner precommit:

- learner selection;
- hyperparameter selection;
- model-result comparison for the first full-168h learner.

At 9 genuine full-168h completed reference events, freeze the learner contract first.

## Priority 7 — business minimum meaningful MAE threshold

Governance v2 is implemented, but the practical threshold is intentionally undefined.

Derive it from downstream decisions, not from model results.

Candidate inputs:

- staffing bands;
- security/police requirements;
- transport/bus planning;
- catering/food inventory;
- hospitality capacity;
- operational cost of overforecast vs underforecast;
- decision thresholds where a forecast change changes an action.

Until the threshold is approved:

`ROBUST_RESEARCH_ADVANCE` is not allowed.

## Priority 8 — P11 broader signal families

Only after genuine odds capture is stable:

1. stakes/rivalry integration audit;
2. separate expected-match-quality signal — do not equate it with 1X2 entropy;
3. price/promotion PIT coverage;
4. lineup/star/verified absence representation;
5. weather/attention later.

Each family gets a separate controlled ablation against the same incumbent before combination.

## Closed loops

Do not reopen without a materially new mechanism:

- estimator-only tuning;
- P2 broad tournament;
- P3 repeated uncertainty analysis on the same estimator sample;
- P5a simple shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple club/opponent calibration;
- P10/P10b fixed pooled-HGB direct replacement;
- blind model/weight sweeps.

## Definition of next milestone

The next meaningful milestone is one of:

1. first genuine P11a v2 odds capture is inserted and audited;
2. P9a target-free freeze manifests are verified on `main`;
3. first genuine Long72 score appears;
4. P7 becomes canonical 9/9 after event 6 completes and genuine attendance is available;
5. P9 reaches 9 full-168h reference events;
6. P4a reaches its labeled 9-event / 3-value gate.

Whichever happens first must be handled under already-defined evidence rules rather than opportunistic retuning.
