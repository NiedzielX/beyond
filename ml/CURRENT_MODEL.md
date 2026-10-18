# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-18**

This is the canonical short-form model state.

Read `AI_BOOTSTRAP.md` and `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md` first in a cold session.

## Current north star

Beyond is a **live demand decision system**.

Immediate forecasting goal:

> **Reduce MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Architecture:

`history + current-season regime + match context -> Pre-Live Model v2`

then:

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> Continuous Live Updater v2`

Active sequence:

`a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2`

## Structural Prior runtime — production incumbent

| Horizon | Model spec | 2023/24 dev MAE | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | 2,559.7 | 1,889.4 | 1,846.3 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | 2,340.0 | 1,748.5 | 1,870.4 |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | 2,476.8 | 1,777.7 | 1,802.3 |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | 2,311.6 | 1,661.7 | 1,775.1 |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | 2,348.0 | 1,651.7 | 1,742.8 |

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Evidence base:

- 5 Ekstraklasa seasons;
- 1,530 matches;
- 7,650 PIT horizon rows;
- verified capacity coverage 100%.

Production remains:

`live_adjustment = 0`

## Existing pre-live signal coverage

The current PIT feature store already includes:

- historical home demand / rolling windows;
- current-season home demand;
- opponent draw and pair history;
- PPG / GD/game / form;
- table position and interactions;
- calendar/timing;
- rest/congestion.

New work must add information or materially improve representation/modeling rather than duplicate these fields.

# a) Historical data

Status: **ACTIVE OPTIMIZATION / STRONGER T-7 MAE CHALLENGER FOUND / PRODUCTION INCUMBENT UNCHANGED**.

## a2 stage 1 — baseline optimization

Evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

Run: `39156711796`

| Horizon | Dev-selected candidate | Mean incumbent MAE | Mean selected MAE | Mean improvement | Decision |
|---|---|---:|---:|---:|---|
| T-30 | `ablate-rest_congestion` | 1,867.82 | 1,864.11 | +3.71 | retain incumbent |
| T-14 | `recency-linear_075` | 1,809.45 | 1,798.25 | +11.19 | mixed; retain incumbent |
| T-7 | `model-hist_absolute_31` | 1,789.98 | 1,721.18 | **+68.81** | material lead |
| T-3 | `incumbent` | 1,718.39 | 1,718.39 | 0.00 | retain incumbent |
| T-1 | `recency-linear_075` | 1,697.28 | 1,707.36 | -10.07 | retain incumbent |

Stage-1 T-7 Hist31:

- development: +97.36 MAE;
- 2024/25: +105.55;
- 2025/26: +32.06;
- mean reference: +68.81;
- worst degradations: +3,685.74 and +4,233.11.

## a2 stage 2 — fixed blend robustness

Evidence:

`ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`

Run: `39157403710`

Fixed alphas:

`0 / .25 / .50 / .75 / 1.0`

Development selected:

`alpha = 1.00`

Signal:

`FULL_HIST31_SELECTED_NO_BLEND_ROBUSTNESS_GAIN`

Conclusion:

- unconditional blending only trades MAE for lower revision size;
- development gives no basis for a partial blend;
- no production change.

## a2 stage 3 — T-7 robust estimator v1

Evidence:

`ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`

Run: `39157926927`

Ten predeclared estimator/regularization candidates were selected on 2023/24 only.

Development winner:

`hist31-leaf20-l2-1`

Exact settings:

- HistGradientBoostingRegressor;
- `loss=absolute_error`;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- **min samples leaf 20**;
- L2 1.0;
- seed 42;
- same T-7 baseline/features and uniform season weights.

Only material change versus stage-1 Hist31:

`min_samples_leaf: 10 -> 20`

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

- incumbent mean reference MAE: **1,789.98**;
- selected mean reference MAE: **1,712.38**;
- improvement: **+77.60**;
- improves both reference seasons: **true**;
- reduces stage-1 Hist31 worst tail on both references: **false**.

Signal:

`REGULARIZED_WINNER_POSITIVE_MEAN_TAIL_NOT_SOLVED`

This is the **lowest T-7 mean reference MAE found so far**.

### Current T-7 decision

`hist31-leaf20-l2-1` is the strongest current MAE challenger, but **not production champion**.

Reason:

- average/median quality is materially better;
- tail remains inconsistent, improving in 2025/26 but worsening in 2024/25;
- references are already exposed historical evidence;
- no post-hoc candidate selection from reference behavior is allowed.

### Immediate a2 next step

Compare a materially different estimator family under the exact same T-7 baseline/feature/split contract.

Priority candidates:

- CatBoost;
- LightGBM;
- XGBoost;
- or another clearly different pinned tabular learner.

Selection remains development-only. Reference scoring occurs only after one candidate is frozen.

Any serious champion candidate then needs a fixed-config broader temporal robustness audit before explicit T-7 freeze/promotion.

# b) Current season

Status: **PARTIALLY TESTED / NOT EXHAUSTED**.

Current Season Adjustment v1 was `NOT PROVEN`; it closes that formulation only.

Next b2 after a2:

- historical PIT actual-vs-expected residuals;
- demand ratio `actual / expected`;
- EWMA / rolling residuals;
- sample-size-aware and hierarchical shrinkage.

Goal:

> detect whether the current season systematically beats or misses our own expected demand.

# c) Match context

Status: **AUDITED + ONE CHALLENGER TESTED / NOT EXHAUSTED**.

Existing context already covers opponent draw, pair history, PPG, GD/game, form, table and past congestion.

Future Fixture Context v1 was `NOT PROVEN` and must not be repeatedly tuned on the same references.

Next safe candidate gaps:

- match stakes / title-Europe-relegation relevance;
- sequence-aware streaks;
- rivalry / derby / exceptional opponent draw where deterministic;
- squad availability only with reliable historical PIT data.

# Freeze point — Pre-Live v2

After a2+b2+c2, freeze per-horizon champions with exact:

- model IDs;
- feature contracts;
- data versions;
- training seasons / weights;
- hyperparameters;
- preprocessing;
- calibration;
- seeds;
- artifact hashes;
- scorecards and limitations.

Only then train the new learned live updater against that stable baseline.

# d) Live demand

Status: **LIVE INFRASTRUCTURE EXISTS / NEW d2 LEARNED MODEL AFTER PRE-LIVE v2 FREEZE**.

Already available:

- public inventory collection;
- PIT trajectory / velocity / acceleration;
- release / coverage-change handling;
- frozen C1 v8 prospective shadow;
- sector and price-area trajectories;
- Roboticket price observations;
- guarded decision support.

New d2 should use continuous time-to-kickoff and learn delta/remaining-demand/reliability against frozen Pre-Live v2.

# Frozen C1 v8

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Historical boundary:

- raw Live LOEO: 2,929.3;
- conservative synthetic: 2,261.5;
- stress synthetic: 2,498.8;
- four-event chronological Prior: 452.8;
- raw Live: 2,103.7;
- frozen v8: 452.8 with PRIOR in 16/16 rows.

Do not retune frozen v8 from this evidence.

# Engineering governance

Full rules:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

Non-negotiable:

- MAE primary, tail/bias mandatory;
- event is independent unit;
- no random snapshot split;
- PIT-only features;
- synthetic data train-only;
- exact versions and hashes;
- code + CI + artifact + result + decision;
- exact incumbent comparison;
- no silent holdout retuning;
- CI green != production promotion.

## Current development decision

Continue:

**a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2**.

Immediate next a2 experiment:

**T-7 materially different external/tabular estimator family comparison**, followed by broader fixed-config temporal robustness for any serious champion candidate.
