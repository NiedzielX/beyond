# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-21**

## Cold-start rule

Read in this order:

1. `ml/CURRENT_MODEL.md`;
2. `ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`;
3. `ml/D2_LONG72_STAGE2_RELIABILITY_GATING_V1.md`;
4. `ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`;
5. `ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`;
6. `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md`;
7. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
8. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
9. `ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`;
10. `ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`;
11. `ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`;
12. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
13. `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
14. `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
15. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
16. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

Run two tracks in parallel.

### Track A — frozen forward validation

Keep unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

### Track B — active R&D

Current historical early-live research lead:

`inventory-linear-extrapolation` for `24–72h`

Active experiment:

`d2-long72-stage2-reliability-gating-v1`

Core rule:

> **Production promotion waits for prospective evidence. R&D does not.**

---

# Pre-Live v3 — frozen research candidate

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Changed horizons only:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`, `NO_ADJUSTMENT`;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`, `ewma50-resid-k4-cap05-min2`.

T-14/T-3/T-1 are exact v2 horizon packages.

20-cell historical mean MAE:

`1934.04 -> 1924.64`, gain `+9.39 / +0.49%`.

V3 remains research-only.

---

# d2-v3 final24 equivalence — COMPLETE

Result:

`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`

Run:

`39636749440`

Artifact ID:

`12361203868`

Hard result:

- maximum v3-v2 final24 anchor-seat delta: **`0.0` seats**.

Because final24 uses T-1 and v3 T-1 equals v2 T-1 exactly:

- do not retrain/rename the same final24 Ridge/P2 problem solely because v3 exists;
- Track-A final24 remains valid as-is;
- active R&D moved earlier than 24h.

---

# Long-horizon data readiness — COMPLETE

Additive export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Existing:

`v7-final24`

remains untouched.

Coverage evidence:

- 14 eligible labeled events;
- 13 with usable data beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Inherited learned-model threshold:

`N = 9 independent events`

Decision:

- current maximum learned window = **72h**;
- 72–168h remains diagnostic-only.

---

# Frozen long72 data + anchor contract — COMPLETE

Result:

`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`

Run:

`39640723942`

Artifact ID:

`12365352293`

Frozen dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Dataset:

- 14 events;
- 130 PIT-safe rows;
- 0–24h: 50 rows;
- 24–48h: 45 rows;
- 48–72h: 35 rows.

Checkpoint hold:

- `0<h<=24` -> T-1;
- `24<h<=72` -> T-3;
- future checkpoint use forbidden.

V2 and v3 are numerically equivalent in this exact 0–72h anchor window because their T-3/T-1 packages are identical.

---

# Long72 Stage 1 — COMPLETE

Result:

`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`

Canonical run:

`39642620259`

Artifact ID:

`12365399256`

Predictions SHA256:

`33de331d2c3bf1e385f513c7fa7e28aa8b454a4d49cfe00d48163e6c083a6df5`

Research lead:

`inventory-linear-extrapolation`

Scope:

`24–72h`

Historical LOEO result:

- anchor MAE `3707.14`;
- inventory MAE `3254.68`;
- gain `+452.46 / +12.21%`.

Band gains:

- 24–48h: `+675.33 / +18.22%`;
- 48–72h: `+675.68 / +14.71%`.

Important limitations:

- event improvement rate only `46.15%`;
- bias `+1458.93 seats`;
- overall worst degradation `3100.60 seats`;
- 48–72h worst degradation `3741.79 seats`;
- original exposed subset worsens `-485.52 MAE`;
- later exposed subset improves `+1953.22 MAE`.

Therefore this is a **historical research lead only**.

---

# ACTIVE — Long72 Stage 2 reliability / tail gating

Contract:

`ml/D2_LONG72_STAGE2_RELIABILITY_GATING_V1.md`

Do not retrain Stage 1.

Pinned expert:

`inventory-linear-extrapolation`

Fixed policies:

- P0 anchor;
- P1 raw inventory;
- P2 observation maturity;
- P3 correction magnitude;
- P4 data quality;
- P5 combined reliability.

A new Stage-2 policy must simultaneously:

- keep positive uplift overall, 24–48h and 48–72h;
- retain >=50% raw uplift in all three views;
- reduce overall and 48–72h worst degradation >=25%;
- reduce absolute bias >=25%;
- be positive on both already-exposed temporal subsets.

If none passes, keep raw inventory only as the historical Stage-1 lead and move to a materially different reliability/target hypothesis. Do not loosen gates after seeing results.

---

# Track A remains unchanged

Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Final24 Stage-1 expert:

`ridge-a10`

Final24 Stage-2 policy:

`P2-observation-maturity`

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Do not mutate it from historical long72 research or prospective outcomes.

---

# Exposure rule

All long72 labels currently used for Stage 1 / Stage 2 are exposed historical R&D evidence.

Never call them unseen holdouts.

LOEO protects event independence but does not create temporal/prospective evidence.

---

# Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- v3 research-only;
- long72 research-only;
- production unchanged;
- `live_adjustment = 0`.

## One-line instruction

> **Stage 1 found a real 24–72h inventory signal. Do not reopen the model zoo. Run the frozen Stage-2 reliability gates now; preserve Track A and production unchanged.**
