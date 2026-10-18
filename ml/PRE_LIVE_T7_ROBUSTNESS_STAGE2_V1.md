# Beyond Ticketing — T-7 Robustness Stage 2 v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / a2 STAGE 2 / NO PRODUCTION CHANGE**

Parent evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

## Why this experiment exists

Stage 1 found a material T-7 lead:

`model-hist_absolute_31`

Mean exposed-reference MAE improvement versus incumbent:

**+68.81 seats**

with positive improvement in both 2024/25 and 2025/26.

However, the pure Hist31 challenger produced severe event-level regressions above **3.6k–4.2k seats**.

Stage 2 asks:

> **Can we preserve most of the T-7 Hist31 MAE gain while constraining harmful deviations from the incumbent?**

## Frozen components

Horizon:

`T-7`

Incumbent:

`structural-prior-runtime-v1-t7-gbr-base`

Hist31 configuration:

- HistGradientBoostingRegressor;
- `loss=absolute_error`;
- learning rate `0.04`;
- `max_iter=300`;
- `max_leaf_nodes=31`;
- `min_samples_leaf=10`;
- `l2_regularization=1.0`;
- seed `42`;
- exact incumbent T-7 baseline / feature mode;
- uniform training-season weights.

Input:

`ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz`

Manifest:

`ml/artifacts/structural_prior_runtime_v1/manifest.json`

Input SHA256 must match the frozen manifest before scoring.

## Candidate formula

First compute:

`delta = alpha * (Hist31 prediction - incumbent prediction)`

If a trust-region cap is active:

`delta = clip(delta, -cap_fraction * capacity, +cap_fraction * capacity)`

Then:

`final = clip(incumbent prediction + delta, 0, capacity)`

## Candidate grid — frozen before evidence

Hist31 weights:

- `0.25`;
- `0.50`;
- `0.75`;
- `1.00`.

Trust-region caps:

- `5%` of verified capacity;
- `10%` of verified capacity;
- uncapped.

Total:

- 12 non-incumbent candidates;
- incumbent fallback;
- 13 total policies.

No candidate is added after seeing development or reference results.

## Development selection protocol

Selection uses only seasons before the exposed reference holdouts.

### Fold 1

Train:

- 2021/22.

Validate:

- 2022/23.

### Fold 2

Train:

- 2021/22;
- 2022/23.

Validate:

- 2023/24.

The known 2023/24 incumbent MAE is asserted exactly.

The 2022/23 fold is additional development evidence and is not used as an independent final holdout claim.

## Robust selection rule

A non-incumbent candidate is eligible only if:

- it improves MAE versus incumbent in **both** development folds;
- its mean development MAE improvement is positive.

Among eligible candidates:

1. find the best mean development MAE gain;
2. retain candidates preserving at least **80%** of that best gain;
3. choose the candidate with the lowest maximum worst-event degradation across development folds;
4. tie-break by lower mean p90 delta versus incumbent;
5. then lower Hist31 `alpha`;
6. then tighter trust-region cap;
7. then deterministic candidate ID.

If no non-incumbent improves both development folds:

`selected = incumbent`

This rule is frozen before 2024/25 or 2025/26 scoring.

## Reference evaluation

Only after the policy is selected, score unchanged on:

1. 2024/25 — train through 2023/24;
2. 2025/26 — train through 2024/25.

Reference outputs include:

- selected robust candidate;
- frozen incumbent;
- pure stage-1 Hist31 comparator.

2024/25 and 2025/26 are already exposed historical reference seasons.

They do **not** choose `alpha`, cap, or any other stage-2 parameter.

Evidence class:

`EXPOSED_HISTORICAL_REFERENCE_SEASONS`

Therefore:

`promotion_allowed = false`

## Required diagnostics

For development and reference folds persist:

- MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- event improvement rate;
- worst-event degradation and exact event identity;
- best event improvement and exact event identity;
- club breakdown where sample permits.

Stage-2 summary must compare:

- selected robust policy MAE gain;
- pure Hist31 MAE gain;
- selected worst-event degradation;
- pure Hist31 worst-event degradation.

## Success interpretation

Strong stage-2 evidence requires both:

- meaningful positive MAE uplift retained versus incumbent;
- material tail reduction versus pure Hist31.

A lower worst-event degradation with near-zero MAE gain is not enough.

A high MAE gain with unchanged severe tail is not enough.

## CI/CD

Implementation:

`ml/pre_live_t7_robustness_stage2_v1.py`

Tests:

`ml/test_pre_live_t7_robustness_stage2_v1.py`

Workflow:

`.github/workflows/pre-live-t7-robustness-stage2-v1.yml`

Canonical result must later include:

- GitHub Actions run ID;
- artifact ID;
- artifact ZIP SHA256;
- JSON SHA256;
- exact selected candidate;
- full development selection evidence;
- reference scorecard;
- explicit decision;
- canonical docs update.

Production remains unchanged throughout this experiment.
