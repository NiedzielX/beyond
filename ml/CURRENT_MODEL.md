# Beyond Ticketing — Current Model State

Last verified: **2026-10-15 20:30 UTC**

This file is the canonical short-form source of truth for the current forecasting model and Live Demand Engine state. For cold-start operational instructions, read `AI_BOOTSTRAP.md` first.

## North star

Build the best leakage-safe **live forecasting system** for final attendance / ticket demand and its evolution toward kickoff.

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
- training-eligible snapshots: **7,198**;
- verified historical stadium-capacity coverage: **100%**;
- model selection: **2023/24 only** after training on 2021/22–2022/23;
- untouched holdouts: **2024/25 + 2025/26**;
- one verified closed-door zero-attendance match remains historical truth but is excluded from normal demand training;
- Supabase historical backfill is complete;
- canonical DB export: `public.export_historical_runtime_v1()`.

Exact input hashes are pinned in `ml/data/STRUCTURAL_PRIOR_RUNTIME_V1_INPUT_MANIFEST.md`.

## Current executable Structural Prior by horizon

All five checkpoints now use a frozen executable current-event runtime.

| Horizon | Model spec | 2023/24 dev MAE | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|---:|
| **T-30** | `structural-prior-runtime-v1-t30-extra-full` | 2,559.7 | **1,889.4** | **1,846.3** |
| **T-14** | `structural-prior-runtime-v1-t14-hist-base` | 2,340.0 | **1,748.5** | **1,870.4** |
| **T-7** | `structural-prior-runtime-v1-t7-gbr-base` | **2,476.8168** | **1,777.6927** | **1,802.2756** |
| **T-3** | `structural-prior-runtime-v1-t3-hist-full` | **2,311.6247** | **1,661.7160** | **1,775.0691** |
| **T-1** | `structural-prior-runtime-v1-t1-hist-full` | **2,347.9931** | **1,651.7336** | **1,742.8351** |

T-7/T-3/T-1 are executable conversions of pre-specified historical champion lineages. Their exact Structural Prior v1 values were pinned after a one-time leakage-safe verification; there was no post-holdout parameter search.

Detailed benchmark provenance: `ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md`.

T-30 remains above the strategic **<1,700 MAE** target, so historical R&D continues in parallel.

## Runtime contracts

### T-30

- estimator: `ExtraTreesRegressor`;
- 500 trees;
- `min_samples_leaf=3`;
- `max_features=0.8`;
- baseline: `baseline_season`;
- full PIT + importance interactions;
- target: verified-capacity occupancy residual;
- final output clipped to `[0, verified_capacity]`.

### T-14

- estimator: `HistGradientBoostingRegressor` absolute-error;
- `learning_rate=0.05`;
- `max_iter=180`;
- `max_leaf_nodes=15`;
- `min_samples_leaf=10`;
- `l2_regularization=1`;
- baseline: `baseline_r3`;
- base PIT features;
- target: verified-capacity occupancy residual.

### T-7

- estimator: `GradientBoostingRegressor(loss="huber")`;
- `n_estimators=180`;
- `learning_rate=0.03`;
- `max_depth=2`;
- `min_samples_leaf=8`;
- baseline: `baseline_season`;
- base PIT features;
- target: verified-capacity occupancy residual.

### T-3 / T-1

- estimator: `HistGradientBoostingRegressor(loss="absolute_error")`;
- `learning_rate=0.05`;
- `max_iter=250`;
- `max_leaf_nodes=15`;
- `min_samples_leaf=10`;
- `l2_regularization=1`;
- baseline: `baseline_season`;
- full PIT + importance interactions;
- target: verified-capacity occupancy residual.

## Frozen artifact bundle

Artifact version:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Freeze commit:

`4d6fbae1ab16bfa7b432a012c889c451ab9161ff`

Artifact hashes:

- T-30: `33e32a8b2f0c617c5adde5cdba592151bb25651ef00fc60aa2e5c090adb51da7`
- T-14: `8d2dbb6ce48ae48fe2e5b7f4340c9e2dfadd38c6e23cc7b123c6f1d2303cdc20`
- T-7: `97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`
- T-3: `33f83899a86b8ebbc61ff5cfb2a3ccb2f09d708d41730136f136bda31d374f30`
- T-1: `f67ee9bf6853a01245de5406861b59e491b86a01a8120023868ad54b19f0ebfa`
- historical runtime: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

Normal scheduled materialization is **load + predict only**. It must never fit a model.

## Structural Prior feature semantics

Historical builder:

`ml/features/structural_prior_feature_store_v1.py`

Current-event builder:

`ml/demand_engine/current_structural_prior_features.py`

Rules:

- historical attendance may carry across seasons;
- current-season attendance is separate from long-run history;
- sporting/form/table state resets each season;
- historical benchmark state adds a completed match only after `kickoff + 3h`;
- current-event sporting reconstruction excludes same-local-date fixtures when exact kickoff is unavailable;
- target never enters its own state;
- exact home/opponent and opponent-draw history are PIT-only;
- verified capacity is mandatory;
- current-event inputs after the requested cutoff are rejected.

