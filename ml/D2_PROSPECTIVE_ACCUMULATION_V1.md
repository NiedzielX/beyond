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

Scorer:

`ml/d2_prospective_score_v1.py`

Canonical compatibility runner:

`ml/run_d2_prospective_score_v1.py`

Prospective registry:

`ml/artifacts/d2_prospective_registry_v1.json`

Triggers:

- manual `workflow_dispatch`;
- relevant pushes to `main`;
- daily cron `05:23 UTC`.

The scorer never writes model state or commits results automatically. It produces evidence artifacts only. A separate reviewed evidence cycle must persist a newly scored event and register it as exposed.

### Initial green run

Run:

`39312944826`

Main SHA:

`5ce2e8e7bfd5b197510108f441c11a75257fd0c8`

Artifact ID:

`12215847975`

Artifact ZIP SHA256:

`ca470b8f18eddabb8c9f4664baff75a776bb6e64d3e50379f6836c22f3b795cc`

Current exporter:

- 10 events;
- 34 live rows.

Result:

`NO_NEW_ELIGIBLE_EVENTS`

Reason:

- frozen development remains exact 9 events / 30 rows;
- event 5 is already registered as exposed;
- no later completed event currently exists in the exporter.

This confirms the scheduled scorer does not accidentally re-consume event 5 as unseen evidence.

## Objective

Accumulate genuinely prospective independent evidence for the frozen d2 package without silently turning new outcomes into training data.

The active question is no longer:

> Which model or policy should win on the existing data?

It is:

> **Does the already-frozen package continue to improve forecasting on new independent completed events, and which component helps or hurts when it fails?**

## Frozen components

Do not change during the prospective evidence window:

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

## Prospective unit

Independent unit:

`completed ticket event / match`

For every newly eligible completed event:

- it must not be part of the frozen 9-event/30-row development set;
- it must not already be present in the committed prospective registry;
- it must not have been used to select Ridge or P2;
- score it once under the frozen contract;
- persist the result regardless of whether it is favorable;
- do not modify the model/policy in the same evidence cycle.

If no newly eligible event exists, the workflow must finish green as:

`NO_NEW_ELIGIBLE_EVENTS`

If prerequisites for a new event are missing, report the event as blocked; do not silently invent or coerce data.

## Required component scorecard

Persist each layer independently.

### Layer A — Structural T-1 base

Persist:

- base forecast;
- absolute error;
- source model ID.

### Layer B — Frozen Pre-Live v2 / b2

Persist:

- b2 correction seats;
- b2 correction fraction;
- prior same-season home-match count;
- Frozen-v2 forecast;
- absolute error;
- incremental error change versus Structural base.

This is mandatory because event 5 showed a prospective wrong-direction b2 correction of `-2163.45 seats`.

### Layer C — Raw frozen Ridge

Persist per row:

- raw predicted delta occupancy;
- governed/clipped delta occupancy;
- revised forecast;
- absolute error;
- incremental error change versus Frozen v2.

### Layer D — Frozen P2 governed Ridge

Persist per row:

- observation index;
- time to kickoff;
- P2 reliability;
- applied delta;
- revised forecast;
- absolute error;
- incremental error change versus raw Ridge and Frozen v2.

### Layer E — C1 v8 comparator

Use only when genuine pre-outcome persisted C1 v8 predictions/scores exist.

Never reconstruct C1 after seeing the outcome and call it prospective evidence.

Persist:

- package ID;
- chosen expert/reason;
- latest error;
- window error;
- provenance proving pre-outcome persistence.

The automated d2 scorer leaves C1 as a separate evidence join so it cannot create a post-outcome comparator accidentally.

## Required metrics

At event level:

- latest absolute error for every layer;
- event-balanced trajectory/window MAE for every layer;
- component incremental improvement/degradation;
- final forecast bias;
- maximum live revision;
- P2 reliability activation profile.

Across accumulated prospective events:

- mean latest MAE;
- median latest AE;
- event-balanced window MAE;
- bias;
- p90 latest AE;
- worst event degradation by component;
- event improvement rate;
- cumulative component contribution:
  - Structural -> Frozen v2/b2;
  - Frozen v2 -> raw Ridge;
  - raw Ridge -> P2;
- club-level diagnostics only when sample size is sufficient.

## Event-5 baseline evidence

First chronological holdout:

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

Potential signal:

> The same-season residual layer may overreact negatively for some high-demand Lech matches.

Do not declare H1 proven from event 5.

Track prospectively:

- sign of b2 correction;
- magnitude;
- base vs Frozen-v2 error;
- club;
- opponent/context only as descriptive data unless already frozen PIT-safe.

### H2 — P2 early conservatism cost

Event 5 showed that P2 shrank useful early Ridge corrections and therefore worsened window MAE versus raw Ridge, while matching Ridge at the final mature observation.

Do not tune P2 from this one event.

Track:

- raw Ridge vs P2 error by observation index;
- whether P2 prevents harmful early corrections on other events;
- aggregate risk/return trade-off prospectively.

## Registry rule

Current registry:

`d2-prospective-registry-v1`

The registry is not a training set.

Its purpose is to mark prospective events that are already exposed so they cannot be scored again as unseen evidence.

A newly scored event enters the registry only after:

1. successful frozen scorer run;
2. evidence artifact review;
3. human-readable result persistence when material;
4. explicit reviewed registry update.

The scheduled workflow has read-only repository permissions and cannot update the registry itself.

## Reopening threshold

Do not start a new challenger simply because one future event is bad.

A separately versioned reopening/retraining cycle requires:

1. materially more independent prospective events;
2. a repeated, interpretable failure mode;
3. a predeclared new hypothesis before retuning;
4. frozen current package retained as benchmark;
5. new train/development/forward split declared before evaluation.

No event used as prospective validation may silently become a holdout again after tuning.

## Production promotion boundary

Production promotion requires materially more than event 5.

At minimum require:

- multiple genuinely prospective independent events;
- positive aggregate latest and trajectory MAE uplift;
- acceptable tail behavior;
- no unresolved systematic component failure;
- frozen reproducible package;
- explicit reviewed promotion decision.

Production remains:

`live_adjustment = 0`

## CI/CD contract

Every prospective scoring run must persist:

- code version / main SHA;
- exporter/data version;
- event IDs;
- model/policy package IDs;
- PIT assertions;
- no-training/no-selection assertions;
- machine-readable event-level JSON/CSV;
- cumulative prospective summary when events exist;
- SHA256 hashes;
- run/artifact IDs;
- human-readable result when a new event closes;
- canonical state update when evidence materially changes interpretation.

## One-line instruction

> **The scheduled frozen scorer is active. Keep the d2 package frozen; when a new eligible completed event appears, score it append-only, persist Structural base -> Frozen-v2/b2 -> raw Ridge -> P2 -> genuine persisted C1 comparator as separate layers, register it as exposed only after review, monitor the event-5 b2/P2 signals without tuning them, and only open a new versioned challenger after materially more independent prospective evidence.**
