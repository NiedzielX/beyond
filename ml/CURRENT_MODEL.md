# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-18**

This is the canonical short-form state. Read `AI_BOOTSTRAP.md` first in a cold session.

## Current north star

Beyond is a **live demand decision system**, not only an attendance model.

For model development, keep these exact workstreams:

- **a) Dane historyczne — dopracować, nie przebudowywać**;
- **b) Aktualny sezon — wzmocnić**;
- **c) Context meczu — rozbudować**;
- **d) Live demand — najmocniej rozwinąć**.

Development order:

`Walidacja -> b -> c -> d -> tuning a`

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## Structural Prior runtime

All five horizons are executable and frozen:

| Horizon | Model spec | 2023/24 dev MAE | 2024/25 historical MAE | 2025/26 historical MAE |
|---|---|---:|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | 2,559.7 | 1,889.4 | 1,846.3 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | 2,340.0 | 1,748.5 | 1,870.4 |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | 2,476.8 | 1,777.7 | 1,802.3 |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | 2,311.6 | 1,661.7 | 1,775.1 |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | 2,348.0 | 1,651.7 | 1,742.8 |

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

## Historical evidence base

- Ekstraklasa 2021/22–2025/26;
- 1,530 matches;
- 7,650 horizon rows;
- verified historical capacity coverage 100%.

## a) Dane historyczne — dopracować, nie przebudowywać

**TAK — działa i jest najbardziej dojrzałe.**

Keep Structural Prior, test feature contribution, remove noisy features and weight newer seasons better.

## b) Aktualny sezon — wzmocnić

**CZĘŚCIOWO — NEXT ACTIVE DEVELOPMENT.**

Current-season evidence exists, but the next model-quality task is an explicit current season adjustment that reacts faster to recent home-match reality.

## c) Context meczu — rozbudować

**CZĘŚCIOWO.**

Existing context includes parts of form, table, opponent and schedule information. Future fixtures / cannibalization and reliable squad context are still missing as first-class governed features.

## d) Live demand — najmocniej rozwinąć

**TAK — działa, ale nie jest finalnie promowane.**

Live inventory, trajectory, velocity, C1 shadow inference, sector and price-area trajectories exist. Official horizons remain evaluation checkpoints; future live work should become more continuous.

## C1 development evidence

Current live evidence base:

- 9 completed in-domain events;
- 206 PIT-valid full-trajectory rows;
- 30 final-24h rows.

Known development replay:

- v2 Live expert LOEO: **2,929.3 MAE**;
- Prior on that LOEO set: **3,968.7 MAE**;
- v8 development replay: **2,713.3 window MAE**;
- v8 latest-row replay: **1,998.1 MAE**;
- non-deployable Prior/Live oracle: **1,867.9 MAE**.

These remain development evidence only.

## Walidacja obecnego modelu — current completed historical evidence

Canonical evidence:

- `ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_WALK_FORWARD_POLICY_VALIDATION_V1_2026-10-18.md`.

### Synthetic trajectory augmentation — LOEO

Train-only augmentation, all scoring on real held-out events:

| Training mode | Prior MAE | Raw Live MAE |
|---|---:|---:|
| `real_only` | 3,968.7 | 2,929.3 |
| `conservative_synthetic` | 3,968.7 | **2,261.5** |
| `stress_synthetic` | 3,968.7 | 2,498.8 |

Conservative synthetic improves raw Live by **667.8 MAE** vs real-only LOEO.

Automated signal:

`PROMISING_FOR_FURTHER_VALIDATION`

No promotion is allowed from this evidence.

### Synthetic trajectory augmentation — chronological walk-forward

Four later real events:

| Training mode | Prior MAE | Raw Live MAE |
|---|---:|---:|
| `real_only` | **452.8** | 2,103.7 |
| `conservative_synthetic` | **452.8** | 1,939.5 |
| `stress_synthetic` | **452.8** | **1,876.7** |

Synthetic augmentation improves raw Live chronologically, but raw Live still loses to Prior on this small four-event subset.

### Frozen v8 policy — chronological walk-forward

The already-fixed v8 gate was then applied without changing or refitting its thresholds.

For real-only Live:

- Prior MAE: **452.8**;
- raw Live MAE: **2,103.7**;
- final v8 policy MAE: **452.8**;
- v8 selected PRIOR in **16 / 16 rows**;
- worst degradation vs Prior: **0.0**.

Conclusion:

> On the currently available four chronological forward events, raw Live is weak but the frozen v8 gate successfully rejects it and preserves Structural Prior exactly.

This is useful retrospective safety evidence, not prospective validation.

## Frozen C1 v8 prospective package — LIVE

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Frozen expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Frozen training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Do not retune this frozen package during prospective validation.

## Current prospective evidence — verified 2026-10-18

- prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- validation state: `AWAITING_FIRST_PROSPECTIVE_SCORE`;
- production live adjustment: **0**.

Therefore there is **no confirmed prospective live MAE yet**.

## Current development decision

Historical validation on the currently available live events is now sufficient to move to the next workstream while prospective C1 evidence continues automatically.

Next active workstream:

**b) Aktualny sezon — wzmocnić.**

Synthetic trajectory augmentation remains a train-side challenger/regularisation technique for future C1 packages. It does not modify frozen v8 automatically.

## E0 — Sector & Price-area Decision Support — IMPLEMENTED

Implemented:

- sector inventory trajectories and status;
- bounded no-action projection;
- Roboticket price-area inventory and price capture;
- mixed-price sector split;
- assumption-based pricing scenarios;
- guarded recommendations;
- RLS-safe dashboard caches and UI.

`auto_price_change_allowed = false`

No learned elasticity or causal uplift is claimed.

Club decision/execution workflow is intentionally deferred. Demo uplift must be labeled simulated.

## Evaluation governance

- no future leakage;
- event is the independent evaluation unit;
- no random row split across the same event trajectories;
- every feature must be available as-of forecast timestamp;
- synthetic variants are train-only and never independent evidence;
- frozen v8 thresholds are not retuned on the same nine events;
- replay / walk-forward is not prospective evidence;
- production remains `live_adjustment = 0` until explicit promotion.
