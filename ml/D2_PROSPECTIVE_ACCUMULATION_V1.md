# Beyond Ticketing — d2 Prospective Accumulation v1

Last updated: **2026-10-21**

Status: **ACTIVE TRACK-A VALIDATION / SCHEDULED DAILY / FROZEN MODEL-POLICY / NO PRODUCTION CHANGE**

Parent evidence:

- `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
- `ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`;
- `ml/results/D2_PROSPECTIVE_SCORE_V1_INITIAL_2026-10-19.md`;
- `ml/results/D2_PROSPECTIVE_READINESS_V1_2026-10-19.md`.

Frozen package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

## Scope — important

This document governs **Track A: prospective validation of the already-frozen d2 package**.

It does **not** prohibit separate Track-B model R&D.

Track A rule:

> Do not mutate Ridge/P2 from events being used to validate Ridge/P2.

Track B rule:

> A new, separately versioned model/target/ensemble hypothesis may be researched now under its own predeclared train/development/reference boundary. It does not need to wait for a prospective sample-count threshold.

Production promotion still requires genuine prospective evidence.

## Operational scorer

Workflow:

`.github/workflows/d2-prospective-score-v1.yml`

Frozen scorer:

`ml/d2_prospective_score_v1.py`

Readiness classifier:

`ml/d2_prospective_outcome_readiness_v1.py`

Evidence-class contract:

`ml/d2_prospective_evidence_class_v1.py`

Prospective registry:

`ml/artifacts/d2_prospective_registry_v1.json`

Triggers:

- manual `workflow_dispatch`;
- relevant pushes to `main`;
- daily cron `05:23 UTC`.

The workflow never writes model state or commits results automatically. It produces evidence artifacts only.

## Two separate export contracts

### Frozen scoring exports

Existing `v7-*` C1 exports remain unchanged and continue to drive frozen model scoring/reconstruction.

Do not loosen the scoring/training contract merely to improve observability.

### Additive readiness feed

Readiness uses:

`d2-readiness -> public.export_d2_prospective_readiness_v1()`

The feed surfaces tracked events with outcome/capacity/snapshot readiness without changing the frozen scoring export.

Mandatory rule:

> **Never estimate actual attendance from seat-map inventory to unblock scoring.**

## Evidence classes — mandatory

Frozen Stage-2 evidence cutoff:

`2026-10-19T19:11:01Z`

### `DELAYED_LABEL_HOLDOUT`

`kickoff_at <= Stage-2 freeze cutoff`

Useful as delayed-label / chronological diagnostic evidence, but it **does not count as genuinely post-freeze prospective evidence for production promotion**.

### `TRUE_POST_FREEZE_PROSPECTIVE`

`kickoff_at > Stage-2 freeze cutoff`

This is the class that can accumulate as genuine forward evidence for eventual promotion decisions.

Never combine these classes into one headline prospective sample size.

## Readiness states

Every non-development, non-registered tracked event receives one state:

- `READY_FOR_PROSPECTIVE_SCORE`;
- `BLOCKED_MISSING_OUTCOME`;
- `BLOCKED_NO_FINAL24_LIVE_ROWS`;
- `BLOCKED_MISSING_CAPACITY`;
- `WAITING_POST_MATCH_GRACE`;
- `FUTURE_NOT_DUE`.

Post-match grace period:

`3 hours`

A readiness/data blocker is a data-contract issue and must not pause unrelated Track-B R&D.

## Objective

Accumulate honest independent evidence for the frozen d2 package without silently turning newly scored outcomes into training data or overstating delayed labels as prospective validation.

The Track-A question is:

> **Does the already-frozen package continue to improve forecasting on genuinely new post-freeze completed events, and which component helps or hurts when it fails?**

## Frozen components

Do not change within this Track-A evidence package:

- Pre-Live v2 freeze ID `pre-live-v2-historical-candidate-2026-10-18-v1`;
- Stage-1 expert `ridge-a10`;
- Ridge alpha `10.0`;
- Stage-1 feature contract/preprocessing;
- raw Ridge correction cap +/-10pp occupancy;
- Stage-2 policy `P2-observation-maturity`;
- P2 observation/time weights;
- frozen C1 v8 package where used as comparator.

## Frozen P2 policy

Observation maturity:

- observation 1 `0.25`;
- observation 2 `0.60`;
- observation 3+ `1.00`.

Time-to-kickoff cap:

- >18h `0.75`;
- >12h and <=18h `0.90`;
- <=12h `1.00`.

Final:

`reliability = min(observation_index_weight, time_weight)`

## Scoring unit

Independent unit:

`completed ticket event / match`

For every newly scoreable event:

- not part of the frozen 9-event/30-row development set;
- not already in the prospective registry;
- not used to select Ridge/P2;
- evidence class assigned before interpretation;
- scored once under the frozen contract;
- result persisted regardless of direction;
- no mutation of the frozen package in the same evidence cycle.

If no newly eligible event exists, scorer may finish green as:

`NO_NEW_ELIGIBLE_EVENTS`

## Required component scorecard

### Layer A — Structural T-1 base

Persist forecast, absolute error and model ID.

### Layer B — Frozen Pre-Live v2 / b2

Persist b2 correction, prior same-season home-match count, Frozen-v2 forecast/error and incremental error change vs Structural base.

### Layer C — Raw frozen Ridge

Persist raw/governed delta, revised forecast/error and incremental effect vs Frozen v2.

### Layer D — Frozen P2 governed Ridge

Persist observation index, time to kickoff, reliability, applied delta, revised forecast/error and incremental effect vs raw Ridge/Frozen v2.

### Layer E — C1 v8 comparator

Use only when genuine pre-outcome persisted C1 evidence exists.

Never reconstruct C1 after seeing the outcome and call it prospective.

## Aggregate metrics

Always report delayed-label and true-post-freeze classes separately.

For each class:

- event count;
- mean latest MAE;
- median latest AE;
- event-balanced window MAE;
- bias;
- p90 latest AE where sample size permits;
- worst event degradation by component;
- event improvement rate;
- component contribution:
  - Structural -> Frozen v2/b2;
  - Frozen v2 -> raw Ridge;
  - raw Ridge -> P2.

Only `TRUE_POST_FREEZE_PROSPECTIVE` may satisfy production-promotion sample requirements.

## Event-5 baseline evidence

`ticket_event_id = 5`

- Structural T-1 base error `7669.07`;
- Frozen-v2 error `9832.52`;
- raw Ridge latest error `6652.81`;
- P2 latest error `6652.81`;
- persisted C1 v8 error `7669.07`.

Event 5 is permanently exposed.

## Delayed-label diagnostics

Current recovered diagnostics include:

- GKS Katowice–Pogoń: Frozen Pre-Live latest error about `1356`, d2/P2 about `2074`;
- Cracovia–Legia: Frozen about `434`, d2/P2 about `1068`.

These events may generate future hypotheses. They cannot be used to mutate current Ridge/P2 and then be presented as unseen validation of that mutation.

## Hypotheses to monitor in Track A

### H1 — b2 negative overreaction

Track b2 sign/magnitude and Structural vs Frozen-v2 error.

Do not modify frozen b2 from individual exposed events.

### H2 — P2 early conservatism cost

Track raw Ridge vs P2 by observation maturity.

Do not modify frozen P2 from individual exposed events.

## Registry rule

The registry is not a training set. Its purpose is to mark exposed/scored events so they cannot later be presented as unseen evidence.

Register an event only after reviewed frozen scoring evidence is persisted.

## Frozen-package reopening vs separate R&D

Do not **rewrite the current frozen d2 package** because one or a few scored events are bad.

A decision to replace/promote that frozen package from Track-A evidence requires materially more independent evidence and repeated interpretable failure/success patterns.

However, this is **not a global R&D gate**.

A separate Track-B challenger may be started now if it has:

1. a materially different predeclared hypothesis;
2. a new candidate/version ID;
3. an honest historical/development/reference boundary;
4. frozen current package retained as benchmark;
5. all exposed events labeled honestly.

Current priority is Pre-Live v3 anchor/regime research. If v3 later freezes, the live residual model must be rebuilt/revalidated against that anchor under a new d2 version.

## Production promotion boundary

Production promotion requires multiple `TRUE_POST_FREEZE_PROSPECTIVE` independent events, positive aggregate latest/trajectory uplift, acceptable tails/bias, no unresolved systematic component failure, a frozen reproducible package and explicit reviewed promotion.

Production remains:

`live_adjustment = 0`

## CI/CD contract

Every scheduled scoring run must persist:

- code/main SHA;
- frozen export versions;
- readiness export version;
- Stage-2 freeze cutoff;
- evidence class per surfaced event;
- model/policy package IDs;
- PIT assertions;
- no-training/no-selection/no-attendance-estimation assertions;
- machine-readable readiness + scoring evidence;
- hashes;
- run/artifact IDs;
- reviewed human-readable result when material.

## One-line instruction

> **Keep the d2 v2/Ridge/P2 package frozen for Track-A scoring, classify delayed-label vs true-post-freeze evidence honestly, and count only true post-freeze events toward production promotion. This validation contract does not block separately versioned Track-B R&D; active model R&D is now the Pre-Live v3 anchor/regime cycle.**
