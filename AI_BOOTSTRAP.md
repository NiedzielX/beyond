# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-21**

## Cold-start rule

Read in this order:

1. `ml/CURRENT_MODEL.md`;
2. `ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`;
3. `ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`;
4. `ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`;
5. `ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`;
6. `ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`;
7. `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md`;
8. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
9. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
10. `ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`;
11. `ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`;
12. `ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`;
13. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
14. `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
15. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

Run two tracks in parallel.

### Track A — frozen forward validation

Keep unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

### Track B — active R&D

Frozen historical early-live package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Exact historical package:

`T-3 anchor + P2 observation-maturity reliability * inventory-linear-extrapolation delta`

for:

`24 < hours_to_kickoff <= 72`

Active next work:

> **Create forward scoring for the sealed long72 package and score genuinely new eligible events without retuning.**

Core rule:

> **Production promotion waits for prospective evidence. R&D does not.**

---

# Track-B historical package — SEALED

Package manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

Package ID:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Status:

`FROZEN_HISTORICAL_RESEARCH_PACKAGE`

Production allowed:

`false`

Prospective evidence required:

`true`

## Historical package evidence

Stage-2 run:

`39644319080`

Artifact ID:

`12366826274`

Artifact ZIP SHA256:

`c750cf385b2c6b6f05fabceaf68ff323a66235862967900419be421f7cdcb4ae`

Stage-2 JSON SHA256:

`a9daa834e15b4f313b15c3e809033b7d79e4ed4357f61a8f5071e6bf20359d8c`

Stage-2 predictions SHA256:

`489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b`

Selected policy:

`P2-observation-maturity`

### Overall 24–72h

- anchor MAE `3707.14`;
- raw Stage-1 inventory MAE `3254.68`;
- sealed P2 package MAE **`3012.63`**;
- improvement vs anchor **`+694.51 / +18.73%`**;
- event improvement rate **`61.54%`**;
- bias `+917.05 seats`;
- worst-event degradation `1488.34 seats`.

Compared with raw inventory:

- another `242.05 seats` lower MAE;
- `52.00%` lower worst-event degradation;
- `37.14%` lower absolute bias.

### 24–48h

- MAE `2752.56`;
- improvement `+954.58 / +25.75%`.

### 48–72h

- MAE `3927.67`;
- improvement `+664.71 / +14.47%`;
- event improvement rate `70%`;
- worst-event degradation `2413.28 seats`.

### Exposed historical stability

Original exposed subset:

`+103.55 MAE improvement`

Later exposed subset:

`+1640.04 MAE improvement`

Both are historical/exposed. Neither is prospective evidence.

---

# Exact P2 long72 policy

Frozen Stage-1 expert:

`inventory-linear-extrapolation`

Observation weight:

- first observation `0.25`;
- second `0.60`;
- third and later `1.00`.

Time weight:

- 60–72h `0.75`;
- 48–60h `0.90`;
- 24–48h `1.00`.

Reliability:

`min(observation_weight, time_weight)`

Do not change these weights from future outcomes.

---

# Final24 remains separate

Final24 v2/v3 equivalence is already proven:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Track-A final24 remains:

- Pre-Live v2;
- `ridge-a10`;
- final24 `P2-observation-maturity`;
- package `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

Do not silently combine, replace or retrain it from long72 historical results.

---

# 72–168h remains diagnostic-only

Coverage audit has only 8 independent events beyond 72h.

Frozen learned-model threshold:

`N = 9`

Do not lower it to open the T-7-aware learned window early.

When N>=9, reopen the 72–168h / Pre-Live-v3-T-7 problem under a new contract.

---

# Next work order

1. create a versioned forward-scoring contract for the sealed long72 package;
2. apply exact frozen expert + P2 logic without retuning;
3. persist prediction timestamp / as-of / event / package lineage before outcome scoring;
4. classify later evidence honestly as delayed-label diagnostic or true post-freeze prospective;
5. accumulate forward MAE, bias, tail and event-improvement evidence;
6. keep Track A running independently;
7. do not activate production.

# Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- Pre-Live v3 research-only;
- long72 P2 historical package research-only until forward evidence exists;
- production unchanged;
- `live_adjustment = 0`.

## One-line instruction

> **Long72 Stage 2 is complete: P2 observation maturity is sealed historically. Do not reopen the same model/policy search; build forward scoring now and test the frozen package on genuinely new events.**
