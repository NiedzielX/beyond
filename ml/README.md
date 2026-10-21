# Beyond ML Benchmark Harness

> **New session / agent:** read [`../AI_BOOTSTRAP.md`](../AI_BOOTSTRAP.md) first. Do not rerun frozen benchmarks merely to recover context.
>
> **Current model source of truth:** [`CURRENT_MODEL.md`](./CURRENT_MODEL.md).
>
> **Canonical accuracy roadmap:** [`DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](./DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md).

This directory is the evaluation and evidence gate for Beyond forecasting models.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Two-track rule

### Track A — frozen validation

Keep Frozen Pre-Live v2 / Ridge / P2 unchanged while accumulating delayed-label and genuine post-freeze evidence.

### Track B — active R&D

Pre-Live v3 is sealed as a separate research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Do not wait for prospective sample-count gates to perform research that can be evaluated honestly now.

> **Production promotion waits for prospective evidence. R&D does not.**

## Current historical research freeze

Manifest:

[`artifacts/pre_live_v3_historical_candidate_v1/manifest.json`](./artifacts/pre_live_v3_historical_candidate_v1/manifest.json)

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Freeze result:

[`results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`](./results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md)

Exact changes vs Frozen v2:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`, no b2;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`, `ewma50-resid-k4-cap05-min2`.

T-14/T-3/T-1 are exact v2 horizon packages.

20-cell mean MAE:

`1934.04 -> 1924.64`, gain `+9.39 / +0.49%`.

T-30 and T-7 improved Frozen v2 in all four rolling folds under a fixed package.

V3 remains research-only: exposed historical references and material tail risk are explicit limitations.

## Current Track-A benchmark

Pre-Live v2:

[`artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](./artifacts/pre_live_v2_historical_candidate_v1/manifest.json)

Frozen live model:

- `ridge-a10`;
- `P2-observation-maturity`.

Production remains:

`live_adjustment = 0`

## Active next experiment — d2-v3 Stage 0

Do **not** retrain a live model simply because v3 has a new freeze ID.

V3 T-1 is exactly the same as v2 T-1, while the current d2 development problem uses final-24h live rows.

Therefore first run an exact 9-event / 30-row anchor equivalence replay:

- v2 anchor per row;
- v3 anchor per row;
- seat and occupancy delta;
- v2 residual target;
- v3 residual target.

If all rows are identical, do not create a cosmetic new Stage-1 model version. Move to a materially different live hypothesis instead.

If they differ, create a new d2-v3 target and rerun event-level LOEO expert/reliability selection under new IDs.

## Historical data contract

Current historical research dataset:

- 5 Ekstraklasa seasons: 2021/22–2025/26;
- 1,530 matches;
- 7,650 point-in-time horizon rows;
- T-30 / T-14 / T-7 / T-3 / T-1;
- exposed references 2024/25 and 2025/26 must always remain labeled exposed.

## Re-run rule

Do not rerun persisted evidence merely to recover context.

Valid triggers include:

- intentional new challenger;
- target/model/ensemble/policy change;
- feature/source semantics change;
- historical data/hash correction;
- benchmark protocol change;
- explicit reproduction request.

## Engineering contract

`code -> tests -> CI -> artifact -> hashes -> result doc -> decision -> canonical docs`

A material change creates a new challenger/version.

Historical/LOEO improvement is not production promotion.
