# Pre-Live v3 — Fixed-Temporal Package Audit v1 — Result

Date: **2026-10-21**

Status: **COMPLETED / V3_FIXED_PACKAGE_PASS / NO PRODUCTION CHANGE**

Canonical contract:

`ml/PRE_LIVE_V3_FIXED_TEMPORAL_PACKAGE_V1.md`

Parent result:

`ml/results/PRE_LIVE_V3_REGIME_REVALIDATION_V1_2026-10-21.md`

Workflow run:

`39628607689`

Job:

`119320431144`

Artifact:

`pre-live-v3-fixed-temporal-package-v1-39628607689`

Artifact ID:

`12358477269`

Artifact ZIP SHA256:

`c190ffe229cb0eaedf65473338dad14ee83bb8768d335ce42d66ff7b3f1b8f02`

Result JSON SHA256:

`f7c665b861cbd9cc7a7d8fd859c8b97a174c65bdad8888b14dee2dc7b20ebf01`

Run merge SHA:

`60cc8dc128669aba7f4770280ae83765746abfa1`

## Protocol

No tuning or selection occurred in this audit.

Exact candidate package:

- T-30: robust historical ensemble + `NO_ADJUSTMENT`;
- T-14: exact Frozen Pre-Live v2 horizon package;
- T-7: robust historical ensemble + `ewma50-resid-k4-cap05-min2`;
- T-3: exact Frozen Pre-Live v2 horizon package;
- T-1: exact Frozen Pre-Live v2 horizon package.

Rolling folds:

1. train `2021/22` -> test `2022/23`;
2. train `2021/22 + 2022/23` -> test `2023/24`;
3. train through `2023/24` -> test `2024/25`;
4. train through `2024/25` -> test `2025/26`.

Frozen Pre-Live v2 was reproduced exactly at unchanged horizons and used as the full-package benchmark.

## Package result

Decision:

`V3_FIXED_PACKAGE_PASS`

20-cell mean MAE:

- Frozen Pre-Live v2: **1,934.04**;
- Pre-Live v3 candidate: **1,924.64**;
- improvement: **+9.39 MAE**;
- relative improvement: **+0.49%**.

Changed-horizon gate:

`PASS`

Unchanged-horizon exact reproduction gate:

`PASS`

The package is therefore eligible to become a separately versioned **historical research freeze candidate**.

This is not production promotion.

---

# T-30 — PASS 4/4

Exact v3 contract:

Historical anchor:

`0.75 current a2 + 0.25 XGBoost depth3`

Current-season regime:

`NO_ADJUSTMENT`

| Test season | Frozen v2 MAE | v3 MAE | MAE improvement |
|---|---:|---:|---:|
| 2022/23 | 2,157.15 | 2,151.17 | **+5.98** |
| 2023/24 | 2,559.74 | 2,526.25 | **+33.50** |
| 2024/25 | 1,889.37 | 1,834.43 | **+54.93** |
| 2025/26 | 1,846.28 | 1,816.54 | **+29.74** |

Summary:

- positive rolling folds: **4/4**;
- mean MAE improvement: **+31.04**;
- relative mean improvement: **+1.47%**;
- minimum paired-bootstrap P(improvement > 0): **0.6353**;
- maximum worst-event degradation across folds: **2,855.70 seats**.

Decision:

`V3_HORIZON_FIXED_TEMPORAL_PASS`

---

# T-7 — PASS 4/4

Exact v3 contract:

Historical anchor:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Current-season regime:

`ewma50-resid-k4-cap05-min2`

| Test season | Frozen v2 MAE | v3 MAE | MAE improvement |
|---|---:|---:|---:|
| 2022/23 | 1,891.86 | 1,880.94 | **+10.92** |
| 2023/24 | 2,246.57 | 2,235.39 | **+11.18** |
| 2024/25 | 1,643.82 | 1,630.11 | **+13.71** |
| 2025/26 | 1,738.98 | 1,711.10 | **+27.88** |

Summary:

- positive rolling folds: **4/4**;
- mean MAE improvement: **+15.92**;
- relative mean improvement: **+0.85%**;
- minimum paired-bootstrap P(improvement > 0): **0.6753**;
- maximum worst-event degradation across folds: **1,563.28 seats**.

Decision:

`V3_HORIZON_FIXED_TEMPORAL_PASS`

---

# T-14 / T-3 / T-1

All three horizons reproduce Frozen Pre-Live v2 exactly across all four rolling folds.

Decision per horizon:

`UNCHANGED_FROZEN_V2_REPRODUCED`

This means v3 is intentionally a **mixed-horizon package**, not an all-horizon rewrite.

## Exact Pre-Live v3 research package

### T-30

Historical:

`0.75 current a2 + 0.25 XGBoost depth3`

Regime:

`NO_ADJUSTMENT`

### T-14

Exact Frozen Pre-Live v2 T-14 package.

### T-7

Historical:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Regime:

`ewma50-resid-k4-cap05-min2`

### T-3

Exact Frozen Pre-Live v2 T-3 package.

### T-1

Exact Frozen Pre-Live v2 T-1 package.

Historical context remains:

`NO_CONTEXT_ALL_HORIZONS`

## Interpretation

The v3 gain is modest at package level because only two of five horizons change, but the two changed horizons improve Frozen v2 in all four rolling folds under an exact frozen contract.

The remaining caution is tail risk:

- T-30 worst-event degradation remains material at about 2,856 seats;
- T-7 worst-event degradation remains about 1,563 seats;
- bootstrap support is positive but not overwhelming on every fold.

Therefore the correct status is:

`FROZEN_HISTORICAL_RESEARCH_CANDIDATE_ELIGIBLE`

not production-ready.

## Next required step

Create and seal a new immutable research freeze candidate, for example:

`pre-live-v3-historical-candidate-2026-10-21-v1`

The freeze must persist:

- exact horizon contracts;
- exact expected rolling MAEs;
- input/runtime hashes;
- source-code hashes;
- parent evidence run/artifact IDs;
- `production_change = false`.

After v3 is sealed, any live-model research against it must use a **new d2 version** because the live residual target changes when the anchor changes.

Do not silently reuse frozen `ridge-a10` / P2 against v3.

## Production boundary

Always:

- Frozen Pre-Live v2 remains unchanged for Track-A prospective validation;
- current Ridge/P2 remains tied to v2;
- production remains unchanged;
- `live_adjustment = 0`.
