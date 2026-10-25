# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)
2. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md)
3. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
4. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)
5. [`ml/MAE_RESEARCH_ROADMAP_V4.md`](ml/MAE_RESEARCH_ROADMAP_V4.md)
6. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md)
7. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md)

Do **not** restart from Roadmap v3. Roadmap v4 is canonical.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

## Current state — 2026-10-25

### Completed today

- repository reconciliation remains complete;
- two genuine post-freeze attendance outcomes were added for events 10 and 16;
- Long72 now has **2 genuine prospective scored events**;
- **P7 Long168 frozen tournament was executed** at genuine 10/9 readiness;
- **P9a T-24/T-48 target-free main freeze audit was completed**;
- `THE_ODDS_API_KEY` is configured and visible to the P11 Edge Function;
- the P11 provider time-format bug was identified and fixed in source on `main`.

### Immediate execution order

`sync corrected P11 runtime -> first genuine P11 capture + audit -> continue Long72 prospective evidence -> accumulate P9 full-168h coverage -> accumulate P4a labels -> separately precommit any P7 follow-up -> define business ΔMAE threshold`

No production change is allowed from any of these research results.

## Repository reconciliation — DONE

The previous `main` vs `ml/p9-p11-execution-2026-10-24` divergence has been reconciled.

- PR #171 merged `main` into the active branch after deliberate conflict resolution.
- P11 and P9a contract CI passed.
- Key P11/P9a implementation blobs were verified identical on both branches.
- PR #172 merged the reconciled history back into `main` with zero file-content differences.
- Final reconciliation merge commit: `c48b0045f371f0b52b98f61d24f39f3be99ec7bb`.

Do **not** recreate P9a/P11a from scratch.

## Long72 prospective evidence

Verified genuine post-match attendance added on 2026-10-25:

- event 10 — Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 — Wisła Kraków vs Raków Częstochowa: **33,000**.

Frozen Long72 result on the first two prospective events:

- reproducible rows: **90**;
- genuine scored events: **2**;
- anchor MAE: **9,069.52**;
- frozen package MAE: **7,641.71**;
- point improvement: **1,427.80 seats / 15.74%**;
- `production_change=false`.

This is **n=2 only**. Preserve it, collect more, and do not retune/calibrate/promote from it.

## P7 Long168 — EXECUTED

The frozen P7 executor ran on genuine readiness:

- frozen independent events: **10**;
- frozen rows: **139**;
- forward held-out events / folds: **5 / 5**;
- anchor event-balanced MAE: **7,409.79**;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: **6,339.99**;
- point `ΔMAE`: **-1,069.80**;
- relative point improvement: **14.44%**;
- event improvement rate: **80%**;
- forward-fold improvement rate: **80%**;
- paired event-block 95% bootstrap interval for `ΔMAE`: **[-2,566.13, +174.47]**;
- interpretation: **`POINT_GAIN_UNCERTAINTY_LIMITED`**;
- research decision: **`ADVANCE_RESEARCH`**;
- production activation: **not allowed**;
- `live_adjustment=0`.

The interval still crosses zero and only five independent events are held out. This is a meaningful research signal, **not robust proof and not a production candidate yet**.

Canonical result: [`ml/P7_LONG168_RESULT_2026-10-25.md`](ml/P7_LONG168_RESULT_2026-10-25.md).

Do not rerun/tune the frozen P7 candidate set against this result. Any continuation must be separately precommitted.

## P9 / P9a Booking Curve

### P9a target-free freeze — COMPLETE

Main T-24/T-48 audit passed with labels/model closed.

T-24:

- manifest SHA: `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- input targets: **19**;
- representation ready: **16**;
- freeze ready: **12**;
- comparator ready: **9**.

T-48:

- manifest SHA: `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`;
- input targets: **16**;
- representation ready: **13**;
- freeze ready: **10**;
- comparator ready: **7**.

Guarantees remain:

- `target_values_opened=false`;
- `model_training_performed=false`;
- no post-cutoff target trajectory use;
- `production_change=false`.

Canonical audit: [`ml/P9A_FREEZE_AUDIT_2026-10-25.md`](ml/P9A_FREEZE_AUDIT_2026-10-25.md).

### P9 full-window learner — STILL DATA-BOUND

Current genuine completed-reference coverage:

- 168h: **5/9 events / 5 clubs**;
- 72h: **9 events / 7 clubs**;
- 48h: **12 events / 7 clubs**;
- 24h: **15 events / 9 clubs**.

Do not select/train/open the first full-168h learner before **9/9** and a separate learner precommit.

## P4a fixture context — STILL DATA-BOUND

- READY events: **5**;
- genuine labeled READY events: **2**;
- distinct labeled `previous_home_match_days`: **2**;
- required gate: `>=9 labeled AND >=3 distinct labeled values`.

Do not run or retune the ablation yet.

## P11a PIT odds — SECRET READY, RUNTIME SYNC PENDING

Purpose: add a genuinely new PIT-safe match-attractiveness / outcome-uncertainty signal, not merely collect odds for their own sake.

Current state:

- DB capture/consensus/readiness contract: live;
- `THE_ODDS_API_KEY`: **configured and verified**;
- GitHub OIDC main-only capture path: working;
- provider adapter tests/type-check: green;
- genuine raw odds rows: **0**;
- schedule: off;
- production change: false.

The first provider request exposed an integration bug: The Odds API requires `commenceTimeFrom/To` in `YYYY-MM-DDTHH:MM:SSZ`, while the deployed function sent millisecond ISO timestamps. Provider returned `422 INVALID_COMMENCE_TIME_FROM`; no rows were inserted.

The source fix is already committed on `main` (`d27d797578f18f09140ccc1723219a3e690d339a`) and strips milliseconds before the provider request. CI passed.

Important operational state: a subsequent Dashboard `Deploy updates` created a newer Edge Function version but retained the previous runtime source. Therefore the remaining blocker is **runtime synchronization of the already-fixed `main` source**, not the API key.

After runtime sync, run one main-only manual capture and audit:

1. local/provider/matched event counts;
2. mapping status and kickoff delta;
3. verified aliases only;
4. complete bookmaker-level 1X2 quotes;
5. quota headers;
6. capture batch + payload SHA lineage;
7. append-only raw rows;
8. `p11_market_context_as_known_v2(...)`;
9. `p11_market_odds_readiness_v2()`.

Keep schedule off until the first genuine capture is accepted.

## Governance / closed loops

Closed unless a materially new mechanism appears:

- P10/P10b fixed pooled-HGB path;
- old estimator-only sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple calibration;
- blind post-hoc tuning.

`ROBUST_RESEARCH_ADVANCE` still requires a predeclared **business-derived** minimum meaningful `ΔMAE`. Do not derive that threshold from P7, Long72, or another challenger result it will judge.

## Never do these

- do not backfill closing odds as historical PIT observations;
- do not insert synthetic odds;
- do not fuzzy-match ambiguous provider fixtures;
- do not enable P11 schedule before first audited capture;
- do not use future target trajectory points in P9/P9a;
- do not open P9a labels merely because freeze tooling exists;
- do not lower P9/P4 gates;
- do not retune frozen Long72 from the first prospective scores;
- do not retune frozen P7 after seeing its scorecard;
- do not change `live_adjustment` from zero without reviewed promotion.

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> forward/event-safe evaluation -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause model development.**
