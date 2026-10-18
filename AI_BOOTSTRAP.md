# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-18**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering it.

## Cold-start rule

Read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
2. `ml/CURRENT_MODEL.md`;
3. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
4. `ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md`;
5. `ml/results/CURRENT_SEASON_REGIME_FIXED_TEMPORAL_AUDIT_V1_2026-10-18.md`;
6. `ml/results/CONTEXT_EXTENSION_V2_2026-10-18.md`;
7. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
8. `ml/C1_MODEL_TOURNAMENT_V1.md`;
9. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
10. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

> **Build d2 — a continuous live updater that learns incremental forecast revisions against the immutable frozen Pre-Live v2 historical candidate contract.**

Do not continue a2/b2/c2 tuning against the same exposed historical reference seasons.

## Architecture

Frozen historical pre-live layer:

`history + proven current-season regime -> Pre-Live v2 historical candidate`

Historical c2 context extension:

`NO_CONTEXT_ALL_HORIZONS`

Forward-only context such as rivalry, verified absences and hype/media remains prospective shadow research.

Next layer:

`frozen Pre-Live v2 + continuous live ticketing trajectory -> d2 Continuous Live Updater`

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 ACTIVE`

## Frozen Pre-Live v2 historical candidate

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Canonical manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

Manifest SHA256:

`44c911d1ac8b1bf6870ed31e1a636b9b8374d8c8da2d57ba3b4fb5b4aaba4d3c`

Seal run:

`39166115174`

Artifact ID:

`12150457295`

Artifact ZIP SHA256:

`c2b7440ae84a96c474992ecbb07c4bb43f319a9e021fc370a82f439b6edd5dd1`

Freeze CI:

- 5/5 unit tests PASS;
- historical input hash PASS;
- **20/20 exact horizon-season MAE reproduction cells PASS at `1e-9`**;
- fresh manifest vs committed manifest byte-for-byte `cmp` PASS;
- canonical manifest SHA lock PASS.

This is a historical candidate freeze, not a production promotion.

## Frozen per-horizon contract

| Horizon | Historical base | b2 current-season regime | historical c2 |
|---|---|---|---|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | `NO_ADJUSTMENT` | `NO_CONTEXT` |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | `NO_ADJUSTMENT` | `NO_CONTEXT` |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` |

Historical reference mean MAE across 2024/25 + 2025/26:

- T-30: `1867.82`;
- T-14: `1809.45`;
- T-7: **`1691.40`**;
- T-3: **`1682.63`**;
- T-1: **`1661.52`**.

## a2 — CLOSED

T-7 historical base is `hist31-leaf20-l2-1`; T-30/T-14/T-3/T-1 retain their Structural Prior incumbents.

Do not reopen feature-ablation, model-family, recency or persistent cross-season calibration grids on the same exposed references without materially new data/hypothesis.

## b2 — CLOSED FOR CURRENT HISTORICAL DATA

Successful hypothesis:

**same-season actual-vs-own-model residual regime**, with strict PIT completion rule:

`prior kickoff + 3h <= current forecast as_of`

Frozen policies activate only after **3 earlier completed same-season home matches**.

Final fixed four-fold audit:

- T-7 mean MAE gain: **+51.47**;
- T-3: **+70.44**;
- T-1: **+69.54**.

Known risk remains explicit:

- max harmful event regression observed: **+2,760.55 seats**;
- club-season uplift is heterogeneous;
- correction cap stays +/-5% verified capacity.

## c2 historical — CLOSED FOR CURRENT DATA

`Context Extension v2` tested PIT-safe sequence-aware sporting form and current-table stakes/pressure incrementally over frozen a2+b2.

Result:

- T-30/T-14/T-7/T-3 selected `NO_CONTEXT` on development;
- T-1 selected `sequence_stakes` on development but failed both references, mean reference delta **-36.97 MAE**.

Do not post-hoc rescue another c2 candidate on exposed references.

Remaining rivalry/absence/hype/media context stays prospective shadow because complete multi-season PIT truth does not exist.

## d2 — ACTIVE NOW

Do **not** train d2 against the old production Structural Prior baseline when the frozen Pre-Live v2 candidate can be reproduced.

Primary target direction:

`live_delta = actual_attendance - frozen_pre_live_v2_p50`

or capacity-normalized equivalent.

Final live candidate:

`d2_p50 = frozen_pre_live_v2_p50 + predicted_live_delta`

Start with one continuous model over time-to-kickoff rather than five fragmented horizon models.

### d2 evidence rules

- event x as-of timestamp rows;
- all snapshots from one event stay in the same validation fold;
- LOEO is primary while event N is small;
- equal event influence / event-balanced weighting;
- no random row split;
- live features must be available at exact as-of;
- release/coverage changes are confidence/structure signals, not automatically demand;
- Structural anchor must identify the frozen Pre-Live v2 lineage;
- primary metric is event-level final-attendance MAE vs frozen Pre-Live v2;
- tail / worst-event degradation / bias are mandatory.

### Existing live/C1 assets to reuse

- full public inventory trajectory collection;
- velocity / acceleration / trajectory-gap features;
- sector aggregates and coverage/release diagnostics;
- frozen C1 v8 package `c1-shadow-v8-frozen-2026-10-16-n9`;
- append-only prospective C1 v8 evidence pipeline;
- existing LOEO modelling/evaluation infrastructure.

C1 v8 remains frozen `EXPERIMENTAL_SHADOW`; do not silently retune it while d2 is developed.

## Production boundary

Production remains:

`live_adjustment = 0`

The frozen historical Pre-Live v2 candidate does not replace production runtime automatically.

## Non-negotiable CI/CD

Every material experiment:

`code -> tests/checks -> CI -> artifact -> metrics -> result doc -> decision -> canonical docs update`

Persist exact data/feature versions, as-of semantics, folds, exclusions, preprocessing, weights, hyperparameters, seeds, source hashes and limitations.

CI green != production promotion.

## One-line instruction

> **Pre-Live v2 historical candidate is sealed. Stop historical a2/b2/c2 retuning. Build d2 as a continuous PIT-safe live residual updater against freeze ID `pre-live-v2-historical-candidate-2026-10-18-v1`, reusing C1/live infrastructure while production and C1 v8 remain unchanged.**
