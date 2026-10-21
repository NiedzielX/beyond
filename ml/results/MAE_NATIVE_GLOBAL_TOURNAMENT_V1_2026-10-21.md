# MAE-Native Global Tournament v1 — 2026-10-21

Status: **COMPLETED HISTORICAL FORWARD RESEARCH**

Production change: **none**

Evidence class: `historical_forward_fold`

## Research question

Can a genuinely different median/L1 residual estimator reduce strict time-respecting MAE versus the frozen Structural Prior Runtime v1, while holding each horizon's baseline and feature mode fixed?

## Canonical input

- historical runtime: `ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz`;
- exact SHA256: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`;
- matches: **1,530**;
- seasons: **5**;
- PIT feature rows: **7,650**;
- horizons: T-30 / T-14 / T-7 / T-3 / T-1.

No unseen claim is made. The historical seasons are already exposed research evidence.

## Validation

Reusable contract: `ml/temporal_validation_v1.py`.

Strict expanding-season folds:

1. 2021/22 + 2022/23 -> 2023/24;
2. 2021/22–2023/24 -> 2024/25;
3. 2021/22–2024/25 -> 2025/26.

For every fold:

`train_end < test_start`

Random row/snapshot splitting is not used.

## Candidates

The candidate set was declared before opening tournament results:

- `incumbent-runtime` — current frozen per-horizon runtime estimator;
- `quantile-linear-a0005` — regularized linear median regression, `q=0.50`, alpha `0.0005`;
- `quantile-linear-a002` — regularized linear median regression, `q=0.50`, alpha `0.002`;
- `gbr-l1-depth2` — GradientBoostingRegressor with `absolute_error` loss.

This is intentionally a compact hypothesis-driven tournament rather than a broad hyperparameter sweep.

## Selector

A challenger is eligible only when both conditions hold:

1. mean MAE across the three forward folds is lower than the incumbent;
2. the challenger beats the incumbent in at least **2/3** forward folds.

Ranking among eligible challengers:

1. lowest mean fold MAE;
2. lowest worst-fold degradation;
3. candidate ID.

## Results

| Horizon | Incumbent mean fold MAE | Best tested challenger | Challenger MAE | Delta vs incumbent | Fold wins | Club improvement rate | Decision |
|---|---:|---|---:|---:|---:|---:|---|
| T-30 | 2098.46 | `quantile-linear-a002` | 2157.72 | **+59.25** | 1/3 | 50.00% | RETAIN INCUMBENT |
| T-14 | 1986.28 | `quantile-linear-a002` | 2053.58 | **+67.30** | 1/3 | 50.00% | RETAIN INCUMBENT |
| T-7 | 2018.93 | `quantile-linear-a002` | 1998.16 | **-20.76** | 1/3 | 62.50% | RETAIN INCUMBENT |
| T-3 | 1916.14 | `quantile-linear-a002` | 1911.81 | **-4.33** | 2/3 | 54.17% | NEW HISTORICAL RESEARCH CHALLENGER LEAD |
| T-1 | 1914.19 | `quantile-linear-a002` | 1979.56 | **+65.38** | 1/3 | 41.67% | RETAIN INCUMBENT |

Negative delta is better.

### T-3 detail

`quantile-linear-a002` is the only challenger to pass the predeclared selector:

- incumbent mean forward-fold MAE: **1916.14**;
- challenger mean forward-fold MAE: **1911.81**;
- improvement: **4.33 seats / ~0.23%**;
- fold wins: **2/3**;
- club improvement rate: **54.17%**;
- worst fold degradation: **125.03 seats**.

This is a very small historical effect. Passing the selector makes it a research lead only; it does **not** justify replacing the frozen runtime or changing production.

### T-7 detail

`quantile-linear-a002` has a larger aggregate improvement:

- delta MAE: **-20.76 seats**;
- club improvement rate: **62.50%**.

However it wins only **1/3** temporal folds and therefore fails the predeclared consistency gate. It is not advanced.

### Other candidates

`quantile-linear-a0005` and `gbr-l1-depth2` are materially worse than the incumbent at every horizon on mean forward-fold MAE and are closed for this exact hypothesis.

## Interpretation

The main result is not that a median model broadly beats the current runtime. It does not.

The frozen Structural Prior Runtime remains strong at T-30, T-14, T-7 and T-1. A linear median residual estimator produces only a marginal T-3 signal.

Because the T-3 improvement is approximately 0.23% and one forward fold degrades by about 125 seats, the next required step is paired event/fixture uncertainty for `ΔMAE` before assigning practical importance to the result.

## CI / artifact lineage

Workflow:

`MAE-Native Global Tournament v1`

Run:

`39668550104`

Artifact:

`12378567266`

Artifact digest:

`sha256:5b9bd145124c8ee98b5fddf4849e37a2337ef66a475339a5a00b57fe76528ab1`

Artifact contains:

- `result.json` — complete machine-readable scorecards and fold manifests;
- `predictions.csv` — paired incumbent/challenger historical forward predictions.

## Decision

- T-30: `RETAIN_INCUMBENT`;
- T-14: `RETAIN_INCUMBENT`;
- T-7: `RETAIN_INCUMBENT`;
- T-3: `ADVANCE_QUANTILE_LINEAR_A002_TO_UNCERTAINTY_DIAGNOSTIC_ONLY`;
- T-1: `RETAIN_INCUMBENT`.

No frozen artifact is changed.

## Next

Run paired event/fixture-block uncertainty for T-3 `quantile-linear-a002` versus `incumbent-runtime`. T-7 `quantile-linear-a002` may be included as a diagnostic because its mean MAE is lower but temporal consistency failed.
