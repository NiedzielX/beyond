# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-28 17:15 UTC**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired: `ΔMAE < 0`.

Readiness is only an experiment prerequisite. It is not model success.

Global guardrails remain unchanged:

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
2. Collect/score P9 and P7 prospective evidence without changing frozen rules.
3. Protect Form5 T-24 forward evidence starting 2026-10-29 17:00 UTC.
4. Keep event448 under inventory watch; do not fabricate zero inventory.
5. Continue P11 append-only odds capture and Long72/P4a accumulation without retuning.
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

## 4. P9 prospective v1 — FIRST REAL T-48 CAPTURED

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen learner:

`PIT booking-curve similarity -> fixed k=5 prior curves -> same-incumbent-family PIT residuals -> median residual -> incumbent correction`

Frozen rules:

- T-48 / T-24 only;
- k=5;
- minimum 3 residual-bearing references;
- no fit/search/tuning;
- no target attendance at prediction time;
- no late bootstrap;
- exact cutoff through cutoff +90m persistence window;
- primary metric = prospective event-balanced MAE.

Workflow:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Current schedule:

`11,26,41,56 * * * *`

### Event443 Cracovia–Motor — first genuine T-48 attempt

Exact T-48: **2026-10-28 17:00:00 UTC**.

Attempt persisted: **2026-10-28 17:00:42.692 UTC**.

Result:

`PIT_SUPPORT_INSUFFICIENT`

Details:

- target incumbent family: `d2_long72_forward_predictions_v1`;
- selected curve neighbors: **[3,23,4,21,20]**;
- usable same-family residual references: **2/3 required**;
- usable refs: **23,21**;
- missing same-family PIT incumbents: **3,4,20**;
- prediction rows: **0**;
- scored events: **0**;
- production activation: false;
- `live_adjustment=0`;
- production change: false.

This is a correct fail-closed. It is neither a model win nor a model loss. Do not relax the 3-reference gate.

### Source-family rule

P9 v1 prefers a fresh Long72 incumbent when one exists within the frozen staleness limit; otherwise it falls back to Structural Prior. Reference residuals must use the same family selected for the target.

Current historical outcome-backed reference coverage at T-48:

- Long72 family: **5 events** `[10,16,21,22,23]`;
- Structural Prior family: **9 events** `[5,10,11,16,19,20,21,22,23]`.

Long72 therefore carries materially higher same-family support risk. Do not change target-family selection inside v1 after observing the first fail-closed.

## 5. P9 live preflight

Current summary:

- attempt events: **1**;
- attempt rows: **1**;
- prediction-ready attempts: **0**;
- support-insufficient attempts: **1**;
- prediction rows: **0**;
- scored events: **0**;
- prospective MAE: unavailable.

Current 10-day preflight:

- **critical: 0**;
- **watch: 1**.

The only watch is event448 Wisła Kraków–Cracovia (`WATCH_NO_SNAPSHOT`).

Near-term P9 windows:

- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**;
- event445 Zagłębie–Korona T-48: **2026-10-31 17:00 UTC**;
- event447 Raków–Pogoń T-48: **2026-10-31 19:30 UTC**.

`export_p9_prospective_inputs_v1()` intentionally exposes targets only inside the exact immutable cutoff window. Do not bypass this to precompute tomorrow's nearest neighbors.

## 6. P9 observability — LIVE

Immutable attempt registry records genuine windows even when no prediction is emitted.

Dashboard distinguishes:

- no captured window;
- `PREDICTION_READY`;
- `PIT_SUPPORT_INSUFFICIENT`;
- `NO_TARGET_INCUMBENT`.

Current dashboard correctly shows:

- attempts 1;
- support-insufficient 1;
- predictions 0;
- scored 0;
- production OFF.

## 7. Event5091 Motor Lublin–Wisła Płock — FIXED END-TO-END

Previous P9 blocker: `WATCH_NO_INCUMBENT`.

Root cause:

Structural Prior Materializer skipped the event with `missing_capacity`.

Verified football capacity was added through the normal capacity registry:

- club key: `motorlublin`;
- venue: Arena Lublin;
- seated football capacity: **15,243**;
- source: official MOSiR Lublin venue material;
- 19,000 is the broader maximum event capacity including floor use and is not used as football capacity.

Repo migration:

`supabase/sql/motor_lublin_verified_capacity_v1.sql`

PR 191 merged, commit:

`214694ee142785ee64896ae21b4934c843183cbf`

After the data fix:

- Structural Prior input became `ready`;
- normal materializer produced prior `id=52`;
- Structural Prior P50 = **13,569**;
- live orchestrator run 178 processed the event normally;
- missing prior count dropped **2 -> 1**;
- P9 preflight for 5091 is now `READY` at T-48 and T-24.

Do not revisit 5091 as a missing-prior problem unless live state changes.

## 8. Event448 Wisła Kraków–Cracovia — GENUINE NO-INVENTORY WATCH

Current:

- kickoff `2026-11-06 19:30 UTC`;
- T-48 `2026-11-04 19:30 UTC`;
- Structural Prior exists;
- P9 status `WATCH_NO_SNAPSHOT`;
- canonical ticket event provider = `roboticket`;
- external event id = **11718**;
- discovery identity is correct;
- direct page is public, HTTP 200, no login redirect;
- direct page identity is `Wisła Kraków - Cracovia`;
- candidate is linked to ticket_event448.

Main promoted RoboTicket collector is dynamic and already includes event448. Cron:

`roboticket_additional_15m` -> `5,20,35,50 * * * *`

Observed collector behavior across repeated runs:

`wislakrakow/11718 returned no ticket sectors`

The other tracked RoboTicket events collect normally in the same runs.

Therefore:

- discovery is not the blocker;
- canonical event mapping is not the blocker;
- collector is not being skipped;
- no canonical snapshot is written because provider currently exposes no ticket sectors.

This must remain **unknown / unavailable**, not `available_total=0`.

Do not fabricate a snapshot. Continue forward polling. Investigate parser/API shape only if the provider visibly opens ticket sectors while the collector still returns none.

## 9. P7 prospective — ACTIVE

Historical frozen result:

- anchor MAE **7409.79**;
- challenger MAE **6339.99**;
- point gain **1069.80 / 14.44%**;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Current prospective state:

- immutable prediction rows: **53**;
- independent events: **6**;
- scored events: **0**.

Collect/score only. No retuning.

## 10. Long72 — FROZEN / LOW PRIORITY

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

Forward workflow:

`.github/workflows/d2-long72-forward-prospective-v1.yml`

Schedule:

`17 * * * *`

At **2026-10-28 17:15 UTC**, upcoming 446/6/444/445/447 still had no Long72 rows. Recheck after the normal `:17` run because fresh Long72 rows can change which incumbent family P9 v1 selects tomorrow.

Do not retune Long72.

## 11. Form5 prospective challenger — PRECOMMITTED AND LIVE

Precommit:

`ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`

Evidence contract:

`supabase/sql/form5_prospective_evidence_v1.sql`

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

Current:

- completed eligible events: **0/8**;
- future stream: **13 events / 12 clubs / 9 distinct values**;
- first qualifying T-24 = event443 on **2026-10-29 17:00 UTC**;
- status `PROSPECTIVE_COLLECTING`;
- MAE null;
- `live_adjustment=0`.

Do not use older/manual Form5 values for this v1.

## 12. P11 odds — ACTIVE FORWARD COLLECTION

Current:

- status `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs **6 / 6**;
- events with >=3 bookmakers **6**;
- T-24 / T-72 / T-168 coverage **5 / 5 / 0**;
- model precommitted false;
- production false.

Continue append-only capture. Never backfill closing odds.

A previous red Actions run was only a Step Summary jq quoting failure after successful quote insertion; current main already contains the reporting fix.

## 13. Rejected research lanes

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

## 14. P4a

Last verified:

- READY **4/9**;
- 3 distinct previous-home-spacing values;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move this gate.

## 15. Structural Prior / orchestrator

Latest verified state after Motor capacity fix:

- event5091 is processed normally with prior id52 / P50 13,569;
- current missing-prior count = **1**;
- remaining missing prior is far-future event452;
- current event448 issue is a missing ticket snapshot, not a prior issue.

Previously fixed fixture/capacity work for 443/447/603 remains valid.

## 16. Governance / security debt

Business minimum meaningful ΔMAE remains unset until independently derived from operational decisions.

Known unrelated Supabase debt includes:

- `public.dashboard_ticketing_fixture_coverage_v1` SECURITY DEFINER view;
- `public.export_historical_runtime_v1()` callable by anon/authenticated as SECURITY DEFINER;
- `public.get_structural_prior_v1(...)` callable by anon/authenticated as SECURITY DEFINER.

Do not conflate these with current P9/Form5 evidence work.

## 17. Cold-start command

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/CURRENT_MODEL.md`, `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`, `ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`, `ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`, and `ml/HYPE_ATTENTION_RESEARCH_2026-10-27.md`. Historical P9 is closed as NOT_EVALUABLE. P9 prospective v1 is frozen. The first real T-48 attempt for event443 was captured at 2026-10-28 17:00:42 UTC and failed closed because Long72 was the selected incumbent family and only 2/5 nearest curve neighbors had same-family PIT residuals; no prediction was emitted. Do not weaken v1. Tomorrow protect event446/6/444 T-48 and event443 T-24. Event5091 is fixed and READY after verified Motor Lublin capacity 15,243 produced Structural Prior id52 / P50 13,569 through the normal materializer. The only current P9 preflight watch is event448, where the normal RoboTicket collector probes event11718 every 15 minutes but the provider still returns no ticket sectors; keep it unknown, never zero. P7 has 53 immutable rows / 6 events / 0 scored. Long72 has 5 scored events and only +0.71% MAE improvement. P11 has 6/6 events/clubs. Form5 is precommitted with a 13-event forward stream and 0 completed eligible events. Ticketing and the tested Hype 48h variant are rejected. Production remains unchanged and `live_adjustment=0`.
