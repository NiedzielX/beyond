# P9 Booking Curve — Learner Precommit v1

Frozen: **2026-10-25, while full T-168 readiness was 8/9 and before the ninth full-window attendance label was available**.

Status: **PRECOMMITTED / LEARNER EXECUTION BLOCKED UNTIL 9/9**

Production: **UNCHANGED** (`live_adjustment = 0`)

## Research question

> Does the PIT-safe shape of the public-inventory booking curve add attendance-forecast information beyond the strongest genuinely persisted incumbent available at T-48 and T-24?

This is the first P9 learner precommit. It freezes one deterministic challenger before the 9th full-window label is available. It is not a candidate sweep.

## Unlock gate

The learner/evaluator must fail closed unless fresh `public.p9_booking_curve_readiness_v1()` reports:

- `complete_events_168 >= 9`;
- at least 3 independent clubs in the full-window reference sample;
- `research_start_trigger = true`;
- target-free representation freeze completed before labels/results are joined.

At freeze time the genuine full-window state is **8/9**. No P9 learner result may be opened before the gate passes.

Do not lower or reinterpret the existing 12-hour trajectory-quality ceiling to force the gate. In particular, events with >12h gaps remain ineligible even if their labels are known.

## Frozen representation

Canonical implementation:

`ml/p9_booking_curve_v1.py`

Git blob SHA at precommit:

`58b542ff57953752e6eebb8f75428d1e0ce23ec7`

Representation contract:

- canonical hours: `168, 144, 120, 96, 72, 60, 48, 36, 24, 18, 12, 6`;
- inventory interpretation: `demand_proxy_not_confirmed_sales`;
- normalization denominator: first visible positive public inventory for the event;
- maximum interpolation gap: **12 hours**;
- minimum overlapping canonical points for curve distance: **3**;
- curve distance: weighted L1 on target-observed canonical points only;
- distance weight at point `h`: proportional to `1 / max(h, 6)`;
- reference event must be different from target;
- reference event must have completed before target `as_of_at`;
- target future trajectory points are forbidden;
- self leakage is forbidden.

The existing P9a target-free freeze harness remains the representation/identity authority:

`ml/p9a_booking_curve_freeze_v1.py`

Existing audited target-free manifests:

- T-24: `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- T-48: `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`.

Those manifests prove the representation contract and target-free freeze path. The post-9/9 evaluation run must create a fresh target-free freeze artifact under the same contract before any target labels are joined, because the genuinely available reference catalog will have grown.

## Evaluated cutoffs

Exactly two cutoff lanes are allowed in v1:

- **T-48**;
- **T-24**.

Reason: these are the two P9a lanes already audited target-free on main. P9 v1 does not introduce a new un-audited cutoff after the 9th label arrives.

The primary headline metric combines both cutoffs; per-cutoff metrics are secondary diagnostics. We do not choose the better-looking cutoff after results are visible.

## Frozen neighbor rule

For every target/cutoff:

1. Build the target curve using only target snapshots visible by its fixed `target_as_of_at`.
2. Build the reference catalog only from events completed before that target cutoff.
3. Exclude the target event itself.
4. Require at least 3 overlapping canonical points.
5. Rank eligible references by the existing weighted-L1 distance, tie-breaking by `ticket_event_id`.
6. Select exactly the closest **5** references when at least 5 are available.
7. If only 3 or 4 eligible references exist, use all 3 or 4.
8. If fewer than 3 eligible references exist, the target is not learner-evaluable.

`k=5` is frozen because it is the existing `DEFAULT_NEIGHBORS` in the canonical P9 representation. It is not tuned from attendance outcomes.

## Incumbent selection rule

The challenger is always a residual correction of a genuinely persisted incumbent; P9 does not replace the structural/live baseline.

For each target/cutoff, choose the incumbent using this deterministic rule:

1. consider only rows with `point_in_time_validated = true`;
2. require both incumbent `as_of_at <= target_as_of_at` and `persisted_at <= target_as_of_at`;
3. prefer `d2_long72_forward_predictions_v1` when an eligible row exists whose `as_of_at` is no more than 6 hours older than the target cutoff;
4. otherwise use the latest eligible `structural_prior_forecasts_v1` row;
5. within a source, choose the largest `as_of_at`, then largest `persisted_at`, then largest row ID;
6. if no eligible incumbent exists, target is not comparator-ready and is excluded fail-closed.

The selected incumbent source family becomes part of the target lineage.

## Reference residual rule

For each selected curve neighbor, calculate a historical residual only when all of the following are true:

1. genuine reported attendance exists for the reference event;
2. the attendance confirmation is post-match;
3. an incumbent from the **same source family as the target incumbent** can be reconstructed for that reference at the analogous fixed cutoff;
4. the reference incumbent obeys the same PIT rule: its `as_of_at` and `persisted_at` must be at or before `reference_kickoff - cutoff_hours`;
5. for `d2_long72_forward_predictions_v1`, the reference incumbent must also be no more than 6 hours stale relative to the analogous cutoff;
6. no target attendance or target post-cutoff snapshot is accessed while constructing the neighbor/residual set.

Reference residual:

`reference_residual = actual_attendance_reference - incumbent_p50_reference`

A selected curve neighbor without a valid same-family residual remains part of representation lineage but does not contribute a residual value.

At least **3 residual-bearing neighbors** are required. Otherwise the target is not learner-evaluable.

## Frozen learner

There is exactly one P9 v1 learner:

`p9-knn-median-residual-k5-v1`

Correction:

`trajectory_residual = median(reference_residuals_of_valid_selected_neighbors)`

Prediction:

`challenger_p50 = clip(target_incumbent_p50 + trajectory_residual, 0, verified_stadium_capacity)`

No distance-weighted attendance residual.

No fitted scaling coefficient.

No intercept.

No regression model.

No hyperparameter search.

No candidate family selection.

No post-hoc correction cap beyond the physically valid final `[0, stadium_capacity]` clipping.

The following representation diagnostics are persisted but are **not** tunable model inputs in v1:

- curve similarity distances;
- reference event count;
- reference club count;
- median remaining pickup share;
- pickup Q25/Q75;
- selected neighbor identities;
- overlap-point counts;
- target curve points;
- target cutoff boundary source/age.

## Target-free freeze before label join

When the 9/9 gate passes, execution order is mandatory:

1. export target-free T-48 and T-24 P9 inputs;
2. freeze target snapshot identities, reference-pool identities, selected-neighbor identities and incumbent identities;
3. persist deterministic manifest SHA(s);
4. hard-verify `target_values_used=false` and `target_future_points_used=false`;
5. only after the freeze artifact exists, join genuine historical attendance for eligible reference residuals and target evaluation;
6. never mutate the frozen identity artifact in response to the resulting MAE.

The evaluator must not choose identities based on which target labels are present or favorable.

## Independent unit and primary metric

Independent unit:

`ticket_event`

Primary metric:

**event-balanced mean absolute error across the two fixed cutoffs**.

For each event:

1. calculate absolute error at every learner-evaluable fixed cutoff among T-48 and T-24;
2. average those errors within the event;
3. average event-level errors across independent events.

The incumbent is aggregated identically.

Primary delta:

`delta_MAE = challenger_event_balanced_MAE - incumbent_event_balanced_MAE`

Negative is better.

## Secondary metrics

Report all of the following without selecting the most favorable one as the headline:

- T-48 event-balanced MAE;
- T-24 event-balanced MAE;
- event-balanced signed bias;
- event improvement rate;
- median event absolute error;
- P90 event absolute error where defined;
- worst event degradation versus incumbent;
- number of learner-evaluable events;
- number of independent clubs;
- residual-bearing neighbor count distribution;
- selected-neighbor diversity;
- paired event-block bootstrap interval for challenger-minus-incumbent MAE;
- `P(delta_MAE < 0)` as descriptive uncertainty evidence.

## Governance interpretation

Use the existing Governance v2 vocabulary:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

`ROBUST_RESEARCH_ADVANCE` remains unavailable unless all existing governance requirements pass, including a separately approved business-derived minimum meaningful absolute `ΔMAE` and sufficient precision.

The business threshold must not be derived from this P9 result.

## Prohibited changes after the 9th label/result is visible

Without a new separately versioned precommit, do not change:

- canonical hour grid;
- 12h interpolation-gap ceiling;
- 3-point minimum overlap;
- cutoff lanes;
- incumbent selection priority;
- 6h incumbent staleness rule;
- weighted-L1 distance definition;
- `k=5` neighbor rule;
- minimum 3 residual-bearing neighbors;
- median residual aggregation;
- same-incumbent-family requirement;
- final capacity clipping;
- event-balanced primary metric;
- reference chronology rules;
- target/reference identity freeze order.

Do not add P11 odds, pricing, weather, media attention, P4 fixture context or P7 features to this P9 v1 lane. Those remain separate information-family ablations.

## Production boundary

- `production_change=false`;
- `production_activation_allowed=false`;
- `live_adjustment=0`.

A positive P9 research result does not activate production automatically.
