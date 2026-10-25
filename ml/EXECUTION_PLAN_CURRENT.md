# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-25**

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

## Priority 1 — P7 event 6 diagnostic

Current canonical readiness on 2026-10-25 is still **8/9** despite event 6 having passed the expected T-168 boundary.

Investigate why event 6 is not counted before doing any additional P7 model work.

Required checks:

- event 6 snapshot timestamps and first snapshot after the T-168 boundary;
- exporter eligibility rule `72 < h <= 168`;
- snapshot/as-of selection;
- data quality/exclusion rules;
- central readiness freshness.

If and only if readiness becomes 9/9:

`readiness -> exact identity freeze -> SHA -> frozen T7 anchor replay verification -> labels -> strict forward folds -> fixed tournament -> paired event-block uncertainty -> research decision`

Do not change the P7 design after the gate opens.

## Priority 2 — reconcile active branch to main

Active branch:

`ml/p9-p11-execution-2026-10-24`

It contains two important implementation slices already partly live in Supabase:

### P9a freeze

- `ml/p9a_booking_curve_freeze_v1.py`;
- `ml/test_p9a_booking_curve_freeze_v1.py`;
- `supabase/sql/p9a_booking_curve_freeze_v1.sql`;
- `supabase/functions/p9a_booking_curve_export_v1/index.ts`;
- `.github/workflows/p9a-booking-curve-freeze-v1.yml`.

### P11a odds v2

- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

Do not recreate either implementation on another branch. Reconcile/merge after CI/review.

## Priority 3 — P9a target-free T-24/T-48 freeze audit

P9a export infrastructure is already live:

- `export_p9a_booking_curve_inputs_v1(integer)`;
- `export_p9a_booking_curve_labels_v1(bigint[])` — labels remain separate;
- Edge Function `p9a_booking_curve_export_v1` ACTIVE v1.

Live target-free export on 2026-10-25:

- T-24: **18 target events / 19 reference events**;
- T-48: **15 target events / 19 reference events**;
- `target_values_used=false`;
- `post_cutoff_target_snapshots_exported=false`;
- `production_change=false`.

After the source/workflow is on `main`:

1. run/verify the main target-free freeze audit;
2. persist/check T-24 and T-48 manifest SHAs;
3. verify frozen snapshot/reference/incumbent identities;
4. verify `target_values_opened=false`;
5. verify `model_training_performed=false`;
6. keep learner status blocked until a separate learner/comparator precommit.

P9a is **freeze tooling**, not a trained model and not permission to open labels.

## Priority 4 — finish P11a v2 operationalization

Already live in Supabase:

- DB capture/consensus/readiness contract;
- Edge Function `p11_odds_capture_v2` ACTIVE v2.

Still required:

1. merge/reconcile P11a v2 source/workflow to `main`;
2. configure/verify `THE_ODDS_API_KEY` in Supabase Edge Function secrets;
3. run exactly one manual capture from `main`;
4. audit event matching, bookmaker count, provider quota, payload hashes and inserted rows;
5. verify `p11_market_context_as_known_v2` for captured events;
6. keep schedule off until the manual capture is accepted.

Do not precommit or fit the P11 odds model until genuine PIT coverage has been audited. No closing-odds backfill.

## Priority 5 — P9 full-168h accumulation + harness hardening

Current 168h reference coverage: **4/9**.

Keep collecting.

Allowed before gate:

- target-free representation tests;
- leakage tests;
- reference-pool lineage audit;
- coverage/readiness reporting;
- deterministic freeze-manifest tooling.

Blocked before gate:

- learner selection;
- hyperparameter selection;
- model-result comparison for the full-168h learner.

At 9 genuine full-168h completed reference events, freeze the learner contract first.

## Priority 6 — business minimum meaningful MAE threshold

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

## Priority 7 — P11 broader signal families

After genuine odds capture is stable:

1. stakes/rivalry integration audit;
2. separate expected-match-quality signal — do not equate it with 1X2 entropy;
3. price/promotion PIT coverage;
4. lineup/star/verified absence representation;
5. weather/attention later.

Each family gets a separate controlled ablation against the same incumbent before combination.

## Priority 8 — frozen evidence lanes

### Long72

Keep forecast-before-label scoring unchanged. Inspect first genuine score when it appears, but do not retune the frozen package.

### P4a

Wait for `>=9` labeled independent events and `>=3` distinct labeled `previous_home_match_days` values. Do not redesign the challenger after labels arrive.

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

1. P7 becomes canonical 9/9 and frozen executor can run;
2. P9a target-free freeze manifests are verified on `main`;
3. first genuine P11a v2 odds capture is inserted and audited;
4. first genuine Long72 score appears;
5. P9 reaches 9 full-168h reference events;
6. P4a reaches its labeled 9-event / 3-value gate.

Whichever happens first must be handled under already-defined evidence rules rather than opportunistic retuning.
