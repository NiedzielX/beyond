# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Then read `ml/MAE_RESEARCH_ROADMAP_V3.md`.
3. Read `ml/PROGRESS_TRACKING.md` for the latest canonical state.
4. For P4/P5, read `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md` before touching feature selection or model code.
5. For P7/Long168, read `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` before touching code or data.
6. Read `ml/CURRENT_MODEL.md`, `ml/CORE_PRODUCT_STATUS.md`, `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`, and `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` as relevant.
7. Do **not** retrain/rebuild frozen historical benchmarks merely to recover context.
8. For latest-state questions, use targeted repo/DB reads rather than historical recomputation.
9. Never store secrets/tokens/service-role keys in repo files.

## Core principle

> **The objective is lower true out-of-sample MAE, not model complexity.**

Always separate:

- Evidence Lane — immutable packages collecting forward evidence;
- MAE R&D Lane — versioned challengers developed in parallel.

Never fabricate PIT history when a state was not captured.

## Validation rule

Use `ml/temporal_validation_v1.py`.

Historical/global:

- strict season/group expanding folds;
- no future-season data in earlier train folds;
- persist exact fold identities + SHA.

Live/context:

- `ticket_event` is the independent unit;
- strict forward-event validation by kickoff;
- tied kickoffs cannot train one another;
- no random snapshot split as headline evidence.

## Closed research loops

Do not reopen without a materially new hypothesis/data source:

1. MAE-native estimator tournament;
2. estimator `ΔMAE` uncertainty;
3. historical Long72 incremental live value;
4. structural/live convex shrinkage;
5. simple post-hoc club/opponent calibration.

## Frozen packages

Do not mutate:

- final24 `v2/Ridge/P2`;
- Long72 `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`;
- Pre-Live / Structural Prior anchors.

Any material feature/model/weight/target change requires a new challenger/version.

## Current evidence checkpoint

Use `public.ml_research_readiness_v1()` instead of relying on prose counts.

Latest checkpoint on 2026-10-23:

- Long72 reproducible forecasts `66`;
- genuine scored Long72 events `0`;
- fixture context `66 / 64 READY`;
- P4a independent READY events `5`;
- P4a labeled READY events `0`;
- next-opponent `66 / 0 READY`;
- Long168 `8/9`, `110` rows >72h.

## P4a fixture context — already frozen

P4a is no longer a feature-selection/design task.

Research question:

> Does `previous_home_match_days` reduce event-level attendance MAE beyond the frozen Long72 pre-live T3+B2 anchor?

Canonical files:

- `supabase/sql/p4_fixture_context_precommit_v1.sql`;
- `ml/p4_fixture_context_harness_v1.py`;
- `ml/test_p4_fixture_context_harness_v1.py`;
- `.github/workflows/p4-fixture-context-precommit-v1.yml`;
- `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md`.

### Independent unit and row selection

- independent unit = `ticket_event`;
- exactly first READY context row per reproducible Long72 event;
- one frozen context observation per event.

### P4a control

`long72-prelive-t3-b2-anchor`

This is frozen Structural Prior T-3 plus frozen B2 current-season correction. It contains no Long72 live/P2 signal.

### P4a primary feature

Only:

`previous_home_match_days`

Current pre-label values over five READY events:

`13, 36, 15, 14, 15`

Coverage 5/5; four distinct values.

### Hard start gate

Evaluation is prohibited until both are true:

- `>=9` labeled independent events;
- `>=3` distinct labeled spacing values.

Do not change this threshold after seeing outcomes/model results.

### Target separation

- `export_p4_fixture_context_inputs_v1()` = target-free inputs;
- `export_p4_fixture_context_labels_v1()` = labels only.

Required sequence:

`target-free export -> freeze identities/features/anchor -> SHA -> explicit execute -> labels -> reproduce freeze -> 9/3 gate -> evaluation`

Automatic main runs must never fetch labels.

Real target-free main audit run `40012547250` passed:

- event count `5`;
- distinct feature values `4`;
- manifest SHA `15cb691b8874dee1e086089f90c9f239b703f9b33894945debe0c819ec73fc86`;
- target values opened `false`;
- model training performed `false`.

### Fixed P4a challenger

`q50-linear-prev-home-spacing-a002`

- residual target = actual attendance - T3+B2 anchor;
- only feature `previous_home_match_days`;
- QuantileRegressor q=.5 alpha=.002;
- RobustScaler;
- no broad search;
- strict forward-event validation, min 5 train events;
- paired event-block bootstrap 5,000 draws seed 42.

Advance only if:

- MAE below anchor;
- >50% held-out events improve;
- >50% forward folds improve.

No P4a result directly activates production.

### Explicitly excluded P4a features

Do not silently add:

- `next_home_match_days` — sparse, currently 1/5 coverage;
- team/home fixture density 7/14/30d — currently no useful event-level variance.

A later activation requires a new precommit/version.

## P4b next-opponent attractiveness

Current state: `0 READY`.

Never reconstruct missing opponent attractiveness from later schedule/outcome knowledge.

## P5

Do not start P5 until P4a or another separately precommitted context experiment demonstrates incremental signal.

If context advances, combine pre-live/structural + context + live using fold-local weights only. Never learn weights on evaluation folds.

## P7 Long168 — harness + executor complete

P7 is fully precommitted and executable but blocked at `8/9`.

Canonical files:

- `ml/p7_long168_harness_v1.py`;
- `ml/p7_long168_anchor_replay_v1.py`;
- `ml/p7_long168_tournament_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `.github/workflows/p7-long168-executor-v1.yml`.

Research start requires `N>=9` independent events with valid >72h observations.

At `N<9`:

- real model execution fails closed;
- only T-7 anchor audit is allowed;
- never lower the gate.

Historical T-7 control is:

`historical_pit_replay`

with:

`persisted_forecast = false`.

The real audit passed target-attendance invariance `8/8`.

At 9/9:

1. read fresh readiness;
2. explicit `mode=execute` dispatch;
3. freeze exact event/as-of/snapshot/bucket identities;
4. persist SHA;
5. verify T-7 replay;
6. only then attach labels;
7. strict forward folds;
8. fixed tournament;
9. uncertainty;
10. research decision only.

## Evidence operations

Operational pipelines are active:

- Long72 forecast-before-label hourly;
- outcome-history sync hourly;
- completed-event scoring in prospective cycle;
- schedule-as-known every 6h;
- fixture-context sidecar every 15m;
- next-opponent sidecar every 15m.

Do not add another tuning loop while P4a/P7 gates are closed.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until explicit reviewed activation based on genuine future evidence.
