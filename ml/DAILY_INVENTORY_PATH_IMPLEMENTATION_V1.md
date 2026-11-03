# Daily inventory path v1 — implementation and evidence

Updated: **2026-11-03, 17:01 UTC**. Precommit: [DAILY_INVENTORY_PATH_PRECOMMIT_V1.md](DAILY_INVENTORY_PATH_PRECOMMIT_V1.md).

Later update, **2026-11-03 19:46 UTC**: the lane has6immutable local attempts /21future points /0scores, including Widzew's19:15cutoff. Verified private Supabase Storage backups and full ledger restore now preserve the evidence independently of the local disk. A bounded host-dependent inference/scoring watcher is active; migration/gateway/scheduled GitHub workflow source is prepared but not deployed. See [deployment/recovery status](DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md) for the current distinction and external requirements. Earlier17:00figures below describe the first capture, not current totals.

## Delivered

- PIT-safe full-prefix dataset and matched future-day inventory labels: `demand_engine/daily_inventory_path_dataset_v1.py`.
- One frozen direct median model with prefix/lead interactions, persistence baseline and event-balanced metrics: `demand_engine/daily_inventory_path_model_v1.py`.
- Immutable local SQLite attempts, forecast vintages, exact artifact/output validation and later observation scoring: `demand_engine/daily_inventory_path_ledger_v1.py`.
- Executable read-only export / audit / fit / preview / shadow / score / export-ledger CLI: `run_daily_inventory_path_v1.py`.
- New frozen artifact: [`artifacts/daily_inventory_path_v1.json`](artifacts/daily_inventory_path_v1.json). Model identity SHA256 `1137e257494583374f768622feca343f2dd7d634ef2446198703f8c27fbd9525`.
- In the separate `BeyondTicketingPanel` checkout: real-time/P-N daily-path chart, original-vintage selector, strict feed parser and observed versus predicted availability. The decorative straight connector to final attendance was removed. Attendance forecast history remains separate.

Existing frozen attendance/SSP artifacts and prospective workflows were not modified. Production remains OFF. New CLI/ledger is research tooling, not a deployed Supabase feature.

## Actual public-data run

Initial read-only export: **38 events / 25,731 snapshots**. Dataset: 218 READY issue cutoffs, 1,429 matched daily targets from 20 events / 14 clubs. These are inventory labels, not attendance labels; multiple targets are not independent matches. There were also 52 missing matured labels and 816 pending targets among READY issues. Coverage is conditional on input eligibility; 2,184 total historical issue cutoffs include many unavailable prefixes.

The final research fit used **1,239 labeled rows / 16 completed events**, with training cutoff `2026-11-03T00:00:00Z`. Actual fit completion/freeze: `2026-11-03T16:37:09.890554Z`.

The fixed chronological 70/30 diagnostic had only **four** training events with labels available by its first test issue (`2026-10-02T16:30Z`). Status is `INSUFFICIENT_DIAGNOSTIC_EVIDENCE`. No diagnostic MAE improvement is claimed, and the split/minimum support were not relaxed. Existing 550-seat attendance criteria do not apply to this new inventory-path target.

## First local post-freeze prospective capture

At **2026-11-03 17:00:13 UTC / 18:00:13 Europe/Warsaw**, the CLI read a fresh export and captured the 17:00 UTC daily cutoff:

| Event | Original prefix observations | Future daily predictions | First target |
|---|---:|---:|---|
| 5091 Motor Lublin–Wisła Płock | 152 | 2 | 2026-11-04 17:00 UTC |
| 10500 Piast Gliwice | 215 | 16 | 2026-11-04 17:00 UTC |

The artifact was frozen before issue time; target events were excluded from fitting. Only source observations captured by the issue cutoff were used. A retry at 17:00:33 preserved both original attempts (`inserted=false`) and their first execution timestamp. Scores: **0**, with all 18 targets not due yet. No historical predictions were backfilled.

The original ledger rows were exported to `BeyondTicketingPanel/public/research/daily-inventory-path-v1.json`. Its real payload passed the panel parser and plot geometry: two vintages with 18 actual model output points. This verifies the local cutoff → inference → immutable local ledger → valid panel-feed chain. It does **not** verify deployed UI rendering, Supabase persistence, a daily scheduler, or forecast accuracy against future observations.

Source-state limitation: public snapshots lack active/visible metadata; provider/source identity does not prove a constant released pool or net sales. Source changes fail closed. Missing data remain missing; literal observed zeros are not converted to unknown merely to make the old attendance lane pass.

## Reproduce / continue in cloud

From repo root, with existing cloud environment bindings (never put keys in command arguments):

```bash
python -m ml.run_daily_inventory_path_v1 export --output /tmp/daily-path-export.json
python -m ml.run_daily_inventory_path_v1 shadow --input /tmp/daily-path-export.json --artifact ml/artifacts/daily_inventory_path_v1.json --ledger /workspace/ops-runtime/2026-11-03-daily-path/shadow-v1.sqlite
python -m ml.run_daily_inventory_path_v1 score --input /tmp/daily-path-export.json --ledger /workspace/ops-runtime/2026-11-03-daily-path/shadow-v1.sqlite --output /tmp/daily-path-score-status.json
python -m ml.run_daily_inventory_path_v1 export-ledger --ledger /workspace/ops-runtime/2026-11-03-daily-path/shadow-v1.sqlite --output /workspace/BeyondTicketingPanel/public/research/daily-inventory-path-v1.json
```

Use a new export filename for each read: exports/artifacts are not overwritten. `shadow` uses real wall-clock time and only records issues inside cutoff…+90 minutes with a model frozen before cutoff. It does not retrospectively fill missing windows. Do not rerun `fit` on this artifact to refresh inference.

Current runtime files are under `/workspace/ops-runtime/2026-11-03-daily-path/`: source exports, coverage, research report, model copy, immutable `shadow-v1.sqlite`, score status and initial preview. The generated panel feed is ignored by Git; the small new frozen model artifact is included in the source changes. Protect/copy the local ledger before replacing this cloud workspace.

## Validation and remaining work

- Python Demand Engine discovery: **174 tests passed**; CLI/lifecycle tests: **25 passed**.
- Panel feed/geometry native Node tests: **17 passed**, including actual timestamp spacing, gaps, zero handling, input/target leakage, cross-event contamination and complete future leads.
- Both repositories pass `git diff --check`.
- Full panel `lint` / `build` remain blocked: no installed `tsc` / `vite`; dependency install returned HTTP403 from npm registry. No deployed browser/UI validation is claimed.
- Existing smoke CI now includes the new CLI/lifecycle tests; this is configuration, not evidence of an executed GitHub run.

Next: apply the saved environment requirements, validate/deploy the prepared research SQL/gateway and verify the gated GitHub workflow before enabling it. Panel dependency access and full typecheck/build remain blocked. At/after **2026-11-04 17:00 UTC**, fetch fresh public snapshots and score the first genuine targets without changing the model. Preserve all older daily vintages. A bounded local/cloud model watcher is active, but no always-on coding daemon or new production scheduler was started. Private Storage recovery is verified; new SQL tables are not deployed.
