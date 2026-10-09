# Beyond Historical Model Tournament v1.3

## Result
**v1.7 stays champion. No production change.**

I rebuilt the challenger tournament with a strict as-of rule:
for every target match, both training outcomes and dynamic features must have
existed before the actual forecast checkpoint.

### T-30
Selected on dev only:
**87.5% v1.7 + 12.5% leakage-safe direct Ridge challenger**

| Slice | v1.7 MAE | Challenger MAE | Improvement |
|---|---:|---:|---:|
| Dev 2022/23–2023/24 | 4571 | 4429 | 3.11% |
| Holdout 2024/25–2025/26 | 4876 | 4846 | 0.62% |
| All 68 OOS | 4724 | 4638 | 1.83% |

Season-block bootstrap probability of improvement: **94.8%**,
but the 95% paired MAE-delta interval still crosses zero
(-22 to 165 people).

So this is a research challenger, not a new champion.

### T-7
The best conservative stage correction selected on dev gives:

| Slice | v1.7 MAE | Challenger MAE | Improvement |
|---|---:|---:|---:|
| Dev | 4507 | 4451 | 1.24% |
| Holdout | 3795 | 3788 | 0.19% |
| All 68 OOS | 4151 | 4120 | 0.76% |

This is too small to promote.

### What failed
- leakage-safe direct Ridge models: worse than v1.7 alone
- LightGBM/XGBoost-style nonlinear models: materially worse
- strict T-7 residual stacking: no robust improvement
- rolling bias correction: no robust holdout gain
- adding more context does not solve demand shocks

## Interpretation
The historical/context information appears close to saturation for this sample.
The next material accuracy gain is much more likely to come from **new demand
information** (true as-of ticket signal / sales trajectory) than from a fancier
algorithm over the same historical inputs.
