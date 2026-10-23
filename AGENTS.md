# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Read `ml/MAE_RESEARCH_ROADMAP_V4.md`.
3. Read `ml/PROGRESS_TRACKING.md` for the latest canonical state.
4. For P10 history, read both `ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md` and `ml/results/P10B_POOLED_VS_PRELIVE_V3_V1_2026-10-23.md`.
5. For P9, read `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md` before changing trajectory representation or fitting a learner.
6. For P11, read `ml/P11_MATCH_ATTRACTIVENESS_CONTEXT_V1_PLAN.md` and `supabase/sql/p11_market_odds_context_v1.sql` before adding market/commercial features.
7. For P4/P5, read `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md`.
8. For P7/Long168, read `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md`.
9. Use targeted repo/DB reads for latest state; do not rebuild frozen history just to recover context.
10. Never store secrets/tokens/service-role keys in repo files.

## Core principle

> **The objective is lower true out-of-sample MAE, not model complexity.**

Current phase: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

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

## P10 / P10b — frozen closeout

P10 v1 showed cross-horizon pooling helps relative to the same horizon-local HGB:

- local `2120.93`;
- pooled `2057.46`;
- `ΔMAE=-63.47`;
- status `POINT_GAIN_UNCERTAINTY_LIMITED`.

P10b tested the same pooled architecture against the actual frozen Pre-Live v3 structural anchor:

- Pre-Live v3 `1919.92`;
- pooled `2067.43`;
- `challenger-incumbent ΔMAE=+147.51`;
- 95% CI `[+82.97,+210.67]`;
- 0/4 folds improved;
- 0/5 horizons improved;
- status **`NO_RESEARCH_GAIN`**.

Do **not** retune P10/P10b after these results. The fixed pooled-HGB direct-replacement path is closed. A future pooling experiment requires a materially different mechanism and a new precommit.

## P9 booking curves

Use existing trajectory infrastructure; do not duplicate it.

Hard rules:

- no target snapshot after `as_of_at`;
- no future target canonical point;
- no self-event historical reference;
- reference event completed before target cutoff;
- public inventory is a demand proxy, not confirmed sales.

Current recorded full-168h coverage: **4/9** genuine completed reference events.

Do not fit the first learnable P9 residual challenger before the gate. At the gate, freeze its learner contract before opening model-result comparisons.

## P11a market odds

A PIT-safe v1 contract is now live and committed:

`supabase/sql/p11_market_odds_context_v1.sql`

It provides:

- append-only private 1X2 observations;
- service-role-only access;
- as-known selection by `captured_at <= as_of_at` and pre-kickoff;
- de-vigged probabilities;
- outcome uncertainty;
- favorite probability;
- target-free readiness.

Current state: **0 genuine PIT 1X2 events**, provider not selected.

Next action is genuine capture from a lawful/reliable provider. Never backfill closing odds into earlier cutoffs.

Do not label 1X2 outcome balance as “expected match quality”; use a separate justified signal for quality.

## P4a / P7

P4a remains frozen/data-bound:

- 5 READY events;
- 0 labels;
- gate `>=9` labeled + `>=3` distinct spacing values;
- fixed previous-home-spacing challenger.

P7 remains frozen/data-bound at the recorded **8/9** >72h events. Do not lower the threshold or redesign the tournament at 9/9.

## Closed loops

Do not reopen without materially new evidence/mechanism:

- estimator-only tuning;
- estimator uncertainty re-analysis on same sample;
- simple structural/live shrinkage;
- historical Long72 incremental-value loop;
- simple club/opponent post-hoc calibration;
- fixed P10/P10b pooled-HGB direct replacement.

## Central readiness

Use `public.ml_research_readiness_v1()` for current gates. It includes P4a, P7, Long72 and P9.

The existing `Beyond ML readiness` automation understands P4a/P9 but is intentionally still disabled.

## Immediate development order

1. integrate a lawful/reliable P11a odds provider for genuine PIT append-only capture;
2. derive the business minimum meaningful MAE threshold;
3. keep P9 genuine 168h curve capture running;
4. design a separate expected-quality signal if justified;
5. keep P4a/P7 evidence collection unchanged.

No research result activates production automatically.
