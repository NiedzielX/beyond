# T-30 Baseline Smoothing v3 — frozen pre-validation specification

Date frozen: **2026-10-16**  
Status: **rolling-origin gate passed / frozen before historical regression validation**

Governance:

`ml/T30_RND_GOVERNANCE_V2.md`

## Hypothesis

At T-30, `baseline_season` can become noisy because it switches to the current-season home mean as soon as only a small number of current-season home attendances exists.

v3 shrinks that noisy current-season mean toward a PIT-safe historical anchor.

## Frozen candidate

Candidate ID:

`structural-prior-t30-v3-prev-shrink-k2`

Horizon:

`T-30`

Feature contract remains unchanged:

`structural-prior-pit-v1+verified-capacity-v1`

Target remains:

`verified-capacity occupancy residual`

Estimator remains the current production T-30 estimator:

```python
ExtraTreesRegressor(
    n_estimators=500,
    min_samples_leaf=3,
    max_features=0.8,
    random_state=42,
    n_jobs=-1,
)
```

Only the baseline changes.

### Baseline formula

Let:

- `n = season_home_n`;
- `current = season_home_mean`;
- `anchor = prev_season_home_mean` when available;
- fallback anchor = `home_attendance_mean`;
- final fallback = current `baseline_season`.

For `n > 0`:

`baseline_v3 = (n * current + 2 * anchor) / (n + 2)`

For `n = 0`:

`baseline_v3 = anchor`

Prediction remains:

`P50 = baseline_v3 + predicted_occupancy_residual * verified_capacity`

and is clipped to `[0, verified_capacity]`.

## Rolling-origin selection evidence

### Fold A

Train: **2021/22**  
Evaluate: **2022/23**

| Metric | Current T-30 | v3 k=2 | Change |
|---|---:|---:|---:|
| MAE | 2,157.147 | **2,050.134** | **-107.013 / -4.96%** |
| Median AE | 1,182.905 | **1,098.937** | -83.968 |
| WAPE | 23.123% | **21.976%** | -1.147 pp |
| Bias | -35.841 | -229.224 | -193.383 |

### Fold B

Train: **2021/22 + 2022/23**  
Evaluate: **2023/24**

| Metric | Current T-30 | v3 k=2 | Change |
|---|---:|---:|---:|
| MAE | 2,559.741 | **2,511.629** | **-48.112 / -1.88%** |
| Median AE | 1,371.231 | 1,419.352 | +48.121 |
| WAPE | 20.463% | **20.078%** | -0.385 pp |
| Bias | -433.388 | **-332.559** | +100.829 toward zero |

### Combined rolling-origin evidence

N = **587**.

| Metric | Current T-30 | v3 k=2 | Change |
|---|---:|---:|---:|
| MAE | 2,358.101 | **2,280.488** | **-77.613 / -3.291%** |
| Median AE | 1,296.796 | **1,265.882** | -30.915 |
| WAPE | 21.601% | **20.890%** | -0.710 pp |
| Bias | -234.276 | -280.803 | -46.528 |

The candidate passes the pre-validation rule:

- improves Fold A MAE: **YES**;
- improves Fold B MAE: **YES**;
- combined MAE improvement >= 3%: **YES — 3.291%**.

## Why k=2 was frozen instead of the lowest-MAE k=3

`prev / k=3` produced a lower combined MAE (**2,266.265; -3.895%**) but a larger combined negative bias (**-337.683**) and a larger bias deterioration on Fold A.

The governance contract explicitly requires bias/stability review rather than choosing a winner from MAE alone. `prev / k=2` is therefore frozen as the more balanced candidate while still clearing the pre-registered 3% MAE gate.

This selection uses only pre-validation rolling-origin evidence. It is not based on 2024/25 or 2025/26 candidate performance.

## Validation status

As of this commit, this frozen v3 candidate has **not** been scored on 2024/25 or 2025/26.

Those seasons are already exposed historical regression sets from prior R&D and are not described as untouched. The next step is one fixed regression-validation pass for this exact frozen candidate. No post-validation parameter change is allowed within v3.

No production runtime/artifact/registry change is authorized by this document.
