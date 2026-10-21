# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md) — concise plan / status / milestone tracking;
3. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — detailed current forecasting state;
4. [`ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`](ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md) — selected early-live package evidence;
5. [`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`](ml/artifacts/d2_long72_stage2_p2_v1/manifest.json) — immutable long72 package lineage;
6. [`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`](ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md) — Stage-1 tournament;
7. [`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`](ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md) — frozen long72 dataset/anchor;
8. [`ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`](ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md) — sealed Pre-Live v3 research anchor;
9. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — canonical roadmap;
10. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — accuracy-first development rules;
11. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — live-engine roadmap;
12. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Current state

### Track A — frozen final24 validation

Keep unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Track A continues append-only prospective validation.

### Track B — frozen research packages

Pre-Live v3 research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Frozen early-live package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Long72 scope:

`24 < hours_to_kickoff <= 72`

Exact package:

- frozen T-3 checkpoint anchor;
- `inventory-linear-extrapolation` expert;
- `±0.10` occupancy correction cap;
- `P2-observation-maturity` reliability.

Development evidence:

- anchor MAE: `3707.14`;
- frozen P2 package MAE: `3012.63`;
- improvement: `+694.51 / +18.73%`;
- event improvement rate: `61.54%`;
- worst event degradation: `1488.34`.

This remains **historical exposed research evidence**, not production proof.

## Active next

> **Prospective append-only scoring of the frozen 24–72h package.**

For every new eligible event preserve and score:

1. frozen T-3 anchor;
2. raw inventory extrapolation;
3. frozen P2 forecast;
4. PIT/event/as-of lineage;
5. attendance only after the outcome becomes available.

Do not retune the package from those outcomes.

The 72–168h band remains diagnostic-only until independent-event coverage reaches the predeclared `N>=9` floor.

## Production boundary

Production remains:

`live_adjustment = 0`

Track-A final24, Pre-Live v3 and long72 P2 remain frozen under their existing evidence classes. No research package is automatic production activation.

## Engineering rule

`code -> tests -> CI -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects evidence integrity. It does not pause model development.**
