# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-21**

## Cold-start rule

Read in this order:

1. `ml/CURRENT_MODEL.md`;
2. `ml/results/D2_LONG72_STAGE2_RELIABILITY_GATING_V1_2026-10-21.md`;
3. `ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`;
4. `ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`;
5. `ml/results/D2_LONG72_ANCHOR_CONTRACT_V1_2026-10-21.md`;
6. `ml/results/D2_LONG_HORIZON_COVERAGE_AUDIT_V1_2026-10-21.md`;
7. `ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`;
8. `ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`;
9. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
10. `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
11. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
12. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
13. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
14. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate state

### Track A — frozen final24 validation

Keep unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

### Track B — frozen research packages

Pre-Live v3:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Early-live long72 package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Track-B long72 package is research-only and not production.

## Long72 exact package

Scope:

`24 < hours_to_kickoff <= 72`

Anchor:

Frozen T-3 checkpoint hold.

Stage-1 expert:

`inventory-linear-extrapolation`

Correction cap:

`±0.10 occupancy`

Stage-2 policy:

`P2-observation-maturity`

Reliability:

- observation #1 `0.25`;
- observation #2 `0.60`;
- observation #3+ `1.00`;
- `60<h<=72` time weight `0.75`;
- `48<h<=60` time weight `0.90`;
- `24<h<=48` time weight `1.00`;
- final reliability = minimum of observation/time weights.

Frozen manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

## Long72 development evidence

Frozen data:

- 14 total events / 130 rows in 0–72h;
- model-selection slice 24–72h: 80 rows / 13 events;
- 48–72h: 35 rows / 10 events.

Selected package:

- anchor MAE `3707.14`;
- P2 MAE `3012.63`;
- improvement `+694.51 / +18.73%`;
- 24–48h improvement `+954.58 / +25.75%`;
- 48–72h improvement `+664.71 / +14.47%`;
- worst degradation `1488.34`;
- bias `+917.05`.

Historical exposed-subset diagnostics:

- original exposed subset `+103.55` MAE improvement;
- later exposed subset `+1640.04`.

All of this is exposed development evidence, not unseen prospective validation.

## Why P2, not P4

`P4-data-quality` has lower historical tail degradation but slightly worse overall MAE.

The selector was frozen before results and ranks eligible Stage-2 policies by overall event-balanced MAE first. Therefore P2 is the selected package; do not switch to P4 post hoc.

## Immediate next work

> **Stop tuning the frozen long72 package on the same historical events. Build append-only prospective scoring for future completed events with valid 24–72h trajectories.**

For each new eligible event, preserve and score:

1. frozen T-3 anchor;
2. raw inventory extrapolation;
3. frozen P2 long72 forecast;
4. outcome only after it becomes available.

Do not mutate the package from these outcomes.

Keep evidence classes explicit. A future event observed after the long72 freeze can become prospective evidence only if the forecast inputs/package were frozen before the label was used.

## 72–168h boundary

Keep `72–168h` diagnostic-only until independent-event coverage reaches the predeclared `N>=9` floor.

Do not reduce the threshold to fit the current sample.

## Final24 equivalence reminder

Pre-Live v3 T-1 equals v2 T-1, so final24 d2 target remains exactly equivalent. Do not create a cosmetic v3 final24 retrain.

## Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- long72 package research-only;
- Pre-Live v3 research-only;
- production unchanged;
- `live_adjustment = 0`.

## One-line instruction

> **The 24–72h package is frozen. Active work is prospective append-only scoring, not more same-sample tuning. Production remains unchanged.**
