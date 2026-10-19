# Beyond Ticketing — d2 Stage 2 Reliability / Tail-Risk Gating v1

Last updated: **2026-10-19**

Status: **COMPLETED / P2 OBSERVATION MATURITY FROZEN / EVENT 5 HOLDOUT COMPLETE / NO PRODUCTION CHANGE**

Canonical Stage-2 result:

`ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`

Frozen manifest:

`ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`

First chronological holdout result:

`ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`

Active next-phase contract:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

Frozen package ID:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Parent Stage-1 expert:

`ridge-a10`

## Objective

Stage 1 established that Ridge materially improves average MAE versus Frozen Pre-Live v2, but raw Ridge had unacceptable tail risk.

Stage 2 therefore asked:

> **When should the live Ridge correction be trusted, shrunk, or ignored?**

## Frozen development boundary

Development events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Rows:

`30`

Independent unit:

`event`

Validation:

`LOEO_STAGE1_RIDGE_THEN_CAUSAL_POLICY`

Event `5` was explicitly excluded from Stage-1/Stage-2 selection.

## Frozen Stage-1 expert

`ridge-a10`

Contract:

- target `target_live_delta_occupancy`;
- Ridge `alpha=10.0`;
- median imputation within training fold;
- missing indicators;
- standardization;
- event-balanced weights;
- raw correction capped at +/-10pp occupancy.

No Stage-1 retuning occurred in Stage 2 or after the holdout.

## Stage-2 tournament

Policies evaluated exactly as predeclared:

1. `P0-frozen-v2`;
2. `P1-raw-ridge`;
3. `P2-observation-maturity`;
4. `P3-correction-magnitude`;
5. `P4-data-quality`;
6. `P5-combined-reliability`.

Frozen gates required:

- latest-row MAE better than Frozen v2;
- event-balanced window MAE better than Frozen v2;
- >=50% retained raw-Ridge latest uplift;
- >=50% retained raw-Ridge window uplift;
- >=25% reduction in raw-Ridge worst latest-event degradation.

Only:

`P2-observation-maturity`

passed every gate.

## Canonical Stage-2 evidence

Run:

`39308629738`

Artifact ID:

`12214478156`

Artifact ZIP SHA256:

`b4ae9183f398a8cd13542390ce05734f050697e903d34242d793b28854bf9296`

| Policy | Latest MAE | Window MAE | Worst degradation | p90 degradation |
|---|---:|---:|---:|---:|
| Frozen v2 | 4,128.01 | 4,128.01 | 0.00 | 0.00 |
| Raw Ridge | 3,320.39 | **3,619.19** | 4,326.90 | 1,683.09 |
| **P2 Observation maturity** | **3,240.99** | 3,657.65 | **1,081.72** | 1,034.05 |
| P3 Correction magnitude | 3,754.30 | 3,900.57 | 1,514.42 | 957.05 |
| P4 Data quality | 3,821.93 | 3,986.70 | 1,081.72 | **625.20** |
| P5 Combined | 3,805.79 | 3,965.32 | 1,081.72 | **625.20** |

## Frozen P2 policy

Observation-index reliability:

- first observation `0.25`;
- second observation `0.60`;
- third or later `1.00`.

Time-to-kickoff cap:

- >18h `0.75`;
- >12h and <=18h `0.90`;
- <=12h `1.00`.

Final reliability:

`min(observation_index_weight, time_weight)`

Forecast:

`final_forecast = frozen_pre_live_v2 + reliability * ridge_delta`

Do not change these values from event-5 evidence.

## Stage-2 development interpretation

P2 versus Frozen v2:

- latest MAE improvement `887.02 seats / 21.49%`;
- window MAE improvement `470.36 / 11.39%`.

P2 versus raw Ridge:

- latest improves another `79.40 seats / 2.39%`;
- retains `92.44%` of raw-Ridge window uplift;
- reduces worst degradation by `75%`;
- reduces p90 degradation by `38.56%`.

The development failure mode was over-trusting sparse early trajectories.

## Event 5 holdout — COMPLETE

Event:

Lech Poznań vs Korona Kielce

Actual attendance:

`37,407`

Canonical holdout run:

`39310995137`

Artifact ID:

`12215538287`

Event-5 errors:

| Layer | Latest error | Window MAE |
|---|---:|---:|
| Structural T-1 base | 7,669.07 | n/a |
| Frozen Pre-Live v2 | 9,832.52 | 9,832.52 |
| Raw frozen Ridge | **6,652.81** | **6,170.35** |
| Frozen P2 | **6,652.81** | 7,263.16 |
| persisted C1 v8 policy | 7,669.07 | 7,669.07* |

`*` C1 window sampling is not identical to canonical d2 final-24h sampling.

Event-5 findings:

1. raw Ridge/P2 latest reduced Frozen-v2 error by `3179.71 seats / 32.34%`;
2. d2 latest beat persisted C1 v8 policy by `1016.26 seats`;
3. P2 had reliability `1.0` at the final mature row and therefore matched raw Ridge latest;
4. P2's early conservative weights worsened window MAE versus raw Ridge on this event, while still improving Frozen v2;
5. Frozen b2 moved Structural T-1 base down by `2163.45 seats` and worsened the pre-live error by the same amount.

## Holdout governance consequence

Event 5 is now exposed permanently.

It may be used as:

- regression evidence;
- component-failure evidence;
- motivation for a future predeclared hypothesis.

It may not be reused as fresh/unseen validation after any tuning.

No Ridge/P2/b2 change is allowed from event 5 alone.

## Prospective signals to monitor

### b2 negative overreaction

Current evidence:

`ONE PROSPECTIVE FAILURE SIGNAL`

Potential future hypothesis:

> same-season residual correction may overreact negatively for some high-demand Lech matches.

Do not tune until repeated independent evidence exists.

### P2 early conservatism

Current evidence:

`ONE HOLDOUT OBSERVATION`

P2 reduced useful early correction on event 5 but retained the mature final correction.

Track risk/return prospectively; do not tune now.

## Chronos / TSFM boundary

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the exposed development/holdout evidence.

## Active next phase

`FROZEN PROSPECTIVE ACCUMULATION`

Use:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

For every new eligible completed event preserve separate:

1. Structural T-1 base;
2. Frozen-v2/b2;
3. raw Ridge;
4. P2;
5. genuine persisted C1 comparator where available.

No retraining in the prospective scoring cycle.

## Production boundary

- `production_change = false`;
- `promotion_allowed = false`;
- production `live_adjustment = 0`;
- Frozen Pre-Live v2 unchanged;
- Ridge/P2 frozen;
- C1 v8 frozen.

## One-line instruction

> **Stage 2 and event 5 are complete. Keep `d2-stage2-p2-observation-maturity-2026-10-19-v1` frozen, never retune from event 5, and score future independent completed events append-only under `D2_PROSPECTIVE_ACCUMULATION_V1` with explicit Structural -> b2 -> Ridge -> P2 -> persisted C1 diagnostics.**
