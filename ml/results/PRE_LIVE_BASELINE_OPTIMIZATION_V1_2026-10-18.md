# Pre-Live Baseline Optimization v1 — Result 2026-10-18

Status: **COMPLETED / STAGE-1 HISTORICAL CHALLENGER EVIDENCE / NO PRODUCTION CHANGE**

Workstream:

**a2 — Historical / Structural Prior optimization**

## Evidence source

GitHub Actions run: `39156711796`  
PR head commit used by the run: `0d9967a652ed0fe083faf27c35e71cb918b43060`  
Artifact: `pre-live-baseline-optimization-v1-39156711796`  
Artifact ID: `12146444371`  
Artifact ZIP SHA256: `e40b1c0434f5f87d7e029e46c68301a308b7f3715492db0a9f86f054fd53e1d1`  
Result JSON SHA256: `55ea6ee19309771b54e0b0336ecaa2871de19d95d2bf4360400ff76e4c2ddc79`

CI result:

- compile: PASS;
- unit tests: **5/5 PASS**;
- historical runtime input hash: PASS;
- feature-store quality: PASS;
- incumbent benchmark assertions: PASS;
- full scoring: PASS;
- evidence artifact upload: PASS.

## Input contract

Frozen historical artifact:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Feature contract:

`structural-prior-pit-v1+verified-capacity-v1`

Historical datasets:

- `historical-multiclub-2021-25-v2.1`;
- `historical-multiclub-2025-26-v1`.

Input SHA256:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

Evidence size:

- **1,530 matches**;
- **7,650 PIT horizon rows**;
- **7,198 training-eligible rows**;
- 0 missing capacity rows;
- 0 invalid as-of rows.

Runtime:

- Python 3.12 in GitHub Actions;
- numpy `2.3.5`;
- pandas `2.2.3`;
- scikit-learn `1.8.0`;
- joblib `1.5.3`;
- random seed `42`.

## Protocol

Development fit:

- train: 2021/22 + 2022/23;
- candidate selection: **2023/24 only**;
- selection metric: MAE.

Reference holdouts after development selection:

1. 2024/25, training through 2023/24;
2. 2025/26, training through 2024/25.

Only the exact incumbent plus the **development-selected candidate** is evaluated on holdouts. Reference holdouts are not used as a second candidate tournament.

Evidence class:

`EXPOSED_HISTORICAL_REFERENCE_SEASONS`

Therefore:

`promotion_allowed = false`

Other governance:

- event is the independent unit;
- no random snapshot split;
- no future leakage allowed;
- input artifact hash asserted;
- exact incumbent reference MAE asserted;
- one-change-at-a-time candidates only in stage 1.

## Candidate contract

15 candidates per horizon:

- exact incumbent;
- 9 feature-group ablations;
- 2 non-incumbent recency policies;
- 3 model-family challengers.

Feature groups:

- calendar/timing;
- home demand history;
- current-season demand;
- opponent demand;
- pair history;
- sporting form;
- table context;
- rest/congestion;
- capacity.

The direct horizon baseline feature is protected from ablation.

The harness fails if a numeric feature is not assigned to a declared group or the protected direct baseline.

Recency challengers:

- `linear_075`;
- `exp_050`.

`exp_075` was deliberately excluded because with two development-training seasons it is identical to `linear_075` and therefore cannot be identified honestly during development selection.

Model challengers:

- `rf_absolute_leaf3`;
- `extra_leaf5`;
- `hist_absolute_31`.

## Result summary

| Horizon | Development-selected candidate | Mean incumbent MAE | Mean candidate MAE | Mean MAE improvement | Reference result |
|---|---|---:|---:|---:|---|
| T-30 | `ablate-rest_congestion` | 1,867.82 | 1,864.11 | **+3.71** | positive both, very small |
| T-14 | `recency-linear_075` | 1,809.45 | 1,798.25 | **+11.19** | mixed by season |
| T-7 | `model-hist_absolute_31` | 1,789.98 | **1,721.18** | **+68.81** | positive both, material lead |
| T-3 | `incumbent` | **1,718.39** | **1,718.39** | 0.00 | incumbent wins development |
| T-1 | `recency-linear_075` | **1,697.28** | 1,707.36 | **-10.07** | not proven |

