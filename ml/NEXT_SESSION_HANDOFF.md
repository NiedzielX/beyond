# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-28 17:04 UTC**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction: `ΔMAE < 0`.

Readiness metrics are prerequisites for evidence, not model success.

Production remains unchanged:

- `live_adjustment = 0`
- no automatic production activation
- no historical/PIT backfill that was not genuinely known at the time
- no retuning of frozen prospective lanes after outcomes

Canonical plan: `ml/EXECUTION_PLAN_CURRENT.md`.

## 2. Immediate execution order

1. protect every P9 T-48/T-24 immutable window;
2. collect/score P9 and P7 prospective evidence without weakening frozen rules;
3. protect Form5 T-24 forward evidence starting 2026-10-29 17:00 UTC;
4. fix forward data-acquisition blockers for event 5091 (missing incumbent) and event 448 (missing inventory snapshots) before their 2026-11-04 T-48 windows;
5. continue P11 append-only odds capture and Long72/P4a accumulation without retuning;
6. do not reopen rejected Ticketing or Hype hypotheses on the same outcomes;
7. prioritize new work by expected incremental prospective MAE reduction, not novelty or readiness counts.

## 3. P9 historical v1 — CLOSED / NOT EVALUABLE

Canonical historical gate:

- T-168: **9/9 events / 9 clubs**;
- `design_precommitted=true`;
- `full_window_gate_open=true`.

Frozen historical result:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Support:

- T-24: **0/11 support-ready**;
- T-48: **0/9 support-ready**;
- attendance labels remained unopened;
- no historical learner MAE result was produced.

Root cause was historical incumbent-ledger coverage, not booking-curve coverage. Never repair it retrospectively.

Read: `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`.

## 4. P9 prospective v1 — FIRST REAL WINDOW CAPTURED

Precommit: `ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`.

Frozen learner:

`PIT booking-curve similarity -> fixed k=5 prior curves -> same-incumbent-family PIT residuals -> median residual -> incumbent correction`

Frozen rules:

- T-48 / T-24 only;
- minimum 3 residual-bearing references;
- no fit/search/tuning;
- no target attendance at prediction time;
- no late bootstrap;
- persistence window = exact cutoff through cutoff + 90m;
- primary metric = prospective event-balanced MAE.

Workflow:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Current schedule:

`11,26,41,56 * * * *`

Gateway:

`supabase/functions/p9_booking_curve_prospective_v1`

### First genuine prospective result — event 443 Cracovia–Motor, T-48

Exact cutoff: **2026-10-28 17:00:00 UTC**.

The immutable attempt was persisted at **17:00:42.692 UTC** and the full workflow completed green.

Canonical attempt status:

`PIT_SUPPORT_INSUFFICIENT`

Details:

- target incumbent family: `d2_long72_forward_predictions_v1`;
- selected booking-curve neighbors: **[3, 23, 4, 21, 20]**;
- valid same-family residual references: **2/3 required**;
- usable same-family refs: **23, 21**;
- missing same-family PIT incumbents: **3, 4, 20**;
- prediction rows produced: **0**;
- scored events: **0**;
- `production_activation_allowed=false`;
- `live_adjustment=0`;
- `production_change=false`.

This is a legitimate frozen fail-closed. It is not a model loss and not a model win. Do not weaken the minimum-three-residual gate.

### Important source-family behavior

The frozen builder prefers a fresh `d2_long72_forward_predictions_v1` incumbent when one exists within its 6h staleness limit. Otherwise it falls back to `structural_prior_forecasts_v1`.

Once the target incumbent family is selected, reference residuals must use that same family.

For event443, a fresh Long72 target incumbent existed, so the target used Long72 even though a Structural Prior also existed. Long72 historical same-family coverage among the five selected curve neighbors was only 2/5, causing the fail-closed.

Do not change this behavior inside P9 v1. If a structural-anchor-only variant is ever tested, it must be a separately precommitted prospective lane, not an after-the-fact mutation of v1.

## 5. P9 current live state and upcoming windows

Current canonical summary:

- attempt events: **1**;
- attempt rows: **1**;
- prediction-ready attempts: **0**;
- support-insufficient attempts: **1**;
- prediction rows: **0**;
- scored events: **0**;
- prospective MAE: not available yet.

Current 10-day preflight:

- critical: **0**;
- watch: **2**.

Near-term ready windows:

- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**;
- event445 Zagłębie–Korona T-48: **2026-10-31 17:00 UTC**;
- event447 Raków–Pogoń T-48: **2026-10-31 19:30 UTC**.

