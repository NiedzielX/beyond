# T-30 Challenger v2 — untouched-holdout verification

Date: **2026-10-16**  
Decision: **REJECTED / NO PRODUCTION CHANGE**

Frozen candidate:

`structural-prior-t30-challenger-v2-extra-leaf1-full`

Frozen pre-holdout spec commit:

`2d02f247e151dc191d4af8790b87288fd5aaa68c`

The candidate was selected on 2023/24 only after training on 2021/22–2022/23. The estimator, baseline, feature contract and target were frozen before either untouched holdout was opened.

## Development selection

| Metric | Current T-30 runtime | Challenger v2 | Delta |
|---|---:|---:|---:|
| 2023/24 MAE | 2,559.741 | **2,523.247** | **-36.494** |

Development relative improvement: **1.43%**.

## Untouched holdouts

### 2024/25

| Metric | Current runtime | Challenger v2 | Delta challenger vs current |
|---|---:|---:|---:|
| MAE | 1,889.367 | **1,882.692** | **-6.675** |
| Median AE | 1,173.335 | **1,069.522** | -103.813 |
| WAPE | 14.811% | **14.759%** | -0.052 pp |
| Bias | +538.604 | +639.392 | +100.788 |

Challenger improvement in MAE: **0.35%**.

### 2025/26

| Metric | Current runtime | Challenger v2 | Delta challenger vs current |
|---|---:|---:|---:|
| MAE | **1,846.279** | 1,876.383 | **+30.104** |
| Median AE | **1,186.210** | 1,249.568 | +63.358 |
| WAPE | **13.564%** | 13.785% | +0.221 pp |
| Bias | **+44.945** | +95.389 | +50.444 |

Challenger degradation in MAE: **1.63%**.

## Combined untouched holdouts

N = **599** matches.

| Metric | Current runtime | Challenger v2 | Delta challenger vs current |
|---|---:|---:|---:|
| MAE | **1,867.643** | 1,879.511 | **+11.868** |
| Median AE | **1,173.335** | 1,207.035 | +33.699 |
| WAPE | **14.162%** | 14.252% | +0.090 pp |
| Bias | **+289.714** | +365.120 | +75.406 |

Combined relative change: **-0.64%** (worse).

## Decision

The challenger fails the robustness gate:

- improves both holdouts: **NO**;
- improves combined MAE: **NO**;
- reaches strategic T-30 `<1700 MAE`: **NO**.

Therefore:

- do not promote;
- do not modify the frozen production T-30 runtime;
- do not tune `leaf`, `max_features`, tree count or blend weights in response to these holdout results;
- retain `structural-prior-runtime-v1-t30-extra-full` as current T-30 runtime.

## R&D implication

A 1.43% single-development-season gain was not sufficient evidence of generalisation. Future T-30 challengers should pass a stronger **pre-holdout robustness gate** using only pre-holdout seasons, e.g. rolling-origin development folds, before either untouched holdout is read.

This result is evidence for governance tightening, not a parameter-tuning signal.
