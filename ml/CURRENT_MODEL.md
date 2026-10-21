# Beyond Ticketing — Current Model & Product State

Last updated: **2026-10-21**

Status: **TRACK-A FINAL24 FROZEN VALIDATION + TRACK-B PRE-LIVE V3 + FROZEN LONG72 RESEARCH PACKAGE**

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Production remains unchanged:

`live_adjustment = 0`

---

# Track A — frozen prospective-validation stack

Pre-Live anchor:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Final-24h live package:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Frozen d2 IDs:

- Stage-1 expert: `ridge-a10`;
- Stage-2 package: `d2-stage2-p2-observation-maturity-2026-10-19-v1`;
- policy: `P2-observation-maturity`.

Track A remains immutable while delayed-label and true post-freeze evidence accumulate.

---

# Track B — frozen Pre-Live v3 research anchor

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Only T-30 and T-7 differ from v2:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`, `NO_ADJUSTMENT`;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`, `ewma50-resid-k4-cap05-min2`.

T-14/T-3/T-1 are exact v2 horizon packages.

20-cell mean MAE:

`1934.04 -> 1924.64`, improvement `+9.39 / +0.49%`.

V3 remains research-only.

---

# Final-24h v2/v3 equivalence — COMPLETE

Result:

`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`

Decision:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

On the frozen 9-event / 30-row final24 replay:

- maximum v3-v2 anchor-seat delta = `0.0`;
- the live residual target is numerically unchanged.

Therefore the final24 Ridge/P2 package is not retrained or renamed solely because v3 exists.

---

# Long-horizon live data contract — FROZEN

Coverage audit:

`ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`

Additive export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Data readiness:

- 14 eligible labeled events;
- 240 PIT-safe 6h rows in final 168h;
- 13 events with data beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Inherited minimum independent-event floor:

`N = 9`

Decision:

- first learned early-live window = **72h**;
- 72–168h remains diagnostic-only.

Frozen long72 dataset/anchor result:

`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`

Frozen dataset:

- 14 events / 130 rows;
- 0–24h: 50 rows / 14 events;
- 24–48h: 45 rows / 13 events;
- 48–72h: 35 rows / 10 events.

Dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Checkpoint-hold anchor:

- `0<h<=24` -> T-1;
- `24<h<=72` -> T-3;
- no future checkpoint use.

Because v3 T-3/T-1 equal v2, the long72 anchor is valid for both freezes.

---

# Long72 Stage 1 — COMPLETE

Result:

`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`

Frozen scope:

`24 < hours_to_kickoff <= 72`

Selection data:

- 80 rows;
- 13 independent events;
- LOEO by event;
- event-balanced evaluation;
- correction cap `±0.10` occupancy.

Research lead:

`inventory-linear-extrapolation`

Headline development result:

- anchor MAE: `3707.14`;
- raw inventory MAE: `3254.68`;
- uplift: `+452.46 / +12.21%`.

Raw Stage-1 lead had unacceptable instability:

- worst event degradation: `3100.60`;
- bias: `+1458.93`;
- original exposed subset: `-485.52 MAE` versus anchor;
- later exposed subset: `+1953.22 MAE`.

Therefore Stage 1 was not frozen alone.

---

# Long72 Stage 2 — FROZEN RESEARCH PACKAGE

Package ID:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

Result:

`ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`

Stage-2 run:

`39644319080`

Artifact ID:

`12366826274`

Exact package:

1. scope: `24<h<=72`;
2. anchor: frozen T-3 checkpoint hold;
3. Stage-1 expert: `inventory-linear-extrapolation`;
4. Stage-1 cap: `±0.10` occupancy;
5. Stage-2 policy: `P2-observation-maturity`.

P2 reliability:

- observation #1 -> `0.25`;
- observation #2 -> `0.60`;
- observation #3+ -> `1.00`;
- `60<h<=72` time weight `0.75`;
- `48<h<=60` time weight `0.90`;
- `24<h<=48` time weight `1.00`;
- applied reliability = minimum of observation and time weights.

## Development performance

### Overall 24–72h

- anchor MAE: **3707.14**;
- frozen P2 package MAE: **3012.63**;
- improvement: **+694.51 / +18.73%**;
- event improvement rate: **61.54%**;
- worst event degradation: **1488.34**;
- bias: **+917.05**.

### 24–48h

- MAE: **2752.56**;
- improvement vs anchor: **+954.58 / +25.75%**.

### 48–72h

- MAE: **3927.67**;
- improvement vs anchor: **+664.71 / +14.47%**;
- event improvement rate: **70%**;
- worst event degradation: **2413.28**.

### Historical stability diagnostics

Original exposed subset:

`+103.55 MAE improvement`

Later exposed subset:

`+1640.04 MAE improvement`

Both are exposed historical development evidence, not unseen validation.

P2 passed all frozen Stage-2 gates for uplift, band consistency, retained value, bias reduction, tail reduction and both temporal subsets.

`P4-data-quality` remains a notable lower-tail-risk alternative, but was not substituted post hoc because the frozen selector ranked eligible policies by overall MAE first.

---

# Active next evidence — prospective long72 scoring

Do **not** retune the frozen long72 package on the same 13 events.

Next work:

1. score `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1` append-only on newly completed events with valid 24–72h trajectories;
2. keep all post-freeze outcomes out of package tuning;
3. persist anchor, raw inventory and frozen P2 forecasts before/independently of the final label where possible;
4. report aggregate MAE, bias, event improvement rate and worst degradation;
5. keep 72–168h diagnostic-only until it reaches `N>=9` independent events.

Track A final24 validation continues in parallel.

---

# Immediate decision

> **Final24 v2/Ridge/P2 remains frozen in Track A. Pre-Live v3 remains a frozen research anchor. The early-live 24–72h research package is now frozen as inventory extrapolation + P2 observation maturity. Active work moves to honest prospective scoring; production remains unchanged.**
