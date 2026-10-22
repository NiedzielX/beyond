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
- Global Model / Structural Prior family: club-history baseline + learned global residual correction.

2024/25 and 2025/26 are exposed historical research evidence for future challenger decisions.

### Frozen final24 live package

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Do not mutate it from new outcomes.

### Frozen Long72 live package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical event-balanced development:

- structural anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- improvement `694.51 / 18.73%`;
- paired event-block 95% interval for `ΔMAE`: `[-1549.89,+148.05]`;
- `P(ΔMAE<0)=0.9500`;
- structural bias `-242.63`;
- frozen P2 bias `+917.05`.

Interpretation: live inventory contains meaningful incremental information, but historical `N=13` is still uncertainty-limited and genuine prospective evidence is required.

True forecast-before-label infrastructure is operational. Manual bootstrap rows remain audit-only and excluded from the official scorecard.

## Closed research loops — do not repeat by default

### MAE-native estimator tournament

Complete. Median/L1 alternatives did not justify replacing the incumbent.

### `ΔMAE` uncertainty for estimator challengers

Complete. T-3/T-7 estimator signals were too weak/inconsistent.

### P5a structural/live convex shrinkage

Complete.

Strict forward-event MAE:

- anchor `3180.22`;
- w=.25 `2974.89`;
- w=.50 `2776.51`;
- w=.75 `2614.46`;
- frozen P2 / w=1.00 `2472.30`;
- train-selected weight `2564.22`.

Decision: **retain full frozen P2; no shrinkage replacement.**

Do not trade away MAE solely to reduce bias. Bias remains a guardrail, not the primary objective.

## Temporal validation contract — operational

Use:

`ml/temporal_validation_v1.py`

It provides:

- strict forward-event folds;
- strict expanding-group/season folds;
- `train_end < test_start` assertions;
- deterministic fold manifests / SHA;
- MAE, median AE, P90 AE, bias, RMSE;
- event-balanced MAE.

No new challenger should invent an ad-hoc random split when this contract applies.

## P4 fixture context — operational evidence collection

Forward schedule-as-known infrastructure:

- `private.fixture_schedule_batches_v1`;
- `private.fixture_schedule_rows_v1`;
- `public.capture_fixture_schedule_as_known_v1(...)`;
- PIT lookup via `public.fixture_context_as_known_v1(...)` and ticket-event adapter.

First genuine schedule capture:

`2026-10-21 20:21:39.668518+00`

Anything before that has no recorded schedule-version state. Never reconstruct those timestamps from today's final schedule.

Current P4 feature family:

- previous home match distance;
- next home match distance when known;
- team fixture density next 7/14/30d;
- home fixture density next 7/14/30d;
- previous/next home opponent identities for later observed attractiveness joins.

Long72 sidecar:

- `private.d2_long72_fixture_context_v1`;
- `public.capture_d2_long72_fixture_context_v1(...)`;
- automatic catch-up every 15 minutes;
- append-only;
- initial state: `12` forecast rows processed, `10 READY`, `2 NO_SCHEDULE_STATE_AS_OF`.

This sidecar changes no prediction. It exists to make later context ablation genuinely PIT-safe.

## Two lanes — always parallel

### Lane A — evidence

Continue automatically:

- final24 prospective scoring;
- hourly Long72 pre-outcome materialization;
- immutable forecast persistence;
- append-only outcome scoring;
- schedule-as-known capture;
- Long72 fixture-context sidecar capture.

### Lane B — MAE R&D

Current priority order:

1. keep P4 forward context evidence accumulating;
2. add next-opponent attractiveness only from a source actually observed by the forecast cutoff;
3. run P4 controlled context ablations when enough labeled rows/events exist;
4. then test P5 `structural + context + live` combinations;
5. start 72–168h learned research at the predeclared `N>=9` independent-event floor;
6. club calibration/shrinkage only if it improves forward generalization.

Current Long168 readiness at last audit:

- `8/9` independent events >72h;
- `110` rows >72h.

Do not lower this threshold.

## Hard boundaries

Never:

- use random snapshot splits as headline evidence;
- train an earlier forecast with future-season/event information;
- call inspected historical holdouts unseen;
- use realized future context at an earlier PIT cutoff;
- recompute old schedule context from a later final schedule and call it PIT-safe;
- retune frozen packages under the same ID;
- learn ensemble weights on the evaluation fold;
- promote from historical uplift alone;
- stop R&D because prospective evidence is still accumulating.

## Production boundary

Production remains unchanged unless explicitly reviewed and activated:

`live_adjustment = 0`

## One-line instruction

> **Estimator tuning and simple structural/live shrinkage are closed. Keep P4 forward context evidence collecting beside Long72; the next meaningful combination is structural + genuinely PIT-safe context + live. Trigger Long168 only at 9 independent >72h events.**
