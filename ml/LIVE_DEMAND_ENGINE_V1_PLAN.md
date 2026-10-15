# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-15**

## Purpose

Build the live forecasting core that combines historical match evidence with current ticketing behaviour to answer two questions continuously before kickoff:

1. **Where is this match currently expected to finish?**
2. **Is demand evolving better or worse than it should at this point in time?**

The goal is not only to minimise final attendance MAE. The system must detect meaningful underperformance or outperformance **early enough for the club to act**, especially at **T-30 and T-14**.

## Product hypothesis

Historical data tells us what a comparable match **should** do.

Live ticketing data tells us what the current match **is actually doing**.

Beyond should learn the gap between those two trajectories and translate it into:

- an updated final attendance / demand forecast;
- calibrated uncertainty;
- an early warning when the match is materially ahead or behind expectation;
- an explanation of the main drivers.

Conceptually:

`Live Forecast(t) = Structural Historical Prior(t) + Live Trajectory Correction(t)`

and

`Trajectory Gap(t) = Observed Live Trajectory(t) - Expected Trajectory(t)`

## Target architecture

### 1. Structural Prior

Freeze the current historical champion per horizon as the baseline input to the live engine.

Current historical stack is multi-club, leakage-safe, point-in-time and trained across five seasons.

The Structural Prior should expose, at minimum:

- `match_key`;
- `horizon`;
- `as_of_at`;
- `historical_p50`;
- later: `historical_p10` / `historical_p90`;
- verified stadium capacity;
- expected occupancy;
- main historical/context drivers;
- model version and feature-set version.

Historical prior inputs currently include validated families such as:

- home-club attendance history;
- opponent draw / attractiveness;
- verified stadium capacity / occupancy;
- timing / seasonality;
- sporting state;
- match importance / quality interactions where validated;
- club identity as a lower-weight contextual family.

The live engine must not retrain or redefine the Structural Prior ad hoc. It consumes a versioned historical forecast.

## 2. Live Trajectory Feature Store

Build one canonical point-in-time feature layer from raw ticketing snapshots.

For every usable snapshot, calculate features relative to kickoff and to prior snapshots for the same event.

### Core identity / timing

- `ticket_event_id`;
- `snapshot_id`;
- `captured_at`;
- `kickoff_at`;
- `days_to_kickoff`;
- `hours_to_kickoff`;
- nearest business checkpoint: T-30 / T-14 / T-7 / T-3 / T-1;
- checkpoint distance / readiness.

### Inventory level

- `available_total`;
- `available_share_of_capacity`;
- `inventory_index_vs_first_reliable_snapshot`;
- `net_removed_since_first`;
- `estimated_public_occupancy_proxy` where defensible;
- scarcity / near-sellout indicators.

### Velocity

At minimum:

- net removed over 6h;
- net removed over 24h;
- net removed over 72h;
- net removed over 7d;
- velocity over 6h / 24h / 72h / 7d;
- rolling velocity stability.

### Acceleration / deceleration

- 6h vs 24h acceleration;
- 24h vs 72h acceleration;
- 72h vs 7d acceleration;
- sustained acceleration / slowdown flags.

### Sector movement

Where sector-level data is available:

- active sector count;
- sector coverage ratio;
- sector additions / removals;
- concentration of remaining inventory;
- sector sellout sequence;
- sudden sector reopenings;
- sector-level velocity.

### Release / replenishment behaviour

- release activity flag;
- replenishment magnitude;
- sector coverage change flag;
- newly exposed inventory;
- temporary inventory spikes;
- suspected operational release vs real demand movement.

### Quality / anomaly controls

- raw snapshot count;
- clean snapshot count;
- anomaly count;
- gap since previous snapshot;
- source quality / readiness;
- duplicated / stale snapshot protection;
- abnormal inventory increase flags;
- whether velocity features are trustworthy at the current point.

No live feature may use information captured after its `as_of_at`.

## 3. Expected Trajectory Model

Learn the expected sales / inventory curve for a match with a given structural profile.

Important limitation:

The five-season historical attendance dataset contains final attendance and historical context, but not historical ticket-inventory trajectories for all 1,530 matches.

