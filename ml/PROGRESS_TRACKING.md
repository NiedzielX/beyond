# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-23**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

The current phase is **representation-first, not tuning-first**. New work should add genuinely new information or improve how existing information is represented before reopening broad estimator searches.

Production remains unchanged:

`live_adjustment = 0`

---

# 2. Structural core

Current production/research incumbent family: **Structural Prior Runtime v1 / Global Model family**.

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- canonical history SHA: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Estimator-only MAE challengers and simple post-hoc club calibration did not justify a runtime replacement.

## Frozen Long72 package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical comparison:

- structural anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- `ΔMAE=-694.51` / `18.73%` improvement;
- 95% event-block interval `[-1549.89,+148.05]`;
- P2 bias `+917.05`.

Status: **FROZEN / GENUINE POST-FREEZE EVIDENCE ACTIVE**.

---

# 3. Roadmap v4 status

| Item | Status | Current decision |
|---|---|---|
| Evidence Lane — Long72 forecast-before-label | ✅ RUNNING | immutable forecast persistence + outcome-only scoring |
| P1 — temporal validation | ✅ DONE | strict expanding-season + forward-event canonical |
| P2 — MAE-native tournament | ✅ DONE | no robust structural replacement |
| P3 — `ΔMAE` uncertainty | ✅ DONE | estimator signals insufficient |
| **P4a — fixture context / previous-home spacing** | 🟡 **PRECOMMITTED / HARNESS READY / 5 READY EVENTS / 0 LABELS** | wait for `>=9` labeled events + `>=3` distinct spacing values |
| P4b — next-home opponent attractiveness | 🟡 DATA ACCUMULATING | fail-closed sidecar operational, still 0 READY |
| P5a — structural/live shrinkage | ✅ DONE | retain full frozen P2 |
| P5 — structural + context + live | ⏸ DATA-BOUND | start only if P4 produces incremental signal |
| P6 — live incremental value | ✅ DONE HISTORICALLY | positive point signal, uncertainty/bias prevent promotion |
| **P7 — 72–168h** | 🟡 **HARNESS + EXECUTOR READY / REAL ANCHOR AUDIT 8/8 PASS / DATA GATE 8/9** | no real tournament before freeze at N>=9 |
| P8 — club calibration | ✅ DONE | no robust gain |
| **P9 — Booking Curve / Trajectory Shape** | 🟡 **REPRESENTATION + READINESS CONTRACT READY** | accumulate genuine completed 168h reference curves; no deep sequence model yet |
| **P10 — Pooled Horizon Global Model v1** | ✅ **HISTORICAL R&D RUN COMPLETE** | positive pooled signal; `POINT_GAIN_UNCERTAINTY_LIMITED`; freeze v1 and compare next against stronger Global Model champion in P10b |
| **P11 — Match Attractiveness / Commercial Context** | 🔵 **PLAN / DATA-CONTRACT STAGE** | odds / expected quality / uncertainty / stakes before weather/social hype |
| **Governance v2 — meaningful MAE** | ✅ IMPLEMENTED | no `ROBUST_RESEARCH_ADVANCE` until business-derived minimum meaningful improvement exists |
| Production | ⛔ NOT READY | `live_adjustment = 0` |

---

# 4. P10 pooled-horizon result — frozen historical R&D evidence

Canonical result:

`ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md`

Real workflow run:

`40024979412`

Frozen run head:

`bfb50ebdf5a1800bd9516a098599b5dd751fc5e7`

Question:

> Does one model trained across T-30/T-14/T-7/T-3/T-1 improve match-balanced OOS MAE versus the same fixed HGB residual model trained separately per horizon?

Validation contract:

- independent unit = `match_key`;
- all horizons of one match remain on the same side of every fold;
- expanding season folds;
- each match contributes equal total training weight;
- paired match-block bootstrap, 5,000 draws, seed 42;
- no broad hyperparameter search.

Observed historical result:

- horizon-local MAE: **2120.93**;
- pooled MAE: **2057.46**;
- `ΔMAE = -63.47` seats;
- relative improvement: **~2.99%**;
- 95% paired match-block interval: **[-106.29, -23.20]**;
- match/event improvement rate: **59.12%**;
- fold improvement rate: **100% (3/3)**;
- pooled candidate improved all five horizons.

Interpretation under Governance v2:

`POINT_GAIN_UNCERTAINTY_LIMITED`

Why not `ROBUST_RESEARCH_ADVANCE`:

`business_meaningful_mae_threshold_not_defined`

This is an encouraging historical cross-learning signal. It is **not** production evidence and does not justify activation by itself.

### P10 v1 is now frozen

Do not change P10 v1 after observing this result.

Any next comparison or model change must be a new experiment/version. The next planned experiment is:

