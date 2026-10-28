# Trajectory Lane B v1 — Implementation Note

Recorded: **2026-10-28, before the first Lane B outer result was opened**

Applies to:

`trajectory-lane-b-small-gru-residual-v1`

## Capacity-channel comparability

The persisted checkpoint rows used for the already-frozen Lane A outer result contain verified structural stadium capacity, but their trajectory field `available_share_of_capacity` is not populated.

To avoid giving Lane B a new capacity-normalized inventory signal after Lane A's outer result is known, the first frozen Lane B run uses:

- `available_index` as the genuine normalized inventory trajectory channel;
- sequence `available_share_of_capacity` as missing / numeric 0 under the precommitted missing-channel rule;
- verified capacity only in the global context (`structural_incumbent_p50_share_of_capacity` and capacity-available flag) and for physical prediction clipping.

This is deliberately conservative and preserves the intended apples-to-apples comparison of **trajectory representation**, rather than adding a new information source to Lane B.

No event identities, folds, architecture, optimizer parameters, seeds, epoch count, target, or scoring rule are changed by this note.

Any future model that explicitly introduces capacity-normalized inventory as a newly populated sequence channel must receive a new version/precommit.
