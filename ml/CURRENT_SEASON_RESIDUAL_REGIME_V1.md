# Beyond Ticketing — Current-Season Residual Regime v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / b2 / NO PRODUCTION CHANGE**

## Why this differs from Current Season Adjustment v1

The old experiment asked whether raw current-season attendance was above/below the club's historical attendance norm. That formulation was not proven.

This experiment asks:

> **Is the club currently drawing systematically above or below what our own strongest rolling Pre-Live base model expected earlier in this same season?**

This targets current-season regime change that may remain after existing Structural Prior features.

## Base model by horizon

- T-30: retained production incumbent;
- T-14: retained production incumbent;
- T-7: frozen historical candidate `hist31-leaf20-l2-1`;
- T-3: retained production incumbent;
- T-1: retained production incumbent.

No production runtime is changed by this experiment.

## PIT rule — critical

A prior home-match residual may enter current-season state only when its outcome was available **before** the target forecast timestamp.

Canonical completion:

`completed_at = kickoff_at + 3 hours`

Effective rule:

`source completed_at < target as_of_at`

The implementation uses canonical event ordering:

- snapshot priority = 0;
- completion priority = 1.

Therefore a snapshot at exactly `completed_at` is processed first and **must not** see the outcome that completes at the same timestamp.

Example:

- Match A kickoff: 10 January 12:00;
- canonical completion: 10 January 15:00;
- Match B snapshot: 10 January 14:00 -> cannot use A;
- snapshot exactly 15:00 -> still cannot use A;
- snapshot 15:00:01 or later -> may use A.

This is stricter than fixture-date ordering and is covered by unit tests.

## Same-season residual state

For every target-season match, calculate the frozen base prediction using only seasons before the target season.

When a home match completes, create two signal forms.

### Capacity-normalized residual

`residual_fraction = (actual - base_prediction) / capacity`

Input clip:

`[-0.25, +0.25]`

### Actual-vs-expected ratio

`demand_ratio = actual / base_prediction - 1`

Input clip:

`[-0.50, +0.50]`

For a target snapshot, state contains only earlier completed home matches of the same club in the same season.

## Candidate signal families

Five predeclared representations:

1. `mean_residual_fraction` — broad same-season regime level;
2. `median_residual_fraction` — robust to one exceptional prior match;
3. `ewma50_residual_fraction` — fixed alpha 0.50, stronger recency;
4. `last3_mean_residual_fraction` — explicit last-three-home-match emphasis;
5. `mean_demand_ratio` — actual/expected ratio rather than capacity residual.

Each is tested with shrinkage:

- `k=2`;
- `k=4`;
- `k=6`.

Shrinkage:

`w = n / (n + k)`

Total:

- **15 non-zero variants**;
- `NO_ADJUSTMENT` fallback.

There is no alpha grid and no cap grid.

## Correction

For residual-fraction candidates:

`raw_delta = shrink * signal * capacity`

For demand-ratio candidates:

`raw_delta = shrink * signal * base_prediction`

Safety cap:

`+/- 5% verified capacity`

Final:

`adjusted = clip(base_prediction + delta, 0, capacity)`

The first available same-season residual is allowed, but shrinkage is strongest when `n` is small.

## Development selection

Two development-era rolling seasons:

### Fold A

Train base model on 2021/22. Evaluate b2 on 2022/23.

### Fold B

Train base model on 2021/22 + 2022/23. Evaluate b2 on 2023/24.

A non-zero candidate is eligible only if:

1. MAE improves versus base in **both** development folds;
2. mean relative MAE improvement is at least **0.5%**.

Among eligible candidates:

1. find the best mean development MAE gain;
2. retain candidates with at least **90%** of that gain;
3. choose minimum maximum worst-event degradation;
4. then lower mean p90 AE delta;
5. then higher mean event-improvement rate;
6. then deterministic candidate ID.

If none passes:

`selected = NO_ADJUSTMENT`

This selection rule is frozen before reference scoring.

## Reference scoring

Only after selection, score unchanged on:

- 2024/25 — base trained through 2023/24;
- 2025/26 — base trained through 2024/25.

References do not choose:

- signal family;
- shrink k;
- cap;
- EWMA alpha;
- base model.

Evidence class:

`TWO_DEVELOPMENT_SEASONS_PLUS_EXPOSED_REFERENCES`

Therefore:

`promotion_allowed = false`

## Signal maturity diagnostics

For the selected candidate, report quality conditional on prior completed same-season home matches available at the target snapshot:

- `0`;
- `1`;
- `2`;
- `3+`.

This answers not only whether b2 helps, but **when in the season it becomes useful**.

## Required scorecard

Per candidate/fold:

- MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- worst-event degradation + identity;
- best-event improvement + identity;
- event improvement rate;
- club breakdown where sample permits;
- correction coverage;
- mean/median/p90/max correction seats;
- conditional MAE by prior same-season home-match count.

## Reproduction gates

2023/24 base MAE is hard-asserted for all five horizons.

2024/25 and 2025/26 base MAE must reproduce canonical values.

T-7 must reproduce frozen `hist31-leaf20-l2-1`, not the old production T-7 runtime.

## Files

Implementation:

`ml/current_season_residual_regime_v1.py`

Tests:

`ml/test_current_season_residual_regime_v1.py`

Workflow:

`.github/workflows/current-season-residual-regime-v1.yml`

The final result must persist run/artifact IDs and hashes, exact winner/fallback per horizon, signal-maturity diagnostics, explicit reference behavior and the next b2 decision.