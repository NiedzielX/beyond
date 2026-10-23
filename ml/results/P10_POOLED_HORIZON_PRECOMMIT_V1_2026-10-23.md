# P10 Pooled Horizon Global Model — Precommit v1

Date: **2026-10-23**

Status: **IMPLEMENTED / REAL HISTORICAL RUN PENDING CANONICAL INPUT CONTRACT CHECK**

Production remains:

`live_adjustment = 0`

## Research question

> Does pooling T-30/T-14/T-7/T-3/T-1 PIT rows in one fixed global residual model reduce match-balanced OOS MAE versus the same fixed estimator trained separately per horizon?

This is a controlled test of **cross-horizon pooling**, not a tournament between different estimator families.

## Data basis

Structural Prior historical population:

- 1,530 matches;
- five complete Ekstraklasa seasons;
- five PIT horizons per match;
- 7,650 PIT rows.

Pinned Structural Prior source manifest:

- `historical_multiclub_2021_25_v2_1.csv`: 1,224 matches, SHA256 `ab7e460f09b9d64d2e45403affe6e405ea1e40d79c2ded3321f3101bd9851fa7`;
- `historical_multiclub_2025_26_v1.csv`: 306 matches, SHA256 `42db003225ba0f5abde4a64cf33b7e5cca96a5250ef8b3f0874badd6c82ed550`.

The frozen runtime history is pinned separately:

`ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz`

SHA256:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

A real P10 evaluation must use the canonical Structural Prior PIT feature contract or an explicitly versioned reconstruction. It must not silently substitute a similar dataset.

## Non-negotiable match blocking

Independent unit:

`match_key`

All horizon rows for one match remain on the same side of every fold.

Forbidden:

`train target match T-30 -> evaluate same target match T-7`

## Training weights

Each match contributes equal total training weight.

For a match with five eligible horizon rows, each row has training weight `1/5`.

This prevents pooling from changing the effective sample objective merely because one match contributes multiple PIT rows.

## Fixed candidate family

### Control

`local-horizon-hgb-absolute-error-v1`

One identical fixed estimator trained independently for each horizon.

### Challenger

`pooled-hgb-absolute-error-v1`

One identical fixed estimator trained across all horizons with numeric `horizon_days`.

Both use:

- home/away categorical features;
- canonical PIT-safe numeric structural features;
- median imputation + missing indicators;
- `HistGradientBoostingRegressor`;
- `loss='absolute_error'`;
- learning rate `0.05`;
- max iter `250`;
- max leaf nodes `15`;
- min samples leaf `10`;
- L2 `1.0`;
- random state `42`.

No broad hyperparameter search in P10 v1.

## Validation

Canonical protocol:

- expanding season folds;
- minimum two training seasons;
- complete `match_key` blocking;
- exact fold manifest + SHA;
- historical evidence remains `historical_exposed_research`.

Headline metric:

- match-balanced MAE.

Required diagnostics:

- overall pooled vs local MAE;
- per-horizon MAE;
- fold/season MAE;
- event/match improvement rate;
- forward fold improvement rate;
- median AE / P90 / bias where applicable;
- paired match-block bootstrap, 5,000 draws, seed 42.

## Governance v2

P10 is the first historical experiment interpreted directly by:

`ml/research_advance_governance_v2.py`

Because a business-derived minimum meaningful MAE threshold is not yet approved, **P10 cannot emit `ROBUST_RESEARCH_ADVANCE` yet**.

Best possible positive state before that threshold exists:

`POINT_GAIN_UNCERTAINTY_LIMITED`

This is intentional and prevents a tiny historical point gain from being described as robust progress.

## Canonical implementation

- `ml/p10_pooled_horizon_global_v1.py`;
- `ml/test_p10_pooled_horizon_global_v1.py`;
- `.github/workflows/mae-roadmap-v4-p9-p10-v1.yml`.

## Real-run input gate

CI first inspects the frozen `historical_runtime_v1.csv.gz` schema.

If it contains the full P10 modeling contract, the real benchmark runs directly.

If it does not, CI records:

`BLOCKED_CANONICAL_FEATURE_STORE_NOT_COMMITTED`

and no alternate dataset is substituted. The next engineering step is then to expose/reconstruct the exact pinned Structural Prior feature store with verified input hashes.

## Decision before real run

**RUN THE CONTROLLED POOLED-VS-LOCAL BENCHMARK ON THE CANONICAL FEATURE STORE. DO NOT CLAIM IMPROVEMENT BEFORE THE SCORECARD EXISTS.**
