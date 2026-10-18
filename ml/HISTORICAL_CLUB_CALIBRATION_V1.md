# Beyond Ticketing — Historical Club Calibration v1

Last updated: **2026-10-18**

Status: **ACTIVE FIXED-POLICY AUDIT / FINAL MAJOR a2 HYPOTHESIS / NO PRODUCTION CHANGE**

## Purpose

Test whether a persistent cross-season home-club residual remains after the correct rolling per-horizon historical model has made its prediction.

This is deliberately different from b2:

- **a2 calibration:** only residuals from prior completed seasons;
- **b2 current-season regime:** residuals from earlier matches in the current season.

Target-season residuals are forbidden in this experiment.

## Base historical model per horizon

- T-30: current production Structural Prior family;
- T-14: current production Structural Prior family;
- T-7: frozen historical candidate `hist31-leaf20-l2-1`;
- T-3: current production Structural Prior family;
- T-1: current production Structural Prior family.

The T-7 estimator itself is not retuned.

## Fixed calibration policy

Policy ID:

`club-median-residual-ratio-k10-cap05-min5`

For each rolling scored historical match:

`residual_ratio = (actual attendance - base prediction) / verified capacity`

For each home club using **prior completed seasons only**:

1. compute median residual ratio;
2. `shrinkage = n / (n + 10)`;
3. `shrunk_ratio = median_ratio * shrinkage`;
4. cap at `±5%` capacity;
5. activate only when `n >= 5`;
6. unknown / low-sample club correction = zero.

Target prediction:

`calibrated = clip(base prediction + bounded_ratio * capacity, 0, capacity)`

No parameter is selected after seeing results.

## Rolling base residual source

### 2022/23

Train base model on 2021/22.

Role:

`warmup_residual_source`

There is no earlier scored season from which a strict prior-season-only club calibration can be built, so 2022/23 is not a calibration evaluation season.

### 2023/24

Train base model on 2021/22–2022/23.

Calibration state uses 2022/23 rolling residuals only.

Role:

`development_evaluation`

### 2024/25

Train through 2023/24.

Calibration state uses 2022/23 + 2023/24 residual history.

Role:

`exposed_reference`

### 2025/26

Train through 2024/25.

Calibration state uses 2022/23 + 2023/24 + 2024/25 residual history.

Role:

`exposed_reference`

## Exact base-model reproduction gates

Already-canonical MAE values are hard-asserted where available.

T-7 additionally asserts the 2022/23 fixed-candidate MAE from the temporal robustness audit.

Any base-model drift fails CI before calibration evidence is accepted.

## Success interpretation

Because the calibration policy is fixed before evidence, no hyperparameter selection occurs.

Per horizon:

- `FIXED_CLUB_CALIBRATION_IMPROVES_ALL_EVALUATION_SEASONS` — positive MAE improvement in 2023/24, 2024/25 and 2025/26;
- `FIXED_CLUB_CALIBRATION_POSITIVE_MEAN_MIXED_SEASONS` — positive mean but not all seasons;
- `FIXED_CLUB_CALIBRATION_NOT_PROVEN` — non-positive mean.

Even the strongest label does not promote production automatically.

## Required diagnostics

Per evaluation season:

- base vs calibrated MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- event improvement rate;
- worst-event degradation and exact event;
- number of historical residual rows;
- prior seasons used;
- clubs with calibration state;
- active calibration event rate;
- correction mean/median/p90/max seats;
- correction share of capacity;
- club-level base vs calibrated MAE.

## Governance

`promotion_allowed = false`

Production remains unchanged throughout.

If this fixed, conservative cross-season policy is not proven, a2 historical optimization is considered sufficiently exhausted for the current data and the roadmap advances to **b2 current-season residual regime**, rather than another arbitrary historical model grid.

## Files

Implementation:

`ml/historical_club_calibration_v1.py`

Tests:

`ml/test_historical_club_calibration_v1.py`

Workflow:

`.github/workflows/historical-club-calibration-v1.yml`
