# Beyond Ticketing — Current-Season Regime Maturity v1

Last updated: **2026-10-18**

Status: **ACTIVE FIXED-CONFIG AUDIT / b2 / NO PRODUCTION CHANGE**

## Purpose

Audit the three final b2 v1 development-selected same-season regime candidates without any further signal/model selection:

- T-7: `ewma50-resid-k6-cap05`;
- T-3: `ewma50-resid-k2-cap05`;
- T-1: `ewma50-resid-k6-cap05`.

T-30 and T-14 are excluded because b2 v1 selected `NO_ADJUSTMENT`.

This audit does **not** choose a new shrinkage, cap, statistic, maturity gate or horizon. It asks whether the frozen signals are stable enough across seasons, maturity stages, clubs and tails to justify a later freeze decision.

## Inherited PIT contract

The audit uses the exact canonical b2 v1 state builder.

A source residual is visible only when:

`source kickoff + 3h < target as_of_at`

A snapshot at exactly the completion timestamp still cannot use that result.

No future/uncompleted outcome is allowed.

## Frozen variants

### T-7

`ewma50-resid-k6-cap05`

- EWMA alpha 0.50;
- shrink `n/(n+6)`;
- correction cap ±5% verified capacity.

### T-3

`ewma50-resid-k2-cap05`

- EWMA alpha 0.50;
- shrink `n/(n+2)`;
- correction cap ±5% verified capacity.

### T-1

`ewma50-resid-k6-cap05`

Same contract as T-7.

No variant changes are allowed inside this audit.

## Rolling folds

1. train 2021/22 -> evaluate 2022/23;
2. train through 2022/23 -> evaluate 2023/24;
3. train through 2023/24 -> evaluate 2024/25;
4. train through 2024/25 -> evaluate 2025/26.

Roles:

- 2022/23 and 2023/24 = b2 development evidence;
- 2024/25 and 2025/26 = already-exposed references.

The audit does not turn reference seasons into fresh validation.

## Required diagnostics

### Overall per fold

- MAE / median AE / p90 / bias / WAPE;
- paired event-level bootstrap of mean absolute-error improvement;
- 10,000 bootstrap samples;
- 95% percentile interval;
- probability mean uplift > 0;
- exact worst-event degradation inherited from canonical scorecard;
- degradation quantiles p50/p75/p90/p95/p99/max;
- harmful regression rates >500 / >1,000 / >2,000 / >3,000 seats.

### Signal maturity

Score separately when the target snapshot has:

- 0 earlier completed same-season home matches;
- 1;
- 2;
- 3+.

For every bucket:

- n;
- base MAE;
- candidate MAE;
- MAE improvement;
- median AE;
- p90 AE;
- paired bootstrap.

This is diagnostic only. The audit does **not** create or select a maturity gate.

### Club consistency

For home-club season cells with at least 5 events:

- base MAE;
- candidate MAE;
- improvement;
- improved/worsened state.

## Reproduction

The fixed variant IDs are hard-asserted.

The audit calls canonical b2 functions for:

- base prediction;
- same-season PIT state;
- variant application;
- scorecard.

An independent replay path must reproduce canonical b2 candidate MAE to `1e-9` per fold.

## Governance

`promotion_allowed = false`

Production remains unchanged.

The result may support one of three follow-up decisions:

1. freeze a b2 layer unchanged as historical Pre-Live candidate evidence;
2. design one materially different maturity/reliability hypothesis **only if development evidence supports it before references are used**;
3. reject the b2 layer for a horizon and continue with no current-season adjustment.

Do not tune maturity thresholds from exposed references.

## Files

Implementation:

`ml/current_season_regime_maturity_v1.py`

Tests:

`ml/test_current_season_regime_maturity_v1.py`

Workflow:

`.github/workflows/current-season-regime-maturity-v1.yml`
