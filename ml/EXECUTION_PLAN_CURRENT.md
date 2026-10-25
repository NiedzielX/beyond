# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-25**

Status: **CURRENT EXECUTION ORDER**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

## Priority 0 — protect evidence integrity

- Branch reconciliation is complete; do not recreate P9a/P11a.
- P7 frozen execution is complete; do not rerun/tune its inspected candidate set.
- P9a target-free audit is complete; keep labels/model closed.
- Preserve frozen Long72 and P4a contracts.
- Do not reopen P10/P10b.
- Do not enable production.

## Priority 1 — synchronize corrected P11 runtime and perform first genuine capture

P11 provider secret is **configured and verified**. The remaining blocker is not credentials.

Current live/source state:

- P11 v2 DB contract live;
- `THE_ODDS_API_KEY` configured;
- main-only GitHub OIDC verified;
- source fix for provider timestamp format committed on `main` as `d27d797578f18f09140ccc1723219a3e690d339a`;
- type-check/tests green;
- deployed Edge runtime still contains pre-fix timestamp generation after Dashboard redeploy;
- genuine rows: **0**;
- schedule: off.

Required sequence after runtime source is synchronized:

1. run one genuine main-only capture;
2. verify local/provider/matched event counts;
3. inspect every mapping status and kickoff delta;
4. require verified aliases and complete 1X2 bookmaker quotes;
5. record provider quota;
6. verify capture batch + payload SHA lineage;
7. verify raw append-only rows;
8. inspect `p11_market_context_as_known_v2(...)`;
9. inspect `p11_market_odds_readiness_v2()`;
10. keep schedule off until accepted.

Do not backfill closing odds.

## Priority 2 — continue Long72 prospective evidence

Current genuine state:

- scored events: **2**;
- anchor event-balanced MAE: **9069.52**;
- frozen package MAE: **7641.71**;
- point improvement: **1427.80 seats / 15.74%**;
- sample size: **2 events only**.

Decision:

- preserve forecasts/results;
- keep outcome sync healthy;
- score new eligible completed events prospectively;
- no retuning;
- no promotion conclusion;
- no post-hoc calibration.

## Priority 3 — accumulate P9 full-168h coverage

Current coverage:

- 168h: **5/9 events / 5 clubs**;
- 72h: **9 events / 7 clubs**;
- 48h: **12 events / 7 clubs**;
- 24h: **15 events / 9 clubs**.

Full-168h learner remains `DATA_BOUND`.

Allowed before 9/9:

- readiness reporting;
- leakage/lineage tests;
- representation audits;
- freeze tooling.

Blocked until 9/9 plus separate learner precommit:

- learner selection;
- hyperparameter selection;
- model fitting;
- opening learner result comparisons.

P9a T-24/T-48 audit is already complete; do not repeat it without a material contract/data reason.

## Priority 4 — accumulate P4a labels

Current:

- READY events: 5;
- genuine labels: **2**;
- distinct labeled `previous_home_match_days`: **2**;
- required: `>=9 labeled AND >=3 distinct labeled values`.

Gate remains closed. Do not run/retune the ablation yet.

## Priority 5 — P7 follow-up only through a new precommit

Frozen P7 result:

- anchor MAE: **7409.79**;
- best challenger MAE: **6339.99**;
- point improvement: **1069.80 / 14.44%**;
- event/fold improvement rates: **80% / 80%**;
- event-block 95% interval: **[-2566.13, +174.47]**;
- status: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision: `ADVANCE_RESEARCH`.

Because the result has now been inspected:

- do not tune `gbr-l1-depth2-n50-lr003` against the same P7 scorecard;
- do not broaden the candidate set post hoc and call it the same experiment;
- do not promote to production;
- if continuing P7, define a **new** challenger/version and evaluation protocol before new results are opened;
- favor genuinely future/prospective evidence or a materially new information mechanism.

Canonical result: `ml/P7_LONG168_RESULT_2026-10-25.md`.

## Priority 6 — business minimum meaningful MAE threshold

Governance v2 still lacks the approved business-derived minimum meaningful `ΔMAE`.

Derive it from actual forecast-driven decisions such as:

- staffing;
- security;
- transport;
- catering;
- hospitality;
- asymmetric cost of over- vs under-forecasting.

Never infer the threshold from P7, Long72, P9 or another result it will judge.

Until approved and precision is sufficient, `ROBUST_RESEARCH_ADVANCE` is unavailable.

## Completed in this execution cycle

### P7 Long168

Frozen tournament executed on 10 independent events / 139 rows. Result is an uncertainty-limited point gain. See `ml/P7_LONG168_RESULT_2026-10-25.md`.

### P9a T-24/T-48

Target-free main freeze audit complete.

- T-24 manifest: `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- T-48 manifest: `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`;
- targets not opened;
- no model training;
- no future target points;
- production unchanged.

See `ml/P9A_FREEZE_AUDIT_2026-10-25.md`.

## Closed loops

Do not reopen without a materially new mechanism:

- P10/P10b fixed pooled-HGB tuning;
- old estimator-only sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple club/opponent calibration;
- blind post-hoc calibration.

## Next meaningful milestones

1. corrected P11 runtime synchronized and first genuine capture audited;
2. additional Long72 prospective outcomes scored;
3. P9 reaches full **9/9** 168h reference coverage and a learner is separately precommitted;
4. P4a reaches **9 labeled / 3 distinct** values;
5. a separate P7 follow-up is precommitted only if the research question remains valuable;
6. business minimum meaningful `ΔMAE` is approved.
