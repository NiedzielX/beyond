# Beyond Ticketing — C1 Model Tournament v1

Status: **canonical C1-alpha training plan / start now**  
Effective: **2026-10-16**

## Decision

Do not wait for more matches before training C1-alpha.

Use the completed events and their full pre-kickoff live trajectories already present in Supabase. The current sample is treated as a small number of independent events with many timestamped observations per event — not as only 10 rows, and not as thousands of independent matches.

The objective is simple:

> **Find the model that produces the lowest honest event-level MAE versus the current Structural Prior, using only point-in-time live information.**

No model family is preferred in advance. The winner is selected by validation performance and stability.

## Current evidence available

At the time this plan was defined, the live database contained approximately:

- 10 completed ticket events with actual attendance;
- ~1,585 pre-kickoff snapshots across those events;
- >24,000 sector-inventory rows across the richer recent events;
- existing point-in-time trajectory features and outcome data;
- an earlier `Ticketing Challenger v1` that already showed a positive signal on a smaller 8-event dataset.

These figures are dynamic and should be re-queried before each training run.

## Core modelling strategy

Do **not** predict final attendance from zero unless used as a benchmark.

Primary target:

`live_residual = actual_attendance - structural_prior_p50`

Preferred normalized alternative for comparison:

`live_residual_occupancy = actual_attendance / capacity - structural_prior_p50 / capacity`

Final live forecast:

`live_p50 = structural_prior_p50 + predicted_live_residual`

The Structural Prior is the incumbent. A live model must prove that it improves it.

## Training unit

The modelling dataset is conceptually:

`event x as_of_timestamp`

Each row represents what Beyond knew at a real timestamp before kickoff.

Rows may come from:

- canonical checkpoint rows;
- regularized trajectory samples, e.g. one observation every 6h;
- event-level live trajectory features;
- sector-level aggregates available at that timestamp.

## Independence rule — non-negotiable

Snapshots from the same event are **not independent validation examples**.

All rows from one event must stay together in the same fold.

Primary validation:

`Leave-One-Event-Out (LOEO)`

For N completed events:

- train on N-1 whole events;
- predict the held-out whole event;
- calculate the event-level final forecast error;
- repeat for every event.

Do not use random row-level train/test split.

Where club diversity permits, also report:

`Leave-One-Club-Out (LOCO)`

## Event weighting

A match with 250 snapshots must not count as 5x more independent evidence than a match with 50 snapshots merely because scraping started earlier.

Use at least one of:

1. equal total weight per event;
2. regularized sampling cadence, default candidate = one row per 6h;
3. both.

Model selection must report which weighting/sampling contract was used.

## Initial feature set

Start small and PIT-safe.

### Structural anchor

- Structural Prior P50;
- Structural Prior expected occupancy;
- horizon / days to kickoff;
- stadium capacity.

### Live inventory / trajectory

- current normalized inventory / availability;
- 6h velocity;
- 24h velocity;
- 72h velocity;
- 7d velocity;
- acceleration;
- trajectory gap;
- observed progress;
- expected progress;
- signal readiness / confidence;
- feature quality.

### Sector-derived aggregates

Where sector data exists at the same PIT timestamp:

- number/share of underperforming sectors;
- number/share of outperforming sectors;
- worst sector gap;
- median sector gap;
- sector-gap dispersion;
- sector absorption / sell-through proxy;
- sector velocity dispersion;
- concentration of remaining availability;
- release / replenishment activity;
- sector coverage changes.

### Context

Only point-in-time context already in the Structural Prior/live contract may be added initially. Avoid uncontrolled feature explosion.

## Missing values

Do not discard an entire event merely because one velocity window is unavailable.

C1-alpha must be **missing-aware**.

Allowed approaches:

- explicit missing indicators;
- median/robust imputation inside each training fold;
- tree models with appropriate missing-value handling;
- feature-specific availability flags.

A missing 7d velocity on a short trajectory is information; it is not proof that the event is unusable.

## Model tournament v1

Run a focused leaderboard.

### Baselines

1. **Structural Prior only / zero correction** — incumbent benchmark;
2. **Bias-only correction** — training-fold mean/median residual;
3. simple trajectory extrapolation benchmark.

### Linear / robust models

