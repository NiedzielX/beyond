# Persistent Club Calibration v1 — Result 2026-10-18

Status: **COMPLETED / FIXED EMPIRICAL-BAYES CROSS-SEASON CALIBRATION NOT PROVEN / NO PRODUCTION CHANGE**

Workstream:

**a2 — Historical / Structural Prior optimization**

## Evidence source

Final-head GitHub Actions run: `39160997315`  
Tested branch head: `8135ba24d241605e1c6139192f0529a2bb7100d5`  
Artifact: `persistent-club-calibration-v1-39160997315`  
Artifact ID: `12148683008`  
Artifact ZIP SHA256: `a90ca19a872e1c2af19aacdcbc57dddbfe9cfca001f324dad98304c1ee833b1b`  
Result JSON SHA256: `47b2371e5999280f0269cca19020c84538de11722e4731d73baf297305cbd13c`

The immediately preceding accepted run `39160907508` on commit `3824d083...` reached the same model decisions. The final-head run above is canonical because it validates the exact branch state being merged. Numerical differences between the two accepted JSONs are floating-point noise at approximately machine precision and do not change any metric interpretation or decision.

CI:

- pinned runtime installation: PASS;
- compile: PASS;
- unit tests: **5/5 PASS**;
- same-season leakage rejection: PASS;
- future-season leakage rejection: PASS;
- frozen historical input hash: PASS;
- exact retained incumbent holdout assertions: PASS;
- exact frozen T-7 historical candidate reproduction: PASS;
- full rolling OOS residual generation: PASS;
- fixed calibration scoring: PASS;
- artifact upload: PASS.

`promotion_allowed = false`

Production remains unchanged.

## Important invalid precursor

The first implementation attempt was correctly rejected by CI before producing accepted evidence because a local T-7 reimplementation did not reproduce the frozen historical candidate:

- actual 2023/24 MAE: `2327.0351`;
- canonical expected: `2317.3395`.

Cause: the local reconstruction passed explicit uniform sample weights, while the canonical Stage-3 fitter did not.

The accepted implementation delegates T-7 fitting to the canonical Stage-3 adapter and also keeps the local reconstruction contract aligned. Exact reproduction assertions remain mandatory.

The failed run is **not evidence**.

## Fixed hypothesis

This experiment was committed before reference scoring and was not tuned from reference behavior.

Residual target:

`(actual_attendance - rolling_base_prediction) / verified_capacity`

Residual archive:

- train 2021/22 -> predict 2022/23;
- train through 2022/23 -> predict 2023/24;
- train through 2023/24 -> predict 2024/25;
- train through 2024/25 -> predict 2025/26.

For target season S, only residuals from seasons strictly `< S` are visible.

No target-season residual is allowed.

Fixed empirical-Bayes policy:

- historical residual input clip: `+/-25% capacity`;
- estimate pooled within-club residual variance;
- estimate between-club mean-residual variance after expected sampling-noise removal;
- reliability per club:

`w = between_variance / (between_variance + within_variance / n)`

- posterior correction:

`w * club_mean_residual_fraction`

- shrinkage prior: zero;
- final correction cap: `+/-5% capacity`;
- club without prior OOS residual state: zero correction.

There is no `k` grid or reference-tuned shrinkage parameter.

## Base model per horizon

- T-30: `structural-prior-runtime-v1-t30-extra-full`;
- T-14: `structural-prior-runtime-v1-t14-hist-base`;
- T-7: frozen historical candidate `hist31-leaf20-l2-1`;
- T-3: `structural-prior-runtime-v1-t3-hist-full`;
- T-1: `structural-prior-runtime-v1-t1-hist-full`.

T-7 is therefore evaluated on top of the strongest frozen historical T-7 candidate, not the old production T-7 incumbent.

## Result summary

Development is 2023/24. References are the already-exposed 2024/25 and 2025/26 seasons.

| Horizon | 2023/24 development MAE improvement | Mean reference MAE improvement | Both references improve? | Decision |
|---|---:|---:|---|---|
| T-30 | **-40.61** | -12.57 | no | reject on development |
| T-14 | **0.00** | +4.90 | no | reject on development |
| T-7 | **-66.16** | -13.06 | no | reject on development |
| T-3 | **-80.59** | +7.71 | yes | reject on development; references cannot rescue |
| T-1 | **-62.97** | -5.32 | no | reject on development |

