# Beyond — Structural Prior Materializer v1

Last verified: **2026-10-15 20:30 UTC**

## Status

**DONE / DEPLOYED / LIVE for T-30 / T-14 / T-7 / T-3 / T-1**

The materializer automatically creates genuine point-in-time Structural Prior P50 forecasts for current Ekstraklasa events without retraining the historical model on scheduler runs.

There is no fallback to legacy Lech models.

## Executable horizon scope

| Horizon | Model spec |
|---|---|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` |

## Architecture

One-time build:

`exact canonical 1,530-match DB export -> five-season PIT feature store -> approved benchmark reproduction gate -> final fit on five completed seasons -> frozen joblib artifacts + SHA manifest`

Scheduled runtime:

`due event/checkpoint -> canonical PIT inputs -> frozen artifact load -> current-event PIT row -> predict P50 -> validated DB insert -> Live Forecast Orchestrator`

**The scheduled runtime contains no `fit()` path.**

## Frozen artifact gate — PASSED

Artifact version:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Freeze commit:

`4d6fbae1ab16bfa7b432a012c889c451ab9161ff`

Artifacts under `ml/artifacts/structural_prior_runtime_v1/`:

- T-30 `structural_prior_t30_v1.joblib`
  - SHA-256 `33e32a8b2f0c617c5adde5cdba592151bb25651ef00fc60aa2e5c090adb51da7`;
- T-14 `structural_prior_t14_v1.joblib`
  - SHA-256 `8d2dbb6ce48ae48fe2e5b7f4340c9e2dfadd38c6e23cc7b123c6f1d2303cdc20`;
- T-7 `structural_prior_t7_v1.joblib`
  - SHA-256 `97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`;
- T-3 `structural_prior_t3_v1.joblib`
  - SHA-256 `33f83899a86b8ebbc61ff5cfb2a3ccb2f09d708d41730136f136bda31d374f30`;
- T-1 `structural_prior_t1_v1.joblib`
  - SHA-256 `f67ee9bf6853a01245de5406861b59e491b86a01a8120023868ad54b19f0ebfa`;
- `historical_runtime_v1.csv.gz`
  - SHA-256 `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`;
- `manifest.json`.

Freeze quality gate:

- 1,530 matches;
- 7,650 horizon snapshots;
- 7,198 training-eligible rows;
- missing capacity: 0;
- invalid as-of rows: 0;
- status: PASS.

Detailed runtime metrics and recovery provenance:

`ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md`

## Reproducibility rule

Historical training data must preserve the **pinned source keys exactly**.

Current-event aliases are applied only in the inference adapter. Historical export semantics must not be rewritten to match current aliases.

Versioned SQL:

`supabase/sql/structural_prior_training_export_v1.sql`

## Current-event PIT inputs

Database resolver:

`public.get_due_early_structural_prior_inputs_v1(...)`

Current attendance:

`public.ml_home_attendance_history_v2`

Current sporting results:

`public.sporting_league_matches_shadow`

Team-name mapping:

`private.structural_prior_club_aliases_v1`

Competition normalization:

`private.structural_prior_competition_aliases_v1`

Verified current capacity:

`private.structural_prior_capacity_registry_v1`

Capacity is never substituted with public seat-map size.

Current-capacity evidence added for the live runtime is versioned in:

`supabase/sql/structural_prior_current_capacities_2026_v1.sql`

## Sporting PIT rule

The current sporting raw table stores `event_date` rather than exact historical kickoff time.

To avoid same-day future leakage, v1 uses a conservative rule:

- only completed fixtures whose local `event_date` is **strictly before** the Structural Prior cutoff local date enter state;
- same-day fixtures are excluded even if the source already marks them completed;
- included fixtures use local noon as a versioned representative timestamp for rest/congestion features.

This rule is persisted in each prior's `input_lineage`.

## Persistence

Writer RPC:

`public.insert_structural_prior_forecast_v1(jsonb)`

It validates:

- horizon in T-30/T-14/T-7/T-3/T-1;
- exact ticket event and kickoff;
- exact target cutoff;
- current model spec/family/feature contract;
- normalized validated competition;
- verified registry capacity;
- P50 inside `[0, capacity]`;
- idempotency on event + horizon + cutoff + model spec.

The writer is `SECURITY INVOKER`; `service_role` has the minimal model-spec read permission required to validate lineage.

P10/P90 remain NULL until probabilistic calibration exists.

## Versioned horizon activations

- `supabase/sql/structural_prior_t7_runtime_v1.sql`;
- `supabase/sql/structural_prior_t3_runtime_v1.sql`;
- `supabase/sql/structural_prior_t1_runtime_v1.sql`.

All three migrations have been applied to production.

## Automation

Artifact build:

`.github/workflows/structural-prior-artifacts.yml`

Scheduled materialization:

`.github/workflows/structural-prior-materializer.yml`

Cadence:

`5,20,35,50 * * * *`

After persisting new priors the materializer invokes Live Forecast Orchestrator immediately.

Supabase Edge Function:

`supabase/functions/structural_prior_materializer_v1/index.ts`

Production Edge Function version at last verification: **10**.

Auth:

- GitHub OIDC audience `beyond-structural-prior-materializer`;
- repository `NiedzielX/beyond`;
- ref `refs/heads/main`;
- service-role credential remains only inside Supabase Edge Function environment.

## Current production proof

Persisted prior counts at last verification:

| Horizon | Priors |
|---|---:|
| T-30 | 1 |
| T-14 | 5 |
| T-7 | 1 |
| T-3 | 5 |
| T-1 | 0 — not yet naturally due |

T-3 automatic materialization completed for five current events, including Lech Poznań — Korona Kielce, Górnik Zabrze — Piast Gliwice, GKS Katowice — Pogoń Szczecin, Cracovia — Legia Warszawa and KGHM Zagłębie Lubin — Jagiellonia Białystok.

Latest verified Live Forecast Orchestrator run:

`private.live_forecast_orchestrator_runs_v1.id = 18`

- active events: **12**;
- processed end-to-end: **12**;
- `missing_prior`: **0**;
- skipped: **0**;
- event errors: **0**;
- canonical checkpoints materialized: **34**.

## T-1 rollout invariant

T-1 runtime, registry, resolver, gateway and artifact are deployed.

A read-only future-time resolver check confirms current events switch to:

- horizon `T-1`;
- status `missing_prior` until the prior exists;
- model `structural-prior-runtime-v1-t1-hist-full`;
- exact target cutoff = kickoff minus 1 day.

The first current T-1 cutoff is **2026-10-16 15:30 UTC**. T-1 must **not** be pre-materialized before that time because the system is point-in-time by design.

## Plan position

- Phase A — Foundation: **DONE**
- Phase B — Shadow Forecasting: **DONE**
- Live Forecast Orchestrator v1: **DONE / LIVE**
- Automatic Structural Prior Materializer all five horizons: **DONE / LIVE**
- First naturally due T-1 production materialization: **NEXT operational checkpoint**
- Phase C learned live correction: **BLOCKED ON EVIDENCE**
