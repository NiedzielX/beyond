# Beyond Ticketing — d2 Live Replay Anchor v1

Last updated: **2026-10-18**

Status: **ACTIVE STAGE 0 / LINEAGE & REPLAY ONLY / NO LEARNED D2 MODEL / NO PRODUCTION CHANGE**

## Purpose

Before training d2, replace the legacy C1 Structural Prior anchor with the exact frozen historical Pre-Live v2 candidate while preserving the existing C1 live-data and LOEO lineage.

Stage 0 asks one question:

> **Can the existing frozen C1 v8 nine-event / 30-row final-24h replay be expressed exactly against freeze ID `pre-live-v2-historical-candidate-2026-10-18-v1` without creating a second live dataset or leaking future information?**

No learned d2 model is fitted in this stage.

## Existing live contract reused unchanged

Source package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Source training contract:

`ml/artifacts/c1_shadow_v8/training_contract_v1.json`

Expected:

- events: `1,3,4,8,9,12,13,14,17`;
- independent events: **9**;
- regularized final-24h rows: **30**;
- cadence: latest PIT-valid snapshot per event x 6h bucket;
- event-balanced / LOEO semantics remain available for later d2 modelling.

Stage 0 hard-fails if the event x as-of row identity differs from the committed C1 contract.

## Why the anchor must change

Current C1 `_event_prior_replay()` reconstructs the old production Structural Prior checkpoints.

For final-24h C1 rows, the selected prior is T-1.

Frozen Pre-Live v2 T-1 uses the same historical base model:

`structural-prior-runtime-v1-t1-hist-full`

but adds frozen b2:

`ewma50-resid-k6-cap05-min3`

Therefore d2 must not relabel the legacy C1 prior as frozen v2. Stage 0 explicitly reconstructs the b2 state and records both:

- `legacy_prior_p50`;
- `frozen_v2_p50`.

## Frozen lineage

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

Expected manifest SHA256:

`44c911d1ac8b1bf6870ed31e1a636b9b8374d8c8da2d57ba3b4fb5b4aaba4d3c`

Stage 0 refuses to run if the freeze lineage changes.

## Same-season b2 reconstruction

The existing C1 exporter already supplies:

- all completed tracked Ekstraklasa events;
- `ml_home_attendance_history_v2` rows for the complete 2026/27 season-to-date;
- sporting league matches for 2026/27;
- club aliases;
- the regularized final-24h live rows.

For each relevant current-season home attendance row, Stage 0 reconstructs a synthetic current event by joining:

- exact attendance kickoff;
- local match date;
- canonical home club key;
- latest consistent sporting row for opponent + round;
- audited same-season home capacity.

It then reuses the existing Structural Prior replay code to calculate the T-1 base prediction for every earlier home match.

The frozen T-1 b2 state is then recreated with the canonical implementation:

- residual fraction: `(actual - base_t1) / capacity`;
- EWMA alpha: `0.50`;
- shrink `k=6`;
- correction cap: `+/-5% capacity`;
- activation only at `3+` earlier completed same-season home matches;
- completion semantics inherited from canonical b2: prior match state becomes available only after kickoff + 3h.

## Capacity lineage

The old C1 attendance export does not include historical capacity per row.

For the existing nine-event dataset only, a read-only Supabase audit on 2026-10-18 verified that each of the seven home clubs has exactly one non-null registry capacity across its current-season attendance rows.

Committed audit:

`ml/artifacts/d2_stage0_capacity_audit_v1.json`

Audited capacities:

- Cracovia: 15,016 — verified;
- GKS Katowice: 15,048 — verified;
- Jagiellonia: 22,372 — verified;
- Lech: 43,269 — verified;
- Legia: 31,006 — **carry_forward**;
- Pogoń Szczecin: 21,163 — verified;
- Śląsk Wrocław: 43,708 — verified.

This is intentionally scoped to the current frozen C1 nine-event set.

A future d2 event outside this audit must not silently inherit this capacity assumption. It needs a new audited lineage/export version.

## Existing nine-event maturity state

Read-only audit found earlier home-attendance rows before each target T-1 cutoff:

- event 1 Lech–Raków: 3;
- event 3 Lech–Jagiellonia: 2;
- event 4 Lech–Radomiak: 4;
- event 8 Jagiellonia–Górnik: 4;
- event 9 Pogoń–Korona: 5;
- event 12 Cracovia–Zagłębie: 4;
- event 13 Śląsk–Lech: 3;
- event 14 GKS Katowice–Wieczysta: 3;
- event 17 Legia–Wisła Kraków: 4.

Therefore event 3 must remain exactly at the legacy T-1 base because the frozen min3 b2 layer is not mature yet. The other eight are eligible for the b2 regime layer, subject to their reconstructed residual signal.

## Base reproduction gate

For every one of the nine target events:

1. replay the legacy C1 T-1 prior using the existing C1 path;
2. independently replay the same target T-1 base through the expanded current-season attendance event set;
3. hard-assert exact equality at tolerance `1e-9`;
4. only then apply frozen b2.

This proves that anchor differences come from the frozen b2 layer, not from a changed base model or feature builder.

## d2 Stage-0 output rows

The output keeps the existing C1 live features and row cadence and adds:

- `legacy_prior_p50`;
- `frozen_v2_p50`;
- `frozen_v2_expected_occupancy`;
- `anchor_delta_seats`;
- `pre_live_freeze_id`;
- `pre_live_manifest_sha256`;
- `anchor_status`;
- `prior_completed_same_season_home_matches`;
- `regime_ewma_residual_fraction`;
- `target_live_delta_attendance`;
- `target_live_delta_occupancy`.

For the primary d2 dataset in this stage:

`anchor_status = FROZEN_V2_EXACT`

for every row or the audit fails.

## CI/CD shape

PR validation is intentionally static because the existing Supabase export gateway accepts GitHub OIDC only from `refs/heads/main`.

PR job:

- compile;
- unit tests;
- frozen manifest SHA test;
- committed C1 9/30 contract test;
- capacity audit test;
- b2 min3/cap behavior test.

After merge to main:

1. request the same `beyond-c1-alpha-training` OIDC token;
2. fetch the existing C1 split payloads;
3. compose the same nine-event/final24 replay payload;
4. build exact frozen-v2 anchors;
5. emit JSON compatibility evidence + CSV d2 Stage-0 rows;
6. upload both as immutable Actions evidence.

## Decision gate

Stage 0 passes only if:

- frozen manifest SHA is exact;
- C1 live row identity remains 9 events / 30 rows;
- all target T-1 base predictions reproduce the legacy C1 base exactly;
- all 30 rows receive `FROZEN_V2_EXACT` lineage;
- event anchors are constant across live snapshots within an event;
- no learned model is fitted;
- production remains unchanged.

After PASS, d2 Stage 1 may run the predeclared small LOEO tournament against the frozen-v2 anchor.
