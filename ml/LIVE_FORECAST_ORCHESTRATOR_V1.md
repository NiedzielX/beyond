# Beyond — Live Forecast Orchestrator v1

Last verified: **2026-10-15 20:30 UTC**

## Status

**DONE / DEPLOYED / SHADOW**

The orchestrator automates the completed Phase-B stack. It does not retrain historical models and it does not apply a learned live correction.

## Runtime flow

Every scheduler invocation:

1. materializes due canonical `live-trajectory-v1.1` checkpoint evidence;
2. scans ticket events with kickoff in the next 31 days;
3. uses the latest snapshot at or before the run time as the PIT `as_of`;
4. resolves the genuine Structural Prior with `public.get_structural_prior_v1`;
5. fails closed when the prior is `not_due`, `missing_prior` or `out_of_domain`;
6. for a `ready` prior, calculates `live-trajectory-v1.1`;
7. calculates `trajectory-gap-v1` against the frozen same-horizon PIT reference pool;
8. persists/updates the append-only trajectory-gap observation keyed by event + source snapshot time;
9. persists the P50-only Structural Prior shadow revision with `live_adjustment = 0`;
10. existing first-detection and revision-audit contracts continue to work automatically.

## Scheduler

GitHub Actions workflow:

`.github/workflows/live-forecast-orchestrator.yml`

Cadence:

`7,22,37,52 * * * *` — every 15 minutes.

The automatic Structural Prior Materializer runs at `5,20,35,50` and invokes the orchestrator immediately after persisting new priors.

All five Structural Prior horizons are now executable: T-30 / T-14 / T-7 / T-3 / T-1.

The workflow uses GitHub OIDC. No Supabase service-role secret is stored in the workflow.

## Edge entrypoint

`supabase/functions/live_forecast_orchestrator_v1/index.ts`

Security:

- custom GitHub OIDC verification;
- issuer: `https://token.actions.githubusercontent.com`;
- audience: `beyond-live-forecast-orchestrator`;
- repository: `NiedzielX/beyond`;
- ref: `refs/heads/main`;
- privileged DB work stays inside the Edge Function environment.

## Database contract

Versioned SQL:

`supabase/sql/live_forecast_orchestrator_v1.sql`

Main RPC:

`public.run_live_forecast_orchestrator_v1(timestamptz)`

The RPC is `SECURITY INVOKER`.

Execution is revoked from `PUBLIC`, `anon` and `authenticated`, and granted only to `service_role`.

Run audit table:

`private.live_forecast_orchestrator_runs_v1`

## Idempotency

The orchestrator uses the latest source snapshot timestamp as the live `as_of`.

Re-running without a newer snapshot:

- reuses/upserts the same trajectory-gap observation key;
- `insert_demand_engine_shadow_forecast_v1` returns the existing revision for the same event + source snapshot + model version;
- does not create a fake forecast timestamp merely because the scheduler ran again.

## Latest production-shadow verification

Latest verified run:

`private.live_forecast_orchestrator_runs_v1.id = 18`

Result:

- active events: **12**;
- processed end-to-end: **12**;
- `missing_prior`: **0**;
- skipped/out-of-domain: **0**;
- event errors: **0**;
- canonical checkpoint rows materialized: **34**.

This verifies the key operational invariant: every currently active event has a genuine Structural Prior anchor and reaches the shadow pipeline successfully.

Current genuine prior set includes:

- one T-30 prior;
- five T-14 priors;
- one T-7 prior;
- five T-3 priors;
- no T-1 prior yet because the first current T-1 checkpoint is not naturally due until 2026-10-16 15:30 UTC.

T-1 runtime/registry/resolver/gateway are already deployed. A read-only future-time resolver check confirms current events move to `T-1 / missing_prior` with model `structural-prior-runtime-v1-t1-hist-full` at the exact kickoff-minus-one-day cutoff.

T-1 must not be materialized early because the stack is point-in-time by design.

No learned live correction is active; `live_adjustment = 0` remains enforced until the learned-correction evidence gate passes.

## Structural Prior dependencies

Canonical materializer doc:

`ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`

Current frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

All five horizon runtimes are registered and executable.

## Current operational bottleneck

Structural Prior coverage is no longer the bottleneck.

The current binding constraint is **prospective governance-eligible live evidence** for Phase C learned correction.

Current training-eligible evidence:

| Horizon | Eligible |
|---|---:|
| T-30 | 0 |
| T-14 | 3 |
| T-7 | 3 |
| T-3 | 4 |
| T-1 | 5 |

Promotion still requires the governance gate in `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`, including 20 independent completed matches, positive uplift, challenger MAE below incumbent, a frozen evidence package and human review.

## Next operational checkpoint

> **Verify the first naturally due T-1 materialization after 2026-10-16 15:30 UTC.**

After that, continue evidence collection and T-30 R&D in parallel. Do not invent or backfill future PIT evidence merely to exercise the pipeline.

## Plan position

- Phase A — Foundation: **DONE**
- Phase B — Shadow Forecasting contracts: **DONE**
- Live Forecast Orchestrator v1: **DONE / LIVE**
- Automatic Structural Prior materialization all five horizons: **DONE / LIVE**
- First naturally due T-1 forecast: **NEXT operational checkpoint**
- Phase C learned live correction: **BLOCKED ON EVIDENCE**
