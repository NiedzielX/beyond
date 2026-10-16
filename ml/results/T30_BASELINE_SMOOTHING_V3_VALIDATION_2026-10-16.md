# T-30 Baseline Smoothing v3 — fixed historical regression validation

Date: **2026-10-16**  
Decision: **RESEARCH SIGNAL ONLY / NO PRODUCTION PROMOTION**

Frozen candidate:

`structural-prior-t30-v3-prev-shrink-k2`

Frozen pre-validation spec commit:

`d37647ace1947eec2227be80c38b3c66db108aea`

Governance:

`ml/T30_RND_GOVERNANCE_V2.md`

The exact `prev / k=2` baseline candidate was selected from rolling-origin pre-validation evidence and frozen before the fixed 2024/25 + 2025/26 regression sets were scored. No search or parameter change was performed during validation.

## Pre-validation evidence

The candidate passed the registered rolling-origin gate:

- Fold A, train 2021/22 -> evaluate 2022/23: **MAE -4.96%** vs production T-30;
- Fold B, train 2021/22–2022/23 -> evaluate 2023/24: **MAE -1.88%**;
- combined pre-validation: **MAE -3.291%**.

## Fixed historical regression validation

### 2024/25

| Metric | Current T-30 | v3 candidate | Change |
|---|---:|---:|---:|
| MAE | **1,889.367** | 1,935.401 | **+46.033 / +2.44% worse** |
| Median AE | 1,173.335 | **1,168.873** | -4.462 |
| WAPE | **14.811%** | 15.172% | +0.361 pp |
| Bias | **+538.604** | +872.837 | +334.233 |

### 2025/26

| Metric | Current T-30 | v3 candidate | Change |
|---|---:|---:|---:|
| MAE | 1,846.279 | **1,781.297** | **-64.982 / -3.52%** |
| Median AE | 1,186.210 | **1,163.192** | -23.018 |
| WAPE | 13.564% | **13.086%** | -0.477 pp |
| Bias | **+44.945** | +59.455 | +14.510 |

### Combined

N = **599**.

| Metric | Current T-30 | v3 candidate | Change |
|---|---:|---:|---:|
| MAE | 1,867.643 | **1,857.706** | **-9.938 / -0.53%** |
| Median AE | 1,173.335 | **1,166.746** | -6.589 |
| WAPE | 14.162% | **14.086%** | -0.075 pp |
| Bias | **+289.714** | +462.751 | +173.037 |

## Decision

The candidate does not meet the robustness requirement:

- improves each fixed historical regression season: **NO**;
- improves combined MAE: **YES, but only 0.53%**;
- combined MAE below 1700: **NO**;
- bias stability acceptable for production promotion: **NO**.

Therefore:

- do not replace `structural-prior-runtime-v1-t30-extra-full`;
- do not tune `k` or the shrinkage formula using these regression results;
- retain v3 only as evidence that early-season home-demand smoothing is a plausible feature family;
- any continuation must be a separately registered challenger with a new structural hypothesis.

## Next structural hypothesis

The raw previous-season attendance anchor ignores venue-capacity regime changes. A more coherent next candidate is an **occupancy-normalized historical anchor**:

`previous_home_occupancy = previous_attendance / previous_verified_capacity`

then mapped into the current venue regime:

`current_capacity_equivalent = previous_home_occupancy_mean * current_verified_capacity`

This is conceptually different from changing v3's shrinkage coefficient and can be reconstructed point-in-time from verified historical capacity. It must start a new challenger cycle and pass the rolling-origin gate before fixed historical regression sets are read.
