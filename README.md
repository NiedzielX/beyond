# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — canonical current forecasting state;
3. [`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`](ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md) — current early-live research lead and limitations;
4. [`ml/D2_LONG72_STAGE2_RELIABILITY_GATING_V1.md`](ml/D2_LONG72_STAGE2_RELIABILITY_GATING_V1.md) — active predeclared long72 Stage-2 contract;
5. [`ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`](ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md) — immutable 0–72h dataset/anchor contract;
6. [`ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`](ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md) — why 72h is the current learned window;
7. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — canonical two-track roadmap;
8. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — accuracy-first development rules;
9. [`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`](ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md) — proof that final24 v2/v3 is unchanged;
10. [`ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`](ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md) — sealed Pre-Live v3 research candidate;
11. [`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json) — immutable v3 lineage;
12. [`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json) — Track-A v2 lineage;
13. [`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`](ml/D2_PROSPECTIVE_ACCUMULATION_V1.md) — Track-A prospective evidence contract;
14. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Mandatory two-track rule

### Track A — frozen validation

Keep unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

This remains the forward/prospective evidence stack.

### Track B — active R&D

Pre-Live v3 remains sealed as research-only.

The active problem is now **early live 24–72h**, not another cosmetic final24 retrain.

Current historical research lead:

`inventory-linear-extrapolation`

Active next experiment:

`d2-long72-stage2-reliability-gating-v1`

> **Production promotion waits for prospective evidence. R&D does not.**

## Production boundary

Production remains:

`live_adjustment = 0`

No research result below is automatic production activation.

## Pre-Live v3 — sealed research candidate

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

V3 changes only:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`, `NO_ADJUSTMENT`;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`, `ewma50-resid-k4-cap05-min2`.

T-14/T-3/T-1 remain exact Frozen-v2 horizon packages.

20-cell historical mean MAE:

`1934.04 -> 1924.64`, gain `+9.39 / +0.49%`.

V3 is a frozen research candidate, not a Track-A or production replacement.

## Final24 v2/v3 — closed as equivalent

Canonical result:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Main evidence:

- run `39636749440`;
- artifact `12361203868`;
- maximum v3-v2 anchor-seat delta: **0.0 seats** on the frozen 30-row final24 development set.

Because the final24 updater uses T-1 and v3 T-1 is exactly v2 T-1:

- no new final24 target was needed;
- no Stage-1 retrain was needed solely because of v3;
- no P2 reselection was needed solely because of v3.

## Long-horizon live — data and anchor contract complete

Additive research export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Existing `v7-final24` remains unchanged.

Coverage audit:

- 14 eligible labeled events;
- 13 with usable rows beyond 24h;
- 10 beyond 48h;
- 8 beyond 72h.

Inherited independent-event floor:

`N = 9`

Decision:

- **72h is the longest learned window currently supported**;
- 72–168h stays diagnostic-only until independent-event coverage reaches the threshold.

Frozen long72 artifact:

- run `39640723942`;
- artifact `12365352293`;
- dataset SHA256 `2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`;
- 14 events / 130 rows.

Checkpoint-hold anchor:

- `0<h<=24` -> T-1;
- `24<h<=72` -> T-3;
- future checkpoint use forbidden.

## Long72 Stage 1 — complete

Canonical main run:

`39642620259`

Artifact ID:

`12365399256`

Research lead:

`inventory-linear-extrapolation`

### 24–72h result

- anchor MAE: `3707.14`;
- inventory MAE: `3254.68`;
- improvement: `+452.46 seats / +12.21%`.

### 24–48h

- improvement: `+675.33 / +18.22%`.

### 48–72h

- anchor MAE: `4592.38`;
- inventory MAE: `3916.71`;
- improvement: `+675.68 / +14.71%`.

The signal is real, but the raw rule is not promotion-ready:

- overall event improvement rate only `46.15%`;
- positive bias `+1458.93 seats`;
- overall worst event degradation `3100.60 seats`;
- 48–72h worst degradation `3741.79 seats`;
- original exposed historical subset gets worse (`-485.52 MAE`), while later exposed subset improves strongly (`+1953.22`).

Therefore Stage 1 closes with a **historical research lead**, not a frozen production candidate.

## Active next — Long72 Stage 2

Contract:

`ml/D2_LONG72_STAGE2_RELIABILITY_GATING_V1.md`

Keep the Stage-1 inventory rule fixed. Test only six bounded causal policies:

- P0 anchor;
- P1 raw inventory;
- P2 observation maturity;
- P3 correction magnitude;
- P4 data quality;
- P5 combined reliability.

A new Stage-2 policy must simultaneously:

- improve anchor overall and in both 24–48h / 48–72h bands;
- retain >=50% of raw uplift in every view;
- reduce overall and 48–72h worst degradation by >=25%;
- reduce absolute bias by >=25%;
- be positive on both already-exposed temporal subsets.

If none passes, do **not** lower gates. Retain raw inventory only as the historical Stage-1 lead and move to a materially different reliability/target hypothesis.

## Track-A frozen v2/d2

Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Frozen live expert:

`ridge-a10`

Frozen reliability policy:

`P2-observation-maturity`

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Track A continues prospective validation independently of Track-B R&D.

## Engineering rule

`code -> tests -> CI -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects evidence integrity. It does not pause model development.**
