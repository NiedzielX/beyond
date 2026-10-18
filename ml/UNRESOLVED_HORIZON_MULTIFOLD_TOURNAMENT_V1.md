# Beyond Ticketing — Unresolved Horizon Multi-Fold Tournament v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / a2 / NO PRODUCTION CHANGE**

Parent direction:

`ml/CURRENT_MODEL.md`

## Purpose

T-7 now has a frozen historical Pre-Live v2 candidate after fixed-config temporal robustness.

The unresolved horizons are:

- T-30;
- T-14;
- T-3;
- T-1.

Stage 1 used a single 2023/24 development season for candidate selection. That is no longer strong enough for unresolved-horizon advancement.

This experiment asks:

> **Does any existing one-change challenger or the T-7 regularized HGB lesson improve an unresolved horizon consistently across multiple earlier rolling development folds before reference holdouts are inspected?**

## Development folds

### Fold A

Train:

- 2021/22.

Validate:

- 2022/23.

### Fold B

Train:

- 2021/22;
- 2022/23.

Validate:

- 2023/24.

Reference seasons are not used for candidate selection.

## Reference scoring

Only after candidate selection is frozen:

1. 2024/25, train through 2023/24;
2. 2025/26, train through 2024/25.

Evidence class:

`EXPOSED_HISTORICAL_REFERENCE_SEASONS`

Therefore:

`promotion_allowed = false`

and production is unchanged.

## Candidate families

The tournament includes the complete Stage-1 one-change candidate set per horizon:

- exact incumbent;
- feature-group ablations;
- explicit recency policies;
- RandomForest absolute-error challenger;
- ExtraTrees challenger;
- HistGradientBoosting absolute-error challenger.

It also adds one deliberate transfer hypothesis from the frozen T-7 historical candidate family:

`model-hist-absolute-leaf20`

Configuration:

- HistGradientBoostingRegressor;
- `loss=absolute_error`;
- learning rate `0.04`;
- `max_iter=300`;
- `max_leaf_nodes=31`;
- `min_samples_leaf=20`;
- L2 regularization `1.0`;
- seed `42`;
- same horizon-specific baseline and feature contract as incumbent;
- uniform explicit sample weights.

This is not a T-7 config copy promoted blindly. It is a challenger tested independently per unresolved horizon.

## Advancement gate

A non-incumbent candidate is eligible only if:

1. MAE improves versus incumbent in **both** development folds;
2. mean relative MAE improvement across the two folds is at least **1%**.

If no candidate passes:

`selected = incumbent`

## Robust selection among eligible candidates

Among eligible candidates:

1. find the best mean MAE improvement;
2. retain candidates with at least **95%** of the best mean gain;
3. select the candidate with the lowest maximum single-event degradation across development folds;
4. tie-break by lower mean p90 AE delta;
5. then lower absolute-bias delta;
6. then deterministic candidate ID.

This is intentionally stricter than Stage 1.

The objective is not to choose a tiny development winner. The objective is to identify a candidate that is both materially better and stable enough to deserve reference scoring.

## Required reference interpretation

Possible signals:

- `NO_STABLE_DEVELOPMENT_CHALLENGER`;
- `STABLE_DEV_CHALLENGER_POSITIVE_BOTH_REFERENCES`;
- `STABLE_DEV_CHALLENGER_POSITIVE_MEAN_MIXED_REFERENCES`;
- `STABLE_DEV_CHALLENGER_NOT_PROVEN_ON_REFERENCES`.

Even a positive-both-reference result remains historical challenger evidence only.

A later freeze requires explicit fixed-config temporal robustness, as already done for T-7.

## Accuracy scorecard

Every candidate/fold persists:

- MAE;
- median AE;
- bias;
- WAPE;
- p90 AE;
- MAE improvement vs incumbent;
- relative MAE improvement;
- worst single-event degradation and identity;
- best event improvement and identity;
- event improvement rate;
- club breakdown where `n >= 5`;
- training/test row counts;
- exact feature count;
- exact candidate contract.

## CI/CD

Implementation:

`ml/unresolved_horizon_multifold_tournament_v1.py`

Tests:

`ml/test_unresolved_horizon_multifold_tournament_v1.py`

Workflow:

`.github/workflows/unresolved-horizon-multifold-tournament-v1.yml`

Canonical result must later persist:

- run ID;
- artifact ID;
- artifact ZIP SHA256;
- result JSON SHA256;
- exact selected candidate per horizon;
- development fold evidence;
- reference evidence;
- explicit decision;
- canonical state update.

## Non-negotiable boundary

- no future leakage;
- event is independent unit;
- no random snapshot split;
- reference holdouts do not select candidates;
- no post-hoc rescue of a candidate because it looks good on 2024/25 or 2025/26;
- no production change from this experiment.
