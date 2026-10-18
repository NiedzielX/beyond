# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-18**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering it.

## Cold-start rule

Read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
2. `ml/CURRENT_MODEL.md`;
3. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
4. `ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md`;
5. `ml/results/PRE_LIVE_UNRESOLVED_MULTIFOLD_V1_2026-10-18.md`;
6. `ml/results/PERSISTENT_CLUB_CALIBRATION_V1_2026-10-18.md`;
7. `ml/results/CURRENT_SEASON_RESIDUAL_REGIME_V1_2026-10-18.md`;
8. `ml/results/CURRENT_SEASON_REGIME_MATURITY_STAGE2_V1_2026-10-18.md`;
9. `ml/results/CURRENT_SEASON_REGIME_FIXED_TEMPORAL_AUDIT_V1_2026-10-18.md`;
10. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
11. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
12. `ml/NORTH_STAR.md`;
13. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

> **Dopracować model maksymalnie teraz i obniżyć MAE tak daleko, jak pozwala uczciwa, reprodukowalna walidacja PIT-safe.**

Do not optimize for finishing roadmap labels. A failed challenger closes the challenger, not the whole workstream.

## Architecture

`history + current-season regime + match context -> Pre-Live Model v2`

then:

`Pre-Live v2 + continuous live trajectory -> Continuous Live Updater v2`

Canonical sequence:

`a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2`

Current active workstream:

**c2 — match context**.

## a2 — CLOSED FOR CURRENT DATA

Historical candidate state:

| Horizon | a2 historical base |
|---|---|
| T-30 | production Structural Prior incumbent |
| T-14 | production Structural Prior incumbent |
| T-7 | **`hist31-leaf20-l2-1` frozen historical candidate** |
| T-3 | production Structural Prior incumbent |
| T-1 | production Structural Prior incumbent |

T-7 fixed temporal audit improves all 4 rolling folds, mean **+104.66 MAE**.

Unresolved-horizon two-fold tournament retains incumbent at T-30/T-14/T-3/T-1.

Persistent cross-season club calibration was tested under two fixed formulations and did not produce stable development evidence.

Do not restart these grids on the same exposed references without materially new data/hypothesis.

## b2 — CLOSED FOR CURRENT DATA

Old raw-attendance-vs-history Current Season Adjustment v1 was not proven.

The successful b2 hypothesis uses **same-season actual-vs-own-model residual state**.

Critical PIT rule:

`prior kickoff + 3h <= current forecast as_of`

No uncompleted match outcome may enter regime state.

Frozen historical b2 policies:

| Horizon | b2 policy |
|---|---|
| T-30 | `NO_ADJUSTMENT` |
| T-14 | `NO_ADJUSTMENT` |
| T-7 | `ewma50-resid-k6-cap05-min3` |
| T-3 | `ewma50-resid-k2-cap05-min3` |
| T-1 | `ewma50-resid-k6-cap05-min3` |

Final fixed 4-fold audit:

- T-7: all 4 folds positive, mean **+51.47 MAE**;
- T-3: all 4 folds positive, mean **+70.44**;
- T-1: all 4 folds positive, mean **+69.54**.

Maturity gate:

- activate only after **3 earlier completed same-season home matches**.

Risk boundary:

- max observed harmful event regression **+2,760.55 seats**;
- club-season improvement share roughly 60–64%;
- correction cap remains +/-5% verified capacity.

These are historical Pre-Live candidates, not production promotion.

## Current Pre-Live candidate stack before c2

| Horizon | a2 base | b2 layer |
|---|---|---|
| T-30 | incumbent | none |
| T-14 | incumbent | none |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` |
| T-3 | incumbent | `ewma50-resid-k2-cap05-min3` |
| T-1 | incumbent | `ewma50-resid-k6-cap05-min3` |

c2 must measure incremental value over this stack, not over the older production-only baseline.

## c2 — ACTIVE NOW

Already present PIT-safe context:

- opponent draw / pair history;
- PPG / GD per game;
- last-5 form;
- table position / gaps;
- top/bottom interactions;
- rest / congestion.

`Future Fixture Context v1` was `NOT PROVEN`. Do not retune the same future-fixture formulation on the same references.

Next c2 priorities:

1. **match stakes / table pressure**
   - title-race relevance;
   - European qualification relevance;
   - relegation relevance;
   - direct-table-rival / points-pressure;
   - late-season importance.
2. **sequence-aware form**
   - winning streak;
   - unbeaten streak;
   - losing streak;
   - points acceleration/deceleration;
   - home-specific streak where justified.
3. rivalry/derby/exceptional draw only with deterministic mapping.
4. squad context only if historical PIT source is reliable and timestamped.

Immediate next experiment:

> **C2 Context Extension v2: PIT-safe match-stakes + sequence-aware form, development-only selection, full temporal/tail diagnostics, incremental evaluation over the frozen a2+b2 stack.**

## Production / Live boundary

Production remains:

`live_adjustment = 0`

Frozen C1 v8 remains `EXPERIMENTAL_SHADOW` and must not be retuned silently.

Prospective collection continues in parallel.

## Non-negotiable CI/CD

Every material experiment:

`code -> tests/checks -> CI -> artifact -> metrics -> result doc -> decision -> canonical docs update`

Persist exact feature definitions, data versions, as-of rules, splits, exclusions, preprocessing, weights/caps/shrinkage, hyperparameters, seeds, benchmark assertions, artifact hashes and limitations.

No random snapshot split. No future standings. No final-season labels in historical as-of features. No silent reference retuning. CI green != production promotion.

## One-line instruction

> **a2 and b2 are sufficiently evaluated for current data. Treat the frozen a2+b2 historical stack as the c2 baseline. Build PIT-safe match-stakes and sequence-aware context next; do not revisit old grids or future-fixture v1. Keep production and frozen C1 unchanged with full CI/CD evidence.**
