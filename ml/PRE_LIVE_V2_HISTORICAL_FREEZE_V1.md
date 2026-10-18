# Beyond Ticketing — Pre-Live v2 Historical Freeze v1

Last updated: **2026-10-18**

Status: **ACTIVE FREEZE GATE / NO PRODUCTION CHANGE**

## Purpose

Freeze the exact historical Pre-Live v2 candidate stack after:

- a2 historical optimization;
- b2 current-season residual regime selection + maturity gating + fixed temporal robustness;
- c2 historical context extension testing, which found no incremental stable uplift.

This is a reproducibility boundary before d2 learned live-updater work.

## Frozen candidate contract

| Horizon | Historical base | Current-season regime | Historical c2 |
|---|---|---|---|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | `NO_ADJUSTMENT` | `NO_CONTEXT` |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | `NO_ADJUSTMENT` | `NO_CONTEXT` |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` |

Production is not changed by this freeze.

## Reproduction gate

The freeze runner must reproduce exact final MAE for all:

- 5 horizons;
- 4 rolling folds: 2022/23, 2023/24, 2024/25, 2025/26.

Total hard assertions:

**20 horizon-season cells**.

Tolerance:

`1e-9`

## Manifest contents

The generated freeze manifest records:

- freeze ID;
- exact per-horizon contract;
- exact four-fold MAE values;
- historical input SHA256;
- feature/data contract metadata;
- SHA256 of the source files that materially define the candidate;
- SHA256 of the canonical evidence documents;
- runtime versions;
- limitations;
- next workstream.

## Source-code hashes

The freeze includes hashes for:

- Structural Prior runtime;
- T-7 frozen historical estimator contract;
- b2 regime implementation;
- b2 fixed temporal audit implementation;
- PIT structural feature-store builder.

This makes later drift explicit.

## c2 boundary

Historical c2 is frozen as:

`NO_CONTEXT_ALL_HORIZONS`

This does **not** mean context has no product value.

Forward-only rivalry, absence, attention/hype and similar signals remain prospective research/shadow inputs because complete 5-season PIT history does not exist and must not be backfilled with future knowledge.

## Promotion boundary

The freeze is:

`FROZEN_HISTORICAL_CANDIDATE`

It is not:

- a production model promotion;
- fresh prospective validation;
- permission to change `live_adjustment`;
- proof that every club/event improves.

Production remains unchanged.

## Next workstream

After the manifest is persisted and verified:

**d2 — Continuous Live Updater against frozen Pre-Live v2**.

The live model must learn incremental revisions relative to this frozen Pre-Live contract rather than continuing to mutate the historical prior during live-model development.

## Files

Implementation:

`ml/pre_live_v2_historical_freeze_v1.py`

Tests:

`ml/test_pre_live_v2_historical_freeze_v1.py`

Workflow:

`.github/workflows/pre-live-v2-historical-freeze-v1.yml`
