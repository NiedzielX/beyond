# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-23**

## Cold-start order

Read in this order:

1. `ml/MAE_RESEARCH_ROADMAP_V4.md`;
2. `ml/PROGRESS_TRACKING.md` — **latest canonical state**;
3. `ml/results/P10B_POOLED_VS_PRELIVE_V3_V1_2026-10-23.md` when touching pooled/global structural research;
4. `ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md` for the earlier pooled-vs-local finding;
5. `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md` for P9;
6. `ml/P11_MATCH_ATTRACTIVENESS_CONTEXT_V1_PLAN.md` and `supabase/sql/p11_market_odds_context_v1.sql` for P11;
7. `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md` for P4/P5;
8. `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` for P7;
9. `ml/CURRENT_MODEL.md`, `ml/CORE_PRODUCT_STATUS.md`, `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`, `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`, `ml/MODEL_PROMOTION_GOVERNANCE_V1.md` as relevant.

Do not rebuild frozen historical benchmarks merely to recover context.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Prefer new information, better representation, correct temporal blocking and honest uncertainty over another broad estimator/hyperparameter sweep.

Production remains:

`live_adjustment = 0`

## Structural core

- 1,530 Ekstraklasa matches / five seasons;
- 7,650 PIT rows at T-30/T-14/T-7/T-3/T-1;
- canonical history SHA `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`;
- strongest reproducible historical structural research anchor: frozen Pre-Live v3.

Previously inspected historical seasons remain exposed R&D evidence.

## P10 / P10b — CLOSED for this architecture

### P10 v1

Pooled cross-horizon HGB beat the **same HGB trained separately per horizon**:

- local MAE `2120.93`;
- pooled MAE `2057.46`;
- `ΔMAE=-63.47`;
- 95% paired CI `[-106.29,-23.20]`;
- 3/3 folds and 5/5 horizons improved;
- status `POINT_GAIN_UNCERTAINTY_LIMITED`.

### P10b

The harder frozen comparison against Pre-Live v3 is complete:

- Pre-Live v3 MAE `1919.92`;
- pooled MAE `2067.43`;
- `challenger-incumbent ΔMAE=+147.51` seats;
- relative degradation `+7.68%`;
- 95% paired CI `[+82.97,+210.67]`;
- event improvement `43.69%`;
- folds improved `0/4`;
- horizons improved `0/5`;
- status **`NO_RESEARCH_GAIN`**.

Do **not** retune P10/P10b after these results. The fixed pooled-HGB direct-replacement path is closed. Any future pooling work requires a materially new mechanism and a new precommit; it is not the current priority.

## P9 — Booking Curve / Trajectory Shape

Canonical idea:

`PIT inventory path -> normalized trajectory -> historical curve similarity -> pickup distribution -> remaining-demand estimate -> structural residual challenger`

Hard PIT rules:

- no target observation after `as_of_at`;
- no target-future canonical point;
- no self-event reference;
- reference event completed before target cutoff;
- public inventory is a demand proxy, not confirmed paid sales.

Current live coverage:

- 168h: **4/9** genuine completed reference events / 4 clubs;
- 72h: 7 events / 5 clubs;
- 48h: 10 events / 6 clubs;
- 24h: 13 events / 8 clubs.

`P9_BOOKING_CURVE_168_START = false`.

Do not fit the first learnable P9 model yet. At 9 genuine full-168h references, freeze the learner contract before model-result comparison.

## P11 — Match Attractiveness / Commercial Context

Priority:

1. PIT odds / outcome uncertainty / stakes / rivalry;
2. price / promotion;
3. lineup / star strength / verified absences;
4. weather / media/social attention.

Existing DB already has rivalry, stakes reconstruction, verified absences, price, weather and media scaffolding.

### P11a market odds v1

Live contract exists:

- append-only private 1X2 observations;
- service-role-only access;
- `p11_market_context_as_known_v1(ticket_event_id, as_of_at)`;
- de-vigged home/draw/away probabilities;
- normalized outcome uncertainty;
- favorite probability;
- target-free readiness RPC.

Current state:

- genuine PIT 1X2 events `0`;
- provider selected `false`;
- model precommitted `false`;
- `NO_GENUINE_ODDS_CAPTURE_YET`.

Do not backfill closing odds. Next development step is a lawful/reliable provider + genuine append-only capture.

Do not call 1X2 balance “expected match quality”; quality needs a separate justified signal.

## Governance v2

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

Robust advancement requires point gain, event/fold stability, PIT/lineage/reproducibility, adequate precision **and** a predeclared business-derived minimum meaningful MAE improvement.

Do not invent `100 seats` or `3%` from model results. Until the business threshold is defined, the strongest allowed positive state is `POINT_GAIN_UNCERTAINTY_LIMITED`.

## Other frozen/data-bound work

### P4a

- 5 READY independent events;
- 0 genuine labels;
- primary feature `previous_home_match_days`;
- gate `>=9` labeled events + `>=3` distinct labeled values;
- fixed challenger `q50-linear-prev-home-spacing-a002`;
- do not redesign after labels arrive.

### P7 Long168

- recorded state `8/9` independent >72h events;
- real execution fails closed below 9;
- at 9/9 follow the already-frozen identity-freeze -> anchor replay -> labels -> strict forward tournament sequence.

Nine events start research; they do not make a small uplift trustworthy.

## Central readiness

Always read fresh state from:

`public.ml_research_readiness_v1()`

It now includes Long72, P4, P7 and P9 (`P9_BOOKING_CURVE_168_START`).

Existing `Beyond ML readiness` automation was updated to understand P4a/P9 but remains **disabled**; do not enable it implicitly.

## Immediate development order

1. select and integrate a lawful/reliable **P11a odds provider** for genuine PIT append-only capture;
2. derive the **business minimum meaningful MAE improvement** from downstream decisions/error costs;
3. keep P9 capture running until genuine 168h coverage reaches its gate;
4. design a separate expected-match-quality signal if useful;
5. keep P4a/P7 evidence collection unchanged.

No research result activates production automatically.
