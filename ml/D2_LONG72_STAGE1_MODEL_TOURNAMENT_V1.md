# d2 Long72 Stage 1 — Early-Live Model Tournament v1

Last updated: **2026-10-21**

Status: **ACTIVE EXPOSED-HISTORICAL LOEO R&D / NO PRODUCTION CHANGE**

Parent evidence:

- `ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`;
- frozen long72 contract from main run `39640723942`.

## Objective

Test whether PIT ticket trajectory adds attendance-forecast value **before the final 24 hours**, where the current frozen final24 Ridge/P2 model has not been validated.

This experiment deliberately excludes `0–24h` from selection.

Window:

`24 < hours_to_kickoff <= 72`

Anchor:

Frozen T-3 checkpoint hold.

Target:

`actual_attendance / capacity - anchor_p50 / capacity`

## Frozen input lineage

The tournament may run only if rebuilding the long72 contract produces the exact frozen bytes from the successful main replay.

Frozen long72 contract run:

`39640723942`

Artifact:

`d2-long72-anchor-contract-v1-39640723942`

Artifact ID:

`12365352293`

Artifact ZIP SHA256:

`83082cca46b6aa78fd744f59e9fd7eaaef6e7d33e8135817bda78a201b454561`

Exact successful input hashes:

- contract JSON: `0083b82bc404055200fb3197cc20e3a87a7c5a57b564d70213af81ff8dcede2a`;
- dataset CSV: `2af62094eec57aba3c3e8c96ed33d06cf611f9cd60b690d72e2deedbdf63ce17`.

No model fitting is permitted if either hash differs.

## Dataset used by Stage 1

Full frozen long72 contract:

- 14 events;
- 130 rows across `0–72h`.

Stage-1 early-live subset:

- 13 independent events;
- 80 rows across `24–72h`;
- 45 rows in `24–48h`;
- 35 rows in `48–72h`;
- 10 independent events in the `48–72h` band.

All Stage-1 rows use the frozen T-3 checkpoint anchor.

## Evidence classification

All historical outcomes used here are already exposed research evidence.

Original frozen final24 Stage-1 event IDs:

`1,3,4,8,9,12,13,14,17`

Later exposed labeled IDs:

`5,11,15,18,19`

Therefore:

- this tournament is **not** an unseen-holdout experiment;
- LOEO prevents same-event snapshot leakage but is not a temporal holdout;
- later exposed events are reported separately for diagnostics;
- a selected expert must pass a separate fixed-candidate chronological audit before reliability Stage 2 is considered.

## Validation

Independent unit:

`ticket event`

Validation:

`Leave-One-Event-Out`

For each held-out event:

- every row from that event is excluded from training;
- training rows receive event-balanced weights (`1 / rows in event`);
- no random snapshot split is allowed.

## Correction governance

Raw model output is occupancy correction relative to T-3 anchor.

Applied correction cap:

`+/- 10 percentage points occupancy`

Final forecast:

`clip(anchor_p50 + correction * capacity, 0, capacity)`

## Predeclared candidates

1. `anchor-zero-correction`;
2. `train-fold-bias`;
3. `inventory-linear-extrapolation`;
4. `ridge-a10`;
5. `ridge-a30`;
6. `huber-a001`;
7. `histgbr-abs-l7-leaf5-l2-10`.

No Chronos/TSFM and no external-family model zoo in this tournament.

The purpose is to establish whether a compact tabular/transparent early-live correction signal exists before expanding the hypothesis space.

## Selector

A learned/heuristic challenger is selector-eligible only if event-balanced MAE improves the zero-correction anchor in all three views:

1. overall `24–72h`;
2. `24–48h`;
3. `48–72h`.

Among eligible candidates rank by:

1. lowest overall `24–72h` event-balanced MAE;
2. lowest `48–72h` event-balanced MAE;
3. lowest overall worst-event degradation;
4. candidate ID deterministic tie-break.

If no challenger satisfies all three positive-MAE gates:

`research_lead_candidate_id = anchor-zero-correction`

## Required metrics

For overall `24–72h` and each band `24–48h`, `48–72h`:

- event-balanced MAE;
- anchor MAE;
- MAE improvement and relative improvement;
- event improvement rate;
- worst-event degradation;
- best-event improvement;
- event-balanced bias;
- mean absolute revision;
- row median AE;
- row p90 AE;
- event count and row count.

Also report separately:

- original Stage-1 exposed subset;
- later exposed subset.

## Decision semantics

Possible Stage-1 conclusion:

### `EARLY_LIVE_SIGNAL_NOT_PROVEN`

No challenger improves both early-live bands plus overall MAE.

Close this model formulation, not long-horizon R&D.

### `EARLY_LIVE_RESEARCH_LEAD_SELECTED`

A challenger passes the LOEO selector.

Next required step:

> freeze that exact candidate and replay it under a separately declared chronological/fixed-candidate audit before any Stage-2 reliability policy is selected.

LOEO selection alone does not justify production, promotion, or reliability tuning.

## Production boundary

Always:

- Track-A Frozen Pre-Live v2 / Ridge / P2 unchanged;
- Pre-Live v3 research-only;
- final24 model unchanged;
- no production write;
- `live_adjustment = 0`.
