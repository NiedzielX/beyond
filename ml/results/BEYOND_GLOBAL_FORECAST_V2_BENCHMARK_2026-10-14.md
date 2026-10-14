# Beyond Global Forecast v2 — Benchmark 2026-10-14

## Decision

**Global multi-club modelling is materially better than club-history baselines on both untouched seasons and all five forecast horizons.**

Model family / baseline selection used 2023/24 only. 2024/25 and 2025/26 were not used to select the winner.

| Horizon | Baseline | Model | 2024/25 MAE | 2025/26 MAE | Combined baseline MAE | Combined model MAE | Improvement |
|---|---|---|---:|---:|---:|---:|---:|
| T-30 | b_season | gbr | 2199.3 | 2184.6 | 2719.7 | 2191.9 | 19.4% |
| T-14 | b_r3 | histgbr | 2026.6 | 2020.4 | 2399.8 | 2023.5 | 15.7% |
| T-7 | b_season | gbr | 1936.1 | 1982.9 | 2465.8 | 1959.6 | 20.5% |
| T-3 | b_season | histgbr | 1967.8 | 1911.1 | 2465.3 | 1939.3 | 21.3% |
| T-1 | b_season | histgbr | 1929.5 | 1918.3 | 2463.5 | 1923.9 | 21.9% |

## Holdout detail

### T-30
- 2024/2025: baseline MAE **2670.0** → model MAE **2199.3**; improvement **17.6%**; n=297.
- 2025/2026: baseline MAE **2768.4** → model MAE **2184.6**; improvement **21.1%**; n=302.

### T-14
- 2024/2025: baseline MAE **2395.7** → model MAE **2026.6**; improvement **15.4%**; n=299.
- 2025/2026: baseline MAE **2403.9** → model MAE **2020.4**; improvement **16.0%**; n=303.

### T-7
- 2024/2025: baseline MAE **2427.7** → model MAE **1936.1**; improvement **20.2%**; n=300.
- 2025/2026: baseline MAE **2503.5** → model MAE **1982.9**; improvement **20.8%**; n=303.

### T-3
- 2024/2025: baseline MAE **2429.3** → model MAE **1967.8**; improvement **19.0%**; n=300.
- 2025/2026: baseline MAE **2501.1** → model MAE **1911.1**; improvement **23.6%**; n=303.

### T-1
- 2024/2025: baseline MAE **2426.2** → model MAE **1929.5**; improvement **20.5%**; n=300.
- 2025/2026: baseline MAE **2500.4** → model MAE **1918.3**; improvement **23.3%**; n=303.

## Feature-family signal (group permutation, 2025/26)

Positive ΔMAE means shuffling the family makes the model worse, so the family contains useful predictive information.

| Horizon | Timing | Opponent demand | Attendance history | Sporting state | Club identity |
|---|---:|---:|---:|---:|---:|
| T-30 | +481 | +307 | +246 | +48 | +125 |
| T-14 | +171 | +237 | +302 | +198 | +49 |
| T-7 | +372 | +307 | +183 | +172 | +92 |
| T-3 | +492 | +343 | +317 | +201 | +50 |
| T-1 | +457 | +302 | +267 | +191 | +61 |

## Interpretation

- The uplift is replicated on two consecutive untouched seasons, not a single holdout.
- T-3 and T-1 are currently the strongest point forecasts at about **1.91k MAE** on 2025/26.
- Timing/seasonality and opponent-demand features are among the strongest information families.
- Attendance history remains important; sporting state adds additional signal, especially close to kickoff.
- Club identity has positive but smaller group importance, which is consistent with learning transferable demand patterns rather than only memorising clubs.

## Next modelling experiments

1. Add historical stadium capacity / occupancy ratio and learn demand in normalized occupancy space as a challenger.
2. Add match-importance features (title/relegation/european qualification pressure) point-in-time, separately from generic table position.
3. Add derby / rivalry and promoted-team / novelty indicators.
4. Add weather only as issuance-time-correct historical forecast data; no realized-weather leakage.
5. Add ticketing trajectory correction on top of this stronger historical global baseline.
6. Add calibrated quantile models for P10/P50/P90 after the point-forecast challenger is frozen.

**No production promotion is made by this benchmark.** The result establishes the new multi-club historical champion candidate and the baseline for subsequent challengers.
