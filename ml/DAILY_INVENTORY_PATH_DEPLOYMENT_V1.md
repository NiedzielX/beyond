# Daily inventory path — deployment and recovery boundary

Updated **2026-11-03**. Existing attendance lanes remain frozen; production_change=false and live_adjustment=0.

## Verified now

- Local/cloud daily-path inference, immutable forecast vintages, later-target scorer, event-balanced metrics, private Storage backup and byte/hash-verified restore.
- Research bucket `beyond-daily-path-research-v1` is private; anonymous public-object access was denied. No service-role key is in the frontend, GitHub workflow, backup manifests or command arguments.
- The host-dependent watcher runs every900seconds, stops after3consecutive failed cycles, and is bounded through **2026-11-04T17:15:00Z**. It is model inference/scoring, not an always-on AI coding session. It can stop if the cloud machine/session is replaced.
- Current runtime: `/workspace/ops-runtime/2026-11-03-daily-path/`. `latest-cycle.json` records actual results; `watcher.pid` identifies the process started by this task. Do not start a second watcher blindly.

## Prepared, not deployed or fully runtime-validated

| Artifact | Status / scope |
|---|---|
| `supabase/sql/daily_inventory_path_shadow_v1.sql` | Migration prepared. Not applied or tested against PostgreSQL. New private model registry, attempts, future-day points, immutable scores; controlled capture/score/feed RPCs, service_role only. It reads public source rows but does not mutate existing attendance evidence. |
| `supabase/functions/daily_inventory_path_gateway_v1/index.ts` | Source prepared; Node TypeScript syntax check passed, not a Deno typecheck or deployed request. Requires explicit GitHub OIDC validation for this repository, main ref, exact workflow_ref and audience. |
| `ml/run_daily_inventory_path_gateway_v1.py` | OIDC-only scheduled runner. No service-role secret in GitHub. New legal attempts are validated by the pinned Python model/ledger before publication; SQL independently checks source identity and cutoff. Unacknowledged writes are retried only inside their original legal window. |
| `.github/workflows/daily-inventory-path-shadow-v1.yml` | YAML parsed. Job is gated by repository variable `DAILY_INVENTORY_PATH_ENABLED == 'true'`; not enabled, pushed or executed in this work. A checked-in file is not scheduled execution. |
| Panel | Parser/geometry tests pass, actual exported payload validated. Full React lint/build blocked by missing dependencies and npm registry HTTP403; no deployed browser validation claimed. |

The migration deliberately does not reimplement model coefficients in SQL. The trusted, pinned Python inference path rechecks outputs before the exact workflow's OIDC identity publishes them. DB enforces event/source lineage, frozen model identity, daily coordinates, +90minute windows, complete leads, unique immutable retries and genuine later targets. Validate all of these on an isolated PostgreSQL/Supabase test target before enabling the new workflow. Do not assume a syntax-only source check validates SQL security or Deno runtime semantics.

## Required environment changes already saved as a draft

Preserving prior destinations, the environment draft adds `registry.npmjs.org` and `api.supabase.com`, plus the missing `SUPABASE_ACCESS_TOKEN` requirement restricted to the management API. Its value belongs in environment settings, never in chat. Existing Supabase service-role and GitHub bindings continue to work.

The tool returned `status=saved`, `requires_publish=true`. Draft persistence does not apply the network change, inject a missing credential, publish an environment or verify access. No administrative management token or DB connection is currently bound. The service-role data key is insufficient for schema migrations or Edge Function deployment.

After the settings become effective:

1. Install panel dependencies without changing declarations/lockfiles; run its real typecheck/build and correct actual failures.
2. Validate/apply the new SQL migration with project migration privileges, preserving the transaction and no old-table mutation boundary. Check that anon/authenticated have no execute or direct private-table access.
3. Deploy only the new `daily_inventory_path_gateway_v1`. Disable the platform's legacy JWT verification for this function so its own scoped GitHub OIDC verification can run; do not disable the code's issuer/audience/repository/ref/workflow checks.
4. Keep the repository enable variable unset until deployment and authorization denial tests pass. Review the concrete changes before merging/publishing; no production attendance activation is part of this work.
5. After enabling the new shadow job, verify a full legal chain: actual workflow run → actual gateway request → successful controlled DB RPC → expected immutable points → DB feed → later genuine observations and scores. A successful no-target run does not prove this chain.

Remote DB retries do not import expired local records. Existing local17:00/19:15vintages remain independently recoverable from private Storage; retain their original evidence identity and execution times.

## Recovery after a cloud restart

With the existing service-role binding and repository code/artifact available, restore the latest content-addressed private manifest into a **new** ledger path:

```bash
python -m ml.run_daily_inventory_path_v1 restore --manifest-key latest --ledger /workspace/ops-runtime/daily-path-restored/shadow-v1.sqlite
python -m ml.run_daily_inventory_path_cycle_v1 --runtime /workspace/ops-runtime/daily-path-restored --panel-feed /workspace/BeyondTicketingPanel/public/research/daily-inventory-path-v1.json
```

Restore rejects bad hashes, unexpected schema and overwriting existing ledgers. Publication/restart can kill live watchers; backup data and running processes are separate guarantees. Inspect the restored ledger and current runtime before starting a single new bounded watcher. Never refit v1 just to restart inference, and never fill a missed daily issue from later source data.

## Metrics and UI interpretation

`ledger_metrics` and cycle summaries calculate paired event-balanced MAE/bias and per-lead results from immutable scores. Pending targets remain separate from matured-but-unscored targets. Empty scores produce null MAE, never zero. There is no new promotion gate implied by a descriptive readout.

The panel can overlay later genuine target observations on the unchanged issued path and report the selected vintage's error. Those later observations are not appended to that vintage's input prefix. Whole-model event-balanced MAE and one-event/vintage errors remain different views; attendance MAE and its550-seat threshold stay separate from inventory-path errors.
