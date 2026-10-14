# Beyond Global Forecast v2.1 — Challenger Matrix — 2026-10-14

## Objective

Improve the five-season Global Forecast v2 without changing the leakage-safe evaluation protocol.

Candidate selection remains development-only. A challenger is considered stronger only when it improves the frozen Global v2 configuration on development and does not show a contradictory result across the two untouched holdout seasons.

## Challenger A — match importance / interaction features

Added point-in-time derived features:

- combined match quality from home + away PPG;
- absolute PPG gap;
- absolute table-position gap;
- combined table strength;
- top-4 / bottom-4 indicators;
- late-season × top/bottom-table interactions;
- combined recent form and absolute form gap;
- rest gap and fixture-congestion sum;
- home recent-attendance / historical-mean ratio;
- home current-season / historical-mean ratio;
- opponent-demand × season-progress and weekend interactions.

### Result

| Horizon | Development | 2024/25 | 2025/26 | Decision |
|---|---:|---:|---:|---|
| T-30 | 2842 → **2759** | 2199 → **2144** | 2185 → **2091** | PROMOTE challenger spec |
| T-14 | 2558 → **2491** | 2027 → **1910** | 2020 → **1969** | PROMOTE challenger spec |
| T-7 | 2602 → **2466** | **1936** → 1964 | 1983 → **1964** | REJECT: mixed holdout |
| T-3 | 2607 → **2498** | 1968 → **1906** | **1911** → 1934 | REJECT: mixed holdout |
| T-1 | 2604 → **2494** | 1930 → **1894** | 1918 → **1871** | PROMOTE challenger spec |

Interpretation: interactions are useful, but they are horizon-dependent. They should not be globally switched on for every checkpoint.

## Challenger B — occupancy-ratio target

Instead of predicting attendance residuals directly, the challenger predicts residual occupancy:

`attendance / capacity_proxy - baseline_attendance / capacity_proxy`

`capacity_proxy` is the maximum eligible historical home attendance observed strictly before the target `as_of_at`. It is therefore leakage-safe, but it is still only a proxy for stadium capacity and should later be replaced by verified stadium-capacity history.

### Result

| Horizon | Development | 2024/25 | 2025/26 | Decision |
|---|---:|---:|---:|---|
| T-30 | **2842** → 2868 | not opened | not opened | REJECT on development |
| T-14 | 2558 → **2532** | 2027 → **1962** | 2020 → **1996** | PROMOTE challenger spec |
| T-7 | **2602** → 2654 | not opened | not opened | REJECT on development |
| T-3 | 2607 → **2580** | 1968 → **1836** | 1911 → **1843** | PROMOTE challenger spec |
| T-1 | 2604 → **2585** | 1930 → **1836** | 1918 → **1805** | PROMOTE challenger spec |

The strongest current point result is **T-1 occupancy: MAE 1804.6 on 2025/26**.

## Best validated historical configuration after v2.1 experiments

| Horizon | Best spec | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| T-30 | Global v2 + importance/interactions | **2143.6** | **2090.8** |
| T-14 | Global v2 + importance/interactions | **1909.5** | **1969.1** |
| T-7 | Global v2 | **1936.1** | **1982.9** |
| T-3 | Global v2 occupancy target | **1835.6** | **1843.4** |
| T-1 | Global v2 occupancy target | **1835.5** | **1804.6** |

## Decisions

1. Do not replace every horizon with one universal feature/target contract.
2. Keep horizon-specific model contracts; evidence now supports different winners by checkpoint.
3. Treat verified historical stadium capacity as a high-priority new data source because the leakage-safe occupancy proxy improved T-14/T-3/T-1.
4. Preserve the original Global v2 T-7 model; both current v2.1 challengers failed the promotion rule there.
5. No production promotion is made yet. These are historical champion candidates to be frozen and then challenged by ticketing trajectory / weather / hype under the same evaluation discipline.

## Next experiment priority

1. Replace `capacity_proxy` with actual point-in-time stadium-capacity history and re-run the occupancy challenger.
2. Add ticketing trajectory on top of the stronger historical baseline.
3. Add calibrated quantile models for P10/P50/P90 using the final point-model feature contract.
4. Only then test Weather/Hype as incremental feature families.
