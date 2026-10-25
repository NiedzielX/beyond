# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-25**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Current phase: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

No research result activates production automatically.

---

## 2. Immediate execution order

Current order:

`sync corrected P11 Edge runtime -> first genuine P11 capture/audit -> continue Long72 prospective scoring -> accumulate P9 full-168h coverage -> accumulate P4a labels -> separately precommit any P7 follow-up -> define business minimum meaningful ΔMAE`

P7 execution and the P9a main target-free audit are now complete.

---

## 3. Repository reconciliation — COMPLETE

Canonical repo: `NiedzielX/beyond`.

Previous active branch: `ml/p9-p11-execution-2026-10-24`.

- PR #171 merged `main` into the active branch after deliberate conflict resolution;
- P11 contract CI passed;
- P9a freeze CI passed;
- key P9a/P11a source/workflow blobs were verified identical on `main` and active;
- PR #172 merged reconciled history back to `main`;
- final reconciliation merge: `c48b0045f371f0b52b98f61d24f39f3be99ec7bb`.

Do not repeat reconciliation or rebuild P9a/P11a from memory.

---

## 4. Genuine outcomes / Long72 prospective evidence

Verified genuine attendance inserted on 2026-10-25:

- event 10 — Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 — Wisła Kraków vs Raków Częstochowa: **33,000**.

Existing frozen Long72 scorer result:

- genuine scored events: **2**;
- anchor MAE: **9069.52**;
- frozen package MAE: **7641.71**;
- point improvement: **1427.80 seats / 15.74%**;
- production change: false.

Interpretation: **first prospective evidence only**. n=2 is insufficient for promotion, redesign, calibration or robust inference.

Continue normal outcome sync and frozen prospective scoring. Do not retune Long72.

---

## 5. P7 Long168 — FROZEN EXECUTION COMPLETE

Run:

`P7 Long168 Executor v1` — GitHub run `40197742930`.

Contract state:

- frozen Long168 events: **10**;
- frozen rows: **139**;
- event IDs: `[1,3,4,5,10,11,15,16,18,19]`;
- identity manifest SHA: `185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`;
- target values absent from freeze;
- target-attendance invariance: PASS;
- frozen Structural Prior hashes verified.

Scorecard:

- forward held-out events / folds: **5 / 5**;
- anchor event-balanced MAE: **7409.79**;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: **6339.99**;
- point delta MAE challenger-minus-anchor: **-1069.80**;
- relative point delta: **-14.44%**;
- event improvement rate: **80%**;
- fold improvement rate: **80%**;
- worst event degradation: **712.05**;
- challenger bias: **-4972.76**.

Paired event-block bootstrap, 5,000 resamples:

- 95% interval: **[-2566.13, +174.47]**;
- `P(delta_MAE < 0)=0.9322`.

Correct interpretation:

- precommitted research-advance rule: PASS;
- decision: `ADVANCE_RESEARCH`;
- evidence status: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- **not robust proof** because the interval crosses zero and held-out N=5;
- no production promotion;
- `production_activation_allowed=false`;
- `live_adjustment=0`.

Canonical result:

`ml/P7_LONG168_RESULT_2026-10-25.md`

Do not rerun/tune the frozen P7 candidate family using this inspected result. Any follow-up must be a new separately precommitted experiment/prospective lane.

---

## 6. P9a target-free freeze — COMPLETE

Run:

`P9a Booking Curve Freeze v1` — GitHub run `40197782502`.

T-24:

