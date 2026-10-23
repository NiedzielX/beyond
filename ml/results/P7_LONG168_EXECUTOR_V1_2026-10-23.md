# P7 Long168 Executor v1 — 2026-10-23

## Status

**EXECUTION PIPELINE IMPLEMENTED / REAL TOURNAMENT STILL BLOCKED AT 8 OF 9**

No real P7 challenger result was opened while implementing this executor.

Current live gate at implementation time:

- independent events with valid rows >72h: `8/9`;
- valid rows >72h: `110`;
- genuine Long72 scored events: `0`;
- next-opponent READY rows: `0`.

Production remains unchanged:

`live_adjustment = 0`

## Why an additional executor layer was needed

The precommit harness already froze the P7 scientific contract, but one execution gap remained:

> historical Long168 events do not have persisted T-7 forecasts in `private.structural_prior_forecasts_v1`.

Using `public.get_structural_prior_v1(...)` for those historical events returns no persisted prior. Silently inventing a stored forecast or substituting a later checkpoint would violate the PIT contract.

P7 therefore uses an explicit historical replay path for the anchor.

## T-7 anchor replay

Canonical module:

`ml/p7_long168_anchor_replay_v1.py`

The replay:

- uses the frozen Structural Prior Runtime v1 artifact family;
- uses the frozen T-7 model artifact only as the P7 control checkpoint;
- reconstructs structural inputs at exactly `kickoff - 7 days`;
- uses only historical attendance with kickoff strictly before the T-7 cutoff;
- uses sporting results from fixtures strictly before the cutoff date;
- strips `actual_attendance` from target event metadata before replay;
- requires T-7 cutoff to be no later than every eligible Long168 live observation;
- checks anchor range against verified stadium capacity.

Evidence classification is explicitly:

`historical_pit_replay`

and:

`persisted_forecast = false`

The replay must never be described as a genuinely persisted/prospective forecast.

## Frozen artifact gates

Expected T-7 artifact SHA256:

`97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`

Expected historical runtime SHA256:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

The live audit checks both manifest lineage and the actual repository file bytes before replay.

## Target-attendance invariance gate

For every current target event, the audit mutates that event's exact-kickoff attendance row to an impossible sentinel value:

`999,999,999`

The replayed T-7 P50 must remain unchanged within `1e-9`.

This proves the target event's final attendance is excluded by the T-7 cutoff rather than merely being ignored by convention.

The live workflow requires:

- every P7 event has an exact target attendance row for the invariance test;
- every event passes the mutation test;
- no event may be silently skipped.

## Tournament executor

Canonical module:

`ml/p7_long168_tournament_v1.py`

Mandatory runtime order:

1. reproduce the supplied P7 freeze manifest from the current Long168 source;
2. require exact manifest SHA and exact frozen identities;
3. validate anchor package, evidence class and exact event set;
4. only after those checks read actual attendance labels;
5. build the frozen feature frame;
6. build strict forward-event folds;
7. fit only the precommitted candidates;
8. score event-balanced MAE and guardrails;
9. run paired event-block bootstrap uncertainty;
10. emit a research-only decision.

## Fixed candidates

- `anchor-only-t7`;
- `q50-linear-residual-a002`;
- `gbr-l1-depth2-n50-lr003`.

No model search or parameter tuning is performed by the executor.

## Training discipline

For learned residual candidates:

`target = actual_attendance - T7_anchor`

Training row weights are:

`1 / rows_for_training_event`

and normalized only by a common constant.

Therefore every training event contributes equal total weight regardless of trajectory coverage.

## Validation

Uses:

`ml/temporal_validation_v1.py::build_forward_event_folds`

with:

- minimum five strictly earlier train events;
- one held-out event per forward fold;
- tied kickoff events unable to train each other;
- `train_end < test_start`;
- exact fold manifest SHA persisted.

At exactly nine eligible chronological events this normally produces four held-out forward events, subject to kickoff ties.

## Metrics and uncertainty

Primary:

- strict-forward event-balanced MAE.

Required diagnostics:

- event-balanced bias;
- event median AE;
- event P90 AE;
- event improvement rate;
- forward-fold improvement rate;
- worst-event degradation;
- 72–96 / 96–120 / 120–144 / 144–168h band metrics.

Uncertainty:

- paired event-block percentile bootstrap;
- 5,000 draws;
- seed 42.

## Decision contract

The best learned candidate advances only when:

- strict-forward event-balanced MAE is below anchor;
- event improvement rate is >50%;
- forward-fold improvement rate is >50%;
- all freeze / anchor / PIT / reproducibility gates pass.

Otherwise:

`RETAIN_ANCHOR`

Bootstrap evidence is always reported but does not by itself override the precommitted majority-event / majority-fold rule.

## Workflow behavior

Workflow:

`.github/workflows/p7-long168-executor-v1.yml`

Automatic push to `main`:

- validates code;
- verifies real frozen artifact bytes;
- fetches Long168 + C1 support exports through the main-only OIDC gateway;
- runs **anchor audit only**;
- fits no P7 challenger.

Real tournament:

- requires explicit `workflow_dispatch` with `mode=execute`;
- starts by running `freeze`;
- fails closed while the research gate is below `9`;
- writes freeze, anchor, predictions, fold manifest and scorecard artifacts.

This prevents the ninth event from automatically opening model results before a deliberate execution action.

## Current decision

**DO NOT EXECUTE THE REAL P7 TOURNAMENT YET.**

At 8/9, only the anchor audit is allowed.

When readiness reaches 9/9:

`freeze -> verified T7 replay -> labels -> forward folds -> fixed tournament -> bootstrap -> research decision`

No production activation is permitted from P7 v1 alone.
