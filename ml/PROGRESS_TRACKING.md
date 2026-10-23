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

Current production/research incumbent family: **Structural Prior Runtime v1 / frozen Pre-Live v3 research package**.

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- canonical history SHA: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Estimator-only MAE challengers, simple post-hoc club calibration and the first pooled-horizon direct replacement do not justify a structural runtime replacement.

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
| **P9 — Booking Curve / Trajectory Shape** | 🟡 **REPRESENTATION READY / 168h DATA GATE 4/9** | keep genuine curve capture running; no learnable P9 model yet |
| **P10 — Pooled Horizon Global Model v1** | ✅ DONE | pooling beats the same local HGB: `-63.47` MAE; `POINT_GAIN_UNCERTAINTY_LIMITED` |
| **P10b — pooled vs frozen Pre-Live v3** | ✅ **DONE / NO_RESEARCH_GAIN** | pooled MAE `2067.43` vs Pre-Live v3 `1919.92`; do not replace structural champion |
| **P11a — PIT market odds** | 🟡 **DATA CONTRACT LIVE / 0 GENUINE EVENTS** | select lawful/reliable provider and begin append-only capture before any ablation |
| **Governance v2 — meaningful MAE** | ✅ IMPLEMENTED | no `ROBUST_RESEARCH_ADVANCE` until business-derived minimum meaningful improvement exists |
| Production | ⛔ NOT READY | `live_adjustment = 0` |

---

# 4. P10 pooled-horizon result — frozen historical R&D evidence

Canonical result:

`ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md`

Real workflow run: `40024979412`

Frozen run head: `bfb50ebdf5a1800bd9516a098599b5dd751fc5e7`

Question:

> Does one model trained across T-30/T-14/T-7/T-3/T-1 improve match-balanced OOS MAE versus the same fixed HGB residual model trained separately per horizon?

Observed result:

- horizon-local MAE: **2120.93**;
- pooled MAE: **2057.46**;
- `ΔMAE = -63.47` seats;
- relative improvement: **~2.99%**;
- 95% paired match-block interval: **[-106.29, -23.20]**;
- match/event improvement rate: **59.12%**;
- fold improvement rate: **3/3**;
- all five horizons improved.

Governance:

`POINT_GAIN_UNCERTAINTY_LIMITED`

Reason robust advancement is blocked:

`business_meaningful_mae_threshold_not_defined`

P10 v1 is frozen. Do not alter it after observing this result.

## 4.1 P10b — comparison against the actual frozen structural champion

Canonical result:

`ml/results/P10B_POOLED_VS_PRELIVE_V3_V1_2026-10-23.md`

Real workflow run: `40028701211`

Frozen execution commit: `dc266e25c641f9b807dac70740ae30f15ed19e73`

Artifact digest:

`sha256:599e9154d9bb2c2be0415044b3acc74eac6acb957eb7dd98bb238e38abb8eab1`

Comparator:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Evidence integrity:

- canonical history SHA verified;
- sealed Pre-Live v3 manifest SHA `b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a` verified;
- all 20 horizon × season comparator MAE cells reproduced within `1e-9`;
- complete match blocking;
- exact common forecastable support;
- 1,197 independent matches;
- 5,972 common-support PIT rows;
- 5,000 paired match-block bootstrap draws, seed 42.

Observed result:

- frozen Pre-Live v3 match-balanced MAE: **1919.92**;
- pooled challenger MAE: **2067.43**;
- `challenger - incumbent ΔMAE = +147.51` seats;
- relative degradation: **+7.68%**;
- 95% interval: **[+82.97, +210.67]**;
- probability `ΔMAE < 0`: **0.0**;
- match/event improvement: **43.69%**;
- folds improved: **0/4**;
- horizons improved: **0/5**.

Governance:

`NO_RESEARCH_GAIN`

Interpretation:

P10 v1 established a real cross-learning effect relative to the same weaker local-HGB architecture. P10b establishes that this architecture is nevertheless **materially weaker than the current frozen Pre-Live v3 package**. Do not retune P10b after the result. Any future pooled architecture must be a materially new mechanism and a new precommit; it is not the next priority.

---

# 5. P9 booking-curve / trajectory-shape workstream

Canonical implementation:

- `ml/p9_booking_curve_v1.py`;
- `ml/test_p9_booking_curve_v1.py`;
- `supabase/sql/p9_booking_curve_readiness_v1.sql`;
- `supabase/sql/ml_research_readiness_add_p9_booking_curve_v1.sql`;
- `.github/workflows/p9-booking-curve-readiness-v1.yml`;
- `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md`.

P9 reuses the existing trajectory infrastructure rather than duplicating it.

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

Live readiness on 2026-10-23:

- completed reference curves reaching 168h: **4 events / 4 clubs**;
- reaching 72h: **7 events / 5 clubs**;
- reaching 48h: **10 events / 6 clubs**;
- reaching 24h: **13 events / 8 clubs**;
- full 168h model status: `DATA_BOUND`;
- central gate `P9_BOOKING_CURVE_168_START`: **false (4/9)**.

P9 v1 intentionally starts with an auditable weighted-L1 similarity / pickup representation. LSTM/Transformer work is not part of v1. Do not fit the first learnable P9 residual challenger before the 168h reference-curve gate and a separate freeze of that learner contract.

