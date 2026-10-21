# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-21**

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
- Global Model v2.1 residual architecture: club-history baseline + learned global residual correction.

2024/25 and 2025/26 are exposed historical research evidence for future challenger decisions.

### Frozen final24 live package

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Do not mutate it from new outcomes.

### Frozen long72 live package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical development:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- uplift `+694.51 / +18.73%`.

True forecast-before-label infrastructure is now operational.

Result:

`ml/results/D2_LONG72_FORWARD_PROSPECTIVE_V1_2026-10-21.md`

First reproducible pre-outcome evidence exists for events 10 and 16. No prospective MAE exists yet because outcomes are not available.

Manual bootstrap rows remain auditable but are excluded from the official scorecard; only reproducible pipeline rows are scoreable.

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

## Two lanes — always parallel

### Lane A — evidence

Continue automatically:

- final24 prospective scoring;
- hourly long72 pre-outcome materialization;
- immutable forecast persistence;
- append-only outcome scoring when attendance becomes available.

### Lane B — MAE R&D

Current priority order:

1. **MAE-native challenger tournament using `temporal_validation_v1`**;
2. event/fixture-block uncertainty for `ΔMAE`;
3. PIT-safe next-home-fixture substitution/cannibalization;
4. forecast combinations;
5. live-ticket residual uplift over the strongest structural/global forecast;
6. 72–168h learned experiment at `N>=9`;
7. club shrinkage/calibration only if it improves global generalization.

## Important MAE framing

Do not claim the current Global v2.1 champion is squared-error-only.

Current incumbents already use MAE-aligned objectives:

- HistGradientBoosting: `loss="absolute_error"`;
- XGBoost: `objective="reg:absoluteerror"`.

The next tournament must therefore test genuinely different L1/median estimators rather than merely rename the same loss:

- `QuantileRegressor(q=0.50)` / regularized linear median;
- other compact robust median residual challengers;
- current HistGBR/XGB absolute-error models as controls.

## Hard boundaries

Never:

- use random snapshot splits as headline evidence;
- train an earlier forecast with future-season/event information;
- call inspected historical holdouts unseen;
- use realized future context at an earlier PIT cutoff;
- retune frozen packages under the same ID;
- learn ensemble weights on the evaluation fold;
- promote from historical uplift alone;
- stop R&D because prospective evidence is still accumulating.

## Production boundary

Production remains unchanged unless explicitly reviewed and activated:

`live_adjustment = 0`

## One-line instruction

> **Long72 prospective evidence and temporal validation are operational. Continue immediately with the MAE-native challenger tournament; evidence collection remains automatic in parallel.**
