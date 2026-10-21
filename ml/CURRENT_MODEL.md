# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-21**

Status: **TRACK-A V2 FROZEN VALIDATION + TRACK-B V3 RESEARCH + LONG72 P2 HISTORICAL PACKAGE SEALED + FORWARD SCORING NEXT**

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Two parallel tracks

### Track A — frozen forward validation

Keep unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

This remains the final24 forward/prospective evidence stack.

### Track B — active R&D

Pre-Live research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Frozen historical early-live package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Active next work:

`forward scoring without retuning`

> **Production promotion waits for prospective evidence. R&D does not.**

---

# Production boundary

Production bundle remains:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

No Track-B research package is production activation.

---

# Track A — Frozen Pre-Live v2 + final24 d2

Pre-Live freeze:

`pre-live-v2-historical-candidate-2026-10-18-v1`

| Horizon | Historical base | b2 regime | c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | 1,691.40 |
| T-3 | Structural Prior | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | 1,682.63 |
| T-1 | Structural Prior | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | 1,661.52 |

Frozen final24 live package:

- expert `ridge-a10`;
- reliability `P2-observation-maturity`;
- package `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

Track A is unchanged by long72 R&D.

---

# Track B — Frozen Pre-Live v3 research candidate

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

V3 changes:

| Horizon | Historical base | current-season regime |
|---|---|---|
| T-30 | `0.75 current a2 + 0.25 XGBoost depth3` | `NO_ADJUSTMENT` |
| T-14 | exact v2 | `NO_ADJUSTMENT` |
| T-7 | `0.25 HGB + 0.25 CatBoost d4 + 0.50 LightGBM leaves15` | `ewma50-resid-k4-cap05-min2` |
| T-3 | exact v2 | `ewma50-resid-k2-cap05-min3` |
| T-1 | exact v2 | `ewma50-resid-k6-cap05-min3` |

Historical package audit:

`1934.04 -> 1924.64`, gain `+9.39 / +0.49%` across the 20 rolling horizon cells.

V3 remains research-only.

---

# Final24 v2/v3 equivalence — COMPLETE

Canonical result:

`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`

Run:

`39636749440`

Artifact ID:

`12361203868`

Decision:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Maximum v3-v2 final24 anchor-seat delta:

`0.0 seats`

Consequence:

- no new final24 target;
- no cosmetic Ridge retrain;
- no final24 P2 reselection solely because v3 exists.

---

# Long-horizon live data contract — COMPLETE

Additive export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Existing final24 export:

`v7-final24`

remains unchanged.

Coverage:

- 14 eligible labeled events;
- 13 beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Frozen learned-model threshold:

`N = 9 independent events`

Decision:

- current learned early-live window = **24–72h**;
- 72–168h remains diagnostic-only.

---

# Frozen long72 data + anchor — COMPLETE

Canonical result:

`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`

Run:

`39640723942`

Artifact ID:

`12365352293`

Dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Dataset:

- 14 events;
- 130 rows;
- 0–24h: 50;
- 24–48h: 45;
- 48–72h: 35.

Checkpoint hold:

- `0<h<=24` -> T-1;
- `24<h<=72` -> T-3;
- no future checkpoint interpolation.

Because v2/v3 T-3 and T-1 are identical, this anchor is numerically valid under both freezes.

---

# Long72 Stage 1 — COMPLETE

Canonical result:

`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`

Run:

`39642620259`

Artifact ID:

`12365399256`

Historical research lead:

`inventory-linear-extrapolation`

Scope:

`24<h<=72`

LOEO historical evidence:

- anchor MAE `3707.14`;
- raw inventory MAE `3254.68`;
- improvement `+452.46 / +12.21%`;
- 24–48h uplift `+675.33 / +18.22%`;
- 48–72h uplift `+675.68 / +14.71%`.

Limitations:

- event improvement rate only `46.15%`;
- bias `+1458.93 seats`;
- overall worst degradation `3100.60 seats`;
- 48–72h worst degradation `3741.79 seats`;
- original exposed subset `-485.52 MAE`.

Stage 1 therefore produced a research expert, not a sealed package by itself.

---

# Long72 Stage 2 — COMPLETE / HISTORICAL PACKAGE SEALED

Canonical result:

`ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`

Run:

`39644319080`

Artifact ID:

`12366826274`

Stage-2 JSON SHA256:

`a9daa834e15b4f313b15c3e809033b7d79e4ed4357f61a8f5071e6bf20359d8c`

Predictions SHA256:

`489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b`

Decision:

`STAGE2_RELIABILITY_POLICY_SELECTED`

Selected policy:

`P2-observation-maturity`

Historical package manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

Package ID:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

## Exact package

For `24<h<=72`:

`forecast = T-3 anchor + reliability * frozen inventory-linear-extrapolation delta`

Observation reliability:

- first observation `0.25`;
- second `0.60`;
- third and later `1.00`.

Time reliability:

- 60–72h `0.75`;
- 48–60h `0.90`;
- 24–48h `1.00`.

Final reliability:

`min(observation_weight, time_weight)`

## Historical package metrics

Overall 24–72h:

- anchor MAE `3707.14`;
- raw inventory MAE `3254.68`;
- P2 package MAE **`3012.63`**;
- improvement vs anchor **`+694.51 / +18.73%`**;
- event improvement rate **`61.54%`**;
- bias **`+917.05 seats`**;
- worst event degradation **`1488.34 seats`**.

Versus raw inventory:

- another `242.05 seats` lower MAE;
- worst degradation reduced `52.00%`;
- absolute bias reduced `37.14%`.

24–48h:

- MAE `2752.56`;
- improvement `+954.58 / +25.75%`.

48–72h:

- MAE `3927.67`;
- improvement `+664.71 / +14.47%`;
- event improvement rate `70%`;
- worst degradation `2413.28 seats`.

Historical stability:

- original exposed subset `+103.55 MAE`;
- later exposed subset `+1640.04 MAE`.

All selection/scoring evidence remains historical and exposed.

---

# Active next — long72 forward scoring without retuning

The sealed package is now fixed historically.

Next contract must:

1. pin `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`;
2. produce early-live predictions before outcome scoring;
3. preserve exact T-3 anchor / inventory extrapolation / P2 logic;
4. preserve package hashes and row-level as-of lineage;
5. classify evidence as delayed-label diagnostic vs genuine post-freeze prospective;
6. score MAE, bias, worst-event degradation and event-improvement rate;
7. forbid parameter/policy changes from observed forward outcomes;
8. keep Track-A final24 separate;
9. keep production unchanged.

When 72–168h reaches N>=9 independent events, open a separate T-7-aware experiment rather than modifying this package.

---

# Prospective evidence classes

Track-A cutoff remains:

`2026-10-19T19:11:01Z`

- `DELAYED_LABEL_HOLDOUT`: diagnostic only;
- `TRUE_POST_FREEZE_PROSPECTIVE`: genuine forward evidence.

The new long72 scoring contract must declare its own package-freeze cutoff and apply the same evidence-integrity principle.

---

# Immediate development decision

> **Keep Track-A v2/Ridge/P2 frozen. Keep Pre-Live v3 research-only. Seal long72 P2 as historical research package and move immediately to forward scoring without retuning. Production remains unchanged.**
