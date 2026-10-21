# a2 External Model + Heterogeneous Ensemble Closure Audit v1

Last updated: **2026-10-21**

Status: **ACTIVE R&D — HISTORICAL CLOSURE AUDIT**

## Why this exists

The earlier a2 investigation tested internal estimator families at all horizons, but the pinned external families:

- CatBoost;
- LightGBM;
- XGBoost;

were evaluated under the canonical contract only at **T-7**.

Therefore a2 was operationally frozen, but one bounded question remained open:

> **Can a materially different external tabular family or a heterogeneous ensemble improve the current a2 historical base at any horizon?**

This audit closes that gap without mutating Frozen Pre-Live v2.

## Governance boundary

This is active model R&D running in parallel with the frozen prospective evidence track.

It does not:

- retrain or modify `pre-live-v2-historical-candidate-2026-10-18-v1`;
- change frozen b2/c2;
- change frozen `ridge-a10`;
- change `P2-observation-maturity`;
- change production;
- consume delayed-label or true prospective d2 events as training data.

Production remains:

`live_adjustment = 0`

## Data and split

Committed historical runtime only:

`ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz`

Canonical historical split:

- train: `2021/2022 + 2022/2023`;
- development selection: `2023/2024`;
- exposed reference 1: `2024/2025`, refit on all earlier seasons;
- exposed reference 2: `2025/2026`, refit on all earlier seasons.

The two reference seasons are **not** used for candidate or ensemble-weight selection.

## Horizons

Audit all five independently:

- T-30;
- T-14;
- T-7;
- T-3;
- T-1.

## Benchmark

The benchmark is the **current frozen a2 historical base**, not production activation.

Current a2 base:

- T-30: current Structural Prior;
- T-14: current Structural Prior;
- T-7: `hist31-leaf20-l2-1`;
- T-3: current Structural Prior;
- T-1: current Structural Prior.

## Candidate families

Single-model candidates:

1. current a2 base;
2. fixed HGB `hist31-leaf20-l2-1` where it is not already the current base;
3. CatBoost MAE depth 4;
4. CatBoost MAE depth 6;
5. LightGBM L1 leaves 15;
6. LightGBM L1 leaves 31;
7. XGBoost L1 depth 2;
8. XGBoost L1 depth 3.

All candidates retain:

- the horizon's existing feature mode;
- the horizon's existing baseline column;
- occupancy-normalized residual target;
- verified capacity;
- deterministic seed `42`;
- the same PIT-safe feature store.

## Heterogeneous ensembles

After scoring single models on development only:

1. select the best variant within each family;
2. create `median-top-family`;
3. create `weighted-top-family-grid025`.

Weighted ensemble contract:

- non-negative weights;
- weights sum to `1.0`;
- grid step `0.25`;
- at least two non-zero members;
- weights selected by **2023/24 development MAE only**;
- frozen unchanged before exposed references are opened.

This prevents an "ensemble" from silently degenerating to a single model.

## Selection

For each horizon:

1. rank all single models + the two ensembles on development MAE;
2. freeze the best development contract;
3. refit that unchanged contract on expanding historical training seasons;
4. score on 2024/25 and 2025/26.

No reference-season tuning is allowed.

## Decision

A development winner advances to a separate fixed-temporal robustness audit only if it improves current a2 MAE on **both** exposed reference seasons.

Possible decisions:

- `NO_CHANGE_CURRENT_A2_WINS_DEVELOPMENT`;
- `RETAIN_CURRENT_A2_MIXED_EXPOSED_REFERENCE_SIGNAL`;
- `RETAIN_CURRENT_A2_CHALLENGER_FAILS_EXPOSED_REFERENCES`;
- `ADVANCE_SELECTED_CONTRACT_TO_FIXED_TEMPORAL_ROBUSTNESS_AUDIT`.

A positive closure-audit result is **not** a new Pre-Live freeze by itself.

## Reproducibility

CI pins:

- Python `3.12`;
- NumPy `2.3.5`;
- pandas `2.2.3`;
- scikit-learn `1.8.0`;
- joblib `1.5.3`;
- CatBoost `1.2.10`;
- LightGBM `4.7.0`;
- XGBoost `3.4.1`.

Machine-readable output must include:

- dependency versions;
- historical-runtime SHA256;
- manifest SHA256;
- all development rankings;
- chosen family variants;
- ensemble member IDs/weights;
- both exposed-reference scorecards;
- per-horizon decision;
- overall signal.

## Interpretation rule

> **A failed challenger closes the challenger, not model R&D. Frozen prospective validation and active R&D continue in parallel.**
