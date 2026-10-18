# C1 Forward Event Diagnostic v1

Last updated: **2026-10-18**  
Status: **RETROSPECTIVE DIAGNOSTIC / NO MODEL CHANGE**

## Purpose

The chronological v8 policy validation showed that Structural Prior beat raw Live on the currently available four forward events, while the frozen v8 gate safely selected PRIOR in all 16 rows.

This diagnostic asks a narrower follow-up question:

> Which live feature groups are associated with the raw Live failure on those four folds, and is the failure a simple one-direction calibration problem or a more heterogeneous trajectory/generalisation problem?

## Scope

The diagnostic reuses exactly the same chronological setup:

- final-24h T-1 rows only;
- minimum 5 earlier completed events before a fold is scored;
- later event is real and never used in its own training set;
- v2 real-only Ridge expert structure remains unchanged;
- frozen v8 thresholds remain unchanged;
- production remains unchanged.

## Diagnostics

For each forward fold the experiment records:

1. all row-level Prior, raw Live and frozen-policy predictions;
2. signed and absolute errors;
3. v8 selection reason, disagreement and live-prediction slope;
4. train-vs-test median/missingness drift for compact live features;
5. leave-one-feature-group-out sensitivity for:
   - `baseline_prior`;
   - `inventory_level`;
   - `motion_velocity`;
   - `release_coverage`;
   - `data_quality`.

## Interpretation guard

Feature-group ablation is **not causal attribution**.

A group whose removal improves retrospective MAE is only a diagnostic suspect because:

- features are correlated;
- the model is refitted after a group is removed;
- only four chronological forward events are currently available;
- the same data must not be used to retune frozen v8.

The output may guide the design of a future challenger, but it does not promote or modify any production model.

## Implementation

Script:

`ml/c1_forward_event_diagnostic_v1.py`

Workflow:

`.github/workflows/c1-forward-event-diagnostic-v1.yml`

Expected evidence artifact:

`c1-forward-event-diagnostic-v1-<github_run_id>`

The exact result is persisted separately after the first successful main-branch experiment run.