---

# 6. P11 match attractiveness / commercial context

Canonical plan:

`ml/P11_MATCH_ATTRACTIVENESS_CONTEXT_V1_PLAN.md`

Existing infrastructure already covers more than the initial repo-only gap audit suggested:

- rivalry relations;
- stakes reconstruction;
- verified absences;
- ticket-price observations;
- weather/media infrastructure.

The primary missing family was genuine PIT market odds.

## P11a — PIT 1X2 market context v1

Canonical SQL:

`supabase/sql/p11_market_odds_context_v1.sql`

Live contract:

- append-only private 1X2 observations;
- service-role-only table/RPC access;
- `p11_market_context_as_known_v1(ticket_event_id, as_of_at)` chooses only observations captured by the requested cutoff and strictly before kickoff;
- de-vigged home/draw/away probabilities;
- normalized outcome-uncertainty entropy;
- favorite probability;
- explicit semantic guard: `expected_match_quality = NOT_DERIVED_FROM_1X2_V1`;
- `p11_market_odds_readiness_v1()` is target-free.

Current readiness:

- genuine PIT 1X2 events: **0**;
- provider selected: **false**;
- model precommitted: **false**;
- status: `NO_GENUINE_ODDS_CAPTURE_YET`.

Do not backfill closing odds to historical T-30/T-14/T-7/T-3/T-1 states. Next action is to select a lawful/reliable source and begin genuine append-only capture.

Broader P11 priority remains:

1. **P11a — PIT odds / outcome uncertainty / stakes / rivalry**;
2. **P11b — price / promotion state**;
3. **P11c — lineup / star strength / verified absences**;
4. **P11d — weather / attention / social hype**.

Expected match quality needs a distinct justified signal such as team-strength/goal-market representation; 1X2 balance alone must not be mislabeled as quality.

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

This prevents small improvements such as `3012 -> 2998` from being called robust progress merely because the point estimate is lower.

---

# 8. Closed R&D loops

Do not reopen without materially new evidence or mechanism:

- estimator-only tuning;
- estimator uncertainty re-analysis on the same sample;
- simple structural/live convex shrinkage;
- historical Long72 incremental-value loop;
- simple post-hoc club/opponent calibration;
- **P10b fixed pooled-HGB architecture as a direct Pre-Live v3 replacement**.

P9/P11 remain valid because they test genuinely new representation or information rather than another blind sweep.

---

# 9. Latest live readiness checkpoint

Canonical source:

`public.ml_research_readiness_v1()`

Checkpoint read on 2026-10-23 after P9 integration:

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

## P9 Booking Curve

- 168h genuine completed reference curves: `4/9`;
- P9 start gate: **false**;
- no learnable model precommitted yet.

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

Independent unit: `ticket_event`

Exactly one input row is used per event: the first READY context row attached to a reproducible Long72 prediction.

Anchor: `long72-prelive-t3-b2-anchor`

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

At `N<9`: `P7_NOT_READY`

Historical T-7 control is explicitly `historical_pit_replay` with `persisted_forecast = false`.

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
- Long168 evidence collection;
- P9 central readiness gate now exposed in `ml_research_readiness_v1()`.

Existing automation `Beyond ML readiness` was updated to know about P4a and P9 but remains **disabled**, preserving the user's previous automation state.

---

# 13. Immediate operating mode

## Development that can proceed now

1. **P11a data acquisition:** select a lawful/reliable odds source and implement append-only genuine PIT capture into the frozen market-odds contract. Do not backfill closing odds.
2. **Governance/business:** derive the minimum practically meaningful MAE improvement from downstream club decisions and asymmetric error cost, independently of model results.
3. **P9 preparation:** keep the representation/readiness contract stable and monitor genuine 168h coverage; first learnable residual model remains blocked at `4/9`.
4. **P11 expected quality:** design a separate justified quality signal; do not relabel 1X2 outcome balance as match quality.

## Data-bound work

- P4a waits for `>=9` labeled independent events and `>=3` distinct spacing values;
- P7 waits for `9/9` independent >72h events;
- P9 waits for `9` genuine completed 168h reference curves before freezing its first learnable residual challenger;
- prospective Long72/final24 scoring continues.

## Explicitly do not do

- do not mutate frozen P10 or P10b after seeing their results;
- do not run another pooled-HGB tuning sweep to rescue P10b;
- do not lower P4a/P7/P9 gates;
- do not call any positive result `ROBUST_RESEARCH_ADVANCE` until the business meaningful threshold exists;
- do not backfill closing odds/final lineup/final weather into earlier PIT cutoffs;
- do not activate production from historical/exposed evidence.

---

## One-line handoff

> **Roadmap v4 remains representation-first: P10 pooling produced a real cross-learning gain against a weaker local HGB but then lost decisively to frozen Pre-Live v3 in P10b (`+147.51` MAE, 0/4 folds, 0/5 horizons), so that direct replacement path is closed; P9 booking curves are technically ready but data-bound at 4/9 full-168h references; P11a now has a live PIT-safe odds contract but 0 genuine observations and needs a real provider/capture path; Governance v2 is active; P4a/P7 remain frozen and data-bound; production remains off.**
