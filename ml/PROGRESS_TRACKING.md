# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-23**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V3.md`

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains unchanged:

`live_adjustment = 0`

---

# 2. Structural core

Current incumbent: **Structural Prior Runtime v1 / Global Model family**.

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

# 3. Roadmap status

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
| Production | ⛔ NOT READY | `live_adjustment = 0` |

---

# 4. Closed R&D loops

Do not reopen without materially new evidence or mechanism:

- estimator-only tuning;
- estimator uncertainty re-analysis on the same sample;
- simple structural/live convex shrinkage;
- historical Long72 incremental-value loop;
- simple post-hoc club/opponent calibration.

---

# 5. Latest live readiness checkpoint

Canonical source:

`public.ml_research_readiness_v1()`

Checkpoint read on 2026-10-23 at ~19:31 UTC:

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

### Primary P4a feature

`previous_home_match_days`

Current target-free values:

`13, 36, 15, 14, 15`

- non-null coverage: `5/5`;
- distinct values: `4`;
- range: `13–36` days.

### Explicitly inactive P4a features

`next_home_match_days`:

- non-null coverage `1/5`;
- status: `SEPARATE_SPARSE_FEATURE_NOT_IN_P4A_V1`;
- missing is not zero.

Fixture-density family:

- all 7/14/30d team/home density features currently have one distinct event-level value;
- status: `INACTIVE_UNTIL_REAL_VARIANCE`.

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

# 6. P4a fixture-context precommit

Canonical:

- `supabase/sql/p4_fixture_context_precommit_v1.sql`;
- `ml/p4_fixture_context_harness_v1.py`;
- `ml/test_p4_fixture_context_harness_v1.py`;
- `.github/workflows/p4-fixture-context-precommit-v1.yml`;
- `ml/results/P4_FIXTURE_CONTEXT_PRECOMMIT_V1_2026-10-23.md`;
- `supabase/functions/c1_alpha_training_export_v1/index.ts`.

## Research question

> Does previous-home match spacing reduce event-level attendance MAE beyond the frozen Long72 pre-live T3+B2 anchor?

## Independent unit

`ticket_event`

Exactly one input row is used per event: the first READY context row attached to a reproducible Long72 prediction.

## Anchor

`long72-prelive-t3-b2-anchor`

This is:

- Structural Prior T-3;
- plus frozen B2 current-season correction;
- no live Long72/P2 signal.

P4a therefore isolates context value before P5 combination research.

## Hard research-start gate

Both must be true:

1. at least `9` labeled events with non-null `previous_home_match_days`;
2. at least `3` distinct labeled spacing values.

At the current `0/9`, model evaluation is prohibited.

## Target separation

Inputs and labels are separate RPCs:

- `export_p4_fixture_context_inputs_v1()` — target-free identities/features/anchor;
- `export_p4_fixture_context_labels_v1()` — labels only.

Mandatory order:

`fetch target-free inputs -> freeze identities + SHA -> explicit execute only -> fetch labels -> reproduce freeze -> check 9/3 gate -> forward evaluation`.

Automatic main audit never opens labels.

## Fixed P4a v1 candidate

- control: `long72-prelive-t3-b2-anchor`;
- challenger: `q50-linear-prev-home-spacing-a002`;
- only feature: `previous_home_match_days`;
- `QuantileRegressor(q=.5, alpha=.002)`;
- `RobustScaler`;
- no hyperparameter search.

Validation:

- strict forward-event;
- minimum 5 train events;
- one row per independent event;
- no random snapshot split;
- exact fold manifest SHA.

Uncertainty:

- paired event-block bootstrap;
- 5,000 draws;
- seed 42.

Research advancement requires:

- lower strict-forward MAE;
- >50% event improvement rate;
- >50% forward-fold improvement rate.

No P4a v1 result can activate production directly.

---

# 7. P7 precommit + executor

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

At `N>=9` the first output remains an exact identity freeze before labels/model results.

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

Fixed candidates:

- `anchor-only-t7`;
- `q50-linear-residual-a002`;
- `gbr-l1-depth2-n50-lr003`.

Real P7 fitting requires explicit `workflow_dispatch -> mode=execute` and still starts with the N>=9 freeze gate.

---

# 8. Evidence operations

Operational pipelines are active:

- Long72 forecast-before-label workflow hourly;
- outcome-history sync hourly;
- completed-event Long72 scoring inside prospective cycle;
- schedule-as-known capture every 6h;
- fixture-context sidecar every 15m;
- next-opponent sidecar every 15m.

Recent cron checks for outcome sync and both P4 sidecars succeeded.

---

# 9. Immediate operating mode

## While P7 remains 8/9 and P4a remains below 9 labels

1. continue Long72/final24 prospective evidence;
2. continue schedule/context/opponent sidecars;
3. continue Long168 raw evidence accumulation;
4. preserve frozen P4a and P7 contracts;
5. do not execute either learned experiment early;
6. do not reopen closed tuning loops.

## If P7 reaches 9/9 first

`readiness -> explicit P7 execute -> freeze -> verified T7 replay -> labels -> forward folds -> fixed tournament -> uncertainty -> research decision`

## If P4a reaches 9 labeled + 3 distinct values first

`explicit P4a execute -> target-free freeze -> labels -> gate verification -> strict forward spacing ablation -> uncertainty -> research decision`

## If P4a shows real incremental signal

Proceed to:

`P5 pre-live/structural + Context + Live`

with fold-local combination weights only.

---

## One-line handoff

> **P4a and P7 are both fully precommitted before their evidence gates open. P4a is at 5 READY / 0 labeled with real spacing variance; P7 is at 8/9 with a validated 8/8 historical T-7 replay path. The next model run must be triggered by data, not by more tuning. Production remains off.**
