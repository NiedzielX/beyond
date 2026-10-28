# P9 Booking Curve Prospective Family Fallback v2

Status: **PRECOMMITTED BEFORE ANY TARGET OUTCOME**

Precommit ID: `p9-knn-median-residual-k5-family-fallback-v2`
Precommit date: 2026-10-28
Production impact: **none**
Live adjustment: **0**

## Why v2 exists

P9 prospective v1 remains frozen as `p9-knn-median-residual-k5-v1`.

The first genuine T-48 attempt (event 443, Cracovia–Motor) was captured correctly but failed closed with `PIT_SUPPORT_INSUFFICIENT` before the target outcome existed. The target had a valid D2 Long72 incumbent, therefore v1 selected the D2 family. Only 2 of the 5 already-frozen curve neighbors had a valid same-family PIT residual. The same five neighbors had 3 valid Structural Prior residuals.

This is a **target-free coverage failure**, not an MAE result. v2 is therefore allowed to address family support coverage without using the target attendance or changing v1.

Event443 is not retroactively predicted or scored by v2. v2 starts only for future immutable T-48/T-24 windows after this precommit.

## Frozen learner components retained from v1

- horizons: T-48 and T-24 only;
- booking-curve representation and P9a freeze are unchanged;
- exact same 5 nearest curve neighbors selected by P9a;
- k = 5;
- minimum usable same-family residual references = 3;
- correction = median of usable residuals;
- challenger = incumbent P50 + median residual, clipped to [0, stadium capacity];
- no fit, hyperparameter search or post-result tuning;
- reference attendance may be used only for already-completed reference events whose genuine outcome was confirmed by the target cutoff;
- target attendance is forbidden at prediction time;
- immutable prediction window is exact cutoff through +90 minutes;
- no production activation.

## Only v2 change: deterministic incumbent-family fallback

Candidate families, in fixed priority order:

1. `d2_long72_forward_predictions_v1`
2. `structural_prior_forecasts_v1`

For each family, using only data persisted by the exact target cutoff:

1. A valid target incumbent from that family must exist.
2. The already-frozen 5 P9a neighbors are not re-ranked or replaced.
3. Count usable same-family residual references among those same 5 neighbors.
4. The first family in the fixed priority order with at least 3 usable residual references is selected.

Consequences:

- If D2 has >=3 usable selected-neighbor residuals, v2 is identical to v1 and no separate fallback prediction is needed.
- If D2 target incumbent exists but D2 support is <3, while Structural target incumbent exists and Structural support is >=3, v2 emits a **Structural fallback** prediction.
- If neither family has >=3 usable selected-neighbor residuals, v2 fails closed.
- Structural is never selected merely because it has more support when D2 already satisfies the v1 minimum.

This preserves the v1 preference and changes only a target-free support failure path.

## Evidence separation

v1 and v2 must remain separately auditable.

v2 fallback predictions must store:

- target event and cutoff;
- exact P9a manifest and target lineage hash;
- selected family;
- target incumbent row;
- unchanged 5 selected neighbor IDs;
- usable residual reference IDs and their incumbent row IDs;
- support manifest hash;
- reference outcome manifest hash;
- GitHub SHA;
- `target_values_used=false`;
- `production_change=false`.

A v2 fallback row must never overwrite or replace a v1 row.

## Primary evaluation

North Star remains prospective event-balanced MAE.

For events where v1 produced a prediction, v1 remains the canonical P9 v1 result.
For v1 fail-closed events where v2 produced a fallback prediction, score v2 only after genuine target attendance is confirmed.

Report separately:

- v1 prediction coverage;
- v2 additional fallback coverage;
- v2 fallback incumbent MAE;
- v2 fallback challenger MAE;
- fallback ΔMAE;
- worst-event degradation;
- event improvement rate.

Do not combine v1 and v2 into production P50 without a later explicit reviewed promotion decision.

## Non-negotiable guards

- no retrospective v2 prediction for event443;
- no target label access at prediction time;
- no historical backfill represented as prospective;
- no change to v1 rows or v1 precommit;
- no relaxation below 3 residual references;
- no alternate neighbor search;
- no further family-order tuning after outcomes;
- `live_adjustment=0`;
- `production_change=false`.
