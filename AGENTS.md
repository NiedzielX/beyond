# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Then read `ml/MAE_RESEARCH_ROADMAP_V4.md`.
3. Read `ml/PROGRESS_TRACKING.md` for the latest canonical state.
4. For P9, read `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md` before changing trajectory representation or fitting a booking-curve learner.
5. For P10/P10b, read `ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md`; P10 v1 is frozen after its real historical run and must not be retuned in place.
6. For P11, read `ml/P11_MATCH_ATTRACTIVENESS_CONTEXT_V1_PLAN.md` before adding odds, price, lineup, weather or attention features.
7. For P4/P5, read `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md` before touching feature selection or model code.
8. For P7/Long168, read `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` before touching code or data.
9. Read `ml/CURRENT_MODEL.md`, `ml/CORE_PRODUCT_STATUS.md`, `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`, and `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` as relevant.
10. Do **not** retrain/rebuild frozen historical benchmarks merely to recover context.
11. For latest-state questions, use targeted repo/DB reads rather than historical recomputation.
12. Never store secrets/tokens/service-role keys in repo files.

## Core principle

> **The objective is lower true out-of-sample MAE, not model complexity.**

The current research phase is **representation-first, not tuning-first**.

Prioritize:

- P9 booking-curve / trajectory-shape representation;
- P10 cross-horizon pooling under strict match blocking;
- P11 economically grounded PIT context;
- uncertainty and business-meaningful gain governance.

Do not default to another broad estimator or hyperparameter sweep.

Always separate:

- Evidence Lane — immutable packages collecting forward evidence;
- MAE R&D Lane — versioned challengers developed in parallel.

Never fabricate PIT history when a state was not captured.

## Validation rule

Use `ml/temporal_validation_v1.py`.

Historical/global:

- strict season/group expanding folds;
- no future-season data in earlier train folds;
- complete `match_key` blocking across all horizons;
- persist exact fold identities + SHA.

Live/context:

- `ticket_event` is the independent unit;
- strict forward-event validation by kickoff;
- tied kickoffs cannot train one another;
- no random snapshot split as headline evidence.

## Governance v2

Use:

`ml/research_advance_governance_v2.py`

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

A positive point estimate alone is not a robust advance.

`ROBUST_RESEARCH_ADVANCE` requires a predeclared minimum practically meaningful MAE improvement plus precision/stability/evidence-integrity gates.

Do not invent the meaningful threshold from the experiment being judged.

Until an approved business-derived threshold exists, the strongest allowed positive state is:

`POINT_GAIN_UNCERTAINTY_LIMITED`

## Closed research loops

Do not reopen without a materially new hypothesis/data source:

1. MAE-native estimator tournament;
2. estimator `ΔMAE` uncertainty;
3. historical Long72 incremental live value;
4. structural/live convex shrinkage;
5. simple post-hoc club/opponent calibration.

P9/P10/P11 are valid because they test new representation, cross-learning, or context rather than another blind tuning loop.

## Frozen packages / experiments

Do not mutate:

- final24 `v2/Ridge/P2`;
- Long72 `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`;
- Pre-Live / Structural Prior anchors;
- P4a precommit after labels arrive;
- P7 Long168 precommit after the 9/9 gate opens;
- **P10 pooled-horizon v1 after the real historical result has been observed**.

Any material feature/model/weight/target/comparator change requires a new challenger/version.

## P10 v1 — frozen positive historical signal

Real workflow run:

`40024979412`

Frozen run head:

`bfb50ebdf5a1800bd9516a098599b5dd751fc5e7`

Result:

- local MAE `2120.93`;
- pooled MAE `2057.46`;
- `ΔMAE=-63.47` seats;
- ~`2.99%` improvement;
- 95% paired match-block CI `[-106.29,-23.20]`;
- match improvement `59.12%`;
- folds improved `3/3`;
- all five horizons improved.

Governance:

`POINT_GAIN_UNCERTAINTY_LIMITED`

because the business meaningful-MAE threshold is not yet defined.

