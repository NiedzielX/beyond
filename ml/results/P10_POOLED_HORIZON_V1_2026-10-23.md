# P10 Pooled Horizon Global Model v1 — Real Historical Result

Date: **2026-10-23**

Evidence class: `historical_exposed_research`

Production change: **none** (`live_adjustment = 0`)

## Question

Does one fixed pooled cross-horizon residual model beat the **same fixed estimator** trained separately per horizon?

## Data / lineage

- canonical raw history SHA256: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`;
- reconstructed Structural Prior PIT rows: `7,650`;
- training-eligible PIT rows: `7,198`;
- matches in raw history: `1,530`;
- evaluated independent matches: `900` across 2023/24–2025/26;
- exact fold manifest SHA256: `5ae7603c0070a40d7c4baa3d984ecff5f6b500aebd0c547ba0b06985b0122a81`;
- workflow run: `40024979412`;
- evidence artifact ID: `12531938228`;
- artifact ZIP SHA256: `56f35c668a4bf38a514d724b6fd01ffd475e28fee1de15d8b762829dad0104d1`.

All five PIT rows for one match remain on the same side of every fold. Each match has equal total training weight in the pooled candidate.

## Controlled result

Control:

`local-horizon-hgb-absolute-error-v1`

Challenger:

`pooled-hgb-absolute-error-v1`

Headline match-balanced MAE:

- local: **2120.93**;
- pooled: **2057.46**;
- improvement: **63.47 seats / 2.99%**;
- `challenger - incumbent ΔMAE = -63.47`.

Paired match-block bootstrap (5,000 draws, seed 42, stratified by fold):

- 95% CI: **[-106.29, -23.20] seats**;
- `P(ΔMAE < 0) = 0.9994`;
- event improvement rate: **54.78%**.

Fold stability:

- 2023/24: `-50.45` seats;
- 2024/25: `-45.14` seats;
- 2025/26: `-94.39` seats;
- forward/expanding folds improved: **3/3**.

## Per-horizon MAE

| Horizon | Local | Pooled | Improvement |
|---|---:|---:|---:|
| T-30 | 2277.57 | **2183.47** | **94.09** |
| T-14 | 2122.55 | **2048.86** | **73.69** |
| T-7 | 2096.76 | **2031.36** | **65.40** |
| T-3 | 2048.97 | **2018.30** | **30.66** |
| T-1 | 2075.70 | **2020.61** | **55.08** |

The pooled challenger improves MAE in all five horizon views in this controlled same-estimator comparison.

## Guardrail interpretation

P90 absolute error also decreased in every horizon. Bias generally moved closer to zero except T-1, where negative bias increased modestly.

Median AE did **not** improve uniformly: several horizons have a slightly worse median while MAE/P90 improve. This is a useful reminder that the pooling benefit is not simply a uniform shift of every event error.

## Governance v2 decision

`POINT_GAIN_UNCERTAINTY_LIMITED`

Passed:

- positive MAE point gain;
- event/fold stability;
- evidence-integrity gate;
- precision gate (95% interval entirely below zero).

Blocked from `ROBUST_RESEARCH_ADVANCE` because:

`business_meaningful_mae_threshold_not_defined`

This is intentional. A statistically precise `63.47`-seat improvement is not automatically a practically meaningful business improvement.

## Critical limitation

This experiment proves that **cross-horizon pooling contains useful information relative to the same local estimator**.

It does **not** yet prove that the pooled candidate beats the current Global Model v2.1 champion, whose horizon-specific family selection includes XGBoost at T-14 and existing HGB models under the canonical benchmark protocol.

Therefore P10 v1 is a mechanism result, not an incumbent replacement result.

## Next experiment

**P10b — pooled candidate vs Global Model v2.1 champion** on the exposed 2024/25 and 2025/26 seasons under the canonical v2.1 selection/training protocol.

No production or frozen-package change follows from P10 v1.
