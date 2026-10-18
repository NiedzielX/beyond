# Current-Season Regime Maturity Stage 2 v1 — Result 2026-10-18

Status: **COMPLETED / B2 MATURITY-GATED HISTORICAL CANDIDATES POSITIVE / NO PRODUCTION CHANGE**

Workstream:

**b2 — Current-season residual regime**

## Evidence source

GitHub Actions run: `39162095068`  
Tested head: `5ef324c9096f03a4655fd6c13e8998ae465c412e`  
Artifact: `current-season-regime-maturity-stage2-v1-39162095068`  
Artifact ID: `12149700211`  
Artifact ZIP SHA256: `45687f45dedc7f04c7a5bf58d9b901fea75606575d3a90c26c6c6bdcf118a81a`  
Result JSON SHA256: `e394f806b81537f4d646c85ce32eaee5b11dd041e3d6be6e23de61c565aeefb9`

CI:

- pinned runtime: PASS;
- compile: PASS;
- unit tests: 4/4 PASS;
- canonical b2 Stage-1 source compatibility: PASS;
- Stage-1 min1 exact reproduction gates: PASS;
- full maturity scoring: PASS;
- artifact upload: PASS.

The first Stage-2 attempt failed before scoring because it used the obsolete internal source label `ewma_residual_fraction`; canonical b2 v1 uses `ewma50_residual_fraction`. The accepted runner changes only this enum label and reuses the exact frozen Stage-1 policies. No numerical model parameter or selection rule changed.

`promotion_allowed = false`

Production remains unchanged.

## Fixed input from Stage 1

Signal source and shrinkage are frozen:

- T-7: `ewma50-resid-k6-cap05`;
- T-3: `ewma50-resid-k2-cap05`;
- T-1: `ewma50-resid-k6-cap05`.

T-30 and T-14 do not participate because Stage 1 selected `NO_ADJUSTMENT`.

## Only variable tested

Minimum number of earlier completed same-season home matches before the correction may activate:

- min1 — exact Stage-1 behavior;
- min2;
- min3.

PIT completion rule remains:

`previous kickoff_at + 3h <= current as_of_at`

## Selection protocol

Development folds only:

1. 2022/23;
2. 2023/24.

Eligibility:

- positive MAE improvement in both folds;
- >=0.5% mean relative MAE improvement.

Among eligible candidates:

1. retain candidates with >=95% of the best mean development MAE gain;
2. minimize maximum worst-event degradation;
3. then mean p90 delta;
4. then prefer the more mature/higher activation threshold.

2024/25 and 2025/26 are scored only after threshold selection is frozen.

## Result summary

All three advancing horizons select **min3**.

| Horizon | Frozen Stage-1 signal | Selected maturity | Dev 2022/23 gain | Dev 2023/24 gain | Ref 2024/25 gain | Ref 2025/26 gain | Mean reference gain |
|---|---|---:|---:|---:|---:|---:|---:|
| T-7 | `ewma50-resid-k6-cap05` | **3** | +93.13 | +70.77 | +7.15 | +34.81 | **+20.98** |
| T-3 | `ewma50-resid-k2-cap05` | **3** | +89.40 | +120.83 | +50.34 | +21.18 | **+35.76** |
| T-1 | `ewma50-resid-k6-cap05` | **3** | +119.73 | +86.88 | +24.66 | +46.87 | **+35.77** |

Canonical signal for every horizon:

`MATURITY_GATED_REGIME_POSITIVE_BOTH_REFERENCES`

## T-7

Selected:

`ewma50-resid-k6-cap05-min3`

Development:

- 2022/23: `1984.99 -> 1891.86`, improvement **+93.13**;
- 2023/24: `2317.34 -> 2246.57`, improvement **+70.77**.

Mean development improvement:

**+81.95 MAE**.

References:

2024/25:

- base: `1650.97`;
- selected: `1643.82`;
- improvement: **+7.15**;
- median AE delta: `+38.74`;
- p90 AE delta: **-360.44**;
- worst event degradation: `+2141.85`;
- event improvement rate: 41.3%.

