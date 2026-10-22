# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Then read `ml/MAE_RESEARCH_ROADMAP_V3.md`.
3. Read `ml/PROGRESS_TRACKING.md` and `ml/CURRENT_MODEL.md` for current state.
4. Read `ml/CORE_PRODUCT_STATUS.md` when product/model scope matters.
5. Read `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` for live-ticket / Long72 implementation.
6. Read `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md` before creating a new experiment.
7. Do **not** retrain, rebuild or reproduce frozen historical benchmarks merely to recover context.
8. For latest-state questions, prefer targeted repo/DB reads over historical recomputation.
9. Never store secrets, tokens, service-role keys or credentials in repo files.

## Core modelling principle

> **The objective is lower true out-of-sample MAE, not model complexity.**

Always separate:

- **Evidence Lane:** immutable frozen packages collecting forward evidence;
- **MAE R&D Lane:** new challenger versions developed in parallel.

Never stop challenger R&D only because prospective labels are still accumulating.

## Validation rule

Use `ml/temporal_validation_v1.py` for new challenger evaluation where applicable.

Historical/global:

- strict season/group expanding folds;
- no future-season data in earlier training folds;
- persist exact fold identities + SHA;
- no random row split as headline evidence.

Live-ticket:

- event is the independent unit;
- strict forward-event validation by kickoff;
- tied kickoff events cannot train each other;
- LOEO is diagnostic, not sufficient by itself;
- no random snapshot split as headline evidence.

## Current closed research loops

Do **not** reopen these without a new hypothesis or materially new data:

1. **MAE-native estimator tournament — closed.**
   - quantile/L1 alternatives did not justify replacing the Structural Prior incumbent.
2. **Estimator `ΔMAE` uncertainty — closed.**
   - T-3/T-7 signals were not robust enough for replacement.
3. **Historical Long72 incremental live value — measured.**
   - anchor MAE `3707.14`;
   - frozen P2 MAE `3012.63`;
   - `ΔMAE=-694.51` / `18.73%` improvement;
   - 95% event-block interval `[-1549.89,+148.05]`;
   - live/P2 bias `+917.05` seats.
4. **Structural ↔ live convex shrinkage P5a — closed.**
   - strict forward-event MAE is lowest for full frozen P2 (`w=1.00`);
   - train-selected shrinkage is `+91.92` seats worse;
   - do not shrink P2 merely to make bias look better.

## Current frozen packages

Do not mutate:

- final24 `v2/Ridge/P2`;
- Long72 `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`;
- Pre-Live v3 research anchor.

Any material model/feature/weight/target change creates a new challenger/version.

## Long72 prospective state

True forecast-before-label evidence is operational.

- main workflow: `d2 Long72 Forward Prospective v1`;
- hourly forward-only materialization;
- immutable predictions;
- outcome-only append scoring;
- manual bootstrap rows retained for audit but excluded from official scorecard;
- never reconstruct a missing forecast after attendance is known.

## P4 fixture context — active evidence lane

Forward schedule-as-known infrastructure is operational:

- `private.fixture_schedule_batches_v1`;
- `private.fixture_schedule_rows_v1`;
- `public.capture_fixture_schedule_as_known_v1(...)`;
- `public.fixture_context_as_known_v1(...)`;
- `public.fixture_context_for_ticket_event_as_known_v1(...)`.

First genuine schedule state was captured at:

`2026-10-21 20:21:39.668518+00`

Historical schedule state before that timestamp does **not** exist. Never backfill today's final schedule into older model rows and call it PIT-safe.

Long72 context sidecar is also operational:

- `private.d2_long72_fixture_context_v1`;
- `public.capture_d2_long72_fixture_context_v1(...)`;
- append-only;
- one row per reproducible Long72 prediction;
- exact schedule batch lineage;
- initial materialization: `12` rows, `10 READY`, `2 NO_SCHEDULE_STATE_AS_OF`.

The sidecar changes no forecast. It exists so future labels can support genuine P4 context ablations.

## Current MAE R&D priority

Continue from the first genuinely actionable item:

1. **keep P4 schedule/context evidence collecting automatically;**
2. add next-opponent attractiveness only from a PIT-safe observed source — do not recompute old timestamps from final outcomes;
3. once enough labeled P4 observations exist, run controlled context ablations;
4. then run P5 `structural + context + live` combinations;
5. keep Long72/final24 prospective scoring active in parallel;
6. start 72–168h learned research immediately when independent >72h coverage reaches the predeclared `N>=9` threshold;
7. keep club calibration/shrinkage lower priority unless it generalizes.

Current 72–168h readiness at last audit:

- `8/9` independent events >72h;
- `110` rows >72h.

Do not lower the threshold.

## Current live runtime operational state

Live Forecast Orchestrator v1 is deployed.

Current Structural Prior runtime registry has executable active runtimes for:

- T-30;
- T-14;
- T-7;
- T-3;
- T-1.

Do not rebuild these runtimes during a normal modelling session unless a dedicated runtime trigger requires it.

This operational state is separate from research model selection.

## Product principle

Optimize for accurate prediction early enough for the club to act, not only the lowest T-1 error.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until explicit reviewed activation.
