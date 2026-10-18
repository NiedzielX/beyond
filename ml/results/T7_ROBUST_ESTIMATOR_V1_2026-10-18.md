# T-7 Robust Estimator v1 — Result 2026-10-18

Status: **COMPLETED / BETTER MAE CANDIDATE FOUND / TAIL NOT FULLY SOLVED / NO PRODUCTION CHANGE**

Workstream:

**a2 — Historical / Structural Prior optimization — T-7 robust estimator stage 3**

## Evidence source

GitHub Actions run: `39157926927`  
Tested branch head: `d42a4bfdc1aeab8ce84503c03309f2c4036691cc`  
Artifact: `t7-robust-estimator-v1-39157926927`  
Artifact ID: `12146809468`  
Artifact ZIP SHA256: `a048828adb79ce5ebf3b6611902f283b58eaf846899598bb132564205340330c`  
Result JSON SHA256: `83da3d85daa7c7bc844b8cb6b63cdf47070068cdabb774d0f4c01e5a3e0258fe`

CI:

- compile: PASS;
- unit tests: **6/6 PASS**;
- input hash assertion: PASS;
- incumbent benchmark assertions: PASS;
- full scoring: PASS;
- artifact upload: PASS.

Dependencies:

- stage-1 JSON SHA256: `55ea6ee19309771b54e0b0336ecaa2871de19d95d2bf4360400ff76e4c2ddc79`;
- stage-2 JSON SHA256: `170cf7bc10437ca4f0b5bb724e7db7ffab0941600932b7c53544c150007b7703`.

## Frozen protocol

Only estimator shape / regularization changes.

Frozen:

- horizon: T-7;
- baseline: `baseline_season`;
- feature mode: current T-7 `base` contract;
- same preprocessing;
- capacity-normalized residual target;
- uniform season weights;
- seed 42;
- development train: 2021/22 + 2022/23;
- selection: 2023/24 by MAE only;
- reference 1: 2024/25, train through 2023/24;
- reference 2: 2025/26, train through 2024/25;
- exact tie -> earlier predeclared candidate order;
- references cannot choose regularization.

Evidence class:

`EXPOSED_HISTORICAL_REFERENCE_SEASONS`

`promotion_allowed = false`

## Development ranking

| Rank | Candidate | MAE | Improvement vs incumbent | Median AE | p90 AE | Bias | Worst degradation |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | **`hist31-leaf20-l2-1`** | **2,317.34** | **+159.48** | **1,103.63** | 5,448.81 | -31.75 | 4,335.66 |
| 2 | `hist15-leaf20-l2-1` | 2,326.00 | +150.82 | 1,199.59 | 5,580.87 | -99.77 | 3,980.11 |
| 3 | `hist31-leaf20-l2-5` | 2,333.89 | +142.93 | 1,145.36 | 5,635.81 | -42.96 | 4,497.05 |
| 4 | `hist15-leaf10-l2-1` | 2,352.73 | +124.09 | 1,233.11 | 5,703.58 | -100.49 | 5,672.76 |
| 5 | `hist15-leaf20-l2-5` | 2,360.03 | +116.78 | 1,107.60 | **5,384.43** | +25.73 | 4,698.18 |
| 6 | stage-1 `hist31-leaf10-l2-1` | 2,366.98 | +109.83 | 1,198.33 | **5,352.10** | -124.82 | 4,899.31 |
| 7 | `hist31-leaf20-l2-10` | 2,367.01 | +109.80 | 1,177.59 | 5,716.18 | -0.65 | 5,418.83 |
| 8 | `hist31-leaf30-l2-5` | 2,403.55 | +73.26 | 1,143.88 | 5,445.86 | +10.66 | 5,545.16 |
| 9 | `gbr-absolute-depth2-leaf8` | 2,497.84 | -21.02 | 1,370.20 | 4,966.72 | -459.51 | 2,178.74 |
| 10 | `gbr-absolute-depth1-leaf12` | 2,521.05 | -44.23 | 1,365.86 | 5,222.89 | -511.42 | 4,458.27 |

