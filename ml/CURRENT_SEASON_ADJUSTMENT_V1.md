# Beyond Ticketing — b) Aktualny sezon — wzmocnić — Current Season Adjustment v1

Last updated: **2026-10-18**  
Status: **EXPERIMENTAL CHALLENGER / NO PRODUCTION CHANGE**

This experiment implements the next canonical model-development workstream:

**b) Aktualny sezon — wzmocnić**

## Problem

The Structural Prior already contains current-season features such as:

- `season_home_n`;
- `season_home_mean`;
- `season_home_last`;
- `season_home_r3`;
- `season_vs_long_ratio`.

They currently enter the model as ordinary features. There is no explicit governed layer that says:

> This club is currently running above/below its own historical home-demand norm, so adjust the baseline by a bounded amount.

## Current Season Adjustment v1

For every home club and forecast timestamp:

1. estimate the club's home-attendance norm from matches completed before the current season;
2. measure current-season home level using either:
   - current-season mean; or
   - current-season rolling last 3 home matches;
3. calculate the delta between current season and historical norm;
4. shrink the delta when only a few current-season home matches exist;
5. apply only a bounded fraction of the delta to the incumbent Structural Prior prediction.

Conceptually:

`adjusted forecast = Structural Prior + alpha × shrink(current season - historical norm)`

## Safety rules

- only matches completed before the forecast timestamp may contribute;
- minimum **2 current-season home matches** before a non-zero adjustment is allowed;
- signal strength is shrunk as `n / (n + k)`;
- absolute adjustment is capped at **20% of stadium capacity** before alpha;
- prediction remains bounded to `[0, capacity]`;
- current Structural Prior remains incumbent;
- no automatic promotion;
- no production artifact or `live_adjustment` changes.

## Candidate variants

The challenger tests:

- source: `season_mean` or `season_r3`;
- shrink `k`: `2 / 4 / 6`;
- adjustment strength `alpha`: `0.25 / 0.50 / 0.75`.

Total: **18 fixed candidate variants per horizon**.

## Evaluation protocol

The adjustment is evaluated separately for:

- T-30;
- T-14;
- T-7;
- T-3;
- T-1.

Selection:

- train incumbent on 2021/22–2022/23;
- choose one adjustment variant on 2023/24 development only.

Then freeze the chosen variant and evaluate unchanged on:

- 2024/25, with Structural Prior trained through 2023/24;
- 2025/26, with Structural Prior trained through 2024/25.

2024/25 and 2025/26 are already exposed historical reference seasons, so this is challenger evidence, not fresh untouched validation.

## Decision labels

Per horizon:

- `PROMISING_CONSISTENT_HOLDOUT_IMPROVEMENT` — both reference holdouts improve;
- `MIXED_BUT_POSITIVE_MEAN` — mean holdout MAE improves but not both seasons;
- `NOT_PROVEN` — mean holdout MAE does not improve.

No label promotes anything automatically.

## Implementation

Script:

`ml/current_season_adjustment_v1.py`

Workflow:

`.github/workflows/current-season-adjustment-v1.yml`

Canonical plan:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`

## Product interpretation

This is the explicit implementation of:

- mocniej brać pod uwagę ostatnie mecze domowe;
- mierzyć, czy klub w tym sezonie jest lepiej/gorzej niż jego historyczna norma;
- aktualizować ten adjustment po każdym kolejnym zakończonym meczu.

**Cel:** model szybciej reaguje na zmianę realiów w danym sezonie bez przebudowywania Structural Prior.
