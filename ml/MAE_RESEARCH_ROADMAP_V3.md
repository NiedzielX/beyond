# Beyond Ticketing — MAE Research Roadmap v3

Last updated: **2026-10-23**

Status: **CANONICAL MAE-FIRST RESEARCH PLAN**

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at every decision-relevant horizon, while keeping every comparison point-in-time safe, reproducible and honest about evidence class.**

The goal is not model complexity. The goal is lower future MAE early enough for a club to act.

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

Guardrails may block an unsafe challenger but do not replace MAE as the north star.

---

## 2. Scientific operating principles

1. **Development and final evidence are separate.** Frozen packages remain immutable while new challenger versions are developed.
2. **Time order is mandatory.** Random row/snapshot splits are not headline evidence.
3. **Training objective should match MAE.** Median / quantile-0.5 and absolute-error candidates are first-class.
4. **Combine only genuinely different information.** Structural, context and live components may be combined only with fold-local weights.
5. **Prefer new predictive information over decorative complexity.** New features must earn inclusion through incremental OOS MAE.
6. **Pool across clubs but test stability.** A gain concentrated in one club/event/fold is not a robust global improvement.
7. **Evidence class is part of the result.** A historical PIT replay is useful research evidence but is not a forecast that was genuinely persisted before the match.

Literature anchors remain:

- Cawley & Talbot (2010) — model-selection overfitting;
- Bergmeir, Hyndman & Koo (2018) — time-aware validation;
- Koenker & Hallock (2001) — quantile regression;
- Bates & Granger (1969), Makridakis et al. (2020) — forecast combination;
- Montero-Manso & Hyndman (2021) — global vs local forecasting.

---

## 3. Baselines and evidence classes

### Structural incumbent

Structural Prior / Global Model family:

- 1,530 Ekstraklasa matches;
- five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- historical runtime SHA `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Previously inspected historical seasons remain exposed historical research evidence.

### Frozen final24 package

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Immutable, prospective evidence only.

### Frozen Long72 package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical exposed comparison:

- anchor MAE `3707.14`;
- P2 MAE `3012.63`;
- `ΔMAE=-694.51` / `18.73%`;
- 95% event-block interval `[-1549.89,+148.05]`;
- P2 bias `+917.05`.

Immutable; genuine forward evidence continues.

### Evidence labels

Use only explicit evidence classes:

- `historical_exposed_research`;
- `historical_forward_fold`;
- `historical_pit_replay`;
- `delayed_label_precommitted`;
- `true_post_freeze_prospective`.

Never call an inspected historical holdout unseen again. Never call a replayed historical anchor a genuinely persisted forecast.

---

## 4. Two-lane operating model

### Lane A — evidence

Continue without retuning:

- final24 prospective scoring;
- Long72 forecast-before-label materialization;
- immutable prediction persistence;
- append-only outcome scoring;
- schedule-as-known capture;
- fixture-context sidecar;
- next-opponent-attractiveness sidecar.

### Lane B — MAE R&D

Every material feature/model/weight/target change receives a new challenger/version ID.

Frozen packages are never mutated.

---

## 5. Roadmap status

Latest checkpoint should always be refreshed from `public.ml_research_readiness_v1()` before acting.

Checkpoint read on 2026-10-23:

- Long72 reproducible forecasts: `58`;
- Long72 genuine scored events: `0`;
- P4 fixture-context sidecar: `58 / 56 READY`;
- P4 next-opponent sidecar: `58 / 0 READY`;
- P7 Long168: `8/9` independent events >72h, `110` rows >72h.

| Item | Status | Current decision |
|---|---|---|
| P1 canonical temporal validation | ✅ DONE | strict forward-event + expanding-season utilities canonical |
| P2 MAE-native estimator tournament | ✅ DONE | no robust structural runtime replacement |
| P3 `ΔMAE` uncertainty | ✅ DONE | small estimator signals insufficient |
| P4a schedule/fixture context | 🟡 INFRA DONE / DATA ACCUMULATING | fail-closed PIT sidecar operational |
| P4b next-home opponent attractiveness | 🟡 INFRA DONE / DATA ACCUMULATING | 0 READY at latest checkpoint |
| P5a structural/live shrinkage | ✅ DONE | retain full frozen P2 |
| P5 structural + context + live | ⏸ DATA-BOUND | wait for genuine labeled P4 context component |
| P6 live incremental value | ✅ DONE HISTORICALLY | positive point signal, uncertainty/bias prevent promotion |
| **P7 72–168h** | 🟡 **HARNESS + EXECUTOR READY / 8 OF 9** | real tournament blocked until freeze at N>=9 |
| P8 club calibration / shrinkage | ✅ DONE | no robust gain; retain incumbent |
| Production | ⛔ NOT READY | `live_adjustment = 0` |

---

## 6. Closed loops

Do not reopen without materially new evidence or mechanism.

### Estimator-only tuning

P2/P3 showed no robust structural replacement. More blind hyperparameter search is not a priority.

### Structural/live convex shrinkage

Strict forward-event MAE:

- anchor `3180.22`;
- w=.25 `2974.89`;
- w=.50 `2776.51`;
- w=.75 `2614.46`;
- frozen P2 `2472.30`;
- train-selected shrinkage `2564.22`.

Decision: retain full P2.

### Club calibration

Conservative home-club residual shrinkage improved point MAE only ~0.15–0.38%; every 95% interval crossed zero and stability was weak.

Decision: no post-hoc club calibration layer.

---

## 7. P4 — new PIT-safe context

Current priority context family is fixture substitution/cannibalization:

- previous-home spacing;
- next-home spacing;
- team/home fixture density 7/14/30d;
- next-home opponent identity/attractiveness.

Schedule states are captured append-only. Historical schedule backfill from today's/final schedule is forbidden.

Next-opponent attractiveness is READY only when both schedule knowledge and historical outcome knowledge existed by forecast `as_of_at`.

### P4 ablation rule

Do not declare an arbitrary independent-event sample floor after seeing model performance.

When genuine labeled/READY context evidence exists:

1. inspect **availability and variance only**;
2. declare the independent-event floor before model fitting/comparison;
3. freeze that gate;
4. run controlled ablations with canonical temporal folds;
5. report incremental MAE and uncertainty.

---

## 8. P5 — structural + context + live

Start only after P4 produces a genuine context component.

Component candidates:

- Structural Prior;
- P4 context challenger;
- Long72 live/P2 where within contract;
- final24 live signal where within contract.

Test in order:

1. simple mean;
2. median;
3. fixed convex combination;
4. MAE-optimized convex weights learned inside training folds only;
5. regularized stacker only if simpler combinations fail.

Always compare with the best single component. Never learn weights on the evaluation fold.

---

## 9. P7 — 72–168h expansion

### Current state

- independent events with valid rows >72h: **8/9**;
- rows >72h: **110**;
- real model training remains prohibited.

### Canonical implementation

P7 is fully precommitted **and executable** before the ninth event.

Read:

- `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md`;
- `ml/p7_long168_harness_v1.py`;
- `ml/p7_long168_anchor_replay_v1.py`;
- `ml/p7_long168_tournament_v1.py`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`;
- `ml/results/P7_LONG168_EXECUTOR_V1_2026-10-23.md`.

