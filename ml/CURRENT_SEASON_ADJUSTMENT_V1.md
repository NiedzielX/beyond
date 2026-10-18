# Beyond Ticketing — b) Aktualny sezon — wzmocnić — Current Season Adjustment v1

Last updated: **2026-10-18**  
Status: **TESTED / NOT PROVEN / NO PRODUCTION CHANGE**

This experiment implemented the canonical workstream:

**b) Aktualny sezon — wzmocnić**

Canonical result:

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

## Problem tested

The Structural Prior already contains current-season features such as:

- `season_home_n`;
- `season_home_mean`;
- `season_home_last`;
- `season_home_r3`;
- `season_vs_long_ratio`.

The challenger tested whether an additional governed post-model layer should explicitly move the baseline when the home club is currently above/below its own pre-current-season home-attendance norm.

## Current Season Adjustment v1

For every home club and forecast timestamp:

1. estimate the club's home-attendance norm from matches completed before the current season;
2. measure current-season home level using either current-season mean or rolling last 3 home matches;
3. calculate current-season delta vs historical norm;
4. shrink the delta when only a few current-season home matches exist;
5. apply a bounded fraction of that delta to the incumbent Structural Prior prediction.

Conceptually:

`adjusted forecast = Structural Prior + alpha × shrink(current season - historical norm)`

## Incumbent-isolation rule

The corrected experiment fits and scores the frozen Structural Prior on the **untouched canonical feature store first**.

Challenger-only current-season columns are added only after the incumbent prediction is fixed. The experiment hard-asserts the exact frozen Structural Prior benchmark on every reference holdout.

This prevents the challenger from silently changing the incumbent feature contract.

## Safety rules

- only matches completed before forecast timestamp may contribute;
- minimum **2 current-season home matches** before a non-zero adjustment;
- signal shrinkage: `n / (n + k)`;
- absolute signal capped at **20% of stadium capacity** before alpha;
- prediction bounded to `[0, capacity]`;
- `NO_ADJUSTMENT` is an explicit valid candidate;
- current Structural Prior remains incumbent;
- no automatic promotion;
- no production artifact or `live_adjustment` changes.

## Candidate variants

The challenger tests:

- source: `season_mean` or `season_r3`;
- shrink `k`: `2 / 4 / 6`;
- adjustment strength `alpha`: `0.25 / 0.50 / 0.75`.

Total: **18 non-zero variants per horizon + `NO_ADJUSTMENT`**.

## Evaluation protocol

Evaluated separately for T-30 / T-14 / T-7 / T-3 / T-1.

Selection:

- train incumbent on 2021/22–2022/23;
- choose the best option, including `NO_ADJUSTMENT`, on 2023/24 development only;
- freeze that choice;
- evaluate unchanged on 2024/25 and 2025/26 reference holdouts.

2024/25 and 2025/26 are already exposed historical reference seasons, so this is challenger evidence, not fresh untouched validation.

## Final result

| Horizon | Selected option | Signal | Mean incumbent MAE | Mean adjusted MAE |
|---|---|---|---:|---:|
| T-30 | `NO_ADJUSTMENT` | `NO_ADJUSTMENT_SELECTED` | 1,867.8 | 1,867.8 |
| T-14 | `NO_ADJUSTMENT` | `NO_ADJUSTMENT_SELECTED` | 1,809.4 | 1,809.4 |
| T-7 | `season_r3-k6-a25` | `NOT_PROVEN` | **1,790.0** | 1,844.3 |
| T-3 | `NO_ADJUSTMENT` | `NO_ADJUSTMENT_SELECTED` | 1,718.4 | 1,718.4 |
| T-1 | `NO_ADJUSTMENT` | `NO_ADJUSTMENT_SELECTED` | 1,697.3 | 1,697.3 |

T-7's development-selected adjustment degrades both holdouts:

- 2024/25: 1,777.7 -> 1,829.7 MAE;
- 2025/26: 1,802.3 -> 1,859.0 MAE.

No horizon has positive mean holdout improvement. No horizon has consistent improvement on both reference seasons.

## Decision

**Current Season Adjustment v1 is not promoted.**

The current-season signal already present inside Structural Prior is retained, but this extra post-model adjustment layer is not justified by the evidence. Do not keep tuning the same adjustment against these exposed reference seasons.

Active model development moves to:

**c) Context meczu — rozbudować.**

## Implementation

Script:

`ml/current_season_adjustment_v1.py`

Workflow:

`.github/workflows/current-season-adjustment-v1.yml`

Canonical plan:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`
