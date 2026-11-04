# PostgreSQL contract validation and cloud continuation

Continuation authorized by the user. Canonical MAE order and frozen flags remain unchanged.

## Operational check09:43UTC /10:43Europe-Warsaw

- Actual RPC: no open due encoder checkpoints; nextKorona603P-3at11:15UTC, currently insufficient input. Next readyGórnik449P-3at16:30UTC. P9v1counts6/0/0;P9v2 5/3/0;frozen encoder8/5/0.
- Daily path still57future points /0scores; first target not mature until17:00UTC. Old watcher PID was gone; last successful cycle2026-11-03T20:54:53Z. No historical issue was backfilled.
- Started one detached bounded subprocess, log/runtime under `/workspace/ops-runtime/2026-11-03-daily-path/`, deadline2026-11-05T09:30Z. It remains host-dependent and is an inference worker, not an autonomous coding service. Verify new cycle/backup before claiming execution.
- MAE-03 hosted checks passed in runs41715153450and41715203331; no context model fit.

## Current implementation

Prepared a disposable PostgreSQL16GitHub Actions service to execute the real daily-path migration with synthetic contracts: capture/retries, timing/lineage/flags, atomicity, private permissions, immutable updates/deletes, genuine zero target matching and idempotent scoring. Test code refuses any target other than localhost database`daily_path_contract`. No production credentials or actual prospective rows are used.

Next:publish source, inspect actual cloud SQL test results, correct defects and reverify. Isolated test success remains distinct from deploying the SQL/Edge gateway to Supabase. Production remains off; admin deployment binding is still absent.

Update:isolated SQL/Deno/browser checks are now green; see verified progress below. No project SQL/Edge deployment was performed.

## Verified progress

- Detached worker completed09:44:27UTCcycle with57pending points and byte-verified private backup. Reusable bounded launcher/status tool added;6local lifecycle tests pass. It distinguishes live PID, launch-only and recent verified cycle; no duplicate was started.
- Actual PostgreSQL16run41810511980passed9contract tests and the companion panel parser accepted both DB-produced ready and zero-scored feeds. Initial failure was a test's identity-column assertion, corrected to check ordinary fields; migration source remained unchanged.
- Prepared gateway now handles opaque Supabase keys consistently with Python and requires signed token lifetime claims/RS256before its exact workflow policy. Six policy/header tests pass under Node; real Deno typecheck/tests are being added to cloud CI. No deployment was performed.
- Local Python checks:260tests pass(189engine +71CLI/research/worker). Frozen artifacts and experiment contracts remain unchanged.

## Further verified progress

Run41811081476passed real Deno typecheck,6policy/header tests and real-entry-point405/401HTTPtests with no inherited credentials, alongside9PostgreSQLcontracts and typed DB feeds. Run41811081596passed260Pythonchecks. PR209now contains the isolated validation and detached inference hardening.

Later hosted Demand Engine run41811862372passed269checks including the9guardian tests. Main health run41811629783succeeded; due-window DB-chain proof is still pending, not replaced by this no-due success.

Panel draft PR8now includes a real Chromium harness. Latest source1a6dd609473bfdbb3730d98ccfb8cb1e24e18f09passed browser run41812968199and TypeScript/build41812968190. It covers full future-day rendering, vintages, zero outcomes, error/empty states, refresh, keyboard and mobile layout. Source-zero-only history gets an explicit no-confirmed-sales/sellout note. Tests use synthetic fixtures only; no fake served feed or production data added.

The deployed Stellis collector was read with`mode=audit`only. Current Korona source explicitly hides counts(active stage but show-availability false), Widzew explicitly exposes literal0, Motor/Piast expose active counters. No DB source rows were written and no current flag was backfilled into history. Private response+hash saved beside the review PDF. This independently corroborates Korona's imminent input blocker.

Reviewed actual4-event/57-point paths and wrote a private PDF/PNG+hash provenance under `/workspace/ops-runtime/2026-11-04-review/`. Near-flat Piast/Jagiellonia prefixes can produce strong declines and Widzew has a zero-only source history. Recorded these limitations before targets mature in `DAILY_PATH_INITIAL_OUTPUT_REVIEW_2026-11-04.md`; did not tune or overwrite v1. Persistence remains the already-issued control.

Observed frozen-encoder scheduling gap:latest scheduled success03:22UTCdespite twice-hourly YAML. Manual main health run41811629783passed at10:03UTCwith no due checkpoint. Started one detached legal-window guardian under `/workspace/ops-runtime/2026-11-04-frozen-window-guardian/`,300second polling, deadlineNov5 09:30UTC. Nine local tests pass; first live cycle correctly found no due checkpoint and did not dispatch. Future due-window run/DB proof remains pending, not DONE. No P9heartbeat claim.

