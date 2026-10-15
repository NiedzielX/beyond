# Beyond — AI Bootstrap / Read This First

Last verified: **2026-10-15**

This file exists to prevent every new AI/chat session from rediscovering the same model state by re-running benchmarks, rebuilding datasets or reverse-engineering the repo history.

## Cold-start rule

**Before doing any Beyond forecasting / ML work, read this file first.**

Then read, only as needed:

1. `ml/CURRENT_MODEL.md` — canonical model / pipeline state;
2. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — implementation plan and phase status;
3. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md` — live orchestration state;
4. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md` — frozen Structural Prior runtime / materialization state;
5. `ml/NORTH_STAR.md` — objective and evaluation philosophy;
6. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md` — promotion / evidence gates.

## Critical rule: do not re-run just to recover context

Do **not** retrain models, rebuild the five-season feature store, rerun historical benchmarks, replay Supabase imports, or reproduce old holdouts merely to understand where the project is.

The frozen results, artifact hashes and model IDs below are trusted project state unless one of the explicit re-run triggers fires.

### Re-run is justified only when at least one is true

- model code / hyperparameters changed;
- feature contract changed;
- historical input version or hash changed;
- a source-data correction affects the benchmark set;
- benchmark protocol changed;
- a new challenger is intentionally being evaluated;
- the user explicitly asks for reproduction / verification;
- a governance check requires a fresh run.

If none of these is true, **read persisted state, query only dynamic rows, and continue from the next unfinished step.**

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

### Historical-export invariant

Historical training rows must preserve pinned source keys exactly. Current-event alias normalization must **not** rewrite historical training data.

This was explicitly validated during artifact freeze after a `radomiak -> radomiak_radom` export normalization changed the 2025/26 T-30 reproduction. The export was corrected rather than changing the approved benchmark.

Versioned contract:

`supabase/sql/structural_prior_training_export_v1.sql`

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

## Structural Prior Runtime v1 — frozen executable early horizons

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

### Frozen artifacts — TRUST WITHOUT REBUILDING

Artifact version:

`structural-prior-runtime-v1-frozen-2026-10-15`

Freeze gate reproduced the approved holdouts exactly before the one-time final fit.

- T-30 artifact SHA-256:
  `33e32a8b2f0c617c5adde5cdba592151bb25651ef00fc60aa2e5c090adb51da7`
- T-14 artifact SHA-256:
  `8d2dbb6ce48ae48fe2e5b7f4340c9e2dfadd38c6e23cc7b123c6f1d2303cdc20`
- historical runtime SHA-256:
  `345bbf72c702fc4356b2ccfe998b5c3c121adea5fef32d34bb9daa9aae10b89d`
- artifact commit:
  `4a8f066742faa24508b733175f7366b4ccaabe2e`

Files:

`ml/artifacts/structural_prior_runtime_v1/`

Normal scheduled materialization does **load + predict only**. It must never call model `fit()`.

## Current genuine Structural Priors

### Original T-30 prior

**Lech Poznań vs Wisła Kraków — event 6**

- horizon: T-30;
- PIT cutoff: 2026-10-01 16:30 UTC;
- P50: **31,832.41**;
- capacity: 43,269;
- expected occupancy: 73.57%;
- persisted prior id: **1**.

### First automatic T-14 batch

Automatic frozen-artifact materialization passed end-to-end on 2026-10-15:

| Prior ID | Event | P50 | Capacity | Occupancy |
|---:|---|---:|---:|---:|
| 2 | Pogoń Szczecin — Radomiak Radom | 16,226.996 | 21,163 | 76.68% |
| 3 | Wisła Kraków — Raków Częstochowa | 17,350.596 | 33,130 | 52.37% |
| 4 | Śląsk Wrocław — Wieczysta Kraków | 19,552.562 | 43,708 | 44.73% |
| 5 | Jagiellonia Białystok — Wisła Płock | 15,635.204 | 22,372 | 69.89% |
| 6 | Legia Warszawa — Lech Poznań | 29,635.741 | 31,006 | 95.58% |

All automatic T-14 priors use the frozen T-14 artifact SHA above.

Do not regenerate persisted priors merely to prove that they exist. Query them if a latest-state check is needed.

## Automatic Structural Prior Materializer

Status:

**DONE / LIVE for T-30 and T-14**

Canonical doc:

`ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`

Automation:

- freeze/build workflow: `.github/workflows/structural-prior-artifacts.yml`;
- materializer workflow: `.github/workflows/structural-prior-materializer.yml`;
- materializer cadence: `5,20,35,50 * * * *`;
- Edge Function: `structural_prior_materializer_v1`;
- writer: `public.insert_structural_prior_forecast_v1(jsonb)`;
- due resolver: `public.get_due_early_structural_prior_inputs_v1(...)`.

The materializer invokes Live Forecast Orchestrator immediately after inserting priors.

T-7 / T-3 / T-1 do not yet have a frozen executable current-event runtime and intentionally remain fail-closed.

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

### Operational automation: DONE for T-30/T-14

Live Forecast Orchestrator v1 and automatic T-30/T-14 Structural Prior Materializer are deployed.

Latest verified orchestrator run:

`private.live_forecast_orchestrator_runs_v1.id = 3`

- active events: **13**;
- processed end-to-end: **6**;
- remaining `missing_prior`: **6**;
- skipped/out-of-domain: **1**;
- event errors: **0**;
- canonical checkpoint rows materialized: **34**.

The six remaining `missing_prior` events are T-7/T-3 and are expected until later-horizon executable runtimes exist.

Latest shadow observation IDs from the first automatic T-14 batch:

- event 10 -> `forecast_observations.id = 1211`;
- event 16 -> `1212`;
- event 23 -> `1213`;
- event 21 -> `1214`;
- event 22 -> `1215`;
- event 6 -> `1216`.

No learned live correction is active. `live_adjustment = 0` remains enforced.

### Trajectory gap contract

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

## Evidence maturity / learned correction

Phase C learned live correction is **blocked on evidence, not on infrastructure**.

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

When starting a new session, do not reconstruct old work. Continue here:

1. **NEXT — freeze executable current-event Structural Prior runtimes for T-7 / T-3 / T-1** and extend automatic materialization so the live loop keeps a genuine historical anchor through kickoff;
2. keep collecting prospective live evidence on the deployed stack;
3. continue T-30 historical R&D toward <1,700 MAE in parallel, without blocking live evidence collection;
4. train Phase C residual correction only when evidence governance permits;
5. calibrate P10/P50/P90 after the point forecast/revision layer is mature;
6. recommendations/intervention learning comes later.

## What may need a live check in a new session

The following are dynamic and may legitimately require a quick DB/GitHub read:

- new snapshots/checkpoints;
- current trajectory classifications;
- completed-event outcomes;
- evidence counts by horizon;
- newly materialized prior rows;
- latest orchestrator run;
- current branch / latest merged commit;
- newly merged challenger results.

A **small targeted read/query is fine**. A historical rerun is not.

## What should never be stored here

- credentials;
- API keys;
- service-role keys;
- passwords;
- private tokens.

## One-line cold-start instruction for an AI agent

> Read `AI_BOOTSTRAP.md` and current-state docs; trust frozen benchmark/artifact/prior state unless an explicit re-run trigger exists; query only dynamic state; continue from the first unfinished action instead of reproducing prior work.
