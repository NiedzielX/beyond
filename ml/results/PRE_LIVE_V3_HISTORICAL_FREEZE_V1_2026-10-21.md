# Pre-Live v3 — Historical Research Freeze v1 — Result

Date: **2026-10-21**

Status: **FROZEN_HISTORICAL_RESEARCH_CANDIDATE / NO TRACK-A OR PRODUCTION CHANGE**

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Canonical manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Workflow run:

`39633561065`

Job:

`119337884636`

Artifact:

`pre-live-v3-historical-freeze-v1-39633561065`

Artifact ID:

`12360033160`

Artifact ZIP SHA256:

`be2a29b7fa95bacbf738ab7622740a908347dd514fe2cc6a99522fb74f2719cc`

The workflow requested 365-day artifact retention, but the repository maximum reduced it to 90 days. The exact manifest is committed in-repo, so canonical lineage does not depend on Actions retention.

## Seal gates

Passed:

- pinned runtime install;
- compile checks;
- freeze unit checks;
- exact 20-cell MAE reproduction;
- source/evidence hash generation;
- manifest hash generation;
- artifact upload.

Raw reproduction tolerance:

`1e-9`

Manifest floating metrics:

`9 decimal places`

Selection performed during seal:

`false`

## Exact frozen research contract

### T-30

Historical:

`0.75 current a2 + 0.25 XGBoost depth3`

Regime:

`NO_ADJUSTMENT`

Reference mean MAE:

**1,825.49**

### T-14

Exact Frozen-v2 horizon contract:

- Structural Prior historical base;
- `NO_ADJUSTMENT`.

Reference mean MAE:

**1,809.45**

### T-7

Historical:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Regime:

`ewma50-resid-k4-cap05-min2`

Reference mean MAE:

**1,670.60**

### T-3

Exact Frozen-v2 horizon contract:

- Structural Prior historical base;
- `ewma50-resid-k2-cap05-min3`.

Reference mean MAE:

**1,682.63**

### T-1

Exact Frozen-v2 horizon contract:

- Structural Prior historical base;
- `ewma50-resid-k6-cap05-min3`.

Reference mean MAE:

**1,661.52**

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

## Rolling MAE matrix

| Horizon | 2022/23 | 2023/24 | 2024/25 | 2025/26 |
|---|---:|---:|---:|---:|
| T-30 | 2,151.17 | 2,526.25 | 1,834.43 | 1,816.54 |
| T-14 | 1,986.70 | 2,339.95 | 1,748.50 | 1,870.39 |
| T-7 | 1,880.94 | 2,235.39 | 1,630.11 | 1,711.10 |
| T-3 | 1,826.95 | 2,190.79 | 1,611.37 | 1,753.89 |
| T-1 | 1,794.26 | 2,261.11 | 1,627.07 | 1,695.96 |

Parent fixed-package evidence showed:

- T-30 positive MAE gain vs Frozen v2 in 4/4 folds;
- T-7 positive MAE gain vs Frozen v2 in 4/4 folds;
- T-14/T-3/T-1 exact Frozen-v2 reproduction;
- 20-cell mean MAE `1934.04 -> 1924.64`, improvement `+9.39 / +0.49%`.

## Input lineage

Historical runtime:

`ml/artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz`

Historical runtime SHA256:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

Input manifest SHA256:

`251f377b9791209e380d287d37c28dd8f93e0973f17bfa3912e6c3b930378ba5`

Feature contract:

`structural-prior-pit-v1+verified-capacity-v1`

Data:

- 1,530 matches;
- 7,650 horizon rows;
- seasons 2021/22–2025/26.

## Runtime

- NumPy `2.3.5`;
- pandas `2.2.3`;
- scikit-learn `1.8.0`;
- joblib `1.5.3`;
- CatBoost `1.2.10`;
- LightGBM `4.7.0`;
- XGBoost `3.4.1`.

## Limitations

- 2024/25 and 2025/26 are exposed historical references, not new prospective evidence;
- package-level gain is modest because only T-30/T-7 change;
- T-30 and T-7 retain material event-level tail degradations;
- historical context remains no-context;
- this freeze does not replace the Track-A v2/Ridge/P2 stack;
- this freeze is not production promotion.

## Decision

Pre-Live v3 is now a sealed immutable **historical research candidate**.

It is valid as the anchor for a new live-model research workstream, but frozen v2 remains the current Track-A prospective-validation anchor.

## Next workstream

`d2-v3 — rebuild/revalidate the live updater against pre-live-v3-historical-candidate-2026-10-21-v1`

The current v2 `ridge-a10` / P2 package cannot be silently reused because its target is defined against the old Pre-Live v2 anchor.

A new d2-v3 cycle must rebuild the anchor replay and residual targets against v3 under a new model/version ID.

## Production boundary

Always:

- Track-A Frozen Pre-Live v2 unchanged;
- Track-A frozen Ridge/P2 unchanged;
- production unchanged;
- `live_adjustment = 0`.
