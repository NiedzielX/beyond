# Beyond Ticketing — d2 Prospective Accumulation v1

Last updated: **2026-10-19**

Status: **ACTIVE / SCHEDULED DAILY / FROZEN MODEL-POLICY / NO RETRAINING / NO PRODUCTION CHANGE**

Parent evidence:

- `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
- `ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`;
- `ml/results/D2_PROSPECTIVE_SCORE_V1_INITIAL_2026-10-19.md`.

Frozen package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

## Operational scorer

Workflow:

`.github/workflows/d2-prospective-score-v1.yml`

Frozen scorer:

`ml/d2_prospective_score_v1.py`

Readiness classifier:

`ml/d2_prospective_outcome_readiness_v1.py`

Evidence-class contract:

`ml/d2_prospective_evidence_class_v1.py`

Canonical compatibility runner:

`ml/run_d2_prospective_score_v1.py`

Prospective registry:

`ml/artifacts/d2_prospective_registry_v1.json`

Triggers:

- manual `workflow_dispatch`;
- relevant pushes to `main`;
- daily cron `05:23 UTC`.

The workflow never writes model state or commits results automatically. It produces evidence artifacts only. A separate reviewed evidence cycle must persist a newly scored event and register it as exposed.

## Two separate export contracts

### Frozen scoring exports

The existing `v7-*` C1 exports remain unchanged and continue to drive model scoring/reconstruction.

In particular, `v7-events` intentionally contains only events with verified outcomes. Do not loosen this frozen training/evidence contract to improve observability.

### Additive readiness feed

Readiness uses a separate route:

`d2-readiness -> public.export_d2_prospective_readiness_v1()`

This read-only feed exposes all tracked Ekstraklasa ticket events with:

- LEFT JOIN verified attendance outcome;
- audited home capacity when available;
- raw final-24h snapshot count from `public.snapshots`;
- outcome/capacity provenance;
- no attendance inference from inventory.

This separation ensures that an event waiting for truth data is visible without changing any frozen model-scoring export.

## Evidence classes — mandatory

Frozen Stage-2 evidence cutoff:

`2026-10-19T19:11:01Z`

This is the end of the canonical Stage-2 main CI run that selected/froze P2.

Every unregistered event is classified from kickoff time as one of:

### `DELAYED_LABEL_HOLDOUT`

`kickoff_at <= Stage-2 freeze cutoff`

The event was not used in development, but it had already kicked off before the frozen package was canonically established.

It may still be useful as delayed-label / chronological diagnostic evidence, but it **does not count as genuinely post-freeze prospective evidence for production promotion**.

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

The post-match grace period is **3 hours**, aligned with the trusted outcome-sync boundary.

Mandatory rule:

> **Never estimate actual attendance from seat-map inventory to unblock scoring.**

## Current readiness discovery

The additive feed currently exposes **21 tracked Ekstraklasa events**.

It revealed completed events that the outcome-gated `v7-events` export correctly did not expose yet.

Notable current blockers include:

- event `15` — GKS Katowice vs Pogoń Szczecin — 96 raw final-24h snapshots — outcome missing;
- event `18` — Cracovia vs Legia Warszawa — 51 raw final-24h snapshots — outcome missing;
- event `11` — Górnik Zabrze vs Piast Gliwice — 96 raw final-24h snapshots — outcome missing;
- event `19` — KGHM Zagłębie Lubin vs Jagiellonia Białystok — 96 raw final-24h snapshots — outcome missing;
- event `20` — Wisła Płock vs Radomiak Radom — verified capacity `15,004`, 96 raw final-24h snapshots — outcome missing.

All five kicked off before the Stage-2 freeze cutoff, so if/when trusted outcomes arrive they are **delayed-label holdouts**, not true post-freeze prospective evidence.

The first currently tracked matches that can qualify as true post-freeze prospective evidence are later fixtures such as event `10` / `16` and subsequent events, provided their live trajectory and verified outcome eventually meet the frozen scoring contract.

## Trusted outcome pipeline

Outcome sync already exists:

`supabase/sql/ticket_event_outcome_history_sync_v1.sql`

Operational rules:

- source = `ml_home_attendance_history_v2`;
- exact `club_slug + kickoff_at` matching;
- only Ekstraklasa;
- only after kickoff + 3 hours;
- never overwrite an existing outcome;
- hourly cron at minute `17`.

A `BLOCKED_MISSING_OUTCOME` event remains blocked until trusted outcome data enters this pipeline. Do not manually derive truth from ticket inventory.

## Objective

Accumulate honest independent evidence for the frozen d2 package without silently turning new outcomes into training data or overstating retrospective/delayed labels as prospective validation.

The active question is:

> **Does the already-frozen package continue to improve forecasting on genuinely new post-freeze completed events, and which component helps or hurts when it fails?**

Delayed-label holdouts may supplement diagnosis but must be reported separately.

## Frozen components

Do not change during the evidence window:

- Pre-Live v2 freeze ID: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- Stage-1 expert: `ridge-a10`;
- Ridge alpha: `10.0`;
- Stage-1 feature contract and preprocessing;
- raw Ridge correction cap: +/-10pp occupancy;
- Stage-2 policy: `P2-observation-maturity`;
- P2 observation/time weights;
- frozen C1 v8 package when used as comparator.

## Frozen P2 policy

Observation maturity:

- observation 1: `0.25`;
- observation 2: `0.60`;
- observation 3+: `1.00`.

Time-to-kickoff cap:

- >18h: `0.75`;
- >12h and <=18h: `0.90`;
- <=12h: `1.00`.

Final:

`reliability = min(observation_index_weight, time_weight)`

## Scoring unit

Independent unit:

`completed ticket event / match`

For every newly scoreable event:

- it must not be part of the frozen 9-event/30-row development set;
- it must not already be present in the committed registry;
- it must not have been used to select Ridge or P2;
- assign evidence class before interpretation;
- score it once under the frozen contract;
- persist the result regardless of whether favorable;
- do not modify the model/policy in the same evidence cycle.

If no newly eligible event exists, the model scorer may finish green as:

`NO_NEW_ELIGIBLE_EVENTS`

The readiness artifact must still show tracked future/blocking state independently.

## Required component scorecard

Persist each layer independently.

### Layer A — Structural T-1 base

- base forecast;
- absolute error;
- source model ID.

### Layer B — Frozen Pre-Live v2 / b2

- b2 correction seats/fraction;
- prior same-season home-match count;
- Frozen-v2 forecast/error;
- incremental error change versus Structural base.

This is mandatory because event 5 showed a wrong-direction b2 correction of `-2163.45 seats`.

### Layer C — Raw frozen Ridge

Per row:

- raw predicted delta occupancy;
- governed/clipped delta;
- revised forecast/error;
- incremental error change versus Frozen v2.

### Layer D — Frozen P2 governed Ridge

Per row:

- observation index;
- time to kickoff;
- P2 reliability;
- applied delta;
- revised forecast/error;
- incremental error versus raw Ridge and Frozen v2.

### Layer E — C1 v8 comparator

Use only when genuine pre-outcome persisted C1 v8 predictions/scores exist.

Never reconstruct C1 after seeing the outcome and call it prospective evidence.

## Required aggregate metrics

Always separate:

1. delayed-label holdouts;
2. true post-freeze prospective events.

For each class report:

- event count;
- mean latest MAE;
- median latest AE;
- event-balanced window MAE;
- bias;
- p90 latest AE where sample size permits;
- worst event degradation by component;
- event improvement rate;
- cumulative component contribution:
  - Structural -> Frozen v2/b2;
  - Frozen v2 -> raw Ridge;
  - raw Ridge -> P2.

Only the `TRUE_POST_FREEZE_PROSPECTIVE` class may satisfy production-promotion sample requirements.

## Event-5 baseline evidence

First explicitly reserved chronological holdout:

`ticket_event_id = 5`

Result:

- Structural T-1 base error: `7669.07`;
- Frozen-v2 error: `9832.52`;
- raw Ridge latest error: `6652.81`;
- P2 latest error: `6652.81`;
- persisted C1 v8 policy/latest error: `7669.07`.

Fresh component warning:

`b2 correction = -2163.45 seats`, worsening the anchor by the same amount.

This is one failure signal only.

## Hypotheses to monitor, not tune yet

### H1 — b2 negative overreaction

Track:

- sign/magnitude of b2 correction;
- Structural vs Frozen-v2 error;
- club;
- opponent/context only as descriptive data unless already frozen PIT-safe.

Do not declare H1 proven from event 5.

### H2 — P2 early conservatism cost

Track:

- raw Ridge vs P2 error by observation index;
- whether P2 prevents harmful early corrections on later events;
- aggregate risk/return trade-off separately by evidence class.

Do not tune P2 from one/few events.

## Registry rule

Current registry:

`d2-prospective-registry-v1`

The registry is not a training set.

Its purpose is to mark events already exposed/scored so they cannot be presented again as unseen evidence.

When registering future events, persist their evidence class explicitly in the reviewed result/registry cycle.

A newly scored event enters the registry only after:

1. successful frozen scorer run;
2. evidence artifact review;
3. human-readable result persistence when material;
4. explicit reviewed registry update.

The scheduled workflow has read-only repository permissions and cannot update the registry itself.

## Reopening threshold

Do not start a new challenger because one event is bad.

A separately versioned reopening/retraining cycle requires:

1. materially more independent evidence, especially true post-freeze events;
2. a repeated interpretable failure mode;
3. a predeclared new hypothesis before retuning;
4. frozen current package retained as benchmark;
5. new train/development/forward split declared before evaluation.

No scored validation event may silently become unseen holdout again after tuning.

## Production promotion boundary

Production promotion requires materially more than event 5 or delayed-label holdouts.

At minimum require:

- multiple **TRUE_POST_FREEZE_PROSPECTIVE** independent events;
- positive aggregate latest and trajectory MAE uplift on that class;
- acceptable tail behavior;
- no unresolved systematic component failure;
- frozen reproducible package;
- explicit reviewed promotion decision.

Production remains:

`live_adjustment = 0`

## CI/CD contract

Every scheduled scoring run must persist:

- code/main SHA;
- frozen scoring export versions;
- readiness export version;
- Stage-2 freeze cutoff;
- readiness/evidence class per surfaced event;
- model/policy package IDs;
- PIT assertions;
- no-training/no-selection/no-attendance-estimation assertions;
- machine-readable readiness + scoring JSON/CSV;
- SHA256 hashes;
- run/artifact IDs;
- human-readable result when material evidence closes;
- canonical state update when evidence materially changes interpretation.

## One-line instruction

> **Keep the d2 package frozen. Use the dedicated tracked-event readiness feed to surface missing prerequisites, never infer attendance from inventory, classify every event as delayed-label or true post-freeze prospective before interpretation, score newly eligible events append-only under the frozen package, and count only TRUE_POST_FREEZE_PROSPECTIVE events toward production-promotion evidence.**
