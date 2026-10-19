# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — canonical accuracy-first development rules, CI/CD and evidence requirements;
3. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — current forecasting / product state;
4. [`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json) — sealed Pre-Live v2 historical candidate lineage;
5. [`ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md`](ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md) — exact freeze evidence;
6. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — active accuracy roadmap;
7. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — live runtime and d2 roadmap;
8. [`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`](ml/C1_V8_PROSPECTIVE_SHADOW_V1.md) — frozen C1 prospective runtime/governance;
9. [`ml/SECTOR_DECISION_PRICING_V1.md`](ml/SECTOR_DECISION_PRICING_V1.md) — E0 sector/pricing product contract;
10. [`ml/NORTH_STAR.md`](ml/NORTH_STAR.md) — product/model objective;
11. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## Current objective

The immediate model-development objective is:

> **Reduce forecasting MAE as far as possible with honest, reproducible evidence before treating the model as mature.**

Do not optimize for completing roadmap labels.

The forecasting architecture is developed in two layers:

### 1. Frozen Pre-Live Model v2 historical candidate

`history + proven current-season regime -> frozen pre-live anchor`

Historical c2 context extension is currently:

`NO_CONTEXT_ALL_HORIZONS`

This means no additional historical c2 feature family survived the current PIT-safe five-season evaluation. It does **not** mean context has no value. Forward-only rivalry, verified absences, media/hype and similar signals remain prospective research/shadow inputs until genuine point-in-time evidence exists.

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Canonical manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

Manifest SHA256:

`44c911d1ac8b1bf6870ed31e1a636b9b8374d8c8da2d57ba3b4fb5b4aaba4d3c`

### 2. Continuous Live Updater v2

`frozen Pre-Live v2 + live trajectory + inventory state + time-to-kickoff + reliability -> live delta / revised forecast`

The live layer must update the immutable frozen Pre-Live v2 anchor continuously rather than operate only at T-30/T-14/T-7/T-3/T-1.

## Active development order

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 ACTIVE`

Current active workstream:

**d2 — Continuous Live Updater against frozen Pre-Live v2**.

T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints; they are not the only valid model-update moments.

## Workstream interpretation

Current status:

- **a2 Historical data:** `CLOSED FOR CURRENT HISTORICAL DATA`;
- **b2 Current season:** `CLOSED FOR CURRENT HISTORICAL DATA / FROZEN INTO PRE-LIVE V2`;
- **c2 Historical match context:** `SUFFICIENTLY EVALUATED / NO HISTORICAL CONTEXT EXTENSION FROZEN`;
- **Pre-Live v2 historical candidate:** `SEALED / REPRODUCIBLE / HISTORICAL CANDIDATE ONLY`;
- **d2 Live demand:** `ACTIVE`.

Mandatory interpretation rule:

> **A failed challenger closes the challenger, not the whole workstream.**

The reason a2/b2/c2 are now closed for the current historical dataset is not that one idea failed. They were closed only after the realistic remaining hypotheses were tested, blocked by unavailable PIT-safe history, or explicitly deferred with rationale.

They may be reopened only for materially new data, a materially new hypothesis, or new genuine prospective evidence. Do not silently restart old grids against the same exposed historical references.

## What was actually completed before the freeze

### a2 — historical baseline optimization

Completed evidence includes:

- feature-group contribution / ablation;
- explicit season-recency weighting;
- internal estimator-family challengers;
- CatBoost / LightGBM / XGBoost external family challengers for T-7;
- horizon-specific optimization;
- T-7 regularization and fixed temporal robustness;
- stronger multi-fold selection for unresolved horizons;
- persistent cross-season club calibration under two fixed formulations.

Final historical base state:

- T-30: retained Structural Prior;
- T-14: retained Structural Prior;
- T-7: `hist31-leaf20-l2-1`;
- T-3: retained Structural Prior;
- T-1: retained Structural Prior.

T-7 fixed audit improves MAE in 4/4 rolling folds with mean improvement **+104.66 MAE**.

### b2 — current-season regime

The successful formulation is same-season actual-vs-own-model residual state with strict PIT completion semantics:

`prior kickoff + 3h <= current forecast as_of`

Frozen b2 policies:

- T-30: `NO_ADJUSTMENT`;
- T-14: `NO_ADJUSTMENT`;
- T-7: `ewma50-resid-k6-cap05-min3`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

Non-zero policies activate only after at least **3 earlier completed same-season home matches**.

Final four-fold mean MAE improvements:

- T-7: **+51.47**;
- T-3: **+70.44**;
- T-1: **+69.54**.

Known risk remains explicit: max harmful single-event regression observed in the fixed audit is **+2,760.55 seats**, and club-level uplift is heterogeneous.

### c2 — historical match context

Historical context work included:

- audit of already-existing opponent / pair / form / table / congestion features;
- Future Fixture Context v1;
- sequence-aware streak / points-acceleration features;
- current-table stakes / pressure features;
- sequence + stakes interaction.

No historical c2 extension survived the frozen protocol. T-1 `sequence_stakes` won development but worsened both reference seasons, mean **-36.97 MAE** versus the frozen a2+b2 stack, so it was rejected without post-hoc rescue.

Forward-only context such as rivalry, verified absences and media/hype remains prospective research because complete historical PIT truth is unavailable.

## Frozen Pre-Live v2 reference state

Historical reference mean MAE across exposed 2024/25 + 2025/26:

- T-30: `1867.82`;
- T-14: `1809.45`;
- T-7: **`1691.40`**;
- T-3: **`1682.63`**;
- T-1: **`1661.52`**.

Freeze CI verified:

- 5/5 unit tests PASS;
- historical input hash PASS;
- **20/20 exact horizon-season MAE reproduction cells PASS at tolerance `1e-9`**;
- fresh manifest vs committed manifest byte-for-byte `cmp` PASS;
- canonical manifest SHA lock PASS.

This is a historical candidate freeze, not a production promotion.

## d2 — active now

New learned live development must use the frozen Pre-Live v2 lineage as its anchor.

Primary target direction:

`live_delta = actual_attendance - frozen_pre_live_v2_p50`

or a capacity-normalized equivalent.

Final learned candidate concept:

`d2_p50 = frozen_pre_live_v2_p50 + predicted_live_delta`

Start with one continuous model over time-to-kickoff rather than five fragmented horizon models.

Frozen C1 v8 remains `EXPERIMENTAL_SHADOW` and continues prospective evidence collection unchanged. It may be reused as a benchmark/data-infrastructure asset but must not be silently retuned into d2.

## Production boundary

Structural Prior remains the production incumbent.

Production remains:

`live_adjustment = 0`

The frozen Pre-Live v2 historical candidate does not automatically replace production runtime.

Until genuinely prospective completed events are scored, do not present development replay as confirmed prospective live accuracy.

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
