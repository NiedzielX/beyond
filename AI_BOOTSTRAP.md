# Beyond — AI Bootstrap / Read This First

Last verified: **2026-10-15**

This file exists to prevent every new AI/chat session from rediscovering the same model state by re-running benchmarks, rebuilding datasets or reverse-engineering the repo history.

## Cold-start rule

**Before doing any Beyond forecasting / ML work, read this file first.**

Then read, only as needed:

1. `ml/CURRENT_MODEL.md` — canonical current model / pipeline state;
2. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — implementation plan and phase status;
3. `ml/NORTH_STAR.md` — objective and evaluation philosophy;
4. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md` — promotion / evidence gates.

## Critical rule: do not re-run just to recover context

Do **not** retrain models, rebuild the five-season feature store, rerun historical benchmarks, replay Supabase imports, or reproduce old holdouts merely to understand where the project is.

The frozen results and model IDs below are trusted project state unless one of the explicit re-run triggers fires.

### Re-run is justified only when at least one is true

- model code / hyperparameters changed;
- feature contract changed;
- historical input version or hash changed;
- a source-data correction affects the benchmark set;
- benchmark protocol changed;
- a new challenger is intentionally being evaluated;
- the user explicitly asks for reproduction / verification;
- a governance check requires a fresh run.

If none of these is true, **read the persisted result and continue from the next unfinished step.**

## North star

Build the best leakage-safe **live forecasting system** for final attendance / ticket demand and its evolution toward kickoff.

Core product stack:

`Structural Prior -> live-trajectory-v1.1 -> trajectory-gap-v1 -> shadow revision -> detection/revision audit -> promotion governance`

Business priority by horizon:

1. T-30 — planning / major intervention;
2. T-14 — strong intervention / correction;
3. T-7 — tactical optimisation;
4. T-3 — late adjustment;
5. T-1 — final estimate / calibration.

The product objective is not only minimum late-stage MAE. It is **sufficiently accurate prediction as early as possible to leave the club time to act**.

## Canonical historical dataset

Trusted state:

- seasons: **2021/22–2025/26**;
- competition: **Ekstraklasa**;
- matches: **1,530 = 5 x 306**;
- PIT horizons: **T-30 / T-14 / T-7 / T-3 / T-1**;
- PIT feature snapshots: **7,650**;
- verified stadium-capacity coverage: **100%**;
- model selection season: **2023/24**;
- untouched holdouts: **2024/25 + 2025/26**;
- one verified closed-door zero-attendance match is retained as historical truth but excluded from normal demand training;
- Supabase historical backfill is complete;
- canonical DB export: `public.export_historical_runtime_v1()`.

Pinned exact input hashes:

`ml/data/STRUCTURAL_PRIOR_RUNTIME_V1_INPUT_MANIFEST.md`

## Current historical champions / candidates

| Horizon | Current best spec | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | **1,889.4** | **1,846.3** |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | **1,748.5** | **1,870.4** |
| T-7 | Global v2 verified-capacity occupancy | **1,799.2** | **1,848.0** |
| T-3 | Global v2.3 verified-capacity + match-importance | **1,701.4** | **1,686.4** |
| T-1 | Global v2.3 verified-capacity + match-importance | **1,684.3** | **1,682.0** |

Do not reproduce these numbers unless a re-run trigger above is true.

Strategic R&D target remains: **T-30 < 1,700 MAE** while preserving true OOS validation.

## Structural Prior Runtime v1

### T-30

Model ID:

`structural-prior-runtime-v1-t30-extra-full`

- estimator: ExtraTreesRegressor;
- 500 trees;
- `min_samples_leaf=3`;
- `max_features=0.8`;
- baseline: `baseline_season`;
- full PIT features including validated importance interactions;
- target: verified-capacity occupancy residual;
- output clipped to `[0, verified_capacity]`.

### T-14

Model ID:

`structural-prior-runtime-v1-t14-hist-base`

- estimator: HistGradientBoostingRegressor, absolute-error loss;
- learning rate 0.05;
- max iter 180;
- max leaf nodes 15;
- min samples leaf 10;
- L2 = 1;
- baseline: `baseline_r3`;
- base PIT features;
- target: verified-capacity occupancy residual.

Runtime / feature code:

- `ml/features/structural_prior_feature_store_v1.py`;
- `ml/demand_engine/current_structural_prior_features.py`;
- `ml/demand_engine/structural_prior_runtime.py`;
- `ml/structural_prior_runtime_benchmark_v1.py`.

## First genuine current-event prior

Event:

**Lech Poznań vs Wisła Kraków — 31 October 2026**

Trusted persisted state:

- ticket event ID: `6`;
- source horizon: **T-30**;
- PIT cutoff: **2026-10-01 16:30:00 UTC**;
- model: `structural-prior-runtime-v1-t30-extra-full`;
- P50: **31,832.41**;
- stadium capacity: **43,269**;
- expected occupancy: **73.57%**;
- persisted row: `private.structural_prior_forecasts_v1.id = 1`;
- resolver `public.get_structural_prior_v1(...)` returns `ready`;
- P10/P90 intentionally remain NULL until probabilistic calibration.

Do not regenerate this prior merely to prove that it exists. Query the persisted row if current confirmation is needed.

## Live Demand Engine status

### Phase A — Foundation: DONE

Canonical live feature contract:

`live-trajectory-v1.1`

Canonical evidence store:

`private.live_trajectory_feature_snapshots_v1`

### Phase B — Shadow Forecasting: DONE

Completed:

- Step 6 — genuine Structural Prior runtime;
- Step 7 — expected trajectory / trajectory gap;
- Step 8 — Structural Prior shadow revisions;
- Step 9 — first-detection / revision audit;
- Step 10 — promotion governance / shadow-only enforcement.

### Step 7 contract

Code:

`ml/demand_engine/trajectory_gap.py`

DB:

- `private.trajectory_gap_observations_v1`;
- `private.trajectory_gap_reference_pool_v1`.

Rules:

- public inventory is a **demand proxy, not confirmed paid sales**;
- no 1:1 conversion from final attendance P50 into public seat-map inventory;
- Structural Prior is mandatory anchor;
- expected progress comes from other PIT-valid trajectories at the same canonical horizon;
- target event and future evidence are excluded;
- minimum descriptive reference pool = **3 events / 2 clubs**;
- status = `UNDERPERFORMING / ON_TRACK / OUTPERFORMING / INSUFFICIENT_SIGNAL`;
- confidence = `NONE / LOW / MEDIUM / HIGH`.

Current T-14 descriptive reference pool at last verification:

- 3 events;
- 2 clubs;
- progress Q25 2.01%;
- median 2.23%;
- Q75 6.19%;
- confidence LOW.

### First new-stack shadow revision

Persisted row:

`public.forecast_observations.id = 1208`

State:

- model version: `beyond-demand-engine-v1-structural-prior-shadow`;
- Structural Prior source: id 1;
- historical P50: **31,832**;
- live adjustment: **0**;
- final P50: **31,832**;
- P10/P90: NULL;
- live features: `live-trajectory-v1.1`;
- trajectory gap: `trajectory-gap-v1`;
- correction remains noop until evidence gate passes.

## Evidence maturity / learned correction

Phase C learned live correction is **blocked on evidence**, not on infrastructure.

Current training-eligible checkpoint evidence at last verification:

| Horizon | Eligible |
|---|---:|
| T-30 | 0 |
| T-14 | 3 |
| T-7 | 3 |
| T-3 | 2 |
| T-1 | 5 |

Promotion governance remains:

- 20 independent completed matches;
- challenger MAE below incumbent;
- positive uplift;
- frozen candidate/evidence package;
- mandatory human review;
- no automatic production activation.

Source of truth:

`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`

## Current next actions

When starting a new session, do not reconstruct old work. Start here:

1. collect prospective evidence on the completed Phase-B stack;
2. when event 6 reaches a canonical reference checkpoint, evaluate trajectory gap using the frozen v1 rules;
3. continue T-30 historical R&D toward <1,700 MAE in parallel;
4. train Phase C residual correction only when evidence governance permits;
5. then calibrate P10/P50/P90;
6. recommendations/intervention learning comes later.

## What may need a live check in a new session

The following are dynamic and may legitimately require a quick DB/GitHub read:

- whether a new snapshot/checkpoint has arrived;
- whether event 6 or other events now have a new trajectory classification;
- completed-event outcomes;
- evidence counts by horizon;
- current branch / latest merged commit;
- newly merged challenger results;
- current Supabase rows if the user asks for latest state.

A **quick read/query is fine**. A full historical rerun is not.

## What should never be stored here

- credentials;
- API keys;
- service-role keys;
- passwords;
- private tokens.

## One-line cold-start instruction for an AI agent

> Read `AI_BOOTSTRAP.md` and `ml/CURRENT_MODEL.md`; trust persisted frozen benchmark/model state unless an explicit re-run trigger is present; query only dynamic state; continue from the first unfinished action instead of reproducing prior work.
