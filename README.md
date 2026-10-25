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

## Current operational warning

Active development branch:

`ml/p9-p11-execution-2026-10-24`

It contains **two active implementation slices** that must not be recreated from scratch:

- **P9a target-free T-24/T-48 booking-curve freeze/export harness**;
- **P11a v2 genuine PIT odds capture**.

The live Supabase project is temporarily **ahead of `main` for both P9a/P11a source code**:

- P9a input/label RPCs are live;
- Edge Function `p9a_booking_curve_export_v1` is ACTIVE v1;
- P11 v2 DB contract is live;
- Edge Function `p11_odds_capture_v2` is ACTIVE v2;
- genuine P11 v2 odds rows remain `0`;
- no automatic P11 odds schedule is enabled.

P9a target-free export currently exposes:

- T-24: `18` target events / `19` reference events;
- T-48: `15` target events / `19` reference events;
- `target_values_used=false`;
- no post-cutoff target snapshots.

This is freeze infrastructure only — it does **not** mean a P9 learner is trained or labels may be opened.

P11 expects external secret `THE_ODDS_API_KEY`; its presence must be configured/verified before the first genuine capture.

Read `ml/NEXT_SESSION_HANDOFF.md` before touching either area.

## Current MAE workstreams

### P9 — Booking Curve / Trajectory Shape

Highest-priority live representation gap:

`normalized PIT trajectory -> historical curve similarity -> pickup distribution -> remaining-demand estimate -> structural residual`

Current full-168h reference coverage: **4/9**. Do not fit the first learnable full-window P9 model before the gate and a separate learner precommit.

P9a already provides target-free T-24/T-48 freeze tooling. After branch reconciliation, verify the main freeze audit/manifests; keep `target_values_opened=false` and `model_training_performed=false` until a separate learner/comparator precommit.

### P10 / P10b — pooled horizon

Closed for the fixed pooled-HGB architecture.

- P10 beat the same weaker local HGB by `63.47` MAE seats;
- P10b lost to frozen Pre-Live v3 by `147.51` MAE seats;
- do not retune this architecture after observing the result.

### P11 — Match Attractiveness / Commercial Context

Priority:

1. genuine PIT market odds / outcome uncertainty / stakes / rivalry;
2. price / promotion;
3. lineup / star strength / verified absences;
4. weather / attention later.

P11a v2 captures raw bookmaker-level 1X2 quotes append-only and derives an as-known de-vigged market consensus. No closing-odds backfill is allowed.

### Governance v2

A small positive point gain is not automatically a robust advance.

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

`ROBUST_RESEARCH_ADVANCE` requires a predeclared **business-derived minimum meaningful MAE improvement**. Do not infer that threshold from the experiment being judged.

## Current frozen/data-bound gates

Always query fresh:

`public.ml_research_readiness_v1()`

Latest recorded checkpoint: **2026-10-25 10:18 UTC**.

- Long72: `90` reproducible rows, `0` genuine scored events;
- P7 Long168: **8/9**, still closed;
- P4a: `5` READY events, `0` genuine labels, gate `>=9 labeled + >=3 distinct labeled spacing values`;
- P9 full-168h: **4/9**;
- P11a v2: `0` genuine odds events.

Important: event 6 was expected to enter the P7 Long168 window, but canonical readiness is still 8/9. The next session must **diagnose event 6 readiness before running any P7 experiment**.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until an explicit reviewed promotion.

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> forward/event-safe evaluation -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause model development.**