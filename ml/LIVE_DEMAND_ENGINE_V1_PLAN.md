# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-15**

## Implementation status

Current position:

> **Phase A — Foundation: COMPLETE after registry PR merge**  
> **Next: Phase B / Step 6 — StructuralPrior adapter**

| Phase | Step | Scope | Status |
|---|---:|---|---|
| A — Foundation | 1 | Canonical LiveTrajectoryFeatureStore | **DONE** |
| A — Foundation | 2 | Exact-cutoff checkpoint/readiness integration | **DONE** |
| A — Foundation | 3 | Robust anomaly / release detection | **DONE** |
| A — Foundation | 4 | Append-only PIT feature evidence store | **DONE** |
| A — Foundation | 5 | Version all live feature contracts | **DONE after registry merge** |
| B — Shadow Forecasting | 6 | StructuralPrior adapter | **NEXT** |
| B — Shadow Forecasting | 7 | Expected trajectory / trajectory gap references | TODO |
| B — Shadow Forecasting | 8 | Persist shadow live forecasts | TODO |
| B — Shadow Forecasting | 9 | Persist first detection + forecast revisions | TODO |
| B — Shadow Forecasting | 10 | Keep live correction shadow-only until evidence is sufficient | TODO |
| C — Learned Correction | 11–14 | Train / evaluate residual live correction | BLOCKED ON EVIDENCE |
| D — Probabilistic | 15–17 | Calibrated P10/P50/P90 live trajectories | TODO |
| E — Recommendations | 18–20 | Action recommendations / intervention learning | LATER |

Canonical live contract registry:

`ml/demand_engine/LIVE_CONTRACT_REGISTRY.md`

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

### 2. Live Trajectory Feature Store

**Foundation implementation: DONE.**

Current feature contract:

`live-trajectory-v1.1`

Canonical implementations:

- Python: `ml/demand_engine/live_trajectory_feature_store.py`;
- DB: `public.get_live_trajectory_features_v1_1_asof`.

For each usable snapshot the store exposes point-in-time features relative to kickoff and prior snapshots for the same event.

#### Core identity / timing

- ticket event / snapshot identity;
- `captured_at` / `as_of_at` / `kickoff_at`;
- days / hours to kickoff;
- T-30 / T-14 / T-7 / T-3 / T-1 checkpoint state.

#### Inventory level

- `available_total`;
- inventory relative to first reliable snapshot;
- public-seat-map normalization;
- optional verified-capacity normalization when capacity is known and appropriate;
- net movement since first observation.

#### Velocity / acceleration

- net movement and velocity over 6h / 24h / 72h / 7d;
- normalized velocity;
- 6h vs 24h acceleration;
- 24h vs 72h acceleration;
- 72h vs 7d acceleration.

#### Sector movement

- matched / entered / left sectors;
- matched absorption;
- matched re-availability;
- coverage inventory effect;
- coverage-change flag.

#### Release / anomaly semantics

Current material matched-sector release threshold:

`max(50 seats, 0.5% of first observed inventory)`

Empirical calibration from the live multi-club sample showed approximately:

- matched-sector release P95 = 18 seats;
- P99 ≈ 40 seats;
- entered-sector inventory P95 = 28 seats;
- positive raw inventory increase P95 = 30 seats.

Therefore tiny returns / toggles are not treated as material releases.

Sector entry / exit is a separate coverage signal and is not conflated with release activity.

A material raw inventory increase without a material matched-sector release or coverage explanation is treated as an anomaly and can downgrade readiness.

#### Quality controls

- raw / clean snapshot count;
- invalid / duplicate snapshot telemetry;
- snapshot age;
- all-history max gap telemetry;
- recent 7-day gap for current-signal readiness;
- stale anchor rejection for short-window velocity;
- explicit point-in-time validation.

Public ticket inventory remains a **demand proxy, not confirmed paid ticket sales**.

### 3. Expected Trajectory Model

Learn the expected sales / inventory curve for a match with a given structural profile.

Important limitation:

The five-season historical attendance dataset contains final attendance and historical context, but not historical ticket-inventory trajectories for all 1,530 matches.

Therefore the first trajectory model must be trained only on events for which real historical/prospective ticketing snapshots exist. Do not fabricate historical sales curves from final attendance.

Expected output:

- expected inventory position;
- expected normalized demand progress;
- expected velocity range;
- expected acceleration range;
- expected final attendance conditional on trajectory if useful.

The expected curve should be normalized where possible so it can generalise across stadium sizes and clubs.

### 4. Trajectory Gap Engine

Compare actual live behaviour with expected behaviour.

Core outputs:

- `trajectory_gap_level`;
- `trajectory_gap_pct`;
- `velocity_gap`;
- `acceleration_gap`;
- sector / coverage context;
- direction: `UNDERPERFORMING / ON_TRACK / OUTPERFORMING`;
- confidence / signal quality.

Do not classify underperformance from inventory level alone. Velocity, acceleration, releases, sector changes and source quality must be considered to avoid false alerts.

### 5. Live Correction Model

Train the live model to predict the residual error of the Structural Prior.

Primary target:

`live_target_residual = actual_attendance - historical_prior_p50`

Candidate predictors:

