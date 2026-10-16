# T-30 Occupancy Anchor v4 — fixed historical regression validation

Date: **2026-10-16**  
Decision: **REJECTED / NO PRODUCTION CHANGE**

Frozen candidate:

`structural-prior-t30-v4-occupancy-anchor-k3`

Frozen spec commit:

`b25d5d11212f25438358c66ff118bf3256e03c80`

## Pre-validation evidence

The capacity-aware occupancy anchor passed the rolling-origin gate before the fixed regression sets were read:

- Fold A: **-5.18% MAE**;
- Fold B: **-2.99% MAE**;
- combined: **-3.994% MAE**.

## Fixed historical regression sets

### 2024/25

| Metric | Current T-30 | v4 candidate | Change |
|---|---:|---:|---:|
| MAE | **1,889.367** | 1,937.750 | **+48.383 / +2.56% worse** |
| Median AE | 1,173.335 | **1,160.310** | -13.026 |
| WAPE | **14.811%** | 15.190% | +0.379 pp |
| Bias | **+538.604** | +857.369 | +318.765 |

### 2025/26

| Metric | Current T-30 | v4 candidate | Change |
|---|---:|---:|---:|
| MAE | **1,846.279** | 1,940.157 | **+93.878 / +5.08% worse** |
| Median AE | **1,186.210** | 1,364.348 | +178.138 |
| WAPE | **13.564%** | 14.253% | +0.689 pp |
| Bias | **+44.945** | +346.031 | +301.086 |

### Combined

N = **599**.

| Metric | Current T-30 | v4 candidate | Change |
|---|---:|---:|---:|
| MAE | **1,867.643** | 1,938.964 | **+71.320 / +3.82% worse** |
| Median AE | **1,173.335** | 1,275.830 | +102.494 |
| WAPE | **14.162%** | 14.703% | +0.541 pp |
| Bias | **+289.714** | +599.566 | +309.851 |

## Decision

The frozen v4 candidate fails the historical regression gate:

- improves each fixed regression season: **NO**;
- improves combined MAE: **NO**;
- reaches `<1700`: **NO**;
- bias stability: **materially worse**.

Therefore:

- do not promote;
- do not tune k after these results;
- production remains `structural-prior-runtime-v1-t30-extra-full`;
- close v4 without merge.

## R&D implication

The rolling-origin gain confirms that historical anchoring can help the T-30 cold-start problem, but applying a previous-season anchor throughout the season is too rigid and does not generalize.

The next hypothesis is **cold-start-only historical anchoring**: use the historical/occupancy anchor only while current-season home evidence is sparse, then revert fully to the current production `baseline_season` once enough current-season home matches exist.

This is a new structural challenger family and must start from the rolling-origin pre-validation gate. The v4 regression-set club errors are audit evidence only and must not be used to tune v5 thresholds.
