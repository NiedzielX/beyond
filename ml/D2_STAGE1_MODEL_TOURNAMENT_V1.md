# Beyond Ticketing — d2 Stage 1 Model Tournament v1

Last updated: **2026-10-19**

Status: **COMPLETED / RESEARCH LEAD SELECTED / NO PRODUCTION CHANGE**

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Next stage:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

## Parent lineage

- frozen Pre-Live v2: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- exact d2 Stage 0 replay: `ml/D2_LIVE_REPLAY_ANCHOR_V1.md`;
- frozen C1 comparator: `c1-shadow-v8-frozen-2026-10-16-n9`.

## Objective

Stage 1 tested whether a compact learned live-residual model can improve final-attendance MAE relative to the sealed Frozen Pre-Live v2 anchor.

Primary target:

`target_live_delta_occupancy = actual_attendance / capacity - frozen_pre_live_v2_p50 / capacity`

Governed forecast:

`forecast = clip(frozen_pre_live_v2_p50 + live_delta * capacity, 0, capacity)`

Maximum raw Stage-1 correction:

`+/-10 percentage points occupancy`

Stage 1 is research ranking only and cannot promote production.

## Frozen development boundary

Development events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Development rows:

`30`

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

The append-only exporter later grew to 10 events / 34 rows. The original 9/30 development lineage was reconstructed by exact event + as-of identity so the new event could not contaminate Stage-1 selection.

## New holdout preserved outside selection

Event ID:

`5`

Match:

`Lech Poznań vs Korona Kielce`

Kickoff:

`2026-10-18T15:30:00Z`

Actual attendance:

`37,407`

Capacity:

`43,269`

Live rows:

`4`

This event was not used for Stage-1 selection and must remain outside Stage-2 policy design.

## Predeclared candidate set

1. `frozen-v2-zero-correction`;
2. `train-fold-bias`;
3. `inventory-linear-extrapolation`;
4. `ridge-a10`;
5. `huber-a001`;
6. `histgbr-abs-l7-leaf5-l2-10`;
7. `ridge-a10-plus-chronos2`;
8. `ridge-a10-plus-bolt-small`.

No open-ended model zoo was allowed.

## Research lead

Selected:

`ridge-a10`

Contract:

- Ridge `alpha=10.0`;
- numeric live features;
- median imputation within training fold;
- missing-value indicators;
- standardization;
- event-balanced weights;
- target = capacity-normalized live residual;
- correction clipped to +/-10pp occupancy.

## Result summary

| Candidate | Latest MAE | Latest improvement vs Frozen v2 | Window MAE | Window improvement | Event improvement rate | Worst latest-event degradation |
|---|---:|---:|---:|---:|---:|---:|
| Frozen v2 | 4,128.01 | 0.00 | 4,128.01 | 0.00 | 0.0% | 0.00 |
| Train-fold bias | 4,655.98 | -527.97 | 4,655.98 | -527.97 | 22.2% | 1,554.36 |
| Inventory extrapolation | 3,869.68 | +258.33 | 3,701.05 | +426.97 | 44.4% | 3,100.60 |
| **Ridge `alpha=10`** | **3,320.39** | **+807.62** | **3,619.19** | **+508.83** | **66.7%** | **4,326.90** |
| Huber | 4,567.83 | -439.81 | 5,135.08 | -1,007.07 | 22.2% | 4,370.80 |
| HistGradientBoosting | 4,186.11 | -58.10 | 4,084.01 | +44.00 | 33.3% | 4,326.90 |
| Ridge + Chronos-2 | 3,428.25 | +699.76 | 3,645.19 | +482.82 | 66.7% | 4,326.90 |
| Ridge + Bolt-small | 3,428.08 | +699.93 | 3,658.58 | +469.43 | 66.7% | 4,326.90 |

Ridge latest-row MAE improvement:

`+807.62 seats / 19.56%`

Ridge event-balanced window improvement:

`+508.83 seats / 12.33%`

Mean absolute Ridge revision:

`1,737.45 seats`

## Chronos / TSFM result

Chronos was used only as a causal public inventory-trajectory forecaster.

TSFM target:

`available_share_of_capacity`

Final attendance / residual labels never entered Chronos context.

Models:

- `amazon/chronos-2`, revision `95a9710e2596287d08352589f42634fa5abdf0a7`;
- `amazon/chronos-bolt-small`, revision `0e96a1377adca89eebae3bbde4f859dc3b9f4b46`.

Runtime:

`chronos-forecasting==2.3.2`

TSFM-ready rows:

`21/30`

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Both TSFM-assisted Ridge candidates improved Frozen v2, but both were worse than plain `ridge-a10`.

Therefore do not fine-tune Chronos or add NeuralProphet / Lag-Llama on the same 9-event development set.

Reopen TSFM only with materially more independent trajectory events or a materially new predeclared hypothesis.

## Canonical evidence

Workflow run:

`39256585339`

Main commit:

`3e95f0025d381eb1bed4a2e00744466b17d21dea`

Artifact ID:

`12187853899`

Artifact ZIP SHA256:

`c494ba609f3c9ee376e8285a9af975cc78d813337bd219fbaf94c7a9a336c6de`

Stage-1 JSON SHA256:

`a666c57631756245245511ec11b40673aa7fb2c6cbb23303fb019993130fae4c`

Predictions CSV SHA256:

`df7cacd7a116c418f869ef6890f1bec289238c1af0f561e18a13b83c0b1f5783`

Full evidence and hashes:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

## Critical interpretation

Stage 1 proves a useful live signal exists on the development lineage.

It does **not** prove raw Ridge is safe.

Worst latest-event degradation remains:

`+4,326.90 seats`

Therefore the next work is not another model zoo. It is Stage 2 reliability/tail-risk governance:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

## Production boundary

Always:

- `promotion_allowed = false`;
- `production_change = false`;
- production `live_adjustment = 0`;
- frozen C1 v8 unchanged;
- Frozen Pre-Live v2 unchanged.

## Files

Implementation:

`ml/d2_stage1_model_tournament_v1.py`

Canonical runner:

`ml/run_d2_stage1_model_tournament_v1.py`

Frozen-development splitter:

`ml/d2_stage1_payload_split_v1.py`

Tests:

- `ml/test_d2_stage1_model_tournament_v1.py`;
- `ml/test_d2_stage1_payload_split_v1.py`.

Workflow:

`.github/workflows/d2-stage1-model-tournament-v1.yml`

## Immediate instruction

> **Freeze `ridge-a10` exactly as selected. Do not use Lech–Korona event 5 to tune it or the next reliability policy. Build Stage 2 only on the original 9-event/30-row lineage, freeze the reliability policy, then open event 5 once as the first chronological holdout.**
