# Structural Prior Runtime v1 — early-horizon benchmark

Status: **historical champion candidate / executable runtime recovery**  
Date: **2026-10-15**

## Protocol

Selection uses **2023/24 only** after training on 2021/22–2022/23. 2024/25 and 2025/26 are untouched holdouts.

The feature layer is rebuilt point-in-time from the validated five-season canonical inputs:

- 1,530 matches;
- 7,650 horizon snapshots;
- T-30 / T-14 / T-7 / T-3 / T-1;
- attendance history may carry across seasons;
- sporting state resets every season;
- a match enters historical state only after `kickoff + 3h`;
- the known closed-door zero-attendance match is retained as historical truth but excluded from demand training;
- verified historical stadium capacity is available for every target.

Target architecture:

`occupancy_residual = attendance / capacity - baseline / capacity`

Prediction:

`P50 = baseline + predicted_occupancy_residual * capacity`

Final prediction is clipped to `[0, verified_capacity]`.

## Frozen early-horizon winners

| Horizon | Baseline | Feature set | Estimator | Dev 2023/24 MAE | 2024/25 MAE | 2025/26 MAE |
|---|---|---|---|---:|---:|---:|
| T-30 | current-season home mean with PIT fallback | full PIT + importance interactions | ExtraTrees, 500 trees, leaf=3, max_features=0.8 | **2,559.7** | **1,889.4** | **1,846.3** |
| T-14 | rolling-3 home attendance | base PIT | HistGradientBoosting absolute-error | **2,340.0** | **1,748.5** | **1,870.4** |
| T-7 | current-season home mean with PIT fallback | base PIT | GradientBoosting Huber, 180 trees, depth=2, leaf=8 | **2,476.8** | **1,777.7** | **1,802.3** |
| T-3 | current-season home mean with PIT fallback | full PIT + importance interactions | HistGradientBoosting absolute-error, 250 iterations | **2,311.6** | **1,661.7** | **1,775.1** |

T-30 holdout diagnostics:

- 2024/25: median AE **1,173.3**, WAPE **14.81%**, bias **+538.6**;
- 2025/26: median AE **1,186.2**, WAPE **13.56%**, bias **+44.9**.

T-14 holdout diagnostics:

- 2024/25: median AE **883.3**, WAPE **13.73%**, bias **-99.4**;
- 2025/26: median AE **1,231.0**, WAPE **13.75%**, bias **-361.0**.

## T-7 executable-runtime recovery

The T-7 estimator/baseline contract was inherited from the previously approved verified-capacity v2.2 champion before the executable-runtime verification gate:

- baseline: `baseline_season`;
- estimator: `GradientBoostingRegressor(loss="huber", n_estimators=180, learning_rate=0.03, max_depth=2, min_samples_leaf=8, random_state=42)`;
- feature mode: base PIT features;
- target: verified-capacity occupancy residual.

Structural Prior Runtime v1 uses the canonical `structural-prior-pit-v1+verified-capacity-v1` feature contract, so exact equality with the older `global-pit-v2+verified-capacity-v1` benchmark was not assumed. The pre-specified executable T-7 runtime was verified once against development and both untouched holdouts before production activation.

Exact pinned verification values:

- development 2023/24: **2,476.8168272009416**;
- holdout 2024/25: **1,777.6927306628588**;
- holdout 2025/26: **1,802.2755802253876**.

For comparison, the previous published v2.2 T-7 benchmark was approximately **2,504** on development, **1,799.2** on 2024/25 and **1,848.0** on 2025/26. The executable Structural Prior v1 contract therefore improves the pre-specified T-7 candidate on development and both untouched holdouts without a post-holdout parameter search.

## T-3 executable-runtime recovery

The T-3 runtime contract was fixed before the recovery gate from the approved Global v2.3 verified-capacity + match-importance champion lineage:

- baseline: `baseline_season`;
- estimator: `HistGradientBoostingRegressor(loss="absolute_error", learning_rate=0.05, max_iter=250, max_leaf_nodes=15, min_samples_leaf=10, l2_regularization=1.0, random_state=42)`;
- feature mode: full PIT features including validated importance interactions;
- target: verified-capacity occupancy residual.

