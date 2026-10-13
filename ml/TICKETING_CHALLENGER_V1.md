# Beyond Ticketing — Ticketing Challenger v1

Status: **shadow research active**  
Production impact: **none**

## Goal

Test whether live public-inventory movement improves attendance forecasts beyond:
1. the historical baseline itself; and
2. a simple bias-only recalibration of that baseline.

This distinction is required so that a large incumbent baseline bias is not incorrectly credited to ticketing data.

## Current research checkpoint

Horizon: **T-24h**.

Dataset available on 2026-10-13:
- 8 independent completed events;
- 6 clubs;
- baseline P50 available at T-24h;
- canonical T-24h live inventory feature available before the checkpoint.

## Feature

`hybrid_v6`

Definition:
- prefer `matched_velocity_6h_pct_of_first_per_hour` when sector matching is available;
- otherwise fall back to `raw_velocity_6h_pct_of_first_per_hour`.

This lets newer multi-club events use sector-matched movement while retaining older Lech raw-only history.

## Model

One-feature Ridge regression on baseline residual ratio:

`target = actual_attendance / baseline_p50 - 1`

Hyperparameter:
- Ridge alpha = **30**.

Training feature is standardised using the training-fold mean and population standard deviation.

The current frozen forward model is:
- version: `ticketing-challenger-v1-t24-ridge-a30-20261013`;
- training events: 8;
- training clubs: 6;
- training feature mean: 0.771822;
- training feature standard deviation: 0.517190;
- mean residual calibration: -16.364%;
- feature beta: 0.016273.

The fitted calibration term is materially larger than the ticketing coefficient, which is why bias-only control remains mandatory in evaluation.

## Validation

Two event-level protocols are maintained.

### Leave-one-event-out

Each event is predicted by a model trained on the other events.

Results:
- baseline MAE: **5,266.1**;
- bias-only MAE: **4,308.8**;
- challenger MAE: **4,057.4**;
- uplift vs baseline: **+1,208.8**;
- incremental ticketing uplift vs bias-only: **+251.4**.

### Leave-one-club-out

All matches belonging to the predicted event's home club are removed from training. This is the more important cross-club generalisation test.

Results:
- baseline MAE: **5,266.1**;
- bias-only MAE: **5,174.0**;
- challenger MAE: **5,007.3**;
- uplift vs baseline: **+258.9**;
- incremental ticketing uplift vs bias-only: **+166.8**.

Both protocols currently classify the feature as `positive_research_signal`, but the sample is far too small for promotion.

## Ablation integration

Historical `baseline_ticketing` rows use only the **leave-one-club-out** predictions.

At T-24h the Context Ablation table therefore currently reports:
- 8 events;
- 6 clubs;
- baseline MAE on the same events: 5,266.1;
- Baseline + Ticketing MAE: 5,007.3;
- MAE uplift: +258.9.

The bias-only control is intentionally not treated as a Context Matrix layer. It is shown separately in Ticketing Challenger so we can isolate the incremental value of ticketing itself.

## Forward shadow scoring

The frozen model scores only:
- `T-24h` snapshots;
- `capture_mode = prospective`;
- checkpoints occurring after model training;
- feature snapshots captured at or before the checkpoint;
- events that already have a valid baseline P50.

The predicted residual adjustment is capped to [-25%, +25%].

No historical event is backfilled using the fitted forward model. Historical evaluation uses cross-validation predictions only.

## Automation order

Every 15 minutes:
1. `event_context_snapshot_15m` — checkpoint snapshot;
2. `crossclub_checkpoint_baseline_15m` — minute 02/17/32/47;
3. `ticketing_challenger_score_15m` — minute 04/19/34/49.

This guarantees that the research scorer runs after snapshot and baseline creation.

## Promotion gate

Ticketing Challenger v1 remains shadow-only.

A future promotion decision requires:
- substantially more independent completed events;
- continued positive leave-one-club-out uplift;
- positive incremental uplift over bias-only control, not merely over a biased baseline;
- prospective shadow evidence from genuinely future checkpoints;
- review of release / sector-coverage anomalies.