**P10b — pooled horizon challenger vs current Global Model v2.1 / Structural champion under a common blocked protocol.**

The purpose of P10b is to determine whether the pooled signal survives against the strongest current structural comparator, rather than only against the same HGB trained horizon-locally.

---

# 5. P9 booking-curve / trajectory-shape workstream

Canonical implementation:

- `ml/p9_booking_curve_v1.py`;
- `ml/test_p9_booking_curve_v1.py`;
- `supabase/sql/p9_booking_curve_readiness_v1.sql`;
- `.github/workflows/p9-booking-curve-readiness-v1.yml`;
- `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md`.

P9 deliberately reuses the existing trajectory infrastructure rather than duplicating it.

Target representation:

`visible PIT snapshots -> normalized trajectory -> historical curve similarity -> pickup distribution -> remaining-demand estimate -> structural residual challenger`

Canonical grid:

`168, 144, 120, 96, 72, 60, 48, 36, 24, 18, 12, 6` hours before kickoff.

PIT rules:

- no target snapshot after `as_of_at`;
- future target canonical points stay missing;
- interpolation only between already-visible target snapshots;
- no target-path extrapolation in the representation layer;
- target event cannot be its own reference;
- reference event must already be completed by target `as_of_at`;
- public inventory is a demand proxy, not confirmed paid sales.

P9 v1 intentionally starts with an auditable weighted-L1 historical similarity / pickup representation. LSTM/Transformer work is not part of v1.

Research-model fitting remains downstream of genuine completed reference-curve coverage.

---

# 6. P11 match attractiveness / commercial context

Canonical plan:

`ml/P11_MATCH_ATTRACTIVENESS_CONTEXT_V1_PLAN.md`

Priority order:

1. **P11a — PIT odds / expected match quality / outcome uncertainty / stakes / rivalry**;
2. **P11b — price / promotion state**;
3. **P11c — lineup / star strength / verified absences**;
4. **P11d — weather / attention / social hype**.

Hard PIT rule:

Closing odds, final lineup, final weather or later-known stakes information may never be backfilled into an earlier forecast cutoff.

Every family requires a separate controlled ablation before combination.

---

# 7. Governance v2 — minimum meaningful improvement

Canonical implementation:

- `ml/research_advance_governance_v2.py`;
- `ml/test_research_advance_governance_v2.py`.

Decision vocabulary:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

A robust research advance requires all of:

1. positive MAE point gain;
2. event/fold stability;
3. PIT + lineage + reproducibility pass;
4. predeclared minimum practically meaningful MAE improvement;
5. observed gain at least that large;
6. adequate precision, by default an event/match-block `ΔMAE` interval fully below zero.

Do not define the meaningful threshold from the same experiment result that it will judge.

Until a business-derived threshold exists, the strongest allowed positive state is:

`POINT_GAIN_UNCERTAINTY_LIMITED`

This deliberately prevents tiny improvements such as `3012 -> 2998` from being called robust progress merely because the point estimate is lower.

---

# 8. Closed R&D loops

Do not reopen without materially new evidence or mechanism:

- estimator-only tuning;
- estimator uncertainty re-analysis on the same sample;
- simple structural/live convex shrinkage;
- historical Long72 incremental-value loop;
- simple post-hoc club/opponent calibration.

P9/P10/P11 are valid because they test new representation/cross-learning/context hypotheses rather than another blind sweep.

---

# 9. Latest live readiness checkpoint

Canonical source:

`public.ml_research_readiness_v1()`

Checkpoint read on 2026-10-23:

## Long72

- reproducible forecasts: `66`;
- genuine scored events: `0`;
- latest reproducible as-of: `2026-10-23T18:05:02.086Z`.

## P4a fixture context

- sidecar rows: `66`;
- READY rows: `64`;
- independent READY events using first READY row: `5`;
- event IDs: `10, 16, 21, 22, 23`;
- genuine labeled READY events: `0`.

Primary P4a feature:

`previous_home_match_days`

Current target-free values:

`13, 36, 15, 14, 15`

- non-null coverage: `5/5`;
- distinct values: `4`;
- range: `13–36` days.

Explicitly inactive/split features:

- `next_home_match_days`: `1/5` non-null, separate sparse feature not in P4a v1;
- fixture-density 7/14/30d family: no useful event-level variance yet.

## P4b next-opponent attractiveness

- sidecar rows: `66`;
- READY: `0`.

Do not substitute later schedule knowledge or hand-authored opponent scores.

## P7 Long168

- independent events with valid rows >72h: `8/9`;
- rows >72h: `110`;
- research-start trigger: **false**.

Do not lower the threshold.

---

# 10. P4a fixture-context precommit

Canonical:

