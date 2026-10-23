# P9 Booking Curve / Trajectory Shape — Precommit v1

Date: **2026-10-23**

Status: **IMPLEMENTATION STARTED / REPRESENTATION PRECOMMITTED / NO MODEL RESULT OPENED**

Production remains:

`live_adjustment = 0`

## Research question

> Does a PIT-safe representation of the full public-inventory trajectory, compared with completed historical booking curves, provide incremental attendance-forecast MAE reduction beyond the strongest structural/pre-live anchor and existing velocity-based live correction?

P9 is deliberately **not** another hyperparameter variant of Long72/P2.

## Existing infrastructure reused

Beyond already has:

- PIT snapshots;
- live trajectory features;
- velocity and acceleration;
- anomaly/release flags;
- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/trajectory_gap.py`.

P9 adds a different representation:

`normalized trajectory -> historical curve similarity -> robust pickup distribution -> remaining-demand estimate -> residual challenger`

## Fixed P9 v1 representation

Canonical hours before kickoff:

`168, 144, 120, 96, 72, 60, 48, 36, 24, 18, 12, 6`

Rules:

1. target curve uses only snapshots with `captured_at <= target as_of_at`;
2. target canonical points later than the forecast cutoff remain missing;
3. interpolation is allowed only between two already-visible target snapshots;
4. no target extrapolation into its future is used as a feature;
5. public inventory is explicitly treated as a **demand proxy, not confirmed paid sales**;
6. normalized `available_index` uses first-visible public inventory;
7. historical reference pool excludes the target event itself;
8. reference event must have completed by target `as_of_at`;
9. curve similarity uses weighted L1 distance on target-observed overlapping canonical points only;
10. minimum overlap is `3` canonical points;
11. first reference pool size target is up to `5` nearest eligible prior events;
12. pickup estimate uses the median and Q25/Q75 of realized reference pickup rather than one-neighbor extrapolation.

Canonical code:

- `ml/p9_booking_curve_v1.py`;
- `ml/test_p9_booking_curve_v1.py`.

## Leakage tests already encoded

Regression tests assert that:

- adding a post-cutoff target snapshot cannot change the target representation;
- future target canonical points are missing;
- curve distance cannot use future target points;
- same-event reference is excluded;
- a reference completed after target `as_of_at` is excluded;
- output explicitly records `target_future_points_used=false`.

## First model family

P9 v1 does **not** precommit an LSTM/Transformer.

The first learnable challenger will remain simple and auditable:

`strong structural/pre-live anchor + pickup/curve-shape residual correction`

The exact learnable residual model is frozen only after genuine reference-curve coverage is audited. Coverage audit must not inspect the final result matrix while choosing the representation.

## Why no deep sequence model yet

Recent sports-ticket research supports the value of sales-trajectory representation, but Beyond currently has a much smaller and semantically different sample. Deep sequence models remain a later candidate only after reference-curve coverage and forward validation justify the capacity.

## Required next steps

1. wire canonical snapshot rows into `CurveObservation`;
2. measure eligible reference events / clubs / overlap distribution at each horizon band;
3. persist a target-free representation audit;
4. freeze the first P9 residual candidate;
5. use strict forward-event evaluation;
6. apply Governance v2 to interpretation;
7. do not mutate frozen Long72/P2.

## Literature anchors

- Weatherford & Kimes (2003), DOI `10.1016/S0169-2070(02)00011-0`;
- Lee et al. (2011), DOI `10.1016/j.ijforecast.2010.10.004`;
- Webb et al. (2020), DOI `10.1016/j.ijhm.2020.102590`;
- Takagi et al. (2026), DOI `10.5220/0015193800004091`.

## Decision

**ADVANCE P9 REPRESENTATION DEVELOPMENT. DO NOT CLAIM MAE UPLIFT YET.**