## New information without partner transactions

Prepared a separate read-only source-state-as-known v2RPC over existing Stellis raw observations. It requires event existence and source capture/receipt by cutoff, masks later promotion links, preserves genuine visible0and separates hidden/inactive/invalid states. It never modifies frozen v1inputs, source rows or forecasts. Eleven new PostgreSQL tests passed alongside the9existing persistence contracts in run41814622537.

A fixed seven-field feature adapter now independently validates timestamps/flags/counts and emits explicit null/missing masks with hourly48-hour source-state summaries. Twelve local tests pass; actual SQL→feature-row validation is being added to the hosted contract. No learner was fitted and project RPC deployment still needs admin binding. Both frontend agent instruction files now point to canonical backend plans and shared `.ai`records, avoiding a second strategy/memory copy.

## Prefix diagnostics and feature integration correction

Before first daily targets matured, added a separate read-only prefix-regime diagnostic: zero-only, constant-positive and varying observed histories, plus failed-input coverage. It retains the original full-cohort evaluator and equal-event denominator; contributions reconcile to primary MAE even when one event spans multiple regimes/vintages. Eight local tests passed. Actual10:44UTCledger review returned57predictions /0scored events and null MAE; no zero-error claim. The SQLite source was not changed.

Hosted source-feature integration failed after the20SQLtests passed because importing the existing demand_engine package requires NumPy; the isolated job installed only psycopg. Reproduced the missing dependency using Python without site packages and confirmed NumPy alone resolves the import. Added the existing pinned NumPy dependency and safe Checks annotations for this synthetic integration step. Thirteen feature tests and eight diagnostic tests pass locally; new hosted proof pending. No SQL/forecast/model semantics changed.

## Integration proof and exact mechanism finding

Hosted run41816696989now passed the entire sourceSQL→features and original persistence→panel/Deno chain(20SQL+13adaptercases); Demand Engine41816697000passed the prefix diagnostics and existing reproductions. Project deployment remains blocked.

Added a read-only exact coefficient audit with6focused local tests. All57issued points reconstruct within9.10e-13places. All120relative-value-history coefficients are0; nine remaining nonzero coefficients are negative global/count/mask terms. Latest and prefix maximum still enter anchor/scale. Documented this before future targets matured, with no fit, issued-point overwrite or claim of measured error. This gives the next separate daily-path experiment a concrete mechanism question:can a genuine-prefix-change comparator beat persistence? Private full audit retained alongside the review PDF.

## Separate genuine-delta baseline implementation

Precommitted`DAILY_INVENTORY_DRIFT_COMPARATOR_PRECOMMIT_V1.md`before implementation/outcomes. One fixed24-hour genuine-anchor velocity rule,6-hour anchor tolerance, actual elapsed time and zero-only clipping; no fit, lookback grid, damping orv1retuning. Separate ledger refuses opening an existingv1ledger before any schema writes. It reuses append-only lifecycle code with its own strict prediction validation and matches the exact original immutable target score, recomputing errors. A private`drift-v1/`content-addressed backup namespace cannot alterv1latest-manifest recovery.

Thirteen local tests pass:rise/decline/flat/zero,gaps/future inputs/hash/freeze guards,legal-window/retry/conflict/SQLimmutability,read-onlyv1protection,exact later scoring,pre-freeze/missed no-backfill and full synthetic capture→later-label→metrics lifecycle. A synthetic5-placeMAE is only a correctness fixture, never Beyondaccuracy. Source publication/hosted validation and real freeze/start still pending at this entry.

Coefficient-audit source356bfc6passed hosted Demand Engine41817308245and full SQL/Deno chain41817308152. Drift recovery now independently checks its ledger marker before uploading any bytes, protecting the original ledger namespace. All13drift tests still pass. Precommit wording was clarified before any real freeze; after freeze its hash and predictor implementation must remain unchanged.

## Real drift freeze and bounded no-due execution

Source3039e494passed hosted Demand Engine41818376777(309unit checks plus original reproductions). Final precommit wording published inbd7da661before freeze. Rule frozen at11:06:27UTC,SHA332f6fd37bc2a09ce665668ef3c9c23d8d34ec3613f18435ec729d95d3bb43cf. First actual cycle completed with0new attempts/points, nullMAEand byte-verified private backup; sourcev1ledger/artifact hashes unchanged. No pre-freeze forecast reconstructed. DetachedPID154243started11:07UTC,300second interval,Nov5 09:30UTCdeadline. Its first scores require tomorrow's new genuine targets and may need later bounded-worker renewal; no perpetual-coding/scheduler claim.
