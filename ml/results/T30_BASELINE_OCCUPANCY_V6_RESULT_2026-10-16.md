# T-30 Baseline Occupancy v6 — rolling-origin result

Date: **2026-10-16**  
Decision: **STOPPED AT PRE-VALIDATION / NO PRODUCTION CHANGE**

Candidate:

`structural-prior-t30-v6-baseline-occupancy`

## Hypothesis

The merged T-30 error audit showed that matches with:

`baseline_season / verified_capacity <= 45%`

are a stable high-error underprediction regime across both rolling-origin folds.

v6 therefore added exactly one PIT-safe numeric feature:

`baseline_occupancy = baseline_season / verified_capacity`

Everything else remained fixed:

- production baseline `baseline_season`;
- verified-capacity occupancy-residual target;
- production ExtraTrees estimator (500 trees, leaf=3, max_features=0.8);
- existing full PIT feature set;
- physical capacity clip.

2024/25 and 2025/26 were **not scored**.

## Rolling-origin result

### Fold A — train 2021/22 -> evaluate 2022/23

| Metric | Current T-30 | v6 | Change |
|---|---:|---:|---:|
| MAE | **2,157.147** | 2,178.052 | **+20.905 / +0.97% worse** |
| Median AE | **1,182.905** | 1,234.817 | +51.912 |
| WAPE | **23.123%** | 23.347% | +0.224 pp |
| Bias | -35.841 | +20.900 | crosses zero |

Low-baseline-occupancy <=45% segment:

- control MAE: **2,737.839**;
- v6 MAE: **2,742.947**;
- delta: **+5.108 worse**;
- bias improves from **-640.978** to **-499.810**, but error does not improve.

### Fold B — train 2021/22 + 2022/23 -> evaluate 2023/24

| Metric | Current T-30 | v6 | Change |
|---|---:|---:|---:|
| MAE | 2,559.741 | **2,552.809** | **-6.932 / -0.27% better** |
| Median AE | **1,371.231** | 1,399.225 | +27.994 |
| WAPE | 20.463% | **20.407%** | -0.055 pp |
| Bias | **-433.388** | -462.497 | -29.109 |

Low-baseline-occupancy <=45% segment:

- control MAE: **4,532.877**;
- v6 MAE: **4,475.411**;
- delta: **-57.466 better**;
- bias improves from **-2,512.069** to **-2,349.171**.

### Combined

N = **587**.

| Metric | Current T-30 | v6 | Change |
|---|---:|---:|---:|
| MAE | **2,358.101** | 2,365.111 | **+7.010 / +0.30% worse** |
| Median AE | **1,296.796** | 1,314.865 | +18.069 |
| WAPE | **21.601%** | 21.665% | +0.064 pp |
| Bias | -234.276 | **-220.386** | +13.890 toward zero |

## Gate

Required:

- improve Fold A: **NO**;
- improve Fold B: **YES, marginally**;
- improve both folds: **NO**;
- combined MAE improvement >=3%: **NO**;
- result: `STOP_PRE_VALIDATION_GATE_NOT_MET`.

## Decision

- do not score 2024/25 or 2025/26;
- do not promote or freeze v6 for prospective shadow;
- do not add `baseline_occupancy` to the production feature contract;
- do not tune the ExtraTrees estimator around this feature;
- production remains `structural-prior-runtime-v1-t30-extra-full`.

## R&D implication

The low-occupancy regime remains real, but the ratio alone is not sufficient to explain it. The next diagnostic should stay entirely inside the rolling-origin evidence and compare **severely underpredicted low-occupancy rows vs well-predicted low-occupancy rows** to identify which contextual variables consistently separate the two groups across both folds.

Only after a repeated mechanism is identified should another challenger family be registered.
