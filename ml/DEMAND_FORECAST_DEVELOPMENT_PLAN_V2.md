# Beyond Ticketing — Demand Forecast Development Plan v2

Last updated: **2026-10-21**

Status: **CANONICAL ACCURACY ROADMAP**

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Rules:

1. frozen evidence packages are immutable;
2. exposed historical evidence must stay labeled exposed;
3. a failed challenger closes the challenger, not the workstream;
4. production promotion waits for genuine forward evidence;
5. production remains `live_adjustment = 0` until explicit reviewed activation.

---

# 1. Track A — frozen final24 prospective validation

Current package:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Pre-Live freeze:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Final24 live package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Purpose:

- delayed-label diagnostics;
- true post-freeze prospective scoring;
- eventual promotion evidence.

Do not tune Track A from new outcomes.

---

# 2. Track B — Pre-Live v3 research anchor

Freeze:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Only T-30 and T-7 change from v2.

20-cell mean historical MAE:

`1934.04 -> 1924.64`, improvement `+9.39 / +0.49%`.

V3 remains research-only.

Final24 v2/v3 anchor equivalence is proven exactly, so do not rerun a cosmetic final24 model cycle.

---

# 3. Long-horizon live R&D — COMPLETE THROUGH STAGE 2

## Data contract

Additive export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Coverage evidence:

- 14 eligible labeled events;
- 240 PIT-safe rows in final 168h;
- 13 events beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Inherited independent-event floor:

`N=9`

Therefore:

- first learned window = final **72h**;
- 72–168h = diagnostic-only for now.

## Frozen long72 anchor/data contract

Result:

`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`

Dataset:

- 14 events / 130 rows in 0–72h;
- 24–72h modeling slice: 80 rows / 13 events;
- 48–72h: 35 rows / 10 events.

Anchor rule:

- 0–24h -> T-1;
- 24–72h -> T-3;
- no future checkpoint use.

Dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

## Stage 1 — early-live expert

Result:

`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`

Research lead:

`inventory-linear-extrapolation`

Development:

- anchor MAE `3707.14`;
- raw expert MAE `3254.68`;
- uplift `+452.46 / +12.21%`.

Raw expert had high bias/tail and temporal heterogeneity, so it was not frozen alone.

## Stage 2 — reliability/tail governance

Result:

`ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`

Frozen research package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

Composition:

- scope `24<h<=72`;
- T-3 frozen checkpoint anchor;
- Stage-1 inventory linear extrapolation;
- Stage-1 cap `±0.10` occupancy;
- Stage-2 `P2-observation-maturity` reliability.

Development performance:

- MAE `3707.14 -> 3012.63`;
- uplift `+694.51 / +18.73%`;
- 24–48h uplift `+954.58 / +25.75%`;
- 48–72h uplift `+664.71 / +14.47%`;
- worst degradation `1488.34`;
- bias `+917.05`;
- original exposed subset uplift `+103.55`;
- later exposed subset uplift `+1640.04`.

All Stage-2 gates passed.

P4 data-quality remains a lower-tail-risk alternate but is not substituted because the frozen selector ranked eligible policies by overall MAE first.

---

# 4. Active priority — prospective long72 scoring

Do **not** run further same-sample policy tuning on the frozen 13-event Stage-2 evidence.

Build append-only prospective evidence for:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

For every newly completed eligible event with 24–72h PIT trajectory, preserve:

1. event identity and kickoff;
2. exact frozen T-3 anchor;
3. raw inventory correction/forecast;
4. frozen P2 reliability and forecast;
5. input snapshot/as-of lineage;
6. final attendance only when available;
7. evidence class and whether forecast state existed before label exposure.

Score:

- event-balanced MAE;
- 24–48h and 48–72h bands;
- bias;
- event improvement rate;
- worst event degradation;
- revision magnitude.

Do not mutate the package from these outcomes.

---

# 5. 72–168h expansion

Keep the 72–168h band diagnostic-only until independent valid-event coverage reaches the predeclared floor:

`N >= 9`

When it does:

1. freeze exact event/as-of identities;
2. define a PIT-safe anchor transition involving T-7;
3. evaluate without reusing future checkpoints;
4. create a new model/package ID if any target/anchor semantics change.

Do not lower the threshold to accelerate T-7 modeling.

---

# 6. Context research — parallel

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

Forward PIT-safe context collection can continue for verified rivalry, absences, sporting state, media/GDELT and valid hype/search/social signals.

Do not backfill final-state knowledge.

---

# 7. Promotion boundary

Neither Pre-Live v3 nor the long72 P2 package is production-ready from historical LOEO evidence alone.

Promotion requires materially more genuine prospective evidence, acceptable tail/bias behavior, frozen reproducible lineage and explicit reviewed activation.

Until then:

`live_adjustment = 0`

## Immediate work order

1. **freeze and use the long72 P2 package exactly as specified**;
2. build append-only prospective long72 scoring;
3. continue final24 Track-A scoring independently;
4. leave 72–168h diagnostic until `N>=9`;
5. continue PIT-safe context collection;
6. do not activate production.
