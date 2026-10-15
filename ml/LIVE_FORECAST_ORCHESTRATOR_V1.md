# Beyond — Live Forecast Orchestrator v1

Last verified: **2026-10-15**

## Status

**DEPLOYED / SHADOW**

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

`7,22,37,52 * * * *` — every 15 minutes, deliberately offset from the media-attention collector.

The workflow uses GitHub OIDC. No Supabase service-role secret is stored in the workflow.

## Edge entrypoint

`supabase/functions/live_forecast_orchestrator_v1/index.ts`

Security:

- custom GitHub OIDC verification;
- accepted issuer: `https://token.actions.githubusercontent.com`;
- accepted audience: `beyond-live-forecast-orchestrator`;
- accepted repository: `NiedzielX/beyond`;
- accepted ref: `refs/heads/main`;
- Edge Function platform JWT verification is disabled only because the function performs this explicit external OIDC verification;
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

Re-running the scheduler without a newer snapshot:

- reuses/upserts the same trajectory-gap observation key;
- `insert_demand_engine_shadow_forecast_v1` returns the existing forecast revision for the same event + source snapshot + model version;
- does not create a fake new forecast timestamp merely because the scheduler ran again.

## First production-shadow verification

Direct DB verification on 2026-10-15 returned:

- active events: **13**;
- processed end-to-end: **1**;
- missing Structural Prior: **9**;
- out of current model domain: **3**;
- event errors: **0**;
- canonical checkpoint rows materialized in that run: **33**.

Processed event:

**Lech Poznań vs Wisła Kraków — event 6**

- Structural Prior P50: **31,832**;
- new orchestrated shadow revision: `forecast_observations.id = 1209`;
- trajectory status: `INSUFFICIENT_SIGNAL`;
- reason: `outside_reference_checkpoint_window`;
- this is correct fail-closed behaviour before the frozen T-14 window.

## Newly exposed bottleneck

The live loop itself is no longer the main blocker.

The first run showed **9 Ekstraklasa events with `missing_prior`**. That means the next development target is:

> **Automatic Structural Prior Materializer / Scheduler**

It must generate genuine T-30/T-14 current-event priors from the frozen runtime specs without retraining/reproducing the historical benchmark on every run.

Until that exists, Live Forecast Orchestrator v1 processes every event that already has a genuine ready prior and explicitly records `missing_prior` for the others. It never falls back to legacy Lech models.

## Plan position

- Phase A — Foundation: **DONE**
- Phase B — Shadow Forecasting contracts: **DONE**
- Operational automation — Live Forecast Orchestrator v1: **DONE / DEPLOYED**
- Automatic Structural Prior materialization across current events: **NEXT**
- Phase C learned live correction: **BLOCKED ON EVIDENCE**
