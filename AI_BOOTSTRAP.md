# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-21**

## Cold-start rule

Read in this order:

1. `ml/MAE_RESEARCH_ROADMAP_V3.md`;
2. `ml/PROGRESS_TRACKING.md`;
3. `ml/CURRENT_MODEL.md`;
4. `ml/CORE_PRODUCT_STATUS.md`;
5. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
6. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
7. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`;
8. only then open detailed result/manifests needed for the current task.

Do not rebuild frozen historical benchmarks merely to recover context.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons, using honest PIT-safe and reproducible evidence.**

Model complexity is secondary. Predictive information and future MAE are primary.

## Current architecture

### Global historical / structural core

Beyond already has a global multi-club model:

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- Global Model v2.1 residual architecture: club-history baseline + learned global residual correction.

Historical 2024/25 and 2025/26 results have already influenced research. They remain useful exposed evidence but are not unseen for new challengers.

### Frozen final24 live package

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Do not mutate it from new outcomes.

### Frozen long72 live package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Scope: `24 < hours_to_kickoff <= 72`

Architecture:

- frozen T-3 anchor;
- `inventory-linear-extrapolation` expert;
- correction cap `±0.10` occupancy;
- `P2-observation-maturity` reliability.

Historical development:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- uplift `+694.51 / +18.73%`.

Do not retune this package on the same development events.

## Two lanes — always work in parallel

### Lane A — evidence

Continue:

- final24 prospective scoring;
- long72 forecast persistence before label exposure;
- append-only outcome join;
- MAE / band / bias / tail scorecards;
- explicit evidence-class labeling.

Lane A validates existing packages. It does not block new model work.

### Lane B — MAE R&D

Current priority order:

1. canonical rolling / forward validation;
2. MAE-native loss / q=0.5 challenger tournament;
3. event/fixture-block uncertainty for `ΔMAE`;
4. new PIT-safe context — especially next-home-fixture substitution/cannibalization;
5. forecast combinations from materially different information sources;
6. live-ticket residual uplift over the strongest structural/global forecast;
7. 72–168h learned experiment once `N>=9` independent events;
8. club-specific shrinkage/calibration only if it improves global generalization.

## Immediate work

Do not wait for future matches.

1. finish long72 two-phase forecast materialization -> outcome scoring;
2. implement forward/rolling evaluation utilities and persist fold boundaries;
3. run MAE-native residual challengers against the strongest global benchmark;
4. add uncertainty around `ΔMAE` using event/fixture as the resampling unit;
5. materialize PIT-safe next-match / fixture-density features;
6. run controlled feature-family ablations;
7. test mean / median / fixed convex / MAE-optimized convex forecast combinations;
8. measure live inventory only as incremental information over the structural champion;
9. continue prospective accumulation and long168 coverage in the background.

## Hard boundaries

Never:

- use random snapshot splits as headline evidence;
- train an earlier forecast with future-season/event information;
- call already inspected historical holdouts unseen;
- use realized weather or final-state context at an earlier PIT cutoff;
- retune frozen packages while keeping the same package ID;
- learn ensemble weights on the evaluation fold;
- promote from historical uplift alone;
- stop R&D merely because prospective evidence is still accumulating.

## Production boundary

Production remains unchanged unless explicitly reviewed and activated:

`live_adjustment = 0`

## One-line instruction

> **Keep frozen packages immutable for evidence; in parallel build new MAE-first challengers using forward validation, MAE-aligned losses, richer PIT-safe context and forecast combinations over the strongest global structural model.**
