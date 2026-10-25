# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-25**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

Operational handoff: `ml/NEXT_SESSION_HANDOFF.md`

Current execution order: `ml/EXECUTION_PLAN_CURRENT.md`

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production: `live_adjustment = 0`.

## Current status

| Item | Status | Current decision |
|---|---|---|
| Branch reconciliation | ✅ DONE | main/active history reconciled; do not repeat |
| Long72 prospective evidence | 🟢 **2 genuine scored events** | preserve evidence, collect more, no retuning |
| P4a previous-home spacing | 🟡 **2/9 genuine labels / 2 distinct** | gate closed; accumulate labels |
| P7 Long168 | ✅ **EXECUTED** | 14.44% point gain; `POINT_GAIN_UNCERTAINTY_LIMITED`; any follow-up needs new precommit |
| P9 full-168h Booking Curve | 🟡 **5/9** | continue collection; learner blocked |
| P9a T-24/T-48 freeze | ✅ **AUDIT COMPLETE** | manifests frozen; labels/model remain closed |
| P10/P10b | ✅ CLOSED | do not retune fixed pooled-HGB path |
| P11a PIT odds | 🟠 **SECRET READY / 0 genuine rows** | sync corrected runtime, then first genuine capture + audit |
| Governance v2 | ✅ IMPLEMENTED / threshold pending | robust state unavailable until business ΔMAE threshold exists |
| Production | ⛔ UNCHANGED | `live_adjustment = 0` |

## Genuine outcomes / Long72

Verified genuine attendance from `frekwencyjny.pl`:

- event 10 — Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 — Wisła Kraków vs Raków Częstochowa: **33,000**.

Existing frozen Long72 scorer result:

- scored events: **2**;
- anchor event-balanced MAE: `9069.5168`;
- frozen package event-balanced MAE: `7641.7132`;
- point MAE improvement: `1427.8036`;
- relative point improvement: `15.7429%`;
- event improvement rate: `1.0`;
- production change: false.

Evidence classification: **first prospective observations only**. n=2 is insufficient for promotion, redesign, calibration or robust inference.

## P7 Long168 — frozen result

Frozen executor completed in GitHub run `40197742930`.

Freeze:

- rows >72h: **139**;
- independent frozen events: **10**;
- identity manifest SHA: `185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`;
- target-attendance invariance: PASS;
- target values absent at freeze;
- frozen artifact hashes verified.

Forward evaluation:

- held-out events/folds: **5/5**;
- anchor MAE: **7409.7882**;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: **6339.9915**;
- delta challenger-minus-anchor: **-1069.7967**;
- relative point improvement: **14.4376%**;
- event improvement rate: **0.8**;
- forward-fold improvement rate: **0.8**;
- worst event degradation: **712.05**;
- challenger bias: **-4972.76**.

Paired event-block bootstrap, 5,000 resamples:

- lower: `-2566.13`;
- upper: `+174.47`;
- median: `-1017.46`;
- `P(delta_MAE < 0)=0.9322`.

Decision:

- precommitted research rule: PASS;
- scorecard decision: `ADVANCE_RESEARCH`;
- evidence interpretation: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- no production promotion;
- do not tune/rerun the frozen P7 candidate set after inspecting this result.

Scorecard SHA: `f684570856e264dae288599a8e24dde6802f84669a43e304c1d900726aa94e45`.

Canonical result: `ml/P7_LONG168_RESULT_2026-10-25.md`.

## P9 booking curve

Fresh coverage:

- 168h: **5 events / 5 clubs**;
- 72h: **9 events / 7 clubs**;
- 48h: **12 events / 7 clubs**;
- 24h: **15 events / 9 clubs**;
- full 168h model status: `DATA_BOUND`;
- learner precommitted: false.

No full-168h learner selection/training before 9/9 plus a separate precommit.

## P9a target-free freeze — COMPLETE

GitHub run: `40197782502`.

T-24:

- manifest: `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- input target count: 19;
- reference catalog events: 20;
- representation ready: 16;
- freeze ready: 12;
- comparator ready: 9.

T-48:

- manifest: `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`;
- input target count: 16;
- reference catalog events: 20;
- representation ready: 13;
- freeze ready: 10;
- comparator ready: 7.

Hard guarantees:

- `target_values_opened=false`;
- `model_training_performed=false`;
- `future_target_snapshot_allowed=false`;
- `production_change=false`.

Canonical audit: `ml/P9A_FREEZE_AUDIT_2026-10-25.md`.

## P4a

- READY events: 5;
- genuine labeled READY events: **2**;
- labeled previous-home-spacing events: 2;
- distinct labeled values: **2**;
- required: `>=9 labeled AND >=3 distinct labeled values`;
- research trigger: false.

## P11a v2

Confirmed working:

- DB capture/readiness/consensus contract;
- `THE_ODDS_API_KEY` configured and visible to Edge runtime;
- main-only GitHub OIDC authorization;
- provider adapter CI/tests;
- schedule remains off.

First genuine provider attempt:

- config verification: `configured=true`;
- provider returned `422 INVALID_COMMENCE_TIME_FROM`;
- root cause: deployed runtime sent ISO timestamps with milliseconds;
- no raw odds rows inserted;
- no target values used;
- no production change.

Source correction is on `main` in commit `d27d797578f18f09140ccc1723219a3e690d339a` and CI passed. It strips milliseconds from provider commence-time query parameters.

A subsequent Dashboard deploy produced Edge Function version 4 but runtime inspection still showed the old source. Therefore the current blocker is **deployment/runtime synchronization**, not provider credentials.

Current P11 readiness:

- raw rows: **0**;
- genuine PIT events: 0;
- events with >=3 bookmakers: 0;
- status: `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`;
- model precommitted: false.

Next P11 action: synchronize corrected source into live runtime, perform one genuine main-only capture, audit it, then decide schedule separately.

## Governance

Closed loops remain closed: P10/P10b, P5a, P6 historical Long72, P8 simple calibration, old estimator sweeps.

Business minimum meaningful `ΔMAE` is still intentionally undefined. It must come from operational decision value, not from P7/Long72/P9 results.

Until the threshold and adequate precision exist, no result is `ROBUST_RESEARCH_ADVANCE`.
