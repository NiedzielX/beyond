# Pre-Live v2 Historical Freeze v1 — Result 2026-10-18

Status: **FROZEN HISTORICAL CANDIDATE / SEALED / NO PRODUCTION CHANGE**

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

## Canonical seal evidence

GitHub Actions run: `39166115174`  
Tested head: `ed5c528916c3dd2eed6037beafac9428a0421247`  
Artifact: `pre-live-v2-historical-freeze-v1-39166115174`  
Artifact ID: `12150457295`  
Artifact ZIP SHA256: `c2b7440ae84a96c474992ecbb07c4bb43f319a9e021fc370a82f439b6edd5dd1`  
Canonical manifest SHA256: `44c911d1ac8b1bf6870ed31e1a636b9b8374d8c8da2d57ba3b4fb5b4aaba4d3c`

Committed manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

CI gates:

- pinned runtime: PASS;
- compile: PASS;
- unit tests: **5/5 PASS**;
- frozen historical input SHA: PASS;
- exact reproduction of **20/20 horizon-season MAE cells** at tolerance `1e-9`: PASS;
- freshly generated manifest vs committed manifest, byte-for-byte `cmp`: PASS;
- canonical manifest SHA lock: PASS;
- artifact upload: PASS.

## Frozen historical contract

| Horizon | Historical base | Current-season regime | Historical c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,691.40** |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | **1,682.63** |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,661.52** |

Reference mean = mean MAE across exposed 2024/25 and 2025/26 historical reference seasons.

## Exact four-fold MAE

| Horizon | 2022/23 | 2023/24 | 2024/25 | 2025/26 |
|---|---:|---:|---:|---:|
| T-30 | 2,157.15 | 2,559.74 | 1,889.37 | 1,846.28 |
| T-14 | 1,986.70 | 2,339.95 | 1,748.50 | 1,870.39 |
| T-7 | 1,891.86 | 2,246.57 | 1,643.82 | 1,738.98 |
| T-3 | 1,826.95 | 2,190.79 | 1,611.37 | 1,753.89 |
| T-1 | 1,794.26 | 2,261.11 | 1,627.07 | 1,695.96 |

The canonical JSON contains exact full-precision values and is authoritative over rounded values in this document.

## Lineage frozen into the manifest

Input:

- 1,530 matches;
- 7,650 PIT feature rows;
- feature contract `structural-prior-pit-v1+verified-capacity-v1`;
- historical runtime SHA256 `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

The manifest also hashes the source files defining:

- Structural Prior runtime;
- T-7 historical candidate fitter;
- b2 regime logic;
- b2 fixed temporal audit;
- PIT feature-store builder;
- canonical a2/b2/c2 evidence documents.

A later source/evidence drift therefore cannot silently remain the same frozen candidate.

## Historical c2 decision

Historical c2 is frozen as:

`NO_CONTEXT_ALL_HORIZONS`

This follows the negative Context Extension v2 tournament. It does not disable prospective context research.

Rivalry, verified absences, media/hype and other forward-only context remain prospective/shadow because complete historical PIT truth does not exist and must not be reconstructed with future knowledge.

## Limitations

This freeze does not erase known limitations:

- 2024/25 and 2025/26 are exposed historical references, not fresh prospective validation;
- b2 has positive aggregate MAE but non-trivial event tail risk and club heterogeneity;
- forward-only context is not part of the retrospective historical stack;
- the freeze is a candidate lineage boundary, not a production promotion.

## Production boundary

Production remains unchanged:

`live_adjustment = 0`

`production_promotion = false`

No production model/runtime artifact is replaced by this freeze.

## Decision

> **Historical Pre-Live v2 candidate development is frozen. Do not continue a2/b2/c2 retuning against the same exposed historical seasons. Start d2 live-model development against this immutable Pre-Live v2 candidate contract.**

Next workstream:

`d2_continuous_live_updater_against_frozen_pre_live_v2`
