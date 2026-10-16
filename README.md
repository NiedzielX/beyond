# Beyond

Beyond Ticketing engineering workspace.

## Start here

For any new AI / engineering session, **do not reconstruct the project from old benchmarks**.

Read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state, trusted frozen results, re-run rules and next actions;
2. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — canonical current forecasting / Demand Engine state;
3. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — current implementation phase and sequence;
4. [`ml/T30_RND_STATUS_2026-10-16.md`](ml/T30_RND_STATUS_2026-10-16.md) — current T-30 research state, rejected challengers and active validation rule;
5. [`ml/T30_RND_GOVERNANCE_V2.md`](ml/T30_RND_GOVERNANCE_V2.md) — T-30 rolling-origin / prospective validation policy;
6. [`ml/NORTH_STAR.md`](ml/NORTH_STAR.md) — model objective and evaluation philosophy;
7. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — evidence and promotion gates.

**Rule:** frozen benchmarks and persisted model state must not be re-run merely to recover context. A re-run is justified only when model code, feature contracts, input data, benchmark protocol or an intentional challenger changes, or when explicit verification is requested.

**T-30 validation rule from 2026-10-16:** 2024/25 and 2025/26 are exposed fixed historical regression/reference seasons for new T-30 R&D and must not be treated as fresh untouched holdouts. New T-30 challenger selection uses the rolling-origin development gate; fresh promotion evidence must come from prospective 2026/27 outcomes or another explicitly locked future period.

## Current direction

Beyond is building a leakage-safe live attendance / ticket-demand forecasting stack:

`Structural Prior -> Live Ticketing Trajectory -> Trajectory Gap -> Shadow Forecast Revision -> Evidence / Promotion`

Early actionability is first-class: T-30 and T-14 matter because clubs still have time to react.

## ML / forecasting

The current multi-club benchmark uses five Ekstraklasa seasons (2021/22–2025/26), 1,530 matches and 7,650 point-in-time snapshots. Current results and model IDs are maintained in [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md).

Older Lech-only audits and v0.1 benchmarks are retained as **historical lineage only** and must not be treated as the current starting point.
