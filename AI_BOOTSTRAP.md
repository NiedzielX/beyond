# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-18**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Before doing Beyond forecasting, ML, dashboard, Growth or recommendation work, read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md` — canonical model-development and CI/CD instruction;
2. `ml/CURRENT_MODEL.md` — current model/product state;
3. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md` — active accuracy roadmap;
4. `ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md` — current a2 stage-1 evidence;
5. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md` — frozen C1 prospective runtime/governance;
6. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — live forecasting runtime/roadmap;
7. `ml/SECTOR_DECISION_PRICING_V1.md` — E0 sector/pricing product contract;
8. `ml/NORTH_STAR.md`;
9. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
10. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
11. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

> **Dopracować model maksymalnie teraz i obniżyć MAE tak daleko, jak pozwala uczciwa, reprodukowalna walidacja.**

Do not optimize for finishing roadmap labels.

Do not mark a whole workstream complete because one challenger failed.

## Canonical architecture

### Pre-Live Model v2

`history + current-season regime + match context -> strongest possible pre-live forecast`

This is the immediate active development area.

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / revised forecast`

This follows the Pre-Live v2 optimization/freeze.

Frozen C1 v8 continues prospective collection in parallel and must not be retuned silently.

## Active work order

1. **a2 — Historical / Structural Prior optimization — ACTIVE**
   - stage 1 baseline optimization: **COMPLETED**;
   - next: **T-7 Hist31 robustness / fixed-blend challenger**;
   - then continue justified feature/model/calibration research before calling a2 complete.
2. **b2 — Current-season regime**
   - residual-based current-season signals;
   - actual-vs-expected ratios;
   - EWMA / rolling residuals;
   - sample-size-aware shrinkage;
   - hierarchical regime signals where justified.
3. **c2 — Match context**
   - match stakes / title-Europe-relegation relevance;
   - better streak representation;
   - rivalry / derby / exceptional opponent draw where deterministic;
   - squad availability only with reliable historical PIT data;
   - do not keep retuning the already weak Future Fixture Context v1 on the same exposed holdouts.
4. **Freeze Pre-Live v2.**
5. **d2 — Continuous Live Updater**
   - continuous time-to-kickoff;
   - earliest usable inventory evidence;
   - forecast refresh on meaningful snapshots;
   - delta / remaining-demand / reliability-weighted blend challengers;
   - explicit release/coverage/data-quality handling.

Shortcut:

`a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2`

## Workstream status — precise wording

- a) Historical data: **ACTIVE OPTIMIZATION / STAGE 1 COMPLETE / PRODUCTION INCUMBENT UNCHANGED**.
- b) Current season: **PARTIALLY TESTED / NOT EXHAUSTED**.
- c) Match context: **AUDITED + ONE CHALLENGER TESTED / NOT EXHAUSTED**.
- d) Live demand: **IMPORTANT / FROZEN C1 PROSPECTIVE COLLECTION ACTIVE / NEW d2 AFTER PRE-LIVE v2 FREEZE**.

Mandatory interpretation:

> **A failed challenger closes the challenger, not the workstream.**

`Current Season Adjustment v1 NOT PROVEN` closes that formulation only.

`Future Fixture Context v1 NOT PROVEN` closes that formulation only.

## Structural Prior — production incumbent

All five horizons are executable and frozen in the current production bundle.

Historical reference MAE:

| Horizon | 2024/25 | 2025/26 |
|---|---:|---:|
| T-30 | 1,889.4 | 1,846.3 |
| T-14 | 1,748.5 | 1,870.4 |
| T-7 | 1,777.7 | 1,802.3 |
| T-3 | 1,661.7 | 1,775.1 |
| T-1 | 1,651.7 | 1,742.8 |

Production remains:

`live_adjustment = 0`

## a2 stage 1 — Pre-Live Baseline Optimization v1

Canonical evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

GitHub Actions run:

`39156711796`

Result by horizon:

| Horizon | Development-selected candidate | Mean incumbent MAE | Mean candidate MAE | Mean improvement | Current decision |
|---|---|---:|---:|---:|---|
| T-30 | `ablate-rest_congestion` | 1,867.82 | 1,864.11 | +3.71 | retain incumbent; gain too small/unstable |
| T-14 | `recency-linear_075` | 1,809.45 | 1,798.25 | +11.19 | retain incumbent; seasons mixed |
| T-7 | `model-hist_absolute_31` | 1,789.98 | **1,721.18** | **+68.81** | advance to robustness/blend stage 2 |
| T-3 | `incumbent` | **1,718.39** | 1,718.39 | 0.00 | retain incumbent |
| T-1 | `recency-linear_075` | **1,697.28** | 1,707.36 | -10.07 | retain incumbent |

T-7 is the material lead:

- development: **+97.36 MAE**;
- 2024/25: **+105.55 MAE**;
- 2025/26: **+32.06 MAE**;
- median AE improves on both reference seasons;
- p90 improves materially on 2024/25 and is approximately neutral on 2025/26.

But tail risk blocks champion replacement:

- worst 2024/25 degradation: **+3,685.74 error** on `Śląsk Wrocław – Raków`;
- worst 2025/26 degradation: **+4,233.11 error** on `Lech – Arka Gdynia`.

Therefore:

- no production artifact changes;
- do not call Hist31 the new T-7 champion yet;
- next a2 experiment must test fixed incumbent/Hist31 blending or another explicitly governed robustness mechanism selected on development only;
- reference holdouts must not be used to tune blend weight.

## Frozen C1 v8 — prospective shadow

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Frozen expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Do not retune or silently retrain this package during prospective validation.

## Current C1 historical evidence

Canonical evidence:

- `ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_WALK_FORWARD_POLICY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_FORWARD_EVENT_DIAGNOSTIC_V1_2026-10-18.md`.

Key results:

- raw Live LOEO: **2,929.3 MAE**;
- conservative train-only synthetic Live LOEO: **2,261.5 MAE**;
- stress train-only synthetic Live LOEO: **2,498.8 MAE**;
- four-event chronological Prior: **452.8 MAE**;
- four-event chronological raw Live: **2,103.7 MAE**;
- frozen v8 selects PRIOR in **16/16 rows** and preserves Prior exactly on those four events.

Interpretation:

- synthetic augmentation helps the raw live expert;
- raw Live is not a universal replacement for Prior;
- frozen v8 was safe on the current retrospective forward events;
- this is not prospective proof that v8 knows when to switch to Live;
- more independent completed prospective events are still required.

## b) evidence already produced

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

Result: `NOT PROVEN / NO PRODUCTION CHANGE`.

Important: this tested one post-model current-season adjustment. It does not exhaust b).

## c) evidence already produced

- `ml/MATCH_CONTEXT_AUDIT_V1.md`;
- `ml/results/MATCH_CONTEXT_FUTURE_FIXTURE_V1_2026-10-18.md`.

Result: Future Fixture Context v1 is `NOT PROVEN / RESEARCH-ONLY`.

Important: this tests one context hypothesis. It does not exhaust c).

## Non-negotiable engineering accuracy / CI/CD

Every material experiment must have committed code and an executable CI workflow.

Never skip:

- exact feature definitions;
- source data/artifact versions;
- as-of availability;
- train/dev/holdout definition;
- exclusions;
- imputation/normalization;
- thresholds/caps/weights/shrinkage;
- hyperparameters;
- deterministic seed;
- incumbent benchmark assertion;
- PIT/leakage checks;
- machine-readable result artifact;
- run/artifact IDs and hashes where available;
- committed result document;
- explicit decision;
- canonical docs update.

Do not accept notebook/manual/local-only benchmarks as canonical evidence.

Do not random-split snapshots from the same event across train/test.

Do not treat synthetic rows as independent real events.

Do not silently retune on the same holdout.

CI success is not automatic production promotion.

## One-line cold-start instruction

> **Optimize for honest MAE reduction, not roadmap completion. a2 stage 1 is complete: T-7 Hist31 is the only material lead (+68.81 mean reference MAE) but has >4k worst-event tail degradation, so the immediate next task is a development-selected T-7 robustness/blend challenger. Production Structural Prior and frozen C1 v8 remain unchanged. After a2, continue b2 -> c2 -> freeze Pre-Live v2 -> d2 with complete CI/CD evidence.**
