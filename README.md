# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — canonical current forecasting state;
3. [`ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`](ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md) — selected long72 historical reliability package;
4. [`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`](ml/artifacts/d2_long72_stage2_p2_v1/manifest.json) — immutable long72 P2 research-package lineage;
5. [`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`](ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md) — early-live Stage-1 research lead;
6. [`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`](ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md) — immutable 0–72h dataset/anchor contract;
7. [`ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`](ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md) — why 72h is the current learned window;
8. [`ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md`](ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md) — long-horizon roadmap;
9. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — canonical two-track roadmap;
10. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — accuracy-first development rules;
11. [`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`](ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md) — proof that final24 v2/v3 is unchanged;
12. [`ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`](ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md) — sealed Pre-Live v3 research candidate;
13. [`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json) — immutable v3 lineage;
14. [`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json) — Track-A v2 lineage;
15. [`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`](ml/D2_PROSPECTIVE_ACCUMULATION_V1.md) — Track-A prospective contract;
16. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Mandatory two-track rule

### Track A — frozen validation

Keep unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

This remains the forward/prospective final24 evidence stack.

### Track B — active R&D

Pre-Live v3 remains sealed as research-only.

The current early-live historical package is:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Next Track-B work:

> **Forward-score this frozen 24–72h package on genuinely new eligible events without retuning.**

> **Production promotion waits for prospective evidence. R&D does not.**

## Production boundary

Production remains:

`live_adjustment = 0`

No historical research package below is automatic production activation.

---

## Pre-Live v3 — sealed research candidate

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

V3 changes only:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`, `NO_ADJUSTMENT`;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`, `ewma50-resid-k4-cap05-min2`.

T-14/T-3/T-1 remain exact Frozen-v2 packages.

Historical 20-cell mean MAE:

`1934.04 -> 1924.64`, gain `+9.39 / +0.49%`.

V3 is a frozen research candidate, not a Track-A or production replacement.

---

## Final24 v2/v3 — closed as exactly equivalent

Canonical decision:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Evidence:

- run `39636749440`;
- artifact `12361203868`;
- maximum v3-v2 anchor-seat delta: **`0.0 seats`** on all frozen final24 rows.

Because final24 uses T-1 and v3 T-1 is exactly v2 T-1:

- no new final24 target was required;
- no Stage-1 retrain was required solely because of v3;
- no final24 P2 reselection was required solely because of v3.

Track-A final24 therefore remains unchanged.

---

## Long-horizon data + anchor — complete

Additive research export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Existing:

`v7-final24`

remains untouched.

Coverage audit:

- 14 eligible labeled events;
- 13 with usable PIT rows beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Inherited independent-event floor:

`N = 9`

Decision:

- **72h is the longest current learned window**;
- 72–168h remains diagnostic-only until independent-event coverage reaches N>=9.

Frozen long72 evidence:

- run `39640723942`;
- artifact `12365352293`;
- dataset SHA256 `2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`;
- 14 events / 130 PIT-safe rows.

Checkpoint hold:

- `0<h<=24` -> T-1;
- `24<h<=72` -> T-3;
- future checkpoint use forbidden.

---

## Long72 Stage 1 — complete

Canonical run:

`39642620259`

Artifact ID:

`12365399256`

Historical research lead:

`inventory-linear-extrapolation`

24–72h:

- anchor MAE: `3707.14`;
- raw inventory MAE: `3254.68`;
- improvement: `+452.46 / +12.21%`.

24–48h:

- improvement: `+675.33 / +18.22%`.

48–72h:

- anchor MAE: `4592.38`;
- raw inventory MAE: `3916.71`;
- improvement: `+675.68 / +14.71%`.

But raw inventory had material risk:

- only `46.15%` of events improved overall;
- bias `+1458.93 seats`;
- worst overall degradation `3100.60 seats`;
- worst 48–72h degradation `3741.79 seats`;
- original exposed subset worsened by `485.52 MAE`.

Therefore Stage 1 produced a research lead, not a package ready for forward use.

---

## Long72 Stage 2 — complete and sealed historically

Canonical run:

`39644319080`

Artifact ID:

`12366826274`

Artifact ZIP SHA256:

`c750cf385b2c6b6f05fabceaf68ff323a66235862967900419be421f7cdcb4ae`

Decision:

`STAGE2_RELIABILITY_POLICY_SELECTED`

Selected policy:

`P2-observation-maturity`

Historical package ID:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

### P2 overall 24–72h

- anchor MAE: `3707.14`;
- P2 MAE: **`3012.63`**;
- improvement: **`+694.51 / +18.73%`**;
- event improvement rate: **`61.54%` = 8/13**;
- bias: **`+917.05 seats`**;
- worst event degradation: **`1488.34 seats`**.

Versus raw Stage 1:

- MAE improves by another `242.05 seats`;
- worst-event degradation drops by `52.00%`;
- absolute bias drops by `37.14%`.

### P2 24–48h

- MAE `2752.56`;
- improvement `+954.58 / +25.75%`.

### P2 48–72h

- MAE `3927.67`;
- improvement `+664.71 / +14.47%`;
- event improvement rate `70%`;
- worst-event degradation `2413.28 seats`.

### Historical stability

Original exposed subset:

- raw inventory: `-485.52 MAE`;
- P2: **`+103.55 MAE`**.

Later exposed subset:

- P2: **`+1640.04 MAE`**.

This is enough to seal a **historical research package**, but not enough for production because every selected/scored event is historical and already exposed.

---

## Active next — forward scoring without retuning

The next contract must apply the sealed package exactly:

`T-3 anchor + P2 reliability * frozen inventory-linear-extrapolation delta`

for `24<h<=72` only.

Rules:

1. do not alter Stage-1 extrapolation logic;
2. do not alter P2 weights after seeing future outcomes;
3. pin the package manifest and all artifact hashes;
4. create predictions before outcome labels are used for evaluation;
5. classify evidence explicitly as delayed-label diagnostic vs genuine post-freeze prospective evidence;
6. keep final24 Track-A Ridge/P2 separate and unchanged;
7. do not activate production.

Separately, reopen 72–168h / T-7-aware learned R&D only when the frozen N=9 independent-event threshold is met.

---

## Track-A frozen v2/d2

Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Final24 expert:

`ridge-a10`

Final24 reliability:

`P2-observation-maturity`

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

This package stays unchanged for prospective validation.

## Engineering rule

`code -> tests -> CI -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects evidence integrity. It does not pause model development.**
