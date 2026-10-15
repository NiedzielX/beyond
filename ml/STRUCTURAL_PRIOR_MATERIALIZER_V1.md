# Beyond — Structural Prior Materializer v1

Last verified: **2026-10-15**

## Status

**DONE / DEPLOYED / LIVE for T-30 and T-14**

The materializer automatically creates genuine point-in-time Structural Prior P50 forecasts for current Ekstraklasa events without retraining the historical model on scheduler runs.

## Scope

v1 supports only the horizons with a frozen executable current-event runtime:

- **T-30** — `structural-prior-runtime-v1-t30-extra-full`;
- **T-14** — `structural-prior-runtime-v1-t14-hist-base`.

T-7 / T-3 / T-1 remain fail-closed until their own executable current-event runtimes are frozen. There is no fallback to legacy Lech models.

## Architecture

One-time build:

`exact canonical 1,530-match DB export -> five-season PIT feature store -> approved benchmark reproduction gate -> final fit on five completed seasons -> frozen joblib artifacts + SHA manifest`

Scheduled runtime:

`due T-30/T-14 event -> canonical PIT inputs -> frozen artifact load -> current-event PIT row -> predict P50 -> validated DB insert -> Live Forecast Orchestrator`

**The scheduled runtime contains no `fit()` path.**

## Frozen artifact gate — PASSED

The freeze completed successfully on 2026-10-15 after reproducing the approved untouched holdouts exactly:

| Horizon | 2024/25 MAE | 2025/26 MAE |
|---|---:|---:|
| T-30 | 1889.3672272292858 | 1846.2792557036205 |
| T-14 | 1748.4970512511325 | 1870.393553818474 |

Production runtimes were then fit once on all five completed seasons:

`2021/2022 .. 2025/2026`

Frozen artifact version:

`structural-prior-runtime-v1-frozen-2026-10-15`

Artifacts under `ml/artifacts/structural_prior_runtime_v1/`:

- T-30 `structural_prior_t30_v1.joblib`
  - SHA-256 `33e32a8b2f0c617c5adde5cdba592151bb25651ef00fc60aa2e5c090adb51da7`;
- T-14 `structural_prior_t14_v1.joblib`
  - SHA-256 `8d2dbb6ce48ae48fe2e5b7f4340c9e2dfadd38c6e23cc7b123c6f1d2303cdc20`;
- `historical_runtime_v1.csv.gz`
  - SHA-256 `345bbf72c702fc4356b2ccfe998b5c3c121adea5fef32d34bb9daa9aae10b89d`;
- `manifest.json`.

Freeze commit:

`4a8f066742faa24508b733175f7366b4ccaabe2e`

## Reproducibility rule discovered during freeze

Historical training data must preserve the **pinned source keys exactly**.

The first freeze attempt exposed that `public.export_historical_runtime_v1()` had normalized historical `radomiak -> radomiak_radom`. The pinned 2025/26 dataset uses `radomiak` on the away side and `radomiak_radom` on the home side. Applying a current-event alias to historical rows changed PIT history and changed the holdout result.

The export was corrected so:

- historical training bytes/semantics remain frozen;
- current-event aliases are applied only in the inference adapter;
- approved benchmark values remain the gate and were **not** changed to accept a different result.

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

Known competition alias:

`PKO BP Ekstraklasa -> Ekstraklasa`

Capacity is never substituted with public seat-map size.

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

- T-30/T-14 only;
- exact ticket event and kickoff;
- exact target cutoff;
- current model spec/family/feature contract;
- normalized validated competition;
- verified registry capacity;
- P50 inside `[0, capacity]`;
- idempotency on event + horizon + cutoff + model spec.

The writer is `SECURITY INVOKER`; `service_role` has the minimal model-spec read permission required to validate lineage. Versioned permission fix:

`supabase/sql/structural_prior_materializer_permissions_v1.sql`

P10/P90 remain NULL until probabilistic calibration exists.

## Automation

Artifact build:

`.github/workflows/structural-prior-artifacts.yml`

Scheduled materialization:

`.github/workflows/structural-prior-materializer.yml`

Cadence:

`5,20,35,50 * * * *`

It runs shortly before Live Forecast Orchestrator (`7,22,37,52`). After persisting new priors it invokes the orchestrator immediately.

Supabase Edge Function:

`supabase/functions/structural_prior_materializer_v1/index.ts`

Auth:

- GitHub OIDC audience `beyond-structural-prior-materializer`;
- repository `NiedzielX/beyond`;
- ref `refs/heads/main`;
- service-role credential remains only inside Supabase Edge Function environment.

## First automatic production-style materialization — PASSED

Five due T-14 priors were scored from the frozen artifact and persisted successfully:

| Prior ID | Event | P50 | Capacity | Expected occupancy |
|---:|---|---:|---:|---:|
| 2 | Pogoń Szczecin — Radomiak Radom | 16,226.996 | 21,163 | 76.68% |
| 3 | Wisła Kraków — Raków Częstochowa | 17,350.596 | 33,130 | 52.37% |
| 4 | Śląsk Wrocław — Wieczysta Kraków | 19,552.562 | 43,708 | 44.73% |
| 5 | Jagiellonia Białystok — Wisła Płock | 15,635.204 | 22,372 | 69.89% |
| 6 | Legia Warszawa — Lech Poznań | 29,635.741 | 31,006 | 95.58% |

All five use frozen T-14 artifact SHA:

`8d2dbb6ce48ae48fe2e5b7f4340c9e2dfadd38c6e23cc7b123c6f1d2303cdc20`

Immediately afterward Live Forecast Orchestrator run `id=3` completed with:

- active events: **13**;
- processed end-to-end: **6**;
- remaining `missing_prior`: **6**;
- event errors: **0**;
- canonical checkpoints materialized: **34**.

The remaining six `missing_prior` rows are T-7/T-3 events and are therefore expected under v1 scope.

## Plan position

- Phase A — Foundation: **DONE**
- Phase B — Shadow Forecasting: **DONE**
- Live Forecast Orchestrator v1: **DONE / LIVE**
- Automatic Structural Prior Materializer T-30/T-14: **DONE / LIVE**
- Executable current-event Structural Prior runtimes T-7/T-3/T-1: **NEXT**
- Phase C learned live correction: **BLOCKED ON EVIDENCE**