No horizon passes the development gate.

Canonical signal for every horizon:

`REJECTED_ON_DEVELOPMENT_REFERENCES_CANNOT_RESCUE`

## Reference detail

### T-30

2024/25:

- base MAE: `1889.37`;
- calibrated MAE: `1900.35`;
- improvement: **-10.99**;
- median AE delta: `-28.38`;
- p90 AE delta: `+396.54`;
- worst event degradation: `+826.45`.

2025/26:

- base MAE: `1846.28`;
- calibrated MAE: `1860.43`;
- improvement: **-14.15**;
- median AE delta: `+39.59`;
- p90 AE delta: `+124.46`;
- worst event degradation: `+804.30`.

Mean reference improvement:

**-12.57 MAE**.

### T-14

2024/25:

- base MAE: `1748.50`;
- calibrated MAE: `1750.28`;
- improvement: **-1.78**.

2025/26:

- base MAE: `1870.39`;
- calibrated MAE: `1858.81`;
- improvement: **+11.58**.

Mean reference improvement:

**+4.90 MAE**, but development is exactly neutral and references are mixed.

This cannot justify adoption.

### T-7

2024/25:

- frozen base MAE: `1650.97`;
- calibrated MAE: `1654.03`;
- improvement: **-3.06**.

2025/26:

- frozen base MAE: `1773.80`;
- calibrated MAE: `1796.86`;
- improvement: **-23.07**.

Mean reference improvement:

**-13.06 MAE**.

The persistent club correction degrades the already-improved T-7 historical candidate.

### T-3

2024/25:

- base MAE: `1661.72`;
- calibrated MAE: `1646.91`;
- improvement: **+14.81**;
- median AE improves by `47.23`;
- p90 AE worsens by `102.93`;
- worst event degradation: `+804.30`.

2025/26:

- base MAE: `1775.07`;
- calibrated MAE: `1774.46`;
- improvement: **+0.61**;
- median AE improves by `27.65`;
- p90 AE worsens by `37.05`;
- worst event degradation: `+804.30`.

Mean reference improvement:

**+7.71 MAE**.

However, 2023/24 development worsens by **80.59 MAE**.

Decision remains reject. Selecting T-3 because the exposed references happen to be positive would be direct holdout rescue / retuning.

### T-1

2024/25:

- base MAE: `1651.73`;
- calibrated MAE: `1641.02`;
- improvement: **+10.71**.

2025/26:

- base MAE: `1742.84`;
- calibrated MAE: `1764.19`;
- improvement: **-21.35**.

Mean reference improvement:

**-5.32 MAE**.

## Interpretation

The fixed empirical-Bayes formulation does **not** support a stable persistent cross-season club-specific residual correction.

Key evidence:

1. No horizon improves the 2023/24 development gate.
2. Four horizons are materially worse on development; T-14 is exactly neutral.
3. T-30 and T-7 also degrade reference mean MAE.
4. T-1 is mixed and negative on reference mean.
5. T-3 happens to improve both exposed references, but only after a large development degradation; governance correctly forbids reference rescue.
6. The frozen T-7 candidate is better without this club calibration.

This is consistent with the separate conservative fixed median/shrinkage club-residual experiment: persistent previous-season club bias is not currently a reliable source of additional forecast accuracy.

## Decision

> **Reject Persistent Club Calibration v1. Do not add a persistent cross-season club-residual correction to Pre-Live v2. Do not tune empirical-Bayes shrinkage/caps against the exposed references.**

This result closes this fixed empirical-Bayes challenger, not the abstract possibility that genuinely new data could reveal a future persistent club effect.

For the current historical dataset, however, a2 has now tested:

- feature contribution / ablation;
- explicit season recency;
- multiple internal estimator families;
- external CatBoost / LightGBM / XGBoost for the strongest horizon;
- T-7 regularization and temporal robustness;
- unresolved-horizon multi-fold selection;
- fixed persistent club calibration under two materially different shrinkage formulations.

The remaining accuracy work should now advance to **b2 — current-season regime**, where same-season completed-match residuals are intentionally allowed under PIT rules.

Production remains unchanged:

`live_adjustment = 0`