- manifest: `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- input targets: 19;
- representation ready: 16;
- freeze ready: 12;
- comparator ready: 9.

T-48:

- manifest: `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`;
- input targets: 16;
- representation ready: 13;
- freeze ready: 10;
- comparator ready: 7.

Hard gates passed:

- `target_values_opened=false`;
- `model_training_performed=false`;
- no future target trajectory points;
- production unchanged.

Canonical audit:

`ml/P9A_FREEZE_AUDIT_2026-10-25.md`

P9a has completed its current freeze/audit purpose. Do not infer permission to train a P9 learner.

---

## 7. Fresh readiness

Canonical source: `public.ml_research_readiness_v1()`.

### Long72

- reproducible rows: **90**;
- genuine scored events: **2**;
- trigger: true.

### P9 full-window booking curve

- 168h: **5/9 events / 5 clubs**;
- 72h: **9 events / 7 clubs**;
- 48h: **12 events / 7 clubs**;
- 24h: **15 events / 9 clubs**;
- full 168h status: `DATA_BOUND`;
- learner precommitted: false.

Do not fit/select the first full-168h learner before 9/9 and a separate precommit.

### P4a

- READY events: 5;
- genuine labeled READY events: **2**;
- labeled non-null previous-home-spacing events: 2;
- distinct labeled spacing values: **2**;
- required: `>=9 labeled + >=3 distinct values`;
- trigger: false.

P4a remains frozen/data-bound.

---

## 8. P11a PIT odds — SECRET READY, RUNTIME SOURCE NOT YET SYNCED

Purpose: add PIT market-implied match quality/outcome uncertainty/stakes as a genuinely new information family.

Confirmed:

- DB capture/consensus/readiness contract live;
- Edge Function `p11_odds_capture_v2` active;
- `THE_ODDS_API_KEY` **configured and verified**;
- GitHub main-only OIDC auth works;
- provider adapter type-check/tests pass;
- schedule remains off;
- raw genuine odds rows: **0**;
- `production_change=false`.

First real provider request failed closed before inserts:

`422 INVALID_COMMENCE_TIME_FROM`

Cause: deployed runtime generated millisecond ISO timestamps while The Odds API requires `YYYY-MM-DDTHH:MM:SSZ`.

Source fix is already on `main`:

`d27d797578f18f09140ccc1723219a3e690d339a`

The fixed source strips milliseconds from `commenceTimeFrom` / `commenceTimeTo`; CI is green.

A subsequent Supabase Dashboard `Deploy updates` produced Edge Function version 4, but inspection showed that runtime still contained the pre-fix source. Therefore:

> **P11 is no longer blocked by an API key. It is blocked only by synchronization/deployment of the corrected main source into the live Edge Function runtime.**

After runtime sync:

1. run one main-only capture;
2. audit event mapping and kickoff deltas;
3. audit complete bookmaker-level 1X2 quotes;
4. audit quota / batch / payload hash lineage;
5. verify append-only raw rows;
6. run `p11_market_context_as_known_v2(...)`;
7. run `p11_market_odds_readiness_v2()`;
8. keep schedule off until accepted.

Never backfill closing odds into earlier cutoffs.

---

## 9. Governance / closed loops

Do not reopen without materially new information/mechanism:

- P10/P10b fixed pooled-HGB path;
- old estimator-only sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple calibration;
- blind post-hoc calibration.

Minimum practically meaningful `ΔMAE` remains intentionally undefined and must be business-derived from actual decision consequences.

Until that threshold exists and precision is adequate, no challenger can be called `ROBUST_RESEARCH_ADVANCE`.

---

## 10. Cold-start command

> Read `AI_BOOTSTRAP.md`, `ml/NEXT_SESSION_HANDOFF.md`, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md`, Roadmap v4, `ml/P7_LONG168_RESULT_2026-10-25.md`, and `ml/P9A_FREEZE_AUDIT_2026-10-25.md`. Query readiness fresh. P7 has already executed and produced a 14.44% point MAE gain but remains uncertainty-limited because its event-block interval crosses zero. P9a T-24/T-48 target-free audit is complete. P9 full 168h remains 5/9 and learner-blocked. P4a remains 2/9 labels and blocked. P11 provider secret is configured; source fix is on main, but live runtime still needs synchronization before first genuine capture. Keep schedule off and production unchanged.
