# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — canonical accuracy-first development rules, CI/CD and evidence requirements;
3. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — current forecasting / product state;
4. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — active development plan;
5. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — live runtime and future live-updater roadmap;
6. [`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`](ml/C1_V8_PROSPECTIVE_SHADOW_V1.md) — frozen C1 prospective runtime/governance;
7. [`ml/SECTOR_DECISION_PRICING_V1.md`](ml/SECTOR_DECISION_PRICING_V1.md) — E0 sector/pricing product contract;
8. [`ml/NORTH_STAR.md`](ml/NORTH_STAR.md) — product/model objective;
9. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## Current objective

The immediate model-development objective is:

> **Reduce forecasting MAE as far as possible with honest, reproducible evidence before treating the model as mature.**

Do not optimize for completing roadmap labels.

The forecasting architecture is now developed in two layers:

### 1. Pre-Live Model v2

`history + current-season regime + match context -> strongest possible pre-live forecast`

This combines and improves the old a/b/c workstreams rather than treating them as isolated post-model corrections.

### 2. Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory state + time-to-kickoff + reliability -> live delta / revised forecast`

The live layer must update the best pre-live forecast continuously rather than operate only at T-30/T-14/T-7/T-3/T-1.

## Active development order

`a2 baseline optimization -> b2 current-season regime -> c2 match context -> freeze Pre-Live v2 -> d2 continuous live updater`

T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints; they are not the only valid model-update moments.

## Workstream interpretation

Current status:

- **a) Historical data:** mature incumbent, but not fully optimized;
- **b) Current season:** `PARTIALLY TESTED / NOT EXHAUSTED`;
- **c) Match context:** `AUDITED + ONE CHALLENGER TESTED / NOT EXHAUSTED`;
- **d) Live demand:** strategically important; new learned live development follows the Pre-Live v2 optimization pass while frozen C1 v8 continues prospective collection in parallel.

Mandatory rule:

> **A failed challenger closes the challenger, not the whole workstream.**

`Current Season Adjustment v1 NOT PROVEN` does not mean b) is complete.

`Future Fixture Context v1 NOT PROVEN` does not mean c) is complete.

## Current evidence boundary

Structural Prior remains the production incumbent.

Historical reference MAE is roughly **1.65k–1.89k** depending on horizon/season.

Frozen C1 v8 remains `EXPERIMENTAL_SHADOW`.

Historical validation showed:

- raw Live has small-sample generalization problems;
- train-only synthetic trajectory augmentation improves raw Live;
- frozen v8 correctly fell back to Prior on the four current chronological forward events;
- this remains retrospective evidence, not prospective production proof.

Until completed prospective events are scored, there is no confirmed prospective live MAE.

Production remains:

`live_adjustment = 0`

## Engineering accuracy / CI/CD

Model work must be fully reproducible.

Every material challenger must have:

- committed code;
- executable CI workflow;
- pinned dependencies;
- deterministic seeds where applicable;
- explicit data / feature / model versions;
- exact train/dev/holdout protocol;
- PIT and leakage checks;
- incumbent benchmark assertions;
- machine-readable evidence artifact;
- run/artifact identifiers and hashes where available;
- committed human-readable result;
- explicit promote / reject / retain decision;
- canonical documentation updated with the result.

**Do not skip implementation details. Do not treat local/manual results as canonical. Do not silently retune against the same holdout.**

See [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) for the full non-negotiable contract.
