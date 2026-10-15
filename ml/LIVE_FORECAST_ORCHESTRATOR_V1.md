# Beyond — Live Forecast Orchestrator v1

Last verified: **2026-10-15**

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
9. persists the P50-only Structural Prior shadow revision with live adjustment = 0;
10. existing first-detection and revision-audit contracts continue to work automatically.

## Scheduler

GitHub Actions workflow:

`.github/workflows/live-forecast-orchestrator.yml`

Cadence:

`7,22,37,52 * * * *` — every 15 minutes.

The automatic Structural Prior Materializer runs shortly before it at `5,20,35,50` and invokes the orchestrator immediately after persisting new T-30/T-14 priors.

The workflow uses GitHub OIDC. No Supabase service-role secret is stored in the workflow.

## Edge entrypoint

`supabase/functions/live_forecast_orchestrator_v1/index.ts`

Security:

- custom GitHub OIDC verification;
- accepted issuer: `https://token.actions.githubusercontent.com`;
- accepted audience: `beyond-live-forecast-orchestrator`;
- accepted repository: `NiedzielX/beyond`;
- accepted ref: `refs/heads/main`;
- privileged DB work stays inside the Edge Function environment.

## Database contract

Versioned SQL:

`supabase/sql/live_forecast_orchestrator_v1.sql`

Main RPC:

`public.run_live_forecast_orchestrator_v1(timestamptz)`

The RPC is `SECURITY INVOKER`, not `SECURITY DEFINER`.

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

After automatic T-14 Structural Prior materialization, orchestrator run `private.live_forecast_orchestrator_runs_v1.id = 3` completed successfully:

- active events: **13**;
- processed end-to-end: **6**;
- remaining `missing_prior`: **6**;
- skipped/out-of-domain: **1**;
- event errors: **0**;
- canonical checkpoint rows materialized: **34**.

Processed with genuine priors:

| Event ID | Structural Prior | P50 | Shadow observation |
|---:|---:|---:|---:|
| 10 | 2 | 16,227 | 1211 |
| 16 | 3 | 17,351 | 1212 |
| 23 | 4 | 19,553 | 1213 |
| 21 | 5 | 15,635 | 1214 |
| 22 | 6 | 29,636 | 1215 |
| 6 | 1 | 31,832 | 1216 |

Current trajectory results remain shadow/descriptive. At that run:

- events 10, 23, 21, 22 and 6: `INSUFFICIENT_SIGNAL / outside_reference_checkpoint_window`;
- event 16: `INSUFFICIENT_SIGNAL / live_signal_partial`.

No live correction was applied; `live_adjustment = 0` remains the enforced behavior until the learned correction evidence gate passes.

## Current operational bottleneck

Automatic T-30/T-14 Structural Prior materialization is no longer a blocker.

The six remaining `missing_prior` events are at **T-7/T-3**. The current resolver already knows the approved historical specs, but those horizons do not yet have a frozen executable current-event runtime/materializer contract.

Next development target:

> **Freeze and deploy executable current-event Structural Prior runtimes for T-7 / T-3 / T-1.**

This is needed so the live loop keeps a genuine historical anchor after a tracked event leaves the T-14 window. Until then later horizons intentionally remain fail-closed; no legacy fallback is allowed.

## Plan position

- Phase A — Foundation: **DONE**
- Phase B — Shadow Forecasting contracts: **DONE**
- Live Forecast Orchestrator v1: **DONE / LIVE**
- Automatic Structural Prior materialization T-30/T-14: **DONE / LIVE**
- Executable T-7/T-3/T-1 current-event runtimes: **NEXT**
- Phase C learned live correction: **BLOCKED ON EVIDENCE**
