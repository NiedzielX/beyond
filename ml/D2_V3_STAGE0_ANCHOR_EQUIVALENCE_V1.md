# d2-v3 Stage 0 — Final-24h Anchor Equivalence v1

Last updated: **2026-10-21**

Status: **ACTIVE / NO TRAINING / NO PRODUCTION CHANGE**

## Question

The existing d2 Stage-1/Stage-2 model was developed on the frozen 9-event / 30-row final-24h replay using the Frozen Pre-Live v2 T-1 anchor.

Pre-Live v3 changes T-30 and T-7, but its sealed T-1 package is exactly the Frozen-v2 T-1 package.

Before retraining anything, test:

> **Does Frozen Pre-Live v3 change the actual final-24h anchor or live-residual target used by the existing d2 development set?**

## Exact development identities

Reuse the existing frozen d2 development contract only:

- 9 events;
- 30 rows;
- event IDs `1,3,4,8,9,12,13,14,17`;
- exact event + `as_of_at` identities from C1 v8 training contract;
- no newer holdout/prospective event enters the test.

## Lineage gates

Hard verify:

1. Frozen-v2 Stage-0 replay is reproduced exactly;
2. v2 T-1 and v3 T-1 historical-base IDs are identical;
3. v2 T-1 and v3 T-1 current-season-regime IDs are identical;
4. both T-1 contracts use `NO_CONTEXT`;
5. v2/v3 T-1 four-fold expected MAE vectors are identical;
6. both freezes use the same historical-runtime SHA and feature contract;
7. capacities and actual-attendance labels remain unchanged.

Only after these gates pass may row-level v3 equivalence be asserted.

## Row-level comparison

For every frozen final-24h row persist:

- `frozen_v2_p50`;
- `frozen_v3_p50`;
- seat delta;
- occupancy-share delta;
- v2 target live delta attendance/occupancy;
- v3 target live delta attendance/occupancy;
- target deltas.

## Decisions

### `V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Requires all 30 rows to have exact zero anchor-seat delta and target difference within `1e-12`, after all lineage gates pass.

Then:

- do not create a cosmetic new Stage-1 model version;
- existing final-24h d2 target/model lineage remains valid against v3 because its T-1 anchor is unchanged;
- next Track-B live R&D must be materially different.

Preferred next hypothesis if data exists:

> extend live updating earlier than 24h so the changed v3 T-7 anchor becomes relevant.

Otherwise test a materially different final-24h target/reliability/feature hypothesis under a new declared contract.

### `V3_FINAL24_ANCHOR_DIFFERS_FROM_V2`

If any lineage or row-level equality gate fails:

- create a new d2-v3 target;
- rerun Stage-1 expert selection under event-level LOEO;
- revalidate reliability/tail governance under new IDs.

## Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- v3 research-only;
- no model training in this experiment;
- no production write;
- `live_adjustment = 0`.
