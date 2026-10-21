# Pre-Live v3 — Fixed-Temporal Package Audit v1

Last updated: **2026-10-21**

Status: **COMPLETED — V3_FIXED_PACKAGE_PASS**

Canonical result:

`ml/results/PRE_LIVE_V3_FIXED_TEMPORAL_PACKAGE_V1_2026-10-21.md`

Workflow run:

`39628607689`

Artifact ID:

`12358477269`

Result JSON SHA256:

`f7c665b861cbd9cc7a7d8fd859c8b97a174c65bdad8888b14dee2dc7b20ebf01`

Artifact ZIP SHA256:

`c190ffe229cb0eaedf65473338dad14ee83bb8768d335ce42d66ff7b3f1b8f02`

## Objective

Audit the exact development-selected Pre-Live v3 package against full Frozen Pre-Live v2 across all four rolling seasons.

There was **no tuning or selection in this audit**.

## Exact package

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

Exact Frozen Pre-Live v2 horizon package.

## Rolling result

### T-30

MAE improvement vs Frozen v2:

`+5.98 / +33.50 / +54.93 / +29.74`

Decision:

`V3_HORIZON_FIXED_TEMPORAL_PASS`

### T-7

MAE improvement vs Frozen v2:

`+10.92 / +11.18 / +13.71 / +27.88`

Decision:

`V3_HORIZON_FIXED_TEMPORAL_PASS`

### T-14 / T-3 / T-1

All 12 unchanged horizon-season cells reproduced Frozen v2 exactly.

Decision:

`UNCHANGED_FROZEN_V2_REPRODUCED`

## Full package

20-cell mean MAE:

- Frozen Pre-Live v2: `1934.04`;
- v3 candidate: `1924.64`;
- mean improvement: `+9.39`;
- relative mean improvement: `+0.49%`.

Decision:

`V3_FIXED_PACKAGE_PASS`

The effect is modest, but both changed horizons improve Frozen v2 in all four rolling folds under a fixed contract.

## Next step

Create and seal a new immutable historical research freeze candidate:

`pre-live-v3-historical-candidate-2026-10-21-v1`

The freeze must persist exact contracts, expected rolling MAEs, runtime/input/source hashes and parent evidence lineage.

A v3 freeze remains research-only. Production and the current Track-A v2/Ridge/P2 package remain unchanged.

If live-model work proceeds against v3, it must use a new d2 version. Frozen `ridge-a10` / P2 cannot be silently reused against a changed anchor.
