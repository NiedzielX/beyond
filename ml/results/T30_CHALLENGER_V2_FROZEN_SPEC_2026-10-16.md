# T-30 Challenger v2 — frozen pre-holdout specification

Date frozen: **2026-10-16**  
Status: **development-selected challenger / holdouts unopened at selection time**

## Governance

This candidate was selected using only:

- training seasons: **2021/22 + 2022/23**;
- development selection season: **2023/24**;
- untouched holdouts: **2024/25 + 2025/26 — not evaluated during selection**.

No production runtime, model registry, artifact or forecast is changed by this candidate definition.

## Frozen candidate

Model ID candidate:

`structural-prior-t30-challenger-v2-extra-leaf1-full`

Contract:

- horizon: `T-30`;
- baseline: `baseline_season`;
- feature contract: `structural-prior-pit-v1+verified-capacity-v1`;
- feature mode: full PIT features including existing validated importance interactions;
- target: verified-capacity occupancy residual;
- prediction: `baseline_season + predicted_residual * verified_capacity`;
- physical clip: `[0, verified_capacity]`.

Estimator is frozen exactly as:

```python
ExtraTreesRegressor(
    n_estimators=700,
    min_samples_leaf=1,
    max_features=1.0,
    random_state=42,
    n_jobs=-1,
)
```

No estimator, feature, target, baseline, shrinkage or blend parameter may be changed after untouched-holdout results are observed. Any change creates a new challenger/version and requires a new governance cycle.

## Development evidence

Development protocol:

- train rows: **522**;
- development rows: **293**;
- numeric features: **80**.

Reference baseline (`baseline_season`) development MAE:

**3073.8890874060467**

Current frozen T-30 Runtime v1 control development MAE:

**2559.7406941266854**

Selected challenger development MAE:

**2523.2468407441124**

Delta vs current frozen T-30 runtime:

**-36.49385338257298 MAE**

Relative development improvement:

**1.4256855573811823%**

## Selection note

The development-only search also produced close alternatives, including a 75/25 ExtraTrees + GBR blend and other ExtraTrees regularization settings. They are not carried into holdout verification. Only the single frozen candidate above is eligible for the one-time holdout read.

## Holdout decision rule

The next step is a **single verification pass**, not a new search.

Report both untouched seasons separately and combined. Do not tune after seeing them.

The challenger is not promoted automatically. Results must be documented against the current frozen T-30 runtime and reviewed under the existing model governance contract.
