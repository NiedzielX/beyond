# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Then read `ml/MAE_RESEARCH_ROADMAP_V3.md`.
3. Read `ml/PROGRESS_TRACKING.md` and `ml/CURRENT_MODEL.md` for current state.
4. Read `ml/CORE_PRODUCT_STATUS.md` when product/model scope matters.
5. Read `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` for live-ticket / long72 implementation.
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

## MAE rule

Current Global v2.1 incumbents are already MAE-aligned:

- HistGradientBoosting `loss="absolute_error"`;
- XGBoost `objective="reg:absoluteerror"`.

Therefore the next tournament must test genuinely different L1/median estimators rather than pretend this is an MSE -> MAE conversion.

Current active challenger priority:

1. regularized linear median / `QuantileRegressor(q=0.50)`;
2. compact robust median residual alternatives;
3. current HistGBR/XGB absolute-error incumbents as controls;
4. select by time-respecting out-of-sample MAE.

## Current frozen packages

Do not mutate:

- final24 `v2/Ridge/P2`;
- long72 `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`;
- Pre-Live v3 research anchor.

Any material model/feature/weight/target change creates a new challenger/version.

## Long72 prospective state

True forecast-before-label evidence is operational.

- main workflow: `d2 Long72 Forward Prospective v1`;
- hourly forward-only materialization;
- immutable predictions;
- outcome-only append scoring;
- first reproducible pre-outcome events: 10 and 16;
- manual bootstrap rows retained for audit but excluded from official scorecard.

Do not reconstruct a missing forecast after attendance is known.

## Current MAE R&D priority

Continue from the first unfinished item:

1. **MAE-native residual tournament using temporal-validation-v1**;
2. event/fixture-block uncertainty for `ΔMAE`;
3. PIT-safe next-fixture/cannibalization features;
4. controlled context ablations;
5. forecast combination tournament;
6. live-ticket incremental uplift over the strongest structural/global forecast;
7. 72–168h challenger once coverage reaches `N>=9`.

## Current live runtime operational state

Live Forecast Orchestrator v1 is deployed.

Current Structural Prior runtime registry shows executable active runtimes for all five checkpoint horizons:

- T-30;
- T-14;
- T-7;
- T-3;
- T-1.

The older T-7/T-3/T-1 fail-closed bootstrap note is obsolete. Do not rebuild these runtimes during a normal modelling session unless a dedicated runtime trigger requires it.

This operational state is separate from research model selection.

## Product principle

Optimize for accurate prediction early enough for the club to act, not only the lowest T-1 error.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until explicit reviewed activation.
