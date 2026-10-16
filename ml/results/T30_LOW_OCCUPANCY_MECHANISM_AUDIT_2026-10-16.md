# T-30 Low-Occupancy Mechanism Audit

Date: **2026-10-16**  
Status: **diagnostic complete / no production change**

## Scope

Follow-up to:

`ml/results/T30_PREVALIDATION_ERROR_AUDIT_V1_2026-10-16.md`

The earlier audit identified the strongest repeated T-30 error regime as:

`baseline_season / verified_capacity <= 45%`

This audit stays entirely inside rolling-origin pre-validation evidence and compares, within that low-occupancy regime:

- the most severely underpredicted quartile by signed error;
- the best-predicted half by absolute error.

Folds:

- A: train 2021/22 -> evaluate 2022/23;
- B: train 2021/22 + 2022/23 -> evaluate 2023/24.

2024/25 and 2025/26 were **not scored**.

No challenger was trained.

## Group severity

### Fold A

Low-occupancy rows: **108**

- severe underprediction rows: 27;
- severe mean error: **-6,256.5 seats**;
- severe mean absolute error: **6,256.5**;
- well-predicted rows: 53;
- well-predicted mean error: **+18.4**;
- well-predicted mean absolute error: **529.0**.

### Fold B

Low-occupancy rows: **51**

- severe underprediction rows: 13;
- severe mean error: **-10,830.0 seats**;
- severe mean absolute error: **10,830.0**;
- well-predicted rows: 26;
- well-predicted mean error: **+573.0**;
- well-predicted mean absolute error: **1,174.2**.

## Stable mechanism

The severely underpredicted rows are not the lowest-demand fixtures. They are systematically **higher absolute-demand matches played in larger capacity regimes**.

### Current-season home demand

`season_home_mean`

| Fold | Severe | Well predicted | SMD |
|---|---:|---:|---:|
| A | 10,391 | 6,389 | **+0.98** |
| B | 14,522 | 5,481 | **+2.15** |

### Long-run home demand relative to league

`home_demand_vs_league_median`

| Fold | Severe | Well predicted | SMD |
|---|---:|---:|---:|
| A | 1.956 | 1.120 | **+0.86** |
| B | 1.692 | 0.769 | **+2.02** |

### Long-run home attendance

`home_attendance_mean`

| Fold | Severe | Well predicted | SMD |
|---|---:|---:|---:|
| A | 11,074 | 6,319 | **+0.86** |
| B | 10,940 | 4,903 | **+1.95** |

Rolling-3 / rolling-5 / rolling-10 and home-attendance median show the same repeated direction.

### Verified capacity

| Fold | Severe | Well predicted | SMD |
|---|---:|---:|---:|
| A | 31,777 | 23,240 | **+0.60** |
| B | 47,757 | 18,441 | **+2.37** |

### Position separation

`abs_position_gap`

| Fold | Severe | Well predicted | SMD |
|---|---:|---:|---:|
| A | 7.22 | 5.79 | +0.35 |
| B | 8.92 | 5.42 | +0.79 |

This is weaker than the demand/capacity mechanism and is already represented in the current feature contract.

## Interpretation

The repeated failure mode is best described as:

> **high absolute-demand home clubs in large-capacity environments whose expected occupancy percentage still looks low.**

This explains why simply adding `baseline_occupancy` in v6 did not solve the problem.

The target is currently:

`occupancy_residual = attendance / capacity - baseline / capacity`

while the strategic evaluation metric is absolute attendance MAE in seats.

An occupancy-residual error of 0.10 means:

- 2,000 seats at capacity 20,000;
- 5,000 seats at capacity 50,000.

The current fit does not explicitly make the second error more important merely because it costs more seats. The mechanism audit therefore points more strongly to **training-loss / objective alignment** than to another missing contextual feature.

## v7 registered hypothesis

Test a capacity-weighted absolute-error tree objective while keeping the Structural Prior semantics unchanged.

Frozen v7 development hypothesis before execution:

- horizon: T-30;
- baseline: `baseline_season`;
- target remains verified-capacity occupancy residual;
- feature set remains current full PIT feature set;
- estimator family remains ExtraTrees;
- tree count / leaf / feature sampling remain production values;
- tree criterion changes from squared error to `absolute_error`;
- training sample weight = verified capacity.

Why:

`capacity * |occupancy residual error| = absolute seat error`

so capacity-weighted absolute-error fitting is directly aligned with the primary T-30 MAE metric while preserving normalized occupancy-residual semantics and physical capacity clipping.

This is a single pre-registered structural challenger, not a parameter grid.

Selection stays rolling-origin only under `ml/T30_RND_GOVERNANCE_V2.md`:

- must improve Fold A;
- must improve Fold B;
- combined MAE improvement must be >=3%;
- 2024/25 and 2025/26 will not be used for selection;
- if it passes, the next meaningful validation is prospective 2026/27 shadow evidence.
