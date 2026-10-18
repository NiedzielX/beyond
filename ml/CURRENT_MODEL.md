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

The current PIT feature store already includes, among others:

### Historical demand

- home attendance mean / median / last;
- rolling 3 / 5 / 10;
- variance / p90 / trend;
- previous-season mean;
- club-vs-league demand;
- opponent demand history;
- home-opponent pair history.

### Current-season demand

- `season_home_n`;
- `season_home_mean`;
- `season_home_last`;
- `season_home_r3`;
- `season_vs_long_ratio`.

### Sporting / match context

- home and away matches played / points / PPG;
- GD per game;
- last-5 points / GD;
- table position and gaps;
- top/bottom-table interactions;
- days since last match;
- previous-14-day congestion;
- opponent-draw interactions.

Therefore the next work should not simply duplicate these variables as another correction layer.

## a) Historical data

Status: **MATURE INCUMBENT / NOT FULLY OPTIMIZED**.

The current Structural Prior stays production incumbent until a challenger proves better.

Immediate a2 optimization is now allowed and required before freezing Pre-Live v2:

- feature-group contribution / ablation;
- evidence-based noisy-feature removal;
- newer-season weighting challengers;
- horizon-specific model-family challengers;
- residual / club calibration challengers;
- validated ensemble candidates.

The goal is a stronger baseline without sacrificing point-in-time integrity or reproducibility.

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

Next b2 priority is residual-based current-season regime modeling:

- actual-vs-expected residuals from completed current-season home matches;
- ratio `actual / expected`;
- EWMA / rolling residuals;
- robust regime signal;
- sample-size-aware / hierarchical shrinkage.

The question is not only whether this season's raw attendance differs from history. The better question is:

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

Only then train the new learned live updater against the frozen Pre-Live v2 baseline.

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

Do not jump directly from the current b/c results into a new production-oriented live model.

The active accuracy work is:

**a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2**.

Frozen C1 v8 prospective collection continues in parallel.

Mandatory interpretation:

> **A failed challenger closes the challenger, not the workstream.**
