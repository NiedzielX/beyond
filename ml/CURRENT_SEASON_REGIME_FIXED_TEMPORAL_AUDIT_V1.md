# Beyond Ticketing — Current-Season Regime Fixed Temporal Audit v1

Last updated: **2026-10-18**

Status: **ACTIVE FIXED-CONFIG AUDIT / b2 FINAL ROBUSTNESS GATE / NO PRODUCTION CHANGE**

Parent evidence:

- `ml/results/CURRENT_SEASON_RESIDUAL_REGIME_V1_2026-10-18.md`;
- `ml/results/CURRENT_SEASON_REGIME_MATURITY_STAGE2_V1_2026-10-18.md`.

## Purpose

Stage 2 froze three historical b2 candidates:

- T-7: `ewma50-resid-k6-cap05-min3`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

This audit performs **no selection and no tuning**.

It asks only:

> Do the exact frozen policies reproduce and remain MAE-positive across all four rolling seasons while preserving transparent tail, club, and activation diagnostics?

## Fixed rolling folds

1. train 2021/22 -> score 2022/23;
2. train through 2022/23 -> score 2023/24;
3. train through 2023/24 -> score 2024/25;
4. train through 2024/25 -> score 2025/26.

## Hard reproduction gates

The exact Stage-2 candidate MAE is predeclared for every horizon/fold.

If any fixed candidate MAE drifts, CI fails.

No tolerance is granted for choosing a new signal, shrinkage, threshold, cap or model.

## Audit dimensions

Per horizon/fold:

- base MAE;
- fixed candidate MAE;
- MAE improvement;
- relative MAE improvement;
- median AE;
- p90 AE;
- bias;
- event improvement rate;
- worst-event degradation + identity;
- best-event improvement + identity;
- active correction share;
- correction magnitude;
- maturity buckets;
- club-level MAE for club-season cells with n>=5.

Aggregate:

- all four folds improve?;
- mean/min/max fold improvement;
- maximum worst-event degradation;
- mean active share;
- share of club-season cells improved;
- worst and best club-season cells.

## Pass condition

For each horizon:

`all four fold MAE improvements > 0`

Overall audit passes only if all three horizons pass.

There is no post-hoc parameter change after this audit.

## Decision boundary

If the fixed audit passes:

- b2 may be treated as sufficiently evaluated for current data;
- the three policies become frozen **historical Pre-Live b2 candidates**;
- T-30/T-14 remain no-adjustment;
- production remains unchanged;
- active development advances to c2 match-context modeling.

If any horizon fails, that horizon retains its pre-b2 base state unless a materially new b2 hypothesis is separately justified. The audit itself does not initiate retuning.

## Files

Implementation:

`ml/current_season_regime_fixed_temporal_audit_v1.py`

Tests:

`ml/test_current_season_regime_fixed_temporal_audit_v1.py`

CI:

`.github/workflows/current-season-regime-fixed-temporal-audit-v1.yml`

`promotion_allowed = false`
