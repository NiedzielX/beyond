# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-28 20:00 UTC**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired: `ΔMAE < 0`.

Readiness is only an experiment prerequisite. It is not model success.

Global guardrails:

- `live_adjustment = 0` unless explicitly promoted after review;
- no synthetic attendance labels;
- no inventory-derived attendance labels;
- no historical/PIT backfill that was not genuinely known at the time;
- no closing-odds backfill;
- no fuzzy ambiguous fixture promotion;
- hidden/unknown inventory is never interpreted as zero;
- frozen prospective lanes are not retuned after outcomes;
- production activation remains review-gated.

## 2. Immediate execution order

1. Protect every P9 T-48/T-24 immutable window.
2. Run/score P9 v1 and the separately precommitted fallback-only P9 v2 without changing either frozen rule set.
3. Protect Form5 T-24 forward evidence starting event443 on 2026-10-29 17:00 UTC.
4. Keep event448 under inventory watch; never fabricate zero inventory.
5. Continue P7, P11 and Long72 prospective accumulation without retuning.
6. Do not reopen rejected Ticketing or Hype hypotheses on the same outcomes.
7. Rank new work by expected incremental prospective MAE reduction.

## 3. P9 historical v1 — CLOSED / NOT EVALUABLE

Historical gate reached:

- T-168: **9/9 events / 9 clubs**;
- `design_precommitted=true`;
- `full_window_gate_open=true`.

Final historical result:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Support:

- T-24: **0/11 support-ready**;
- T-48: **0/9 support-ready**;
- attendance labels remained unopened;
- no historical challenger MAE result was produced.

Do not repair historical P9 retrospectively.

Read: `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`.

## 4. P9 prospective v1 — FIRST REAL WINDOW CAPTURED

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen learner:

`PIT booking-curve similarity -> fixed k=5 prior curves -> same-incumbent-family PIT residuals -> median residual -> incumbent correction`

Frozen rules:

- T-48 / T-24 only;
- exact frozen 5-neighbor P9a set;
- k=5;
- minimum 3 residual-bearing references;
- no fit/search/tuning;
- no target attendance at prediction time;
- no late bootstrap;
- exact cutoff through cutoff +90m persistence window;
- primary metric = prospective event-balanced MAE.

Workflow:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Schedule:

`11,26,41,56 * * * *`

### Event443 Cracovia–Motor — first genuine T-48 attempt

Exact T-48: **2026-10-28 17:00:00 UTC**.

Attempt persisted: **2026-10-28 17:00:42.692 UTC**.

Result:

`PIT_SUPPORT_INSUFFICIENT`

Details:

- target incumbent family: `d2_long72_forward_predictions_v1`;
- selected curve neighbors: **[3,23,4,21,20]**;
- usable same-family D2 residual references: **2/3 required**;
- usable refs: **23,21**;
- missing same-family PIT incumbents: **3,4,20**;
- prediction rows: **0**;
- scored events: **0**;
- production activation: false;
- `live_adjustment=0`;
- production change: false.

This is a correct fail-closed. It is neither a model win nor a model loss. Do not relax the 3-reference gate and do not retro-predict event443 in v1.

### Current source-family support pools

T-48 outcome-backed residual-ready events:

- D2 Long72: **5** `[10,16,21,22,23]`;
- Structural Prior: **9** `[5,10,11,16,19,20,21,22,23]`.

T-24:

- D2 Long72: **5** `[10,16,21,22,23]`;
- Structural Prior: **11** `[5,10,11,15,16,18,19,20,21,22,23]`.

Global pool size is diagnostic only. Actual eligibility still depends on support among the exact frozen five selected neighbors.

## 5. P9 prospective Family Fallback v2 — PRECOMMITTED, DEPLOYED, MAIN

