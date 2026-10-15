# Beyond Ticketing — Current Model State

Last verified: **2026-10-15**

This file is the canonical short-form source of truth for the current forecasting model and Live Demand Engine state.

## North star

Build the best possible leakage-safe **live forecasting system** for final attendance / ticket demand and its evolution toward kickoff.

The product combines:

- **Structural Prior** — what this match should do from historical/context evidence;
- **Live Ticketing Trajectory** — what the current match is actually doing;
- **Live Correction** — what the divergence implies for the final outcome.

Early actionability is first-class. T-30/T-14 must not be sacrificed for late-horizon accuracy.

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong intervention / correction;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final forecast / calibration checkpoint.

## Canonical historical dataset

- seasons: **2021/22–2025/26**;
- competition: **Ekstraklasa**;
- matches: **1,530** = 5 × 306;
- PIT horizons: **T-30 / T-14 / T-7 / T-3 / T-1**;
- PIT feature snapshots: **7,650**;
- verified historical stadium-capacity coverage: **100%**;
- model selection: **2023/24 only** after training on 2021/22–2022/23;
- untouched holdouts: **2024/25 + 2025/26**;
- one verified closed-door zero-attendance match remains historical truth but is excluded from normal demand training;
- Supabase historical backfill is complete: **1,224** validated 2021/22–2024/25 rows + **306** 2025/26 rows;
- canonical DB export: `public.export_historical_runtime_v1()`.

Exact Structural Prior Runtime v1 input hashes are pinned in:

`ml/data/STRUCTURAL_PRIOR_RUNTIME_V1_INPUT_MANIFEST.md`

## Current best validated historical specification by horizon

| Horizon | Current best spec | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| **T-30** | **Structural Prior Runtime v1 — ExtraTrees + full PIT + verified-capacity occupancy residual** | **1,889.4** | **1,846.3** |
| **T-14** | **Structural Prior Runtime v1 — HistGBR + base PIT + verified-capacity occupancy residual** | **1,748.5** | **1,870.4** |
| T-7 | Global v2 verified-capacity occupancy | **1,799.2** | **1,848.0** |
| T-3 | Global v2.3 verified-capacity + match-importance | **1,701.4** | **1,686.4** |
| T-1 | Global v2.3 verified-capacity + match-importance | **1,684.3** | **1,682.0** |

Combined two-holdout MAE for the executable early-horizon Runtime v1:

- T-30: **~1,867.8**;
- T-14: **~1,809.4**.

Current single lowest holdout MAE is **T-1 = ~1,682.0 on 2025/26**.

### Frozen T-30 runtime

Model spec ID:

`structural-prior-runtime-v1-t30-extra-full`

- `ExtraTreesRegressor`;
- 500 trees;
- `min_samples_leaf=3`;
- `max_features=0.8`;
- baseline: `baseline_season`;
- full PIT feature mode including validated importance interactions;
- target: verified-capacity occupancy residual;
- output clipped to `[0, verified_capacity]`.

T-30 remains above the strategic **<1,700 MAE** target, so historical R&D continues in parallel.

### Frozen T-14 runtime

Model spec ID:

`structural-prior-runtime-v1-t14-hist-base`

- `HistGradientBoostingRegressor`, absolute-error loss;
- `learning_rate=0.05`;
- `max_iter=180`;
- `max_leaf_nodes=15`;
- `min_samples_leaf=10`;
- `l2_regularization=1`;
- baseline: `baseline_r3`;
- base PIT feature mode;
- target: verified-capacity occupancy residual.

## Structural Prior Runtime — current event proof

First genuine current Structural Prior:

**Lech Poznań vs Wisła Kraków — 31 October 2026**

- ticket event: `6`;
- horizon: **T-30**;
- exact PIT cutoff: **2026-10-01 16:30:00 UTC**;
- model: `structural-prior-runtime-v1-t30-extra-full`;
- P50: **31,832.41**;
- verified stadium capacity: **43,269**;
- expected occupancy: **73.57%**;
- persisted as `private.structural_prior_forecasts_v1.id=1`;
- `point_in_time_validated = true`;
- `public.get_structural_prior_v1(...)` returns `ready` with exact model/feature/checkpoint lineage;
- P10/P90 remain intentionally `NULL` until probabilistic calibration exists.