2025/26:

- base: `1773.80`;
- selected: `1738.98`;
- improvement: **+34.81**;
- median AE delta: **-51.76**;
- p90 AE delta: `+14.76`;
- worst event degradation: `+2141.85`;
- event improvement rate: 40.3%.

Mean reference improvement:

**+20.98 MAE**.

Interpretation:

> Maturity gating removes the Stage-1 mixed-reference problem. T-7 now has positive MAE evidence on both reference seasons, but tail risk remains explicit and must be included in the fixed audit.

## T-3

Selected:

`ewma50-resid-k2-cap05-min3`

Development:

- 2022/23: `1916.35 -> 1826.95`, improvement **+89.40**;
- 2023/24: `2311.62 -> 2190.79`, improvement **+120.83**.

Mean development improvement:

**+105.12 MAE**.

References:

2024/25:

- base: `1661.72`;
- selected: `1611.37`;
- improvement: **+50.34**;
- median AE delta: **-131.06**;
- p90 AE delta: **-514.21**;
- worst event degradation: `+2141.85`;
- event improvement rate: 44.3%.

2025/26:

- base: `1775.07`;
- selected: `1753.89`;
- improvement: **+21.18**;
- median AE delta: **-82.53**;
- p90 AE delta: `+44.76`;
- worst event degradation: `+2141.85`;
- event improvement rate: 41.6%.

Mean reference improvement:

**+35.76 MAE**.

Interpretation:

> T-3 is the strongest b2 maturity-gated candidate: all four historical rolling seasons improve and both reference medians improve.

## T-1

Selected:

`ewma50-resid-k6-cap05-min3`

Development:

- 2022/23: `1913.99 -> 1794.26`, improvement **+119.73**;
- 2023/24: `2347.99 -> 2261.11`, improvement **+86.88**.

Mean development improvement:

**+103.31 MAE**.

References:

2024/25:

- base: `1651.73`;
- selected: `1627.07`;
- improvement: **+24.66**;
- median AE delta: **-9.13**;
- p90 AE delta: `+198.63`;
- worst event degradation: `+2141.85`;
- event improvement rate: 41.3%.

2025/26:

- base: `1742.84`;
- selected: `1695.96`;
- improvement: **+46.87**;
- median AE delta: **-116.88**;
- p90 AE delta: **-126.96**;
- worst event degradation: `+2141.85`;
- event improvement rate: 45.2%.

Mean reference improvement:

**+35.77 MAE**.

## Maturity / coverage

At min3 the correction is applied only after at least three earlier completed same-season home matches.

Reference active shares are still substantial:

- T-7: ~77–79%;
- T-3: ~77–81%;
- T-1: ~80%.

Mean absolute corrections remain controlled at roughly 400–510 seats on references, with the fixed safety cap still limiting maximum movement to 5% verified capacity.

## Tail boundary

Maturity gating improves mean MAE but does not remove the maximum possible bounded harm:

`max observed worst-event degradation = +2141.85 seats`

This is the 5% capacity safety cap on the largest affected stadium/event and remains a required risk metric.

Therefore Stage 2 is not treated as production promotion.

## Decision

> **Freeze these three maturity-gated policies as b2 historical candidates and run one final fixed-config temporal robustness audit over all four rolling seasons without further tuning.**

Frozen candidate definitions for the audit:

- T-7: `ewma50-resid-k6-cap05-min3` on top of `hist31-leaf20-l2-1`;
- T-3: `ewma50-resid-k2-cap05-min3` on top of retained T-3 Structural Prior;
- T-1: `ewma50-resid-k6-cap05-min3` on top of retained T-1 Structural Prior.

T-30/T-14 remain `NO_ADJUSTMENT` for b2.

The fixed audit may diagnose stability, tail, club heterogeneity and maturity coverage but may not change source, shrinkage, cap or threshold.

If the fixed audit reproduces the four-fold positive MAE pattern without contract drift, b2 can be considered sufficiently evaluated for current data and development should advance to c2.
