# Historical replay packet preparation

Status: implementation and synthetic contracts verified; actual packet export remains parent-owned after publication. Exact precommit4acdfd98… and the parent historical-blind-backtest SDD preceded implementation. No old model, dataset, worker, source or ledger was edited.

New module exposes build_packets(dataset_bytes,source_bytes,synthetic_test=False,precommit=None) and prepare_packets(outputdir,dataset_bytes,source_bytes,...). Original source/dataset bytes and canonical hashes are verified. All input coordinates are selected from first real daily/segment observations before target matching. Test inputs contain12 measured features and history quality only; future values/statuses are kept in a separate truth vault. The immutable manifest hashes training_rows.json, test_inputs.json and truth.json separately. A new private directory is required; no overwrite or false historical known_at.

Actual source read-only in-memory reconstruction:31selectedfixturegroups,300eligibleorigins,900horizoncoordinates;698MATCHED,177postkickoff and25stale targets. Every canonical matched row's features, prefix and actual label were re-derived against original inventory. No actual packet files, model fits, predictions or errors were produced by this agent.

15 meaningful synthetic tests pass: future-value poison cannot change earlier inputs; hidden/scope-changing future remains an unscored coordinate; stale/postkickoff/zero/one-point/tie cases; real elapsed hourly drift quality; source byte/hash/catalogue/feature tampering; separate private file hashes/modes and no overwrite. Python compile and diff checks pass. A composed synthetic integration with the actual independent engine also passes:6fixtures/54origins/162coordinates, one diagnosticHGBfit, a guard forbidding any truth.json open in the prediction phase, a persisted prediction seal, then separate truth scoring with unchanged prediction bytes. This is synthetic-only evidence, not real historical accuracy.

Verified at 2026-11-09T20:14:15.495057+00:00

Final source handoff 2026-11-09T20:15:51.545930+00:00; no further source changes planned.
