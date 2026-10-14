# Beyond Global Forecast v2.2 — Verified Stadium Capacity — 2026-10-14

## Objective

Replace the leakage-safe max-attendance capacity proxy with verified season-specific stadium capacity and test whether occupancy-normalised modelling improves the frozen Global v2 historical model.

Evaluation protocol is unchanged:

- point-in-time features only;
- development selection: 2023/24;
- untouched holdouts: 2024/25 and 2025/26;
- no automatic production promotion.

## Capacity coverage

Verified capacity coverage is **100%** for all 1,530 historical matches.

The capacity layer includes season-specific values plus explicit venue switches where a club changed home venue during a season.

## Result

| Horizon | Development MAE | 2024/25 MAE | 2025/26 MAE | Decision vs Global v2 |
|---|---:|---:|---:|---|
| T-30 | 2842 → **2733** | 2199 → **1999** | 2185 → **1995** | PROMOTE historical challenger |
| T-14 | 2558 → **2429** | 2027 → **1870** | 2020 → **1960** | PROMOTE historical challenger |
| T-7 | 2602 → **2504** | 1936 → **1799** | 1983 → **1848** | PROMOTE historical challenger |
| T-3 | 2607 → **2547** | 1968 → **1852** | 1911 → **1832** | PROMOTE vs Global v2; mixed vs existing proxy-occupancy challenger |
| T-1 | 2604 → **2544** | 1930 → **1809** | 1918 → **1840** | PROMOTE vs Global v2; mixed vs existing proxy-occupancy challenger |

## Interpretation

Verified stadium capacity is the strongest single new feature/data layer tested so far.

It improves the frozen Global v2 model on:

- development;
- 2024/25 holdout;
- 2025/26 holdout;
- all five forecast horizons.

The largest practical change is at T-7, where MAE moves from:

- 2024/25: **1936.1 → 1799.2**;
- 2025/26: **1982.9 → 1848.0**.

This confirms that modelling demand in occupancy space is structurally useful and that the earlier max-attendance capacity proxy was capturing a real missing variable rather than producing a random uplift.

## Current horizon-specific decision after v2.2

For pure predictive quality, retain the best validated specification per horizon rather than forcing one universal contract:

- T-30: verified-capacity occupancy challenger;
- T-14: verified-capacity occupancy challenger;
- T-7: verified-capacity occupancy challenger;
- T-3: existing proxy-occupancy challenger remains narrowly better on combined two-season MAE, while verified capacity is better on 2025/26;
- T-1: existing proxy-occupancy challenger remains narrowly better on combined two-season MAE, while verified capacity is better on 2024/25.

The T-3/T-1 discrepancy should be treated as a next-experiment question, not resolved by hand-picking a preferred season.

## Next experiment

Test a single pre-registered challenger that combines:

1. verified stadium capacity;
2. match-importance / quality interactions;
3. the current horizon-specific baseline contract.

This combined challenger must be selected on development only and should only replace the current horizon winner if it improves both untouched holdout seasons or materially improves combined error without introducing instability.