The strongest stage-1 lead is clearly **T-7 `model-hist_absolute_31`**.

---

## T-30 — ablate rest/congestion

Development:

- incumbent MAE: **2,559.74**;
- challenger MAE: **2,550.43**;
- improvement: **+9.31**.

Reference holdouts:

| Season | Incumbent MAE | Challenger MAE | Improvement | Event improvement rate |
|---|---:|---:|---:|---:|
| 2024/25 | 1,889.37 | 1,882.12 | **+7.25** | 46.8% |
| 2025/26 | 1,846.28 | 1,846.11 | **+0.17** | 44.4% |

Mean improvement:

**+3.71 MAE**.

Tail diagnostics:

- 2024/25 worst degradation: **+1,162.29 error** on `Śląsk Wrocław – Lechia Gdańsk`;
- 2025/26 worst degradation: **+837.62 error** on `Wisła Płock – Jagiellonia`.

2025/26 median AE is worse: **1,186.21 -> 1,238.17** and p90 is essentially unchanged/slightly worse.

Decision:

> **Keep as weak ablation evidence only. Do not change T-30 champion.**

The average gain is too small relative to event-level instability to justify a champion change.

---

## T-14 — linear recent-season weighting

Development:

- incumbent MAE: **2,339.95**;
- `linear_075`: **2,331.25**;
- improvement: **+8.70**.

Reference holdouts:

| Season | Incumbent MAE | Challenger MAE | Improvement | Event improvement rate |
|---|---:|---:|---:|---:|
| 2024/25 | 1,748.50 | 1,717.12 | **+31.38** | 46.5% |
| 2025/26 | **1,870.39** | 1,879.39 | **-9.00** | 49.2% |

Mean improvement:

**+11.19 MAE**, but the two seasons disagree.

Tail diagnostics:

- 2024/25 worst degradation: **+1,855.89 error** on `Lechia Gdańsk – Legia`;
- 2025/26 worst degradation: **+1,578.93 error** on `Lech – Motor Lublin`.

Decision:

> **Promising directional evidence for recency, but not consistent enough to replace T-14 incumbent.**

Do not tune the decay against these exposed holdouts.

---

## T-7 — HistGradientBoosting absolute-error challenger

Selected candidate:

`model-hist_absolute_31`

Configuration:

- HistGradientBoostingRegressor;
- `loss=absolute_error`;
- learning rate `0.04`;
- `max_iter=300`;
- `max_leaf_nodes=31`;
- `min_samples_leaf=10`;
- `l2_regularization=1.0`;
- seed `42`;
- same T-7 baseline and feature contract as incumbent;
- uniform season weights.

### Development

| Metric | Incumbent | Hist31 |
|---|---:|---:|
| MAE | 2,476.82 | **2,379.46** |
| Median AE | 1,288.41 | **1,206.21** |
| p90 AE | 5,598.34 | **5,325.76** |
| Bias | -504.93 | **+6.52** |

Development MAE improvement:

**+97.36**.

### 2024/25 reference holdout

| Metric | Incumbent | Hist31 |
|---|---:|---:|
| MAE | 1,777.69 | **1,672.14** |
| Median AE | 1,091.35 | **948.92** |
| p90 AE | 4,767.84 | **4,340.95** |
| Bias | +133.90 | -56.63 |
| Event improvement rate | — | 51.3% |

MAE improvement:

**+105.55**.

Worst event-level degradation:

`Śląsk Wrocław – Raków`, 2024-10-26

