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

## Production Structural Prior

| Horizon | Model spec | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | 1,889.4 | 1,846.3 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | 1,748.5 | 1,870.4 |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | 1,777.7 | 1,802.3 |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | 1,661.7 | 1,775.1 |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | 1,651.7 | 1,742.8 |

Frozen production bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Evidence base:

- 5 Ekstraklasa seasons;
- 1,530 matches;
- 7,650 PIT horizon rows;
- verified capacity coverage 100%.

Production remains:

`live_adjustment = 0`

# a) Historical data

Status: **ACTIVE / CURRENT MODEL-FAMILY GRID SETTLED PER HORIZON / RESIDUAL-CLUB CALIBRATION NEXT / PRODUCTION UNCHANGED**.

## Stage 1 — baseline optimization

Evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

Run: `39156711796`

| Horizon | Dev-selected candidate | Mean reference improvement | Stage-1 interpretation |
|---|---|---:|---|
| T-30 | `ablate-rest_congestion` | +3.71 | tiny / unstable |
| T-14 | `recency-linear_075` | +11.19 | mixed |
| T-7 | `model-hist_absolute_31` | **+68.81** | material lead |
| T-3 | incumbent | 0.00 | incumbent |
| T-1 | `recency-linear_075` | -10.07 | not proven |

Stage 1 made T-7 the only material initial lead.

## T-7 Stages 2–5 — completed

Canonical evidence:

- `ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`;
- `ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`;
- `ml/results/T7_EXTERNAL_MODEL_FAMILY_V1_2026-10-18.md`;
- `ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md`.

### Frozen T-7 historical candidate

`hist31-leaf20-l2-1`

Exact config:

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

Stage-3 / Stage-4 reference result:

- incumbent mean reference MAE: **1,789.98**;
- fixed candidate mean reference MAE: **1,712.38**;
- improvement: **+77.60**;
- both reference seasons improve.

Stage 4 tested pinned CatBoost / LightGBM / XGBoost variants; none beat the HGB development winner.

Stage 5 fixed-config rolling audit:

| Season | Incumbent | Candidate | Improvement | Bootstrap P(uplift > 0) |
|---|---:|---:|---:|---:|
| 2022/23 | 2,088.94 | **1,984.99** | +103.95 | 91.8% |
| 2023/24 | 2,476.82 | **2,317.34** | +159.48 | 99.08% |
| 2024/25 | 1,777.69 | **1,650.97** | +126.73 | 99.35% |
| 2025/26 | 1,802.28 | **1,773.80** | +28.48 | 76.04% |

Aggregate:

- positive MAE improvement: **4/4 folds**;
- mean fold improvement: **+104.66**;
- median and p90 AE improve in all four folds;
- bias closer to zero in all four folds;
- reportable club-season cells improved: **47/72 = 65.28%**.

Risk remains explicit:

- earliest-fold worst degradation: **+6,623.99**;
- 2025/26 bootstrap CI crosses zero;
- event improvement rate ~53–55%;
- 25/72 reportable club-season cells do not improve.

Decision:

> **Freeze `hist31-leaf20-l2-1` as the historical T-7 Pre-Live candidate. Do not call it production champion. Stop T-7 micro-tuning on the current exposed historical set.**

Production T-7 remains `structural-prior-runtime-v1-t7-gbr-base`.

## Unresolved-horizon multi-fold tournament — completed

Evidence:

`ml/results/PRE_LIVE_UNRESOLVED_MULTIFOLD_V1_2026-10-18.md`

Run: `39159907426`

Artifact ID: `12148169124`

Result JSON SHA256:

`f7bf178bad293547f3e866dd312997e2415744b68d66f5d4ed5db9cc8b984b1a`

Protocol strengthened Stage 1:

- Fold A: train 2021/22 -> validate 2022/23;
- Fold B: train 2021/22–2022/23 -> validate 2023/24;
- candidate must be identifiable and improve incumbent MAE in both folds;
- recency is explicitly non-identifiable with only one training season;
- references cannot rescue a development-inconsistent candidate;
- only incumbent + frozen multi-fold winner are scored on 2024/25–2025/26.

### T-30

No non-incumbent improves both identifiable development folds.

