# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-18**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Before doing Beyond forecasting, ML, dashboard, Growth or recommendation work, read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md` — canonical model-development and CI/CD instruction;
2. `ml/CURRENT_MODEL.md` — current model/product state;
3. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md` — active accuracy roadmap;
4. `ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md` — a2 stage-1 evidence;
5. `ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md` — T-7 stage-2 evidence;
6. `ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md` — T-7 stage-3 evidence;
7. `ml/results/T7_EXTERNAL_MODEL_FAMILY_V1_2026-10-18.md` — T-7 stage-4 evidence;
8. `ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md` — T-7 stage-5 fixed-config robustness evidence;
9. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md` — frozen C1 prospective runtime/governance;
10. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — live forecasting runtime/roadmap;
11. `ml/SECTOR_DECISION_PRICING_V1.md` — E0 sector/pricing product contract;
12. `ml/NORTH_STAR.md`;
13. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
14. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
15. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

> **Dopracować model maksymalnie teraz i obniżyć MAE tak daleko, jak pozwala uczciwa, reprodukowalna walidacja.**

Do not optimize for finishing roadmap labels.

Do not mark a whole workstream complete because one challenger failed.

## Canonical architecture

### Pre-Live Model v2

`history + current-season regime + match context -> strongest possible pre-live forecast`

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / revised forecast`

Frozen C1 v8 continues prospective collection in parallel and must not be retuned silently.

## Active work order

1. **a2 — Historical / Structural Prior optimization — ACTIVE**
   - Stage 1 baseline optimization: **COMPLETED**;
   - T-7 Stage 2 fixed blending: **COMPLETED / NO ROBUSTNESS GAIN**;
   - T-7 Stage 3 stronger regularization: **COMPLETED / LOWER MAE FOUND**;
   - T-7 Stage 4 external model-family comparison: **COMPLETED / HGB REMAINS DEVELOPMENT WINNER**;
   - T-7 Stage 5 fixed temporal robustness: **COMPLETED / POSITIVE 4 OF 4 ROLLING FOLDS / TAIL RISK REMAINS**;
   - T-7 exact config `hist31-leaf20-l2-1`: **FROZEN HISTORICAL PRE-LIVE CANDIDATE / NOT PRODUCTION CHAMPION**;
   - next: **multi-fold unresolved-horizon tournament for T-30 / T-14 / T-3 / T-1**.
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
   - squad availability only with reliable historical PIT data.
4. **Freeze Pre-Live v2.**
5. **d2 — Continuous Live Updater**.

Shortcut:

`a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2`

## Workstream status

- a) Historical data: **ACTIVE / T-7 HISTORICAL CANDIDATE FROZEN / OTHER HORIZONS UNRESOLVED / PRODUCTION UNCHANGED**.
- b) Current season: **PARTIALLY TESTED / NOT EXHAUSTED**.
- c) Match context: **AUDITED + ONE CHALLENGER TESTED / NOT EXHAUSTED**.
- d) Live demand: **IMPORTANT / FROZEN C1 PROSPECTIVE COLLECTION ACTIVE / NEW d2 AFTER PRE-LIVE v2 FREEZE**.

Mandatory interpretation:

> **A failed challenger closes the challenger, not the workstream.**

## Structural Prior — production incumbent

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

## T-7 historical candidate — frozen after a2 Stages 1–5

Candidate:

`hist31-leaf20-l2-1`

Exact settings:

- HistGradientBoostingRegressor;
- absolute-error loss;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- min samples leaf 20;
- L2 1.0;
- seed 42;
- T-7 base feature contract;
- `baseline_season`;
- capacity-normalized residual target.

### Stage 3 / 4 reference result

- incumbent mean reference MAE: **1,789.98**;
- fixed candidate mean reference MAE: **1,712.38**;
- mean improvement: **+77.60**;
- both reference seasons improve: true.

### Stage 5 rolling temporal audit

Run: `39159276055`

| Season | Incumbent | Candidate | Improvement | Bootstrap P(uplift > 0) |
|---|---:|---:|---:|---:|
| 2022/23 | 2,088.94 | **1,984.99** | +103.95 | 91.8% |
| 2023/24 | 2,476.82 | **2,317.34** | +159.48 | 99.08% |
| 2024/25 | 1,777.69 | **1,650.97** | +126.73 | 99.35% |
| 2025/26 | 1,802.28 | **1,773.80** | +28.48 | 76.04% |

Aggregate:

- positive MAE improvement: **4/4 folds**;
- mean fold improvement: **+104.66 MAE**;
- median/p90 improve in all four folds;
- bias closer to zero in all four folds;
- club-season cells improved: **47/72 = 65.28%**.

Remaining risk:

- worst harmful regression reaches **+6,623.99** in the earliest fold;
- 2025/26 bootstrap interval crosses zero;
- only ~53–55% individual events improve;
- 25/72 reportable club-season cells do not improve.

### T-7 decision

Freeze this exact configuration as the **historical T-7 Pre-Live candidate**.

Do not:

- continue micro-tuning T-7 on the same exposed seasons;
- call it a production champion;
- replace `structural-prior-runtime-v1-t7-gbr-base` from retrospective evidence alone.

Reopen T-7 only for genuinely new evidence or a materially new hypothesis.

## Immediate a2 next step

Build a stronger **multi-fold development tournament** for unresolved horizons:

- T-30;
- T-14;
- T-3;
- T-1.

Default development consistency protocol:

- train 2021/22 -> validate 2022/23;
- train 2021/22–2022/23 -> validate 2023/24;
- candidate must improve incumbent MAE in both folds before it may advance;
- if none does, retain incumbent without using references to rescue a candidate;
- freeze one candidate before 2024/25–2025/26 reference scoring;
- full MAE/median/p90/bias/tail/club diagnostics mandatory.

Start with attributable Stage-1 hypotheses: incumbent, feature-group ablations, explicit recency weights and the small internal model-family set. No open-ended model search.

## Frozen C1 v8 — prospective shadow

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Do not retune or silently retrain this package during prospective validation.

Historical C1 boundary:

- raw Live LOEO: **2,929.3 MAE**;
- conservative train-only synthetic: **2,261.5**;
- stress train-only synthetic: **2,498.8**;
- four-event chronological Prior: **452.8**;
- raw Live: **2,103.7**;
- frozen v8: **452.8**, PRIOR in 16/16 rows.

## b) evidence already produced

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

Result: `NOT PROVEN / NO PRODUCTION CHANGE`.

One failed formulation does not exhaust b).

## c) evidence already produced

- `ml/MATCH_CONTEXT_AUDIT_V1.md`;
- `ml/results/MATCH_CONTEXT_FUTURE_FIXTURE_V1_2026-10-18.md`.

Future Fixture Context v1: `NOT PROVEN / RESEARCH-ONLY`.

One failed formulation does not exhaust c).

## Non-negotiable engineering accuracy / CI/CD

Every material experiment must have committed code and executable CI.

Never skip exact feature definitions, source/artifact versions, as-of rules, train/dev/holdout, exclusions, preprocessing, hyperparameters, seeds, incumbent/challenger reproduction assertions, leakage checks, machine-readable artifacts, hashes, result docs and explicit decisions.

No random split of snapshots from the same event.

No synthetic rows as independent evidence.

No silent retuning on the same holdout.

CI success is not automatic production promotion.

## One-line cold-start instruction

> **Optimize for honest MAE reduction, not roadmap completion. T-7 `hist31-leaf20-l2-1` is frozen as the historical Pre-Live candidate after improving MAE in 4/4 rolling folds, but it is not a production champion and tail risk remains explicit. Stop T-7 micro-tuning on the same data. Continue a2 with multi-fold selection for T-30/T-14/T-3/T-1, then b2 -> c2 -> freeze Pre-Live v2 -> d2, with complete CI/CD evidence.**
