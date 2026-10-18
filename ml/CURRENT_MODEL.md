# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-18**

This is the canonical short-form state. Read `AI_BOOTSTRAP.md` first in a cold session.

## Current north star

Beyond is a **live demand decision system**, not only an attendance model.

Model-development workstreams:

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

Historical evidence base:

- Ekstraklasa 2021/22–2025/26;
- 1,530 matches;
- 7,650 horizon rows;
- verified historical capacity coverage 100%.

## a) Dane historyczne — dopracować, nie przebudowywać

**TAK — działa i jest najbardziej dojrzałe.**

Keep Structural Prior. Later tuning may test feature contribution, noisy-feature removal and stronger weighting of newer seasons, but only after d).

## b) Aktualny sezon — wzmocnić

**TESTED / NOT PROVEN / NO PRODUCTION CHANGE.**

Current Season Adjustment v1 was evaluated with the incumbent Structural Prior isolated before challenger-only signals were added.

Result:

- T-30 / T-14 / T-3 / T-1: `NO_ADJUSTMENT` selected on development;
- T-7 selects `season_r3-k6-a25` on 2023/24 development but degrades both reference holdouts;
- no horizon improves mean holdout MAE;
- no horizon improves both reference seasons.

Canonical evidence:

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

Do not promote or keep tuning the same explicit adjustment against the exposed reference seasons. Current-season information already inside Structural Prior remains unchanged.

## c) Context meczu — rozbudować

**AUDITED / FUTURE-FIXTURE EXTENSION NOT PROVEN / NO PRODUCTION CHANGE.**

The PIT feature store already contains substantial context:

- opponent demand and pair history;
- home/away PPG, GD/game and last-5 form;
- table positions/gaps and top/bottom interactions;
- past rest and 14-day congestion.

Future Fixture Context v1 then tested the main remaining safe-to-evaluate gap: next-home-fixture timing, attractiveness and a bounded cannibalization proxy.

Result:

| Horizon | Selected option | Mean incumbent MAE | Mean challenger MAE |
|---|---|---:|---:|
| T-30 | `NO_CONTEXT_EXTENSION` | 1,867.8 | 1,867.8 |
| T-14 | `NO_CONTEXT_EXTENSION` | 1,809.4 | 1,809.4 |
| T-7 | `future_timing_attractiveness` | **1,790.0** | 1,790.9 |
| T-3 | `NO_CONTEXT_EXTENSION` | 1,718.4 | 1,718.4 |
| T-1 | `future_timing_attractiveness` | **1,697.3** | 1,712.4 |

No horizon improves mean holdout MAE and no horizon improves both reference seasons.

The experiment is additionally only `SCHEDULE_AS_RECORDED_RETROSPECTIVE_PROXY` evidence because historical schedule versions are unavailable.

Canonical evidence:

- `ml/MATCH_CONTEXT_AUDIT_V1.md`;
- `ml/results/MATCH_CONTEXT_FUTURE_FIXTURE_V1_2026-10-18.md`.

Do not add future-fixture features to Structural Prior. Do not backfill injuries/suspensions/expected XI without a real historical PIT source.

## d) Live demand — najmocniej rozwinąć

**ACTIVE DEVELOPMENT.**

Already implemented:

- live public inventory collection;
- PIT trajectory / velocity / acceleration features;
- release / coverage-change handling;
- frozen C1 v8 prospective shadow inference;
- sector trajectories;
- price-area trajectories and real Roboticket price observations;
- guarded sector and price-area recommendations;
- dashboard decision support.

Development goal now:

> Improve how live evidence updates Structural Prior continuously, while keeping the frozen v8 package untouched and collecting prospective evidence automatically.

Do not confuse this with retuning v8. New live-demand work must be a separately governed challenger / product layer.

## C1 development evidence

Current live evidence base used by frozen v8:

- 9 completed in-domain training events;
- 206 PIT-valid full-trajectory rows;
- 30 final-24h rows.

Known development replay:

- v2 Live expert LOEO: **2,929.3 MAE**;
- Prior on that LOEO set: **3,968.7 MAE**;
- v8 development replay: **2,713.3 window MAE**;
- v8 latest-row replay: **1,998.1 MAE**;
- non-deployable Prior/Live oracle: **1,867.9 MAE**.

These remain development evidence only.

## Historical validation of C1

Canonical evidence:

- `ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_WALK_FORWARD_POLICY_VALIDATION_V1_2026-10-18.md`;
- `ml/results/C1_FORWARD_EVENT_DIAGNOSTIC_V1_2026-10-18.md`.

Key results:

- real-only Live LOEO: **2,929.3 MAE**;
- conservative train-only synthetic Live LOEO: **2,261.5 MAE**;
- four-event chronological Prior: **452.8 MAE**;
- four-event chronological raw Live: **2,103.7 MAE**;
- frozen v8 policy: **452.8 MAE**, selecting PRIOR in **16/16 rows**, worst degradation **0.0**.

The forward-event diagnostic found mixed raw-Live error direction and no single compact feature group whose removal consistently fixes all four events. The failure is better described as heterogeneous small-sample generalisation / feature-state distribution shift.

Do not retune frozen v8 from these events.

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

Do not retune or silently retrain this package during prospective validation.

## Current prospective evidence — verified 2026-10-18

- prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- validation state: `AWAITING_FIRST_PROSPECTIVE_SCORE`;
- production live adjustment: **0**.

Therefore there is **no confirmed prospective live MAE yet**.

## Current development decision

Historical C1 validation is complete for the currently available data. Workstreams b) and c) have both been tested without a validated production improvement. Prospective C1 evidence continues automatically.

Next active workstream:

**d) Live demand — najmocniej rozwinąć.**

The next implementation should focus on continuous live evidence and decision quality, not another v8 retune. Preserve Structural Prior as the production incumbent and frozen v8 as the prospective shadow comparator.

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
