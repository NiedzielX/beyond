# Rolling72 v2: bounded private recovery

Date: 2026-11-09. Status: IMPLEMENTED — actual remote private backup, independent restore and trusted model replay verified.

This implements recovery for the separate paired-v2 prospective ledger under
[the exact precommit](../../../ml/artifacts/rolling72_v2/precommit.json) and
[offline-training/paired-shadow SDD](../2026-11-08-rolling-72h-offline-training-and-shadow-v2.md).
It changes no frozen v1 file, model, old ledger, forecast or assumption.

The bundle contains a consistent read-only SQLite backup, its exact lane freeze,
all original source receipts referenced by the ledger, original identity registry,
the exact precommit, model bytes, private manifest, completed fit marker and bounded
operator metadata. Model bytes are checksummed but NEVER deserialized by backup or
restore. Hashes establish byte consistency within this trusted local pipeline;
they do not authenticate arbitrary uploaded pickle files.

Only the existing private bucket `beyond-daily-path-research-v1` may be used. New
objects use `rolling72-shadow-v2/<envelope-sha256>.json`; bucket creation, public
access, mutable latest manifests and access to older namespaces are forbidden.
Envelope, compressed/inflated payload, individual files, source count and metadata
are bounded. Filenames are flat and allowlisted. SQLite application identity,
exact table set, integrity, foreign keys, lane freeze, source receipts, model
manifest/marker/bytes, registry and clocks must all validate before any restore.
Restore requires a new private directory outside Git and never overwrites files.

Acceptance: synthetic-only tests prove a full local upload/readback/independent
restore using fake immutable private storage; altered envelope/files/model/source,
foreign or unexpected SQLite, unsafe names, compression corruption, exceeded
bounds, public/missing bucket and existing destination all fail closed. Actual
remote completion is a separate parent-run step after published code and genuine
v2 forecasts. Recovery is not managed SQL serving, hosted forecast execution or
evidence of MAE improvement. Defaults remain `production_change=false` and
`live_adjustment=0`.

Local evidence: `python -m unittest ml.test_rolling72_backup_v2 -q` passes 15
synthetic-only tests; both new Python files compile and `git diff --check` passes.
The fake upload performs one privacy check, verified upload read, an independent
second read and a full independent restore. A patched `joblib.load` that raises
confirms restore never executes model bytes. Actual private recovery was completed after genuine v2 capture; evidence follows.


Actual completion: published code8b02d71/freeze30e1c98 preceded first forecasts10:45:31UTC. Private10file793066byte bundle20cb6626… was read back and independently restored. A second actual remote retrieval at19:46UTC restored a new private directory, loaded the trusted unchanged artifact and exactly replayed allsix candidate predictions, with no refit/backfill/oldledgerwrite. [Public machine proof](../../../ml/ROLLING_72H_FIRST_PAIRED_SHADOW_PROOF_2026-11-09.json). This completed recovery requirement does not close future accuracy or panel-serving gates.