Long72 forward workflow runs hourly at minute `17`. At the 2026-10-28 17:04 UTC check, upcoming 446/6/444/445/447 did not yet have Long72 forward rows, but they may acquire fresh rows before their P9 cutoffs. Therefore tomorrow's P9 source family cannot be assumed in advance.

Do not assume the event443 support failure will repeat, but treat same-family Long72 support as an elevated risk.

## 6. P9 attempt observability / dashboard — LIVE

P9 prospective attempts are immutable and stored even when no prediction is emitted.

Browser-facing aggregate status distinguishes:

- no window captured yet;
- `PREDICTION_READY`;
- `PIT_SUPPORT_INSUFFICIENT`;
- `NO_TARGET_INCUMBENT`.

Current dashboard state correctly shows:

- 1 attempt;
- 1 support-insufficient;
- 0 predictions;
- 0 scored;
- production OFF.

This prevents `0 predictions` from being misread as `nothing happened`.

## 7. P7 prospective — ACTIVE

Historical frozen result:

- anchor MAE **7409.79**;
- challenger MAE **6339.99**;
- point gain **1069.80 / 14.44%**;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Current prospective state at 2026-10-28 17:04 UTC:

- immutable prediction rows: **53**;
- independent prediction events: **6**;
- scored rows/events: **0 / 0**;
- latest prediction persisted 2026-10-28 13:29 UTC.

Collect/score only. No retuning.

## 8. Long72 — LOW PRIORITY, FROZEN

Current prospective scored events: **5**.

Overall 24–72h event-balanced result:

- anchor MAE: **6082.40**;
- package MAE: **6039.39**;
- improvement: **43.01 / 0.71%**;
- event improvement rate: **60%**;
- worst event degradation: **3633.23**.

By band:

- 24–48h: package worsens MAE by **105.08**;
- 48–72h: package improves MAE by **191.10**.

Do not retune or promote based on this small/weak result.

Prospective forward workflow schedule:

`.github/workflows/d2-long72-forward-prospective-v1.yml` -> `17 * * * *`.

## 9. Form5 prospective challenger — PRECOMMITTED AND LIVE

Precommit:

`ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`

Evidence contract:

`supabase/sql/form5_prospective_evidence_v1.sql`

Frozen design:

- source must be exactly `TheSportsDB v1 shadow`;
- immutable prospective T-24 snapshots only;
- comparator = true immutable `baseline`, not rejected Ticketing;
- form5 = points from five most recent completed Ekstraklasa matches known before checkpoint;
- LOCO primary / LOEO secondary;
- fixed ridge alpha **30**;
- correction cap **±25%**;
- global gate **8 completed events / 5 clubs / >=2 distinct values**;
- per-fold minimum **5 training events / 4 clubs / non-zero x_sd**;
- no MAE is exposed until the global gate and full LOCO fold support are satisfied;
- production always off.

Current live state:

- completed eligible events: **0/8**;
- completed eligible clubs: **0/5**;
- completed distinct values: **0/2**;
- future stream: **13 events / 12 clubs / 9 distinct values**;
- first qualifying T-24: event443 on **2026-10-29 17:00 UTC**;
- status `PROSPECTIVE_COLLECTING`;
- MAE fields null;
- `live_adjustment=0`.

Do not use older/manual `sport.form5` snapshot values for this v1. Only exact TheSportsDB lineage qualifies.

## 10. P11 odds — ACTIVE FORWARD COLLECTION

Current readiness:

- status `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs with PIT 1X2: **6 / 6**;
- events with >=3 bookmakers: **6**;
- T-24 / T-72 / T-168 coverage: **5 / 5 / 0**;
- model precommitted: **false**;
- production: **false**.

Continue append-only capture. Never backfill closing odds.

A prior red Actions run was a Step Summary `jq` quoting failure after successful odds capture. Capture itself inserted genuine quotes; current main already contains the safe summary implementation. Do not patch that old failure again.

Cracovia–Motor had no unambiguous provider match in one capture cycle; do not fuzzy-match or backfill it.

## 11. Ticketing challenger — REJECTED

The old positive dashboard signal was stale because its refresh function circularly copied the stale summary table.

After fixing the refresh and using the current leakage-safe CV sample:

- sample: **19 events / 11 clubs**;
- LOCO baseline MAE: ~**4704.1**;
- LOCO challenger MAE: ~**5427.7**;
- challenger worsens MAE by ~**723.6**;
- LOEO also worsens MAE by ~**610.4**.

Decision: **REJECTED_NO_UPLIFT**.

Evidence chain now has zero positive Ticketing signal and no promotion queue entry. Do not reuse the old 8-event positive snapshot.

## 12. Hype / Attention — CURRENT LANE CLOSED UNTIL NEW FORWARD EVIDENCE

Canonical note:

`ml/HYPE_ATTENTION_RESEARCH_2026-10-27.md`

Current 24h `hype.media_attention`:

- 10 completed eligible events / 10 clubs;
- distinct values: **1**;
- all frozen T-24 values are 0;
- therefore not testable.

`hype.mention_acceleration`:

- 4 completed eligible events / 4 clubs;
- 3 distinct values;
- gate remains 8 / 5 / >=2.

One pre-specified 48h alternative was tested with strict PIT rules and true baseline:

- baseline MAE **4156.0**;
- challenger MAE **4225.4**;
- ΔMAE = **+69.4 worse**;
- only 2/10 events non-zero.

Decision: **REJECTED_NO_UPLIFT**.

Do not search more attention windows on the same outcomes.

## 13. P4a

Last verified:

- labeled READY **4/9**;
- 3 distinct previous-home-spacing values;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move the gate.

## 14. Current P9 preflight data blockers

### Event 5091 Motor Lublin–Wisła Płock

Current status:

- `WATCH_NO_INCUMBENT` at both T-48 and T-24;
- T-48 cutoff **2026-11-04 17:00 UTC**;
- ticketing is healthy: ~49 snapshots and continuing;
- live orchestrator sees the event but returns `missing_prior`;
- `get_structural_prior_v1(5091, now())` expects a T-14 prior with target cutoff **2026-10-23 17:00 UTC** and model spec `structural-prior-runtime-v1-t14-hist-base`;
- no qualifying prior is persisted yet.

Investigate through the existing Structural Prior materializer. Do not invent a prior, fixture round or historical input manually.

### Event 448 Wisła Kraków–Cracovia

Current status:

- `WATCH_NO_SNAPSHOT` at both T-48 and T-24;
- T-48 cutoff **2026-11-04 19:30 UTC**;
- Structural Prior exists;
- canonical ticket source points to RoboTicket event **11718**;
- RoboTicket discovery candidate exists, direct public page is reachable and candidate is already linked to ticket_event 448;
- canonical snapshots: **0**;
- private RoboTicket candidate snapshots for external event 11718: **0**.

Identity/discovery is therefore not the blocker. Investigate the lower-level inventory collector horizon/scheduling. Do not interpret missing inventory as zero and do not fabricate snapshots.

## 15. Structural Prior / orchestrator state

Latest checked orchestrator run had:

- active events: 20;
- processed: 18;
- missing priors: 2;
- errors: 0.

Known current issues include event5091 missing prior and event448 missing snapshot.

Previously fixed capacity/fixture resolver work for event443/447/603 remains valid.

## 16. Governance / security debt

Business minimum meaningful ΔMAE is still intentionally unset until independently derived from operational decisions.

Known unrelated Supabase debt remains, including:

- `public.dashboard_ticketing_fixture_coverage_v1` SECURITY DEFINER view;
- `public.export_historical_runtime_v1()` callable by anon/authenticated as SECURITY DEFINER;
- `public.get_structural_prior_v1(...)` callable by anon/authenticated as SECURITY DEFINER;
- RLS-protected research tables with no browser policies where intentional.

Do not conflate this debt with current P9/Form5 evidence changes.

## 17. Cold-start command

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/CURRENT_MODEL.md`, `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`, `ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`, `ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`, `ml/HYPE_ATTENTION_RESEARCH_2026-10-27.md`, and the live Supabase summaries. Historical P9 is 9/9 but NOT_EVALUABLE and must never be repaired retrospectively. The first genuine P9 prospective T-48 attempt for event443 was captured at 2026-10-28 17:00:42 UTC and failed closed with `PIT_SUPPORT_INSUFFICIENT`: Long72 was the target incumbent family, only 2/5 selected neighbors had same-family PIT residuals, and no prediction was emitted. Keep v1 frozen. Tomorrow protect event446/6/444 T-48 and event443 T-24. P7 currently has 53 immutable rows / 6 events / 0 scored. Long72 has 5 scored events with only +0.71% MAE improvement. P11 has 6/6 events/clubs and 6 events with >=3 bookmakers. Form5 is precommitted and live with 13 future events but 0 completed eligible events; first T-24 is 2026-10-29 17:00 UTC. Ticketing challenger and the tested Hype 48h variant are rejected. Watch event5091 for a genuine prior and event448 for genuine inventory snapshots. Production remains unchanged; optimize only toward true prospective event-balanced MAE.
