# T-7 External Model Family v1 — Result 2026-10-18

Status: **COMPLETED / INTERNAL HGB REMAINS DEVELOPMENT WINNER / NO PRODUCTION CHANGE**

Workstream:

**a2 — Historical / Structural Prior optimization — T-7 external model family stage 4**

## Evidence source

GitHub Actions run: `39158519963`  
Tested branch head: `8cc3b84f0bb85663f2b95f8d182ce3b6d5d70e39`  
Artifact: `t7-external-model-family-v1-39158519963`  
Artifact ID: `12147987319`  
Artifact ZIP SHA256: `063924b69efbde10df23efcd4583ebcfcbfad976335d65b4a02f67764bfa904f`  
Result JSON SHA256: `5c874bce3c6a1fb6466046d0bbedab3fcf66b1b633972f650f4a8c278926d48d`

CI:

- pinned external dependencies installed: PASS;
- dependency version print: PASS;
- compile: PASS;
- unit tests: **6/6 PASS**;
- historical input hash assertion: PASS;
- incumbent benchmark assertions: PASS;
- full scoring: PASS;
- evidence artifact upload: PASS.

## Runtime

Pinned runtime:

- numpy `2.3.5`;
- pandas `2.2.3`;
- scikit-learn `1.8.0`;
- joblib `1.5.3`;
- CatBoost `1.2.10`;
- LightGBM `4.7.0`;
- XGBoost `3.4.1`.

## Frozen protocol

Only estimator family changes.

Fixed:

- horizon T-7;
- baseline `baseline_season`;
- T-7 `base` feature contract;
- incumbent one-hot categorical preprocessing;
- median numeric imputation + missing indicators;
- capacity-normalized residual target;
- uniform season weights;
- seed 42;
- train/dev/reference split;
- exact incumbent benchmark assertions.

Native categorical handling was intentionally excluded so estimator family was the only material changed dimension.

Development:

- train: 2021/22 + 2022/23;
- select: 2023/24 by MAE only.

After selection only production incumbent + selected candidate were scored on:

- 2024/25, rolling training through 2023/24;
- 2025/26, rolling training through 2024/25.

References could not choose model family/configuration.

Evidence class:

`EXPOSED_HISTORICAL_REFERENCE_SEASONS`

`promotion_allowed = false`

## Candidate set

Seven predeclared candidates:

1. internal Stage-3 `hist31-leaf20-l2-1`;
2. CatBoost MAE depth 4;
3. CatBoost MAE depth 6;
4. LightGBM L1 15 leaves;
5. LightGBM L1 31 leaves;
6. XGBoost absolute-error depth 2;
7. XGBoost absolute-error depth 3.

No open-ended hyperparameter search was used.

## Development ranking

| Rank | Candidate | Family | MAE | Improvement vs incumbent | Median AE | p90 AE | Bias | Worst degradation |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | **`hist31-leaf20-l2-1`** | HGB | **2,317.34** | **+159.48** | **1,103.63** | 5,448.81 | -31.75 | 4,335.66 |
| 2 | `lightgbm-l1-leaves15-l2-5` | LightGBM | 2,323.57 | +153.24 | 1,148.27 | 5,703.79 | -128.02 | **3,962.88** |
| 3 | `lightgbm-l1-leaves31-l2-5` | LightGBM | 2,369.53 | +107.29 | 1,250.21 | 5,602.27 | -62.39 | 4,234.54 |
| 4 | `catboost-mae-depth4-l2-5` | CatBoost | 2,387.27 | +89.54 | 1,247.75 | **5,294.56** | -458.10 | 5,896.70 |
| 5 | `catboost-mae-depth6-l2-5` | CatBoost | 2,417.66 | +59.16 | 1,278.03 | 5,560.24 | -326.10 | 3,667.86 |
| 6 | `xgboost-l1-depth3-l2-5` | XGBoost | 2,445.52 | +31.29 | 1,231.64 | 5,633.36 | -488.31 | 3,704.80 |
| 7 | `xgboost-l1-depth2-l2-5` | XGBoost | 2,446.41 | +30.40 | 1,275.82 | 5,363.69 | -519.53 | **2,039.73** |

Development winner:

`hist31-leaf20-l2-1`

The closest external model was LightGBM 15 leaves, only **6.23 MAE** worse on development than HGB, and with a smaller development worst degradation. However, development selection is MAE-first by the predeclared protocol. Reference seasons are not allowed to rescue the runner-up.

## Reference result of frozen selected model

Because the internal Stage-3 HGB remained the development winner, Stage 4 reference scoring reproduces that same configuration.

### 2024/25

- incumbent MAE: **1,777.69**;
- selected MAE: **1,650.97**;
- improvement: **+126.73**;
- median AE: **926.00**;
- p90 AE: **4,396.22**;
- bias: **+13.05**;
- worst degradation: **+4,094.16** on `Śląsk Wrocław – Legia`.

### 2025/26

- incumbent MAE: **1,802.28**;
- selected MAE: **1,773.80**;
- improvement: **+28.48**;
- median AE: **1,051.76**;
- p90 AE: **3,753.08**;
- bias: **-5.43**;
- worst degradation: **+3,700.56** on `Lechia Gdańsk – Legia`.

Tiny sub-seat differences versus the persisted Stage-3 numeric values are numerical/runtime-level reproduction noise only:

- mean selected Stage-4 ref MAE: `1712.3810537`;
- frozen Stage-3 mean ref MAE: `1712.3810375`;
- delta: **+0.000016 MAE**.

This is operationally the same model/result.

## Aggregate

- production incumbent mean reference MAE: **1,789.98**;
- selected HGB mean reference MAE: **1,712.38**;
- improvement: **+77.60 MAE**;
- improves both references: true;
- selected external family: false;
- signal: `INTERNAL_STAGE3_HGB_REMAINS_DEVELOPMENT_WINNER`.

## Decision

1. **Do not change production T-7 champion yet.**
2. `hist31-leaf20-l2-1` remains the strongest current T-7 MAE challenger.
3. CatBoost, LightGBM and XGBoost as tested here do not beat the HGB development winner.
4. Do not score/select the LightGBM runner-up on references post hoc; that would violate the frozen selection protocol.
5. Stop broadening estimator families for this stage unless a materially new hypothesis is introduced.
6. Advance the strongest fixed T-7 challenger to the required broader chronological/temporal robustness audit before any explicit freeze/promotion decision.

## Next a2 step

**Stage 5 — fixed-config broader temporal robustness.**

Freeze `hist31-leaf20-l2-1` exactly and test it without per-fold reselection across additional valid chronological historical folds/seasons.

The audit must:

- keep candidate config fixed;
- avoid fold-specific hyperparameter selection;
- label folds that contributed to earlier development/reference work;
- compare to the correct rolling incumbent;
- report MAE, bias, median, p90, worst-event degradation and event improvement rate;
- remain retrospective robustness evidence, not prospective proof.