Development selects:

`hist31-leaf20-l2-1`

Exact configuration:

- HistGradientBoostingRegressor;
- loss: `absolute_error`;
- learning rate: `0.04`;
- iterations: `300`;
- max leaf nodes: `31`;
- **min samples leaf: `20`**;
- L2: `1.0`;
- seed: `42`.

Compared with the stage-1 Hist31 lead, the only material change is stronger leaf-size regularization:

`min_samples_leaf: 10 -> 20`

Development MAE improves further:

- stage-1 Hist31 in this run: **2,366.98**;
- selected leaf20: **2,317.34**;
- additional development improvement: **49.64 MAE**.

## 2024/25 reference

- incumbent MAE: **1,777.69**;
- selected MAE: **1,650.97**;
- improvement: **+126.73 MAE**;
- median AE: **926.00**;
- p90 AE: **4,396.22**;
- bias: **+13.05**.

This is better MAE than stage-1 Hist31, which improved 2024/25 by +105.55.

Worst degradation:

`Śląsk Wrocław – Legia`, 2024-08-25

- actual: 36,208;
- incumbent prediction: 28,354.44;
- selected prediction: 24,260.28;
- incumbent AE: 7,853.56;
- selected AE: 11,947.72;
- degradation: **+4,094.16**.

Versus stage-1 Hist31 worst degradation (`+3,685.74`):

- tail change: **-408.42 worse**;
- tail reduction rate: **-11.08%**.

## 2025/26 reference

- incumbent MAE: **1,802.28**;
- selected MAE: **1,773.80**;
- improvement: **+28.48 MAE**;
- median AE: **1,051.76**;
- p90 AE: **3,753.08**;
- bias: **-5.43**.

Worst degradation:

`Lechia Gdańsk – Legia`, 2026-05-17

- actual: 35,000;
- incumbent prediction: 28,207.52;
- selected prediction: 24,506.96;
- incumbent AE: 6,792.48;
- selected AE: 10,493.04;
- degradation: **+3,700.56**.

Versus stage-1 Hist31 worst degradation (`+4,233.11`):

- tail reduction: **+532.55**;
- tail reduction rate: **12.58%**.

## Aggregate result

- mean reference incumbent MAE: **1,789.98**;
- selected mean MAE: **1,712.38**;
- mean improvement: **+77.60 MAE**;
- selected improves both reference seasons: **true**;
- selected reduces stage-1 Hist31 worst tail on both seasons: **false**.

Automated signal:

`REGULARIZED_WINNER_POSITIVE_MEAN_TAIL_NOT_SOLVED`

This is currently the **lowest mean reference T-7 MAE found in the a2 experiments**.

## Decision

1. **Do not change production T-7 champion yet.**
2. `hist31-leaf20-l2-1` becomes the strongest current T-7 MAE challenger.
3. Stronger leaf-size regularization improved average MAE beyond stage-1 Hist31.
4. Tail behavior is mixed: improved in 2025/26, worse in 2024/25.
5. Do not post-hoc choose `hist15-leaf20-l2-1` or another candidate from reference behavior; only the development winner was validly scored on references.
6. Do not create a reference-derived tail threshold and call it unseen.

## Next a2 step

The next useful evidence should broaden the estimator family rather than keep micro-tuning this same exposed HGB grid.

Priority:

- predeclared external tabular boosting challengers (CatBoost / LightGBM / XGBoost where runtime pinning is clean), or a similarly materially different family;
- same T-7 baseline and feature contract first, so the change remains attributable to estimator family;
- development-only selection;
- exact incumbent assertions;
- full MAE/tail scorecard;
- reference scoring only after one candidate is frozen.

A fixed-config broader temporal robustness audit should follow any serious champion candidate before explicit T-7 freeze/promotion.
