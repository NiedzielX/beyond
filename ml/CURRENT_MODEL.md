# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-21**

Status: **TRACK-A V2 FROZEN VALIDATION + TRACK-B V3 FROZEN RESEARCH ANCHOR + LONG72 STAGE2 ACTIVE**

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Two parallel tracks

### Track A — frozen forward validation

Current package remains unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Track A continues delayed-label / true-post-freeze scoring under the existing prospective contract.

### Track B — active R&D

Frozen research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Current early-live historical research lead:

`inventory-linear-extrapolation` for `24–72h`

Active experiment:

`d2-long72-stage2-reliability-gating-v1`

> **Production promotion waits for prospective evidence. R&D does not.**

---

# Production boundary

Production bundle remains:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

No Track-B result is production activation.

---

# Track A — Frozen Pre-Live v2 + final24 d2

Pre-Live freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

| Horizon | Historical base | b2 regime | c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | 1,691.40 |
| T-3 | Structural Prior | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | 1,682.63 |
| T-1 | Structural Prior | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | 1,661.52 |

Frozen final24 d2:

- Stage-1 expert `ridge-a10`;
- Stage-2 policy `P2-observation-maturity`;
- package `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

This remains the prospective-validation stack and is not modified by long72 R&D.

---

# Track B — Frozen Pre-Live v3 research candidate

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Exact v3 contract:

| Horizon | Historical base | current-season regime |
|---|---|---|
| T-30 | `0.75 current a2 + 0.25 XGBoost depth3` | `NO_ADJUSTMENT` |
| T-14 | exact v2 T-14 package | `NO_ADJUSTMENT` |
| T-7 | `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15` | `ewma50-resid-k4-cap05-min2` |
| T-3 | exact v2 T-3 package | `ewma50-resid-k2-cap05-min3` |
| T-1 | exact v2 T-1 package | `ewma50-resid-k6-cap05-min3` |

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

Historical fixed-package audit:

- 20-cell mean MAE `1934.04 -> 1924.64`;
- gain `+9.39 / +0.49%`;
- T-30 positive in 4/4 rolling folds;
- T-7 positive in 4/4;
- T-14/T-3/T-1 reproduce v2 exactly.

V3 remains research-only.

---

# Final24 v2/v3 equivalence — COMPLETE

Result:

`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`

Run:

`39636749440`

Artifact ID:

`12361203868`

Decision:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Frozen development set:

- 9 events;
- 30 final24 rows;
- IDs `1,3,4,8,9,12,13,14,17`.

Maximum v3-v2 anchor-seat delta:

`0.0 seats`

Only machine-level serialization noise remains in derived targets.

Consequence:

> Do not retrain or rename final24 Ridge/P2 merely because the Pre-Live freeze ID changed.

---

# Long-horizon data contract — COMPLETE

Additive export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Existing final24 export:

`v7-final24`

remains unchanged.

Coverage audit result:

`ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`

Current labeled/event coverage:

- 14 eligible events;
- 13 with data beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Inherited independent-event threshold:

`N = 9`

Decision:

`BUILD_FIRST_LONG_HORIZON_MODEL_TO_72H`

Therefore:

- 24–72h is learnable now;
- 72–168h remains diagnostic-only until coverage reaches N>=9.

---

# Frozen long72 data + anchor contract — COMPLETE

Result:

`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`

Run:

`39640723942`

Artifact ID:

`12365352293`

Dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Frozen dataset:

- 14 events;
- 130 rows;
- 0–24h: 50 rows;
- 24–48h: 45 rows;
- 48–72h: 35 rows.

Checkpoint hold:

- `0<h<=24` -> T-1;
- `24<h<=72` -> T-3;
- future checkpoint use forbidden.

Current-season replay uses versioned capacity at kickoff and horizon-specific PIT forecastability. Early-season matches without a reconstructable checkpoint prior are recorded as unforecastable, never imputed with synthetic sporting state.

Because v2/v3 T-3 and T-1 are identical, the frozen 0–72h anchor is valid under both freezes.

---

# Long72 Stage 1 — COMPLETE

Result:

`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`

Canonical run:

`39642620259`

Artifact ID:

`12365399256`

Stage-1 JSON SHA256:

`f19ea1378d0f8b07007bf45c2ab7f3fa20ebb3c53e32afa4548723336b71358a`

Predictions SHA256:

`33de331d2c3bf1e385f513c7fa7e28aa8b454a4d49cfe00d48163e6c083a6df5`

Selection scope:

`24<hours_to_kickoff<=72`

Historical LOEO research lead:

`inventory-linear-extrapolation`

## Stage-1 lead metrics

Overall 24–72h:

- anchor MAE `3707.14`;
- inventory MAE `3254.68`;
- improvement `+452.46 / +12.21%`;
- event improvement rate `46.15%`;
- bias `+1458.93 seats`;
- worst event degradation `3100.60 seats`.

24–48h:

- inventory MAE `3031.81`;
- uplift `+675.33 / +18.22%`.

48–72h:

- anchor MAE `4592.38`;
- inventory MAE `3916.71`;
- uplift `+675.68 / +14.71%`;
- event improvement rate `60%`;
- worst event degradation `3741.79 seats`.

## Historical heterogeneity

Original exposed Stage-1 subset:

- inventory is worse than anchor by `485.52 MAE`.

Later exposed subset:

- inventory improves anchor by `1953.22 MAE`.

Neither subset is unseen.

Interpretation:

> Early inventory trajectory contains useful predictive signal, but the raw Stage-1 rule is not stable enough to become a frozen early-live package.

---

# ACTIVE — Long72 Stage 2 reliability / tail governance

Contract:

`ml/D2_LONG72_STAGE2_RELIABILITY_GATING_V1.md`

Frozen expert:

`inventory-linear-extrapolation`

No Stage-1 model retraining is allowed in this experiment.

Policies:

- P0 anchor;
- P1 raw inventory;
- P2 observation maturity;
- P3 correction magnitude;
- P4 data quality;
- P5 combined reliability.

Stage-2 advancement requires all of:

- positive uplift overall, 24–48h and 48–72h;
- >=50% retained raw uplift in every view;
- >=25% reduction of overall worst-event degradation;
- >=25% reduction of 48–72h worst-event degradation;
- >=25% reduction of absolute bias;
- positive historical uplift on both already-exposed temporal subsets.

If no policy passes:

`RAW_INVENTORY_RETAINED_NO_STAGE2_POLICY_PASSED`

Do not loosen thresholds on the same evidence.

---

# Prospective evidence classes

Track-A cutoff:

`2026-10-19T19:11:01Z`

- `DELAYED_LABEL_HOLDOUT`: diagnostic only;
- `TRUE_POST_FREEZE_PROSPECTIVE`: genuine forward-promotion evidence.

Track-A prospective scoring continues independently of Track-B long72 R&D.

---

# Immediate development decision

> **Keep v2/Ridge/P2 frozen for Track-A evidence. Keep v3 sealed as a research anchor. Final24 v2/v3 is closed as equivalent. Long72 Stage 1 found a real but unstable inventory signal; run the predeclared Stage-2 reliability/tail gates now without reopening the model zoo or changing production.**