Scientific contract:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_FAMILY_FALLBACK_V2.md`

Precommit ID:

`p9-knn-median-residual-k5-family-fallback-v2`

Why v2 exists:

- event443 v1 failed before outcome because D2 had only 2/5 usable selected-neighbor residuals;
- the **same exact five neighbors** had 3 Structural Prior residuals (`23,21,20`);
- this is a target-free coverage failure, not an MAE result.

Frozen v2 rule:

1. Reproduce the exact v1 target-family decision and exact five P9a neighbors.
2. If the v1 family has >=3 usable selected-neighbor residuals, v2 emits nothing: `V1_COVERED`.
3. Only if v1 selected D2 and D2 support is <3 may v2 check Structural on those same five neighbors.
4. Structural fallback is allowed only with a valid PIT Structural target incumbent and >=3 usable Structural residuals.
5. If neither family satisfies the unchanged minimum support gate, v2 fails closed.
6. If v1 already selected Structural and Structural support is insufficient, v2 does not search another family.

Unchanged from v1:

- T-48 / T-24 only;
- k=5;
- minimum 3 refs;
- same neighbors;
- median residual correction;
- no model fit/search/tuning;
- target attendance forbidden at prediction time;
- exact +90m immutable persistence window;
- no production activation;
- `live_adjustment=0`.

Hard no-retro rule:

- event443 T-48 must never receive a retrospective v2 prediction;
- live DB verification after rollout: event443 v2 attempts **0**, predictions **0**, scores **0**.

Implementation:

- builder: `ml/p9_booking_curve_prospective_family_fallback_v2.py`;
- tests: `ml/test_p9_booking_curve_prospective_family_fallback_v2.py`;
- 5 contract tests cover fallback-ready, v1-covered D2, v1-covered Structural, both-insufficient and target-outcome leak rejection;
- migration: `supabase/sql/p9_booking_curve_prospective_family_fallback_v2.sql`;
- separate immutable private attempt/prediction/score ledgers;
- service-role-only RPCs;
- gateway modes: `fallback-summary-v2`, `record-fallback-attempt-v2`, `persist-fallback-v2`, `score-fallback-v2`.

Security:

- anon/authenticated EXECUTE denied for v2 RPCs;
- anon/authenticated SELECT denied on v2 private tables;
- service_role only;
- post-DDL security advisor showed no new v2 security finding.

Repo/main:

- PR **#199** merged;
- main SHA: **`e710d8b49e7a764561e2bdc7663bca74ed0d1174`**;
- `P9 Family Fallback v2 Contract` run #3 = **SUCCESS**;
- P9 integration run **40758645007 / run #20 = SUCCESS** after merge.

Current v2 live state after integration run:

- attempt rows: **0**;
- prediction rows: **0**;
- scored events: **0**;
- event443 rows: **0**;
- production activation false;
- `live_adjustment=0`;
- production change false.

No genuine post-precommit P9 window has occurred yet, so zero v2 rows are expected.

## 6. P9 live preflight — 2026-10-28 ~19:58 UTC

Current 10-day preflight:

- **critical: 0**;
- **watch: 1**.

Only watch:

- event448 Wisła Kraków–Cracovia = `WATCH_NO_SNAPSHOT`.

Near-term windows:

- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC** — READY;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC** — READY;
- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC** — READY;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC** — READY;
- event445 Zagłębie–Korona T-48: **2026-10-31 17:00 UTC** — READY;
- event447 Raków–Pogoń T-48: **2026-10-31 19:30 UTC** — READY.

Current family diagnostic is still allowed to change before future cutoffs because fresh Long72 incumbents can appear. Do not precompute tomorrow's exact neighbors outside the immutable window.

## 7. P9 observability

P9 v1 immutable attempt registry is live and dashboard-safe.

Dashboard distinguishes:

- no captured window;
- `PREDICTION_READY`;
- `PIT_SUPPORT_INSUFFICIENT`;
- `NO_TARGET_INCUMBENT`.

Current v1 dashboard state:

- attempts 1;
- support-insufficient 1;
- predictions 0;
- scored 0;
- production OFF.

P9 v2 has a separate private summary/RPC and must remain separately auditable. Do not merge v1/v2 into one MAE result.

## 8. Long72 — FROZEN / LOW MAE PRIORITY, HEARTBEAT VERIFIED

Current scored events: **5**.

Overall:

- anchor MAE **6082.40**;
- package MAE **6039.39**;
- improvement **43.01 / 0.71%**;
- event improvement rate **60%**;
- worst event degradation **3633.23**.

By band:

- 24–48h worsens MAE by **105.08**;
- 48–72h improves MAE by **191.10**.

Do not retune Long72.

Operational issue found 2026-10-28:

- independent 4x/hour Long72 cron did not emit scheduled runs for roughly two hours;
- manual safe rerun of the existing forward workflow succeeded and refreshed rows around **19:44 UTC** for events 443/446/6/444.

Fix:

- PR **#198** merged;
- commit **`c8769d49c06a536adb1500e8f54c528bb45f644e`**;
- Long72 no longer relies on its independent cron;
- it now runs from `workflow_run` after successful **Structural Prior Materializer** completion;
- `workflow_dispatch`, PR and push validation remain available;
- frozen package, persistence and scoring are unchanged.

End-to-end proof:

- Structural Prior Materializer run149 attempt3 was deliberately rerun after the fix and completed successfully;
- its completion automatically created Long72 run **40759137164 / run #45**, event=`workflow_run`, on current main SHA `e710d8b...`;
- Long72 `validate` = **SUCCESS**;
- Long72 `prospective-main` = **SUCCESS**;
- forward fetch, frozen materialization, immutable persist, scoring and artifact upload all completed successfully;
- resulting DB rows created at **2026-10-28 19:59:58 UTC** include fresh Long72 observations for event443, 446 and 444;
- event6 retains its earlier valid Long72 row; 445/447 still have no Long72 row and remain Structural candidates.

Heartbeat issue is CLOSED unless a future Structural completion fails to trigger Long72.

## 9. Form5 prospective challenger — PRECOMMITTED AND READY FOR FIRST T-24

Precommit:

`ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen:

