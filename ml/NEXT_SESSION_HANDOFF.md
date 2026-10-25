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

`precommit P7 prospective follow-up -> preserve scheduled P11a accumulation -> preserve P11b/P11d context collection -> continue Long72 prospective scoring -> accumulate P9 to 9/9 -> accumulate P4a labels -> define business minimum meaningful ΔMAE`

P7 tournament, P9a freeze, P11a first genuine capture and P11 context audit are already complete.

---

## 3. Repository state

Canonical repo: `NiedzielX/beyond`.

Branch reconciliation is complete. Do not repeat it or rebuild P9a/P11a from memory.

Roadmap v4 is canonical.

---

## 4. Long72 prospective evidence

Current genuine scored events: **2**.

- event 10 — Pogoń Szczecin vs Radomiak Radom: 19,050;
- event 16 — Wisła Kraków vs Raków Częstochowa: 33,000.

Frozen result on n=2:

- anchor MAE: 9069.52;
- package MAE: 7641.71;
- point improvement: 1427.80 / 15.74%;
- production change: false.

Interpretation: first prospective evidence only. Do not retune/calibrate/promote.

---

## 5. P7 Long168 — frozen tournament complete

GitHub run: `40197742930`.

- frozen events: 10;
- rows: 139;
- forward held-out events/folds: 5/5;
- anchor MAE: 7409.79;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: 6339.99;
- point improvement: 1069.80 / 14.44%;
- event/fold improvement rate: 80% / 80%;
- 95% event-block interval: `[-2566.13, +174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision: `ADVANCE_RESEARCH`;
- no production activation.

Canonical result:

`ml/P7_LONG168_RESULT_2026-10-25.md`

The tournament is now exposed. **Do not rerun/tune it.**

Next allowed P7 action is a new prospective validation precommit for the already-selected mechanism, frozen before new qualifying attendance labels are opened.

---

## 6. P9 / P9a

P9a target-free freeze audit is complete.

- T-24 manifest: `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- T-48 manifest: `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`;
- labels closed;
- no model training;
- no future target trajectory points.

Full P9 remains data-bound:

- 168h: 5/9 events / 5 clubs;
- 72h: 9 / 7;
- 48h: 12 / 7;
- 24h: 15 / 9;
- learner precommitted: false.

Do not fit/select the first full-168h learner before 9/9 plus a separate precommit.

---

## 7. P4a

- READY events: 5;
- genuine labels: 2;
- distinct labeled previous-home-spacing values: 2;
- required: >=9 labels + >=3 distinct values;
- trigger: false.

Remain frozen/data-bound.

---

## 8. P11a — genuine bookmaker capture active

The runtime timestamp bug is resolved. Live Edge runtime is version 6 and is synchronized with `main`.

First genuine capture:

- GitHub run `40199626764`;
- captured at `2026-10-25T13:46:04.688Z`;
- 3 local candidates;
- 2 provider events;
- 2 deterministic matches;
- 34 raw append-only bookmaker rows;
- event 22: 18 quotes, kickoff delta 0;
- event 6: 16 quotes, kickoff delta 0;
- event 23: `NO_PROVIDER_MATCH`, no insert;
- target values used: false;
- production change: false.

Current readiness:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- genuine PIT events: 2;
- events with >=3 bookmakers: 2;
- coverage at 24h / 72h / 168h: 2 / 1 / 0;
- model precommitted: false.

Scheduled GitHub capture is enabled:

`17 */6 * * *`

Pushes only run contract/tests; provider calls occur on schedule or explicit manual dispatch.

Do not alter matching tolerance or backfill missing historical odds.

Canonical evidence:

`ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`

---

## 9. P11b/c/d target-free context audit

Canonical audit:

`ml/P11_CONTEXT_AUDIT_2026-10-25.md`

### P11b price

Existing real price infrastructure is already substantial and healthy.

Live function:

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)`

Verified:

- event 6: `PRICE_CONTEXT_READY`;
- event 22: `PRICE_AREA_ONLY`;
- historical cutoff returns historical as-known state;
- no target table is referenced;
- promotion flag remains null because no explicit promotion source exists;
- price changes are not relabeled as promotions.

No P11b attendance model is opened.

### P11c verified absences

Current evidence: only 1 active PIT-valid verified absence / 1 team.

Refresh is healthy, but modeling is **DATA_BOUND**.

Do not interpret missing rows as "player available".

### P11d weather

Existing mechanism status:

`research_only_no_uplift`

Do not reopen the same weather mechanism under a new name.

### P11d media attention

Prospective-only collector is healthy:

- >1,000 samples;
- 12 events;
- historical backfill forbidden;
- media attention remains `prospective_collecting`;
- mention acceleration remains warm-up;
- current feature variance is not sufficient for evaluation.

Do not force an ablation yet.

---

## 10. Governance / P12

Governance threshold framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

Numerical minimum meaningful ΔMAE remains intentionally unset until business-derived.

P12 pre-plan:

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

P12 is lower priority than current P9/P11 evidence work.

---

## 11. Closed loops

Do not reopen without a materially new mechanism:

- P10/P10b;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple calibration;
- existing weather mechanism;
- old estimator sweeps;
- post-hoc tuning on inspected evidence.

---

## 12. Cold-start command

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md`, Roadmap v4, P7 result, P9a audit, P11a first capture and P11 context audit. Query readiness fresh. P7 tournament is exposed and must not be tuned; the next P7 action is a separately frozen prospective validation lane. P11a genuine capture is live on a six-hour schedule and already has 34 raw rows across 2 events. P11b price as-known contract is live. P11c is data-bound. Existing weather is no-uplift; media attention is still prospective collecting. P9 remains 5/9 and P4a 2/9. Keep production unchanged.
