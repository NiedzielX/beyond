# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-21**

Status: **FINAL24 TRACK-A FROZEN + LONG72 TRACK-B FROZEN RESEARCH PACKAGE + PROSPECTIVE SCORING NEXT**

## Production boundary

Production remains:

`live_adjustment = 0`

No package below is production activation.

---

# Track A — frozen final24 validation

Pre-Live anchor:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Frozen final24 live package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + P2_reliability(t) * ridge_a10_delta(t)`

Track A remains immutable while delayed-label and true post-freeze evidence accumulate.

---

# Track B — Pre-Live v3 research anchor

Freeze:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Only T-30 and T-7 differ from v2. T-3 and T-1 remain identical to v2.

Historical package improvement:

`1934.04 -> 1924.64` mean 20-cell MAE, `+0.49%`.

V3 remains research-only.

---

# Final24 v2/v3 equivalence — CLOSED

Result:

`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`

Decision:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

On the frozen 9-event / 30-row final24 replay:

- maximum anchor-seat delta: `0.0`;
- residual target unchanged.

Therefore final24 Ridge/P2 is not retrained or relabeled for v3.

---

# Long-horizon live data contract

Additive export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

The existing `v7-final24` route remains unchanged.

Coverage audit:

- 14 eligible labeled events;
- 240 PIT-safe rows in final 168h;
- 13 events beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Inherited independent-event floor:

`N = 9`

Decision:

- learned live window: final **72h**;
- 72–168h: diagnostic-only until `N>=9`.

---

# Frozen long72 data + anchor contract

Result:

`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`

Artifact ID:

`12365352293`

Dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Dataset:

- 14 events / 130 rows in 0–72h;
- 24–72h modeling slice: 80 rows / 13 events;
- 48–72h: 35 rows / 10 events.

Checkpoint hold:

- `0<h<=24` -> T-1;
- `24<h<=72` -> T-3;
- future checkpoint use forbidden.

Same-season b2 replay is horizon-specific. Historical home matches without a reconstructable checkpoint forecast remain explicitly unforecastable rather than receiving invented sporting state.

---

# Long72 Stage 1 — early-live expert

Result:

`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`

Scope:

`24<h<=72`

Validation:

- event-level LOEO;
- event-balanced;
- no random snapshot split;
- occupancy correction cap `±0.10`.

Research lead:

`inventory-linear-extrapolation`

Development:

- anchor MAE `3707.14`;
- raw expert MAE `3254.68`;
- uplift `+452.46 / +12.21%`.

Raw expert was not frozen alone because of high bias, tail degradation and strong temporal-subset heterogeneity.

---

# Long72 Stage 2 — frozen research package

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

Package:

1. scope `24<h<=72`;
2. T-3 checkpoint anchor;
3. Stage-1 expert `inventory-linear-extrapolation`;
4. raw correction cap `±0.10` occupancy;
5. Stage-2 reliability `P2-observation-maturity`.

P2 reliability:

- observation #1 -> `0.25`;
- observation #2 -> `0.60`;
- observation #3+ -> `1.00`;
- `60<h<=72` time weight `0.75`;
- `48<h<=60` time weight `0.90`;
- `24<h<=48` time weight `1.00`;
- applied reliability = minimum of observation and time weights.

Development metrics:

- overall anchor MAE `3707.14`;
- package MAE `3012.63`;
- uplift `+694.51 / +18.73%`;
- 24–48h uplift `+954.58 / +25.75%`;
- 48–72h uplift `+664.71 / +14.47%`;
- event improvement rate `61.54%`;
- worst event degradation `1488.34`;
- bias `+917.05`.

Historical exposed-subset diagnostics:

- original exposed subset: `+103.55` MAE improvement;
- later exposed subset: `+1640.04`.

P2 passed all predeclared Stage-2 gates.

`P4-data-quality` remains a lower-tail-risk alternative, but is not substituted post hoc because the frozen selector ranked eligible policies by overall MAE first.

---

# Active next — append-only prospective long72 scoring

Do not tune the frozen long72 package again on the same historical events.

For each newly completed eligible event with valid 24–72h PIT trajectory, preserve and score:

1. exact frozen T-3 anchor;
2. raw inventory extrapolation;
3. frozen P2 reliability and forecast;
4. source snapshot / as-of lineage;
5. final attendance only when available;
6. evidence class and whether forecast state existed before label exposure.

Report:

- event-balanced MAE;
- 24–48h MAE;
- 48–72h MAE;
- bias;
- event improvement rate;
- worst event degradation;
- revision magnitude.

Do not mutate the package from prospective outcomes.

---

# 72–168h boundary

Keep 72–168h diagnostic-only until independent-event coverage reaches:

`N >= 9`

Only then define a new PIT-safe anchor transition involving T-7 and create a separate model/package version.

---

# Immediate instruction

> **Keep final24 v2/Ridge/P2 frozen in Track A. Keep Pre-Live v3 and the long72 P2 package frozen as research assets. Active work moves to append-only prospective scoring of long72; production remains unchanged.**