The harness must fail closed below nine independent events.

### P7 v1 research question

> Does PIT live ticket trajectory in `72 < h <= 168` reduce event-balanced MAE beyond the Structural Prior T-7 anchor?

### Historical T-7 anchor problem and evidence boundary

The current historical Long168 events have no persisted T-7 rows in `private.structural_prior_forecasts_v1`.

Therefore P7 must **not** pretend those forecasts were persisted.

The canonical executor uses the frozen Structural Prior Runtime v1 historical replay path at exactly `kickoff - 7 days`.

Replay rules:

- use only attendance with kickoff strictly before the T-7 cutoff;
- use sporting facts strictly before the cutoff;
- strip target-event `actual_attendance` from event metadata before replay;
- require T-7 cutoff to be no later than every eligible Long168 observation;
- use the frozen T-7 artifact and frozen historical runtime;
- classify output as `historical_pit_replay`;
- set `persisted_forecast = false`.

Frozen lineage:

- T-7 model artifact SHA256 `97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`;
- historical runtime SHA256 `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

The main-branch executor workflow verifies the actual bytes, not only manifest declarations.

### Target-attendance invariance

Before an anchor package may be used, every eligible P7 target event must pass an explicit mutation test:

1. find its exact-kickoff attendance row;
2. mutate attendance to an impossible sentinel;
3. replay T-7;
4. require the T-7 P50 to remain unchanged within `1e-9`.

No eligible event may be silently skipped.

### P7 anchor

Use Structural Prior **T-7** throughout 72–168h.

Forbidden:

- future T-3/T-1 predictions;
- interpolation from future checkpoints;
- extrapolating frozen Long72 P2 backward beyond 72h.

### Fixed candidate family

- `anchor-only-t7`;
- `q50-linear-residual-a002`;
- `gbr-l1-depth2-n50-lr003`.

No broad tuning in P7 v1.

### P7 validation

Canonical strict forward-event validation:

- independent unit: event;
- minimum train events: 5;
- `train_end < test_start`;
- tied kickoffs cannot train each other;
- each training event contributes equal total weight;
- no random snapshot split.

Primary metric:

- strict-forward event-balanced MAE.

Required secondary metrics:

- median AE;
- signed bias;
- P90 AE;
- worst-event degradation;
- event-improvement rate;
- forward-fold improvement rate;
- MAE by 72–96 / 96–120 / 120–144 / 144–168h band.

Uncertainty:

- paired event-block percentile bootstrap;
- 5,000 draws;
- seed 42.

Interpretation:

- `ΔMAE >=0` → no MAE gain;
- negative point delta with CI crossing zero → uncertainty-limited point gain;
- CI upper bound below zero → supported historical-forward gain.

### Research advancement rule

A learned candidate may advance only when all lineage/PIT gates pass and:

1. strict-forward event-balanced MAE beats T-7 anchor;
2. more than 50% of independently held-out events improve;
3. more than 50% of usable forward folds improve.

Otherwise retain the anchor.

`N=9` is permission to start research only. Production promotion is impossible from P7 v1 alone.

### Mandatory execution order at 9/9

1. re-read `public.ml_research_readiness_v1()`;
2. explicitly dispatch `.github/workflows/p7-long168-executor-v1.yml` with `mode=execute`;
3. export current Long168 payload;
4. freeze exact eligible event/as-of/snapshot/bucket identities;
5. persist deterministic freeze manifest SHA256;
6. reject any target/outcome field in the freeze payload;
7. verify historical T-7 replay package and exact event-set identity;
8. only after freeze + anchor verification, read/join attendance labels;
9. build strict forward-event fold manifest;
10. run fixed candidate tournament;
11. run paired event-block uncertainty;
12. persist artifacts/hashes/result doc;
13. decide research advancement only;
14. keep production unchanged.

### Automatic workflow boundary

Automatic pushes to `main` may run:

- code/contract validation;
- frozen artifact byte checks;
- live support-export fetch;
- historical T-7 anchor audit.

They must **not** fit the real P7 challengers automatically.

Real fitting requires explicit `workflow_dispatch -> mode=execute`, and that path itself begins with the N>=9 freeze gate.

---

## 10. Evaluation contract for every serious challenger

Primary:

- event/fixture-balanced MAE by decision horizon/window.

Required secondary evidence:

- median AE;
- P90 AE;
- signed bias;
- worst-event degradation;
- event-improvement rate;
- club/fold/horizon stability;
- correction magnitude where applicable;
- paired uncertainty for `ΔMAE`.

A research challenger advances only when:

1. protocol was declared before the final comparison;
2. PIT safety passes;
3. primary time-respecting MAE improves;
4. gain is not explained by one event/club/fold;
5. bias/tail behavior does not invalidate the gain;
6. artifacts and hashes are reproducible.

Production promotion is a separate reviewed decision requiring genuine future evidence.

---

## 11. Canonical readiness gates

Use:

`public.ml_research_readiness_v1()`

Current objective triggers:

1. `P7_LONG168_START` — independent events >72h reaches 9;
2. `LONG72_FIRST_GENUINE_SCORE` — first genuine prospective Long72 score exists;
3. `P4_NEXT_OPPONENT_FIRST_READY` — first READY next-opponent row exists.

An hourly condition watch monitors these triggers.

---

## 12. Immediate execution sequence

### Continue automatically

- final24/Long72 prospective evidence;
- Long72 forecast-before-label persistence;
- schedule-as-known capture;
- fixture-context sidecar;
- next-opponent sidecar;
- Long168 raw evidence accumulation;
- P7 historical T-7 **anchor audit only**.

### If P7 reaches 9/9 first

Priority becomes:

`readiness -> explicit execute dispatch -> identity freeze + SHA -> verified historical T7 replay -> labels -> forward-fold manifest -> fixed P7 tournament -> uncertainty -> decision`.

### If genuine P4 labels arrive first

Priority becomes:

`availability/variance inspection -> predeclared sample floor -> controlled ablation -> uncertainty`.

If P4 produces signal, proceed to P5 combinations.

### Do not spend cycles on

- retuning frozen final24/Long72 packages;
- rebuilding canonical historical data;
- blind hyperparameter sweeps;
- post-hoc club calibration repeats;
- random snapshot validation;
- model complexity without new predictive information;
- claiming replayed anchors were genuinely persisted forecasts.

---

## 13. Implementation / CI rule

Every material experiment follows:

`hypothesis -> PIT contract -> precommit -> code -> tests -> freeze identities -> temporal evaluation -> uncertainty -> artifacts/hashes -> result doc -> decision -> canonical docs`

CI must enforce where applicable:

- deterministic seeds;
- pinned dependencies;
- input/data hashes;
- actual frozen artifact byte hashes where artifacts are reused;
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

> **P1/P2/P3/P5a/P6/P8 are closed. P4 is collecting genuine context evidence. P7 is fully precommitted and executable but must fail closed at 8/9; historical T-7 anchors are explicit PIT replays, not persisted forecasts. At 9/9 use the manual executor: freeze first, labels/models second. Production remains unchanged.**