- source exactly `TheSportsDB v1 shadow`;
- immutable prospective T-24 snapshots only;
- comparator = true immutable baseline;
- LOCO primary / LOEO secondary;
- ridge alpha **30**;
- correction cap **±25%**;
- global gate **8 events / 5 clubs / >=2 distinct values**;
- per-fold minimum **5 train events / 4 clubs / non-zero x_sd**;
- MAE hidden until complete gate/fold support;
- production OFF.

Current 2026-10-28 state:

- completed eligible events: **0/8**;
- future stream: **13 events / 12 clubs / 9 distinct values**;
- first qualifying T-24 = event443 on **2026-10-29 17:00 UTC**;
- event443 has fresh `sport.form5=4`, full five-match lineage, captured before cutoff;
- status `PROSPECTIVE_COLLECTING`;
- MAE null;
- `live_adjustment=0`.

Do not use older/manual Form5 values for this v1.

## 10. P7 prospective — ACTIVE

Historical frozen result:

- anchor MAE **7409.79**;
- challenger MAE **6339.99**;
- point gain **1069.80 / 14.44%**;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Current prospective state from latest verified handoff:

- immutable prediction rows: **53**;
- independent events: **6**;
- scored events: **0**.

Collect/score only. No retuning.

## 11. P11 odds — ACTIVE FORWARD COLLECTION

Latest verified:

