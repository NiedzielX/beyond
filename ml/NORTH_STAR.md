# Beyond Ticketing — ML North Star

Last updated: **2026-10-15**

## Single objective

Build the **best possible live forecasting system** for football ticket demand / final attendance and its evolution over time.

The model must use both:

- historical evidence from past matches;
- current point-in-time evidence from the match being sold now.

Everything else is secondary.

## What Beyond must predict

For every active match and every point in time before kickoff, Beyond should estimate:

1. **Final demand / attendance** — where this match is currently expected to finish.
2. **Expected demand trajectory** — how sales / public inventory should evolve from now until kickoff if the match behaves normally given its historical and contextual profile.
3. **Observed trajectory** — what is actually happening now in the live ticketing signal.
4. **Trajectory gap** — whether the match is selling materially better or worse than it should at this point in time.
5. **Future trajectory** — how the gap is expected to evolve if nothing changes.
6. **Calibrated uncertainty** — P10 / P50 / P90 or equivalent quantiles around the final outcome and trajectory.
7. **Reason codes / drivers** — which evidence moved the forecast or caused the match to be classified as above / below expectation.

The core question is not only:

> How many people will attend?

It is also:

> Given what similar matches historically did and what this match is doing right now, is demand evolving as expected — and where is it heading?

## Product value

Beyond should detect a meaningful demand problem or opportunity **early enough for the club to act**.

Examples:

- a match is selling materially slower than comparable matches should at T-30;
- demand was healthy at T-30 but deteriorates relative to expectation at T-14;
- a campaign changes ticketing velocity and moves the forecast upward;
- a match is outperforming its historical potential, creating a pricing / inventory / communication opportunity.

Therefore **T-30 and T-14 are primary business horizons**, even if T-3 or T-1 eventually achieve lower absolute error.

## Model architecture target

The intended forecasting stack is:

### 1. Structural historical prior

Estimate expected final demand and expected trajectory from information available before live sales evidence is considered, including:

- home-club demand history;
- opponent draw / attractiveness;
- stadium capacity / expected occupancy;
- seasonality and kickoff timing;
- sporting state and match importance;
- competition / event context;
- other validated point-in-time context features.

### 2. Live trajectory model

Continuously interpret current ticketing evidence, including where available:

- public inventory level;
- inventory index relative to the event's starting state / comparable events;
- velocity over multiple windows;
- acceleration / deceleration;
- sector-level movement;
- scarcity / sell-out pressure;
- release / replenishment activity;
- anomalies and source-quality flags.

### 3. Residual / trajectory correction

Compare observed live behaviour with the expected historical trajectory and estimate the correction to the structural prior.

Conceptually:

`live forecast = historical prior + trajectory correction`

The correction should answer:

> Is this match currently performing better or worse than its expected demand curve, by how much, and what does that imply for final attendance?

## Optimisation target

Primary goal: minimise true out-of-sample error on unseen future matches **while maximising useful lead time**.

Predictive quality and early actionability are both first-class objectives.

A model that reaches 1,000 MAE at T-1 but cannot identify a demand problem until the final day may be less valuable than a model with 1,400 MAE at T-30 that reliably identifies the problem four weeks earlier.

## Primary evaluation dimensions

### Final-outcome accuracy

- MAE;
- WAPE / MAPE where appropriate;
- median absolute error;
- directional bias;
- stability across clubs, seasons and horizons.

### Probabilistic quality

- quantile / pinball loss;
- P10-P90 empirical coverage;
- interval width and calibration.

### Live trajectory quality

- forecast error of the expected trajectory at each horizon;
- error in predicted final demand after each live update;
- stability / revision quality between successive forecasts;
- incremental uplift from live signals over the historical prior.

### Early-warning quality

For materially underperforming / outperforming matches:

- detection precision;
- detection recall;
- false-alarm rate;
- average first-detection lead time;
- percentage detected by T-30 / T-14 / T-7;
- magnitude of final miss avoided by the alert.

The system should eventually support an explicit metric such as:

`actionable detection = correct direction + material gap + sufficient lead time`

## Horizon priority

Business priority:

1. **T-30** — planning and major intervention window;
2. **T-14** — strong intervention / correction window;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final forecast / calibration checkpoint.

All horizons matter, but model R&D must not optimise T-1 at the expense of T-30 / T-14 usefulness.

## Non-negotiable methodology

- strict point-in-time features;
- no future leakage;
- chronological / walk-forward validation;
- untouched holdout data;
- cross-club validation;
- reproducible feature and model versions;
- one canonical Feature Store for training and inference;
- challenger vs champion comparisons under the same protocol;
- ablation of feature families;
- historical and live-signal contributions measured separately;
- no feature or model is kept because it sounds plausible — only because it improves out-of-sample forecasting or earlier reliable detection.

## Priority order

1. Improve T-30 / T-14 historical prior accuracy.
2. Build and validate the live trajectory / expected-vs-observed gap model.
3. Improve later-horizon point accuracy where it also supports calibration and final outcome quality.
4. Build calibrated P10 / P50 / P90 trajectories.
5. Learn which interventions actually improve demand only after the forecast and early-warning layer is trustworthy.
6. Product presentation, recommendation UI and Growth are downstream of the predictive core.

## Current strategic rule

Do not wait for new matches when usable historical data already exists.

Use historical data aggressively for structural-model R&D now. Use future matches for evidence that genuinely requires prospective observation, especially live ticketing trajectories and intervention-response evidence.

**The north star is not simply the lowest MAE. It is the earliest reliable prediction of where demand is heading and whether the current match is performing better or worse than it should.**
