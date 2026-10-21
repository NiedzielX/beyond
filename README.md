# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — current forecasting state;
3. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — canonical two-track roadmap;
4. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — accuracy-first development rules;
5. [`ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`](ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md) — sealed v3 research candidate result;
6. [`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json) — immutable v3 lineage;
7. [`ml/results/PRE_LIVE_V3_FIXED_TEMPORAL_PACKAGE_V1_2026-10-21.md`](ml/results/PRE_LIVE_V3_FIXED_TEMPORAL_PACKAGE_V1_2026-10-21.md) — package robustness evidence;
8. [`ml/results/PRE_LIVE_V3_REGIME_REVALIDATION_V1_2026-10-21.md`](ml/results/PRE_LIVE_V3_REGIME_REVALIDATION_V1_2026-10-21.md) — v3 regime revalidation;
9. [`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json) — Track-A v2 lineage;
10. [`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`](ml/D2_PROSPECTIVE_ACCUMULATION_V1.md) — Track-A prospective contract;
11. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — live-engine roadmap;
12. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Mandatory two-track rule

### Track A — frozen validation

Keep the current forward-evidence package unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

### Track B — active R&D

Pre-Live v3 is now sealed as a research-only historical/pre-live anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Active next work:

`d2-v3 — rebuild/revalidate the live updater against v3`

> **Production promotion waits for prospective evidence. R&D does not.**

## Production boundary

Production remains:

`live_adjustment = 0`

Neither v2 nor v3 research state is automatic production activation.

## Pre-Live v3 — sealed research candidate

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Freeze run:

`39633561065`

Artifact ID:

`12360033160`

Exact changed horizons:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`, `NO_ADJUSTMENT`;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`, `ewma50-resid-k4-cap05-min2`.

T-14/T-3/T-1 retain exact Frozen-v2 horizon packages.

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

## V3 package evidence

20-cell mean MAE:

- Frozen v2: `1934.04`;
- v3: `1924.64`;
- gain: `+9.39 / +0.49%`.

T-30 rolling gains vs v2:

`+5.98 / +33.50 / +54.93 / +29.74`

T-7 rolling gains:

`+10.92 / +11.18 / +13.71 / +27.88`

The gain is real but modest, references are historically exposed, and tail risk remains material. V3 is therefore a **frozen research candidate**, not production or Track-A replacement.

## Why T-1 did not enter v3

T-1 passed the earlier historical-anchor audit but failed package-level consistency against Frozen v2 after regime revalidation:

- 2024/25 `+1.92` MAE;
- 2025/26 `-15.39`.

V3 correctly retains exact v2 T-1.

## Track-A frozen v2/d2

Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Frozen live expert:

`ridge-a10`

Frozen reliability policy:

`P2-observation-maturity`

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

This stack stays unchanged for prospective validation.

## Active next — d2-v3

The live residual target changes when the pre-live anchor changes, so old Ridge/P2 cannot be silently attached to v3.

Immediate work:

1. reconstruct v3 anchors on the frozen d2 development rows;
2. define new d2-v3 live residual labels;
3. preserve event-level LOEO / no random snapshot split;
4. benchmark `v3-zero-correction` plus the frozen v2/Ridge/P2 stack;
5. run a compact materially-different model tournament;
6. revalidate reliability/tail governance under new IDs;
7. keep exposed events honestly exposed;
8. no production write.

## Prospective validation continues in parallel

Track A still separates:

- `DELAYED_LABEL_HOLDOUT`;
- `TRUE_POST_FREEZE_PROSPECTIVE`.

Do not use prospective sample-count gates to pause d2-v3 R&D.

## Engineering rule

`code -> tests -> CI -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects evidence integrity. It does not pause model development.**
