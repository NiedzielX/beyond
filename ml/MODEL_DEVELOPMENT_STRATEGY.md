# Beyond Ticketing — Model Development Strategy

Last updated: **2026-10-14**

## Core decision

Beyond model development must not wait for the 20-event prospective Live Ticketing gate.

There are two parallel evidence tracks:

### Track A — Historical model R&D (start immediately)

Purpose: build the strongest leakage-safe attendance-demand baseline using the large historical match dataset already available.

This track can iterate now using historical matches and does **not** depend on collecting 20 new events.

Use it for features that can be reconstructed point-in-time without future leakage, including:

- prior attendance history;
- opponent identity / historical opponent draw;
- seasonality;
- day / kickoff time;
- competition / stage when historically known;
- standings, points, PPG and form as known before the match;
- rest / fixture congestion;
- prior-season opponent popularity;
- stadium/capacity context;
- other historically reconstructable context.

The existing Lech historical benchmark contains roughly 256 modelling rows and has already produced multiple model generations through v1.7/v1.8. This dataset should be used to improve the historical baseline immediately.

Required methodology:

- strict chronological / walk-forward validation;
- untouched holdout seasons;
- no random split as headline evidence;
- no feature computed from the current match outcome or later state;
- pre-registered model/feature comparison where practical;
- consistent metrics: MAE, median AE, WAPE/MAPE, bias, ±5/10/20%;
- horizon-specific evaluation;
- ablation by feature family;
- reproducible feature set and model versioning.

### Track B — Prospective live-signal validation (collect continuously)

Purpose: prove whether proprietary signals available only during the live sales window improve the historical baseline.

Examples:

- public inventory level/index;
- 6h/24h velocity;
- acceleration;
- sector-matched inventory movement;
- release / sector coverage anomaly flags;
- prospective Hype / media attention;
- genuinely point-in-time external signals that cannot be safely reconstructed historically.

The current Live Ticketing gate of 20 completed eligible matches belongs **only to Track B / promotion governance**. It is not a prerequisite for Track A model development.

## Product architecture

The intended model should be layered:

`Historical demand model`  
`+ live ticketing correction`  
`+ only validated context challengers`  
`= final P10 / P50 / P90`

Historical R&D should therefore aim to make the baseline materially stronger before live correction is applied.

## Immediate model-improvement programme

### 1. Rebuild v1.7 as executable code

v1.7 is the current frozen historical champion but the active runtime still uses a v1.3-derived baseline. Reconstruct exact v1.7 inference and make it reproducible.

### 2. Create Feature Store v1 now

Do not wait for new events. Historical point-in-time features should populate the same versioned Feature Store contract used later for inference.

Historical training snapshots and future live snapshots should have the same schema where the feature exists at both times.

### 3. Build Benchmark v0.2

Expand beyond the current v0.1 comparison.

Minimum model families:

- naive rolling / historical baselines;
- Ridge / Elastic Net residual models;
- existing Gradient Boosting baseline;
- HistGradientBoosting or equivalent boosted-tree baseline;
- CatBoost (already tested once, but keep as controlled comparator under the canonical feature store);
- a second strong tree challenger such as LightGBM/XGBoost if dependency and reproducibility requirements are satisfied.

Do not choose a winner by one metric. Compare MAE, WAPE, bias, stability by season/horizon and worst-case error.

### 4. Build feature-family ablations

Test groups rather than ad-hoc individual features:

- attendance history;
- opponent demand;
- seasonality/timing;
- sporting state;
- match importance/context;
- historical weather where a point-in-time-safe source exists;
- competition/stage;
- interaction features.

Every family must prove out-of-sample improvement before entering the champion contract.

### 5. Compare horizon strategies

Benchmark two approaches:

A. separate models per horizon;  
B. one global model with `horizon/time_to_match` as an input.

Required checkpoints should include at least T-30/T-14/T-7/T-3/T-1 where historical feature availability permits.

### 6. Probabilistic forecasting

P10/P50/P90 should ultimately be learned/calibrated rather than created by arbitrary interval widening.

Evaluate:

- quantile regression / pinball loss;
- empirical P10-P90 coverage;
- interval width calibration by horizon;
- calibration stability across seasons and opponent classes.

### 7. Historical multi-club expansion

The biggest leverage after Lech is to obtain/import historical home-match attendance datasets for the other tracked clubs, not wait for them to accumulate one match at a time prospectively.

For each club, target multiple seasons of:

- date/kickoff;
- opponent;
- competition;
- attendance;
- capacity if relevant;
- point-in-time sporting context where reconstructable.

This enables a true global multi-club baseline with club effects/calibration and much stronger leave-one-club / leave-one-season testing.

## What must still wait for prospective matches?

Historical data cannot honestly replace prospective evidence for signals that were not observed historically at the forecast checkpoint.

Therefore these still collect in parallel:

- live public ticket inventory trajectory;
- sector-level movement where historical snapshots do not exist;
- Hype/media samples under the current prospective-only protocol;
- model behaviour on genuinely unseen future fixtures.

This is validation work, not a reason to stop model R&D.

## Priority rule

Until the forecasting core is mature:

1. improve the historical model using all available historical data;
2. build canonical Feature Store + benchmark infrastructure;
3. collect prospective live-ticket evidence in parallel;
4. add Weather/Hype/Sporting only through controlled ablation;
5. postpone non-core product expansion when it competes with model quality work.

**We do not wait for data that already exists historically. We wait only for evidence that genuinely cannot be reconstructed from history.**
