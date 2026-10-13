# Beyond Ticketing — Sporting Challenger v1

Status: **current candidate rejected**  
Production impact: **none**

## Goal

Test whether Sporting Context improves attendance forecasts after the already validated research sequence:

`Baseline → Baseline + Ticketing → + Sporting`

The first candidate intentionally tests only `sport.match_stakes`. Form5, rivalry and absence impact are not backfilled into historical checkpoints because they were not available point-in-time for those events.

## Evidence discipline

For historical T-24h events, Match Stakes is reconstructed from league results with match dates strictly before the target match date. Current sporting observations are never backdated into historical checkpoints.

For future prospective snapshots, the evaluation layer prefers the `sport.match_stakes` value frozen inside the immutable context snapshot.

Historical evidence mode:
- `retrospective_historical_fact_reconstruction`

Prospective evidence mode:
- `prospective_snapshot_observation`

## Candidate

Checkpoint: `T-24h`

Input baseline: `baseline_ticketing`

Feature: `sport.match_stakes`

Target:

`actual_attendance / baseline_ticketing_p50 - 1`

Model:
- one-feature Ridge regression;
- alpha = 30;
- residual adjustment capped conceptually to [-25%, +25%] during candidate scoring;
- event-level validation only.

Candidate version:

`sporting-challenger-v1-t24-stakes-ridge-a30-20261013`

## Dataset

Current completed-event sample:
- 8 independent events;
- 6 clubs;
- all have a T-24h Baseline + Ticketing prediction;
- Match Stakes can be reconstructed without using matches played after the target.

## Results

### Leave-one-club-out

This is the primary cross-club generalisation test.

- Baseline + Ticketing MAE: **5,007.3**
- bias-only control MAE: **7,138.1**
- + Match Stakes MAE: **7,314.0**
- uplift vs Baseline + Ticketing: **-2,306.8**
- incremental sporting uplift vs bias-only: **-175.9**

Status: `rejected_no_uplift`

### Leave-one-event-out

- Baseline + Ticketing MAE: **5,007.3**
- bias-only control MAE: **5,576.6**
- + Match Stakes MAE: **5,734.6**
- uplift vs Baseline + Ticketing: **-727.4**
- incremental sporting uplift vs bias-only: **-158.0**

Status: `rejected_no_uplift`

## Decision

The current heuristic Match Stakes score is **not promoted into the ablation forecast chain**.

`context_ablation_predictions_v1` intentionally contains **0** rows for `baseline_ticketing_sporting`.

This is deliberate. The research framework must be able to reject a feature rather than manufacture a Sporting P50 just because Sporting carries a 30% research-prior weight in Context Matrix.

## What this does not mean

It does **not** mean Sporting Context as a category has no value.

It means the current single-feature Match Stakes heuristic does not improve the forecast on the available sample.

The next Sporting candidate should be considered only after point-in-time coverage improves for:
- `sport.form5` — last five relevant matches across competitions;
- `sport.rivalry_opponent`;
- `sport.absence_impact`;
- future revised Match Stakes representations if justified.

## Automation

The Sporting candidate summary is recomputed internally every 6 hours via:

`sporting_challenger_summary_6h`

This internal job does not send user notifications and does not change P50.

## Dashboard

Model Lab exposes a dedicated Sporting Challenger v1 panel showing:
- Baseline + Ticketing MAE;
- bias-only control;
- + Match Stakes MAE;
- delta vs Ticketing;
- leave-one-event-out and leave-one-club-out results;
- explicit `Current candidate rejected` state.
