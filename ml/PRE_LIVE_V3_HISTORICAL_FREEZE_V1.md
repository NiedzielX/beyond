# Pre-Live v3 — Historical Research Freeze v1

Last updated: **2026-10-21**

Status: **COMPLETED — FROZEN_HISTORICAL_RESEARCH_CANDIDATE**

Canonical result:

`ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`

Canonical manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Workflow run:

`39633561065`

Artifact ID:

`12360033160`

Artifact ZIP SHA256:

`be2a29b7fa95bacbf738ab7622740a908347dd514fe2cc6a99522fb74f2719cc`

## Exact frozen research contract

### T-30

Historical anchor:

`0.75 current a2 + 0.25 XGBoost depth3`

Current-season regime:

`NO_ADJUSTMENT`

Historical context:

`NO_CONTEXT`

### T-14

Exact Frozen Pre-Live v2 T-14 package.

### T-7

Historical anchor:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Current-season regime:

`ewma50-resid-k4-cap05-min2`

Historical context:

`NO_CONTEXT`

### T-3

Exact Frozen Pre-Live v2 T-3 package.

### T-1

Exact Frozen Pre-Live v2 T-1 package.

## Sealed rolling MAE

| Horizon | 2022/23 | 2023/24 | 2024/25 | 2025/26 |
|---|---:|---:|---:|---:|
| T-30 | 2151.170512301 | 2526.245203472 | 1834.434818304 | 1816.541318063 |
| T-14 | 1986.701536006 | 2339.950499328 | 1748.497051251 | 1870.393553818 |
| T-7 | 1880.936411763 | 2235.391355368 | 1630.112559463 | 1711.095982769 |
| T-3 | 1826.950300928 | 2190.790001468 | 1611.374341514 | 1753.891494223 |
| T-1 | 1794.257779854 | 2261.110393082 | 1627.074638912 | 1695.960636965 |

Seal gate:

- exact reproduction tolerance `1e-9`;
- no selection performed;
- source/evidence hashes persisted;
- pinned runtime persisted;
- manifest committed in-repo.

## Status semantics

`FROZEN_HISTORICAL_RESEARCH_CANDIDATE` means the v3 historical/pre-live package is immutable and may be used as a research anchor for the next live-model cycle.

It does **not** mean:

- production promotion;
- replacement of the Track-A Frozen Pre-Live v2 anchor;
- permission to reuse frozen v2 d2 Ridge/P2 against v3.

## Next workstream

`d2-v3 — rebuild/revalidate live updater against pre-live-v3-historical-candidate-2026-10-21-v1`

That work must receive a new d2 version/contract because the live residual target changes with the anchor.

## Production boundary

Always:

- Track-A Frozen Pre-Live v2 unchanged;
- Track-A frozen Ridge/P2 unchanged;
- production unchanged;
- `live_adjustment = 0`.
