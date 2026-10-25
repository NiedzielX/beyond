# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-25**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md` — latest operational truth;
2. `ml/EXECUTION_PLAN_CURRENT.md` — exact next work order;
3. `ml/PROGRESS_TRACKING.md` — canonical status snapshot;
4. `ml/MAE_RESEARCH_ROADMAP_V4.md` — canonical strategy;
5. `ml/P7_LONG168_RESULT_2026-10-25.md` and `ml/P9A_FREEZE_AUDIT_2026-10-25.md`;
6. relevant frozen precommit/result files before touching each workstream.

Do not restart from Roadmap v3. Do not reconstruct frozen experiments from memory.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Immediate order

`sync corrected P11 runtime -> first genuine P11 capture/audit -> continue Long72 prospective evidence -> accumulate P9 168h coverage -> accumulate P4a labels -> separately precommit any P7 follow-up -> define business ΔMAE threshold`

## Current canonical state

### Repository

Branch reconciliation is complete.

- P9a/P11a source and workflows are on `main`.
- PRs #171/#172 are merged.
- Final reconciliation merge: `c48b0045f371f0b52b98f61d24f39f3be99ec7bb`.
- Do not repeat branch reconciliation or recreate P9a/P11a.

### Long72 prospective evidence

Two genuine post-freeze attendance outcomes are scored:

- event 10 Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 Wisła Kraków vs Raków Częstochowa: **33,000**.

Current prospective point evidence:

- genuine scored events: **2**;
- anchor MAE: `9069.52`;
- frozen package MAE: `7641.71`;
- point improvement: `1427.80` seats / `15.74%`.

Do not retune, calibrate or promote from n=2.

### P7 Long168 — EXECUTED

Frozen execution completed successfully at 10/9 genuine readiness.

- frozen events: **10**;
- rows: **139**;
- forward held-out events/folds: **5/5**;
- anchor MAE: **7409.79**;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: **6339.99**;
- point improvement: **1069.80 seats / 14.44%**;
- event improvement rate: **80%**;
- fold improvement rate: **80%**;
- 95% paired event-block bootstrap interval for challenger-minus-anchor MAE: **[-2566.13, +174.47]**;
- interpretation: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision: `ADVANCE_RESEARCH`;
- `production_activation_allowed=false`;
- `live_adjustment=0`.

Do not rerun or tune the frozen P7 candidate set from this scorecard. Any follow-up requires a separate precommit.

Canonical result: `ml/P7_LONG168_RESULT_2026-10-25.md`.

### P9a — TARGET-FREE AUDIT COMPLETE

T-24 manifest:

`738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`

- representation ready 16;
- freeze ready 12;
- comparator ready 9.

T-48 manifest:

`ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`

- representation ready 13;
- freeze ready 10;
- comparator ready 7.

Audit guarantees:

- target values not opened;
- no future target points;
- no model training;
- production unchanged.

P9a is freeze tooling only. Do not fit a learner from this audit.

Canonical audit: `ml/P9A_FREEZE_AUDIT_2026-10-25.md`.

### P9 full-168h

Current genuine coverage:

- 168h: **5/9** events / 5 clubs;
- 72h: 9 / 7;
- 48h: 12 / 7;
- 24h: 15 / 9.

Full-168h learner remains blocked. No learner selection/training before 9/9 plus separate precommit.

### P4a

- READY events: 5;
- genuine labels: **2**;
- distinct labeled spacing values: **2**;
- gate: `>=9 labels AND >=3 distinct values`;
- gate remains closed.

### P11a PIT odds

- DB capture/readiness/consensus contract: live;
- `THE_ODDS_API_KEY`: **configured and verified**;
- GitHub OIDC main-only capture auth: verified;
- adapter tests/type-check: green;
- genuine odds rows: **0**;
- schedule: off.

First provider call failed closed with HTTP 422 because the deployed runtime sent ISO timestamps with milliseconds. No odds rows were written.

Source fix is on `main` in commit:

`d27d797578f18f09140ccc1723219a3e690d339a`

The fix strips milliseconds from `commenceTimeFrom/To`; CI passed.

A Dashboard `Deploy updates` created Edge Function version 4 but retained the previous runtime code. Therefore the remaining blocker is **runtime synchronization with the corrected main source**, not the API key.

After runtime sync, run one main-only capture, audit it fully, then consider schedule separately.

### Closed research loops

Do not reopen without materially new information/mechanism:

- P10/P10b fixed pooled-HGB path;
- P5a shrinkage;
- P6 historical Long72 signal;
- P8 simple club/opponent calibration;
- old estimator-only sweeps;
- post-hoc tuning on inspected evidence.

## Governance

`ROBUST_RESEARCH_ADVANCE` still requires a predeclared business-derived minimum meaningful MAE improvement and adequate precision.

Do not derive the business threshold from P7, Long72, or any challenger result it will judge.

The old ChatGPT Beyond readiness automations remain intentionally disabled.
