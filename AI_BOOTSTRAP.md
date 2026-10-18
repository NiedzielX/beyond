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
6. `ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md` — a2 T-7 stage-3 evidence;
7. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md` — frozen C1 prospective runtime/governance;
8. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — live forecasting runtime/roadmap;
9. `ml/SECTOR_DECISION_PRICING_V1.md` — E0 sector/pricing product contract;
10. `ml/NORTH_STAR.md`;
11. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
12. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
13. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

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
   - stage 1 baseline optimization: **COMPLETED**;
   - T-7 fixed-blend robustness stage 2: **COMPLETED / NO ROBUSTNESS GAIN**;
   - T-7 stronger-regularization stage 3: **COMPLETED / LOWER MAE FOUND / TAIL STILL MIXED**;
   - next: **materially different T-7 model-family challengers** under the same baseline/feature/split contract;
   - then fixed-config broader temporal robustness before any T-7 champion freeze.
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

- a) Historical data: **ACTIVE OPTIMIZATION / T-7 STRONGER MAE CHALLENGER FOUND / PRODUCTION INCUMBENT UNCHANGED**.
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

## a2 stage 1 — baseline optimization

Evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

Run: `39156711796`

Key T-7 lead:

`model-hist_absolute_31`

- development improvement: **+97.36 MAE**;
- 2024/25: **+105.55**;
- 2025/26: **+32.06**;
- mean reference improvement: **+68.81**;
- mean reference MAE: **1,721.18**.

Tail problem:

- 2024/25 worst degradation: **+3,685.74**;
- 2025/26 worst degradation: **+4,233.11**.

## a2 stage 2 — fixed blend robustness

Evidence:

`ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`

Run: `39157403710`

Development selected `alpha=1.00` from fixed blends `0 / .25 / .50 / .75 / 1.0`.

Signal:

`FULL_HIST31_SELECTED_NO_BLEND_ROBUSTNESS_GAIN`

Conclusion:

- constant blending only trades away MAE for smaller revisions;
- development provides no basis to pick a partial blend;
- production remains unchanged.

## a2 stage 3 — T-7 robust estimator v1

Evidence:

`ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`

Run: `39157926927`

Selected on 2023/24 development:

`hist31-leaf20-l2-1`

Exact change versus stage-1 Hist31:

`min_samples_leaf: 10 -> 20`

Other core settings remain:

- HistGradientBoostingRegressor;
- `loss=absolute_error`;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- L2 1.0;
- seed 42.

### Development

- incumbent MAE: **2,476.82**;
- selected MAE: **2,317.34**;
- improvement: **+159.48**;
- median AE: **1,103.63**;
- bias: **-31.75**.

### 2024/25

- incumbent MAE: **1,777.69**;
- selected MAE: **1,650.97**;
- improvement: **+126.73**;
- median AE: **926.00**;
- p90 AE: **4,396.22**;
- bias: **+13.05**;
- worst degradation: **+4,094.16** on `Śląsk Wrocław – Legia`.

### 2025/26

- incumbent MAE: **1,802.28**;
- selected MAE: **1,773.80**;
- improvement: **+28.48**;
- median AE: **1,051.76**;
- p90 AE: **3,753.08**;
- bias: **-5.43**;
- worst degradation: **+3,700.56** on `Lechia Gdańsk – Legia`.

### Aggregate

- mean incumbent MAE: **1,789.98**;
- selected mean MAE: **1,712.38**;
- mean improvement: **+77.60**;
- both reference seasons improve: **true**;
- tail improves versus stage-1 Hist31 on both references: **false**.

Signal:

`REGULARIZED_WINNER_POSITIVE_MEAN_TAIL_NOT_SOLVED`

This is the **lowest T-7 mean reference MAE found so far**.

Decision:

- no production champion change yet;
- `hist31-leaf20-l2-1` becomes strongest current T-7 MAE challenger;
- do not post-hoc pick a different stage-3 candidate from reference behavior;
- next test a materially different estimator family, not another tiny HGB micro-grid;
- any serious champion candidate then requires a fixed-config broader temporal robustness audit before freeze/promotion.

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

- raw Live LOEO: **2,929.3 MAE**;
- conservative train-only synthetic Live LOEO: **2,261.5 MAE**;
- stress train-only synthetic Live LOEO: **2,498.8 MAE**;
- four-event chronological Prior: **452.8 MAE**;
- four-event chronological raw Live: **2,103.7 MAE**;
- frozen v8 selects PRIOR in **16/16 rows** and preserves Prior exactly.

## b) evidence already produced

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

Result: `NOT PROVEN / NO PRODUCTION CHANGE`.

Important: one failed formulation does not exhaust b).

## c) evidence already produced

- `ml/MATCH_CONTEXT_AUDIT_V1.md`;
- `ml/results/MATCH_CONTEXT_FUTURE_FIXTURE_V1_2026-10-18.md`.

Result: Future Fixture Context v1 is `NOT PROVEN / RESEARCH-ONLY`.

Important: one failed formulation does not exhaust c).

## Non-negotiable engineering accuracy / CI/CD

Every material experiment must have committed code and executable CI.

Never skip exact feature definitions, source/artifact versions, as-of rules, train/dev/holdout, exclusions, imputation/normalization, hyperparameters, seeds, incumbent assertions, leakage checks, machine-readable artifacts, hashes, result docs and explicit decisions.

No random split of snapshots from the same event.

No synthetic rows as independent evidence.

No silent retuning on the same holdout.

CI success is not automatic production promotion.

## One-line cold-start instruction

> **Optimize for honest MAE reduction, not roadmap completion. T-7 `hist31-leaf20-l2-1` is now the strongest MAE challenger at 1712.38 mean reference MAE (+77.60 vs incumbent), but tail is still inconsistent across seasons, so production remains unchanged. Next compare materially different T-7 estimator families under the same development-only selection contract, then run broader fixed-config temporal robustness before any T-7 freeze. Continue a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2 with complete CI/CD evidence.**