4. Ridge;
5. ElasticNet;
6. HuberRegressor.

### Non-linear models

7. HistGradientBoostingRegressor with strong regularization;
8. shallow XGBoost, if dependency is available and pinned;
9. shallow LightGBM, if dependency is available and pinned;
10. constrained ExtraTrees / RandomForest.

Do not create a huge hyperparameter search. Use a small predeclared grid appropriate to small-N data.

## Statistical time-series challengers

ETS / Holt / Theta / low-order ARIMA may be tested as **trajectory extrapolation benchmarks or feature generators**.

They are not assumed to be the final model because Beyond has multiple events, irregular snapshot histories, cross-event context and sector features rather than one long homogeneous time series.

A useful pattern is:

`statistical trajectory projection -> feature -> residual regression model`

## Validation metrics

Primary selection metric:

**event-level MAE of final attendance**

Always report:

- Structural Prior MAE;
- candidate Live MAE;
- absolute uplift = `prior_error - live_error`;
- relative MAE improvement;
- median absolute error;
- bias;
- event improvement rate;
- worst-event degradation;
- LOEO fold results individually.

Where capacity normalization is used, report occupancy error as a secondary metric.

## Model selection rule

First milestone:

> Candidate must beat Structural Prior MAE under honest LOEO validation.

Aggressive R&D target:

- Live MAE < 1,700;
- stretch target < 1,500.

These are targets, not guaranteed results.

Do not promote a model solely because aggregate MAE is lower if one or two held-out events suffer catastrophic degradation. Stability matters.

## Continuous model vs horizon-specific models

Start with a **single continuous live-correction model** using `days_to_kickoff` / horizon as a feature.

Reason:

- maximizes the amount of training evidence;
- avoids fragmenting a small event sample into five tiny datasets;
- can learn how the correction evolves over time.

After the continuous model is benchmarked, compare it with horizon-specific models only if the evidence supports splitting.

## Structural Prior compatibility

The tournament baseline must use the **current Structural Prior generation**, not legacy `beyond-forecast-v0.1`.

The historical/live replay dataset must therefore contain, for every usable event/timestamp:

- current-compatible Structural Prior P50 or a reproducible historical replay of it;
- exact model/feature lineage;
- PIT cutoff semantics.

If an event cannot receive a valid current-compatible Structural Prior because it is outside model domain, do not silently substitute a legacy forecast. Mark the baseline source explicitly and exclude it from the primary C1 leaderboard if necessary.

## Existing Ticketing Challenger v1

`ml/TICKETING_CHALLENGER_V1.md` is prior evidence, not the final C1 model.

It demonstrated that live ticketing features could add signal under small-N grouped validation.

C1 Model Tournament v1 extends this idea by:

- using the current Structural Prior as incumbent;
- using full trajectories rather than one T-24h row;
- adding sector-derived signals;
- using missing-aware features;
- evaluating a controlled model leaderboard.

## 20-match rule

The 20-independent-completed-match rule is **not a training-start gate**.

It remains a later governance/promotion threshold for calling a learned live correction sufficiently validated for normal production promotion.

C1-alpha may be trained, compared and run in experimental/shadow mode on the existing completed-event evidence now.

## Implementation sequence

1. build versioned `C1_ALPHA_TRAINING_DATASET_V1` from existing completed events;
2. reconstruct current-compatible Structural Prior anchors for usable historical live events;
3. sample/weight trajectory rows so every event has equal validation importance;
4. add sector aggregates PIT-safely;
5. run LOEO leaderboard;
6. report Structural Prior vs every challenger;
7. select the simplest stable MAE winner;
8. freeze exact spec and dependency versions;
9. run it as `C1-alpha` experimental/shadow on current events;
10. keep accumulating evidence, but do not block initial development on future matches.

## Non-negotiable anti-overfitting rules

- no random snapshot split;
- no future snapshots in a training row;
- no target-event outcome-derived features;
- no treating thousands of snapshots as thousands of independent matches;
- no huge hyperparameter sweep;
- no silent legacy baseline substitution;
- no tuning to a held-out event after seeing its error within the same candidate version;
- every experiment stores its dataset/model/feature version.

## One-line operating rule

> **Use every PIT-valid observation we already have, but judge every model by how well it predicts an entirely unseen match.**
