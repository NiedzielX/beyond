# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-25 11:55 Europe/Warsaw**

Status: **CURRENT EXECUTION ORDER**

Canonical strategy remains `ml/MAE_RESEARCH_ROADMAP_V4.md`.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

## Priority 0 — protect evidence integrity

- Branch reconciliation is complete; do not recreate P9a/P11a.
- Preserve frozen P4a/P7/P9 contracts.
- Do not retune Long72 from the first prospective outcomes.
- Do not reopen P10/P10b.
- Do not enable production.

## Priority 1 — first genuine P11 capture NOW

P11 is the immediate time-sensitive task because pre-match odds are perishable PIT evidence.

Already live/on `main`:

- P11 v2 DB contract;
- `p11_odds_capture_v2` ACTIVE v2;
- manual GitHub OIDC workflow;
- no automatic schedule.

Current genuine rows: **0**.

Manual dispatch required:

`Actions -> P11 Odds Capture v2 -> Run workflow -> main -> capture=true`

The workflow must verify `THE_ODDS_API_KEY` first and fail closed if absent.

After one capture, audit:

1. local/provider/matched event counts;
2. every mapping status;
3. verified aliases only;
4. bookmaker count / complete 1X2;
5. kickoff delta;
6. provider quota;
7. capture batch and payload SHA lineage;
8. raw append-only rows;
9. `p11_market_context_as_known_v2(...)`;
10. `p11_market_odds_readiness_v2()`.

Keep schedule off until accepted.

## Priority 2 — execute frozen P7 Long168

P7 canonical readiness is now **10/9**, trigger **OPEN**.

This changed after genuine outcomes for:

- event 10 Pogoń–Radomiak: 19,050;
- event 16 Wisła–Raków: 33,000.

Do not redesign the experiment. Run exactly:

`Actions -> P7 Long168 Executor v1 -> Run workflow -> main -> mode=execute`

Frozen workflow must perform:

1. hash verification;
2. live Long168/support export;
3. frozen T-7 anchor replay;
4. exact identity freeze;
5. fixed precommitted tournament;
6. artifact upload;
7. `production_change=false`;
8. `production_activation_allowed=false`;
9. `live_adjustment=0`.

Review scorecard only after the freeze is written by the workflow.

## Priority 3 — preserve first Long72 prospective evidence

Current genuine prospective state:

- scored events: **2**;
- anchor event-balanced MAE: **9069.52**;
- frozen package MAE: **7641.71**;
- point improvement: **1427.80 seats / 15.74%**;
- sample size: **2 events only**.

Decision:

- record evidence;
- keep collecting;
- no retuning;
- no promotion conclusion;
- no post-hoc calibration.

The hourly prospective workflow already scores eligible completed events after outcomes exist.

## Priority 4 — P9a main target-free freeze audit

P9a remains freeze tooling only.

Run/verify T-24 and T-48 main audits and require:

- deterministic manifests/SHAs;
- exact frozen reference/snapshot/incumbent identities;
- `target_values_opened=false`;
- `model_training_performed=false`;
- no post-cutoff target snapshots.

Do not fit the learner yet.

## Priority 5 — P9 full-168h accumulation

Fresh coverage after the 24.10 outcomes:

- 168h: **5/9 events / 5 clubs**;
- 72h: **9 events / 7 clubs**;
- 48h: **12 events / 7 clubs**;
- 24h: **15 events / 9 clubs**.

Full-168h learner remains blocked.

Allowed:

- readiness reporting;
- leakage/lineage tests;
- representation audits;
- freeze tooling.

Blocked until 9/9 + learner precommit:

- learner selection;
- hyperparameter selection;
- opening learner result comparisons.

## Priority 6 — P4a continues prospectively

Current:

- READY events: 5;
- genuine labels: **2**;
- distinct labeled `previous_home_match_days`: **2**;
- required: `>=9 labeled AND >=3 distinct labeled values`.

Gate remains closed. Do not run the ablation yet.

## Priority 7 — business minimum meaningful MAE threshold

Governance v2 still lacks the business-derived minimum meaningful `ΔMAE`.

Derive it from decisions such as staffing, security, transport, catering, hospitality and asymmetric forecast-error cost — never from the challenger results themselves.

Until approved, no result can be called `ROBUST_RESEARCH_ADVANCE`.

## Closed loops

Do not reopen without a materially new mechanism:

- P10/P10b fixed pooled-HGB tuning;
- old estimator-only sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple club/opponent calibration;
- blind post-hoc calibration.

## Next meaningful milestones

1. first genuine P11 capture audited;
2. P7 frozen tournament executed at genuine 10/9 readiness;
3. additional Long72 prospective outcomes arrive;
4. P9 reaches full 9/9 168h references;
5. P4a reaches 9 labeled / 3 distinct labeled values;
6. P9a main freeze manifests are verified.
