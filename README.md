# Beyond

Beyond Ticketing engineering workspace.

## Start here

For any new AI / engineering session, **do not reconstruct the project from old benchmarks or stale implementation notes**.

Read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state, current runtime status and immediate work order;
2. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — canonical current forecasting / Demand Engine state;
3. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — current model-development plan;
4. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — live engine implementation and promotion roadmap;
5. [`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`](ml/C1_V8_PROSPECTIVE_SHADOW_V1.md) — frozen C1 prospective runtime/governance;
6. [`ml/SECTOR_DECISION_PRICING_V1.md`](ml/SECTOR_DECISION_PRICING_V1.md) — E0 sector/pricing product contract;
7. [`ml/NORTH_STAR.md`](ml/NORTH_STAR.md) — model objective and evaluation philosophy;
8. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — evidence and promotion gates.

**Rule:** frozen benchmarks and persisted model state must not be re-run merely to recover context. A re-run is justified when model code, feature contracts, input data, benchmark protocol or an intentional challenger changes, or when explicit verification is requested.

## Current direction

Beyond is building a live demand decision system.

For model development, use exactly these workstreams:

- **a) Dane historyczne — dopracować, nie przebudowywać**;
- **b) Aktualny sezon — wzmocnić**;
- **c) Context meczu — rozbudować**;
- **d) Live demand — najmocniej rozwinąć**.

Before further development, first run:

- **Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy.**

## Kolejność developmentu

1. **Walidacja obecnego modelu**
2. **b) Aktualny sezon — wzmocnić**
3. **c) Context meczu — rozbudować**
4. **d) Live demand — najmocniej rozwinąć**
5. **a) Dane historyczne — dopracować, nie przebudowywać**

Skrót:

`Walidacja -> b -> c -> d -> tuning a`

See [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md).

## Current evidence boundary

The historical Structural Prior is mature and benchmarked. C1 v8 is still `EXPERIMENTAL_SHADOW`.

As of 2026-10-18 the prospective C1 pipeline has created predictions for new matches, but **no prospective event has been scored yet**, so there is no confirmed prospective live MAE.

Do not present development replay results around ~2.0k–2.7k as production accuracy.

## ML / forecasting

The current multi-club historical benchmark uses five Ekstraklasa seasons (2021/22–2025/26), 1,530 matches and 7,650 point-in-time horizon rows. Current results and model IDs are maintained in [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md).

Older Lech-only audits and v0.1 benchmarks are historical lineage only and must not be treated as the current starting point.
