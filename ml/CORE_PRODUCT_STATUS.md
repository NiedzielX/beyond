# Beyond Ticketing — Core Product Status

Last verified: **2026-10-14**  
Purpose: canonical source of truth for the forecasting core. If another ML document conflicts with this file, this file wins until it is explicitly superseded.

> **North star:** build the best possible point-in-time model for final football attendance / ticket demand and its evolution toward kickoff. Predictive quality is the objective. Product features, Growth, Weather, Hype and evidence gates matter only when they improve, validate or communicate the forecast.

## Executive state

Beyond now has a credible **global historical forecasting core**, not only a Lech-specific model.

Current state:

- historical Ekstraklasa ground truth: **1,530 matches / 5 complete seasons (2021/22–2025/26)**;
- 306 matches per season;
- 2021/22–2024/25 historical layer independently reconciled against a pinned schedule/result reference;
- one verified closed-doors match is retained as historical ground truth but excluded from default demand-model training;
- canonical multi-season point-in-time feature artifact: **7,650 snapshots** (`1,530 matches × 5 horizons`);
- horizons: **T-30d, T-14d, T-7d, T-3d, T-1d**;
- current historical research champion candidate: **Global Model v2.1**;
- architecture: **fixed club-history baseline + learned residual correction**;
- selected model families: **HistGradientBoosting / XGBoost**, selected independently by horizon;
- Global Model v2.1 improves MAE over the club-history baseline on **every horizon and both later seasons**;
- v1.7 T-7 runtime recovery was already reconstructed and numerically verified in CI; it is no longer an unknown/missing artifact;
- the production/live runtime is still separate from Global Model v2.1; v2.1 has **not** been promoted automatically;
- Live Ticketing remains a separate prospective correction study with **8/20** eligible completed events in the existing promotion gate;
- the 20-event Live Ticketing gate does **not** block historical model R&D.

## Global Model v2.1 — current result

### Evaluation protocol

Model-family selection is separated from final historical holdouts:

1. candidate models train on **2021/22 + 2022/23**;
2. model family is selected on **2023/24 only**;
3. selected family is refit through 2023/24 and evaluated on **2024/25**;
4. the same selected family is refit through 2024/25 and evaluated on **2025/26**;
5. every feature is computed only from information available before the snapshot `as_of_at`;
6. the target match outcome never enters its own feature state.

This is a season-blocked, point-in-time protocol. Random train/test split is not accepted as headline evidence.

### Holdout results

| Horizon | Selected model | 2024/25 baseline MAE | 2024/25 model MAE | Improvement | 2025/26 baseline MAE | 2025/26 model MAE | Improvement |
|---|---|---:|---:|---:|---:|---:|---:|
| T-30d | HistGradientBoosting | 2,491.3 | **2,092.6** | **16.0%** | 2,633.5 | **2,061.5** | **21.7%** |
| T-14d | XGBoost | 2,436.1 | **1,998.5** | **18.0%** | 2,508.4 | **1,979.6** | **21.1%** |
| T-7d | HistGradientBoosting | 2,340.0 | **1,800.5** | **23.1%** | 2,429.1 | **1,896.4** | **21.9%** |
| T-3d | HistGradientBoosting | 2,316.6 | **1,785.3** | **22.9%** | 2,397.5 | **1,851.7** | **22.8%** |
| T-1d | HistGradientBoosting | 2,297.5 | **1,749.6** | **23.8%** | 2,396.9 | **1,833.7** | **23.5%** |

Interpretation: the global historical feature set contains a meaningful predictive signal beyond a reasonable club-specific attendance-history baseline. The improvement is not confined to one horizon or one holdout season.

## Current model architecture

For a match at a forecast checkpoint:

`Point-in-time historical state`

→ `club-history baseline`

→ `global residual model`

→ `historical P50 candidate`

→ later: `validated live-ticket correction`

→ later: `calibrated P10 / P50 / P90`

The historical model and live-ticket signal are deliberately separate layers. Historical model development can use the large archive now; live-ticket uplift must continue to be validated prospectively.

## Current baseline

The historical fixed baseline is point-in-time and hierarchical:

1. if at least 5 prior home matches exist: rolling-5 home attendance;
2. otherwise: available historical home mean;
3. otherwise: current-season league median;
4. otherwise: previous-season / prior league median fallback.

The learned model predicts the **residual error** of this baseline rather than replacing it blindly.

Residual architecture currently generalises better than the tested direct-attendance challengers.

## Feature Store v2.1

The multi-season feature artifact contains **7,650 point-in-time snapshots**.

### Attendance / home-demand history

- historical home attendance mean / median / last;
- rolling 3 / 5 / 10 home attendance;
- attendance dispersion / upper historical level;
- current-season home attendance state;
- previous-season home mean;
- days since previous home match;
- recent home trend vs long-run home mean;
- home demand level relative to league median.

### Opponent demand

- opponent historical draw across all home clubs;
- opponent recent draw vs long-run draw;
- previous-season opponent demand;
- exact **home–opponent pair history**;
- pair attendance vs the host club's normal demand.

### Timing / seasonality

- round;
- season progress;
- month;
- weekday;
- kickoff time;
- weekend flag;
- cyclical date/time encodings.

### Sporting state

Reconstructed from matches completed before `as_of_at` in the current season:

- matches played;
- points / PPG;
- goal-difference rate;
- last-5 form;
- rest days;
- fixture congestion;
- table position;
- home-away PPG / position / form gaps.

### Future feature families

Weather, Hype and live ticket inventory are **challenger feature families**, not separate product goals. They enter P50 only if they reduce out-of-sample error under the same point-in-time benchmark.