## Structural Prior materialization status

**DONE / LIVE for T-30 / T-14 / T-7 / T-3 / T-1.**

Production components:

- artifact freeze: `.github/workflows/structural-prior-artifacts.yml`;
- materializer: `.github/workflows/structural-prior-materializer.yml`;
- cadence: `5,20,35,50 * * * *`;
- Edge Function: `structural_prior_materializer_v1`, production version **10** at last verification;
- due resolver: `public.get_due_early_structural_prior_inputs_v1(...)`;
- prior resolver: `public.get_structural_prior_v1(...)`;
- writer: `public.insert_structural_prior_forecast_v1(jsonb)`;
- registry: `private.structural_prior_model_specs_v1`.

The T-1 resolver has been verified to return `T-1 / missing_prior` with `structural-prior-runtime-v1-t1-hist-full` once the simulated clock passes each event's true T-1 cutoff. T-1 priors are intentionally **not** generated before those cutoffs.

Current persisted prior counts:

| Horizon | Priors |
|---|---:|
| T-30 | 1 |
| T-14 | 5 |
| T-7 | 1 |
| T-3 | 5 |
| T-1 | 0 — first current cutoff not yet due |

## Live Demand Engine implementation status

### Phase A — Foundation: **DONE**

Canonical live feature contract: `live-trajectory-v1.1`.

Canonical evidence store: `private.live_trajectory_feature_snapshots_v1`.

### Phase B — Shadow Forecasting: **DONE**

Completed:

1. executable Structural Prior at all five horizons;
2. expected trajectory / trajectory gap;
3. append-only Structural Prior shadow revisions;
4. first-detection / revision audit;
5. promotion governance / shadow-only enforcement;
6. automatic materializer -> orchestrator hand-off.

Latest verified orchestrator run:

`private.live_forecast_orchestrator_runs_v1.id = 18`

- active events: **12**;
- processed end-to-end: **12**;
- `missing_prior`: **0**;
- skipped: **0**;
- event errors: **0**;
- checkpoint rows materialized: **34**.

No learned live correction is active. `live_adjustment = 0` remains enforced.

## Trajectory gap contract

Implementation: `ml/demand_engine/trajectory_gap.py`.

DB:

- `private.trajectory_gap_observations_v1`;
- `private.trajectory_gap_reference_pool_v1`.

Contract:

- public seat-map inventory is a **demand proxy, not confirmed paid sales**;
- Structural Prior P50 is the mandatory final-demand anchor;
- no 1:1 conversion from attendance P50 to public inventory;
- expected progress comes from other PIT-valid, training-eligible trajectories at the same canonical horizon;
- target event and future reference evidence are excluded;
- minimum reference diversity: **3 events / 2 clubs**;
- status: `UNDERPERFORMING / ON_TRACK / OUTPERFORMING / INSUFFICIENT_SIGNAL`;
- confidence: `NONE / LOW / MEDIUM / HIGH`.

## Structural Prior domain guard

Current Structural Prior runtimes are validated on **Ekstraklasa**.

Resolver states:

- `not_due` before the next checkpoint;
- `out_of_domain` outside validated competition scope;
- `missing_prior` when a due current spec has no genuine materialized P50;
- `invalid_prior` on lineage/PIT mismatch;
- `ready` only when exact current model/feature/checkpoint lineage exists.

No silent fallback to legacy Lech models is allowed.

## Live evidence maturity

Current stored evidence:

| Horizon | Training-eligible | Total stored |
|---|---:|---:|
| T-30 | **0** | 1 |
| T-14 | **3** | 5 |
| T-7 | **3** | 9 |
| T-3 | **4** | 9 |
| T-1 | **5** | 10 |

Therefore **no learned live correction is promoted**. Infrastructure is ready; the binding constraint is prospective evidence.

Governance source: `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

Promotion requires:

- 20 independent completed matches;
- challenger MAE below incumbent;
- positive uplift;
- frozen candidate/evidence package;
- mandatory human review;
- no automatic production activation.

## Current product stack

`Structural Prior -> live-trajectory-v1.1 -> trajectory-gap-v1 -> P50-only shadow revision -> first-detection/revision audit -> Promotion Governance`

## Next implementation sequence

1. **Verify first naturally due T-1 materialization after 2026-10-16 15:30 UTC.** Do not backfill it early.
2. Continue prospective evidence collection on the five-horizon live stack.
3. Continue T-30 historical R&D toward **<1,700 MAE** in parallel.
4. Phase C — train/evaluate live residual correction only when evidence governance permits.
5. Phase D — calibrated P10/P50/P90.
6. Phase E — recommendations / intervention learning.

## Evaluation rule

Every historical challenger preserves the chronological contract:

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

- `AI_BOOTSTRAP.md`
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
