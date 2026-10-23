# P10b — Pooled Horizon vs Frozen Pre-Live v3 — Result

Date: **2026-10-23**

Status: **COMPLETE / NO_RESEARCH_GAIN / PRODUCTION UNCHANGED**

Workflow run: `40028701211`

Frozen execution commit: `dc266e25c641f9b807dac70740ae30f15ed19e73`

Artifact: `p10b-pooled-vs-prelive-v3-v1-40028701211`

Artifact id: `12532794687`

Artifact digest: `sha256:599e9154d9bb2c2be0415044b3acc74eac6acb957eb7dd98bb238e38abb8eab1`

Production: `live_adjustment = 0`

## Question

Does the fixed P10 v1 pooled cross-horizon architecture beat frozen Pre-Live v3 on the exact common forecastable support under complete match blocking and the exact four forward season folds?

## Result

**No.**

| Metric | Frozen Pre-Live v3 | Pooled challenger |
|---|---:|---:|
| Match-balanced MAE | **1919.92** | **2067.43** |

`challenger - incumbent ΔMAE = +147.51 seats`

Relative degradation: **+7.68%**.

Paired match-block bootstrap, 5,000 draws, seed 42:

- 95% interval for `ΔMAE`: **[+82.97, +210.67]**;
- probability `ΔMAE < 0`: **0.0**;
- independent matches: **1,197**.

Stability:

- match/event improvement rate: **43.69%**;
- fold improvement rate: **0/4**;
- pooled challenger lost on **all five horizons**.

## Per horizon

| Horizon | Pre-Live v3 MAE | Pooled MAE | ΔMAE |
|---|---:|---:|---:|
| T-30 | 2079.31 | 2235.35 | +156.04 |
| T-14 | 1985.40 | 2067.46 | +82.05 |
| T-7 | 1863.03 | 2029.11 | +166.08 |
| T-3 | 1844.70 | 2009.10 | +164.39 |
| T-1 | 1843.31 | 2011.30 | +167.99 |

## Per forward fold

| Test season | Pre-Live v3 MAE | Pooled MAE | ΔMAE |
|---|---:|---:|---:|
| 2022/23 | 1924.60 | 2090.05 | +165.45 |
| 2023/24 | 2306.27 | 2463.39 | +157.12 |
| 2024/25 | 1685.59 | 1887.08 | +201.49 |
| 2025/26 | 1768.66 | 1835.72 | +67.05 |

## Evidence integrity

- canonical history SHA: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`;
- sealed Pre-Live v3 manifest SHA: `b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`;
- all 20 horizon × season Pre-Live v3 MAE cells reproduced within `1e-9` before comparison;
- exact common support rows: **5,972**;
- matches on common support: **1,197**;
- complete `match_key` blocking;
- fold manifest SHA: `716a50af6e09d20a751c0f25cfa56f9761fd4cd7f1a8b22d605d174ab8282c17`.

## Governance v2

Decision:

`NO_RESEARCH_GAIN`

Reasons:

- no positive MAE point gain;
- event/fold stability failed;
- `ΔMAE` interval is entirely on the wrong side of zero;
- business meaningful-MAE threshold remains undefined, although this is not material because the challenger already loses.

## Interpretation

P10 v1 remains a valid finding: pooling improved the same fixed HGB architecture relative to training that architecture separately per horizon.

P10b answers the more important product/model question: **that pooled architecture is still materially weaker than the current frozen Pre-Live v3 structural package.**

Therefore:

1. do not replace Pre-Live v3 with P10/P10b pooling;
2. do not retune P10b after observing this result;
3. close this pooled architecture as a direct replacement candidate;
4. retain the scientific lesson that cross-horizon sharing can help a weaker base learner, but future pooled work would require a materially different mechanism/architecture and a new precommit;
5. prioritize genuinely new information/representation: P9 booking curves and P11 match/commercial context.

No production change is justified.