## Feature ablation — current signal

T-7 ablation indicates:

- removing attendance-history features materially worsens MAE;
- removing calendar / seasonality worsens MAE;
- removing sporting-state features worsens MAE, especially on 2024/25;
- opponent context provides smaller but still useful incremental signal;
- richer home–opponent pair history and recent-vs-long-run demand trends produced the material v2 → v2.1 improvement.

The current conclusion is therefore **more predictive information > more decorative model complexity**.

## Model families tested

Historical / global work has now tested or documented:

- rolling attendance baselines;
- opponent historical baselines;
- Ridge / Elastic Net;
- Huber robust regression;
- Gradient Boosting;
- HistGradientBoosting;
- Extra Trees;
- Random Forest;
- XGBoost;
- LightGBM;
- CatBoost;
- direct attendance targets;
- residual targets;
- log-ratio targets;
- simple family-diverse ensembles;
- earlier Lech-specific v1.3–v1.8 model generations.

### Rejected current challengers

Against the five-season Global Model v2 research setup, the following did not justify replacing the residual HistGBR/XGB architecture:

- raw CatBoost residual model;
- CatBoost direct attendance;
- CatBoost log-attendance;
- HistGradientBoosting direct attendance;
- XGBoost direct attendance;
- log-ratio residual targets;
- simple CatBoost / HistGBR / XGB ensembles selected on development MAE.

Some looked marginally better on development data but did not improve consistently on later seasons.

## The 12 questions we should always know

### 1. What is the best historical model today?

**Global Model v2.1 research champion candidate.**

It uses a point-in-time club-history baseline plus a learned residual correction. HistGradientBoosting wins T-30/T-7/T-3/T-1; XGBoost wins T-14 under the current development protocol.

### 2. What is the training population?

**1,530 complete Ekstraklasa matches across 2021/22–2025/26.**

The model no longer depends only on Lech history.

### 3. Do we have a Feature Store?

We now have a **canonical v2 point-in-time contract** and a five-season v2.1 feature artifact containing **7,650 snapshots**.

The legacy public `ml_feature_snapshots` table is not the canonical global store. A private v2 schema exists for canonical historical/live snapshots; full database materialisation of the five-season artifact is operational work and must not be confused with whether the feature definitions exist.

### 4. What is the target?

Current historical target: **final match attendance**.

Live public inventory remains a demand/sales proxy, not guaranteed ticket sales. Do not label changes in public inventory as confirmed sales without club transaction data.

### 5. What are the forecast horizons?

Current historical matrix:

- T-30d;
- T-14d;
- T-7d;
- T-3d;
- T-1d.

### 6. How is validation handled?

Season-blocked and point-in-time:

- 2021/22 + 2022/23 train candidate families;
- 2023/24 selects the family;
- 2024/25 and 2025/26 are later historical holdouts for the frozen v2.1 experiment;
- all attendance/sporting/context features are restricted to information known before `as_of_at`.

For new iterations, avoid repeatedly tuning against the same historical holdouts. New challenger decisions must increasingly rely on rolling-season CV and genuinely future 2026/27 evidence.

### 7. What is current MAE by horizon?

On 2025/26:

- T-30d: **2,061.5**;
- T-14d: **1,979.6**;
- T-7d: **1,896.4**;
- T-3d: **1,851.7**;
- T-1d: **1,833.7**.

On 2024/25:

- T-30d: **2,092.6**;
- T-14d: **1,998.5**;
- T-7d: **1,800.5**;
- T-3d: **1,785.3**;
- T-1d: **1,749.6**.

### 8. How much does the global model beat the baseline?

Across the two later seasons and all five horizons: roughly **16–24% MAE improvement**.

The best relative improvements are around T-7/T-3/T-1.

### 9. What does the Live Ticketing challenger prove?

Separately from Global Model v2.1, the current T-24 Live Ticketing study shows a positive but still small prospective signal:

- LOCO baseline MAE: about 5,266;
- bias-only control: about 5,174;
- ticketing challenger: about 5,007;
- current evidence set: **8 eligible completed events / 6 clubs**.

It supports continued collection, not production promotion yet.

### 10. Do we need to wait for 20 new matches before improving the model?

**No.**

The 20-event gate applies to prospective Live Ticketing promotion evidence only. Historical/global model R&D uses the multi-season archive immediately.

### 11. Are Weather / Hype / Sporting automatically part of P50?

No.

Sporting state is currently useful inside Global Model v2.1 under the new five-season point-in-time feature contract. Earlier, separate Sporting/Match Context challengers against the small live-ticket study were rejected; these are different experiments and must not be conflated.

Weather and Hype remain challenger families and require controlled ablation / future evidence before inclusion.

### 12. What is the next modelling priority?

1. reproduce Global Model v2.1 end-to-end in CI from canonical historical inputs;
2. freeze v2.1 as the historical research champion;
3. build calibrated P10/P50/P90 around the stronger point model;
4. measure incremental live-ticket uplift **over v2.1**, not over the old weak baseline;
5. test Weather and Hype against v2.1 with the same leakage-safe protocol;
6. use 2026/27 future fixtures as prospective evidence for new challengers.

## Immediate priority

Do **not** spend the next sprint on Growth or additional product surfaces.

The next milestone is:

> **Global Model v2.1 → reproducible CI → probabilistic forecast → live-ticket incremental uplift over the new historical champion.**

## Supporting evidence

Primary current benchmark report: `ml/results/GLOBAL_MODEL_V2_2026-10-14.md`.

Reproducible benchmark runner on the model branch: `ml/global_model_v21_benchmark.py`.
