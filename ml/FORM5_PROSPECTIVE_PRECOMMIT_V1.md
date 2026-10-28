# Form5 Prospective Challenger — Precommit v1

Precommitted: **2026-10-28**, before the first genuine outcome from the automated TheSportsDB `sport.form5` stream is available to the learner.

## Objective

Test whether recent home-team league form improves true prospective T-24 attendance MAE versus the immutable baseline forecast.

North Star:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction: `ΔMAE < 0`.

Readiness is not model success.

## Data contract

Only use immutable `event_context_snapshots_v1` rows where:

- `checkpoint_code = 'T-24h'`;
- `capture_mode = 'prospective'`;
- `sport.form5` is present with a non-null numeric value;
- `sport.form5.source_name = 'TheSportsDB v1 shadow'`;
- observation `observed_at`, row `created_at`, and `source_observed_at` are all at or before the T-24 checkpoint;
- the attendance outcome was not available at prediction time.

The automated form5 observation is defined as home-team league points from exactly the five most recent completed Ekstraklasa matches known through TheSportsDB `fetched_at` before the target checkpoint.

Historical immutable snapshots must never be backfilled with the new automated feature.

## Testability gate

Do not evaluate the learner before all conditions are true:

- at least **8 completed eligible events**;
- at least **5 distinct home clubs**;
- at least **2 distinct form5 numeric values**.

If the gate is not met, status is `PROSPECTIVE_COLLECTING` and no MAE claim is allowed.

## Frozen learner

Comparator:

- immutable true `baseline` T-24 prediction from the same snapshot;
- do **not** use the rejected Ticketing challenger as the anchor.

Feature:

- `sport.form5` points, range 0–15.

Fold model:

1. Calculate training-fold baseline residual ratio:
   `(actual_attendance - baseline_p50) / baseline_p50`.
2. Standardize `sport.form5` using training-fold mean and population standard deviation only.
3. Fit one ridge slope with fixed `alpha = 30` plus the training-fold mean residual intercept.
4. Apply the resulting residual correction to the held-out baseline P50.
5. Clamp the total residual correction to **[-25%, +25%]**.

No parameter search, feature transformation search, alternate windows, interaction search, or post-outcome tuning is allowed in v1.

## Validation protocol

Primary protocol:

- **leave-one-club-out (LOCO)**.

Secondary diagnostic:

- leave-one-event-out (LOEO).

LOEO and LOCO must not be presented as independent confirmation when the sample contains only one event per home club.

Minimum training-fold requirements:

- at least 5 training events;
- at least 4 training clubs;
- non-zero training-fold feature standard deviation.

## Metrics

Primary:

- event-balanced incumbent MAE;
- event-balanced challenger MAE;
- `ΔMAE`.

Mandatory downside diagnostics:

- event improvement rate;
- worst-event degradation;
- median challenger absolute error;
- P90 challenger absolute error;
- number/share of predictions hitting the ±25% cap;
- fold slope sign stability.

A point improvement alone is not sufficient for promotion.

## Decision states

- `PROSPECTIVE_COLLECTING` — gate not met.
- `EVALUATED_NO_UPLIFT` — gate met and challenger does not improve primary MAE.
- `POINT_GAIN_UNCERTAINTY_LIMITED` — point MAE improves but sample/downside/stability is insufficient.
- `PROMOTION_REVIEW_CANDIDATE` — meaningful MAE improvement with acceptable downside on a sufficiently independent prospective sample; still requires explicit human review.

No state automatically changes production forecasts.

## Production guard

For v1:

- `production_activation_allowed = false`;
- `live_adjustment = 0`;
- `production_change = false`.

The purpose of v1 is evidence collection only.
