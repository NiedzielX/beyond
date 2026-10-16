# T-30 Occupancy Anchor v4 — frozen pre-regression specification

Date frozen: **2026-10-16**  
Status: **rolling-origin gate passed / frozen before historical regression validation**

Governance:

`ml/T30_RND_GOVERNANCE_V2.md`

## Structural hypothesis

Raw attendance from a previous season is not directly comparable when a club's stadium or verified capacity regime changes.

v4 normalizes previous-season home demand into occupancy first:

`previous_home_occupancy = previous_home_attendance / previous_verified_capacity`

Then maps the previous-season mean occupancy into the target event's current verified capacity:

`occupancy_anchor = mean(previous_home_occupancy) * current_verified_capacity`

The early current-season home mean is shrunk toward that capacity-aware anchor.

This uses completed previous-season home matches only, so it is point-in-time safe for every current-season T-30 checkpoint.

## Frozen candidate

Candidate ID:

`structural-prior-t30-v4-occupancy-anchor-k3`

Horizon: `T-30`

Feature contract remains:

`structural-prior-pit-v1+verified-capacity-v1`

Estimator remains the current production estimator:

```python
ExtraTreesRegressor(
    n_estimators=500,
    min_samples_leaf=3,
    max_features=0.8,
    random_state=42,
    n_jobs=-1,
)
```

The occupancy anchor is used only in the baseline / occupancy-residual target. It is not added to the estimator feature matrix in v4.

### Frozen baseline formula

Let:

- `n = season_home_n`;
- `current = season_home_mean`;
- `anchor = previous-season mean verified home occupancy * current verified capacity`;
- `k = 3`.

For clubs with a previous-season same-club occupancy anchor and `n > 0`:

`baseline_v4 = (n * current + 3 * anchor) / (n + 3)`

For `n = 0`:

`baseline_v4 = anchor`

For promoted/re-entering clubs without a same-club previous-season anchor, preserve the production `baseline_season` rather than inventing an anchor.

Prediction remains:

`P50 = baseline_v4 + predicted_occupancy_residual * current_verified_capacity`

clipped to `[0, current_verified_capacity]`.

## Rolling-origin pre-validation evidence

Occupancy-anchor coverage:

- 2021/22: 0% — no previous season in canonical dataset;
- 2022/23 onward: **83.33%** of T-30 rows; missing same-club anchors fall back to the production baseline.

### Fold A

Train: **2021/22**  
Evaluate: **2022/23**

| Metric | Current T-30 | v4 k=3 | Change |
|---|---:|---:|---:|
| MAE | 2,157.147 | **2,045.359** | **-111.788 / -5.18%** |
| Median AE | 1,182.905 | **1,031.993** | -150.912 |
| WAPE | 23.123% | **21.925%** | -1.198 pp |
| Bias | -35.841 | -39.282 | -3.441 |

### Fold B

Train: **2021/22 + 2022/23**  
Evaluate: **2023/24**

| Metric | Current T-30 | v4 k=3 | Change |
|---|---:|---:|---:|
| MAE | 2,559.741 | **2,483.202** | **-76.539 / -2.99%** |
| Median AE | **1,371.231** | 1,379.429 | +8.198 |
| WAPE | 20.463% | **19.851%** | -0.612 pp |
| Bias | -433.388 | -508.741 | -75.353 |

### Combined rolling-origin evidence

N = **587**.

| Metric | Current T-30 | v4 k=3 | Change |
|---|---:|---:|---:|
| MAE | 2,358.101 | **2,263.908** | **-94.193 / -3.994%** |
| Median AE | 1,296.796 | **1,230.856** | -65.940 |
| WAPE | 21.601% | **20.738%** | -0.863 pp |
| Bias | -234.276 | -273.612 | -39.336 |

The candidate passes the pre-validation gate:

- improves Fold A MAE: **YES**;
- improves Fold B MAE: **YES**;
- combined MAE improvement >=3%: **YES — 3.994%**;
- bias remains materially more balanced than the stronger-shrinkage k=5/k=8 alternatives.

## Why k=3 was frozen instead of k=8

`k=8` had the lowest combined rolling-origin MAE (**2,250.522; -4.562%**) but materially worsened underprediction bias:

- combined bias: **-417.365**;
- Fold B bias: **-704.822**.

`k=3` retains most of the MAE benefit while keeping combined bias much closer to the production control. The governance policy requires stability review instead of selecting by MAE alone.

This choice was made before scoring the exposed 2024/25 + 2025/26 historical regression sets.

## Regression-validation status

As of this commit, the frozen k=3 candidate has not been scored on 2024/25 or 2025/26 in the v4 cycle.

Those seasons are exposed fixed historical regression sets, not pristine untouched holdouts. The next step is one fixed regression-validation pass for this exact spec. No `k`, estimator, formula or fallback change is allowed after those results are observed within v4.

No production runtime, artifact, registry or live forecast is changed by this document.
