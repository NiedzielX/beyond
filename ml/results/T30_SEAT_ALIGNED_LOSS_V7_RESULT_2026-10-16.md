# T-30 Seat-Aligned Loss v7 — rolling-origin result

Date: **2026-10-16**  
Decision: **STOPPED AT PRE-VALIDATION / NO PRODUCTION CHANGE**

Candidate:

`structural-prior-t30-v7-seat-aligned-extra`

## Hypothesis

The low-occupancy mechanism audit showed that the worst T-30 failures are high absolute-demand matches in large-capacity environments. Because the production target is an occupancy residual while the primary evaluation metric is absolute attendance MAE, v7 tested direct objective alignment:

- target remains verified-capacity occupancy residual;
- baseline remains `baseline_season`;
- feature set remains the production full PIT contract;
- ExtraTrees structural parameters remain 500 trees / leaf=3 / max_features=0.8;
- criterion changes from squared error to `absolute_error`;
- training `sample_weight = verified capacity`.

Rationale:

`capacity * |occupancy residual error| = absolute seat error`.

2024/25 and 2025/26 were **not scored**.

## Rolling-origin result

### Fold A — train 2021/22 -> evaluate 2022/23

| Metric | Current T-30 | v7 | Change |
|---|---:|---:|---:|
| MAE | **2,157.147** | 2,191.742 | **+34.595 / +1.60% worse** |
| Median AE | **1,182.905** | 1,305.433 | +122.528 |
| WAPE | **23.123%** | 23.494% | +0.371 pp |
| Bias | -35.841 | +182.014 | crosses zero |

Low baseline occupancy <=45%:

- current MAE: **2,737.839**;
- v7 MAE: **2,673.504**;
- improvement: **64.334 seats**;
- bias improves from **-640.978** to **-221.067**.

Capacity >=35k:

- current MAE: 4,024.456;
- v7 MAE: **3,901.687**;
- bias moves from +390.554 to +1,014.253.

### Fold B — train 2021/22 + 2022/23 -> evaluate 2023/24

| Metric | Current T-30 | v7 | Change |
|---|---:|---:|---:|
| MAE | **2,559.741** | 2,631.453 | **+71.713 / +2.80% worse** |
| Median AE | **1,371.231** | 1,410.728 | +39.496 |
| WAPE | **20.463%** | 21.036% | +0.573 pp |
| Bias | -433.388 | **-388.445** | +44.942 toward zero |

Low baseline occupancy <=45%:

- current MAE: **4,532.877**;
- v7 MAE: 4,671.155;
- change: **+138.278 worse**;
- bias worsens from -2,512.069 to -2,872.497.

Capacity >=35k:

- current MAE: **7,018.051**;
- v7 MAE: 7,425.498.

### Combined

N = **587**.

| Metric | Current T-30 | v7 | Change |
|---|---:|---:|---:|
| MAE | **2,358.101** | 2,411.223 | **+53.122 / +2.25% worse** |
| Median AE | **1,296.796** | 1,339.466 | +42.670 |
| WAPE | **21.601%** | 22.088% | +0.487 pp |
| Bias | -234.276 | **-102.730** | +131.546 toward zero |

## Gate

- improves Fold A: **NO**;
- improves Fold B: **NO**;
- improves both folds: **NO**;
- combined improvement >=3%: **NO**;
- result: `STOP_PRE_VALIDATION_GATE_NOT_MET`.

## Decision

- do not score 2024/25 or 2025/26;
- do not promote or freeze v7 for prospective shadow;
- do not change production target/loss/estimator;
- production remains `structural-prior-runtime-v1-t30-extra-full`.

## R&D conclusion for the 2026-10-16 cycle

The controlled v2-v7 cycle tested:

- estimator regularization;
- historical baseline smoothing;
- capacity-normalized historical anchoring;
- cold-start-only anchoring;
- explicit baseline occupancy state;
- seat-aligned loss weighting.

None produced a robust pre-registered improvement sufficient for promotion. Continuing with additional model families or parameter sweeps on the same historical evidence would increase selection bias without a clear mechanism.

Therefore historical T-30 architecture tinkering should pause. The next priority is prospective 2026/27 evidence collection, live-data quality, outcome capture and evaluation readiness. A new historical challenger family should be opened only when new data or a genuinely new structural signal becomes available.