- `supabase/sql/p4_fixture_context_precommit_v1.sql`;
- `ml/p4_fixture_context_harness_v1.py`;
- `ml/test_p4_fixture_context_harness_v1.py`;
- `.github/workflows/p4-fixture-context-precommit-v1.yml`;
- `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md`;
- `supabase/functions/c1_alpha_training_export_v1/index.ts`.

Research question:

> Does previous-home match spacing reduce event-level attendance MAE beyond the frozen Long72 pre-live T3+B2 anchor?

Independent unit:

`ticket_event`

Exactly one input row is used per event: the first READY context row attached to a reproducible Long72 prediction.

Anchor:

`long72-prelive-t3-b2-anchor`

Hard research-start gate:

1. at least `9` labeled events with non-null `previous_home_match_days`;
2. at least `3` distinct labeled spacing values.

At the current `0/9`, model evaluation is prohibited.

Mandatory execution order:

`fetch target-free inputs -> freeze identities + SHA -> explicit execute only -> fetch labels -> reproduce freeze -> check 9/3 gate -> forward evaluation`.

Fixed P4a v1 candidate:

- control: `long72-prelive-t3-b2-anchor`;
- challenger: `q50-linear-prev-home-spacing-a002`;
- only feature: `previous_home_match_days`;
- `QuantileRegressor(q=.5, alpha=.002)`;
- `RobustScaler`;
- no hyperparameter search;
- strict forward-event validation, minimum 5 train events;
- paired event-block bootstrap, 5,000 draws, seed 42.

No P4a v1 result can activate production directly.

---

# 11. P7 precommit + executor

Canonical:

- `ml/p7_long168_harness_v1.py`;
- `ml/p7_long168_anchor_replay_v1.py`;
- `ml/p7_long168_tournament_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `.github/workflows/p7-long168-executor-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`;
- `ml/results/P7_LONG168_EXECUTOR_V1_2026-10-23.md`;
- `ml/results/P7_LONG168_ANCHOR_AUDIT_V1_2026-10-23.md`.

At `N<9`:

`P7_NOT_READY`

Historical T-7 control is explicitly:

`historical_pit_replay`

with:

`persisted_forecast = false`.

Real main-branch anchor audit:

- run id `39967794585`;
- events `1,3,4,5,11,15,18,19`;
- target-attendance invariance PASS `8/8`;
- skipped events `0`;
- package SHA `7e21831d4da724cd6906ccb34688eb8f4fadd39923054510dea1b33162862362`.

At `N>=9` the exact order remains:

`readiness -> explicit execute -> freeze identities -> verify T-7 replay -> labels -> strict forward folds -> fixed tournament -> uncertainty -> research decision`

Nine events are a research-start gate, not evidence that a small uplift is trustworthy.

---

# 12. Evidence operations

Operational pipelines remain active:

- Long72 forecast-before-label hourly;
- outcome-history sync hourly;
- completed-event Long72 scoring inside prospective cycle;
- schedule-as-known capture every 6h;
- fixture-context sidecar every 15m;
- next-opponent sidecar every 15m;
- Long168 evidence collection.

---

# 13. Immediate operating mode

## Development that can proceed now

1. **P10b:** precommit and evaluate pooled-horizon cross-learning against the current strongest Global Model v2.1 / Structural comparator under common match-blocked temporal folds.
2. **P9:** validate/deploy the readiness contract and audit genuine completed 168h curve-reference coverage; do not train a richer learner before the representation/coverage contract is stable.
3. **P11a:** design PIT odds / expected-quality / stakes ingestion and as-known contract before any model ablation.
4. **Governance/business:** derive the minimum practically meaningful MAE improvement from downstream club decisions and asymmetric error cost, not from model score distributions.

## Data-bound work

- P4a waits for `>=9` labeled independent events and `>=3` distinct spacing values;
- P7 waits for `9/9` independent >72h events;
- prospective Long72/final24 scoring continues.

## Explicitly do not do

- do not mutate frozen P10 v1 after seeing its result;
- do not re-run a broad estimator sweep merely because P10 was positive;
- do not lower P4a/P7 gates;
- do not call P10 `ROBUST_RESEARCH_ADVANCE` until the business meaningful threshold exists;
- do not activate production from historical/exposed evidence.

---

## One-line handoff

> **Roadmap v4 is representation-first: P9 booking-curve/pickup representation is being made evidence-ready; P10 v1 produced a real historical pooled-horizon gain of 63.47 MAE seats with CI below zero but remains `POINT_GAIN_UNCERTAINTY_LIMITED`; P10b must now test that signal against the strongest Global Model champion; P11a prioritizes PIT odds/quality/stakes; P4a and P7 stay frozen and data-bound; production remains off.**
