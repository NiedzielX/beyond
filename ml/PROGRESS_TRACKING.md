# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-23**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V3.md`

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains unchanged:

`live_adjustment = 0`

---

# 2. Current model state

## Structural core

Current incumbent: **Structural Prior Runtime v1 / Global Model family**.

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- canonical history SHA: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Estimator-only MAE challengers and post-hoc club calibration did not justify a runtime replacement.

## Frozen Long72 package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical P6 comparison:

- structural anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- `ΔMAE = -694.51` / `18.73%` improvement;
- 95% event-block interval `[-1549.89,+148.05]`;
- `P(ΔMAE<0)=0.9500`;
- frozen P2 bias `+917.05`.

Status: **FROZEN / GENUINE POST-FREEZE EVIDENCE ACTIVE**.

---

# 3. Roadmap tracking

| Roadmap item | Status | Decision / evidence |
|---|---|---|
| Evidence Lane — Long72 forecast-before-label | ✅ DONE / RUNNING | immutable hourly persistence + outcome-only scoring active |
| P1 — canonical forward/rolling validation | ✅ DONE | strict expanding-season + forward-event folds |
| P2 — MAE-native challenger tournament | ✅ DONE | no robust runtime replacement |
| P3 — `ΔMAE` uncertainty | ✅ DONE | estimator signals did not justify replacement |
| P4a — schedule-as-known / fixture spacing-density | ✅ INFRA DONE / DATA ACCUMULATING | PIT lookup + append-only Long72 sidecar operational |
| P4b — next-home opponent attractiveness | ✅ INFRA DONE / DATA ACCUMULATING | strict schedule + outcome-knowledge gates; append-only sidecar operational |
| P5a — structural ↔ live convex shrinkage | ✅ DONE | full frozen P2 retains lowest strict forward-event MAE |
| P5 — structural + context + live | ⏸ DATA-BOUND | wait for genuine labeled P4 context evidence |
| P6 — live-ticket incremental value | ✅ DONE HISTORICALLY | +18.73% MAE point uplift; CI crosses zero; +917-seat bias guardrail |
| **P7 — 72–168h learned model** | 🟡 **HARNESS READY / DATA GATE 8/9** | experiment contract committed before N=9; model training prohibited until identity freeze |
| P8 — club calibration / shrinkage | ✅ DONE | small 0.15–0.38% point gains; all CIs cross zero; retain incumbent |
| Production activation | ⛔ NOT READY | `live_adjustment = 0` |

---

# 4. Closed R&D loops

Do not repeat without materially new information:

- P2/P3 estimator-only loop — no robust replacement;
- P5a structural/live convex shrinkage — full P2 remains best;
- P6 historical incremental live value — useful point signal, uncertainty-limited;
- P8 simple club/opponent residual calibration — no robust gain.

---

# 5. P4 forward context state

## P4a fixture context

Operational and fail-closed:

- immutable schedule-as-known batches;
- PIT fixture lookup;
- append-only Long72 fixture-context sidecar.

Latest live checkpoint on 2026-10-23:

- reproducible Long72 forecasts: `48`;
- fixture-context sidecar rows: `48`;
- fixture-context READY: `46`;
- the two original pre-schedule forecasts remain permanently unavailable by design.

## P4b next-home opponent attractiveness

Operational PIT-safe sidecar with schedule-state and outcome-knowledge gates.

Latest checkpoint:

- sidecar rows: `48`;
- READY: `0`.

Do not fill missing values from later schedule knowledge or outcomes not system-known at forecast time.

---

# 6. Long72 prospective state

Latest live checkpoint:

- reproducible forecast rows: `48`;
- genuine scored events: `0`;
- latest reproducible as-of observed at checkpoint: `2026-10-23 07:20:02.19+00`.

The first genuine score is an evidence-review trigger only. Do not retune the frozen package from the first result.

---

# 7. P7 Long168 — harness precommitted

Canonical harness:

- `ml/p7_long168_harness_v1.py`;
- `ml/test_p7_long168_harness_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`.

Current data gate:

- independent events with valid rows `>72h`: **8/9**;
- valid rows `>72h`: **110**;
- threshold remains exactly `N>=9`.

### Precommitted sequence at 9/9

1. export the current `d2-long-horizon-168-rows-v1` payload;
2. **before opening Long168 model results**, freeze exact eligible identities in `72 < h <= 168`;
3. persist deterministic manifest SHA256 containing event/as-of/snapshot/bucket identities;
4. reject target/outcome fields in the freeze payload;
5. only after freeze, join attendance labels for evaluation;
6. use Structural Prior **T-7** as the control anchor throughout the 72–168h band;
7. do not extrapolate Long72 P2 backward beyond 72h;
8. run only the fixed P7 v1 challenger family;
9. validate with strict forward-event folds using `ml/temporal_validation_v1.py`;
10. report paired event-block `ΔMAE` uncertainty using `ml/mae_delta_uncertainty_v1.py`.

### Fixed P7 v1 candidate family

- `anchor-only-t7`;
- `q50-linear-residual-a002` — fixed q=.5 quantile linear residual;
- `gbr-l1-depth2-n50-lr003` — small fixed absolute-error booster.

No broad hyperparameter sweep is allowed in P7 v1.

### P7 evaluation

Primary:

- strict-forward **event-balanced MAE**.

Required secondary evidence:

- median AE;
- signed bias;
- P90 AE;
- worst-event degradation;
- event-improvement rate;
- forward-fold consistency;
- MAE by 72–96 / 96–120 / 120–144 / 144–168h;
- paired event-block bootstrap, 5,000 draws, seed 42.

`N=9` means **research may start**. It never means production adequacy.

---

# 8. Canonical readiness gate

Use:

`public.ml_research_readiness_v1()`

Objective triggers:

1. `P7_LONG168_START` — independent events >72h reaches `9`;
2. `LONG72_FIRST_GENUINE_SCORE` — first genuine Long72 event score exists;
3. `P4_NEXT_OPPONENT_FIRST_READY` — first READY next-opponent row exists.

An hourly condition watch is active for these gates.

---

# 9. Immediate operating mode

## Now

1. keep Long72, final24 and P4 evidence collection running;
2. keep P7 harness immutable while Long168 remains `8/9`;
3. do not train or inspect P7 challenger results before the ninth event and identity freeze;
4. do not reopen closed estimator/shrinkage/calibration loops.

## On the next data trigger

### If Long168 becomes 9/9

Priority becomes P7 immediately:

`readiness -> freeze identities + SHA -> attach labels -> strict forward folds -> fixed candidate tournament -> event-block uncertainty -> decision`.

### If genuine labeled P4 evidence becomes available first

Inspect only feature availability/variance, predeclare the independent-event sample floor before model comparison, then run controlled context ablations.

### If P4 produces a genuine incremental signal

Run P5 `structural + context + live` combination research with fold-local combination weights only.

---

## One-line handoff

> **P7 is no longer a design task: the Long168 experiment is fully precommitted and must fail closed at 8/9. The next Long168 action at 9/9 is identity freeze first, model comparison second. P4/P5 remain genuinely label-bound.**