- status `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs **6 / 6**;
- events with >=3 bookmakers **6**;
- T-24 / T-72 / T-168 coverage **5 / 5 / 0**;
- model precommitted false;
- production false.

Continue append-only capture. Never backfill closing odds.

Previous red Actions runs were reporting-only failures after successful quote insertion; current main contains the safe summary fix. Do not treat them as lost odds evidence.

## 12. Rejected research lanes

### Ticketing challenger

Current leakage-safe sample:

- 19 events / 11 clubs;
- LOCO baseline MAE ~**4704.1**;
- challenger MAE ~**5427.7**;
- challenger worse by ~**723.6**.

Decision: `REJECTED_NO_UPLIFT`.

The older positive 8-event dashboard state was stale and must not be reused.

### Hype / Attention

24h media_attention:

- 10 completed events / 10 clubs;
- distinct values **1**;
- all frozen T-24 values 0;
- not testable.

mention_acceleration:

- 4 completed events / 4 clubs;
- 3 distinct values;
- below gate.

Single pre-specified 48h alternative:

- baseline MAE **4156.0**;
- challenger MAE **4225.4**;
- ΔMAE **+69.4 worse**;
- only 2/10 non-zero events.

Decision: `REJECTED_NO_UPLIFT`.

Do not search more attention windows on the same outcomes.

Read: `ml/HYPE_ATTENTION_RESEARCH_2026-10-27.md`.

## 13. Event5091 Motor Lublin–Wisła Płock — FIXED

Verified football capacity:

- Arena Lublin seated football capacity: **15,243**;
- normal Structural Prior materializer produced prior id52 / P50 **13,569**;
- P9 preflight is READY.

Do not revisit unless live state changes.

## 14. Event448 Wisła Kraków–Cracovia — GENUINE NO-INVENTORY WATCH

Current:

- kickoff `2026-11-06 19:30 UTC`;
- P9 status `WATCH_NO_SNAPSHOT`;
- canonical provider = `roboticket`;
- external event id = **11718**;
- discovery/mapping is correct;
- public page exists;
- repeated collector runs report no ticket sectors for this event while other RoboTicket events work.

Keep this **unknown/unavailable**, never zero. Continue forward polling. Investigate parser/API shape only if provider visibly opens sectors while collector still returns none.

## 15. P4a

Last verified:

- READY **4/9**;
- 3 distinct previous-home-spacing values;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move this gate.

## 16. Structural Prior / orchestrator

Current important state:

- event5091 fixed and normal;
- event448 issue is missing ticket snapshot, not prior;
- Structural Prior Materializer is the verified upstream heartbeat for Long72;
- deliberate Structural rerun -> Long72 `workflow_run` -> full prospective persistence succeeded end-to-end on 2026-10-28.

## 17. Governance / security debt

Business minimum meaningful ΔMAE remains unset until independently derived from operational decisions.

Known unrelated Supabase debt includes:

- `public.dashboard_ticketing_fixture_coverage_v1` SECURITY DEFINER view;
- `public.export_historical_runtime_v1()` callable by anon/authenticated as SECURITY DEFINER;
- `public.get_structural_prior_v1(...)` callable by anon/authenticated as SECURITY DEFINER.

Do not conflate these with current P9/Form5 evidence work.

## 18. Cold-start command

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/CURRENT_MODEL.md`, `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`, `ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`, `ml/P9_BOOKING_CURVE_PROSPECTIVE_FAMILY_FALLBACK_V2.md`, `ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`, and `ml/HYPE_ATTENTION_RESEARCH_2026-10-27.md`. Historical P9 is closed as NOT_EVALUABLE. P9 prospective v1 remains frozen. Event443 T-48 was captured correctly and failed closed because D2 had only 2/5 same-family refs. A separate fallback-only P9 v2 was precommitted before any target outcome: it preserves the exact same five neighbors and only falls D2->Structural when D2 has <3 refs and Structural has >=3 among those same five; event443 is never retro-predicted. PR199 is merged on main SHA e710d8b49e7a764561e2bdc7663bca74ed0d1174; contract CI and P9 integration run40758645007 are green; v2 DB ledgers are still zero. Tomorrow protect event446/6/444 T-48 and event443 T-24. Long72 heartbeat is verified end-to-end: Structural completion automatically created workflow_run 40759137164 and both validate/prospective-main succeeded, with fresh rows at 19:59:58 UTC. Form5 first qualifying T-24 is event443 at 2026-10-29 17:00 UTC. Event448 remains unknown/no-snapshot and must never be fabricated as zero. Production remains unchanged and live_adjustment=0.