- trajectory gap;
- normalized inventory position;
- multi-window velocity;
- acceleration;
- sector movement;
- scarcity;
- release / coverage / anomaly flags;
- signal quality;
- days to kickoff;
- selected interactions between structural prior and live evidence.

Core output:

`live_p50 = historical_p50 + predicted_live_correction`

Later probabilistic output:

- `live_p10`;
- `live_p50`;
- `live_p90`.

The historical prior and live correction must remain separable so the incremental value of proprietary live ticketing data is measurable.

### 6. Early Warning Engine

States:

- `ON_TRACK`;
- `UNDERPERFORMING`;
- `OUTPERFORMING`;
- `INSUFFICIENT_SIGNAL`.

Alert payload should include:

- event / match;
- first detected timestamp;
- first detected horizon / days to kickoff;
- current state;
- trajectory gap magnitude;
- expected final impact;
- historical P50;
- live P50;
- P10 / P90 when available;
- confidence;
- reason codes;
- signal-quality state.

The system must preserve **first detection**, not only the current state. Lead time is a core KPI.

## Evaluation Framework

### Final forecast quality

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
- percentage of events improved;
- performance by club and horizon.

### Trajectory quality

- trajectory-gap prediction error;
- forecast revision quality over time;
- whether additional snapshots improve final forecast;
- stability of revisions;
- false correction rate caused by releases / anomalies.

### Early-warning quality

- precision;
- recall;
- false-positive / false-negative rate;
- average / median first-detection lead time;
- percentage correctly detected by T-30 / T-14 / T-7;
- final outcome miss avoided after detection.

Target product KPI:

`Actionable Detection = correct direction + material gap + sufficient lead time`

## Horizon priorities

1. **T-30** — primary planning / intervention horizon;
2. **T-14** — strong intervention / correction horizon;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final forecast / calibration checkpoint.

Model development must not optimise T-1 at the expense of earlier actionable horizons.

## Current live evidence constraint

Canonical readiness source:

`private.ticketing_horizon_readiness_v2_1`

Canonical append-only evidence source:

`private.live_trajectory_feature_snapshots_v1`

After initial exact-cutoff materialization:

| Horizon | Materialized rows | Training-eligible |
|---|---:|---:|
| T-30 | 1 | **0** |
| T-14 | 5 | **3** |
| T-7 | 9 | **3** |
| T-3 | 6 | **2** |
| T-1 | 10 | **5** |

Evidence QA:

- 31 materialized rows;
- 0 post-cutoff source-snapshot leakage violations;
- 0 invalid `as_of_at >= kickoff_at` rows;
- 0 PIT-validation failures;
- 0 feature-version mismatches;
- idempotent replay leaves the evidence row count unchanged.

Consequences:

- T-30 live model training is not statistically credible yet;
- T-14 has only 3 training-eligible exact-checkpoint rows;
- no early-horizon live correction should be promoted from this sample;
- collection continues prospectively while Phase B is built in shadow mode.

A first genuine T-30+ collection case is active:

- Jagiellonia Białystok vs Crystal Palace;
- kickoff: 2026-12-10;
- RoboTicket candidate `5190`;
- mapped `ticket_event_id=24`;
- collection started well before T-30;
- formal T-30 checkpoint remains `not_due` until the exact cutoff.

## Implementation sequence

### Phase A — Foundation — COMPLETE

1. **DONE** — canonical LiveTrajectoryFeatureStore.
2. **DONE** — exact-cutoff horizon readiness; legacy nearest-snapshot v1 is not used for new modelling.
3. **DONE** — robust empirically calibrated anomaly / release semantics.
4. **DONE** — append-only deterministic point-in-time feature evidence store for training and inference lineage.
5. **DONE after registry merge** — version registry for all current live contracts.

### Phase B — Shadow Forecasting — NEXT

6. **NEXT** — add `StructuralPrior` adapter exposing the current historical champion per horizon.
7. Add initial trajectory-gap calculations using descriptive / rule-based expected references where ML evidence is insufficient.
8. Persist shadow live forecasts on every eligible snapshot.
9. Persist first-detection events and forecast revisions.
10. Never auto-promote live correction from a tiny sample.

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
19. Recommendations remain separate from the forecasting truth layer.
20. Eventually learn intervention effectiveness from observed club actions and post-intervention trajectory changes.

## Immediate coding backlog

Current code lives under `ml/demand_engine/`; do not create a duplicate parallel engine unless architecture changes explicitly require it.

1. **NEXT — `StructuralPrior` adapter**
   - wrap the current horizon-specific historical champions;
   - expose one stable request/response contract;
   - persist exact model / feature lineage;
   - no retraining inside the live engine.

2. `trajectory_gap`
   - expected-vs-observed representation;
   - initially permit descriptive / rule-based references when ML evidence is insufficient;
   - versioned gap schema.

3. `shadow_forecast`
   - combine prior + current live evidence;
   - persist shadow predictions and revision history;
   - no production promotion.

4. `early_warning`
   - state classification;
   - first-detection persistence;
   - lead-time measurement;
   - reason codes / confidence.

5. `evaluate_live_engine`
   - historical prior vs live-corrected comparison;
   - horizon-specific MAE / WAPE / bias;
   - early-warning precision / recall / lead time;
   - leave-event-out evaluation when the sample permits.

## Definition of v1 success

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
