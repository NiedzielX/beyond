# Pre-Live v3 — Fixed-Temporal Package Audit v1

Last updated: **2026-10-21**

Status: **ACTIVE FIXED-CONFIG PACKAGE AUDIT**

Parent result:

`ml/results/PRE_LIVE_V3_REGIME_REVALIDATION_V1_2026-10-21.md`

## Objective

Audit the exact development-selected Pre-Live v3 package against full Frozen Pre-Live v2 across all four rolling seasons.

There is **no tuning or selection in this audit**.

## Exact package under audit

### T-30 — changed

Historical anchor:

`0.75 current a2 + 0.25 XGBoost depth3`

Current-season regime:

`NO_ADJUSTMENT`

### T-7 — changed

Historical anchor:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Current-season regime:

`ewma50-resid-k4-cap05-min2`

### T-14 / T-3 / T-1 — unchanged

Use exact Frozen Pre-Live v2 horizon package.

This makes the candidate a mixed-horizon v3 package rather than an all-horizon rewrite.

## Rolling folds

1. train `2021/22` -> test `2022/23`;
2. train `2021/22 + 2022/23` -> test `2023/24`;
3. train through `2023/24` -> test `2024/25`;
4. train through `2024/25` -> test `2025/26`.

Frozen Pre-Live v2 is hard-reproduced at tolerance `1e-9` in all 20 horizon-season cells.

The T-30/T-7 exposed-reference MAEs from the parent v3 run are also hard reproduction gates.

## Metrics

For every horizon/fold persist:

- Frozen-v2 MAE / median AE / p90 AE / bias;
- v3 candidate MAE / median AE / p90 AE / bias;
- MAE improvement;
- event improvement rate;
- worst-event degradation;
- paired bootstrap P(improvement > 0) and 95% interval;
- harmful-regression counts >500 / >1000 / >2000 / >3000 seats.

Also persist full-package season and 20-cell aggregate summaries.

## Decision gates

The package passes only if:

1. T-30 improves Frozen v2 in all four rolling folds;
2. T-7 improves Frozen v2 in all four rolling folds;
3. T-14/T-3/T-1 reproduce Frozen v2 exactly;
4. package mean MAE improves Frozen v2 across the full 20-cell matrix;
5. no source/model/policy contract changed from the parent selection.

Possible decisions:

- `V3_FIXED_PACKAGE_PASS`;
- `V3_FIXED_PACKAGE_REJECT`.

A pass permits creation of a new **historical research freeze candidate**. It does not activate production and it does not move the existing v2/Ridge/P2 Track-A package.

## Production boundary

Always:

- Frozen Pre-Live v2 remains unchanged as Track-A benchmark;
- current frozen d2 remains tied to v2;
- historical c2 remains `NO_CONTEXT_ALL_HORIZONS`;
- `production_change = false`;
- production `live_adjustment = 0`.
