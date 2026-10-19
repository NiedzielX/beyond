# Beyond Ticketing — d2 Stage 1 Model Tournament v1

Last updated: **2026-10-19**

Status: **ACTIVE EXPERIMENT / d2 / NO PRODUCTION CHANGE**

Parent lineage:

- frozen Pre-Live v2: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- exact d2 Stage 0 replay: `ml/D2_LIVE_REPLAY_ANCHOR_V1.md`;
- frozen C1 comparator: `c1-shadow-v8-frozen-2026-10-16-n9`.

## Objective

Run the first learned d2 tournament against the sealed Frozen Pre-Live v2 anchor.

Primary prediction target:

`target_live_delta_occupancy = actual_attendance / capacity - frozen_pre_live_v2_p50 / capacity`

Final governed candidate:

`forecast = clip(frozen_pre_live_v2_p50 + live_delta * capacity, 0, capacity)`

Every live correction is safety-capped to:

`+/-10 percentage points occupancy`

This stage is research ranking only. It cannot promote production.

## Evaluation boundary

Current independent completed-event evidence:

- 9 events;
- 30 final-24h live rows;
- exact Frozen Pre-Live v2 anchor on every row.

Independent unit:

`event`

Validation:

`Leave-One-Event-Out`

Rules:

- every row from the held-out event is excluded from training;
- training rows receive event-balanced sample weights;
- no random snapshot split;
- no future snapshot information;
- no C1 v8 retraining;
- no production write.

## Core candidate set

Predeclared candidates:

1. `frozen-v2-zero-correction`;
2. `train-fold-bias`;
3. `inventory-linear-extrapolation`;
4. `ridge-a10`;
5. `huber-a001`;
6. `histgbr-abs-l7-leaf5-l2-10`;
7. `ridge-a10-plus-chronos2`;
8. `ridge-a10-plus-bolt-small`.

No open-ended model zoo is allowed in Stage 1.

## Why Chronos is used as a trajectory model, not a direct attendance label model

The public seat-map trajectory and final attendance are related but not the same measured variable.

Therefore Chronos is **not** given a synthetic time series such as:

`inventory proxy -> inventory proxy -> final attendance`

because that would mix incompatible measurement semantics and could create a misleading benchmark.

Instead the TSFM target is strictly observable at every context point:

`available_share_of_capacity`

Chronos forecasts the future public inventory-proxy trajectory toward kickoff.

The zero-shot terminal trajectory forecast then becomes an additional live feature for the supervised d2 residual model.

Final attendance / residual labels never enter Chronos context.

## TSFM challengers

### Chronos-2

Model:

`amazon/chronos-2`

Pinned weight revision:

`95a9710e2596287d08352589f42634fa5abdf0a7`

Use:

- zero-shot only;
- univariate public inventory-proxy trajectory in Stage 1;
- no fine-tuning;
- no cross-learning between held-out events;
- p10 / p50 / p90 terminal forecast.

### Chronos-Bolt-small

Model:

`amazon/chronos-bolt-small`

Pinned weight revision:

`0e96a1377adca89eebae3bbde4f859dc3b9f4b46`

Use:

- zero-shot lightweight TSFM benchmark;
- same causal trajectory contract as Chronos-2.

Package:

`chronos-forecasting==2.3.2`

Pinned runtime:

`ml/requirements-d2-tsfm-v1.txt`

## Causal time-series construction

Stage 0 already samples the final 24h trajectory on approximately 6h buckets.

Stage 1 regularizes those observations onto a fixed 6h sequence.

For each forecast row:

1. take only rows from the same event with `as_of_at <= current as_of_at`;
2. derive 6h buckets from `hours_to_kickoff`;
3. if an older bucket is missing, forward-fill only from an **older** observed value;
4. never interpolate from a future/later observation;
5. require at least **2 real observed context points** before a TSFM feature becomes ready;
6. forecast the remaining number of 6h steps toward kickoff.

If fewer than two real context points exist:

`tsfm_ready = 0`

and the supervised model handles the missing TSFM values through train-fold imputation.

## TSFM output features

Per TSFM family:

- readiness flag;
- real context-point count;
- prediction steps to kickoff;
- terminal available-share p50;
- projected removed-share to kickoff;
- p90-p10 uncertainty width;
- out-of-physical-range flag.