Therefore the first trajectory model must be trained only on events for which real historical/prospective ticketing snapshots exist. Do not fabricate historical sales curves from final attendance.

### Expected output

For a match and timestamp, estimate:

- expected inventory position;
- expected normalized demand progress;
- expected velocity range;
- expected acceleration range;
- expected final attendance conditional on trajectory if useful.

The expected curve should be normalized where possible so it can generalise across stadium sizes and clubs, for example using:

- capacity / occupancy;
- inventory relative to first reliable snapshot;
- percentage of expected demand captured by each horizon.

## 4. Trajectory Gap Engine

Compare actual live behaviour with the expected trajectory.

Core outputs:

- `trajectory_gap_level`;
- `trajectory_gap_pct`;
- `velocity_gap`;
- `acceleration_gap`;
- `sector_gap`;
- direction: `UNDERPERFORMING / ON_TRACK / OUTPERFORMING`;
- confidence / signal quality.

Example interpretation:

- historical model expects a final attendance around 24,500;
- comparable matches normally show a stronger trajectory at T-30;
- current event is materially behind that trajectory;
- current velocity is also below expectation;
- estimated final demand is revised downward.

Do not classify underperformance from inventory level alone. Velocity, acceleration, releases, sector changes and source quality must be considered to avoid false alerts.

## 5. Live Correction Model

Train the live model to predict the residual error of the Structural Prior.

Primary target:

`live_target_residual = actual_attendance - historical_prior_p50`

Candidate live predictors:

- trajectory gap;
- normalized inventory position;
- multi-window velocity;
- acceleration;
- sector movement;
- scarcity;
- release / replenishment flags;
- signal quality;
- days to kickoff;
- selected interaction terms between structural prior and live evidence.

Core output:

`live_p50 = historical_p50 + predicted_live_correction`

Later probabilistic output:

- `live_p10`;
- `live_p50`;
- `live_p90`.

The historical prior and live correction must be evaluated separately so the incremental value of proprietary live ticketing data is measurable.

## 6. Early Warning Engine

The live forecast alone is not enough. The system must also determine whether a club should care now.

### States

- `ON_TRACK`;
- `UNDERPERFORMING`;
- `OUTPERFORMING`;
- `INSUFFICIENT_SIGNAL`.

### Alert payload

At minimum:

- event / match;
- first detected timestamp;
- first detected horizon / days-to-kickoff;
- current state;
- trajectory gap magnitude;
- expected final impact;
- historical P50;
- live P50;
- P10 / P90 when available;
- confidence;
- reason codes;
- signal-quality state.

The system should preserve **first detection**, not only the current status. Lead time is a core KPI.

## 7. Evaluation Framework

### Final forecast quality

Continue measuring:

- MAE;
- median absolute error;
- WAPE / MAPE where appropriate;
- RMSE;
- bias;
- stability by club / season / horizon.

### Incremental live uplift

For the same completed event and checkpoint compare:

1. historical prior error;
2. historical prior + live correction error.

Report:

- MAE uplift;
- WAPE uplift;
- bias change;
- number / percentage of events improved;
- performance by club and horizon.

### Trajectory quality

Measure:

- trajectory gap prediction error;
- forecast revision quality over time;
- whether additional snapshots improve the final forecast;
- stability of forecast revisions;
- false correction rate caused by releases or source anomalies.

### Early-warning quality

For materially underperforming / outperforming events measure:

- precision;
- recall;
- false-positive rate;
- false-negative rate;
- average first-detection lead time;
- median first-detection lead time;
- percentage correctly detected by T-30;
- percentage correctly detected by T-14;
- percentage correctly detected by T-7;
- final outcome miss avoided after detection.

Target product KPI concept:

`Actionable Detection = correct direction + material gap + sufficient lead time`

## 8. Horizon Priorities

Business priority is not identical to forecast-error priority.

1. **T-30** — primary planning / intervention horizon;
2. **T-14** — strong intervention / correction horizon;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final forecast / calibration checkpoint.

Model development must not optimise T-1 at the expense of earlier actionable horizons.

## 9. Current Evidence Constraint

As of 2026-10-15, the live dataset is still small at early horizons.

Canonical readiness source:

