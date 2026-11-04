# Daily inventory path — deployment and recovery boundary

Updated **2026-11-04**. Existing attendance lanes remain frozen; production_change=false and live_adjustment=0.

## Verified now

- Local/cloud daily-path inference, immutable forecast vintages, later-target scorer, event-balanced metrics, private Storage backup and byte/hash-verified restore.
- Research bucket `beyond-daily-path-research-v1` is private; anonymous public-object access was denied. No service-role key is in the frontend, GitHub workflow, backup manifests or command arguments.
- The host-dependent watcher runs every900seconds, stops after3consecutive failed cycles, and is bounded through **2026-11-04T17:15:00Z**. It is model inference/scoring, not an always-on AI coding session. It can stop if the cloud machine/session is replaced.
- Current runtime: `/workspace/ops-runtime/2026-11-03-daily-path/`. `latest-cycle.json` records actual results; `watcher.pid` identifies the process started by this task. Do not start a second watcher blindly.

## Prepared, not deployed or fully runtime-validated

| Artifact | Status / scope |
|---|---|
| `supabase/sql/daily_inventory_path_shadow_v1.sql` | Migration prepared; actual isolated PostgreSQL16contract tests passed in run41811081476. Not applied to the project database. New private model registry, attempts, future-day points, immutable scores; controlled capture/score/feed RPCs, service_role only. It reads public source rows but does not mutate existing attendance evidence. |
| `supabase/functions/daily_inventory_path_gateway_v1/index.ts` | Source prepared; actual Deno typecheck, scoped-policy/key-transport tests and isolated real-entry-point405/401checks passed in run41811081476. No deployed request or valid live signed OIDC chain is claimed. Requires explicit GitHub OIDC validation for this repository, main ref, exact workflow_ref and audience. |
| `ml/run_daily_inventory_path_gateway_v1.py` | OIDC-only scheduled runner. No service-role secret in GitHub. New legal attempts are validated by the pinned Python model/ledger before publication; SQL independently checks source identity and cutoff. Unacknowledged writes are retried only inside their original legal window. |
| `.github/workflows/daily-inventory-path-shadow-v1.yml` | YAML parsed. Job is gated by repository variable `DAILY_INVENTORY_PATH_ENABLED == 'true'`; published to a draft PR branch, not merged to main, enabled or executed. A checked-in file is not scheduled execution. |
| Panel | Parser/geometry tests pass, actual exported payload validated. Full React typecheck and production build passed in GitHub Actions (run41709931291); local dependency installation remains blocked by npm registry HTTP403. Vercel preview deployed; no browser interaction/E2E validation claimed. |

The migration deliberately does not reimplement model coefficients in SQL. The trusted, pinned Python inference path rechecks outputs before the exact workflow's OIDC identity publishes them. DB enforces event/source lineage, frozen model identity, daily coordinates, +90minute windows, complete leads, unique immutable retries and genuine later targets. Validate all of these on an isolated PostgreSQL/Supabase test target before enabling the new workflow. Do not assume a syntax-only source check validates SQL security or Deno runtime semantics.

## Required environment changes already saved as a draft

Preserving prior destinations, the environment draft adds `registry.npmjs.org` and `api.supabase.com`, plus the missing `SUPABASE_ACCESS_TOKEN` requirement restricted to the management API. Its value belongs in environment settings, never in chat. Existing Supabase service-role and GitHub bindings continue to work.

The tool returned `status=saved`, `requires_publish=true`. Draft persistence does not apply the network change, inject a missing credential, publish an environment or verify access. No administrative management token or DB connection is currently bound. The service-role data key is insufficient for schema migrations or Edge Function deployment.

After the settings become effective:

1. Restore local panel dependency access for interactive development. Hosted GitHub Actions already passed real typecheck/build after a parser literal-type fix; preserve those checks.
2. Apply the already isolated-tested SQL migration with project migration privileges, preserving the transaction and no old-table mutation boundary. Check that anon/authenticated have no execute or direct private-table access.
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

## Source checkpoints and latest evidence

Backend draft PR: https://github.com/NiedzielX/beyond/pull/205. Panel draft PR: https://github.com/NiedzielX/BeyondTicketingPanel/pull/8. No merge or production activation was performed. Backend Demand Engine Smoke passed in Actions run41709480252; panel TypeScript and production build passed in run41709931291.

At2026-11-03T20:01:46Z the watcher added Jagiellonia's daily issue: the local stream contains7attempts,4events with predictions,57future-day points,0scores. The verified training manifest contains lead times through28days; longer outputs are explicitly marked as extrapolation, without changing weights or predictions. The served JSON includes model-bound support metadata and genuine-score overlays when outcomes mature.

## 2026-11-04 validation and host recovery

Canonical validation/recovery note:`DAILY_PATH_CLOUD_VALIDATION_2026-11-04.md`. Actual cloud tests cover the migration, synthetic DB→pinned panel parser, Deno types/policy and real local denial paths. The original foreground worker stopped afterNov3 20:54; a detached bounded replacement passedNov4 09:44and09:59cycles with verified backup. Use the reusable launcher/status CLI, not a historical exec-session ID. This remains host-dependent.

The existing frozen encoder main workflow passed a manual health check in run41811629783at10:03UTC, while no checkpoint was open. A separate legal-window guardian is collecting operational state for today's genuine cutoffs. Neither this no-due success nor isolated tests prove the still-pending due-window DB chain. No P9heartbeat DONE claim follows.
