# Current-Season Regime Fixed Temporal Audit v1 — Result 2026-10-18

Status: **PASS / B2 FIXED HISTORICAL CANDIDATES TEMPORALLY ROBUST / NO PRODUCTION CHANGE**

Workstream:

**b2 — Current-season residual regime**

## Evidence source

GitHub Actions run: `39162448305`  
Tested head: `4f8af3340d96184b66fe60a1b7e4d3ed1119c440`  
Artifact: `current-season-regime-fixed-temporal-audit-v1-39162448305`  
Artifact ID: `12149610912`  
Artifact ZIP SHA256: `9a8bb3ed2f3ba4dbcf6b786c8cb1ab067ef1bca62afebbe674f6dec277141f0a`  
Result JSON SHA256: `1d0556a831166ae665d2be209450122461329e584c6c4751ba130502c8afbccb`

CI:

- pinned runtime: PASS;
- compile: PASS;
- unit tests: 3/3 PASS;
- exact Stage-2 fixed-candidate MAE reproduction: PASS for all 12 horizon-season cells;
- full four-fold audit: PASS;
- artifact upload: PASS.

`promotion_allowed = false`

Production remains unchanged.

## No tuning in this audit

The exact Stage-2 candidates were frozen before the audit:

- T-7: `ewma50-resid-k6-cap05-min3` on top of `hist31-leaf20-l2-1`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

T-30/T-14 remain `NO_ADJUSTMENT` for b2.

This audit performs no model/feature/threshold selection.

## Rolling folds

1. 2021/22 -> 2022/23;
2. through 2022/23 -> 2023/24;
3. through 2023/24 -> 2024/25;
4. through 2024/25 -> 2025/26.

All three fixed candidates improve MAE on all four folds.

## Result summary

| Horizon | Fixed candidate | Four folds positive | Mean MAE improvement | Minimum fold improvement | Mean active share | Max worst-event degradation |
|---|---|---|---:|---:|---:|---:|
| T-7 | `ewma50-resid-k6-cap05-min3` | **yes** | **+51.47** | +7.15 | 78.4% | +2,760.55 |
| T-3 | `ewma50-resid-k2-cap05-min3` | **yes** | **+70.44** | +21.18 | 79.1% | +2,760.55 |
| T-1 | `ewma50-resid-k6-cap05-min3` | **yes** | **+69.54** | +24.66 | 79.4% | +2,760.55 |

Overall audit:

`PASS`

## T-7 fold results

| Season | Base MAE | Fixed b2 MAE | Improvement |
|---|---:|---:|---:|
| 2022/23 | 1,984.99 | 1,891.86 | **+93.13** |
| 2023/24 | 2,317.34 | 2,246.57 | **+70.77** |
| 2024/25 | 1,650.97 | 1,643.82 | **+7.15** |
| 2025/26 | 1,773.80 | 1,738.98 | **+34.81** |

Mean improvement:

**+51.47 MAE**.

Club-season cells with n>=5:

- 72 total;
- 44 improve;
- 28 worsen;
- improved share: **61.1%**.

Worst club-season cell:

`Śląsk Wrocław 2023/24`, MAE degradation **-295.25**.

Best club-season cell:

`Ruch Chorzów 2023/24`, improvement **+459.09**.

## T-3 fold results

| Season | Base MAE | Fixed b2 MAE | Improvement |
|---|---:|---:|---:|
| 2022/23 | 1,916.35 | 1,826.95 | **+89.40** |
| 2023/24 | 2,311.62 | 2,190.79 | **+120.83** |
| 2024/25 | 1,661.72 | 1,611.37 | **+50.34** |
| 2025/26 | 1,775.07 | 1,753.89 | **+21.18** |

Mean improvement:

**+70.44 MAE**.

Median AE improves on all four folds.

Club-season cells with n>=5:

- 72 total;
- 46 improve;
- 26 worsen;
- improved share: **63.9%**.

Worst club-season cell:

`Lechia Gdańsk 2025/26`, MAE degradation **-417.16**.

Best club-season cell:

`Ruch Chorzów 2023/24`, improvement **+1,224.31**.

## T-1 fold results

| Season | Base MAE | Fixed b2 MAE | Improvement |
|---|---:|---:|---:|
| 2022/23 | 1,913.99 | 1,794.26 | **+119.73** |
| 2023/24 | 2,347.99 | 2,261.11 | **+86.88** |
| 2024/25 | 1,651.73 | 1,627.07 | **+24.66** |
| 2025/26 | 1,742.84 | 1,695.96 | **+46.87** |

Mean improvement:

**+69.54 MAE**.

Club-season cells with n>=5:

- 72 total;
- 43 improve;
- 29 worsen;
- improved share: **59.7%**.

Worst club-season cell:

`Lechia Gdańsk 2025/26`, MAE degradation **-226.76**.

Best club-season cell:

`Ruch Chorzów 2023/24`, improvement **+1,138.95**.

## Tail / risk boundary

The fixed policies are temporally MAE-positive but not harmless on every event.

Maximum single-event degradation observed across the four-fold audit:

**+2,760.55 seats**.

The correction remains bounded by the fixed +/-5% capacity safety cap.

Event improvement rate is below 50% in several folds, which means the MAE gain is driven by the magnitude of improvements rather than by winning on every match.

Club-level heterogeneity is also real: only ~60–64% of club-season cells improve.

These limitations must remain part of the candidate contract and are one reason this is a historical Pre-Live candidate rather than a production promotion.

## Decision

> **b2 is sufficiently evaluated for the current historical dataset. Freeze the maturity-gated policies as historical Pre-Live v2 candidates; do not tune them further against the same exposed seasons. Advance active development to c2 match-context modeling.**

Frozen historical b2 state:

- T-30: `NO_ADJUSTMENT`;
- T-14: `NO_ADJUSTMENT`;
- T-7: `ewma50-resid-k6-cap05-min3`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

The base historical model under T-7 remains `hist31-leaf20-l2-1`.

Production remains unchanged:

`live_adjustment = 0`

Next workstream:

**c2 — match context**.
