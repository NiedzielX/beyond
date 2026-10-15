# Beyond — Structural Prior Materializer v1

Last updated: **2026-10-15**

## Purpose

Automatically create genuine point-in-time Structural Prior P50 forecasts for current Ekstraklasa events without retraining the historical model on every scheduler run.

## Scope

v1 supports only the two horizons with a frozen executable current-event runtime:

- **T-30** — `structural-prior-runtime-v1-t30-extra-full`;
- **T-14** — `structural-prior-runtime-v1-t14-hist-base`.

T-7 / T-3 / T-1 remain fail-closed until their own current-event executable runtimes are frozen. There is no fallback to legacy Lech models.

## Architecture

Build time:

`canonical 1,530-match DB export -> five-season PIT feature store -> frozen benchmark reproduction -> final fit on five completed seasons -> joblib artifacts + SHA manifest`

Scheduled runtime:

`due T-30/T-14 event -> canonical PIT inputs -> frozen artifact load -> current-event PIT row -> predict P50 -> validated DB insert -> Live Forecast Orchestrator`

The scheduled runtime contains no `fit()` path.

## Frozen artifact build gate

`ml/demand_engine/freeze_structural_prior_artifacts.py`

The build is allowed only if it reproduces the already-approved untouched holdouts exactly:

| Horizon | 2024/25 MAE | 2025/26 MAE |
|---|---:|---:|
| T-30 | 1889.3672272292858 | 1846.2792557036205 |
| T-14 | 1748.4970512511325 | 1870.393553818474 |

After the gate passes, the production runtime is fit once on all five completed seasons:

`2021/2022 .. 2025/2026`

Artifacts live under:

`ml/artifacts/structural_prior_runtime_v1/`

Expected files:

- `structural_prior_t30_v1.joblib`;
- `structural_prior_t14_v1.joblib`;
- `historical_runtime_v1.csv.gz`;
- `manifest.json`.

The manifest pins SHA-256, library versions, training seasons, feature contract and benchmark reproduction.

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

## Sporting PIT rule

The current sporting raw table presently stores `event_date` but not exact historical kickoff time.

To avoid same-day future leakage, v1 uses a deliberately conservative rule:

- only a completed fixture whose local `event_date` is **strictly before** the Structural Prior cutoff local date may enter state;
- same-day fixtures are excluded even if the source already marks them completed;
- for rest/congestion calculations, an included fixture uses local noon as a versioned representative timestamp.

This rule is recorded in each prior's `input_lineage` and should be replaced when exact historic kickoff timestamps are available.

## Capacity / domain safety

The model domain is canonical `Ekstraklasa`.

Known competition aliases are normalized explicitly, e.g.:

`PKO BP Ekstraklasa -> Ekstraklasa`

Capacity is not taken from the public seat-map size. It must come from the verified capacity registry with source/version lineage.

## Persistence

Writer RPC:

`public.insert_structural_prior_forecast_v1(jsonb)`

It validates:

- T-30/T-14 only;
- exact ticket event and kickoff;
- exact target cutoff;
- current model spec/family/feature contract;
- normalized validated competition;
- verified registry capacity;
- P50 inside `[0, capacity]`;
- idempotency on event + horizon + cutoff + model spec.

P10/P90 stay NULL until probabilistic calibration exists.

## Automation

Artifact build workflow:

`.github/workflows/structural-prior-artifacts.yml`

Scheduled materialization:

`.github/workflows/structural-prior-materializer.yml`

Materializer cadence:

`5,20,35,50 * * * *`

It intentionally runs shortly before the Live Forecast Orchestrator (`7,22,37,52`). After inserting a new prior it also invokes the orchestrator immediately.

## Security

Supabase Edge Function:

`supabase/functions/structural_prior_materializer_v1/index.ts`

GitHub OIDC audience:

`beyond-structural-prior-materializer`

Only `NiedzielX/beyond` on `refs/heads/main` is accepted. The service-role credential remains only inside the Supabase Edge Function environment.

## Current implementation gate

The first due-input verification identifies five ready T-14 events for automatic materialization:

- Pogoń Szczecin — Radomiak Radom;
- Wisła Kraków — Raków Częstochowa;
- Śląsk Wrocław — Wieczysta Kraków;
- Jagiellonia Białystok — Wisła Płock;
- Legia Warszawa — Lech Poznań.

After deployment, all five must resolve from `missing_prior` to `ready` before v1 is marked operationally complete.
