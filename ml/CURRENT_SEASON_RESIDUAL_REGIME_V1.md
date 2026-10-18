# Beyond Ticketing — Current-Season Residual Regime v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / b2 / NO PRODUCTION CHANGE**

## Why this is different from Current Season Adjustment v1

The old `CURRENT_SEASON_ADJUSTMENT_V1` asked:

> Is current-season raw attendance above/below the club's historical attendance norm?

That formulation was not proven.

This experiment asks instead:

> **Is the club currently drawing systematically above or below what our own strongest Pre-Live base model expected earlier in this same season?**

This isolates a current-season regime shift that may remain after Structural Prior's existing current-season features.

## Base model state

Use the strongest current historical Pre-Live candidate per horizon:

- T-30: retained production incumbent;
- T-14: retained production incumbent;
- T-7: frozen historical candidate `hist31-leaf20-l2-1`;
- T-3: retained production incumbent;
- T-1: retained production incumbent.

No production runtime is changed by this experiment.

## PIT rule — critical

A previous home-match residual may enter current-season regime state only when that previous match is actually completed at the current forecast timestamp.

Canonical completion time:

`completed_at = kickoff_at + 3 hours`

For every current snapshot:

`previous completed_at <= current as_of_at`

This is stricter than simply ordering matches by fixture date.

Example:

- Match A kickoff: 10 January 12:00;
- Match A completion state: 10 January 15:00;
- Match B T-30 snapshot: 10 January 14:00.

Match B **must not** use Match A's attendance residual yet.

A snapshot at 16:00 may use it.

The implementation stores the latest completion timestamp used and hard-fails if future completion leakage is detected.

## Same-season residual state

For every target-season home match, first calculate the frozen base prediction using only training seasons before the target season.

When a match completes, create:

### Capacity-normalized residual

`residual_fraction = (actual - base_prediction) / capacity`

Input clip:

`[-0.25, +0.25]`

### Actual-vs-expected ratio

`demand_ratio = actual / base_prediction - 1`

Input clip:

`[-0.50, +0.50]`

For every home club, maintain only residuals from earlier completed home matches in the same season.

## Candidate signal families

Three materially different same-season representations:

1. `mean_residual_fraction` — mean capacity-normalized residual;
2. `ewma_residual_fraction` — EWMA of residual fraction with fixed alpha `0.50`;
3. `mean_demand_ratio` — mean actual/expected ratio.

Each signal is tested with shrinkage:

- `k=2`;
- `k=4`;
- `k=6`.

Shrinkage:

`w = n / (n + k)`

A signal becomes available after the first earlier completed same-season home match. The first match is automatically strongly shrunk.

Total:

- 9 non-zero variants;
- `NO_ADJUSTMENT` fallback.

No alpha/cap grid is added.

## Correction

For residual-fraction candidates:

`raw_delta = shrink * residual_signal * capacity`

For demand-ratio candidates:

`raw_delta = shrink * ratio_signal * base_prediction`

Safety cap:

`+/- 5% verified capacity`

Final:

`adjusted = clip(base_prediction + delta, 0, capacity)`

## Selection protocol

Candidate selection uses two development-era rolling seasons only.

### Development Fold A

Train base model:

- 2021/22.

Evaluate current-season regime:

- 2022/23.

### Development Fold B

Train base model:

- 2021/22 + 2022/23.

Evaluate current-season regime:

- 2023/24.

A candidate is eligible only if:

1. MAE improves versus base in **both** development folds;
2. mean relative MAE improvement is at least **0.5%**.

Among eligible candidates:

1. identify the best mean development MAE gain;
2. keep candidates retaining at least **90%** of that gain;
3. choose minimum maximum worst-event degradation;
4. then lower mean p90 AE delta;
5. then higher mean event-improvement rate;
6. then deterministic candidate ID.

If no candidate passes:

`selected = NO_ADJUSTMENT`

## Reference scoring

Only after development selection is frozen, evaluate unchanged on:

1. 2024/25 — base trained through 2023/24;
2. 2025/26 — base trained through 2024/25.

The references do not select:

- signal source;
- shrink `k`;
- cap;
- EWMA alpha;
- base model.

Evidence class:

`EXPOSED_HISTORICAL_REFERENCE_SEASONS`

Therefore:

`promotion_allowed = false`

## Signal-maturity diagnostics

For the selected candidate, report MAE conditional on the number of earlier completed same-season home matches available at the forecast timestamp:

- `0`;
- `1`;
- `2`;
- `3+`.

This is necessary because b2 should answer not only whether current-season regime helps, but **when in the season it starts becoming useful**.

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
- mean/median/max correction seats;
- conditional MAE by prior same-season home-match count.

## Reproduction gates

Reference base MAE must reproduce canonical values.

For T-7, the experiment must reproduce frozen `hist31-leaf20-l2-1` exactly for all canonical seasons where an expected value exists.

For other horizons, retained Structural Prior benchmarks remain hard-asserted where canonical expected values exist.

## Files

Implementation:

`ml/current_season_residual_regime_v1.py`

Tests:

`ml/test_current_season_residual_regime_v1.py`

Workflow:

`.github/workflows/current-season-residual-regime-v1.yml`

The final result must later persist run/artifact hashes, exact winner per horizon, signal-maturity diagnostics and the explicit advance/reject decision.
