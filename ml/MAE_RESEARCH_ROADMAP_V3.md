# Beyond Ticketing — MAE Research Roadmap v3

Last updated: **2026-10-23**

Status: **CANONICAL MAE-FIRST RESEARCH PLAN**

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at every decision-relevant horizon, while keeping every comparison point-in-time safe, reproducible and honest about evidence class.**

Model complexity is not the goal. New predictive information and lower future MAE are the goal.

Primary objective:

- lower event/fixture-balanced MAE versus the incumbent at the same horizon.

Required guardrails:

- signed bias;
- median AE;
- P90 AE;
- worst-event degradation;
- event-improvement rate;
- club/horizon/fold stability;
- PIT-safe lineage and deterministic artifacts.

Production remains unchanged:

`live_adjustment = 0`

---

## 2. Scientific operating principles

1. Development and final evidence are separate.
2. Frozen packages remain immutable while new challengers receive new version IDs.
3. Time order is mandatory; random live-row/snapshot splits are not headline evidence.
4. Training objectives should match MAE where practical.
5. New features must earn inclusion through incremental OOS MAE.
6. Combination weights may be learned only inside training folds.
7. Event is the independent unit for live/context evidence.
8. Evidence class is part of every result.
9. Missing PIT state remains missing; later knowledge is never backfilled into an earlier forecast.

---

## 3. Structural core and frozen baselines

Structural Prior / Global Model family:

