# T-30 Pre-validation Error Audit v1

Date: **2026-10-16**  
Status: **diagnostic complete / no production change**

Runtime audited:

`structural-prior-runtime-v1-t30-extra-full`

Governance:

- Fold A: train 2021/22 -> evaluate 2022/23;
- Fold B: train 2021/22 + 2022/23 -> evaluate 2023/24;
- 2024/25 and 2025/26 were not scored;
- minimum eligible segment size: 15 rows in each fold;
- diagnostic only; no candidate or production mutation.

## Overall control

| Fold | N | MAE | Median AE | Bias | WAPE |
|---|---:|---:|---:|---:|---:|
| A — 2022/23 | 294 | 2,157.1 | 1,182.9 | -35.8 | 23.12% |
| B — 2023/24 | 293 | 2,559.7 | 1,371.2 | -433.4 | 20.46% |

## Strongest stable structural pattern — low baseline occupancy

Segment:

`baseline_season / verified_capacity <= 45%`

| Fold | N | MAE | MAE vs fold | Bias | WAPE |
|---|---:|---:|---:|---:|---:|
| A | 108 | 2,737.8 | **1.27x** | **-641.0** | 28.22% |
| B | 51 | 4,532.9 | **1.77x** | **-2,512.1** | 38.65% |

This is the clearest actionable pattern because it combines:

- the same underprediction direction in both folds;
- materially elevated error in both folds;
- a direct mechanistic link to the current target architecture.

The Structural Prior predicts an occupancy residual:

`attendance / capacity - baseline / capacity`

but the estimator currently receives `baseline_season` and `capacity` as separate numeric inputs. It does not receive the explicit ratio `baseline_season / capacity` as its own feature.

This creates a coherent v6 hypothesis: expose baseline occupancy state directly to the estimator rather than adding another manual baseline correction.

## Other stable patterns

### High long-run home demand

`home_demand_vs_league_median = high`

| Fold | N | MAE | MAE vs fold | Bias |
|---|---:|---:|---:|---:|
| A | 133 | 3,299.7 | 1.53x | -272.9 |
| B | 144 | 3,570.3 | 1.39x | -762.6 |

Stable high error and underprediction, but this feature is already present in the model. It is therefore secondary to the missing explicit occupancy state.

### Any bottom-four team

| Fold | N | MAE | MAE vs fold | Bias |
|---|---:|---:|---:|---:|
| A | 117 | 2,424.3 | 1.12x | -516.0 |
| B | 119 | 3,012.8 | 1.18x | -804.0 |

Stable underprediction and elevated error. Existing importance interactions already include `bottom4_any`, so no new challenger is justified from this segment alone.

### Home team in top four

| Fold | N | MAE | MAE vs fold | Bias |
|---|---:|---:|---:|---:|
| A | 70 | 2,674.9 | 1.24x | -1,058.1 |
| B | 69 | 3,005.3 | 1.17x | -287.8 |

Stable high error and underprediction. Position and top-four interactions are already in the feature contract.

### Capacity 35k+

| Fold | N | MAE | MAE vs fold | Bias |
|---|---:|---:|---:|---:|
| A | 51 | 4,024.5 | 1.87x | +390.6 |
| B | 46 | 7,018.1 | 2.74x | -2,597.5 |

Very high error but **bias direction flips**, so this is not a clean correction target by itself.

### Zero current-season home matches

| Fold | N | MAE | Bias |
|---|---:|---:|---:|
| A | 41 | 3,046.5 | -765.1 |
| B | 38 | 1,977.0 | -1,541.6 |

Stable underprediction, but v3-v5 already tested multiple historical-anchor approaches. Those experiments did not generalize robustly enough to justify another baseline-anchor variant.

## Protective / low-error occupancy regimes

`baseline occupancy 65–85%` is consistently easier:

- Fold A MAE: 1,517.6 = 0.70x fold MAE;
- Fold B MAE: 1,534.8 = 0.60x fold MAE.

`baseline occupancy 85%+` is easier still in MAE terms.

This supports the interpretation that the model's hardest regime is specifically low expected occupancy rather than capacity alone.

## Decision

The next T-30 challenger should test a **new explicit occupancy-state feature**, not another baseline smoothing rule.

Pre-registered v6 hypothesis:

`baseline_occupancy = baseline_season / verified_capacity`

Properties:

- deterministic;
- point-in-time safe;
- available in both historical and current-event runtime;
- directly aligned with the occupancy-residual target;
- does not require new external data;
- does not encode target attendance.

v6 should keep the production estimator, target, baseline and existing feature set unchanged and add only this explicit feature first. Selection remains rolling-origin only under `ml/T30_RND_GOVERNANCE_V2.md`. If it passes the pre-validation gate, the next meaningful validation is prospective 2026/27 shadow evidence rather than repeated tuning on exposed 2024/25–2025/26 regression seasons.
