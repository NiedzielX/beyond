# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start rules and current state;
2. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md) — **latest operational handoff: main vs active branch vs live Supabase**;
3. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md) — **exact next work order**;
4. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md) — canonical status snapshot;
5. [`ml/MAE_RESEARCH_ROADMAP_V4.md`](ml/MAE_RESEARCH_ROADMAP_V4.md) — literature-grounded MAE-first strategy;
6. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — detailed forecasting state;
7. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — experiment / CI rules;
8. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) and [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) when touching live/promotion logic.

Do **not** start from Roadmap v3. Roadmap v4 is canonical.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with point-in-time-safe, reproducible evidence.**

Complexity is not the objective. Lower future MAE is.

Current mode: **representation-first, not tuning-first**.

## Current execution priority — 2026-10-25

The immediate priority is now:

`reconcile branch -> merge P11/P9a source to main -> first genuine manual P11 capture -> audit -> P9a freeze audit -> outcome-sync diagnostic`

Why P11 is first: the live P11 v2 Edge Function is already deployed, but genuine PIT evidence is still `0`. Genuine pre-match odds are perishable evidence and cannot be recreated later without violating the PIT contract.

Current P11 capture candidates returned by `public.p11_market_capture_inputs_v2(14)` on 2026-10-25 include:

- event 23: Śląsk Wrocław vs Wieczysta Kraków — kickoff `2026-10-25 11:15 UTC`;
- event 21: Jagiellonia Białystok vs Wisła Płock — kickoff `2026-10-25 13:45 UTC`;
- event 22: Legia Warszawa vs Lech Poznań — kickoff `2026-10-25 16:30 UTC`;
- event 6: Lech Poznań vs Wisła Kraków — kickoff `2026-10-31 16:30 UTC`.

The first capture must remain manual and audited. No automatic schedule is enabled yet.

## Repository / live state

Active development branch:

`ml/p9-p11-execution-2026-10-24`

Fresh comparison on 2026-10-25:

- status: **diverged**;
- active branch: **32 commits ahead** of `main`;
- active branch: **14 commits behind** `main`;
- do **not** blindly force-push or recreate the implementation;
- first merge current `main` into the active branch, resolve/verify, then open/merge the active branch back to `main`.

The branch contains two implementation slices that must be preserved:

- **P9a target-free T-24/T-48 booking-curve freeze/export harness**;
- **P11a v2 genuine PIT odds capture**.

Live Supabase project: `adchzwqboeekhokapxqi`.

Already live:

### P9a

- P9a input/label RPCs;
- Edge Function `p9a_booking_curve_export_v1` — ACTIVE v1.

### P11a v2

- P11 v2 DB capture/consensus/readiness contract;
- Edge Function `p11_odds_capture_v2` — **ACTIVE v2**;
- `verify_jwt=false` intentionally because the function validates GitHub Actions OIDC itself;
- raw P11 v2 rows: **0** at the latest check;
- automatic schedule: **off**.

The next missing P11 step is **not deployment**. It is verifying/configuring `THE_ODDS_API_KEY`, merging the workflow/source to `main`, and running one genuine manual capture.

## Current MAE workstreams

### P7 — Long168

Current canonical readiness remains **8/9**.

The event-6 issue is now understood: the frozen Long168 export contract requires an event to be completed and to have genuine `actual_attendance`. A T-168 snapshot by itself does **not** make the event eligible.

Therefore event 6 (Lech Poznań vs Wisła Kraków, 2026-10-31) cannot become the ninth P7 event before the match has been played and a genuine attendance outcome is available.

Do not bypass or relax this gate. P7 stays frozen until canonical readiness genuinely reaches 9/9.

### P9 — Booking Curve / Trajectory Shape

Highest-priority representation gap:

`normalized PIT trajectory -> historical curve similarity -> pickup distribution -> remaining-demand estimate -> structural residual`

Current full-168h reference coverage: **4/9**.

Do not fit the first learnable full-window P9 model before the gate and a separate learner precommit.

P9a target-free freeze/export infrastructure is already live. After branch reconciliation, run the main T-24/T-48 freeze audit and keep:

- `target_values_opened=false`;
- `model_training_performed=false`.

P9a is freeze tooling, not a trained model.

### P10 / P10b — pooled horizon

Closed for the fixed pooled-HGB architecture.

- P10 beat the same weaker local HGB by `63.47` MAE seats;
- P10b lost to frozen Pre-Live v3 by `147.51` MAE seats;
- do not retune this architecture after observing the result.

### P11 — Match Attractiveness / Commercial Context

Priority signal families:

1. genuine PIT market odds / outcome uncertainty / stakes / rivalry;
2. price / promotion;
3. lineup / star strength / verified absences;
4. weather / attention later.

P11a v2 captures raw bookmaker-level 1X2 quotes append-only and derives an as-known de-vigged market consensus. No closing-odds backfill is allowed.

Current P11 status:

- provider: `the-odds-api-v4`;
- provider selected: true;
- genuine PIT events: `0`;
- clubs with PIT 1X2: `0`;
- events with >=3 bookmakers: `0`;
- model precommitted: false;
- status: `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`;
- `production_change=false`.

### Long72 / P4a

Latest canonical state:

- Long72: `90` reproducible prediction rows, `0` genuine scored events;
- P4a: `5` READY independent events, `0` genuine labels;
- P4a gate: `>=9 labeled + >=3 distinct labeled previous_home_match_days values`.

After the P11/P9a operational work, inspect upstream attendance/outcome sync before assuming these scoring pipelines are broken. Do not retune frozen packages from early labels.

### Governance v2

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

`ROBUST_RESEARCH_ADVANCE` requires a predeclared **business-derived minimum meaningful MAE improvement**. Do not infer that threshold from an experiment being judged.

## Exact immediate work order

1. Reconcile `main` into `ml/p9-p11-execution-2026-10-24` and preserve both P9a/P11a implementations.
2. Run CI/tests and merge the active branch back to `main`.
3. Verify/configure Supabase Edge Function secret `THE_ODDS_API_KEY`.
4. Run exactly one manual P11 capture from `main` through the GitHub OIDC workflow.
5. Audit mapping, provider event identity, bookmaker count, kickoff delta, quota, payload hash and inserted raw rows.
6. Verify `public.p11_market_context_as_known_v2(...)` and `public.p11_market_odds_readiness_v2()`.
7. Keep P11 schedule off until that capture is accepted.
8. Run/verify P9a target-free T-24/T-48 freeze audit and manifests.
9. Inspect Long72/P4a upstream outcome sync.
10. Keep P7 frozen until event 6 is completed and genuine attendance makes canonical readiness 9/9.
11. Keep P9 full-168h collecting at 4/9; no learner fitting yet.

## Never do these

- do not backfill closing odds as historical PIT observations;
- do not insert synthetic odds into P11 v2;
- do not capture in-play odds as pre-match evidence;
- do not fuzzy-match ambiguous provider fixtures;
- do not enable automatic P11 scheduling before the first audited capture;
- do not use future target trajectory points in P9/P9a;
- do not call P9a freeze tooling a trained model;
- do not open P9a labels merely because the export contract exists;
- do not lower P7/P9/P4 gates because data is slow;
- do not reopen P10/P10b with a hyperparameter sweep;
- do not claim historical exposed research as prospective evidence;
- do not change `live_adjustment` from zero without reviewed promotion.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until an explicit reviewed promotion.

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> forward/event-safe evaluation -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause model development.**
