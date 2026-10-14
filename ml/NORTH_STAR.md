# Beyond Ticketing — ML North Star

Last updated: **2026-10-14**

## Single objective

Build the **best possible forecasting model** for football ticket demand / final attendance and its evolution over time.

Everything else is secondary.

## What success means

For a match and a point in time before kickoff, Beyond should estimate:

- final attendance / demand outcome;
- expected trajectory as kickoff approaches;
- calibrated uncertainty (P10 / P50 / P90 or equivalent quantiles);
- how the forecast changes when new evidence arrives.

The model should generalise across clubs and matches, not only fit Lech.

## Optimisation target

Primary goal: minimise true out-of-sample forecast error on unseen future matches while maintaining calibrated uncertainty and low systematic bias.

Primary evaluation dimensions:

- MAE;
- WAPE / MAPE where appropriate;
- median absolute error;
- directional bias;
- quantile / pinball loss;
- P10-P90 empirical coverage;
- stability across clubs, seasons and forecast horizons.

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
- no feature or model is kept because it sounds plausible — only because it improves out-of-sample forecasting.

## Priority order

1. Improve the model.
2. Improve the data and features available to the model.
3. Improve evaluation and uncertainty calibration.
4. Collect new prospective evidence in parallel.
5. Only then optimise product presentation around the model.

Investor demo, Growth, Weather, Hype, promotion gates and dashboard features are not independent goals. They matter only insofar as they improve the forecast, prove the forecast, or communicate the forecast.

## Current strategic rule

Do not wait for new matches when usable historical data already exists.

Use historical data aggressively for model R&D now. Use future matches only for evidence that genuinely requires prospective observation, such as live inventory trajectories or prospective-only Hype signals.

**The north star is predictive quality.**
