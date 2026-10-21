# Beyond Ticketing — Demand Forecast Development Plan v2

Last updated: **2026-10-21**

Status: **CANONICAL ACCURACY ROADMAP / LONG72 HISTORICAL PACKAGE SEALED / FORWARD EVIDENCE NEXT**

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Mandatory rules:

1. frozen evidence packages are immutable;
2. R&D does not wait for prospective sample-count gates when honest research can run now;
3. a failed challenger closes the challenger, not the workstream;
4. historical success is not prospective evidence;
5. future outcomes never retune an already-frozen package in place.

---

# 1. Parallel tracks

## Track A — frozen validation / promotion evidence

Current stack:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Purpose:

- delayed-label diagnostics;
- true post-freeze prospective evidence;
- eventual production-promotion evidence.

Track A remains unchanged.

## Track B — active accuracy R&D

Pre-Live research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Frozen early-live historical package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Active next work:

`long72 forward scoring without retuning`

> **Production promotion waits for prospective evidence. R&D does not.**

---

# 2. Track-A frozen v2

Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Final24 d2 package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Final24 expert:

`ridge-a10`

Production:

`live_adjustment = 0`

Do not mutate this stack from new outcomes.

---

# 3. Pre-Live v3 historical R&D — COMPLETE AND SEALED

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Exact package:

| Horizon | Historical base | current-season regime |
|---|---|---|
| T-30 | `0.75 current a2 + 0.25 XGBoost depth3` | `NO_ADJUSTMENT` |
| T-14 | exact v2 | `NO_ADJUSTMENT` |
| T-7 | `0.25 HGB + 0.25 CatBoost d4 + 0.50 LightGBM leaves15` | `ewma50-resid-k4-cap05-min2` |
| T-3 | exact v2 | `ewma50-resid-k2-cap05-min3` |
| T-1 | exact v2 | `ewma50-resid-k6-cap05-min3` |

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

20-cell mean MAE:

`1934.04 -> 1924.64`

Improvement:

`+9.39 / +0.49%`

V3 remains research-only because evidence is historical/exposed and aggregate gain is modest.

---

# 4. Final24 v2/v3 — CLOSED AS EXACTLY EQUIVALENT

Canonical result:

`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`

Run:

`39636749440`

Maximum v3-v2 final24 anchor delta:

`0.0 seats`

Reason:

- final24 updater uses T-1;
- v3 T-1 is exactly the v2 T-1 package.

Consequences:

- no new final24 target;
- no cosmetic final24 Ridge retrain;
- no final24 P2 reselection solely because v3 exists.

This closed the old `d2-v3 final24 rebuild` idea and redirected R&D to earlier live windows.

---

# 5. Long-horizon live data foundation — COMPLETE

Additive research export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Existing final24 export:

`v7-final24`

remains unchanged.

Coverage audit:

- 14 eligible labeled events;
- 13 with usable data beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Frozen learned-model threshold:

`N = 9 independent events`

Decision:

- learn in 24–72h now;
- keep 72–168h diagnostic-only until N>=9.

Frozen long72 dataset:

- run `39640723942`;
- artifact `12365352293`;
- dataset SHA256 `2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`;
- 14 events / 130 rows.

Checkpoint hold:

- `0<h<=24` -> T-1;
- `24<h<=72` -> T-3;
- future checkpoint use forbidden.

---

# 6. Long72 Stage 1 — COMPLETE

Canonical result:

`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`

Run:

`39642620259`

Historical research lead:

`inventory-linear-extrapolation`

Scope:

`24<h<=72`

Event-level LOEO result:

- anchor MAE `3707.14`;
- raw inventory MAE `3254.68`;
- improvement `+452.46 / +12.21%`;
- 24–48h uplift `+675.33 / +18.22%`;
- 48–72h uplift `+675.68 / +14.71%`.

But raw inventory had unacceptable instability for sealing by itself:

- event improvement rate `46.15%`;
- bias `+1458.93 seats`;
- worst overall degradation `3100.60 seats`;
- worst 48–72h degradation `3741.79 seats`;
- original exposed subset `-485.52 MAE`.

Stage 1 therefore froze the expert for Stage 2 but did not create a forward package.

---

# 7. Long72 Stage 2 — COMPLETE / POLICY SELECTED

Canonical result:

`ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`

Run:

`39644319080`

Artifact:

`12366826274`

Decision:

`STAGE2_RELIABILITY_POLICY_SELECTED`

Selected policy:

`P2-observation-maturity`

Frozen expert remains:

`inventory-linear-extrapolation`

No Stage-1 retraining occurred.

## P2 historical metrics

Overall 24–72h:

- anchor MAE `3707.14`;
- P2 MAE `3012.63`;
- uplift `+694.51 / +18.73%`;
- event improvement rate `61.54%`;
- bias `+917.05 seats`;
- worst event degradation `1488.34 seats`.

