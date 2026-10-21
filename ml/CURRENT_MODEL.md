# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-21**

Status: **TRACK-A V2 FROZEN VALIDATION + TRACK-B V3 FROZEN RESEARCH CANDIDATE + D2-V3 NEXT**

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Two parallel tracks

### Track A — frozen validation

Current forward-evidence stack remains unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Track A continues append-only delayed-label / true-post-freeze scoring.

### Track B — active accuracy R&D

A new historical/pre-live anchor is now sealed:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Next active work:

`d2-v3 — rebuild/revalidate live updater against Frozen Pre-Live v3 research anchor`

> **Production promotion waits for prospective evidence. R&D does not.**

---

# Production boundary

Production bundle remains:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

No research freeze below is production activation.

---

# Track A — Frozen Pre-Live v2

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

| Horizon | Historical base | b2 regime | c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | 1,691.40 |
| T-3 | Structural Prior | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | 1,682.63 |
| T-1 | Structural Prior | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | 1,661.52 |

This remains the anchor for the current frozen Ridge/P2 prospective-validation package.

---

# Track B — Frozen Pre-Live v3 research candidate

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Canonical manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Freeze run:

`39633561065`

Artifact ID:

`12360033160`

Result:

`ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`

## Exact v3 contract

| Horizon | Historical base | current-season regime | Historical c2 |
|---|---|---|---|
| T-30 | `0.75 current a2 + 0.25 XGBoost depth3` | `NO_ADJUSTMENT` | `NO_CONTEXT` |
| T-14 | exact v2 T-14 base | `NO_ADJUSTMENT` | `NO_CONTEXT` |
| T-7 | `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15` | `ewma50-resid-k4-cap05-min2` | `NO_CONTEXT` |
| T-3 | exact v2 T-3 base | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` |
| T-1 | exact v2 T-1 base | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` |

Reference mean MAE:

- T-30: **1,825.49**;
- T-14: **1,809.45**;
- T-7: **1,670.60**;
- T-3: **1,682.63**;
- T-1: **1,661.52**.

Compared with Frozen v2, only T-30 and T-7 change.

## Package audit result

20-cell mean MAE:

- Frozen v2: `1934.04`;
- v3: `1924.64`;
- improvement: `+9.39 / +0.49%`.

T-30 vs Frozen v2:

`+5.98 / +33.50 / +54.93 / +29.74` MAE across the four rolling folds.

T-7 vs Frozen v2:

`+10.92 / +11.18 / +13.71 / +27.88`.

T-14/T-3/T-1 reproduce v2 exactly.

Important limitations:

- gain is modest;
- 2024/25 and 2025/26 are exposed historical references;
- T-30/T-7 still have material event-level tail regressions;
- v3 is a research anchor, not Track-A replacement or production.

---

# Why T-1 did not enter v3

The T-1 historical ensemble had passed the earlier 4/4 historical-anchor audit, but after current-season-regime revalidation the full package was mixed vs Frozen v2:

- 2024/25: `+1.92` MAE;
- 2025/26: `-15.39` MAE.

Therefore v3 correctly retains the v2 T-1 package.

---

# Why T-7 b2 changed

On the new T-7 anchor, development-only regime selection moved from the v2 policy:

`ewma50-resid-k6-cap05-min3`

to:

`ewma50-resid-k4-cap05-min2`

This was selected before the exposed references were opened.

T-30 selected `NO_ADJUSTMENT` on the new anchor.

---

# Track A frozen d2 package

Stage-1 expert:

`ridge-a10`

Stage-2 package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Development summary:

- Frozen-v2 latest MAE `4128.01`;
- raw Ridge latest `3320.39`;
- P2 latest `3240.99`;
- P2 window `3657.65`;
- P2 worst degradation `1081.72`.

These remain tied to Frozen Pre-Live v2.

**Do not silently reuse Ridge/P2 against v3.**

---

# Active Track-B next workstream — d2-v3

The live residual target changes because the anchor changed.

Required next cycle:

1. reconstruct the frozen v3 anchor for the existing d2 replay rows;
2. create a new `d2-v3` target relative to v3;
3. keep the old v2/Ridge/P2 stack as benchmark;
4. rerun a compact live-model tournament under event-level temporal/LOEO controls;
5. revalidate reliability/tail governance under a new policy ID;
6. do not use exposed forward outcomes as unseen selection data;
7. no production write.

The previous Stage-1 Chronos formulation remains closed unless the new anchor/target creates a materially different predeclared hypothesis.

---

# Prospective evidence classes

Stage-2 v2 cutoff:

`2026-10-19T19:11:01Z`

- `DELAYED_LABEL_HOLDOUT`: diagnostic only;
- `TRUE_POST_FREEZE_PROSPECTIVE`: genuine forward-promotion evidence.

Track-A prospective scoring continues against v2 while Track-B d2-v3 research proceeds separately.

---

# Context research

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

Forward PIT-safe context collection continues for verified rivalry, absences, sporting state, media/GDELT and valid hype/search/social sources.

---

# Immediate development decision

> **Keep Frozen Pre-Live v2 / Ridge / P2 unchanged for Track-A validation. Pre-Live v3 is now a sealed Track-B research anchor. Active model R&D moves to a new d2-v3 rebuild/revalidation against v3, while production remains unchanged.**
