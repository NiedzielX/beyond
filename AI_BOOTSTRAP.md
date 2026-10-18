# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-18**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Before doing Beyond forecasting, ML, dashboard, Growth or recommendation work, read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md` — canonical model-development and CI/CD instruction;
2. `ml/CURRENT_MODEL.md` — current model/product state;
3. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md` — active accuracy roadmap;
4. `ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md` — a2 stage-1 evidence;
5. `ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md` — a2 T-7 stage-2 evidence;
6. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md` — frozen C1 prospective runtime/governance;
7. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — live forecasting runtime/roadmap;
8. `ml/SECTOR_DECISION_PRICING_V1.md` — E0 sector/pricing product contract;
9. `ml/NORTH_STAR.md`;
10. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
11. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
12. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

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
   - T-7 fixed-blend robustness stage 2: **COMPLETED / NO ROBUSTNESS GAIN**;
   - next: **T-7 stronger-regularization / robust estimator challenger**, keeping the stage-1 feature/baseline contract fixed;
   - then continue justified model-family / calibration research before calling a2 complete.
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

- a) Historical data: **ACTIVE OPTIMIZATION / T-7 MATERIAL LEAD FOUND / PRODUCTION INCUMBENT UNCHANGED**.
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
| T-7 | `model-hist_absolute_31` | 1,789.98 | **1,721.18** | **+68.81** | material lead; robustness research required |
| T-3 | `incumbent` | **1,718.39** | 1,718.39 | 0.00 | retain incumbent |
| T-1 | `recency-linear_075` | **1,697.28** | 1,707.36 | -10.07 | retain incumbent |

T-7 Hist31 improves:

- development: **+97.36 MAE**;
- 2024/25: **+105.55 MAE**;
- 2025/26: **+32.06 MAE**;
- mean reference: **+68.81 MAE**.

But stage-1 tail risk:

- 2024/25 worst degradation: **+3,685.74** on `Śląsk Wrocław – Raków`;
- 2025/26 worst degradation: **+4,233.11** on `Lech – Arka Gdynia`.

## a2 T-7 stage 2 — fixed blend robustness

Canonical evidence:

`ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`

GitHub Actions run:

`39157403710`

Predeclared blend alphas:

`0.00 / 0.25 / 0.50 / 0.75 / 1.00`

Development ranking by MAE:

| Alpha | Development MAE | Improvement vs incumbent | Worst degradation |
|---:|---:|---:|---:|
| **1.00** | **2,379.46** | **+97.36** | 4,317.24 |
| 0.75 | 2,381.95 | +94.86 | 3,237.93 |
| 0.50 | 2,400.99 | +75.83 | 2,158.62 |
| 0.25 | 2,433.51 | +43.30 | 1,079.31 |
| 0.00 | 2,476.82 | 0.00 | 0.00 |

Development therefore selects:

`alpha = 1.00`

Reference result remains full Hist31:

- mean reference improvement: **+68.81 MAE**;
- improves both reference seasons: **true**;
- tail reduction versus stage 1: **0**.

Automated signal:

`FULL_HIST31_SELECTED_NO_BLEND_ROBUSTNESS_GAIN`

Interpretation:

- simple constant blending is **not** the solution under the declared MAE-first protocol;
- choosing a smaller alpha from reference-season tail behavior would be holdout retuning;
- full Hist31 remains the strongest MAE candidate found so far;
- production T-7 champion remains unchanged because severe isolated regressions are still unresolved.

### Immediate a2 next step

Test **predeclared stronger-regularization / robust T-7 estimators** while keeping the T-7 baseline, feature contract, data splits and selection governance fixed.

Primary hypothesis:

> Hist31 may be too locally flexible for a few events; stronger regularization may retain much of its MAE gain while reducing tail degradation without post-hoc gating.

Do not invent a tail penalty from 2024/25 or 2025/26 outcomes and call it unseen evidence.

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

> **Optimize for honest MAE reduction, not roadmap completion. a2 found a real T-7 Hist31 lead (+68.81 mean reference MAE), but fixed blending does not solve its >4k worst-event tail because development selects 100% Hist31. Keep production unchanged and next test predeclared stronger-regularization / robust T-7 estimators under the same development-only selection protocol. Then continue a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2 with complete CI/CD evidence.**