Examples:

- `ablate-sporting_form`: +11.34 then -21.31;
- `ablate-rest_congestion`: -27.75 then +9.31;
- `model-extra_leaf5`: +20.07 then -57.99.

Decision: **retain incumbent**.

### T-14

No non-incumbent improves both identifiable development folds.

The prior recency signal cannot advance because recency has only one identifiable development fold under the available historical window.

Examples:

- `ablate-table_context`: +12.37 then -67.56;
- `ablate-sporting_form`: +60.96 then -118.69.

Decision: **retain incumbent**.

### T-3

No non-incumbent improves both development folds.

Several average-looking hypotheses reverse sign:

- `ablate-rest_congestion`: +81.25 then -31.67;
- `ablate-home_history`: +48.09 then -2.90;
- `model-hist_absolute_31`: +34.59 then -26.26;
- `model-extra_leaf5`: +92.31 then -99.60.

Decision: **retain incumbent**.

### T-1

Two candidates improve both development folds:

- `ablate-rest_congestion`;
- `ablate-capacity`.

Development selects `ablate-rest_congestion`:

- 2022/23 improvement: **+63.47**;
- 2023/24 improvement: **+11.97**;
- mean: **+37.72**.

Frozen reference scoring:

- 2024/25: incumbent 1,651.73 vs selected 1,690.10 -> **-38.36**;
- 2025/26: incumbent 1,742.84 vs selected 1,717.57 -> **+25.26**;
- mean reference change: **-6.55** — worse.

Signal:

`MULTIFOLD_SELECTED_CANDIDATE_NOT_PROVEN_ON_REFERENCES`

Do not post-hoc score/select `ablate-capacity` to rescue the experiment.

Decision: **retain incumbent**.

## Current per-horizon historical candidate state

| Horizon | Historical Pre-Live candidate | Production runtime changed? |
|---|---|---|
| T-30 | current production incumbent | no |
| T-14 | current production incumbent | no |
| T-7 | **`hist31-leaf20-l2-1` frozen historical candidate** | no |
| T-3 | current production incumbent | no |
| T-1 | current production incumbent | no |

## Immediate remaining a2 hypothesis

Do **not** continue permutations of the same ablation/recency/internal-estimator grid.

Next justified a2 hypothesis:

**historical residual / club calibration**.

Required principles:

- calculate PIT residuals against the correct rolling per-horizon incumbent/historical candidate;
- test whether a persistent club-level residual remains out-of-sample;
- shrink low-sample club estimates strongly toward zero;
- no club memorization without evidence;
- multi-fold development selection;
- full club and tail diagnostics;
- keep the frozen T-7 estimator itself unchanged while calibration is tested as a separate layer.

If residual/club calibration is not proven, a2 should be considered sufficiently exhausted for the current data and development should advance to b2 rather than another model-grid search.

# b) Current season

Status: **PARTIALLY TESTED / NOT EXHAUSTED**.

Current Season Adjustment v1 was `NOT PROVEN`; it closes that formulation only.

Next b2 after a2:

- historical PIT actual-vs-expected residuals within current season;
- demand ratio `actual / expected`;
- EWMA / rolling residuals;
- sample-size-aware and hierarchical shrinkage.

Goal:

> detect whether the current season systematically beats or misses our own expected demand.

Important separation:

- a2 club calibration asks whether a persistent cross-season club residual exists;
- b2 asks whether the **current season regime** differs from expected demand.

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

After a2+b2+c2, freeze exact per-horizon:

- model ID;
- feature contract;
- data version;
- training seasons / weights;
- hyperparameters;
- preprocessing;
- calibration;
- seed;
- artifact hash;
- benchmark scorecard;
- limitations.

Only then train the new learned live updater.

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

Package: `c1-shadow-v8-frozen-2026-10-16-n9`

Status: `EXPERIMENTAL_SHADOW`

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
- exact incumbent/challenger reproduction where applicable;
- no silent holdout retuning;
- CI green != production promotion.

## Current development decision

Continue:

**a2 residual/club calibration -> if exhausted, b2 -> c2 -> freeze Pre-Live v2 -> d2**.

Production remains unchanged.