- 1,530 Ekstraklasa matches;
- five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- historical runtime SHA `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Previously inspected historical seasons remain exposed research evidence.

Frozen Long72 package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical exposed comparison:

- anchor MAE `3707.14`;
- P2 MAE `3012.63`;
- `ΔMAE=-694.51` / `18.73%`;
- 95% event-block interval `[-1549.89,+148.05]`;
- P2 bias `+917.05`.

Evidence labels include:

- `historical_exposed_research`;
- `historical_forward_fold`;
- `historical_pit_replay`;
- `delayed_label_precommitted`;
- `true_post_freeze_prospective`;
- `true_post_freeze_prospective_context`.

Never call inspected historical holdouts unseen again. Never call replayed historical anchors genuinely persisted forecasts.

---

## 4. Two-lane operating model

### Lane A — evidence

Continue without retuning:

- final24 prospective scoring;
- Long72 forecast-before-label persistence;
- append-only outcome scoring;
- schedule-as-known capture;
- fixture-context sidecar;
- next-opponent-attractiveness sidecar;
- Long168 observation accumulation.

### Lane B — MAE R&D

Every material feature/model/weight/target change gets a new challenger/version.

Frozen packages are never mutated.

---

## 5. Current roadmap status

Always refresh current counts from:

`public.ml_research_readiness_v1()`

Latest checkpoint on 2026-10-23:

- Long72 reproducible forecasts: `66`;
- Long72 genuine scored events: `0`;
- P4 fixture-context sidecar: `66 / 64 READY`;
- P4a independent READY events: `5`;
- P4a labeled READY events: `0`;
- P4 next-opponent sidecar: `66 / 0 READY`;
- P7 Long168: `8/9` independent events >72h, `110` rows >72h.

| Item | Status | Current decision |
|---|---|---|
| P1 temporal validation | ✅ DONE | strict expanding-season + forward-event canonical |
| P2 MAE-native estimator tournament | ✅ DONE | no robust structural replacement |
| P3 `ΔMAE` uncertainty | ✅ DONE | estimator signals insufficient |
| **P4a previous-home fixture spacing** | 🟡 **PRECOMMITTED / HARNESS READY / 5 READY / 0 LABELED** | wait for fixed 9-label + 3-value gate |
| P4b next-home opponent attractiveness | 🟡 DATA ACCUMULATING | 0 READY |
| P5a structural/live shrinkage | ✅ DONE | retain full frozen P2 |
| P5 structural/pre-live + context + live | ⏸ DATA-BOUND | start only if context produces incremental signal |
| P6 live incremental value | ✅ DONE HISTORICALLY | positive point signal; uncertainty/bias prevent promotion |
| **P7 72–168h** | 🟡 **HARNESS + EXECUTOR READY / 8 OF 9** | no real tournament before freeze at N>=9 |
| P8 club calibration | ✅ DONE | no robust gain |
| Production | ⛔ NOT READY | `live_adjustment = 0` |

---

## 6. Closed loops

Do not reopen without materially new evidence or mechanism:

- estimator-only tuning;
- estimator uncertainty re-analysis on the same sample;
- simple structural/live convex shrinkage;
- historical Long72 incremental-value loop;
- simple post-hoc club/opponent calibration.

---

## 7. P4a — previous-home spacing context experiment

### Research question

> **Does `previous_home_match_days` reduce event-level attendance MAE beyond the frozen Long72 pre-live T3+B2 anchor?**

This is the first controlled P4 context ablation.

Canonical files:

- `supabase/sql/p4_fixture_context_precommit_v1.sql`;
- `ml/p4_fixture_context_harness_v1.py`;
- `ml/test_p4_fixture_context_harness_v1.py`;
- `.github/workflows/p4-fixture-context-precommit-v1.yml`;
- `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md`.

### Independent unit and row selection

Independent unit:

`ticket_event`

Use exactly one row per event:

> first READY fixture-context row attached to a reproducible Long72 prediction.

Snapshot rows are not independent evidence for this experiment.

### P4a anchor

Control ID:

`long72-prelive-t3-b2-anchor`

Definition:

- frozen Structural Prior T-3;
- plus frozen B2 current-season residual correction;
- no Long72 live/P2 signal.

P4a therefore measures incremental fixture-context value before P5 combination work.

### Primary feature frozen before labels

Only:

`previous_home_match_days`

Current target-free values across the first five READY events:

`13, 36, 15, 14, 15`

- coverage `5/5`;
- four distinct values;
- range `13–36` days;
- genuine labeled events `0`.

### Hard research-start gate

Real P4a evaluation is prohibited until both are true:

1. at least `9` labeled independent events with non-null spacing;
2. at least `3` distinct labeled spacing values.

This gate is already frozen. It must not be changed after outcomes/model results appear.

`N=9` starts research only; it is not production sufficiency.

### Target separation and freeze order

Canonical exports:

- `public.export_p4_fixture_context_inputs_v1()` — target-free context/anchor identities;
- `public.export_p4_fixture_context_labels_v1()` — labels only.

Mandatory order:

1. fetch target-free inputs;
2. reject target leakage;
3. freeze event/context/anchor/feature identities;
4. persist deterministic manifest SHA;
5. only on explicit execute open labels;
6. reproduce the freeze;
7. enforce 9/3 gate;
8. run strict forward-event evaluation.

Automatic main runs never fetch labels.

Real pre-label audit run `40012547250` passed:

- event count `5`;
- distinct spacing values `4`;
- target values opened `false`;
- model training performed `false`;
- freeze SHA `15cb691b8874dee1e086089f90c9f239b703f9b33894945debe0c819ec73fc86`;
- artifact id `12527550414`;
- artifact digest `sha256:6900f48ab5a6d84ed9cd282fd70bea17c6cc51ee55d18b134ae36055f52dc519`.

### Fixed P4a v1 candidate family

Control:

`long72-prelive-t3-b2-anchor`

Challenger:

`q50-linear-prev-home-spacing-a002`

Specification:

- target residual = actual attendance - anchor P50;
- only feature = `previous_home_match_days`;
- median imputation;
- `RobustScaler`;
- `QuantileRegressor`;
- quantile `.50`;
- alpha `.002`;
- solver `highs`;
- no hyperparameter search.

### Validation and uncertainty

- strict forward-event validation;
- minimum five training events;
- tied kickoffs cannot train one another;
- no random snapshot split;
- exact fold manifest SHA;
- paired event-block bootstrap;
- 5,000 draws;
- seed 42.

Advance only if all pass:

1. strict-forward MAE below anchor;
2. event improvement rate >50%;
3. forward-fold improvement rate >50%;
4. freeze/PIT/lineage gates pass.

Otherwise:

`RETAIN_ANCHOR`

No P4a result can directly activate production.

### Features excluded from P4a v1

`next_home_match_days`:

- current coverage 1/5;
- sparse;
- missing is not zero;
- requires a separate future experiment/version.

Fixture-density 7/14/30d, team/home:

- currently one distinct event-level value each;
- inactive until genuine variance exists;
- requires a separate precommit before modeling.

---

## 8. P4b — next-home opponent attractiveness

Infrastructure is operational and fail-closed.

Current state:

`0 READY`

READY requires schedule knowledge and historical opponent/outcome knowledge to exist by forecast `as_of_at`.

Never reconstruct missing values from later/final knowledge.

When the first READY row appears:

1. inspect availability/variance only;
2. predeclare a separate sparse-feature experiment before fitting;
3. do not silently add it to P4a v1.

---

## 9. P5 — structural/pre-live + context + live

Start only after a P4 context experiment demonstrates genuine incremental signal.

Candidate components:

- Structural/Pre-live anchor;
- validated P4 context component;
- Long72 live/P2 where within contract;
- final24 live signal where within contract.

Test in order:

1. simple mean;
2. median;
3. fixed convex combination;
4. MAE-optimized convex weights learned inside train folds only;
5. regularized stacker only if simpler approaches fail.

Always compare to the best single component. Never learn weights on evaluation folds.

---

## 10. P7 — 72–168h expansion

Current state:

- independent events >72h: `8/9`;
- rows >72h: `110`;
- real model training remains prohibited.

Canonical implementation:

- `ml/p7_long168_harness_v1.py`;
- `ml/p7_long168_anchor_replay_v1.py`;
- `ml/p7_long168_tournament_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `.github/workflows/p7-long168-executor-v1.yml`.

