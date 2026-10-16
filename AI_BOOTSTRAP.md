# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-16**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Before doing Beyond forecasting, ML, dashboard, Growth or recommendation work, read in this order:

1. `ml/CURRENT_MODEL.md` — canonical current model/product state;
2. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — implementation roadmap;
3. `ml/C1_MODEL_TOURNAMENT_V1.md` — C1-alpha validation rules;
4. latest `ml/results/C1_ALPHA_*.md` evidence — current experiment state;
5. `ml/SECTOR_DECISION_PRICING_V1.md` — sector/no-action/pricing contract;
6. `ml/NORTH_STAR.md`;
7. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
8. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
9. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`;
10. `growth/GROWTH_EXECUTION_DATA_V2.md`.

## Critical product direction — DO NOT LOSE THIS

Beyond is **not** primarily a generic campaign recommendation tool.

Primary output:

`event -> sector -> trajectory -> no-action projection -> pricing scenario -> recommendation`

For an active event the product should tell the club which sector is behind/ahead, how far it is from trajectory, where it is projected to finish if nothing changes, what price action is worth testing, and what happened after the club acted.

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## Structural Prior state

All five current-event horizons are executable and frozen:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Scheduled inference is load + predict only.

## C1-alpha — train now, do not wait for 20 matches

The 20-independent-match rule is a **later promotion gate**, not a training-start gate.

Current C1 evidence:

- 9 completed Ekstraklasa events in current Structural Prior domain;
- 206 PIT-valid regularized full-trajectory rows;
- 8/9 events with PIT-safe T-24 `hybrid_v6`;
- one completed Lech Europa League event outside the primary leaderboard.

Never treat multiple snapshots from one event as independent matches.

## C1-alpha result ladder — current canonical state

Read the result files instead of rerunning experiments only to recover context.

### v1 — mixed all-phase tournament

`ml/results/C1_ALPHA_MODEL_TOURNAMENT_V1_2026-10-16.md`

Result: no improvement. Mixing heterogeneous T-14/T-7/T-3/T-1 evidence into one model is not the right formulation.

### v2 — final-24h live expert — **best aggregate challenger**

`ml/results/C1_ALPHA_T1_TOURNAMENT_V2_2026-10-16.md`

Winner:

`ridge_directocc_compact_generic_a10`

- Structural Prior: **3,968.7 MAE**;
- live expert: **2,929.3 MAE**;
- improvement: **26.19%**;
- improves 4/9 events;
- too unstable for unconditional activation.

### v3 — nested threshold/blend gate

`ml/results/C1_ALPHA_T1_GATED_V3_2026-10-16.md`

- **3,054.3 MAE**;
- safer tail risk, but only 2/9 events improved.

### v4 — stacked meta gate

`ml/results/C1_ALPHA_T1_STACKED_V4_2026-10-16.md`

- **3,106.8 MAE**;
- more stacking did not solve expert selection.

### v5 — stacked gate + `hybrid_v6`

`ml/results/C1_ALPHA_T1_HYBRID_GATE_V5_2026-10-16.md`

- **3,073.8 MAE**;
- 4/9 events improved;
- still unstable.

### v6 — one-row T-24 challenger — **rejected direction**

`ml/results/C1_ALPHA_T24_RESIDUAL_V6_2026-10-16.md`

LOEO:

- Structural Prior: **3,968.7 MAE**;
- v6: **3,873.2 MAE**;
- only **2.41%** improvement.

LOCO:

- v6: **3,989.8 MAE** — slightly worse than prior.

Oracle prior-or-v6: **2,942.1 MAE**, far worse than the v2 pair's oracle.

Therefore **do not continue T-24-only as the main direction**.

## The key C1-alpha finding

The strongest live information is in the **full final-24h trajectory**, not a single T-24 feature.

The v2 Structural Prior/live pair has a non-deployable outcome-aware oracle switch of approximately:

**1,867.9 MAE**

This is the closest evidence to the desired ~1.9k target.

The unsolved problem is:

> **When should Beyond trust Structural Prior, and when should it trust the v2 live expert?**

Do not describe the oracle as a model or deployable result.

Production remains:

`live_adjustment = 0`

## Immediate C1-alpha next action — v7

Build an **event-level expert reliability diagnostic** for the existing v2 pair.

One diagnostic row per completed event. Derive PIT-safe features only:

- Structural Prior P50 / occupancy;
- round number / current-season home evidence before T-1;
- earliest and latest v2 live estimate in final 24h;
- prior-vs-live disagreement magnitude/sign;
- v2 prediction range / standard deviation / slope across final 24h;
- observation window and snapshot count;
- signal readiness / data quality;
- matched-sector vs raw-only evidence;
- release / coverage flags.

Actual outcome and oracle winner are evaluation labels only, never predictors.

After v7, define a **small predeclared reliability policy** and validate it by whole-event holdout. Do not build another broad hyperparameter/stacking sweep first.

## Dynamic pricing / E0 — continue in parallel

Pricing is a first-class intervention.

MVP sector output:

- `HOLD / INCREASE / DECREASE`;
- proposed price/scenario;
- projected sell-through/availability impact;
- projected revenue proxy;
- confidence;
- reason codes;
- assumption/model version.

Before learned elasticity exists, label it assumption-based scenario analysis.

Never change a club's production price automatically:

`auto_price_change_allowed = false`

## No-action semantics

Preferred label:

**Projected outcome if current trajectory continues**

This is a continuation scenario, not causal proof.

## Historical governance

Canonical history:

- Ekstraklasa 2021/22–2025/26;
- 1,530 matches;
- 7,650 horizon rows;
- verified capacity coverage 100%.

2024/25 and 2025/26 are no longer pristine untouched T-30 holdouts. Do not repeatedly tune against them or relabel them as untouched.

## Critical rule: do not re-run just to recover context

Do not retrain models, rebuild feature stores, replay imports or rerun historical benchmarks merely to understand current state.

Re-run only when the model/feature/data/benchmark contract changes, a new challenger is intentionally evaluated, governance requires it, or the user explicitly requests reproduction.

## Immediate work order

1. complete and persist **v7 expert reliability diagnostic** for Structural Prior + v2 live expert;
2. derive one small predeclared selector/reliability policy and validate it whole-event;
3. keep Structural Prior/orchestrator healthy and `live_adjustment=0`;
4. continue sector trajectory gap/status and no-action projection;
5. continue price-data ingest and E0 pricing scenarios;
6. persist recommendation/decision/execution history;
7. keep collecting prospective 2026/27 evidence;
8. continue T-30 R&D in parallel, not as the product critical path.

## One-line cold-start instruction

> **Do not wait for 20 matches and do not start another generic model tournament: the best current challenger is the v2 final-24h expert at 2,929 MAE, the v2 prior/live oracle is ~1,868, and the next task is to diagnose PIT-safe expert reliability so Beyond can learn when to trust each expert without outcome leakage.**
