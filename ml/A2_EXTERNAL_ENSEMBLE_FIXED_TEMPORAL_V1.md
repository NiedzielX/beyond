# a2 External/Ensemble Fixed-Temporal Robustness Audit v1

Last updated: **2026-10-21**

Status: **COMPLETED — T-30 / T-7 / T-1 PASS 4/4 ROLLING FOLDS**

Canonical result:

`ml/results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md`

Parent closure result:

`ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`

Workflow run:

`39625425854`

Artifact ID:

`12356632426`

Result JSON SHA256:

`e6532db4bccfe567dd1eeaf3196f74d1a41a78a66eea53bc975892868ff2c900`

Artifact ZIP SHA256:

`7d9cfe2609affcb35b7c99252d42231ce1e5e55b24fbb3bb1dfd3470a0226e4e`

## Objective

Replay the exact T-30/T-7/T-1 ensemble contracts selected by the all-horizon closure audit through a stronger rolling temporal audit.

There was **no tuning or selection in this audit**.

## Exact frozen challenger contracts

### T-30

Members / weights:

- current a2 base `0.75`;
- HGB hist31 `0.00`;
- CatBoost depth6 `0.00`;
- LightGBM leaves15 `0.00`;
- XGBoost depth3 `0.25`.

### T-7

Members / weights:

- current a2 / HGB hist31 `0.25`;
- CatBoost depth4 `0.25`;
- LightGBM leaves15 `0.50`;
- XGBoost depth3 `0.00`.

### T-1

Members / weights:

- current a2 base `0.00`;
- HGB hist31 `0.25`;
- CatBoost depth4 `0.50`;
- LightGBM leaves15 `0.25`;
- XGBoost depth3 `0.00`.

Changing a member, weight, feature contract, baseline, target or hyperparameter creates a new challenger and is not permitted under this evidence package.

## Rolling folds

1. train `2021/22` -> test `2022/23` — additional pre-selection historical fold;
2. train `2021/22 + 2022/23` -> test `2023/24` — original development selection season;
3. train through `2023/24` -> test `2024/25` — exposed reference;
4. train through `2024/25` -> test `2025/26` — exposed reference.

The exact closure-run MAEs for folds 2-4 were hard reproduction gates at tolerance `1e-9`.

## Result

All three exact contracts passed the predeclared gate of positive MAE improvement in all four rolling folds.

| Horizon | Fold improvements (2022/23, 2023/24, 2024/25, 2025/26) | Mean gain | Relative mean gain | Worst event degradation | Club-season cells improved |
|---|---|---:|---:|---:|---:|
| T-30 | +5.98 / +33.50 / +54.93 / +29.74 | **+31.04** | **1.47%** | 2,855.70 | 50/72 |
| T-7 | +20.18 / +8.90 / +10.27 / +27.86 | **+16.80** | **0.87%** | 1,632.41 | 42/72 |
| T-1 | +16.48 / +55.46 / +2.27 / +6.28 | **+20.12** | **1.05%** | 2,309.70 | 38/72 |

Minimum paired-bootstrap P(improvement > 0):

- T-30 `0.6353`;
- T-7 `0.6612`;
- T-1 `0.5196`.

## Decision

- T-30: `ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`;
- T-7: `ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`;
- T-1: `ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`.

These are now **robust historical challengers**, not automatic frozen replacements.

The effect sizes remain modest and tail regressions remain material, especially the weak T-1 reference gains. Therefore the correct next step is a separately versioned Pre-Live v3 challenger, not mutation of current a2 or Frozen Pre-Live v2.

## Next required R&D step

Build a Pre-Live v3 historical candidate using:

- T-30 -> exact robust ensemble;
- T-14 -> current a2 base;
- T-7 -> exact robust ensemble;
- T-3 -> current a2 base;
- T-1 -> exact robust ensemble.

Then **revalidate the current-season regime against those new anchors**.

Existing b2 residual policies were derived relative to the old historical bases and may not be silently inherited into v3.

A new v3 cycle must compare at minimum:

1. new robust historical base only;
2. existing b2 formulation applied unchanged to the new anchor as a fixed comparator;
3. a newly selected current-season-regime challenger under a declared historical temporal boundary;
4. Frozen Pre-Live v2 as the unchanged benchmark.

Only after that package passes its own historical/fixed-temporal evidence gates may it receive a new freeze ID.

If Pre-Live v3 is later frozen, d2 must be rebuilt/revalidated against that new anchor under a new d2 version. The current frozen Ridge/P2 package remains tied to Frozen Pre-Live v2 for Track-A prospective validation.

## Production boundary

Always:

- current a2 state unchanged;
- Frozen Pre-Live v2 unchanged;
- b2 unchanged;
- c2 unchanged;
- frozen Ridge/P2 unchanged;
- `production_change = false`;
- production `live_adjustment = 0`.

## Interpretation

> **The bounded a2 external-family/ensemble gap is closed. T-30/T-7/T-1 are robust challenger inputs for the next versioned Pre-Live cycle; they do not overwrite the frozen v2 stack.**