- actual: 16,265;
- incumbent prediction: 19,833.43;
- Hist31 prediction: 23,519.18;
- incumbent AE: 3,568.43;
- Hist31 AE: 7,254.18;
- **degradation: +3,685.74**.

### 2025/26 reference holdout

| Metric | Incumbent | Hist31 |
|---|---:|---:|
| MAE | 1,802.28 | **1,770.22** |
| Median AE | 1,153.15 | **1,130.63** |
| p90 AE | 3,965.92 | **3,962.48** |
| Bias | +78.86 | -129.11 |
| Event improvement rate | — | 51.5% |

MAE improvement:

**+32.06**.

Worst event-level degradation:

`Lech – Arka Gdynia`, 2026-05-08

- actual: 41,598;
- incumbent prediction: 36,152.69;
- Hist31 prediction: 31,919.58;
- incumbent AE: 5,445.31;
- Hist31 AE: 9,678.42;
- **degradation: +4,233.11**.

### T-7 interpretation

Three independent historical views point in the same direction:

- development: **+97.36 MAE**;
- 2024/25: **+105.55 MAE**;
- 2025/26: **+32.06 MAE**.

Mean reference improvement:

**+68.81 MAE**.

Median AE improves on both holdouts. p90 improves materially on 2024/25 and is approximately neutral on 2025/26.

However, the challenger creates severe isolated regressions above **3.6k–4.2k seats**.

Decision:

> **T-7 Hist31 is the primary a2 stage-2 candidate, but it is NOT ready to become the champion because tail risk remains too large.**

Next step must test robustness / controlled blending with incumbent using development-only selection, while preserving exact reference evidence separation.

---

## T-3 — incumbent retained

Development selects the exact incumbent.

Reference MAE remains:

- 2024/25: **1,661.72**;
- 2025/26: **1,775.07**.

Decision:

> **No stage-1 evidence justifies changing T-3.**

---

## T-1 — recency challenger not proven

Development:

- incumbent MAE: **2,347.99**;
- `linear_075`: **2,294.72**;
- development improvement: **+53.27**.

Reference holdouts:

| Season | Incumbent MAE | Challenger MAE | Improvement |
|---|---:|---:|---:|
| 2024/25 | **1,651.73** | 1,693.41 | **-41.67** |
| 2025/26 | 1,742.84 | **1,721.30** | **+21.53** |

Mean result:

**-10.07 MAE worse than incumbent**.

Tail diagnostics:

- 2024/25 worst degradation: **+3,080.12** on `Lech – Jagiellonia`;
- 2025/26 worst degradation: **+1,958.51** on `Lech – Legia`.

Decision:

> **Do not replace T-1 incumbent with this recency weighting.**

---

## Overall decision

`promotion_allowed = false`

Production remains unchanged.

Per horizon:

- **T-30:** retain incumbent; ablation effect is too small / unstable;
- **T-14:** retain incumbent; recency signal is mixed and needs stronger evidence, not holdout retuning;
- **T-7:** retain incumbent for now, but advance Hist31 into a dedicated stage-2 robustness/blend experiment;
- **T-3:** retain incumbent;
- **T-1:** retain incumbent; selected recency challenger is not proven.

The current frozen Structural Prior bundle therefore remains production incumbent.

## Next a2 work

Immediate priority:

### T-7 robustness / blend stage 2

Use only predeclared candidate blending and development-only selection to test whether the Hist31 MAE gain can be retained while reducing harmful event-level revisions.

At minimum compare:

- incumbent only;
- fixed incumbent/Hist31 blends;
- full Hist31.

Report:

- MAE;
- median AE;
- p90 AE;
- bias;
- worst-event degradation;
- improvement rate;
- exact worst-event identity;
- result on both exposed reference seasons after development selection.

Do not tune blend weight from reference holdouts.

After the T-7 robustness step, continue a2 with the remaining justified model-family / calibration research rather than declaring a2 complete from this single stage.
