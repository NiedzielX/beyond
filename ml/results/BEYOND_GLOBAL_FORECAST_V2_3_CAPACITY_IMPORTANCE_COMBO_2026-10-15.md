# Beyond Global Forecast v2.3 — Verified Capacity + Match Importance — 2026-10-15

## Objective

Test whether combining the two strongest historical information layers — verified stadium capacity and point-in-time match-importance / quality interactions — improves the current five-season historical model.

Protocol remains leakage-safe and season-blocked:

- 2021/22–2022/23 train → 2023/24 development gate;
- accepted specification refit on 2021/22–2023/24 → 2024/25 holdout;
- same accepted specification refit on 2021/22–2024/25 → 2025/26 holdout;
- 2024/25 and 2025/26 are not used to accept/reject the challenger;
- one closed-doors match remains excluded from demand training.

## Development gate

The combined challenger passed the development gate only at **T-3** and **T-1**.

It did not improve development at T-30, T-14 or T-7, so it is rejected there without using holdout behaviour to rescue it.

## Accepted challenger results

| Horizon | 2024/25 MAE | 2025/26 MAE | Combined MAE | Previous best combined MAE | Improvement |
|---|---:|---:|---:|---:|---:|
| T-3 | **1701.4** | **1686.4** | **1693.9** | ~1839.5 | **~7.9%** |
| T-1 | **1684.3** | **1682.0** | **1683.1** | ~1820.0 | **~7.5%** |

Combined holdout size: **603 matches** per accepted horizon.

Additional robustness checks:

- T-3 combined bias: approximately **-31** attendees;
- T-1 combined bias: approximately **-152** attendees;
- T-3 median absolute error: approximately **1,048**;
- T-1 median absolute error: approximately **1,090**.

Bootstrap 95% intervals for absolute-error MAE:

- T-3: approximately **1,524–1,871**;
- T-1: approximately **1,514–1,860**.

## Decision

- **T-3:** promote as historical champion candidate.
- **T-1:** promote as historical champion candidate.
- **T-30 / T-14 / T-7:** reject this combined challenger because it fails the development gate.

This strengthens the case for horizon-specific model contracts rather than one universal feature set.

## Product implication

The best point forecast is now around **1.68–1.69k MAE** close to kickoff, but Beyond's business priority remains earlier actionable forecasting. Therefore the next predictive work is not further T-1 tuning; it is adding proprietary ticketing trajectory evidence to **T-30 / T-14**.

No production activation is performed by this result.
