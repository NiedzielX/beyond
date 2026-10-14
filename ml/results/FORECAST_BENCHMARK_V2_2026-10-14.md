# Beyond Forecast Benchmark v2 — 2026-10-14

Status: **completed in GitHub Actions**  
Horizon: **T-7**  
Production impact: **none**

## Objective

Test whether changing model family / regularisation / ensembling can materially improve the exact leakage-safe recovered v1.7 T-7 forecasting setup **without changing the information available to the model**.

## Protocol

- exact recovered v1.7 point-in-time T-7 features;
- prior-season-only training fold;
- opponent frequency gate preserved;
- capacity cap preserved;
- development seasons: **2022/23 + 2023/24** (34 matches);
- untouched holdout: **2024/25 + 2025/26** (34 matches);
- candidate selection: development MAE, then WAPE, then absolute bias;
- holdout not used for candidate selection;
- v1.7 reproduction required to pass before benchmarking.

## Reproducibility gate

Recovered v1.7 T-7 was reproduced across all 68 OOS matches with:

- mean absolute prediction difference: ~`1.22e-11` persons;
- maximum absolute prediction difference: ~`4.73e-11` persons.

Therefore the benchmark is comparing candidates against the exact historical champion, not an approximation.

## Candidate families

The tournament included:

- Ridge (multiple alphas);
- Elastic Net;
- Huber robust regression;
- Gradient Boosting;
- HistGradientBoosting;
- Extra Trees;
- Random Forest;
- family-diverse ensembles.

## Development result

The development-only winner was:

`ensemble_family_inverse_mae`

Members:

- `v17_ridge_a0_3`;
- `elastic_a0_01_l10_1`;
- `extra_trees_leaf2_mf0_7`.

Development MAE:

- v1.7: **4507.3**;
- selected ensemble: **4503.0**.

Improvement: only **~4.3 people MAE**.

This was already a very weak development advantage.

## Untouched holdout result

| Metric | v1.7 champion | Dev-selected ensemble |
|---|---:|---:|
| MAE | **3794.9** | 4159.6 |
| Median AE | **3420.1** | 3810.4 |
| RMSE | **4610.3** | 4893.0 |
| MAPE | **14.08%** | 15.70% |
| WAPE | **12.65%** | 13.86% |
| Bias | -368.6 | **-105.9** |
| P90 absolute error | **7155.5** | 7399.5 |
| Within ±10% | **44.1%** | 41.2% |

Holdout MAE degradation versus v1.7: **+364.8 people**.

Decision: **KEEP v1.7**.

## Interpretation

The experiment strongly suggests that, on the current exact T-7 feature set, **model-family complexity is not the bottleneck**.

A family-diverse ensemble could fit the development period marginally better, but the gain disappeared and reversed materially on the untouched holdout. This is consistent with overfitting to a small historical feature space rather than discovering a stronger predictive relationship.

This result is consistent with earlier v1.7/v1.8 research in which more complex direct nonlinear models did not materially beat the frozen baseline.

## Modelling implication

Do **not** spend the next sprint adding more algorithms to the same T-7 inputs.

The next meaningful improvement must come primarily from **new predictive information**, a broader training population, or a better temporal representation.

Priority candidates:

1. build a larger historical multi-club dataset and train a global model with club-specific effects/calibration;
2. canonicalise point-in-time features in the Feature Store;
3. incorporate live ticket trajectory as a true model feature/correction where historical snapshots exist;
4. expand horizon modelling so T-30/T-14/T-7/T-3/T-1 can share information where beneficial;
5. test genuinely new feature families via ablation (opponent demand/popularity, competition/stage, weather interactions, hype once evidence exists), not by assumption;
6. calibrate P10/P50/P90 probabilistically after the point model is improved.

## North-star conclusion

**The current model needs more information, not more decorative complexity.**

Any next model change should be able to answer: what new predictive information is this adding, and does it reduce unseen-match error under the same leakage-safe benchmark?
