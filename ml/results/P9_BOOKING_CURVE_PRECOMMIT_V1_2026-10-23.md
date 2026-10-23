# P9 Booking Curve / Trajectory Shape — Precommit v1

Date: **2026-10-23**

Status: **REPRESENTATION IMPLEMENTED / REAL READINESS AUDITED / SHORT-HORIZON R&D READY / FULL 168H DATA-BOUND**

Production remains:

`live_adjustment = 0`

## Research question

> Does a PIT-safe representation of the public-inventory trajectory, compared with completed historical booking curves, reduce attendance-forecast MAE beyond the strongest structural/pre-live anchor and existing velocity-based live correction?

P9 is deliberately a new **trajectory representation**, not another Long72/P2 hyperparameter variant.

## Representation

Conceptual pipeline:

`normalized trajectory -> historical curve similarity -> robust pickup distribution -> remaining-demand estimate -> structural residual challenger`

Canonical hours before kickoff:

`168, 144, 120, 96, 72, 60, 48, 36, 24, 18, 12, 6`

Rules:

1. use target snapshots only when `captured_at <= target as_of_at`;
2. later target canonical points remain missing;
3. never extrapolate the target trajectory into its future as a feature;
4. interpolate only between already-visible observations;
5. interpolation bracket may not exceed **12 hours**, matching the canonical live-trajectory `DATA_GAP_HOURS` quality ceiling;
6. public inventory remains `demand_proxy_not_confirmed_sales`;
7. normalize using first-visible public inventory;
8. exclude the target event from its reference pool;
9. reference event must have completed by target `as_of_at`;
10. weighted-L1 curve distance uses only target-observed overlapping points;
11. minimum overlap is three canonical points;
12. pickup uses robust median/Q25/Q75 over eligible nearest historical curves, not one-neighbor extrapolation.

Canonical implementation:

- `ml/p9_booking_curve_v1.py`;
- `ml/test_p9_booking_curve_v1.py`;
- `supabase/sql/p9_booking_curve_readiness_v1.sql`;
- `public.p9_booking_curve_readiness_v1()`.

## Leakage / quality tests

Tests fail closed when:

- a post-cutoff snapshot would be needed;
- a future target point would be used;
- interpolation requires a gap >12h;
- the target event appears in its own reference set;
- a reference event had not completed by target `as_of_at`.

Output explicitly records `target_future_points_used=false`.

## Real completed-event readiness audit

Read from `public.p9_booking_curve_readiness_v1()` after deployment on 2026-10-23.

Completed outcome events available: **15**.

| Curve window | Ready events | Ready clubs | Ready event IDs | Status |
|---|---:|---:|---|---|
| 24→6h | **13** | **8** | 2,3,4,5,8,9,11,12,14,15,17,18,19 | enough to begin controlled short-horizon R&D |
| 48→6h | **10** | **6** | 2,3,4,5,9,11,14,15,18,19 | enough to begin controlled short-horizon R&D |
| 72→6h | **7** | **5** | 3,4,5,11,15,18,19 | representation ready; small for learned claims |
| 168→6h | **4** | **4** | 5,15,18,19 | **DATA_BOUND** |

These counts require:

- event history beginning at or before the window start;
- history reaching 6h or later;
- at least three snapshots in the window;
- maximum within-window snapshot gap <=12h;
- completed event with genuine attendance outcome.

## Development decision

### P9a — start now

Use the **24–48h booking-curve family** as the first controlled R&D lane because it has 13/10 independent events and multi-club coverage.

Before fitting:

1. freeze exact target-event/as-of identities;
2. calculate each target's reference pool using **prior completed events only**;
3. persist reference identities and curve-distance/pickup features;
4. freeze the first simple residual candidate;
5. use strict forward-event evaluation;
6. report event-balanced MAE and event-block uncertainty;
7. interpret through Governance v2.

P9a must not reuse a future completed event merely because the experiment is historical.

### Full P9 168h — wait

Only four completed events currently satisfy the full 168→6h quality contract. That is insufficient for a serious learned challenger.

Do not weaken the 12h quality rule or fabricate historical trajectory points to increase N.

## First model family

No LSTM/Transformer in v1.

First learnable design remains deliberately simple:

`strong structural/pre-live anchor + fixed curve-similarity/pickup features -> MAE-aligned residual challenger`

Deep sequence models become candidates only after the reference population materially expands.

## Literature anchors

- Weatherford & Kimes (2003), DOI `10.1016/S0169-2070(02)00011-0`;
- Lee et al. (2011), DOI `10.1016/j.ijforecast.2010.10.004`;
- Webb et al. (2020), DOI `10.1016/j.ijhm.2020.102590`;
- Takagi et al. (2026), DOI `10.5220/0015193800004091`.

## Decision

> **ADVANCE P9a 24–48h DEVELOPMENT NOW. KEEP FULL 168h P9 DATA-BOUND. NO MAE UPLIFT CLAIM EXISTS YET.**