The older v2.3 result used the `global-pit-v2` lineage and was recorded as a historical benchmark rather than an executable current-event artifact. Structural Prior Runtime v1 therefore performed a one-time verification of the already-fixed T-3 architecture on the canonical `structural-prior-pit-v1+verified-capacity-v1` contract. No estimator, baseline or feature search was performed after observing either holdout.

Exact pinned verification values:

- development 2023/24: **2,311.6246893162593**;
- holdout 2024/25: **1,661.715966441126**;
- holdout 2025/26: **1,775.069078799718**.

The previous published v2.3 T-3 holdouts were **1,701.4** and **1,686.4**. The executable Structural Prior v1 contract is therefore better on 2024/25 and worse on 2025/26; it is not claimed to dominate the older historical benchmark. It is frozen because it is the pre-specified, leakage-safe executable conversion required to keep a genuine Structural Prior anchor through T-3 without falling back to a legacy model. Any further T-3 model improvement must be evaluated as a separate challenger under the normal governance protocol.

## Comparison with previous verified-capacity lineage

| Horizon | Previous reference 2024/25 | Previous reference 2025/26 | Runtime v1 2024/25 | Runtime v1 2025/26 |
|---|---:|---:|---:|---:|
| T-30 | 1,998.7 | 1,994.6 | **1,889.4** | **1,846.3** |
| T-14 | 1,869.8 | 1,960.3 | **1,748.5** | **1,870.4** |
| T-7 | 1,799.2 | 1,848.0 | **1,777.7** | **1,802.3** |
| T-3 | **1,701.4** | **1,686.4** | **1,661.7** | 1,775.1 |

The T-30/T-14/T-7 executable runtimes improve the corresponding previous references on both untouched seasons. T-3 is a mixed contract-conversion result and is documented as such rather than retrospectively tuned against holdouts.

## Development-only search decisions

T-30:

- verified-capacity occupancy residual was better on development than attendance residual, ratio residual and direct occupancy;
- `baseline_season` was better on development than rolling-3 / rolling-5 / long-run mean alternatives;
- full PIT features + ExtraTrees leaf=3 beat the focused HistGBR / ExtraTrees / RandomForest development challengers;
- removing the physical capacity clip worsened both holdouts after the spec had already been frozen.

T-14:

- base PIT features + HistGradientBoosting remained the development winner after the focused estimator expansion;
- importance interactions did not justify replacing the base feature set at this horizon.

T-7:

- no new estimator search was performed during executable-runtime recovery;
- the estimator and `baseline_season` were inherited from the approved v2.2 T-7 champion;
- verification used the Structural Prior v1 PIT contract and confirmed an improvement on development and both untouched holdouts.

T-3:

- no new estimator search was performed during executable-runtime recovery;
- the HistGradientBoosting family, parameters, `baseline_season` and full importance feature set were fixed from the accepted v2.3 lineage before recovery verification;
- the exact Structural Prior v1 development and holdout values were then pinned without post-holdout tuning.

## Decision

- **T-30:** frozen executable Structural Prior runtime; continue R&D because it remains above the strategic `<1700 MAE` target.
- **T-14:** frozen executable Structural Prior runtime.
- **T-7:** frozen executable current-event Structural Prior runtime and automatic materialization.
- **T-3:** approved for frozen executable current-event runtime and automatic Structural Prior materialization after the versioned DB registry/resolver change is applied.
- No live ticketing feature is used in these numbers. This benchmark measures the Structural Prior only.
- **T-1 remains fail-closed** until its executable runtime is separately frozen and verified.

## Reproducibility note

Code:

- `ml/features/structural_prior_feature_store_v1.py`
- `ml/demand_engine/structural_prior_runtime.py`
- `ml/demand_engine/freeze_structural_prior_artifacts.py`

Canonical five-season history is present in Supabase and is exported through the versioned Structural Prior training export contract. Frozen artifact builds must reproduce the pinned benchmark values before fitting the final all-five-season runtime artifact. Scheduled materialization only loads frozen artifacts and predicts; it must never call model `fit()`.
