# Pre-Live v3 — Historical Research Freeze v1

Last updated: **2026-10-21**

Status: **ACTIVE SEALING GATE / RESEARCH ONLY**

Parent evidence:

- `ml/results/PRE_LIVE_V3_REGIME_REVALIDATION_V1_2026-10-21.md`;
- `ml/results/PRE_LIVE_V3_FIXED_TEMPORAL_PACKAGE_V1_2026-10-21.md`.

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

## Purpose

Seal the exact fixed Pre-Live v3 mixed-horizon package after it passed the package-level 4-fold audit.

No tuning, selection, weight changes, regime changes or horizon changes are permitted in this gate.

## Exact contract

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

## Expected rolling MAE — hard gate

| Horizon | 2022/23 | 2023/24 | 2024/25 | 2025/26 |
|---|---:|---:|---:|---:|
| T-30 | 2151.170512301 | 2526.245203472 | 1834.434818304 | 1816.541318063 |
| T-14 | 1986.701536006 | 2339.950499328 | 1748.497051251 | 1870.393553818 |
| T-7 | 1880.936411763 | 2235.391355368 | 1630.112559463 | 1711.095982769 |
| T-3 | 1826.950300928 | 2190.790001468 | 1611.374341514 | 1753.891494223 |
| T-1 | 1794.257779854 | 2261.110393082 | 1627.074638912 | 1695.960636965 |

Raw reproduction tolerance:

`1e-9`

Manifest metrics are canonicalized to 9 decimal places after exact reproduction assertions.

## Manifest requirements

Persist:

- freeze ID/status;
- exact horizon contracts;
- all 20 expected and reproduced MAEs;
- historical runtime hash;
- input manifest hash;
- source-code SHA256 hashes;
- evidence SHA256 hashes;
- pinned dependency versions;
- dataset/feature contract metadata;
- explicit limitations;
- next workstream.

## Status semantics

Successful seal status:

`FROZEN_HISTORICAL_RESEARCH_CANDIDATE`

This does not mean:

- production promotion;
- replacement of Track-A Frozen Pre-Live v2;
- permission to reuse frozen v2 d2 Ridge/P2 against v3.

## Next workstream after successful seal

`d2-v3 — rebuild/revalidate live updater against frozen Pre-Live v3 research anchor`

That work must receive a new d2 version/contract.

## Production boundary

Always:

- Track-A Frozen Pre-Live v2 unchanged;
- Track-A frozen Ridge/P2 unchanged;
- production unchanged;
- `live_adjustment = 0`.
