# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-21**

## Cold-start rule

Read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
2. `ml/CURRENT_MODEL.md`;
3. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
4. `ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`;
5. `ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`;
6. `ml/results/PRE_LIVE_V3_FIXED_TEMPORAL_PACKAGE_V1_2026-10-21.md`;
7. `ml/results/PRE_LIVE_V3_REGIME_REVALIDATION_V1_2026-10-21.md`;
8. `ml/results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md`;
9. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
10. `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
11. `ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`;
12. `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
13. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
14. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
15. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

Run two tracks in parallel.

### Track A — frozen forward validation

Keep unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

This is the current append-only prospective evidence stack.

### Track B — active accuracy R&D

Pre-Live v3 is now sealed as a historical research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Active next work:

> **d2-v3 — rebuild/revalidate the live updater against Frozen Pre-Live v3 under a new target/model/policy version.**

Core rule:

> **Production promotion waits for prospective evidence. R&D does not.**

---

# Pre-Live v3 — FROZEN RESEARCH CANDIDATE

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Seal run:

`39633561065`

Artifact ID:

`12360033160`

Result:

`ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`

Exact changed horizons:

### T-30

`0.75 current a2 + 0.25 XGBoost depth3`

Regime:

`NO_ADJUSTMENT`

Reference mean MAE:

`1825.49`

### T-7

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Regime:

`ewma50-resid-k4-cap05-min2`

Reference mean MAE:

`1670.60`

T-14/T-3/T-1 retain exact v2 horizon packages.

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

## v3 package evidence

20-cell mean MAE:

- v2 `1934.04`;
- v3 `1924.64`;
- gain `+9.39 / +0.49%`.

T-30 rolling gains vs v2:

`+5.98 / +33.50 / +54.93 / +29.74`

T-7 rolling gains:

`+10.92 / +11.18 / +13.71 / +27.88`

Important caveat:

- gain is modest;
- exposed historical refs remain exposed;
- event-level tail risk remains material;
- v3 is not production and does not replace Track-A v2.

---

# Why T-1 is not in v3

Its historical ensemble passed the earlier anchor-only robustness test, but the full anchor+regime package was mixed vs Frozen v2:

- 2024/25 `+1.92`;
- 2025/26 `-15.39`.

Therefore v3 retains exact v2 T-1.

---

# Track A frozen v2 + d2

Pre-Live v2 ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Stage-1 expert:

`ridge-a10`

Stage-2 policy:

`P2-observation-maturity`

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Do not mutate this stack from prospective outcomes.

Do not attach this Ridge/P2 package to v3.

---

# Active next — d2-v3

The new live cycle must start from the changed anchor, not from old residual labels.

Required work order:

1. reproduce v3 anchors on the frozen 9-event / 30-row d2 development set;
2. create new live residual targets relative to v3;
3. preserve event-level LOEO / no random snapshot split;
4. compare against both v3-zero-correction and frozen v2/Ridge/P2 benchmark;
5. test a compact set of materially different experts, not an open-ended model zoo;
6. reselect/revalidate reliability and tail governance under new IDs;
7. keep prospective events honestly exposed;
8. no production write.

If the old Ridge remains best under the new target, that still requires a new d2-v3 model identity because the anchor/target changed.

TSFM may only re-enter through a materially different predeclared hypothesis, not same-data rescue tuning.

---

# Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- v3 research-only;
- production unchanged;
- `live_adjustment = 0`.

## One-line instruction

> **Pre-Live v3 is sealed. Keep v2/Ridge/P2 frozen for Track-A evidence and immediately start d2-v3 reconstruction/tournament work against the new v3 anchor under a new version.**
