# Postmatch scoring readiness — November 6, 2026

The real history collector had no attendance outcomes and therefore had never executed its nonempty score persistence loop. An isolated positive-path test found that it passes the `scores` directory as the file argument to `persist_score(path, row)`. The first prefix creates a file named `scores`; the next prefix fails with an immutable-score conflict. This was reproduced entirely in a disposable clone before any real labels arrived. No actual evidence was changed.

## Corrected operational path

`ml/c1_history_scoring_adapter_v1.py` preserves the original model loading, source guards, capture function, complete scoring replay, summary, review thresholds and backup. It supplies the unchanged persistor with `scores/event-<id>-snapshot-<id>.json`. Existing malformed evidence is preserved and rejected, never deleted or silently migrated. Original frozen collector/model/precommit bytes remain unchanged; no fitting or forecast adjustment.

`ml/run_postmatch_outcome_closure_v3.py` reuses the existing public source acquisition, actual run/attempt linkage, append-only verification, fixed three opportunities and deadline. Only history scoring is routed through the explicit path adapter. V2's locked code/ref is not rewritten. Publish before activating separate v3 runtime/ref; preserve every original forecast hash and exclusive locks. At this implementation checkpoint, source publication/activation are still pending.

## Offline real-model verification

`ml/postmatch_scoring_readiness_v1.py` uses cached actual issued forecasts and their exact saved inputs, original frozen estimators and all four benchmark models. It declares purely synthetic attendance as floor(verified capacity/2), independent of forecast values, and simulated postmatch clocks. Network sockets are denied; append/table/sync operations occur only in memory. Temporary score directories are destroyed after the test.

The full run passed at **15:23:38 UTC**: 3 real fresh prefixes and 4 real residual prefixes across 2 simulated event units; 26 original evidence/input hashes unchanged. It verifies raw staging → append-only response/readback → exact outcome sync → complete unchanged-model/benchmark replay → distinct immutable score files → event-balanced metrics with the review gate closed → idempotent retry. It also reproduces the original defect and verifies the corrected full cycle. Early/duplicate/revised synthetic labels and forecast substitution are rejected.

**This is engineering readiness, not measured attendance accuracy.** Real outcomes imported: 0. Real scores written: 0. Models fitted: 0. Attendance MAE: null. Synthetic numerical MAE is intentionally not exported. This does not prove the later live DB source/outcome chain.

## Genuine current capture

At 15:11 UTC, both actual workers were healthy. Wisła448 now has a genuine snapshot36408 at15:00:04 / actual issue15:06:52; fresh structural and stored prior both **28,294.020759748306**, with no newly known home facts. Motor fresh structural remains **11,928.239260475439** versus original prior **12,920.269297843897**, with7 newly known home facts. Those are forecast values, not MAE. New structural stream now has2 captured independent events and0 scored; the earlier stale-Wisła coverage remains missing historically. No backfill.

`production_change=false`, `live_adjustment=0`; all existing scientific review gates stay unchanged.

## Actual November 7 resume

The previous turn stopped before publication/activation; these new files were still uncommitted. V2 did execute its three scheduled opportunities. The08:20run42355072143 independently verified Motor8410/Wisła31849, appended history72/73 and created2genuine outcomes at08:22:42UTC. It then hit the exact diagnosed history persistence bug and left one genuine partial score at the malformed path. Do not claim the adapter was deployed yesterday or rewrite the failed V2state. New SDD/run: `.ai/specs/2026-11-07-postmatch-score-recovery.md`, `.ai/runs/2026-11-07-postmatch-score-recovery.md`.

Recovery is now separately guarded: require independent private byte recovery and exact genuine full frozen-score replay before relocating the original bytes under exclusive locks. Preserve a local original archive, immutable event/snapshot filename and all original timestamps. A prepared journal handles interrupted rename safely. Ten focused adapter/recovery/routing tests and all461registered root checks pass. The expired fixed-slot closure-v3 is not a future schedule; do not launch it as such.
