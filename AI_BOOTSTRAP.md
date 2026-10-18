# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-18**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Before doing Beyond forecasting, ML, dashboard, Growth or recommendation work, read in this order:

1. `ml/CURRENT_MODEL.md` — canonical current model/product state;
2. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md` — current development plan;
3. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md` — frozen C1 prospective runtime/governance;
4. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — live forecasting roadmap;
5. `ml/SECTOR_DECISION_PRICING_V1.md` — E0 sector/pricing product contract;
6. `ml/NORTH_STAR.md`;
7. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
8. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
9. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Critical product direction

Beyond is a **live demand decision system**.

Use these exact model-development workstreams:

- **a) Dane historyczne — dopracować, nie przebudowywać**;
- **b) Aktualny sezon — wzmocnić**;
- **c) Context meczu — rozbudować**;
- **d) Live demand — najmocniej rozwinąć**.

Development order:

`Walidacja -> b -> c -> d -> tuning a`

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## Structural Prior — production incumbent

All five horizons T-30/T-14/T-7/T-3/T-1 are executable and frozen.

Production remains:

`live_adjustment = 0`

Historical reference:

| Horizon | 2024/25 MAE | 2025/26 MAE |
|---|---:|---:|
| T-30 | 1,889.4 | 1,846.3 |
| T-14 | 1,748.5 | 1,870.4 |
| T-7 | 1,777.7 | 1,802.3 |
| T-3 | 1,661.7 | 1,775.1 |
| T-1 | 1,651.7 | 1,742.8 |

## C1 v8 — frozen prospective shadow

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Frozen live expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Do not retune or silently retrain this package during prospective validation.

## Walidacja obecnego modelu — historical result

Canonical evidence:

- `ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_WALK_FORWARD_POLICY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_FORWARD_EVENT_DIAGNOSTIC_V1_2026-10-18.md`.

Key result:

- LOEO raw Live: **2,929.3 MAE**;
- conservative train-only synthetic Live: **2,261.5**;
- four-event chronological raw Live: **2,103.7** vs Prior **452.8**;
- frozen v8 selects PRIOR in **16 / 16 rows** and preserves Prior exactly;
- forward diagnostic finds no single compact feature group that consistently fixes raw Live;
- frozen v8 remains unchanged.

Current prospective evidence:

- prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- state: `AWAITING_FIRST_PROSPECTIVE_SCORE`.

There is still no confirmed prospective live MAE.

## b) Aktualny sezon — wzmocnić — TESTED / NOT PROVEN

Canonical evidence:

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

Current Season Adjustment v1 tested an explicit bounded/shrunk correction on top of Structural Prior with the incumbent isolated before challenger-only signals are added.

Result:

- T-30: `NO_ADJUSTMENT`;
- T-14: `NO_ADJUSTMENT`;
- T-7: `season_r3-k6-a25` wins development but worsens 2024/25 and 2025/26 holdouts;
- T-3: `NO_ADJUSTMENT`;
- T-1: `NO_ADJUSTMENT`;
- no horizon has positive mean holdout improvement;
- no promotion;
- production unchanged.

Do not keep tuning the same explicit current-season adjustment against the exposed reference seasons. Current-season features already inside Structural Prior remain.

## Current development state

### c) Context meczu — rozbudować — NEXT ACTIVE DEVELOPMENT

Start with a point-in-time audit of context already present in the canonical feature store, then add the smallest governed challenger that can be evaluated without leakage.

Priority:

1. opponent strength / attractiveness;
2. future fixtures and cannibalization / fixture congestion;
3. form and table context not already captured sufficiently;
4. squad injuries/suspensions/key players only if reliable PIT history exists.

### d) Live demand — najmocniej rozwinąć

- inventory od pierwszego momentu sprzedaży;
- velocity / acceleration / sector / price-area movement;
- aktualizacja forecastu po każdym znaczącym snapshotcie;
- checkpointy T-30/T-14/T-7/T-3/T-1 głównie do pomiaru jakości.

### a) Dane historyczne — dopracować, nie przebudowywać

- utrzymać Structural Prior;
- feature contribution;
- usunąć noisy features;
- lepiej ważyć nowsze sezony.

## E0 sector / price-area decision support — implemented

Implemented:

- sector trajectory / status;
- bounded no-action sector projection;
- Roboticket price capture;
- price-area mapping / mixed-price split;
- assumption-based scenarios;
- guarded recommendations;
- RLS-safe dashboard cache/UI.

`auto_price_change_allowed = false`

No learned elasticity or causal pricing uplift is claimed.

Club decision/execution workflow remains deferred. Simulated intervention uplift must be labeled simulated.

## Non-negotiable forecasting rules

- no future leakage;
- event is the independent evaluation unit;
- no random snapshot-row split across the same events;
- every feature must exist as-of forecast time;
- synthetic variants are train-only and never new independent evidence;
- frozen v8 is not retuned on the same nine events;
- replay/walk-forward is not prospective evidence;
- production remains `live_adjustment = 0` until explicit promotion.

## One-line cold-start instruction

> **Walidacja historyczna C1 jest wykonana; frozen v8 odcina unsafe Live. b) Current Season Adjustment v1 zostało przetestowane i nie udowodniło poprawy, więc go nie promuj. Następny aktywny development: c) Context meczu — rozbudować; potem d -> tuning a.**
