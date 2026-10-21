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

For new historical/global challengers:

- use season-blocked / rolling / expanding-origin views;
- no future-season data in earlier training folds;
- persist fold identities;
- no random row split as headline evidence.

For live-ticket challengers:

- event is the independent unit;
- LOEO is diagnostic, not sufficient by itself;
- add forward-event validation by kickoff;
- no random snapshot split as headline evidence.

## MAE rule

Every serious point-forecast tournament should include MAE-aligned candidates where practical:

- median/LAD;
- q=0.50 quantile regression;
- absolute-error / quantile tree boosting.

Evaluate by out-of-sample MAE, not training loss.

## Current frozen packages

Do not mutate:

- final24 `v2/Ridge/P2`;
- long72 `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`;
- Pre-Live v3 research anchor.

Any material model/feature/weight/target change creates a new challenger/version.

## Current MAE R&D priority

Continue from the first unfinished item:

1. long72 forecast-before-label persistence + append-only scoring;
2. canonical rolling/forward validation utilities;
3. MAE-native residual tournament;
4. block/event uncertainty for `ΔMAE`;
5. PIT-safe next-fixture/cannibalization features;
6. controlled context ablations;
7. forecast combination tournament;
8. live-ticket incremental uplift over the strongest structural/global forecast;
9. 72–168h challenger once coverage reaches `N>=9`.

## Product principle

Optimize for accurate prediction early enough for the club to act, not only the lowest T-1 error.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until explicit reviewed activation.
