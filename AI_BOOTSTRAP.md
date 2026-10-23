# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-23**

## Cold-start rule

Read in this order:

1. `ml/MAE_RESEARCH_ROADMAP_V4.md`;
2. `ml/PROGRESS_TRACKING.md`;
3. `ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md` when working on pooled/global structural models;
4. `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md` when working on live trajectory/booking-curve research;
5. `ml/P11_MATCH_ATTRACTIVENESS_CONTEXT_V1_PLAN.md` when working on new commercial/context signals;
6. `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md` when working on P4/P5;
7. `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` when working on P7/Long168;
8. `ml/CURRENT_MODEL.md`;
9. `ml/CORE_PRODUCT_STATUS.md`;
10. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
11. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
12. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

Do not rebuild frozen historical benchmarks merely to recover context.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons, using honest PIT-safe and reproducible evidence.**

The current research mode is **representation-first, not tuning-first**.

Prefer:

- new predictive information;
- better trajectory representation;
- cross-learning with correct blocking;
- stronger PIT context;
- honest uncertainty.

Do not default to another estimator/hyperparameter sweep.

Production remains:

`live_adjustment = 0`

## Structural core

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- Structural Prior / Global Model remains the production/research incumbent family;
- historical runtime SHA: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Previously inspected historical seasons remain exposed research evidence.

## Roadmap v4 priorities

### P9 — Booking Curve / Trajectory Shape

Use the existing trajectory infrastructure; do not duplicate it.

Target representation:

`PIT snapshots -> normalized trajectory -> historical curve similarity -> pickup distribution -> remaining-demand estimate -> structural residual challenger`

Canonical v1 files:

- `ml/p9_booking_curve_v1.py`;
- `ml/test_p9_booking_curve_v1.py`;
- `supabase/sql/p9_booking_curve_readiness_v1.sql`;
- `.github/workflows/p9-booking-curve-readiness-v1.yml`;
- `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md`.

P9 v1 deliberately starts with an auditable weighted-L1 similarity/pickup representation. Do not jump to LSTM/Transformer before genuine curve-reference coverage justifies it.

Hard rules:

- no target observation after `as_of_at`;
- target future canonical points remain missing;
- no self-event reference;
- reference event must already be completed by the target cutoff;
- public inventory is a demand proxy, not confirmed paid sales.

### P10 — Pooled Horizon Global Model

P10 v1 has already been executed on historical exposed evidence and is now frozen.

Real run:

`40024979412`

Frozen run head:

`bfb50ebdf5a1800bd9516a098599b5dd751fc5e7`

Observed result:

- local-horizon MAE `2120.93`;
- pooled MAE `2057.46`;
- `ΔMAE=-63.47` seats;
- ~`2.99%` improvement;
- 95% paired match-block CI `[-106.29,-23.20]`;
- event improvement `59.12%`;
- fold improvement `3/3`;
- all five horizons improved.

Governance status:

`POINT_GAIN_UNCERTAINTY_LIMITED`

Do **not** modify P10 v1 after seeing this result.

Next experiment must be a new version:

**P10b — pooled-horizon challenger vs the current strongest Global Model v2.1 / Structural comparator under a common match-blocked temporal protocol.**

### P11 — Match Attractiveness / Commercial Context

Priority order:

1. PIT odds / expected quality / outcome uncertainty / stakes / rivalry;
2. price / promotion state;
3. lineup / star strength / verified absences;
4. weather / media/social attention.

Never backfill closing odds, final lineup or later-known context into an earlier cutoff.

## Governance v2

Canonical:

- `ml/research_advance_governance_v2.py`;
- `ml/test_research_advance_governance_v2.py`.

Decision vocabulary:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

`ROBUST_RESEARCH_ADVANCE` requires a predeclared minimum practically meaningful MAE improvement plus adequate precision and stability.

Do **not** invent an arbitrary business threshold such as 100 seats or 3% merely to enable promotion.

Until a business-derived threshold exists, the strongest allowed positive state is:

`POINT_GAIN_UNCERTAINTY_LIMITED`

## Frozen Long72 package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical comparison:

- anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- `ΔMAE=-694.51` / `18.73%`;
- 95% interval `[-1549.89,+148.05]`;
- P2 bias `+917.05`.

Immutable. Genuine prospective evidence continues.

## Closed loops

Do not reopen without materially new information:

- P2 estimator tournament;
- P3 estimator uncertainty;
- P5a structural/live shrinkage;
- P6 historical incremental live value;
- P8 simple club/opponent calibration.

P9/P10/P11 are allowed because they test new representation/cross-learning/context hypotheses.

## Current live checkpoint

Always read fresh state from:

`public.ml_research_readiness_v1()`

Latest checkpoint recorded on 2026-10-23:

- Long72 reproducible forecasts: `66`;
- genuine Long72 scored events: `0`;
- fixture-context sidecar: `66 / 64 READY`;
- P4a independent READY events: `5`;
- P4a genuine labeled READY events: `0`;
- P4 next-opponent sidecar: `66 / 0 READY`;
- Long168: `8/9` independent events >72h, `110` rows >72h.

Do not rely on prose counts when a fresh RPC result is available.

## P4a — previous-home spacing is frozen

Do **not** redesign P4a after labels arrive.

Canonical files:

- `supabase/sql/p4_fixture_context_precommit_v1.sql`;
- `ml/p4_fixture_context_harness_v1.py`;
- `ml/test_p4_fixture_context_harness_v1.py`;
- `.github/workflows/p4-fixture-context-precommit-v1.yml`;
- `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md`.

Research question:

> Does `previous_home_match_days` reduce event-level attendance MAE beyond the frozen Long72 pre-live T3+B2 anchor?

Independent unit:

`ticket_event`

Primary feature:

`previous_home_match_days`

Hard start gate:

- `>=9` labeled independent events with non-null spacing;
- `>=3` distinct labeled spacing values.

Mandatory order:

`target-free inputs -> identity/feature/anchor freeze -> manifest SHA -> explicit execute -> labels -> freeze reproduction -> 9/3 gate -> evaluation`

Fixed challenger:

- `q50-linear-prev-home-spacing-a002`;
- residual target = attendance minus T3+B2 anchor;
- QuantileRegressor q=.5 alpha=.002;
- RobustScaler;
- strict forward-event validation, min 5 train events;
- paired event-block bootstrap, 5,000 draws, seed 42.

Do not silently add sparse `next_home_match_days` or zero-variance density features.

## P4b next-opponent attractiveness

Infrastructure exists and is fail-closed.

Current recorded state: `0 READY`.

Never reconstruct missing opponent attractiveness using later schedule/outcome knowledge.

## P5 — combination research

Do not start P5 until P4 produces an incremental context signal.

If context advances, learn any combination weights inside training folds only.

## P7 Long168 — frozen harness/executor

Do not redesign P7 at 9/9.

Research start requires:

`>=9` independent events with valid rows >72h.

At the recorded `8/9`:

- model execution fails closed;
- only anchor audit is allowed;
- do not lower the threshold.

Historical T-7 control is explicit replay evidence:

`historical_pit_replay`

with:

`persisted_forecast = false`

At 9/9 exact order is:

`readiness -> explicit execute -> identity freeze -> SHA -> T-7 replay verification -> labels -> strict forward folds -> fixed tournament -> uncertainty -> research decision`

Nine events are only a research-start gate, not evidence that a small uplift is trustworthy.

## Evidence operations

Operational pipelines are already active:

- Long72 forecast-before-label hourly;
- outcome-history sync hourly;
- completed-event scoring in Long72 prospective cycle;
- schedule-as-known every 6h;
- fixture-context sidecar every 15m;
- next-opponent sidecar every 15m;
- Long168 accumulation.

## Immediate development order

1. precommit **P10b** against the strongest current Global Model comparator;
2. validate/deploy P9 readiness and audit genuine completed 168h curve-reference coverage;
3. design P11a PIT odds / expected-quality / stakes capture;
4. derive the business minimum meaningful MAE threshold;
5. keep P4a/P7 evidence collection running without redesign.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`
