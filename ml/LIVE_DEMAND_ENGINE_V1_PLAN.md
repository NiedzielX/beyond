# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-21**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector / Price-area Decision Support MVP: IMPLEMENTED**  
> **Pre-Live v2 historical candidate: FROZEN + SEALED / TRACK A**  
> **final24 d2 Stage 1: DONE / ridge-a10 FROZEN**  
> **final24 d2 Stage 2: DONE / P2-observation-maturity FROZEN**  
> **final24 prospective validation: ACTIVE / TRACK A**  
> **Pre-Live v3 historical research candidate: FROZEN + SEALED / TRACK B**  
> **final24 v2/v3 equivalence: PROVEN / CLOSED**  
> **long72 data + anchor: FROZEN**  
> **long72 Stage 1: DONE / inventory-linear-extrapolation**  
> **long72 Stage 2: DONE / P2-observation-maturity SELECTED**  
> **long72 historical research package: SEALED**  
> **long72 forward scoring: ACTIVE NEXT**

Canonical documents:

- `ml/CURRENT_MODEL.md`;
- `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
- `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md`;
- `ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`;
- `ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`;
- `ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`;
- `ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`;
- `ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`;
- `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
- `AI_BOOTSTRAP.md`.

## Two-track rule

### Track A — frozen final24 validation

Keep:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Score new outcomes append-only. Do not mutate from outcomes.

### Track B — active model R&D

Pre-Live v3 remains a research anchor.

Current sealed historical early-live package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Active next work:

`forward scoring without retuning`

> **Production promotion waits for prospective evidence. R&D does not.**

## Production boundary

Production remains:

`live_adjustment = 0`

Structural Prior remains production incumbent.

Neither Track-A frozen validation nor Track-B historical package is automatic activation.

---

# Track A — frozen final24 v2 stack

Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Stage-1 expert:

`ridge-a10`

Stage-2 policy:

`P2-observation-maturity`

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + P2_final24(t) * ridge_delta(t)`

This remains Track-A prospective benchmark.

---

# Track B — frozen Pre-Live v3 research anchor

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Changed horizons:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`, `NO_ADJUSTMENT`;
- T-7: `0.25 HGB + 0.25 CatBoost d4 + 0.50 LightGBM leaves15`, `ewma50-resid-k4-cap05-min2`.

T-14/T-3/T-1 are exact v2 packages.

This matters because long72 currently uses T-3 and final24 uses T-1, so both are v2/v3 equivalent inside their current live windows.

---

# Final24 v2/v3 equivalence — COMPLETE

Run:

`39636749440`

Decision:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Maximum anchor delta:

`0.0 seats`

Therefore no cosmetic final24 retraining occurred.

---

# Long72 foundation — COMPLETE

Research export:

`v8-long168`

Coverage:

- 13 events beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Frozen learned threshold:

`N = 9`

Therefore learned window:

`24–72h`

72–168h remains diagnostic-only.

Frozen long72 dataset:

- run `39640723942`;
- artifact `12365352293`;
- SHA `2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`;
- 14 events / 130 PIT-safe rows.

Anchor:

`T-3 checkpoint hold for 24–72h`

No future checkpoint interpolation.

---

# Long72 Stage 1 — COMPLETE

Run:

`39642620259`

Research expert:

`inventory-linear-extrapolation`

Overall 24–72h:

- anchor MAE `3707.14`;
- raw inventory MAE `3254.68`;
- uplift `+452.46 / +12.21%`.

But raw expert had high bias/tail risk and historical-subset heterogeneity.

Stage 1 expert was therefore frozen for reliability testing, not forward use by itself.

---

# Long72 Stage 2 — COMPLETE

Run:

`39644319080`

Artifact:

`12366826274`

Decision:

`STAGE2_RELIABILITY_POLICY_SELECTED`

Selected:

`P2-observation-maturity`

Exact policy:

Observation maturity:

- first row `0.25`;
- second `0.60`;
- third+ `1.00`.

Time maturity:

- 60–72h `0.75`;
- 48–60h `0.90`;
- 24–48h `1.00`.

Reliability:

`min(observation_weight, time_weight)`

Architecture:

`long72_forecast(t) = frozen_T3_anchor + P2_long72(t) * inventory_extrapolation_delta(t)`

## Historical metrics

Overall 24–72h:

- P2 MAE `3012.63`;
- uplift vs anchor `+694.51 / +18.73%`;
- event improvement rate `61.54%`;
- bias `+917.05`;
- worst degradation `1488.34`.

24–48h:

- uplift `+954.58 / +25.75%`.

48–72h:

- uplift `+664.71 / +14.47%`;
- event improvement rate `70%`.

Compared with raw inventory:

- MAE improves by another `242.05 seats`;
- worst degradation falls `52.00%`;
- absolute bias falls `37.14%`.

Both historical exposed subsets become positive.

---

# Long72 historical package — SEALED

Package ID:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

Status:

`FROZEN_HISTORICAL_RESEARCH_PACKAGE`

Evidence class:

`EXPOSED_HISTORICAL_R_AND_D`

Production allowed:

`false`

Prospective evidence required:

`true`

---

# Active next — long72 forward scoring

Build a separate scorer around the sealed package.

For every eligible `24<h<=72` row:

1. use PIT-safe T-3 anchor;
2. use only same-event inventory observations available by row `as_of_at`;
3. compute exact frozen inventory extrapolation correction;
4. apply exact frozen P2 long72 reliability;
5. clip forecast to `[0, capacity]`;
6. persist package ID, event/as-of/snapshot/anchor/capacity lineage;
7. create prediction without outcome access;
8. score only later when trusted outcome is available.

Evidence classes must separate:

- delayed-label diagnostic;
- true post-package-freeze prospective.

Future outcomes may trigger a new challenger ID, but may not mutate the frozen package.

---

# 72–168h / T-7-aware branch

Do not learn this band yet.

Reopen only when:

`independent events with >72h valid coverage >= 9`

Then create a separate package/target using the T-7-aware anchor. Do not extend the current long72 package in place.

---

# Track-A prospective validation continues

For each new completed final24 event, preserve:

- Structural base;
- Frozen Pre-Live v2;
- raw frozen Ridge;
- frozen final24 P2;
- evidence class.

Never use Track-A outcomes to mutate the frozen final24 package.

---

# Engineering rule

`code -> tests -> CI -> pinned inputs -> machine JSON -> artifact/hash -> result doc -> decision -> canonical docs`

## One-line rule

> **The historical 24–72h package is now T-3 + inventory extrapolation + P2 maturity. Freeze it, forward-score it without retuning, keep final24 Track A separate, and leave production at live_adjustment=0.**
