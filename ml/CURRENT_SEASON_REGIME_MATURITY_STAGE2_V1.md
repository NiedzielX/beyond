# Beyond Ticketing — Current-Season Regime Maturity Stage 2 v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / b2 STAGE 2 / NO PRODUCTION CHANGE**

Parent evidence:

`ml/results/CURRENT_SEASON_RESIDUAL_REGIME_V1_2026-10-18.md`

## Purpose

Stage 1 found material current-season residual-regime leads at T-3 and T-1 and a mixed-reference signal at T-7.

Development diagnostics also showed that low-sample regime state can be unstable while the strongest gains usually appear once the club has several earlier completed same-season home matches.

Stage 2 therefore changes **only one thing**:

> how many earlier completed same-season home matches are required before the already-selected Stage-1 regime correction may activate.

Signal source, shrink `k`, correction cap and PIT logic remain frozen.

## Fixed Stage-1 signal per horizon

- T-7: `ewma50-resid-k6-cap05`;
- T-3: `ewma50-resid-k2-cap05`;
- T-1: `ewma50-resid-k6-cap05`.

T-30/T-14 do not participate because Stage 1 selected `NO_ADJUSTMENT`.

## Activation candidates

- min 1 prior completed same-season home match — exact Stage-1 behavior;
- min 2;
- min 3.

The min-1 candidate must reproduce Stage-1 MAE exactly for 2022/23–2025/26 or CI fails.

## Selection

Development folds only:

1. 2022/23, base trained on 2021/22;
2. 2023/24, base trained through 2022/23.

Eligibility:

- positive MAE improvement in both development folds;
- >=0.5% mean relative MAE improvement.

Among eligible candidates:

1. find best mean MAE gain;
2. retain candidates with >=95% of best gain;
3. select lower maximum worst-event degradation;
4. then lower mean p90 delta;
5. then the more mature/higher minimum prior-match threshold;
6. deterministic ID.

References 2024/25–2025/26 are scored only after activation threshold is frozen.

## Governance note

The Stage-2 activation hypothesis is justified by the **development-bucket diagnostics** already present in Stage 1. The reference seasons are exposed historical evidence and do not select the threshold.

This stage can create a stronger frozen historical b2 candidate, not production promotion.

`promotion_allowed = false`

## Files

Implementation:

`ml/current_season_regime_maturity_stage2_v1.py`

Tests:

`ml/test_current_season_regime_maturity_stage2_v1.py`

Workflow:

`.github/workflows/current-season-regime-maturity-stage2-v1.yml`
