# Pre-Live v3 — Historical Anchor + Current-Season Regime Revalidation v1

Last updated: **2026-10-21**

Status: **ACTIVE TRACK-B R&D / NO FREEZE / NO PRODUCTION CHANGE**

Parent evidence:

- `ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`;
- `ml/results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md`;
- `ml/results/CURRENT_SEASON_REGIME_FIXED_TEMPORAL_AUDIT_V1_2026-10-18.md`;
- `ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md`.

## Objective

Build the first versioned Pre-Live v3 challenger around the robust historical anchors and answer:

> **Once the historical anchor changes, does the current-season residual-regime layer still add stable incremental value, and does the resulting v3 package beat Frozen Pre-Live v2?**

This experiment does not mutate v2.

## Candidate historical anchors

| Horizon | v3 historical anchor |
|---|---|
| T-30 | robust `0.75 current a2 + 0.25 XGBoost depth3` ensemble |
| T-14 | current a2 Structural Prior |
| T-7 | robust `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15` ensemble |
| T-3 | current a2 Structural Prior |
| T-1 | robust `0.25 HGB hist31 + 0.50 CatBoost depth4 + 0.25 LightGBM leaves15` ensemble |

The T-30/T-7/T-1 weights are fixed from the completed robustness cycle. They are not retuned here.

## Why b2 must be revalidated

The frozen b2 layer is based on same-season residuals:

`actual attendance - historical anchor forecast`

Changing the historical anchor changes those residuals.

Therefore old b2 cannot be silently copied into v3.

## Frozen-v2 comparator

Every fold must also reproduce the exact Frozen Pre-Live v2 package:

- old historical base;
- old frozen b2 policy;
- no historical c2 extension.

The canonical v2 MAEs are hard reproduction gates at tolerance `1e-9`.

## Selection boundary

Development only:

1. train 2021/22 -> test 2022/23;
2. train 2021/22+2022/23 -> test 2023/24.

Exposed references, never used for selection:

3. train through 2023/24 -> test 2024/25;
4. train through 2024/25 -> test 2025/26.

No event-5, delayed-label d2, or true prospective event enters this experiment.

## PIT contract

A same-season source match may enter regime state only when:

`source kickoff + 3h < target as_of_at`

Snapshot events are processed before completion events at equal timestamps.

No future or uncompleted target-season outcome may enter state.

## Stage A — signal/shrinkage revalidation

Reuse the same bounded b2 candidate space:

Signals:

- mean residual fraction;
- median residual fraction;
- EWMA-50 residual fraction;
- last-3 mean residual fraction;
- mean demand ratio.

Shrinkage:

- k=2;
- k=4;
- k=6.

Common contract:

- residual fraction clip +/-25pp;
- demand-ratio clip +/-50%;
- correction cap +/-5pp capacity;
- EWMA alpha 0.50.

Signal selection is development-only using the canonical b2 rule:

1. candidate must improve both development folds;
2. mean relative MAE improvement >=0.5%;
3. retain candidates within 90% of best mean gain;
4. among near-best, minimize worst-event degradation, then p90 degradation, then prefer better event improvement rate.

If no signal passes, select `NO_ADJUSTMENT`.

## Stage B — maturity revalidation

For the selected Stage-A signal only, compare activation after:

- min1 prior completed same-season home match;
- min2;
- min3.

Development-only maturity selection:

1. candidate must improve both development folds;
2. mean relative MAE improvement >=0.5%;
3. retain candidates within 95% of best mean gain;
4. among near-best, minimize worst-event degradation, then p90 degradation, then prefer higher maturity.

If no threshold passes, select `NO_ADJUSTMENT`.

## Fixed old-b2 comparator on the new anchor

Separately score the old frozen b2 formulation against the v3 historical anchor:

- T-30 `NO_ADJUSTMENT`;
- T-14 `NO_ADJUSTMENT`;
- T-7 `ewma50-resid-k6-cap05-min3`;
- T-3 `ewma50-resid-k2-cap05-min3`;
- T-1 `ewma50-resid-k6-cap05-min3`.

This comparator is diagnostic only and is not selected using exposed references.

## Required per-fold layers

1. Frozen Pre-Live v2;
2. v3 historical anchor only;
3. old frozen-b2 formulation applied to the v3 anchor;
4. development-selected v3 regime package.

For each layer persist:

- MAE;
- median AE;
- p90 AE;
- bias;
- event improvement rate;
- worst-event degradation versus the relevant incumbent;
- b2 correction coverage/magnitude.

## Reference decision

The development-selected v3 package is opened once on 2024/25 and 2025/26.

Per horizon:

- if final v3 package beats Frozen Pre-Live v2 on both exposed references -> `ADVANCE_V3_HORIZON_TO_FIXED_TEMPORAL_PACKAGE_AUDIT`;
- otherwise -> `RETAIN_FROZEN_V2_HORIZON`.

A positive reference decision is not a freeze. It only advances the exact package to a separate fixed-temporal package audit.

## Production boundary

Always:

- Frozen Pre-Live v2 unchanged;
- frozen d2 Ridge/P2 unchanged;
- historical c2 remains `NO_CONTEXT_ALL_HORIZONS`;
- no production write;
- `live_adjustment = 0`.

## Interpretation

> **Pre-Live v3 is a new challenger package, not an edit to v2. The historical anchor changes first; b2 is then re-derived against that anchor under the original PIT-safe selection discipline.**
