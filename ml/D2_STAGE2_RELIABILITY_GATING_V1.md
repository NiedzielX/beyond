# Beyond Ticketing — d2 Stage 2 Reliability / Tail-Risk Gating v1

Last updated: **2026-10-19**

Status: **COMPLETED / P2 OBSERVATION MATURITY FROZEN / NO PRODUCTION CHANGE**

Canonical result:

`ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`

Frozen manifest:

`ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`

Frozen package ID:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Parent Stage-1 expert:

`ridge-a10`

## Objective

Stage 1 established that Ridge materially improves average MAE versus Frozen Pre-Live v2, but raw Ridge had unacceptable tail risk:

- latest MAE: `3320.39`;
- latest uplift vs Frozen v2: `+807.62 seats / 19.56%`;
- worst latest-event degradation: `+4326.90 seats`.

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

Reserved event `5` was explicitly excluded from selection.

## Frozen Stage-1 expert

`ridge-a10`

No Stage-1 retuning occurred in Stage 2.

Frozen expert contract:

- target: `target_live_delta_occupancy`;
- Ridge `alpha=10.0`;
- median imputation within training fold;
- missing indicators;
- standardization;
- event-balanced weights;
- raw correction capped at +/-10pp occupancy.

## Frozen Stage-2 tournament

Policies evaluated exactly as predeclared:

1. `P0-frozen-v2`;
2. `P1-raw-ridge`;
3. `P2-observation-maturity`;
4. `P3-correction-magnitude`;
5. `P4-data-quality`;
6. `P5-combined-reliability`.

No threshold grid or post-hoc rescue was used.

## Frozen advancement gates

A Stage-2 policy had to:

- beat Frozen v2 on latest-row MAE;
- beat Frozen v2 on event-balanced window MAE;
- retain at least 50% of raw-Ridge latest uplift;
- retain at least 50% of raw-Ridge window uplift;
- reduce raw-Ridge worst latest-event degradation by at least 25%.

Only one policy passed every gate:

`P2-observation-maturity`

## Canonical result

Canonical run:

`39308629738`

Main commit:

`4dc653f0f021c4b05aecadc985d55b69afa1dc11`

Artifact ID:

`12214478156`

Artifact ZIP SHA256:

`b4ae9183f398a8cd13542390ce05734f050697e903d34242d793b28854bf9296`

| Policy | Latest MAE | Window MAE | Worst degradation | p90 degradation |
|---|---:|---:|---:|---:|
| P0 Frozen v2 | 4,128.01 | 4,128.01 | 0.00 | 0.00 |
| P1 Raw Ridge | 3,320.39 | **3,619.19** | 4,326.90 | 1,683.09 |
| **P2 Observation maturity** | **3,240.99** | 3,657.65 | **1,081.72** | 1,034.05 |
| P3 Correction magnitude | 3,754.30 | 3,900.57 | 1,514.42 | 957.05 |
| P4 Data quality | 3,821.93 | 3,986.70 | 1,081.72 | **625.20** |
| P5 Combined | 3,805.79 | 3,965.32 | 1,081.72 | **625.20** |

## Frozen P2 policy

Observation-index reliability:

- first observation: `0.25`;
- second observation: `0.60`;
- third or later observation: `1.00`.

Time-to-kickoff cap:

- `hours_to_kickoff > 18`: `0.75`;
- `12 < hours_to_kickoff <= 18`: `0.90`;
- `hours_to_kickoff <= 12`: `1.00`.

Final reliability:

`min(observation_index_weight, time_weight)`

Forecast:

`final_forecast = frozen_pre_live_v2 + reliability * ridge_delta`

## P2 interpretation

P2 versus Frozen v2:

- latest MAE improvement: **887.02 seats / 21.49%**;
- window MAE improvement: **470.36 seats / 11.39%**.

P2 versus raw Ridge:

- latest MAE improves another **79.40 seats / 2.39%**;
- retains **92.44%** of raw Ridge window uplift;
- reduces worst-event degradation by **75%**;
- reduces p90 degradation by **38.56%**.

The core failure mode was over-trusting sparse early trajectories. P2 solves this by reducing reliability for the first and second observations while allowing mature trajectories to use the full Ridge signal.

## Reserved holdout — now active

Event `5`:

- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 final-24h rows.

This event was excluded from Stage-1 and Stage-2 selection.

Now that Stage 2 is frozen, score exactly once:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen P2 governed Ridge;
4. frozen C1 v8 where contract-compatible.

**No retuning after opening event 5.**

## Chronos / TSFM boundary

Stage-1 decision remains:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same exposed data.

## Production boundary

- `production_change = false`;
- `promotion_allowed = false`;
- production `live_adjustment = 0`;
- Frozen Pre-Live v2 unchanged;
- frozen C1 v8 unchanged.

## One-line instruction

> **Stage 2 is frozen as `d2-stage2-p2-observation-maturity-2026-10-19-v1`. Do not change Ridge or P2. Open event 5 once, score the frozen package, persist the result regardless of outcome, then continue append-only prospective evidence collection.**
