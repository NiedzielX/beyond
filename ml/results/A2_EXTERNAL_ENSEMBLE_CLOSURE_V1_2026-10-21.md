# a2 External Model + Heterogeneous Ensemble Closure Audit v1 — Result

Date: **2026-10-21**

Status: **COMPLETED / 3 HORIZONS ADVANCE TO FIXED-TEMPORAL ROBUSTNESS / NO FROZEN OR PRODUCTION CHANGE**

Canonical experiment:

`ml/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1.md`

Workflow run:

`39624170933`

Artifact:

`a2-external-ensemble-closure-v1-39624170933`

Artifact ID:

`12356162577`

Artifact ZIP SHA256:

`c86ad72301e95716a908f4e2b4811e33af37b898b3eed54aed094fc4d91658a4`

Result JSON SHA256:

`dc2b65359e4841ba84d2bb51485c8b9da68816a33f9413f9208943fecaecf88a`

Head SHA used by the run:

`8c668037723be0e55691e0811b28672c060720da`

## Runtime

Pinned runtime passed:

- NumPy `2.3.5`;
- pandas `2.2.3`;
- scikit-learn `1.8.0`;
- joblib `1.5.3`;
- CatBoost `1.2.10`;
- LightGBM `4.7.0`;
- XGBoost `3.4.1`.

Compile checks and unit checks were green.

## Selection protocol

- train: `2021/2022 + 2022/2023`;
- development selection: `2023/2024` only;
- exposed references: `2024/2025` and `2025/2026`;
- no reference-season tuning;
- all five horizons tested independently;
- current a2 historical base retained as benchmark;
- no b2/c2/d2 training;
- no production write;
- Frozen Pre-Live v2 unchanged.

## Overall result

`A2_CLOSURE_AUDIT_FOUND_ROBUSTNESS_FOLLOWUP_CANDIDATES`

Horizons advancing unchanged to a fixed-temporal robustness audit:

- **T-30**;
- **T-7**;
- **T-1**.

Horizons retained on current a2 after mixed exposed-reference evidence:

- T-14;
- T-3.

## T-30

Selected development contract:

`weighted-top-family-grid025`

Members / weights:

- current a2 base `0.75`;
- HGB hist31 `0.00`;
- CatBoost depth6 `0.00`;
- LightGBM leaves15 `0.00`;
- XGBoost depth3 `0.25`.

Development:

- current a2 MAE `2559.74`;
- selected MAE `2526.25`;
- improvement `+33.50`.

Exposed references:

- 2024/25: `1889.37 -> 1834.43`, improvement `+54.93`;
- 2025/26: `1846.28 -> 1816.54`, improvement `+29.74`.

Decision:

`ADVANCE_SELECTED_CONTRACT_TO_FIXED_TEMPORAL_ROBUSTNESS_AUDIT`

## T-14

Selected development contract:

`weighted-top-family-grid025`

Development improvement:

`+16.94`

Exposed references:

- 2024/25 improvement `+58.02`;
- 2025/26 degradation `-2.58`.

Decision:

`RETAIN_CURRENT_A2_MIXED_EXPOSED_REFERENCE_SIGNAL`

No further robustness audit for this challenger.

## T-7

Selected development contract:

`weighted-top-family-grid025`

Members / weights:

- current a2 / HGB hist31 `0.25`;
- CatBoost depth4 `0.25`;
- LightGBM leaves15 `0.50`;
- XGBoost depth3 `0.00`.

Development:

- current a2 MAE `2317.34`;
- selected MAE `2308.44`;
- improvement `+8.90`.

Exposed references:

- 2024/25: `1650.97 -> 1640.70`, improvement `+10.27`;
- 2025/26: `1773.80 -> 1745.94`, improvement `+27.86`.

Decision:

`ADVANCE_SELECTED_CONTRACT_TO_FIXED_TEMPORAL_ROBUSTNESS_AUDIT`

The gain is small, so robustness is mandatory before any candidate freeze.

## T-3

Selected development contract:

`weighted-top-family-grid025`

Development improvement:

`+19.59`

Exposed references:

- 2024/25 degradation `-2.80`;
- 2025/26 improvement `+30.54`.

Decision:

`RETAIN_CURRENT_A2_MIXED_EXPOSED_REFERENCE_SIGNAL`

No further robustness audit for this challenger.

## T-1

Selected development contract:

`weighted-top-family-grid025`

Members / weights:

- current a2 base `0.00`;
- HGB hist31 `0.25`;
- CatBoost depth4 `0.50`;
- LightGBM leaves15 `0.25`;
- XGBoost depth3 `0.00`.

Development:

- current a2 MAE `2347.99`;
- selected MAE `2292.53`;
- improvement `+55.46`.

Exposed references:

- 2024/25: `1651.73 -> 1649.47`, improvement `+2.27`;
- 2025/26: `1742.84 -> 1736.56`, improvement `+6.28`.

Decision:

`ADVANCE_SELECTED_CONTRACT_TO_FIXED_TEMPORAL_ROBUSTNESS_AUDIT`

The reference uplift is extremely small and tail degradations remain material, so this candidate must not be treated as a new champion without a stricter rolling audit.

## Interpretation

The missing external-family/ensemble question was worth testing: heterogeneous ensembles produced positive development signals at every horizon, but only T-30/T-7/T-1 improved both exposed reference seasons.

This does **not** replace current a2 or Frozen Pre-Live v2.

The next step is frozen and predeclared:

> replay the exact selected T-30/T-7/T-1 contracts across the fixed rolling folds, including the earlier 2022/23 fold, and audit MAE stability, tails, club consistency and paired uncertainty.

T-14 and T-3 are closed for this challenger formulation.

## Production boundary

Always:

- `production_change = false`;
- Frozen Pre-Live v2 unchanged;
- b2 unchanged;
- c2 unchanged;
- d2 Ridge/P2 unchanged;
- production `live_adjustment = 0`.
