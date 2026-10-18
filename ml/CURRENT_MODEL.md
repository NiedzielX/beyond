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

Frozen production bundle:

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

Status: **ACTIVE OPTIMIZATION / T-7 HISTORICAL CANDIDATE FROZEN / OTHER HORIZONS NEXT / PRODUCTION UNCHANGED**.

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

Stage 1 identified T-7 as the only material initial opportunity.

## a2 stage 2 — T-7 fixed blend robustness

Evidence:

`ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`

Run: `39157403710`

Development selected:

`alpha = 1.00`

Signal:

`FULL_HIST31_SELECTED_NO_BLEND_ROBUSTNESS_GAIN`

Conclusion:

- unconditional fixed blending only trades MAE for lower revision size;
- development gives no basis for a partial blend;
- production unchanged.

## a2 stage 3 — T-7 robust estimator

Evidence:

`ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`

Run: `39157926927`

Development winner:

`hist31-leaf20-l2-1`

Exact settings:

- HistGradientBoostingRegressor;
- `loss=absolute_error`;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- `min_samples_leaf=20`;
- L2 1.0;
- seed 42;
- same T-7 base features and `baseline_season`;
- capacity-normalized residual target.

Stage-3 result:

- 2023/24 development: 2,476.82 -> **2,317.34**, +159.48 MAE;
- 2024/25: 1,777.69 -> **1,650.97**, +126.73;
- 2025/26: 1,802.28 -> **1,773.80**, +28.48;
- mean reference: 1,789.98 -> **1,712.38**, +77.60.

Tail remained material:

- 2024/25 worst degradation: +4,094.16;
- 2025/26 worst degradation: +3,700.56.

## a2 stage 4 — external T-7 model families

Evidence:

`ml/results/T7_EXTERNAL_MODEL_FAMILY_V1_2026-10-18.md`

Run: `39158519963`

Pinned external families:

- CatBoost 1.2.10;
- LightGBM 4.7.0;
- XGBoost 3.4.1.

Development ranking top:

1. `hist31-leaf20-l2-1` — **2,317.34 MAE**;
2. LightGBM 15 leaves — 2,323.57;
3. LightGBM 31 leaves — 2,369.53.

The internal HGB remained the development winner. References therefore reproduced the Stage-3 result:

- mean reference MAE **1,712.38**;
- mean improvement **+77.60**.

Decision:

- tested CatBoost/LightGBM/XGBoost variants do not beat the frozen HGB development winner;
- do not rescue the LightGBM runner-up from reference behavior;
- stop broadening the T-7 model zoo without a genuinely new hypothesis.

## a2 stage 5 — fixed T-7 temporal robustness

Evidence:

`ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md`

Run: `39159276055`

Artifact ID: `12148660037`

Result JSON SHA256:

`0e3f6720be56dabe358cea00b3ad5edf896e4dc7f71940cb89b400f287621d54`

The Stage-3 winner was frozen exactly. No tuning or candidate selection occurred.

Rolling folds:

| Test season | Incumbent MAE | Fixed challenger MAE | Improvement | Paired bootstrap P(uplift > 0) | Worst degradation |
|---|---:|---:|---:|---:|---:|
| 2022/23 | 2,088.94 | **1,984.99** | **+103.95** | 91.8% | +6,623.99 |
| 2023/24 | 2,476.82 | **2,317.34** | **+159.48** | 99.08% | +4,335.66 |
| 2024/25 | 1,777.69 | **1,650.97** | **+126.73** | 99.35% | +4,094.16 |
| 2025/26 | 1,802.28 | **1,773.80** | **+28.48** | 76.04% | +3,700.56 |

Aggregate:

- positive MAE improvement: **4/4 rolling folds**;
- mean fold improvement: **+104.66 MAE**;
- median fold improvement: +115.34;
- median AE improves in all four folds;
- p90 AE improves in all four folds;
- bias is closer to zero in all four folds;
- reportable club-season cells improved: **47/72 = 65.28%**.

Important remaining risk:

- earliest 2022/23 fold has a +6,623.99 worst single-event degradation;
- 2025/26 paired bootstrap 95% interval crosses zero and P(uplift > 0) is 76.04%;
- event improvement rate is only about 53–55%, so value comes from error magnitude, not universal per-event wins;
- 25/72 reportable club-season cells do not improve.

### T-7 freeze decision

`hist31-leaf20-l2-1` is now the **frozen historical T-7 candidate for Pre-Live v2**.

Freeze means:

- stop T-7 estimator/hyperparameter tuning on the current exposed historical reference set;
- preserve this exact config for later Pre-Live v2 integration and future evidence;
- reopen T-7 tuning only for genuinely new data or a materially new hypothesis;
- do **not** replace the production T-7 runtime from historical evidence alone.

Production T-7 remains:

`structural-prior-runtime-v1-t7-gbr-base`

## Immediate remaining a2 work

T-7 estimator search is paused/frozen.

Next optimize unresolved horizons with a stronger **multi-fold development selection** protocol:

- T-30;
- T-14;
- T-3;
- T-1.

Do not repeat one-season winner selection if a candidate is unstable across earlier rolling development folds.

A justified next harness should:

- use 2022/23 and 2023/24 as development-era rolling folds where technically valid;
- require explicit improvement/stability criteria before a candidate advances;
- freeze the selected candidate before 2024/25–2025/26 reference scoring;
- preserve exact incumbent benchmark assertions;
- report full MAE, median, p90, bias, tail and club diagnostics.

Residual/club calibration remains a valid later a2 hypothesis after per-horizon model-family/protocol work.

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

**multi-fold unresolved-horizon tournament for T-30 / T-14 / T-3 / T-1**, while keeping the T-7 historical candidate frozen and production unchanged.
