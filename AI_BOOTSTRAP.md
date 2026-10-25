# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-25 11:55 Europe/Warsaw**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md` — latest operational truth;
2. `ml/EXECUTION_PLAN_CURRENT.md` — exact next work order;
3. `ml/PROGRESS_TRACKING.md` — canonical status snapshot;
4. `ml/MAE_RESEARCH_ROADMAP_V4.md` — canonical strategy;
5. relevant frozen precommit/result files before touching each workstream.

Do not restart from Roadmap v3. Do not reconstruct frozen experiments from memory.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Immediate order

`P11 first genuine manual capture -> audit -> P7 frozen execute -> P9a freeze audit -> continue Long72/P4a/P9 evidence accumulation`

## Current canonical state

### Repository

Branch reconciliation is complete.

- P9a/P11a source and workflows are already on `main`.
- Reconciliation PRs #171 and #172 are merged.
- Final reconciliation merge commit on main: `c48b0045f371f0b52b98f61d24f39f3be99ec7bb`.
- Do not rebuild the implementation or repeat branch reconciliation.

### Long72

Two genuine post-freeze attendance outcomes were confirmed on 2026-10-25:

- event 10 Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 Wisła Kraków vs Raków Częstochowa: **33,000**.

The frozen scorer inserted **2 genuine prospective scores**.

Point evidence on n=2:

- anchor MAE `9069.52`;
- frozen package MAE `7641.71`;
- point improvement `1427.80` seats / `15.74%`.

Do not retune, calibrate or promote from n=2.

### P7 Long168

Fresh canonical readiness:

- independent eligible events: **10**;
- threshold: 9;
- rows >72h: 139;
- `research_start_trigger=true`.

P7 is **genuinely unlocked**.

Do not redesign it. Run the existing frozen workflow manually on main:

`P7 Long168 Executor v1 -> mode=execute`

The workflow must freeze identities, replay the frozen T-7 anchor, run only the fixed tournament, upload artifacts and keep production disabled.

### P9 full-168h

Fresh coverage:

- 168h: **5/9**;
- 72h: 9 events;
- 48h: 12 events;
- 24h: 15 events.

Full-168h learner remains blocked. No learner selection before 9/9 and a separate precommit.

### P4a

- READY events: 5;
- genuine labels: **2**;
- distinct labeled previous-home-spacing values: **2**;
- required: >=9 labels + >=3 distinct labeled values;
- gate remains closed.

### P11a v2

Live:

- DB capture/consensus/readiness contract;
- Edge Function `p11_odds_capture_v2` ACTIVE v2;
- workflow source on main;
- schedule off.

Genuine odds rows remain **0** until first capture.

Immediate manual action:

`Actions -> P11 Odds Capture v2 -> Run workflow -> main -> capture=true`

The workflow verifies/configuration state of `THE_ODDS_API_KEY` and fails closed if it is absent.

Do not bypass the GitHub OIDC main-only capture path.

### P9a

Freeze/audit infrastructure is ready. It is not a trained model.

After P11/P7, verify main T-24/T-48 freeze manifests and require:

- no target values opened;
- no post-cutoff target snapshots;
- no model training performed.

## Closed research loops

Do not reopen without materially new information/mechanism:

- P10/P10b fixed pooled-HGB path;
- P5a shrinkage;
- P6 historical Long72 signal;
- P8 simple club/opponent calibration;
- old estimator-only sweeps;
- post-hoc tuning on already inspected evidence.

## Governance

`ROBUST_RESEARCH_ADVANCE` still requires a predeclared business-derived minimum meaningful MAE improvement.

Do not derive that threshold from the first genuine scorecard or any challenger result being judged.

The old ChatGPT Beyond readiness automations remain intentionally disabled.
