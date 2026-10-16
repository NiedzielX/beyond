# T-30 Cold Start v5 — rolling-origin pre-validation result

Date: **2026-10-16**  
Decision: **STOPPED AT PRE-VALIDATION / NO HISTORICAL REGRESSION READ / NO PRODUCTION CHANGE**

## Hypothesis

Historical occupancy support should affect T-30 only while current-season home evidence is sparse, then revert exactly to the production `baseline_season`.

Candidate family:

- prior strength `k ∈ {1,2,3}`;
- historical support active only while `season_home_n <= max_n`, where `max_n ∈ {1,2,3}`;
- production ExtraTrees estimator and feature matrix unchanged.

Governance:

`ml/T30_RND_GOVERNANCE_V2.md`

Only rolling-origin pre-validation was used:

- Fold A: train 2021/22 -> evaluate 2022/23;
- Fold B: train 2021/22 + 2022/23 -> evaluate 2023/24.

2024/25 and 2025/26 were **not scored** in this experiment.

## Best observed candidate

`cold_start_occ_k2_maxn3`

Affected rolling-origin evaluation rows:

- 159 / 587 = **27.09%**.

### Fold A

| Metric | Current T-30 | v5 best | Change |
|---|---:|---:|---:|
| MAE | **2,157.147** | 2,191.488 | **+34.341 / 1.59% worse** |
| Median AE | 1,182.905 | 1,182.905 | 0 |
| WAPE | **23.123%** | 23.491% | +0.368 pp |
| Bias | -35.841 | +40.203 | crosses zero |

### Fold B

| Metric | Current T-30 | v5 best | Change |
|---|---:|---:|---:|
| MAE | 2,559.741 | **2,504.569** | **-55.172 / 2.16% better** |
| Median AE | **1,371.231** | 1,393.962 | +22.730 |
| WAPE | 20.463% | **20.021%** | -0.441 pp |
| Bias | -433.388 | **-333.798** | +99.590 toward zero |

### Combined rolling-origin

N = **587**.

| Metric | Current T-30 | v5 best | Change |
|---|---:|---:|---:|
| MAE | 2,358.101 | **2,347.762** | **-10.339 / 0.44% better** |
| Median AE | **1,296.796** | 1,309.946 | +13.150 |
| WAPE | 21.601% | **21.506%** | -0.095 pp |
| Bias | -234.276 | **-146.479** | +87.797 toward zero |

## Gate result

Required:

- improve Fold A: **NO**;
- improve Fold B: **YES**;
- improve every rolling-origin fold: **NO**;
- combined MAE improvement >= 3%: **NO — only 0.44%**.

`passing_candidate_count = 0`

Therefore the experiment stops here.

## Decision

- do not score 2024/25 or 2025/26;
- do not freeze a v5 candidate for prospective shadow;
- do not change production runtime/artifacts/registry;
- close PR without merge;
- do not continue tuning `k` or `max_n` from these results.

The baseline-anchoring family (v3-v5) has now produced inconsistent behavior across rolling folds and exposed fixed regression seasons. The next R&D step should be a pre-validation-only error audit of the current production T-30 runtime to identify a structural residual pattern that is stable across both rolling-origin folds before defining another challenger family.
