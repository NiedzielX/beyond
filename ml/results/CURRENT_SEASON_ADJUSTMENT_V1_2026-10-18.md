# Current Season Adjustment v1 — 2026-10-18

Status: **COMPLETED / NOT PROVEN / NO PRODUCTION CHANGE**

## Evidence

GitHub Actions run: `39147976647`  
Main commit: `a0b7462a1b7e57fa5f427571a8b3194bca47aa79`  
Artifact: `current-season-adjustment-v1-39147976647`  
Artifact id: `12143874040`  
Artifact SHA256: `490b037059467552821112d9709d754eddfb9c6ef86054a3918f7c1da8dac934`

The corrected experiment isolates the incumbent Structural Prior before adding challenger-only current-season signals and hard-asserts the frozen historical benchmark for every holdout.

## Protocol

- development train: `2021/2022`, `2022/2023`;
- variant selection: `2023/2024` only;
- frozen reference holdouts: `2024/2025`, `2025/2026`;
- 18 non-zero current-season variants;
- explicit `NO_ADJUSTMENT` candidate;
- minimum 2 current-season home matches;
- signal capped at 20% of capacity before alpha;
- point-in-time safe;
- no automatic promotion;
- production unchanged.

## Result by horizon

| Horizon | Selected on development | Signal | Mean incumbent MAE | Mean adjusted MAE | Delta vs incumbent |
|---|---|---|---:|---:|---:|
| T-30 | `NO_ADJUSTMENT` | `NO_ADJUSTMENT_SELECTED` | 1,867.8 | 1,867.8 | 0.0 |
| T-14 | `NO_ADJUSTMENT` | `NO_ADJUSTMENT_SELECTED` | 1,809.4 | 1,809.4 | 0.0 |
| T-7 | `season_r3-k6-a25` | `NOT_PROVEN` | **1,790.0** | 1,844.3 | **-54.3** |
| T-3 | `NO_ADJUSTMENT` | `NO_ADJUSTMENT_SELECTED` | 1,718.4 | 1,718.4 | 0.0 |
| T-1 | `NO_ADJUSTMENT` | `NO_ADJUSTMENT_SELECTED` | 1,697.3 | 1,697.3 | 0.0 |

No horizon shows positive mean holdout improvement. No horizon shows consistent improvement across both reference seasons.

## T-7 detail

T-7 is the only horizon where a non-zero adjustment wins on the 2023/24 development season:

`season_r3-k6-a25`

Configuration:

- source: current-season rolling last 3 home matches;
- shrink `k = 6`;
- alpha `0.25`.

But it fails both reference holdouts:

| Season | Incumbent MAE | Adjusted MAE | Improvement vs incumbent |
|---|---:|---:|---:|
| 2024/25 | **1,777.7** | 1,829.7 | -52.0 |
| 2025/26 | **1,802.3** | 1,859.0 | -56.7 |

Therefore the development win does not generalise.

## Other horizons

For T-30, T-14, T-3 and T-1, every non-zero current-season correction loses to the incumbent already on the development season, so the governed selector correctly chooses `NO_ADJUSTMENT`.

Best non-zero candidates were small/shrunk corrections, but they still did not beat the incumbent development MAE.

## Decision

1. **Do not promote Current Season Adjustment v1.**
2. **Do not modify Structural Prior.** Current-season information is already present in the incumbent feature set and this extra post-model adjustment adds no validated value.
3. Keep `NO_ADJUSTMENT` as the correct governed outcome when a challenger cannot prove improvement.
4. Keep the implementation and evidence for traceability; do not keep tuning the same idea against the exposed reference seasons.
5. Move active model development to **c) Context meczu — rozbudować**.
6. Frozen C1 v8 and production `live_adjustment = 0` remain unchanged.

This is historical challenger evidence on already exposed reference seasons, not fresh prospective validation.
