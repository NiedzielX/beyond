# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-21**

## Cold-start rule

Read in this order:

1. `ml/CURRENT_MODEL.md`;
2. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
3. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
4. `ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`;
5. `ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`;
6. `ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`;
7. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
8. `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
9. `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
10. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
11. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
12. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

Run two tracks in parallel.

### Track A — frozen forward validation

Keep unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

### Track B — active R&D

Sealed research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Final-24h equivalence is now proven:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Therefore **do not retrain/rename the same final-24h Ridge/P2 problem just because v3 has a new freeze ID**.

Active next work:

> **d2-long-horizon-live-v1 — add an earlier-than-24h live research export and evaluate live forecasting where changed v3 T-7 can actually matter.**

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

20-cell mean MAE:

`1934.04 -> 1924.64`, gain `+9.39 / +0.49%`.

V3 remains research-only.

---

# d2-v3 Stage 0 — COMPLETE

Result:

`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`

Run:

`39636749440`

Artifact ID:

`12361203868`

Exact frozen development set:

- 9 events;
- 30 final-24h rows;
- event IDs `1,3,4,8,9,12,13,14,17`.

Hard result:

- maximum v3-v2 anchor-seat delta: **`0.0` seats**.

Only floating serialization noise in derived values:

- target-attendance max delta `3.64e-12` seats;
- target-occupancy max delta `1.73e-16`.

Consequences:

- no new final-24h target is required;
- no Stage-1 retrain is required solely due to the v3 anchor;
- no P2 reselection is required solely due to the v3 anchor.

The current final-24h residual target is mathematically unchanged because both v2 and v3 use the exact same T-1 package.

---

# Earlier-than-24h live data — CONFIRMED

Direct Supabase PIT audit on the current C1-eligible labeled Ekstraklasa events shows:

- 14 labeled capacity-resolved events under the C1 event contract;
- 13/14 have valid PIT trajectory rows beyond 24h;
- 10/14 have valid rows beyond 48h;
- 8/14 have valid rows in 72–168h;
- several events have a near-full 7-day, 6-hour-bucket trajectory.

The current `v7-final24` RPC is the limiting contract, not data collection.

`get_live_trajectory_features_v1_1_asof` already validates PIT-safe earlier snapshots.

## Important exposure rule

Current later labeled events `5,11,15,18,19` are already exposed from prior diagnostics/readiness work. They may be used only under an explicitly declared new chronological research split and must never be called unseen holdouts.

---

# Active next — long-horizon data contract

Do not mutate `v7-final24`.

Create an additive research RPC/export with:

- up to 168h pre-kickoff window;
- 6h buckets;
- latest snapshot per event x bucket;
- same eligibility + capacity rules as v7;
- same PIT feature function;
- explicit coverage/missingness metadata.

Then decide whether the honest first modeling window is 48h, 72h or 168h based on independent event coverage.

No random snapshot split.

Event remains the independent unit.

---

# Track A remains unchanged

Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Stage-1 expert:

`ridge-a10`

Stage-2 policy:

`P2-observation-maturity`

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Do not mutate it from prospective outcomes.

---

# Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- v3 research-only;
- production unchanged;
- `live_adjustment = 0`.

## One-line instruction

> **Final-24h v2/v3 is exactly equivalent, so do not waste a cycle retraining the same target. Build the additive earlier-than-24h live export now and move Track-B R&D to a genuinely new long-horizon live problem.**
