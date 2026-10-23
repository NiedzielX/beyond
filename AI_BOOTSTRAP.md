# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-23**

## Cold-start rule

Read in this order:

1. `ml/MAE_RESEARCH_ROADMAP_V3.md`;
2. `ml/PROGRESS_TRACKING.md`;
3. `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md` when working on P4/P5;
4. `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` when working on P7/Long168;
5. `ml/CURRENT_MODEL.md`;
6. `ml/CORE_PRODUCT_STATUS.md`;
7. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
8. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
9. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

Do not rebuild frozen historical benchmarks merely to recover context.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons, using honest PIT-safe and reproducible evidence.**

Model complexity is secondary. New predictive information and future MAE are primary.

Production remains:

`live_adjustment = 0`

## Structural core

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- Structural Prior / Global Model remains incumbent;
- historical runtime SHA: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Previously inspected historical seasons remain exposed research evidence.

## Frozen Long72 package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical comparison:

- anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- `ΔMAE=-694.51` / `18.73%`;
- 95% interval `[-1549.89,+148.05]`;
- P2 bias `+917.05`.

Immutable. Genuine prospective evidence continues.

## Closed loops

Do not reopen without materially new information:

- P2 estimator tournament;
- P3 estimator uncertainty;
- P5a structural/live shrinkage;
- P6 historical incremental live value;
- P8 simple club/opponent calibration.

## Current live checkpoint

Always read fresh state from:

`public.ml_research_readiness_v1()`

Latest checkpoint on 2026-10-23:

- Long72 reproducible forecasts: `66`;
- genuine Long72 scored events: `0`;
- fixture-context sidecar: `66 / 64 READY`;
- P4a independent READY events: `5`;
- P4a genuine labeled READY events: `0`;
- P4 next-opponent sidecar: `66 / 0 READY`;
- Long168: `8/9` independent events >72h, `110` rows >72h.

Do not rely on prose counts when a fresh RPC result is available.

## P4a — previous-home spacing is already precommitted

Do **not** redesign P4a after labels arrive.

Canonical files:

- `supabase/sql/p4_fixture_context_precommit_v1.sql`;
- `ml/p4_fixture_context_harness_v1.py`;
- `ml/test_p4_fixture_context_harness_v1.py`;
- `.github/workflows/p4-fixture-context-precommit-v1.yml`;
- `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md`.

Research question:

> Does `previous_home_match_days` reduce event-level attendance MAE beyond the frozen Long72 pre-live T3+B2 anchor?

Independent unit:

`ticket_event`

Input selection:

- exactly first READY fixture-context row per reproducible Long72 event.

Control:

`long72-prelive-t3-b2-anchor`

This means frozen Structural Prior T-3 + frozen B2 current-season correction, with no Long72 live/P2 signal.

Primary feature:

`previous_home_match_days`

Current target-free values across the first five independent READY events:

`13, 36, 15, 14, 15`

Coverage `5/5`, four distinct values, range 13–36 days.

### P4a hard gate

Real evaluation requires both:

- `>=9` labeled independent events with non-null spacing;
- `>=3` distinct labeled spacing values.

This threshold is frozen. Do not change it after seeing labels or MAE.

### P4a target separation

Inputs and labels are separate:

- `public.export_p4_fixture_context_inputs_v1()` — target-free;
- `public.export_p4_fixture_context_labels_v1()` — labels only.

Mandatory order:

`target-free inputs -> identity/feature/anchor freeze -> manifest SHA -> explicit execute -> labels -> freeze reproduction -> 9/3 gate -> evaluation`

Automatic main runs never open labels.

Real target-free main audit passed on workflow run `40012547250`:

- event count `5`;
- distinct spacing values `4`;
- target values opened `false`;
- model training performed `false`;
- freeze SHA `15cb691b8874dee1e086089f90c9f239b703f9b33894945debe0c819ec73fc86`.

### P4a fixed challenger

- `q50-linear-prev-home-spacing-a002`;
- residual target = attendance minus T3+B2 anchor;
- only feature = `previous_home_match_days`;
- QuantileRegressor q=.5, alpha=.002;
- RobustScaler;
- no hyperparameter search;
- strict forward-event validation, min 5 train events;
- paired event-block bootstrap, 5,000 draws, seed 42.

Advance research only if:

- strict-forward MAE improves;
- event improvement rate >50%;
- forward-fold improvement rate >50%.

### P4a excluded features

Do not silently add:

- `next_home_match_days` — currently sparse, 1/5 coverage;
- team/home fixture density 7/14/30d — currently no useful event-level variance.

These require separate future precommitted experiment versions.

## P4b next-opponent attractiveness

Infrastructure exists and is fail-closed.

Current state: `0 READY`.

Never reconstruct missing opponent attractiveness using outcomes or schedule knowledge unavailable at the forecast cutoff.

## P5 — combination research

Do not start P5 until P4 produces an incremental context signal.

If P4a advances, test Structural/Pre-live + Context + Live in this order:

1. simple mean;
2. median;
3. fixed convex combination;
4. MAE-optimized convex weights learned inside training folds only;
5. regularized stacker only if simpler methods fail.

Never learn combination weights on an evaluation fold.

## P7 Long168 — fully precommitted and executable

Do not redesign P7 at 9/9.

Canonical files:

- `ml/p7_long168_harness_v1.py`;
- `ml/p7_long168_anchor_replay_v1.py`;
- `ml/p7_long168_tournament_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `.github/workflows/p7-long168-executor-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`;
- `ml/results/P7_LONG168_EXECUTOR_V1_2026-10-23.md`;
- `ml/results/P7_LONG168_ANCHOR_AUDIT_V1_2026-10-23.md`.

Research start requires:

`>=9` independent events with valid rows >72h.

At 8/9:

- model execution fails closed;
- only anchor audit is allowed;
- do not lower the threshold.

Historical T-7 control is explicit replay evidence:

`historical_pit_replay`

and always:

`persisted_forecast = false`

Real anchor audit passed `8/8` target-attendance invariance.

At 9/9 exact order is:

1. read fresh readiness;
2. explicit `p7-long168-executor-v1` dispatch with `mode=execute`;
3. freeze exact event/as-of/snapshot/bucket identities;
4. persist SHA;
5. verify T-7 replay package;
6. only then join labels;
7. strict forward folds;
8. fixed candidate tournament;
9. paired event-block uncertainty;
10. research decision only;
11. production unchanged.

## Evidence operations

Operational pipelines are already active:

- Long72 forecast-before-label hourly;
- outcome-history sync hourly;
- completed-event scoring in Long72 prospective cycle;
- schedule-as-known every 6h;
- fixture-context sidecar every 15m;
- next-opponent sidecar every 15m.

Do not add another tuning loop merely because P4a/P7 are waiting for data.

## Hard boundaries

Never:

- call inspected historical holdouts unseen;
- use future context at an earlier cutoff;
- reconstruct missing schedule/opponent state;
- mutate frozen Long72/final24 packages;
- open P4a labels before its target-free freeze;
- change the P4a 9/3 gate after seeing outcomes;
- open P7 model results before identity freeze;
- lower the P7 nine-event gate;
- random-split live snapshots as headline evidence;
- promote from historical uplift alone.

## One-line instruction

> **P4a and P7 are both precommitted and data-bound. P4a is 5 READY / 0 labeled with a frozen 9-label + 3-value gate; P7 is 8/9. Do not invent more tuning while these gates are closed.**