Current DB T-30/T-14 Structural Prior specs point to the Runtime v1 IDs above.

## Structural Prior feature semantics

Historical builder:

`ml/features/structural_prior_feature_store_v1.py`

Current-event builder:

`ml/demand_engine/current_structural_prior_features.py`

Rules:

- historical attendance may carry across seasons;
- current-season attendance is separate from long-run history;
- sporting/form/table state resets each season;
- a completed match enters state only after `kickoff + 3h`;
- target never enters its own state;
- exact home/opponent and opponent-draw history are PIT-only;
- verified historical capacity is season/venue specific;
- current-event attendance and sporting inputs after the requested cutoff are rejected.

Historical quality gate:

- **1,530 matches**;
- **7,650 snapshots**;
- **7,198 training-eligible snapshots**;
- **0 missing verified capacities**;
- **0 as-of / kickoff violations**.

## Live Demand Engine implementation status

### Phase A — Foundation: **DONE**

Completed:

1. canonical `live-trajectory-v1.1` feature store;
2. exact-cutoff readiness;
3. calibrated release/anomaly semantics;
4. append-only PIT live-feature evidence store;
5. explicit live contract registry.

### Phase B — Shadow Forecasting: **DONE**

#### Step 6 — Structural Prior: **DONE**

- 6a adapter / model-domain guard: **DONE**;
- 6b executable historical runtime + current-event PIT row + genuine P50 materialization: **DONE**;
- DB-native five-season historical input: **DONE**.

#### Step 7 — expected trajectory / trajectory gap: **DONE**

Implementation:

`ml/demand_engine/trajectory_gap.py`

DB:

- `private.trajectory_gap_observations_v1`;
- `private.trajectory_gap_reference_pool_v1`.

Contract:

- public seat-map inventory is a **demand proxy, not confirmed paid sales**;
- Structural Prior P50 is the mandatory final-demand anchor;
- there is **no 1:1 conversion** from attendance P50 to public inventory;
- expected progress is descriptive and comes from other PIT-valid, training-eligible trajectories at the same canonical horizon;
- target event and future reference evidence are excluded;
- minimum reference diversity: **3 events / 2 clubs**;
- status: `UNDERPERFORMING / ON_TRACK / OUTPERFORMING / INSUFFICIENT_SIGNAL`;
- confidence: `NONE / LOW / MEDIUM / HIGH`.

Current T-14 descriptive reference pool:

- **3 events / 2 clubs**;
- progress Q25 **2.01%**;
- median **2.23%**;
- Q75 **6.19%**;
- confidence: **LOW**.

First event-6 trajectory observation:

- source snapshot `15278`;
- as-of `2026-10-15 12:31:03 UTC`;
- `live-trajectory-v1.1`;
- **754 / 754 clean snapshots**;
- signal readiness `ready`;
- first availability **17,683**;
- current availability **10,534**;
- normalized net absorption **40.43%**;
- hours to kickoff **387.98**;
- status `INSUFFICIENT_SIGNAL`;
- reason `outside_reference_checkpoint_window`.

This is an intentional fail-closed result. The live signal is healthy; the event has simply not yet entered the frozen T-14 reference window.

#### Step 8 — persist shadow live forecasts: **DONE**

Implementation:

`ml/demand_engine/structural_prior_shadow.py`

First new-stack shadow revision:

- `public.forecast_observations.id=1208`;
- model version `beyond-demand-engine-v1-structural-prior-shadow`;
- source Structural Prior `id=1`;
- historical model `structural-prior-runtime-v1-t30-extra-full`;
- historical P50 **31,832**;
- live adjustment **0**;
- final P50 **31,832**;
- P10/P90 **NULL**;
- live feature version `live-trajectory-v1.1`;
- trajectory gap `INSUFFICIENT_SIGNAL / outside_reference_checkpoint_window`.

The source Structural Prior horizon is retained. The legacy nearest-checkpoint labeler is not used for the new stack.

