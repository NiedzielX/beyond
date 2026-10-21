# Beyond ML Benchmark Harness

> **New session / agent:** read [`../AI_BOOTSTRAP.md`](../AI_BOOTSTRAP.md) first. Do not rerun frozen benchmarks merely to recover context.
>
> **Current model source of truth:** [`CURRENT_MODEL.md`](./CURRENT_MODEL.md).
>
> **Canonical accuracy roadmap:** [`DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](./DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md).

This directory is the evaluation and evidence gate for Beyond forecasting models.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

A challenger is not promoted because it is newer or more complex. It must improve the correct frozen benchmark under a declared temporal contract and survive the required robustness checks.

## Two-track model-development rule

### Track A — frozen validation

Keep the current Frozen Pre-Live v2 / Ridge / P2 package unchanged while accumulating delayed-label and genuine post-freeze evidence.

### Track B — active R&D

Continue model research immediately when an honest evaluation boundary exists.

**Do not wait for a prospective event-count threshold to perform historical/model research that can be evaluated now.**

> **Production promotion waits for prospective evidence. R&D does not.**

## Current historical benchmark

The active historical research benchmark is multi-club:

- five Ekstraklasa seasons: 2021/22–2025/26;
- 1,530 matches;
- 7,650 point-in-time feature snapshots;
- horizons: T-30 / T-14 / T-7 / T-3 / T-1;
- development selection season: 2023/24;
- exposed reference seasons: 2024/25 and 2025/26.

The reference seasons are no longer described as untouched after they have been opened. New experiments must label their evidence honestly.

## Latest historical R&D result

See:

- [`results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`](./results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md)
- [`results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md`](./results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md)

The bounded external-model/heterogeneous-ensemble audit is complete.

Robust historical challengers:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`;
- T-1: `0.25 HGB hist31 + 0.50 CatBoost depth4 + 0.25 LightGBM leaves15`.

Each improved MAE in all four fixed rolling folds.

This does **not** replace Frozen Pre-Live v2. The active next research cycle is a separately versioned Pre-Live v3 candidate with current-season-regime revalidation on the new anchors.

## Current frozen benchmark

Track-A source of truth remains:

- [`CURRENT_MODEL.md`](./CURRENT_MODEL.md)
- [`artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](./artifacts/pre_live_v2_historical_candidate_v1/manifest.json)
- [`LIVE_DEMAND_ENGINE_V1_PLAN.md`](./LIVE_DEMAND_ENGINE_V1_PLAN.md)
- [`D2_PROSPECTIVE_ACCUMULATION_V1.md`](./D2_PROSPECTIVE_ACCUMULATION_V1.md)

Production remains `live_adjustment = 0`.

## Re-run rule

Do not rebuild the feature store or rerun persisted experiments merely to rediscover current state.

Valid triggers include:

- intentional new challenger evaluation;
- model implementation/hyperparameter change;
- target/ensemble change;
- feature-contract change;
- historical input/hash change;
- source-data correction;
- benchmark-protocol change;
- explicit reproduction request.

## Historical benchmark v0.1 — retained for lineage

The original benchmark was Lech-only and is retained as model lineage, not as the current research state.

- Club: Lech Poznań.
- Target: final match attendance.
- Development seasons: `2022/2023`, `2023/2024`.
- Holdout seasons used at that time: `2024/2025`, `2025/2026`.
- Capacity-constrained attendance rows were excluded.
- Attendance-history features were shifted so only already completed matches were visible.
- Sporting context was pre-match only.
- A model for a test season was trained only on matches before that season started.
- CatBoost configuration was selected using development MAE only.

### v0.1 decision

CatBoost was **not promoted**. On the then-holdout 32-match set it reached MAE `5,918` vs `5,318` for the incumbent and had a much larger negative bias (`-4,867` vs `-2,338`).

That result remains historical lineage and has been superseded by the five-season Global Forecast / Structural Prior benchmark.

## Promotion criteria

A challenger should not be promoted if it improves a headline number while materially worsening MAE/WAPE, bias, temporal stability, club stability or tail risk.

For probabilistic models the gate also includes pinball loss and P10–P90 empirical coverage.

Historical robustness is not production promotion. Production requires separate genuine forward evidence and explicit reviewed activation.

## Data contract

Raw datasets are not treated as model outputs. Training and inference must use versioned, point-in-time feature contracts. Benchmark outputs belong in `ml/results/` and material experiments must persist machine-readable evidence, run/artifact IDs and hashes.
