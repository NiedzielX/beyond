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
| P4a — schedule/fixture context | 🟡 DATA ACCUMULATING | PIT sidecar operational |
| P4b — next-home opponent attractiveness | 🟡 DATA ACCUMULATING | fail-closed sidecar operational, still 0 READY |
| P5a — structural/live shrinkage | ✅ DONE | retain full frozen P2 |
| P5 — structural + context + live | ⏸ DATA-BOUND | requires genuine labeled P4 component |
| P6 — live incremental value | ✅ DONE HISTORICALLY | positive point signal, uncertainty/bias prevent promotion |
| **P7 — 72–168h** | 🟡 **HARNESS + EXECUTOR READY / DATA GATE 8/9** | no real tournament before freeze at N>=9 |
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

Checkpoint read on 2026-10-23:

## Long72

- reproducible forecasts: `58`;
- genuine scored events: `0`.

## P4a fixture context

- sidecar rows: `58`;
- READY: `56`;
- two earliest rows remain permanently unavailable because no schedule state existed yet.

## P4b next-opponent attractiveness

- sidecar rows: `58`;
- READY: `0`.

Do not substitute later schedule knowledge or hand-authored opponent scores.

## P7 Long168

- independent events with valid rows >72h: `8/9`;
- rows >72h: `110`;
- research-start trigger: **false**.

Do not lower the threshold.

---

# 6. P7 precommit harness

Canonical:

- `ml/p7_long168_harness_v1.py`;
- `ml/test_p7_long168_harness_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`.

At `N<9`:

`P7_NOT_READY`

At `N>=9` the first required output is still an exact identity freeze:

- event;
- as-of;
- snapshot;
- 6h bucket;
- deterministic manifest SHA256.

Attendance labels and model results may only be opened after freeze validation.

---

# 7. P7 execution pipeline

Canonical:

- `ml/p7_long168_anchor_replay_v1.py`;
- `ml/p7_long168_tournament_v1.py`;
- `ml/test_p7_long168_executor_v1.py`;
- `.github/workflows/p7-long168-executor-v1.yml`;
- `ml/results/P7_LONG168_EXECUTOR_V1_2026-10-23.md`.

## Historical T-7 anchor issue resolved explicitly

The current historical Long168 events have no persisted T-7 rows in `private.structural_prior_forecasts_v1`.

P7 therefore does **not** pretend such forecasts were persisted.

Instead it uses the existing frozen Structural Prior Runtime v1 replay path and labels the result:

`historical_pit_replay`

with:

`persisted_forecast = false`

The replay is built at exactly `kickoff - 7 days` using chronologically prior attendance/sporting facts.

### Frozen lineage

T-7 artifact SHA256:

`97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`

Historical runtime SHA256:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

The executor workflow checks the actual file bytes before replay.

### Target invariance

The anchor audit mutates each target event's exact-kickoff attendance to a sentinel value and requires the replayed T-7 P50 to remain unchanged.

No target event may be skipped from this check.

## Fixed candidate family

- `anchor-only-t7`;
- `q50-linear-residual-a002`;
- `gbr-l1-depth2-n50-lr003`.

No broad hyperparameter search.

## Validation / scoring

- strict forward-event folds;
- minimum 5 training events;
- equal total training weight per event;
- primary = event-balanced MAE;
- majority-event and majority-fold improvement required for research advancement;
- paired event-block bootstrap, 5,000 draws, seed 42.

---

# 8. P7 workflow behavior

Automatic push to `main`:

- code/test validation;
- actual frozen artifact SHA validation;
- live Long168/support export fetch;
- **T-7 anchor audit only**;
- zero real challenger fitting.

Real P7 tournament:

`workflow_dispatch -> mode=execute`

The execute path starts with `freeze`, so it still fails closed at 8/9.

When valid, it emits:

- freeze manifest;
- anchor package;
- fold manifest;
- predictions CSV;
- scorecard JSON.

No P7 v1 output may directly activate production.

---

# 9. Immediate operating mode

## While P7 remains 8/9

1. continue Long72/final24 prospective evidence;
2. continue P4 sidecars;
3. continue Long168 raw evidence accumulation;
4. allow P7 anchor audit only;
5. do not execute the real P7 tournament;
6. do not reopen closed tuning loops.

## If P7 reaches 9/9 first

Priority:

`readiness -> explicit execute dispatch -> freeze identities + SHA -> verified historical T7 replay -> labels -> forward folds -> fixed tournament -> event-block uncertainty -> research decision`

## If genuine P4 labels/READY context become available first

Priority:

`availability/variance audit -> predeclare independent-event floor -> freeze ablation protocol -> controlled context ablation -> uncertainty`

If P4 produces incremental signal, proceed to P5 structural + context + live combination research.

---

## One-line handoff

> **P7 is now fully executable but still scientifically blocked at 8/9. Historical T-7 anchors are explicit PIT replays, never claimed as persisted forecasts. At 9/9 use the manual execute path, which freezes identities before labels/results. Production remains off.**
