# Beyond Ticketing — Current Model & Product State

Last updated: **2026-10-30**

Status: **STRUCTURAL INCUMBENT + FROZEN PROSPECTIVE LANES + FROZEN-ENCODER ATTENDANCE SHADOW**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE with PIT-safe, reproducible evidence.**

`Delta MAE = challenger MAE - incumbent MAE`

Desired: `Delta MAE < 0`.

---

# 2. Structural incumbent

Current structural research champion family remains **Global Model v2.1**.

Foundation:

- 1,530 Ekstraklasa matches;
- complete 2021/22–2025/26 seasons;
- 7,650 historical PIT rows;
- structural horizons T-30d / T-14d / T-7d / T-3d / T-1d.

Architecture:

`PIT historical state -> club-history baseline -> global residual model -> structural P50`

This remains the attendance anchor that any trajectory challenger must beat prospectively.

---

# 3. Supervised trajectory research — closed

Frozen development cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled independent events;
- 19 eligible checkpoint rows;
- 5 strict-forward outer test events;
- fold registry SHA256:
  `fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`.

Results:

| Model | Event-balanced MAE | Delta vs structural | Decision |
|---|---:|---:|---|
| Structural | **2594.54** | — | incumbent |
| Lane A v1 | 4153.34 | +1558.80 | rejected |
| Lane B v1 | 2595.40 | +0.87 | do not advance |
| Lane B v2 | 4792.42 | +2197.88 | mechanism not supported |

The cohort is exposed. Do not reuse it as unseen confirmation or tune new correction mechanics against the same outer events.

---

# 4. Target-free SSP trajectory representation — supported

Precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Result:

`ml/results/trajectory_self_supervised_24h_delta_v1_result.json`

Task:

`genuine trajectory prefix -> normalized inventory movement ~24h later`

No attendance labels. No structural P50.

Frozen result:

- train: 21 events / 3397 usable pairs;
- validation: 5 later events / 168 usable pairs;
- zero-change event-balanced MAE: **0.0917223592**;
- GRU event-balanced MAE: **0.0628961688**;
- Delta: **-0.0288261905**;
- improved validation events: **5/5**.

Decision:

`REPRESENTATION_SUPPORTED`

Frozen encoder:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Interpretation:

> **Inventory trajectory dynamics are learnable under this frozen target-free task. This does not establish attendance-forecast improvement.**

---

# 5. Current trajectory attendance candidate

Candidate:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Components:

1. frozen SSP v1 GRU encoder;
2. 8-dimensional trajectory embedding;
3. one fixed Ridge residual-ratio head;
4. Ridge alpha 10;
5. correction ratio cap +/-10%;
6. exact exposed 10-event / 19-row historical fit cohort;
7. no historical candidate selection;
8. prospective horizons P-7 / P-3 / P-1.

Frozen head:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

The head was fitted once. Its role is not to claim historical improvement; it is a fixed mapping to be judged on future immutable attendance outcomes.

---

# 6. Active prospective trajectory shadow

Precommit:

`ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`

Prediction:

`structural P50 * (1 + frozen clipped residual ratio)`

with the ratio clipped to `[-0.10,+0.10]`.

Eligibility is fail-closed and PIT-safe. Inputs are reconstructed strictly at exact P-7/P-3/P-1 cutoffs using genuine observations and a structural prior genuinely available by that cutoff.

Persistence:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Workflow:

`.github/workflows/trajectory-frozen-encoder-shadow-v1.yml`

Schedule:

`20 * * * *`

The exact frozen head artifact was persisted to `main` on 2026-10-29 and the workflow passed end-to-end afterwards.

First genuine prospective attendance evidence was created for **event446 Wisła Płock–Piast Gliwice at P-1** on 2026-10-30:

- target cutoff `11:15 UTC`;
- immutable attempt at `11:21:26 UTC`;
- PIT source snapshot `11:05:02 UTC`;
- status `PREDICTION_READY`;
- incumbent structural P50 `6084.5618737955`;
- challenger P50 `6693.01806117505`;
- trajectory residual `+608.45618737955`;
- frozen correction equals the +10% cap;
- target values used false;
- production change false;
- score pending genuine confirmed attendance.

Current shadow state:

- attempts: 1;
- predictions: 1;
- scores: 0.

The protected run completed successfully with `due_target_count=1`, `attempt_count=1`, `prediction_count=1`, `inserted_scores=0`.

---

# 7. Trajectory data reality

Current genuine pre-kickoff history:

- 32 events / 14 clubs with any observation;
- median first observation ~P-9.3;
- earliest ~P-30.3;
- P-31...P-60 historical coverage currently zero.

Therefore:

- P-60 is a collection horizon;
- models use genuine variable-length prefixes;
- no fabricated complete 60-day vector;
- no forward-fill/interpolation merely for model convenience;
- hidden/unknown inventory is never zero.

Public inventory is a demand/inventory proxy, not confirmed sales or attendance.

---

# 8. Existing prospective lanes

## P7

- historical point gain 14.44%, uncertainty limited;
- latest canonical prospective state: 53 immutable rows / 6 events / 0 scored;
- no retuning.

## P9 v1

Fresh state on 2026-10-30:

- 3 attempts / 0 predictions / 0 scored;
- all support-insufficient;
- correct fail-closed.

## P9 Family Fallback v2

- 2 attempts / 1 immutable prediction / 0 scored;
- event446 prediction exists;
- event444 fallback support insufficient;
- separate evidence only;
- never pool with v1.

## Form5

- prospective collecting;
- 0/8 completed eligible events;
- frozen alpha 30 / cap +/-25%;
- completed-event rows remain zero until genuine attendance outcomes are available.

## Long72

- 5 scored events;
- 6082.40 -> 6039.39 MAE;
- 0.71% point gain;
- frozen / low priority.

## P11 / P4a

Continue genuine collection. Do not force model fit below frozen gates.

---

# 9. Product interpretation

Intended future product view remains:

`observed trajectory | today | predicted remaining trajectory -> final attendance P10/P50/P90`

But the trajectory representation is not promoted because it looked good on a target-free task.

It must now prove attendance value through genuinely future predictions created before outcomes.

The first such frozen-encoder attendance prediction now exists, but one event is evidence collection, not a model decision.

---

# 10. Immediate model decision

> **Keep the structural model as incumbent. Freeze the supported SSP encoder and its single Ridge attendance head. Collect P-7/P-3/P-1 immutable prospective shadow evidence without retuning. Score event446 only after genuine attendance confirmation, then accumulate a cohort before interpreting Delta MAE. The next meaningful decision is future attendance Delta MAE, not another historical model search.**
