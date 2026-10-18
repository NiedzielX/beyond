# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-18**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
2. `ml/CURRENT_MODEL.md`;
3. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
4. `ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`;
5. `ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`;
6. `ml/results/T7_EXTERNAL_MODEL_FAMILY_V1_2026-10-18.md`;
7. `ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md`;
8. `ml/results/PRE_LIVE_UNRESOLVED_MULTIFOLD_V1_2026-10-18.md`;
9. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
10. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
11. `ml/SECTOR_DECISION_PRICING_V1.md`;
12. `ml/NORTH_STAR.md`;
13. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

> **Dopracować model maksymalnie teraz i obniżyć MAE tak daleko, jak pozwala uczciwa, reprodukowalna walidacja.**

Do not optimize for finishing roadmap labels. A failed challenger closes the challenger, not the workstream.

## Architecture

`history + current-season regime + match context -> Pre-Live Model v2`

then:

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> Continuous Live Updater v2`

Active sequence:

`a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2`

## Current a2 state

The first model/feature/recency optimization phase is now settled under stronger multi-fold rules.

### Historical candidate per horizon

| Horizon | Historical Pre-Live candidate | Production changed? |
|---|---|---|
| T-30 | current production incumbent | no |
| T-14 | current production incumbent | no |
| T-7 | **`hist31-leaf20-l2-1` frozen historical candidate** | no |
| T-3 | current production incumbent | no |
| T-1 | current production incumbent | no |

### T-7

`hist31-leaf20-l2-1` is frozen after Stages 1–5.

Stage-3/4 references:

- incumbent mean MAE: **1,789.98**;
- candidate: **1,712.38**;
- improvement: **+77.60**.

Fixed temporal audit:

- positive MAE improvement in **4/4 rolling folds**;
- mean fold improvement **+104.66**;
- median/p90 improve 4/4;
- 47/72 reportable club-season cells improve;
- tail risk remains, including +6,623.99 worst degradation in 2022/23;
- 2025/26 bootstrap uncertainty crosses zero.

Decision:

- freeze as historical candidate;
- stop T-7 micro-tuning on the same historical references;
- do not call it production champion;
- reopen only for genuinely new data/materially new hypothesis.

### T-30 / T-14 / T-3 / T-1 multi-fold result

Canonical run: `39159907426`.

Protocol:

- train 2021/22 -> validate 2022/23;
- train 2021/22–2022/23 -> validate 2023/24;
- challenger must be identifiable and improve incumbent in both development folds;
- references cannot rescue a failed development challenger.

Result:

- T-30: no eligible non-incumbent -> incumbent retained;
- T-14: no eligible non-incumbent -> incumbent retained;
- T-3: no eligible non-incumbent -> incumbent retained;
- T-1: `ablate-rest_congestion` wins both development folds (+63.47, +11.97) but fails references on mean (-6.55) -> incumbent retained.

Do not post-hoc select other candidates using reference results.

## Immediate next a2 task

**Historical residual / club calibration.**

Question:

> Does a stable cross-season home-club residual remain after the correct rolling per-horizon model prediction, and can it improve future matches with strong shrinkage and no leakage/memorization?

Required:

- PIT residuals only from completed earlier matches;
- separate calibration layer, not estimator retuning;
- small predeclared mean/median/normalized/shrunk variants;
- low-sample shrinkage;
- bounded corrections;
- multi-fold development selection;
- full club/tail/correction diagnostics;
- T-7 estimator itself stays frozen.

If this is not proven, treat a2 historical optimization as sufficiently exhausted for current data and advance to b2.

## b2 after a2

Current Season Adjustment v1 was `NOT PROVEN`, but b2 is not exhausted.

Next b2 should model current-season actual-vs-expected regime using residuals/demand ratios, EWMA/rolling windows and sample-size-aware shrinkage.

Important distinction:

- a2 club calibration = persistent cross-season club residual;
- b2 = current-season regime shift.

## c2 after b2

Still open:

- match stakes / title-Europe-relegation relevance;
- sequence-aware streaks;
- deterministic rivalry/derby/exceptional draw;
- squad context only with reliable PIT historical data.

## Production / C1 boundary

Production remains:

`live_adjustment = 0`

Frozen C1 v8 remains `EXPERIMENTAL_SHADOW` and must not be retuned silently.

Historical C1 boundary:

- raw Live LOEO 2,929.3;
- conservative synthetic 2,261.5;
- stress synthetic 2,498.8;
- four-event Prior 452.8;
- raw Live 2,103.7;
- frozen v8 452.8 with PRIOR 16/16.

## Non-negotiable CI/CD

Every material experiment:

`code -> tests/checks -> CI -> artifact -> metrics -> result doc -> decision -> canonical docs update`

Persist exact features, data/artifact versions, as-of rules, splits, exclusions, preprocessing, weights/caps/shrinkage, hyperparameters, seeds, benchmark assertions, hashes and limitations.

No random snapshot split. No synthetic rows as independent evidence. No silent reference retuning. CI green != production promotion.

## One-line instruction

> **T-7 is frozen as historical Pre-Live candidate; T-30/T-14/T-3/T-1 retain incumbents after a stricter two-fold tournament. Do not continue the same model grid. Test historical residual/club calibration as the final major a2 hypothesis; if not proven, move to b2. Keep production and frozen C1 unchanged, with full reproducible CI/CD evidence.**
