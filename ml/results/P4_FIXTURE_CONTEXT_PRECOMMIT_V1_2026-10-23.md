# P4a Fixture Context Precommit v1 — 2026-10-23

## Status

**PRECOMMITTED / TARGET-FREE INPUT PATH READY / DATA-BOUND**

Production remains unchanged:

`live_adjustment = 0`

## Research question

> Does previous-home match spacing reduce event-level attendance MAE beyond the frozen Long72 pre-live T3+B2 anchor?

This experiment isolates fixture-context value before any Structural + Context + Live combination work.

## Independent evidence unit

`ticket_event`

Snapshot rows are not independent evidence for P4a.

For each event, P4a uses exactly the **first READY fixture-context row** attached to a reproducible Long72 prediction.

## Anchor

Control:

`long72-prelive-t3-b2-anchor`

Definition:

- frozen Structural Prior T-3;
- plus frozen B2 current-season residual correction;
- no Long72 live inventory/P2 signal.

Therefore P4a measures incremental context value over the pre-live anchor, not over the live P2 package.

## Feature selection performed before labels

Primary P4a v1 feature:

`previous_home_match_days`

Latest target-free audit before any genuine labels:

- READY independent events: `5`;
- event IDs: `10, 16, 21, 22, 23`;
- previous-home spacing values: `13, 36, 15, 14, 15` days;
- non-null coverage: `5/5`;
- distinct values: `4`;
- observed range: `13–36` days;
- genuine labeled events: `0`.

This is enough to establish that the feature has real pre-label coverage and variance, but not enough to start model evaluation.

## Features explicitly excluded from P4a v1

### `next_home_match_days`

Current coverage is only `1/5` independent events.

Status:

`SEPARATE_SPARSE_FEATURE_NOT_IN_P4A_V1`

Missing is not zero.

### Fixture density

Current event-level values show no useful variance:

- team density 7d: one distinct value;
- team density 14d: one distinct value;
- team density 30d: one distinct value;
- home density 7d: one distinct value;
- home density 14d: one distinct value;
- home density 30d: one distinct value.

Status:

`INACTIVE_UNTIL_REAL_VARIANCE`

Minimum activation condition for a later experiment family: at least two distinct event-level values before labels/model results are used for feature selection.

## Hard research-start gate

P4a v1 model evaluation is prohibited until both are true:

1. at least `9` independent labeled events with non-null `previous_home_match_days`;
2. at least `3` distinct spacing values among those labeled events.

`N=9` is a research-start floor only. It is not evidence of production adequacy.

The threshold was frozen before any P4a target values/model results were opened.

## Target separation

Canonical exports:

- `public.export_p4_fixture_context_inputs_v1()` — target-free context/anchor identities;
- `public.export_p4_fixture_context_labels_v1()` — labels only.

The GitHub workflow must:

1. fetch target-free inputs;
2. freeze exact identities/features/anchor values and manifest SHA;
3. only on explicit `workflow_dispatch -> mode=execute` fetch labels;
4. reproduce the freeze before any evaluation;
5. fail closed unless the hard research-start gate passes.

Automatic main-branch audit never fetches labels.

## Frozen candidate family

### Control

`long72-prelive-t3-b2-anchor`

### Challenger

`q50-linear-prev-home-spacing-a002`

Specification:

- residual target: `actual_attendance - anchor_p50`;
- only feature: `previous_home_match_days`;
- `SimpleImputer(strategy=median)`;
- `RobustScaler`;
- `QuantileRegressor`;
- quantile `0.50`;
- alpha `0.002`;
- solver `highs`;
- no hyperparameter search.

A different context feature/model family requires a new experiment version.

## Validation

Canonical strict forward-event validation:

- independent unit: event;
- minimum training events: `5`;
- `train_end < test_start`;
- tied kickoffs cannot train one another;
- no random snapshot split;
- exact fold manifest SHA persisted.

At exactly nine chronologically distinct events this normally produces four forward held-out events, subject to tied kickoffs.

## Primary metric

Event-level MAE against the pre-live T3+B2 anchor.

Because P4a has one frozen context row per event, each held-out event contributes exactly one error observation.

Required diagnostics:

- challenger MAE;
- anchor MAE;
- `ΔMAE`;
- event-improvement rate;
- forward-fold improvement rate;
- worst-event degradation.

## Uncertainty

Paired event-block bootstrap:

- 5,000 draws;
- seed `42`.

## Research advancement rule

The challenger advances only if all are true:

1. strict-forward MAE < anchor MAE;
2. event improvement rate >50%;
3. forward-fold improvement rate >50%;
4. freeze / PIT / lineage gates pass.

Otherwise:

`RETAIN_ANCHOR`

Bootstrap uncertainty must always be reported with the decision.

## Production boundary

P4a v1 cannot activate production directly.

Even a positive P4a result only permits the next research step:

`P5 Structural/Pre-live + Context + Live combination research`

Production remains:

`live_adjustment = 0`

## Canonical implementation

- `supabase/sql/p4_fixture_context_precommit_v1.sql`;
- `ml/p4_fixture_context_harness_v1.py`;
- `ml/test_p4_fixture_context_harness_v1.py`;
- `.github/workflows/p4-fixture-context-precommit-v1.yml`;
- `supabase/functions/c1_alpha_training_export_v1/index.ts`;
- `supabase/sql/ml_research_readiness_v1.sql`.

## Current decision

**WAIT FOR GENUINE LABELS. DO NOT RUN P4a MODEL EVALUATION YET.**

Current gate:

`0/9 labeled events`, while pre-label feature coverage/variance is already sufficient to keep the frozen P4a v1 design.
