# Beyond — AI Bootstrap / Read This First

Last verified: **2026-10-15 20:30 UTC**

This file exists to prevent every new AI/chat session from rediscovering model state by re-running benchmarks, rebuilding datasets or reverse-engineering repo history.

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

Pinned input contract:

- `ml/data/STRUCTURAL_PRIOR_RUNTIME_V1_INPUT_MANIFEST.md`;
- `supabase/sql/structural_prior_training_export_v1.sql`.

Historical source keys are immutable benchmark inputs. Current-event alias normalization must not rewrite historical training rows.

## Structural Prior Runtime v1 — all five executable horizons

All canonical checkpoints now have frozen executable current-event runtimes. Scheduled inference is **load + predict only** and must never call model `fit()`.

| Horizon | Model spec | Baseline | Features | Estimator | Dev 2023/24 MAE | 2024/25 MAE | 2025/26 MAE |
|---|---|---|---|---|---:|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | `baseline_season` | full PIT + importance | ExtraTrees leaf=3 | 2,559.7 | **1,889.4** | **1,846.3** |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | `baseline_r3` | base PIT | HistGBR absolute-error | 2,340.0 | **1,748.5** | **1,870.4** |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | `baseline_season` | base PIT | GBR Huber | **2,476.8168** | **1,777.6927** | **1,802.2756** |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | `baseline_season` | full PIT + importance | HistGBR 250 | **2,311.6247** | **1,661.7160** | **1,775.0691** |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | `baseline_season` | full PIT + importance | HistGBR 250 | **2,347.9931** | **1,651.7336** | **1,742.8351** |

T-7/T-3/T-1 were recovered as pre-specified executable contracts and then pinned exactly. No post-holdout parameter search was performed. Detailed provenance is in `ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md`.

Strategic R&D target remains: **T-30 < 1,700 MAE** while preserving true OOS validation.

## Frozen artifact bundle — TRUST WITHOUT REBUILDING

Artifact version:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Artifact freeze commit:

`4d6fbae1ab16bfa7b432a012c889c451ab9161ff`

Hashes:

- T-30: `33e32a8b2f0c617c5adde5cdba592151bb25651ef00fc60aa2e5c090adb51da7`
- T-14: `8d2dbb6ce48ae48fe2e5b7f4340c9e2dfadd38c6e23cc7b123c6f1d2303cdc20`
- T-7: `97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`
- T-3: `33f83899a86b8ebbc61ff5cfb2a3ccb2f09d708d41730136f136bda31d374f30`
- T-1: `f67ee9bf6853a01245de5406861b59e491b86a01a8120023868ad54b19f0ebfa`
- historical runtime: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

Files:

`ml/artifacts/structural_prior_runtime_v1/`

Quality gate at freeze:

- 1,530 matches;
- 7,650 PIT rows;
- 7,198 training-eligible rows;
- capacity missing: 0;
- invalid-time rows: 0;
- status: PASS.

## Automatic Structural Prior Materializer

Status:

**DONE / LIVE for T-30 / T-14 / T-7 / T-3 / T-1**

Automation:

- freeze/build workflow: `.github/workflows/structural-prior-artifacts.yml`;
- materializer workflow: `.github/workflows/structural-prior-materializer.yml`;
- cadence: `5,20,35,50 * * * *`;
- Edge Function: `structural_prior_materializer_v1`;
- Edge Function production version at this verification: **10**;
- writer: `public.insert_structural_prior_forecast_v1(jsonb)`;
- due resolver: `public.get_due_early_structural_prior_inputs_v1(...)`;
- model registry: `private.structural_prior_model_specs_v1`.

Versioned activation migrations:

- `supabase/sql/structural_prior_t7_runtime_v1.sql`;
- `supabase/sql/structural_prior_t3_runtime_v1.sql`;
- `supabase/sql/structural_prior_t1_runtime_v1.sql`.

The T-1 resolver path has been verified with future-time read-only simulation: current events resolve to `T-1 / missing_prior` at their genuine T-1 cutoffs and use `structural-prior-runtime-v1-t1-hist-full`.

**Do not pre-materialize T-1 forecasts before their PIT cutoff.** The first current T-1 cutoffs are on 2026-10-16 UTC, so zero persisted T-1 priors is currently expected.

## Current persisted Structural Prior counts

Dynamic state at this verification:

| Horizon | Persisted priors |
|---|---:|
| T-30 | 1 |
| T-14 | 5 |
| T-7 | 1 |
| T-3 | 5 |
| T-1 | 0 — not yet naturally due |

Do not regenerate persisted priors merely to prove they exist. Query current state when needed.

## Live Demand Engine status

### Phase A — Foundation: DONE

Canonical live feature contract:

`live-trajectory-v1.1`

Canonical evidence store:

`private.live_trajectory_feature_snapshots_v1`

### Phase B — Shadow Forecasting: DONE

Completed:

- genuine Structural Prior runtime;
- expected trajectory / trajectory gap;
- Structural Prior shadow revisions;
- first-detection / revision audit;
- promotion governance / shadow-only enforcement;
- automatic Structural Prior materialization at all five checkpoints.

### Latest verified orchestration health

`private.live_forecast_orchestrator_runs_v1.id = 18`

- active events: **12**;
- processed end-to-end: **12**;
- `missing_prior`: **0**;
- skipped: **0**;
- event errors: **0**;
- checkpoint rows materialized: **34**.

This is the key operational invariant: the currently active event set is fully processed with no missing Structural Prior anchor.

No learned live correction is active. `live_adjustment = 0` remains enforced.

## Trajectory gap contract

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

## Evidence maturity / learned correction

Phase C learned live correction is **blocked on evidence, not on infrastructure**.

Current training-eligible live evidence:

| Horizon | Eligible | Total stored |
|---|---:|---:|
| T-30 | 0 | 1 |
| T-14 | 3 | 5 |
| T-7 | 3 | 9 |
| T-3 | 4 | 9 |
| T-1 | 5 | 10 |

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

1. **NEXT operational checkpoint — verify the first naturally due T-1 materialization after 2026-10-16 15:30 UTC**; do not create it early;
2. keep collecting prospective live snapshots, outcomes and governance-eligible evidence on the deployed five-horizon stack;
3. continue T-30 historical R&D toward `<1,700 MAE` in parallel, without blocking evidence collection;
4. train Phase C residual correction only when the evidence gate permits;
5. calibrate P10/P50/P90 after the point forecast/revision layer is mature;
6. recommendations/intervention learning comes later.

## What may need a live check in a new session

The following are dynamic and may legitimately require a small DB/GitHub read:

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
