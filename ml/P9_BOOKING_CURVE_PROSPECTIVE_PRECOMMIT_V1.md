# P9 Booking Curve — Prospective Validation Precommit v1

Frozen: **2026-10-25, before the first prospective P9 prediction**

Status: **PRECOMMITTED / WAITING FOR FIRST ELIGIBLE T-48 TARGET**

Production: **UNCHANGED** (`live_adjustment = 0`)

## Purpose

The first historical P9 cohort reached 9/9 booking-curve readiness but was not honestly evaluable because its nearest historical curve references did not contain enough point-in-time incumbent forecasts persisted by the analogous historical cutoffs.

Canonical historical decision:

`ml/P9_BOOKING_CURVE_HISTORICAL_COHORT_RESULT_2026-10-25.md`

The learner itself was frozen **before** the ninth historical label and is not redesigned here.

This prospective lane validates the exact same mechanism on future matches where target predictions are persisted before attendance is available and where prior reference events can accumulate honest PIT booking curves + PIT incumbents + genuine outcomes.

## Frozen learner

Precommit ID:

`p9-knn-median-residual-k5-v1`

Mechanism:

`target incumbent + median residual of valid same-family incumbents among fixed nearest PIT-safe booking curves`

Unchanged rules:

- fixed cutoffs: **T-48 and T-24**;
- canonical P9 representation from `ml/p9_booking_curve_v1.py`;
- canonical hours: `168,144,120,96,72,60,48,36,24,18,12,6`;
- maximum interpolation gap: **12h**;
- minimum overlap: **3 canonical points**;
- weighted-L1 booking-curve distance;
- fixed `k=5` nearest references;
- use all 3 or 4 when only 3–4 valid references exist;
- fewer than 3 residual-bearing references => **no prediction**;
- target/reference residual incumbents must be from the same source family;
- Long72 incumbent maximum staleness relative to fixed cutoff: **6h**;
- reference residual = `genuine reference attendance - PIT incumbent P50 at analogous cutoff`;
- correction = median reference residual;
- challenger = `clip(target incumbent + correction, 0, verified stadium capacity)`;
- no fitted coefficient;
- no regression model;
- no candidate sweep;
- no post-hoc correction cap beyond stadium-capacity clipping.

## Prospective target eligibility

A target/cutoff can produce a prediction only when all are true:

1. competition canonicalizes to `Ekstraklasa`;
2. kickoff is still in the future;
3. no genuine attendance outcome exists for the target;
4. the exact fixed cutoff has passed:
   - T-48: `now >= kickoff - 48h`;
   - T-24: `now >= kickoff - 24h`;
5. the prediction run occurs no later than **90 minutes after the fixed cutoff**;
6. target booking-curve snapshots used by the model satisfy `captured_at <= fixed target_as_of_at`;
7. target future snapshots after the cutoff are not exported to the freeze harness;
8. target incumbent was genuinely persisted by the exact cutoff;
9. target incumbent selection follows the historical precommit unchanged;
10. verified stadium capacity exists;
11. target/reference curve lineage freezes successfully;
12. at least 3 selected nearest references have:
    - kickoff strictly before target cutoff,
    - genuine attendance confirmed after their own kickoff,
    - a same-source-family incumbent persisted by their analogous cutoff.

No late bootstrap prediction is allowed outside the 90-minute persistence window.

## Incumbent selection

For the future target at T-48/T-24:

1. require `point_in_time_validated=true`;
2. require incumbent `as_of_at <= fixed target_as_of_at`;
3. require incumbent `persisted_at <= fixed target_as_of_at`;
4. prefer `d2_long72_forward_predictions_v1` when an eligible row exists and is no more than 6 hours stale relative to the fixed cutoff;
5. otherwise use latest eligible `structural_prior_forecasts_v1`;
6. tie-break by largest `as_of_at`, then `persisted_at`, then row ID;
7. if no eligible target incumbent exists, fail closed and do not predict.

Reference incumbents must use the same selected source family.

## Reference chronology

For each future target:

- reference event must be different from target;
- reference kickoff must be strictly before target `target_as_of_at`;
- reference curve uses only snapshots before its own kickoff;
- reference outcome must be genuine reported attendance confirmed after its own kickoff;
- reference incumbent must have been persisted by the analogous T-48/T-24 cutoff;
- no target outcome is ever available to the prediction builder.

## Prediction persistence

Predictions are immutable and must be persisted before target kickoff and before any target attendance confirmation.

Required lineage:

- target ticket event ID;
- cutoff hours;
- exact `target_as_of_at`;
- `predicted_at`;
- target incumbent source/row ID/P50;
- selected reference event IDs;
- residual-bearing reference event IDs;
- reference incumbent row IDs;
- reference genuine attendance source identities;
- P9a target-free representation manifest SHA;
- target-free incumbent support manifest SHA;
- correction residual;
- challenger P50;
- verified stadium capacity;
- prediction identity SHA;
- source version / GitHub SHA;
- `target_values_used=false`;
- `production_change=false`.

No actual target attendance field belongs in the prediction ledger.

## Cadence

Scheduled check:

**hourly**.

A target is persisted only once per `(ticket_event_id, cutoff_hours)`.

The exact prediction window is `[fixed cutoff, fixed cutoff + 90 minutes]`.

This is intentionally narrow so a workflow outage cannot be converted into retrospective “prospective” evidence.

## Current first prospective windows

At precommit time the nearest known windows are:

- event 443 Cracovia vs Motor Lublin:
  - T-48 opens `2026-10-28T17:00:00Z`;
  - T-24 opens `2026-10-29T17:00:00Z`;
- event 446 Wisła Płock vs Piast Gliwice:
  - T-48 opens `2026-10-29T11:15:00Z`;
- event 6 Lech Poznań vs Wisła Kraków:
  - T-48 opens `2026-10-29T16:30:00Z`;
- event 444 GKS Katowice vs Widzew Łódź:
  - T-48 opens `2026-10-29T19:15:00Z`.

Later fixtures remain eligible when they enter the same fixed windows.

## Scoring

Target attendance may be joined only after:

- kickoff completed;
- genuine reported attendance exists;
- `attendance_confirmed_at > predicted_at`.

Prediction is never recomputed after attendance is known.

Primary prospective metric after completed targets exist:

**event-balanced MAE across all persisted eligible T-48/T-24 predictions**.

Per event:

1. compute AE for each persisted cutoff;
2. average within event;
3. average across independent events.

Secondary metrics remain the frozen historical precommit metrics:

- T-48 MAE;
- T-24 MAE;
- signed bias;
- event improvement rate;
- median event AE;
- P90 event AE;
- worst event degradation;
- paired event-block uncertainty once informative.

## Interpretation

Governance vocabulary remains:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

No result can self-declare robust without the independent business minimum meaningful ΔMAE and precision requirements.

## Prohibited changes

After the first prospective prediction, do not change without a new separately versioned precommit:

- cutoff lanes;
- 90-minute persistence window;
- representation grid;
- 12h interpolation-gap limit;
- overlap rule;
- weighted-L1 distance;
- fixed `k=5`;
- minimum 3 residual-bearing references;
- target incumbent priority;
- 6h Long72 staleness rule;
- same-family reference requirement;
- median residual aggregation;
- capacity clipping;
- event-balanced primary metric.

Do not introduce P11 odds/prices/weather/media, P4 context or P7 features into this lane.

## Production boundary

- `production_activation_allowed=false`;
- `live_adjustment=0`;
- `production_change=false`.

Prospective P9 evidence never activates production automatically.