`private.ticketing_horizon_checkpoint_readiness_v1`

Current coverage across tracked events:

| Horizon | Ready events | Completed ready events |
|---|---:|---:|
| T-30 | 1 | 0 |
| T-14 | 7 | 3 |
| T-7 | 9 | 3 |
| T-3 | 11 | 5 |
| T-1 | 10 | 9 |

Consequences:

- T-30 live model training is not yet statistically credible;
- T-14 has retrospective signal but only 3 completed events with usable checkpoint + outcome;
- no model should be promoted from these tiny samples;
- collection must continue prospectively while the architecture and feature computation are implemented now.

A first genuine T-30+ collection case is already active:

- Jagiellonia Białystok vs Crystal Palace;
- kickoff: 2026-12-10;
- RoboTicket candidate `5190`;
- mapped ticket event ID `24`;
- collection activated well before T-30.

## 10. Implementation Sequence

### Phase A — Foundation

1. Implement canonical `LiveTrajectoryFeatureStore`.
2. Reuse / integrate `private.ticketing_horizon_checkpoint_readiness_v1`.
3. Add robust anomaly / release detection.
4. Create deterministic point-in-time feature snapshots suitable for both training and inference.
5. Version all live feature contracts.

### Phase B — Shadow Forecasting

6. Add `StructuralPrior` adapter exposing the current historical champion forecast per horizon.
7. Add initial trajectory-gap calculations using descriptive / rule-based expected references where ML evidence is insufficient.
8. Persist shadow live forecasts on every eligible snapshot.
9. Persist first-detection events and forecast revisions.
10. Never auto-promote the live correction from a tiny sample.

### Phase C — Learned Trajectory Correction

11. Once sufficient completed events exist, train the first residual correction model.
12. Compare against the same historical prior on identical events / horizons.
13. Use chronological / leave-event-out / leave-club-out validation as sample size permits.
14. Promote only if live signals add stable out-of-sample uplift.

### Phase D — Probabilistic Live Forecast

15. Add calibrated P10 / P50 / P90 trajectory forecasts.
16. Evaluate pinball loss and interval coverage.
17. Calibrate uncertainty separately by horizon if required.

### Phase E — Recommendations

18. Only after forecasting and early-warning reliability are proven, connect detection state to recommendations.
19. Recommendations must remain separate from the forecasting truth layer.
20. Eventually learn intervention effectiveness from observed club actions and post-intervention trajectory changes.

## 11. Immediate Coding Backlog

Highest-priority code now:

1. `ml/live/live_trajectory_feature_store.py`
   - deterministic snapshot-to-features transformation;
   - multi-window velocity / acceleration;
   - capacity-normalized inventory;
   - sector / release / quality features.

2. `ml/live/structural_prior.py`
   - adapter around the current historical champion contracts;
   - standard output schema for live consumption.

3. `ml/live/trajectory_gap.py`
   - expected-vs-observed representation;
   - initially support non-ML references if evidence is insufficient;
   - versioned gap schema.

4. `ml/live/shadow_forecast.py`
   - combine prior + current live evidence;
   - persist shadow predictions and revision history;
   - no production promotion.

5. `ml/live/early_warning.py`
   - state classification;
   - first detection persistence;
   - lead-time measurement;
   - reason codes and confidence.

6. `ml/live/evaluate_live_engine.py`
   - historical prior vs live-corrected comparison;
   - horizon-specific MAE / WAPE / bias;
   - early-warning precision / recall / lead time;
   - leave-event-out evaluation when the sample permits.

## 12. Definition of v1 Success

Live Demand Engine v1 is successful when it can, on completed unseen events:

1. reproduce a versioned historical prior;
2. construct a leakage-safe live trajectory from raw ticketing snapshots;
3. identify whether the event is ahead / on track / behind expected behaviour;
4. update the final forecast without using future data;
5. demonstrate incremental value over the historical prior;
6. record when a problem / opportunity was first detectable;
7. provide calibrated uncertainty once sufficient evidence exists.

The long-term goal is stronger than simply reaching a lower T-1 MAE.

**Beyond should reliably detect where demand is heading, explain whether the current match is behaving better or worse than expected, and do so early enough for the club to act.**