Do not alter P10 v1 to improve this result.

Next valid experiment:

**P10b — compare pooled-horizon cross-learning against the current strongest Global Model v2.1 / Structural champion under a common match-blocked temporal protocol.**

## P9 booking curve

Canonical implementation:

- `ml/p9_booking_curve_v1.py`;
- `ml/test_p9_booking_curve_v1.py`;
- `supabase/sql/p9_booking_curve_readiness_v1.sql`;
- `.github/workflows/p9-booking-curve-readiness-v1.yml`.

Use the existing trajectory infrastructure.

PIT rules:

- no target snapshot after `as_of_at`;
- no future target canonical point;
- interpolation only inside already-visible target observations;
- no target self-reference;
- historical reference must be completed before target cutoff;
- public inventory is a demand proxy, not confirmed sales.

P9 v1 is a simple auditable curve-similarity/pickup representation. Do not jump to a deep sequence model before genuine curve-reference coverage is demonstrated.

## P11 match attractiveness / commercial context

Priority:

1. PIT odds / expected quality / outcome uncertainty / stakes / rivalry;
2. price / promotion;
3. lineup / star strength / verified absences;
4. weather / attention.

No closing-odds, final-lineup, final-weather or later-stakes backfill into earlier cutoffs.

Each feature family requires a separate controlled ablation before combination.

## Current evidence checkpoint

Use `public.ml_research_readiness_v1()` instead of relying on prose counts.

Latest recorded checkpoint on 2026-10-23:

- Long72 reproducible forecasts `66`;
- genuine scored Long72 events `0`;
- fixture context `66 / 64 READY`;
- P4a independent READY events `5`;
- P4a labeled READY events `0`;
- next-opponent `66 / 0 READY`;
- Long168 `8/9`, `110` rows >72h.

## P4a fixture context — frozen

Research question:

> Does `previous_home_match_days` reduce event-level attendance MAE beyond the frozen Long72 pre-live T3+B2 anchor?

Independent unit:

`ticket_event`

Only feature:

`previous_home_match_days`

Hard start gate:

- `>=9` labeled independent events;
- `>=3` distinct labeled spacing values.

Required sequence:

`target-free export -> freeze identities/features/anchor -> SHA -> explicit execute -> labels -> reproduce freeze -> gate -> evaluation`

Fixed challenger:

`q50-linear-prev-home-spacing-a002`

No P4a result directly activates production.

Do not silently add sparse `next_home_match_days` or currently zero-variance density features.

## P4b next-opponent attractiveness

Current recorded state: `0 READY`.

Never reconstruct missing opponent attractiveness from later schedule/outcome knowledge.

## P5

Do not start P5 until P4a or another separately precommitted context experiment demonstrates incremental signal.

If context advances, combination weights must be learned inside training folds only.

## P7 Long168 — frozen harness + executor

P7 is blocked at the recorded `8/9` gate.

At `N<9`:

- real model execution fails closed;
- only T-7 anchor audit is allowed;
- never lower the gate.

Historical T-7 control is:

`historical_pit_replay`

with:

`persisted_forecast = false`.

At 9/9:

`fresh readiness -> explicit execute -> identity freeze -> SHA -> T-7 replay verification -> labels -> strict forward folds -> fixed tournament -> uncertainty -> research decision`

Nine events are a research-start gate only. They are not enough to believe a small uplift automatically.

## Immediate development order

1. P10b precommit + common-protocol comparator;
2. P9 readiness live validation / genuine 168h reference coverage;
3. P11a PIT odds/quality/stakes data contract;
4. business-derived minimum meaningful MAE threshold;
5. keep P4a/P7 evidence collection running unchanged.

## Evidence operations

Operational pipelines are active:

- Long72 forecast-before-label hourly;
- outcome-history sync hourly;
- completed-event scoring in prospective cycle;
- schedule-as-known every 6h;
- fixture-context sidecar every 15m;
- next-opponent sidecar every 15m;
- Long168 accumulation.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`
