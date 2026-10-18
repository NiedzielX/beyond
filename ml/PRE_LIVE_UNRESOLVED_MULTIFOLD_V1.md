# Beyond Ticketing — Pre-Live Unresolved-Horizon Multi-Fold v1

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / a2 / NO PRODUCTION CHANGE**

## Purpose

Re-evaluate the still-unresolved historical Pre-Live horizons with a stronger selection protocol:

- T-30;
- T-14;
- T-3;
- T-1.

T-7 is deliberately excluded because `hist31-leaf20-l2-1` is already frozen as the historical T-7 Pre-Live candidate after Stages 1–5.

The goal is not to add another model zoo. The goal is to determine whether any already-justified Stage-1 hypothesis is stable enough across **two development-era rolling folds** to deserve reference scoring.

## Candidate contract

Reuse the exact Stage-1 candidate families:

- production incumbent;
- one feature-group ablation at a time;
- explicit recency weights;
- the small internal model-family challenger set.

No new external dependency or hyperparameter search is introduced.

Feature-group completeness rules from Stage 1 still apply: an unassigned numeric model feature is an error, not something silently ignored.

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

The 2023/24 incumbent MAE must reproduce the canonical Stage-1 artifact exactly:

- T-30: `2559.7406941266854`;
- T-14: `2339.9504993283904`;
- T-3: `2311.6246893162593`;
- T-1: `2347.9931110468183`.

Tolerance:

`1e-9`

## Important recency identifiability rule

A recency-weighting policy is **not identifiable** when only one training season exists.

With one season, all meaningful season weighting collapses to the same single historical season. Any numerical difference caused by passing explicit `sample_weight` is an implementation artifact, not evidence that recency weighting works.

Therefore:

- recency candidates are marked `RECENCY_NOT_IDENTIFIABLE_WITH_ONE_TRAINING_SEASON` on Fold A;
- a candidate needs **two identifiable development folds** to advance;
- recency challengers therefore cannot be promoted by this tournament from one genuinely informative recency fold alone.

This is intentional. We do not use 2024/25 or 2025/26 to manufacture a second tuning fold because those seasons are already exposed references.

## Advancement rule

A non-incumbent candidate is eligible only if:

1. it is identifiable in at least two development folds;
2. it improves incumbent MAE by more than `1e-9` in **every identifiable development fold**.

Among eligible candidates:

1. select maximum mean development MAE improvement;
2. tie-break with lower maximum worst-event degradation;
3. then earlier predeclared Stage-1 candidate order.

If no candidate qualifies:

`selected = incumbent`

This rule is frozen before reference scoring.

## Reference scoring

Only after one candidate per horizon is frozen from development:

1. score 2024/25 using training through 2023/24;
2. score 2025/26 using training through 2024/25.

Only:

- production incumbent;
- development-selected candidate

are scored on references.

Reference seasons cannot rescue a development-inconsistent challenger.

Evidence class:

`DEVELOPMENT_MULTIFOLD_PLUS_EXPOSED_REFERENCE_SEASONS`

`promotion_allowed = false`

## Mandatory diagnostics

Per development and reference fold persist:

- MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- event improvement rate;
- exact worst-event degradation and event identity;
- club breakdown;
- training rows;
- exact feature count;
- sample weights;
- identifiability state.

## Interpretation

Possible outcomes per horizon:

### No multi-fold development winner

Retain incumbent as the historical candidate. Do not look at exposed references to rescue another candidate.

### Multi-fold winner, but weak/mixed references

Keep as research challenger only. Do not freeze/promote it automatically.

### Multi-fold winner with positive references

Advance that horizon to a fixed-config robustness audit analogous in principle to T-7, with the exact candidate frozen before additional historical analysis.

## CI/CD

Implementation:

`ml/pre_live_unresolved_multifold_v1.py`

Tests:

`ml/test_pre_live_unresolved_multifold_v1.py`

Workflow:

`.github/workflows/pre-live-unresolved-multifold-v1.yml`

Canonical result must persist:

- run ID;
- artifact ID;
- ZIP SHA256;
- JSON SHA256;
- exact selected candidate per horizon;
- all development-fold evidence;
- all reference evidence;
- explicit decision;
- canonical docs update.

Production remains unchanged throughout.