### P7 question

> Does PIT live ticket trajectory in `72 < h <= 168` reduce event-balanced MAE beyond the Structural Prior T-7 control?

### Historical T-7 boundary

Current historical Long168 events do not have persisted T-7 rows.

Use frozen Runtime v1 historical replay only, classified as:

`historical_pit_replay`

with:

`persisted_forecast = false`

Never present replay as a genuinely persisted forecast.

Frozen lineage:

- T-7 artifact SHA `97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`;
- historical runtime SHA `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

The real 8-event anchor audit passed target-attendance invariance 8/8.

### P7 fixed candidates

- `anchor-only-t7`;
- `q50-linear-residual-a002`;
- `gbr-l1-depth2-n50-lr003`.

No broad tuning.

### P7 validation

- strict forward-event;
- minimum 5 train events;
- equal total training weight per event;
- event-balanced MAE primary;
- 72–96 / 96–120 / 120–144 / 144–168h diagnostics;
- paired event-block bootstrap 5,000 draws seed 42.

### Mandatory order at 9/9

1. re-read readiness;
2. explicit `mode=execute` dispatch;
3. freeze exact event/as-of/snapshot/bucket identities;
4. persist SHA;
5. verify historical T-7 replay package;
6. only then attach labels;
7. strict forward folds;
8. fixed tournament;
9. uncertainty;
10. research-only decision;
11. production unchanged.

`N=9` permits research start only.

---

## 11. Evaluation contract for serious challengers

Primary:

- event/fixture-balanced MAE at the relevant decision horizon/window.

Required secondary evidence:

- median AE;
- P90 AE;
- signed bias;
- worst-event degradation;
- event-improvement rate;
- club/fold/horizon stability where applicable;
- paired uncertainty for `ΔMAE`.

A challenger advances only when:

1. protocol was declared before final comparison;
2. PIT safety passes;
3. time-respecting MAE improves;
4. the gain is not one-event/one-fold driven;
5. bias/tail behavior remains acceptable;
6. artifacts/hashes are reproducible.

Production promotion is a separate reviewed decision requiring genuine future evidence.

---

## 12. Canonical readiness gates

Use:

`public.ml_research_readiness_v1()`

Current objective triggers:

1. `P7_LONG168_START` — independent events >72h reaches 9;
2. `LONG72_FIRST_GENUINE_SCORE` — first genuine prospective Long72 score;
3. `P4_PREVIOUS_HOME_SPACING_START` — >=9 labeled P4a events and >=3 distinct spacing values;
4. `P4_NEXT_OPPONENT_FIRST_READY` — first READY next-opponent row.

No automatic chat notification is required; inspect readiness when actively working on the project.

---

## 13. Immediate execution sequence

Continue automatically in infrastructure:

- Long72 forecast-before-label persistence;
- outcome-history sync;
- completed-event scoring;
- schedule-as-known capture;
- fixture-context sidecar;
- next-opponent sidecar;
- Long168 raw evidence accumulation.

If P7 reaches 9/9 first:

`readiness -> explicit P7 execute -> freeze -> T7 replay verification -> labels -> forward tournament -> uncertainty -> decision`

If P4a reaches 9 labeled + 3 distinct values first:

`explicit P4a execute -> target-free freeze -> labels -> gate verification -> strict forward spacing ablation -> uncertainty -> decision`

If P4a advances:

`P5 structural/pre-live + context + live`

Do not spend cycles on:

- retuning frozen packages;
- blind hyperparameter sweeps;
- random live snapshot validation;
- reopening closed calibration loops;
- adding unprecommitted context features;
- model complexity without new predictive information.

---

## 14. Implementation / CI rule

Every material experiment follows:

`hypothesis -> PIT contract -> precommit -> code/tests -> freeze identities -> labels only after freeze -> temporal evaluation -> uncertainty -> artifacts/hashes -> result doc -> decision -> canonical docs`

CI should enforce where applicable:

- deterministic seeds;
- pinned dependencies;
- input/data/artifact hashes;
- target-leakage assertions;
- as-of/kickoff ordering;
- no self/future leakage;
- persisted fold identities;
- machine-readable output;
- explicit evidence class;
- explicit decision;
- production remains off unless separately reviewed.

---

## One-line handoff

> **P1/P2/P3/P5a/P6/P8 are closed. P4a and P7 are both fully precommitted and data-bound: P4a is 5 READY / 0 labeled with a frozen 9-label + 3-value gate; P7 is 8/9. The next model run must be triggered by genuine evidence, not more tuning.**