24–48h:

- P2 MAE `2752.56`;
- uplift `+954.58 / +25.75%`.

48–72h:

- P2 MAE `3927.67`;
- uplift `+664.71 / +14.47%`;
- event improvement rate `70%`;
- worst degradation `2413.28 seats`.

Versus raw inventory:

- another `242.05 seats` lower overall MAE;
- worst-event degradation reduced `52.00%`;
- absolute bias reduced `37.14%`.

Historical exposed stability:

- original subset `+103.55 MAE`;
- later subset `+1640.04 MAE`.

P2 therefore passes the full predeclared Stage-2 gate set.

---

# 8. Long72 historical package — SEALED

Package ID:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

Status:

`FROZEN_HISTORICAL_RESEARCH_PACKAGE`

Package scope:

`24<h<=72`

Package formula:

`T-3 anchor + P2 reliability * inventory-linear-extrapolation delta`

Observation weights:

- first observation `0.25`;
- second `0.60`;
- third and later `1.00`.

Time weights:

- 60–72h `0.75`;
- 48–60h `0.90`;
- 24–48h `1.00`.

Final reliability:

`min(observation_weight, time_weight)`

Evidence class:

`EXPOSED_HISTORICAL_R_AND_D`

Production allowed:

`false`

Prospective evidence required:

`true`

---

# 9. Track-B priority 1 — LONG72 FORWARD SCORING — ACTIVE NEXT

Do not reopen the historical Stage-1/Stage-2 search on the same outcomes.

Create a forward-scoring contract for the sealed package.

## Required forward behavior

At every eligible `24<h<=72` as-of row:

1. obtain the PIT-safe T-3 anchor already valid at that timestamp;
2. compute the frozen inventory-linear-extrapolation proposed correction using only same-event data available at or before `as_of_at`;
3. apply exact sealed P2 reliability;
4. clip to physical `[0, capacity]` bounds;
5. persist forecast + package ID + manifest/hash + event/as-of/snapshot/capacity lineage;
6. do not use outcome attendance during prediction generation.

## Forward evidence classes

At minimum:

- `DELAYED_LABEL_DIAGNOSTIC`;
- `TRUE_POST_FREEZE_PROSPECTIVE`.

Only true post-freeze prospective events may count toward eventual promotion evidence.

## Forward scorecard

Report:

- 24–72h event-balanced MAE;
- 24–48h MAE;
- 48–72h MAE;
- bias;
- event improvement rate;
- worst event degradation;
- revision magnitude;
- package-vs-anchor and package-vs-final24 continuity where relevant.

Do not change the expert or P2 weights from scored forward outcomes.

If future evidence exposes a failure mode, open a new challenger/package ID.

---

# 10. Track-B priority 2 — 72–168h / T-7-aware R&D

The changed v3 T-7 anchor becomes materially relevant beyond the 72h learned boundary.

Reopen only when:

`independent events with valid >72h coverage >= 9`

Then build a separate versioned target/anchor experiment.

Do not mutate the sealed long72 package.

---

# 11. Track-A prospective validation continues

While Track-B forward scoring runs:

- continue scoring final24 v2/Ridge/P2 append-only;
- preserve delayed-label vs true prospective classes;
- do not mutate Track A from outcomes;
- repair truth/capacity/readiness blockers separately.

---

# 12. Context research — parallel

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

Forward PIT-safe collection may continue for rivalry, verified absences, sporting context, media/GDELT and valid hype/search/social signals.

Do not backfill final-state knowledge into historical training.

---

# 13. What waits and what does not

## Must wait

Only genuinely future evidence:

- future outcomes;
- future trajectories;
- forward-only context observations.

## Must not wait

- forward-scoring infrastructure;
- package lineage/sealing;
- PIT-safe feature work;
- CI/reproducibility work;
- context ingestion infrastructure;
- 72–168h readiness accumulation.

---

# 14. Promotion boundary

Neither Pre-Live v3 nor the long72 historical P2 package is production promotion evidence by itself.

Production requires materially more genuine prospective evidence, acceptable tail risk/bias, a reproducible frozen package and explicit reviewed activation.

Until then:

`live_adjustment = 0`

---

# 15. Immediate work order

1. **seal/verify `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`**;
2. build forward-scoring code/CI around the sealed package;
3. generate/persist predictions without outcome access;
4. accumulate forward evidence without retuning;
5. keep Track-A final24 validation running independently;
6. watch 72–168h coverage until N>=9;
7. continue PIT-safe context collection;
8. do not activate production.

## One-line rule

> **Long72 Stage 2 is complete and P2 is sealed historically. The active model-development task is forward scoring of the frozen 24–72h package without retuning; Track A remains frozen and production remains unchanged.**
