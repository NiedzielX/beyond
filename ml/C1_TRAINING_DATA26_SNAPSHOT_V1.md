# C1 expanded training-support snapshot26 v1 — no fit

2026-11-04. The six newly confirmed completed events6/443/444/445/446/447 are now prepared as additional exposed training information, not validation. Existing median20/Ridge20 artifacts, collectors, scalers, policies and review gates remain unchanged.

## Actual data and integrity

-26 independent canonical home-matchday fixtures /12clubs /80rows /same30features.
- Original20events /74rows retained **byte-for-byte** as the CSV prefix, SHA256 `be9aab4721e69661b8f14d3e1e8938abde569dabd6f7878e0986868fc0756549`. No original prior was reconstructed using newly obtained attendance history.
- Added exactly one latest actually persisted C1-time row for each of the six events, chosen by that declared source rule, not by its error. Resolve the stored T-1anchor, require its real generation before source time, match the genuine snapshot/time, and reconstruct the frozen original model output. Maximum numeric discrepancy **7.275957614183426e-12**persons.
- Combined80rowCSV SHA256 `0b8eb22c767d16e07b84b59eaa73aeff5ca55b11a220f4939dbb2ae2aaa9d778`; label knowledge cutoff18:45:48.637107UTC, prepared18:45:55UTC. New targets confirmed by that time; all inputs before kickoff. Old training targets independently agree with the current unchanged outcomes.

Private data: `/workspace/ops-runtime/2026-11-04-c1-training-data26-v1/`. Source/truth/prior/snapshot records, raw CSV, validation receipts and canonical fixture metadata stay outside Git. Six tests cover exact byte preservation, disjoint support/schema, independent fixture units, source/time/label availability, target exclusion and numeric serving parity.

This is frozen-feature reconstruction at actual stored forecast times, **not a dump of original private input vectors**. Numeric serving parity and source identities are verified; historical upstream assumptions retain their documented scope. All26events are training/exposed for a successor. Fresh validation events0; models fitted0; new candidate forecasts0; attendance-MAE computedfalse. The existing C1score3248.81on17cannot be used as validation for a future model trained on these26.

## Next experimental boundary

A possible successor may test only added support26vs20 while holding the declared learner, fitted preprocessor, target, regularization, event weights, clipping and policy fixed. It needs its own exact precommit **before fit** and genuine paired future evidence. The six new rows use one source point each, whereas the original20retain their historical prefixes; declare this sampling explicitly. Never call a training fit or this numerical reconstruction an accuracy improvement. No model/parameter selection or production activation occurs here. `production_change=false`, `live_adjustment=0`.

Private recovery of6data/lineage/validation files: 30091bytes, SHA256 `0ec7ef631298c73420a329ee30668392644c186dab451764e5d45d5a8ed41278`. Upload, byte read-back and decompression verified; no raw row/CSV added toGit.
