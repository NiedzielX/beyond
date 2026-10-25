# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-25**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/PROGRESS_TRACKING.md`;
4. `ml/MAE_RESEARCH_ROADMAP_V4.md`;
5. `ml/P7_LONG168_RESULT_2026-10-25.md`;
6. `ml/P9A_FREEZE_AUDIT_2026-10-25.md`;
7. `ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`;
8. `ml/P11_CONTEXT_AUDIT_2026-10-25.md`;
9. relevant frozen precommit/result files before touching each workstream.

Do not restart from Roadmap v3. Do not reconstruct frozen experiments from memory.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Immediate order

`precommit P7 prospective follow-up -> preserve scheduled P11a accumulation -> preserve P11b/P11d collection -> continue Long72 prospective evidence -> accumulate P9 to 9/9 -> accumulate P4a labels -> define business ΔMAE threshold`

## Current canonical state

### Long72

- genuine scored events: 2;
- anchor MAE: 9069.52;
- package MAE: 7641.71;
- point improvement: 1427.80 / 15.74%;
- no retuning from n=2.

### P7 Long168

Frozen tournament is complete and exposed:

- 10 frozen events / 139 rows;
- 5 forward held-out events/folds;
- anchor MAE 7409.79;
- best candidate `gbr-l1-depth2-n50-lr003`;
- challenger MAE 6339.99;
- point gain 1069.80 / 14.44%;
- 95% event-block CI `[-2566.13, +174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision `ADVANCE_RESEARCH`;
- production activation false.

Do not rerun/tune this tournament. The next allowed P7 step is a separately precommitted prospective validation lane.

### P9 / P9a

P9a target-free audit is complete and labels/model remain closed.

Full P9 coverage:

- 168h 5/9 events / 5 clubs;
- 72h 9/7;
- 48h 12/7;
- 24h 15/9.

Full learner remains blocked until 9/9 plus separate precommit.

### P4a

- READY events 5;
- genuine labels 2;
- distinct labeled spacing values 2;
- gate >=9 labels AND >=3 distinct values;
- gate closed.

### P11a odds

Runtime/source sync is complete. Live Edge runtime is version 6.

First genuine capture:

- run `40199626764`;
- 34 raw append-only bookmaker rows;
- 2 matched events;
- both kickoff deltas 0;
- one unmatched event failed closed;
- target values false;
- production change false.

Readiness:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- events with genuine PIT 1X2: 2;
- >=3 bookmakers: 2;
- 24h / 72h / 168h: 2 / 1 / 0;
- model precommitted false.

Scheduled capture is enabled every six hours:

`17 */6 * * *`

Never backfill closing odds into earlier horizons.

### P11b price

Live PIT-safe contract:

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)`

It uses only observations captured by `as_of_at` and does not reference outcomes.

Promotion evidence is unavailable and remains null. Never infer promotion from a price change.

No P11b attendance model is opened.

### P11c absences

Only 1 active verified row / 1 team. Data-bound. Missing rows are not negative evidence.

### P11d weather / attention

Weather mechanism is already `research_only_no_uplift`; do not reopen it.

Media attention is prospective-only and still collecting; current feature variance is insufficient for evaluation.

### Governance / P12

Governance framework exists, but numeric business minimum meaningful ΔMAE remains intentionally unset.

P12 pre-plan exists and remains lower priority.

## Closed research loops

Do not reopen without materially new information/mechanism:

- P10/P10b;
- P5a;
- P6 historical Long72 incremental signal;
- P8 simple calibration;
- existing weather mechanism;
- old estimator-only sweeps;
- post-hoc tuning on inspected evidence.

The old ChatGPT Beyond readiness automations remain intentionally disabled.
