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

Never stop challenger R&D only because prospective labels are still accumulating, but do not fabricate PIT history when the necessary source state was never captured.

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

## Closed research loops

Do **not** reopen without a materially new hypothesis/data source:

1. MAE-native estimator tournament — no robust incumbent replacement.
2. Estimator `ΔMAE` uncertainty — T-3/T-7 signals insufficient.
3. Historical Long72 live incremental value — measured:
   - anchor MAE `3707.14`;
   - frozen P2 MAE `3012.63`;
   - `ΔMAE=-694.51` / `18.73%`;
   - 95% interval `[-1549.89,+148.05]`;
   - P2 bias `+917.05`.
4. Structural ↔ live convex shrinkage P5a — no replacement:
   - strict forward-event P2 MAE `2472.30`;
   - train-selected shrinkage MAE `2564.22`;
   - retain full frozen P2.

## Frozen packages

Do not mutate:

- final24 `v2/Ridge/P2`;
- Long72 `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`;
- Pre-Live v3 research anchor.

Any material model/feature/weight/target change creates a new challenger/version.

## Long72 prospective state

Operational:

- workflow `d2 Long72 Forward Prospective v1`;
- hourly forecast-before-label materialization;
- immutable predictions;
- outcome-only append scoring;
- manual bootstrap rows audit-only;
- never reconstruct a missing forecast after attendance is known.

Current checkpoint:

- 12 reproducible prediction rows;
- 0 scored genuine events because current precommitted matches have not produced final attendance yet.

## P4a schedule/fixture context — operational

Forward schedule evidence:

- `private.fixture_schedule_batches_v1`;
- `private.fixture_schedule_rows_v1`;
- `public.capture_fixture_schedule_as_known_v1(...)`.

First genuine schedule state:

`2026-10-21 20:21:39.668518+00`

PIT lookup:

- `public.fixture_context_as_known_v1(...)`;
- `public.fixture_context_for_ticket_event_as_known_v1(...)`.

Long72 append-only sidecar:

- `private.d2_long72_fixture_context_v1`;
- `public.capture_d2_long72_fixture_context_v1(...)`;
- initial/current checkpoint: `12` rows, `10 READY`, `2 NO_SCHEDULE_STATE_AS_OF`.

Never backfill today's final schedule into timestamps before it was observed.

## P4b next-home opponent attractiveness — operational

PIT lookup:

- `public.opponent_attractiveness_as_known_v1(...)`;
- `public.next_home_opponent_attractiveness_for_ticket_event_as_known_v1(...)`.

Long72 append-only sidecar:

- `private.d2_long72_next_opponent_attractiveness_v1`;
- `public.capture_d2_long72_next_opponent_attractiveness_v1(...)`.

A READY score requires:

1. next home opponent present in schedule state known by the forecast cutoff;
2. historical outcome kickoff + created/updated/confirmed timestamps all known by the same cutoff;
3. club history `>=8`;
4. opponent history `>=3`.

Current checkpoint:

- 12 rows processed;
- 2 `FIXTURE_CONTEXT_NO_SCHEDULE_STATE_AS_OF`;
- 10 `NO_NEXT_HOME_MATCH_IN_SCHEDULE_STATE`;
- 0 READY.

This is correct fail-closed behavior. Never substitute later schedule knowledge or hand-authored opponent attractiveness.

## Current MAE R&D priority

All currently unblocked P4 capture infrastructure is done.

Continue with:

1. keep Long72 forecasts + both P4 sidecars collecting automatically;
2. monitor for genuinely READY next-opponent rows and final attendance labels;
3. once enough labeled P4 events exist, run controlled context ablations;
4. then run P5 `structural + context + live` combinations;
5. keep final24/Long72 prospective scoring active;
6. start 72–168h research immediately when independent >72h coverage reaches `N>=9`;
7. keep club calibration/shrinkage lower priority.

Current Long168 readiness:

- `8/9` independent events >72h;
- `110` rows >72h.

Do not lower the threshold.

## Live runtime operational state

Live Forecast Orchestrator v1 is deployed.

Structural Prior runtime registry has executable active runtimes for T-30/T-14/T-7/T-3/T-1.

Do not rebuild these during normal modelling work unless a dedicated runtime trigger requires it.

## Product principle

Optimize for accurate prediction early enough for the club to act, not only the lowest T-1 error.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until explicit reviewed activation.