The raw terminal p50 is retained in evidence; the supervised feature uses a physically clipped `[0,1]` terminal available share plus an explicit out-of-range flag.

## Base live features

Reuse the existing PIT-safe C1 trajectory contract, but replace the prior layer with the exact Frozen Pre-Live v2 anchor.

Key groups include:

- frozen anchor P50 / expected occupancy;
- capacity;
- continuous time to kickoff;
- available inventory level / normalized share;
- removed-since-first / previous;
- 6h / 24h velocities;
- acceleration;
- sector absorption/release where available;
- coverage effects;
- observation-window / gap diagnostics;
- signal/data-quality flags.

## Learned model contracts

### Ridge

- `alpha=10.0`;
- median imputation with missing indicators;
- standardization;
- event-balanced weights.

### Huber

- `epsilon=1.35`;
- `alpha=0.01`;
- `max_iter=1000`;
- same imputation/scaling and event weights.

### HistGradientBoosting

- absolute-error loss;
- learning rate `0.05`;
- `100` iterations;
- max leaf nodes `7`;
- min samples leaf `5`;
- L2 `10.0`;
- seed `42`;
- event-balanced weights.

These parameters are frozen before the first real Stage-1 evidence run.

## Simple benchmarks

### Frozen-v2 zero correction

`forecast = frozen_pre_live_v2_p50`

This is the primary incumbent for d2.

### Train-fold bias

Use only training-event residuals to estimate a constant occupancy correction.

### Inventory linear extrapolation

Use current public available inventory and the most local valid removal velocity to extrapolate availability to kickoff.

This is only a transparent proxy benchmark; inventory is not treated as confirmed sales or attendance.

## Accuracy scorecard

Primary ranking metrics:

1. latest-row MAE across the 9 independently held-out events;
2. event-balanced trajectory-window MAE.

Also mandatory:

- improvement versus Frozen Pre-Live v2;
- event improvement rate;
- row bias;
- worst latest-event degradation;
- best latest-event improvement;
- non-zero revision rate;
- mean / max revision magnitude;
- event-level latest result table.

A research lead must improve both:

- latest-row MAE;
- event-balanced window MAE.

Tie-break:

1. lower latest-row MAE;
2. lower event-balanced window MAE;
3. lower worst-event degradation;
4. deterministic candidate ID.

This ranking does **not** equal production promotion.

## TSFM interpretation rule

Chronos-2 / Chronos-Bolt can advance only if their feature-assisted candidate improves the final attendance-residual leaderboard versus the matching non-TSFM Ridge benchmark.

A good inventory-trajectory forecast alone is insufficient.

If TSFM-assisted Ridge does not improve attendance MAE:

> close the Stage-1 TSFM challenger, not d2 as a whole.

If Chronos shows signal:

Stage 2 may evaluate one materially richer Chronos formulation, such as covariate-informed Chronos-2 or fine-tuning, but only after the zero-shot result is persisted.

## Why no NeuralProphet / Lag-Llama in Stage 1

Stage 1 intentionally tests one modern TSFM family plus its lightweight sibling, not another model zoo.

Chronos-2 is the primary TSFM challenger because it supports modern zero-shot forecasting and later covariate-informed extensions, while Chronos-Bolt provides a lighter benchmark under the same family/API.

NeuralProphet and Lag-Llama remain optional future challengers only if the Chronos family or new data provides a reason to reopen the TSFM family.

## Production boundary

Always:

- `promotion_allowed = false`;
- `production_change = false`;
- production `live_adjustment = 0`;
- frozen C1 v8 unchanged;
- Frozen Pre-Live v2 unchanged.

With only 9 independently completed events, a Stage-1 winner is a **research lead**, not a production-ready champion.

## Files

Implementation:

`ml/d2_stage1_model_tournament_v1.py`

Canonical pinned runner:

`ml/run_d2_stage1_model_tournament_v1.py`

Tests:

`ml/test_d2_stage1_model_tournament_v1.py`

TSFM dependencies:

`ml/requirements-d2-tsfm-v1.txt`

Workflow:

`.github/workflows/d2-stage1-model-tournament-v1.yml`