#### Step 9 — first detection / revisions: **DONE**

DB:

- `private.trajectory_first_detection_v1`;
- trigger `private.capture_first_trajectory_divergence_v1()`;
- view `private.structural_shadow_revision_history_v1`.

Rules:

- only PIT-valid `UNDERPERFORMING` or `OUTPERFORMING` observations create first detection;
- `ON_TRACK` and `INSUFFICIENT_SIGNAL` never create a false alert;
- out-of-order earlier PIT evidence can replace a later detection timestamp;
- every new-stack shadow forecast is append-only in `forecast_observations`;
- after actual attendance is known, each revision is labelled `IMPROVED / WORSENED / UNCHANGED`; before outcome it remains `PENDING_OUTCOME`.

Current event 6:

- first detection: **none** — correct;
- new-stack revisions: **1**;
- revision effect: `PENDING_OUTCOME`.

Versioned SQL evidence:

`ml/demand_engine/sql/phase_b_shadow_contracts_v1.sql`

#### Step 10 — promotion gate: **DONE as governance**

Single source of truth:

`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`

Existing Live Ticketing gate remains authoritative:

- **20 independent completed matches**;
- challenger MAE must beat incumbent MAE;
- uplift must be positive;
- frozen candidate package;
- mandatory human review;
- `auto_activation_allowed = false` at DB level.

The new live stack does **not** create a second threshold. The Step-8 writer is shadow-only and preserves Structural Prior P50 until a future learned correction passes this governance.

## Structural Prior domain guard

Current historical champions are validated on **Ekstraklasa**.

Resolver states:

- `not_due` before T-30;
- `out_of_domain` outside validated competition scope;
- `missing_prior` when a due current spec has no genuine materialized P50;
- `invalid_prior` on lineage/PIT mismatch;
- `ready` only when exact current model/feature/checkpoint lineage exists.

No silent fallback to Lech v1.3/v0.3 is allowed.

## Live evidence maturity

Canonical checkpoint evidence remains small:

| Horizon | Training-eligible |
|---|---:|
| T-30 | **0** |
| T-14 | **3** |
| T-7 | **3** |
| T-3 | **2** |
| T-1 | **5** |

Therefore **no learned live correction is promoted**. Phase B being complete means the leakage-safe observation stack exists; it does not mean live uplift is statistically proven.

## Current product stack

`Structural Prior -> live-trajectory-v1.1 -> trajectory-gap-v1 -> P50-only shadow revision -> first-detection/revision audit -> Promotion Governance`

## Next implementation sequence

1. **NOW — prospective evidence collection on the new stack.**
2. When event 6 enters the frozen T-14 reference window, generate its first descriptive trajectory classification without changing Step-7 rules.
3. Continue T-30 historical R&D toward **<1,700 MAE** in parallel.
4. Phase C — train/evaluate live residual correction only when evidence is sufficient.
5. Phase D — calibrated P10/P50/P90.
6. Phase E — recommendations / intervention learning.

## Evaluation rule

Every historical challenger preserves the same chronological contract:

- selection on 2023/24 only;
- 2024/25 and 2025/26 untouched holdouts;
- all features point-in-time;
- no target outcome in its own state;
- same completed event/checkpoint for baseline-vs-model comparison.

Every future live challenger must compare, on identical completed events/checkpoints:

1. Structural Prior error;
2. Structural Prior + live correction error.

No model is promoted because it looks intuitive or wins on a tiny prospective sample.

## Key evidence files

- `ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md`
- `ml/results/LIVE_DEMAND_ENGINE_PHASE_B_2026-10-15.md`
- `ml/data/STRUCTURAL_PRIOR_RUNTIME_V1_INPUT_MANIFEST.md`
- `ml/features/structural_prior_feature_store_v1.py`
- `ml/demand_engine/current_structural_prior_features.py`
- `ml/demand_engine/trajectory_gap.py`
- `ml/demand_engine/structural_prior_shadow.py`
- `ml/demand_engine/sql/phase_b_shadow_contracts_v1.sql`
- `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`
- `ml/NORTH_STAR.md`
