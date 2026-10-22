# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-22**

## Cold-start rule

Read in this order:

1. `ml/MAE_RESEARCH_ROADMAP_V3.md`;
2. `ml/PROGRESS_TRACKING.md`;
3. `ml/CURRENT_MODEL.md`;
4. `ml/CORE_PRODUCT_STATUS.md`;
5. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
6. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
7. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`;
8. only then open detailed result/manifests needed for the current task.

Do not rebuild frozen historical benchmarks merely to recover context.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons, using honest PIT-safe and reproducible evidence.**

Model complexity is secondary. Predictive information and future MAE are primary.

## Current architecture

### Global historical / structural core

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- Structural Prior / Global Model family: club-history baseline + learned global residual correction.

2024/25 and 2025/26 are exposed historical research evidence for future challenger decisions.

### Frozen Long72 live package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical event-balanced result:

- structural anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- `18.73%` MAE improvement;
- 95% paired event-block interval for `ΔMAE`: `[-1549.89,+148.05]`;
- P2 bias `+917.05`.

Interpretation: material historical incremental live signal, but N=13 remains uncertainty-limited and genuine prospective evidence is required.

## Closed loops — do not repeat by default

- MAE-native estimator tournament: complete, no replacement.
- estimator `ΔMAE` uncertainty: complete, no replacement.
- P6 structural vs live incremental value: complete historically.
- P5a structural/live convex shrinkage: complete, retain full frozen P2.

Strict forward-event P5a MAE:

- anchor `3180.22`;
- w=.25 `2974.89`;
- w=.50 `2776.51`;
- w=.75 `2614.46`;
- frozen P2 `2472.30`;
- train-selected shrinkage `2564.22`.

Do not trade away MAE solely to reduce bias. Bias remains a guardrail, not the primary selector.

## Temporal validation contract

Use `ml/temporal_validation_v1.py`.

- strict forward-event folds for live work;
- strict expanding-season/group folds for historical/global work;
- event is the live independent unit;
- no random snapshot split as headline evidence;
- persist exact fold identities/SHA.

## P4 forward evidence infrastructure — fully operational

### P4a schedule/fixture context

Forward schedule evidence:

- `private.fixture_schedule_batches_v1`;
- `private.fixture_schedule_rows_v1`;
- `public.capture_fixture_schedule_as_known_v1(...)`.

First genuine schedule state:

`2026-10-21 20:21:39.668518+00`

PIT fixture lookup:

- `public.fixture_context_as_known_v1(...)`;
- `public.fixture_context_for_ticket_event_as_known_v1(...)`.

Long72 sidecar:

- `private.d2_long72_fixture_context_v1`;
- `public.capture_d2_long72_fixture_context_v1(...)`;
- append-only, automatic every 15 minutes.

Current checkpoint:

- 12 reproducible Long72 rows;
- 12 fixture-context sidecar rows;
- 10 READY;
- 2 pre-schedule rows fail closed as `NO_SCHEDULE_STATE_AS_OF`.

### P4b next-home opponent attractiveness

PIT lookup:

- `public.opponent_attractiveness_as_known_v1(...)`;
- `public.next_home_opponent_attractiveness_for_ticket_event_as_known_v1(...)`.

Long72 sidecar:

- `private.d2_long72_next_opponent_attractiveness_v1`;
- `public.capture_d2_long72_next_opponent_attractiveness_v1(...)`;
- append-only, automatic every 15 minutes.

READY requires:

1. next home opponent known in a schedule state observed by `as_of_at`;
2. historical attendance outcome kickoff + created/updated/confirmed all no later than `as_of_at`;
3. club history `>=8`;
4. opponent history `>=3`.

Current checkpoint:

- 12 rows processed;
- 2 fixture-context unavailable before schedule capture;
- 10 rows have no next home match in the schedule state known then;
- 0 READY attractiveness rows.

Do not fill those rows from later schedule knowledge or hand-authored scores.

## Two lanes

### Lane A — evidence

Continue automatically:

- final24 prospective scoring;
- hourly Long72 pre-outcome materialization;
- immutable forecast persistence;
- append-only outcome scoring;
- schedule-as-known capture;
- fixture-context sidecar;
- next-opponent-attractiveness sidecar.

Current genuine Long72 scored events: `0` because the active precommitted matches do not yet have final attendance.

### Lane B — MAE R&D

All currently unblocked P4 data-capture work is done.

Next sequence:

1. allow genuine P4 labeled evidence to accumulate;
2. run controlled schedule/context ablations once independent labeled events exist;
3. run P5 `structural + context + live` combinations only after a genuine context component exists;
4. trigger 72–168h learned research at the predeclared `N>=9` independent-event threshold;
5. keep club calibration/shrinkage lower priority.

Current Long168 readiness:

- `8/9` independent events >72h;
- `110` rows >72h.

Do not lower the threshold.

## Hard boundaries

Never:

- use random snapshot splits as headline evidence;
- train earlier forecasts with future event/season information;
- call inspected historical holdouts unseen;
- use realized future context at an earlier PIT cutoff;
- reconstruct old schedule context from a later final schedule and call it PIT-safe;
- reconstruct opponent attractiveness from outcomes not system-known at the forecast cutoff;
- retune frozen packages under the same ID;
- learn combination weights on the evaluation fold;
- promote from historical uplift alone.

## Production boundary

Production remains unchanged unless explicitly reviewed and activated:

`live_adjustment = 0`

## One-line instruction

> **All currently unblocked P4 evidence collection is operational and fail-closed. Do not invent missing context. Wait only where genuine labels/data are mathematically required; trigger Long168 at 9 independent >72h events and P5 context combinations only after labeled P4 evidence exists.**
