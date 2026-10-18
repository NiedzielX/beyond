# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-18**

This is the canonical short-form model state.

Read `AI_BOOTSTRAP.md` and `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md` first in a cold session.

## Current north star

Beyond is a **live demand decision system**.

The immediate forecasting goal is:

> **Reduce MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

The development architecture is:

### Pre-Live Model v2

`history + current-season regime + match context -> strongest possible pre-live forecast`

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory state + time-to-kickoff + reliability -> live delta / revised forecast`

Active sequence:

`a2 baseline optimization -> b2 current-season regime -> c2 match context -> freeze Pre-Live v2 -> d2 continuous live updater`

## Structural Prior runtime — current production incumbent

Current frozen runtime:

| Horizon | Model spec | 2023/24 dev MAE | 2024/25 historical MAE | 2025/26 historical MAE |
|---|---|---:|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | 2,559.7 | 1,889.4 | 1,846.3 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | 2,340.0 | 1,748.5 | 1,870.4 |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | 2,476.8 | 1,777.7 | 1,802.3 |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | 2,311.6 | 1,661.7 | 1,775.1 |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | 2,348.0 | 1,651.7 | 1,742.8 |

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

Historical evidence base:

- Ekstraklasa 2021/22–2025/26;
- 1,530 matches;
- 7,650 PIT horizon rows;
- verified historical capacity coverage 100%.

## What Structural Prior already contains

Do not assume b) and c) are absent from the incumbent.

The current PIT feature store already includes historical demand, current-season demand, opponent/pair history, sporting form, table context, calendar/time and rest/congestion signals.

Therefore new work should test new information or a materially better representation, not duplicate existing variables under another name.

## a) Historical data

Status: **ACTIVE OPTIMIZATION / T-7 MATERIAL LEAD FOUND / PRODUCTION INCUMBENT UNCHANGED**.

### a2 stage 1 — Pre-Live Baseline Optimization v1

Canonical evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

Run:

`39156711796`

| Horizon | Development-selected candidate | Mean incumbent MAE | Mean candidate MAE | Mean improvement | Interpretation |
|---|---|---:|---:|---:|---|
| T-30 | `ablate-rest_congestion` | 1,867.82 | 1,864.11 | +3.71 | too small / unstable to change champion |
| T-14 | `recency-linear_075` | 1,809.45 | 1,798.25 | +11.19 | mixed by season; retain incumbent |
| T-7 | `model-hist_absolute_31` | 1,789.98 | **1,721.18** | **+68.81** | material lead; robustness research required |
| T-3 | `incumbent` | **1,718.39** | 1,718.39 | 0.00 | incumbent wins development |
| T-1 | `recency-linear_075` | **1,697.28** | 1,707.36 | -10.07 | not proven |

T-7 `model-hist_absolute_31` uses the incumbent T-7 baseline/feature contract with:

- HistGradientBoostingRegressor;
- `loss=absolute_error`;
- learning rate 0.04;
- 300 iterations;
- max 31 leaf nodes;
- min samples leaf 10;
- L2 = 1.0;
- seed 42;
- uniform season weights.

MAE improvement:

- 2023/24 development: **+97.36**;
- 2024/25 reference: **+105.55**;
- 2025/26 reference: **+32.06**;
- mean reference: **+68.81**.

But harmful single-event regressions are too large:

- `Śląsk Wrocław – Raków` 2024/25: **+3,685.74** error degradation;
- `Lech – Arka Gdynia` 2025/26: **+4,233.11** error degradation.

### a2 T-7 stage 2 — fixed-blend robustness v1

Canonical evidence:

`ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`

Run:

`39157403710`

Fixed predeclared alpha candidates:

`0.00 / 0.25 / 0.50 / 0.75 / 1.00`

Development result:

| Alpha | MAE | Improvement vs incumbent | Worst degradation |
|---:|---:|---:|---:|
| **1.00** | **2,379.46** | **+97.36** | 4,317.24 |
| 0.75 | 2,381.95 | +94.86 | 3,237.93 |
| 0.50 | 2,400.99 | +75.83 | 2,158.62 |
| 0.25 | 2,433.51 | +43.30 | 1,079.31 |
| 0.00 | 2,476.82 | 0.00 | 0.00 |

Development selects:

`alpha = 1.00`

Reference result therefore remains full Hist31:

- mean reference incumbent MAE: **1,789.98**;
- selected/full-Hist31 MAE: **1,721.18**;
- improvement: **+68.81**;
- improves both reference seasons: **true**;
- tail reduction vs stage 1: **0**.

Automated signal:

`FULL_HIST31_SELECTED_NO_BLEND_ROBUSTNESS_GAIN`

Interpretation:

> **A constant blend does not solve the T-7 tail problem under the declared MAE-first selection protocol.**

Choosing a smaller alpha because it looks safer on 2024/25 or 2025/26 would be holdout retuning and is not allowed.

### Current a2 next step

Keep the current production T-7 incumbent unchanged and test **predeclared stronger-regularization / robust T-7 estimators** while preserving:

- the T-7 baseline;
- feature contract;
- data splits;
- development-only selection;
- exact incumbent assertions;
- full MAE + tail scorecard.

Primary hypothesis:

> Hist31's average gain is real, but a less locally flexible absolute-error booster may retain most of the MAE improvement with smaller event-level regressions.

Do not invent a tail penalty from exposed reference outcomes and call it unseen evidence.

After this T-7 work, continue remaining justified a2 model-family / feature / calibration research before declaring a2 complete.

## b) Current season

Status: **PARTIALLY TESTED / NOT EXHAUSTED**.

`Current Season Adjustment v1` tested a bounded post-model correction based on current-season home level versus historical norm.

Result:

- T-30 / T-14 / T-3 / T-1: `NO_ADJUSTMENT` selected;
- T-7: `season_r3-k6-a25` won development but degraded both reference holdouts;
- no horizon improved mean holdout MAE;
- no production change.

Canonical evidence:

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

Interpretation:

> That formulation is not proven. The workstream is not exhausted.

Next b2 priority after a2 freeze is residual-based current-season regime modeling:

- actual-vs-expected residuals from completed current-season home matches;
- ratio `actual / expected`;
- EWMA / rolling residuals;
- robust regime signal;
- sample-size-aware / hierarchical shrinkage.

The better question is:

> **Is this club currently running systematically above or below what our own incumbent model expected?**

## c) Match context

Status: **AUDITED + ONE CHALLENGER TESTED / NOT EXHAUSTED**.

The existing PIT feature store already contains substantial opponent, sporting, form, table and past-congestion context.

`Future Fixture Context v1` tested next-home-fixture timing / attractiveness / cannibalization.

Result:

| Horizon | Selected option | Mean incumbent MAE | Mean challenger MAE |
|---|---|---:|---:|
| T-30 | `NO_CONTEXT_EXTENSION` | 1,867.8 | 1,867.8 |
| T-14 | `NO_CONTEXT_EXTENSION` | 1,809.4 | 1,809.4 |
| T-7 | `future_timing_attractiveness` | **1,790.0** | 1,790.9 |
| T-3 | `NO_CONTEXT_EXTENSION` | 1,718.4 | 1,718.4 |
| T-1 | `future_timing_attractiveness` | **1,697.3** | 1,712.4 |

No horizon improves mean holdout MAE; no horizon improves both reference seasons.

Canonical evidence:

- `ml/MATCH_CONTEXT_AUDIT_V1.md`;
- `ml/results/MATCH_CONTEXT_FUTURE_FIXTURE_V1_2026-10-18.md`.

Interpretation:

> Future Fixture Context v1 is not proven. The entire context workstream is not complete.

Next c2 candidate gaps:

- match stakes / title-Europe-relegation relevance;
- sequence-aware winning / unbeaten / losing streaks;
- exceptional opponent draw / rivalry / derby where deterministic and PIT-safe;
- squad availability only after a reliable historical PIT source exists.

Do not keep retuning the same Future Fixture v1 formulation on the same exposed reference seasons.

## Freeze point: Pre-Live v2

After a2 + b2 + c2 are evaluated, freeze the strongest reproducible configuration:

- exact feature contract;
- exact per-horizon model specs;
- training seasons / weighting;
- calibration;
- data versions;
- hyperparameters;
- artifact hashes;
- benchmark result.

Only then train the new learned live updater against frozen Pre-Live v2.

## d) Live demand

Status: **CURRENT LIVE INFRASTRUCTURE EXISTS / NEW d2 LEARNED MODEL FOLLOWS PRE-LIVE v2 FREEZE**.

Already implemented:

- live public inventory collection;
- PIT trajectory / velocity / acceleration;
- release / coverage-change handling;
- frozen C1 v8 prospective shadow inference;
- sector trajectories;
- price-area trajectories and Roboticket price observations;
- guarded sector / pricing decision support.

New d2 architecture should prioritize:

- continuous `time_to_kickoff`, not only five checkpoints;
- earliest usable sales observation;
- forecast refresh on meaningful snapshots;
- delta-vs-Pre-Live prediction;
- remaining-demand prediction;
- reliability-weighted blend challenger;
- explicit data-quality / coverage / release handling.

T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints, not the only update moments.

## C1 development evidence

Current frozen-v8 live evidence base:

- 9 completed in-domain training events;
- 206 PIT-valid full-trajectory rows;
- 30 final-24h rows.

Historical development / validation evidence:

- raw Live LOEO: **2,929.3 MAE**;
- conservative train-only synthetic Live LOEO: **2,261.5 MAE**;
- stress train-only synthetic Live LOEO: **2,498.8 MAE**;
- four-event chronological Prior: **452.8 MAE**;
- four-event chronological raw Live: **2,103.7 MAE**;
- frozen v8: **452.8 MAE**, selecting PRIOR in **16/16 rows** on those events.

Canonical evidence:

- `ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_WALK_FORWARD_POLICY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_FORWARD_EVENT_DIAGNOSTIC_V1_2026-10-18.md`.

Do not retune frozen v8 from those events.

## Frozen C1 v8 prospective package

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Frozen expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Frozen training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

This remains frozen while prospective evidence accumulates.

There is no confirmed prospective live MAE until independent completed prospective events are scored.

## Engineering / validation governance

Full rules are in `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`.

Non-negotiable summary:

- MAE is primary, but tail degradation and bias must be reported;
- event is the independent evaluation unit;
- no random snapshot split across the same event;
- every feature must be available as-of forecast timestamp;
- synthetic data is train-only and not independent evidence;
- exact feature/data/model versions must be persisted;
- every serious challenger requires code + CI + artifact + result document + decision;
- benchmark incumbent must be the exact compared contract;
- no silent retuning on the same holdout;
- no local/manual benchmark becomes canonical without reproducible CI evidence;
- CI success does not equal production promotion;
- production remains `live_adjustment = 0` until explicit promotion.

## Current development decision

Active work remains:

**a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2**.

Within a2 the immediate next experiment is:

**T-7 stronger-regularization / robust estimator challenger.**

Frozen C1 v8 prospective collection continues in parallel.
