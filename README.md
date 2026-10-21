# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and execution order;
2. [`ml/MAE_RESEARCH_ROADMAP_V3.md`](ml/MAE_RESEARCH_ROADMAP_V3.md) — canonical MAE-first research strategy;
3. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md) — concise status and milestones;
4. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — detailed current forecasting state;
5. [`ml/CORE_PRODUCT_STATUS.md`](ml/CORE_PRODUCT_STATUS.md) — global historical core and product-level model status;
6. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — experiment / CI rules;
7. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — frozen live packages and live evidence lane;
8. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion boundary.

Historical result documents and manifests remain immutable evidence and are linked from `ml/CURRENT_MODEL.md`.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with point-in-time-safe, reproducible evidence.**

Complexity is not the objective. Lower future MAE is.

## Operating model

### Lane A — Evidence / validation

Keep frozen packages immutable and score them forward:

- final24 `v2/Ridge/P2`;
- long72 `inventory-linear-extrapolation + P2`;
- persist forecasts before labels where possible;
- append outcomes later without recomputation;
- keep evidence class explicit.

### Lane B — MAE R&D

Do **not** wait for Lane A to accumulate labels. In parallel:

1. make rolling / forward validation canonical;
2. test MAE-native losses and median/quantile models;
3. add genuinely new PIT-safe context features;
4. test forecast combinations;
5. measure live-ticket signal as an incremental residual over the strongest structural/global model;
6. quantify uncertainty around `ΔMAE`;
7. open 72–168h learning once the predeclared `N>=9` start floor is reached.

## Current structural/global baseline

Beyond already has a multi-club historical core:

- 1,530 Ekstraklasa matches across five complete seasons;
- 7,650 PIT snapshots across T-30/T-14/T-7/T-3/T-1;
- Global Model v2.1 residual architecture;
- roughly 16–24% MAE improvement over the club-history baseline across 2024/25 and 2025/26 historical holdouts.

Those historical holdouts are now exposed research evidence and must not be described as unseen again.

## Frozen live packages

### Final24

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

### Long72

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical development evidence:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- improvement `+694.51 / +18.73%`.

Do not retune either frozen package on already-opened evidence.

## Immediate work order

1. finish immutable long72 forecast materialization + append-only scoring;
2. implement canonical rolling/forward validation utilities;
3. run an MAE-native challenger tournament over the strongest global residual benchmark;
4. add event/fixture-block uncertainty for `ΔMAE`;
5. materialize PIT-safe fixture-cannibalization / next-match context;
6. run controlled context ablations;
7. test simple forecast combinations before complex stackers;
8. measure live-ticket incremental uplift over the strongest structural model;
9. keep long168 coverage growing and launch 72–168h research at `N>=9`;
10. preserve future 2026/27 fixtures as genuine prospective evidence.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until an explicit reviewed promotion.

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> forward/event-safe evaluation -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause model development.**
