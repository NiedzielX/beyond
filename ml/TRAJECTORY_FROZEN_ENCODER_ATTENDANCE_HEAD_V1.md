# Beyond Ticketing — Frozen Encoder Attendance Head v1

Precommit date: **2026-10-28**

Status: **PRECOMMITTED FIT-ONLY HISTORICAL TRAINING / PROSPECTIVE EVALUATION REQUIRED**

Precommit ID:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Production impact: **none**

`live_adjustment = 0`

References:

- `ml/TRAJECTORY_SELF_SUPERVISED_V1_RESULT.md`;
- `ml/artifacts/trajectory_self_supervised_encoder_v1.json`;
- `ml/artifacts/trajectory_development_cohort_v1.json`;
- `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`.

---

# 1. Purpose

The target-free trajectory encoder v1 is supported on temporally later inventory-dynamics validation:

- zero-change event-balanced MAE: 0.09172;
- frozen encoder MAE: 0.06290;
- 31.4% improvement;
- 5/5 validation events improved.

This does **not** prove attendance value.

The next question is:

> **Can the frozen trajectory representation provide a useful, conservative correction over structural attendance P50 on genuinely future events?**

The encoder is now immutable. Only a small downstream attendance head is fitted.

---

# 2. Evidence boundary

The 10-event / 19-row historical attendance cohort is already exposed by Lane A/B v1/v2.

Therefore this head is **not historically selected or validated** on that cohort.

Historical labels are used only to fit one precommitted head.

Do not:

- compare alternative alphas on historical MAE;
- compare raw-seat vs ratio targets after fitting;
- compare alternative feature subsets;
- tune the correction cap against historical errors;
- report exposed historical MAE as validation evidence.

The first meaningful attendance evidence must come from immutable predictions created before genuinely future outcomes.

---

# 3. Frozen encoder

Artifact:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Encoder identity:

- architecture: one-layer GRU;
- input dimension: 4;
- hidden dimension: 8;
- parameter count in original SSP model: 417;
- source PyTorch artifact SHA256:
  `3740ba690f75623b4722d28c4084f6062c36cc8dd22e5020c1a5135d4d6f1e2e`;
- SSP decision: `REPRESENTATION_SUPPORTED`.

Only the GRU hidden representation is used by the attendance head.

All encoder GRU weights remain frozen.

No attendance gradient may update the encoder.

---

# 4. Attendance training cohort

Use exactly the frozen historical attendance identities from:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 independent events;
- 19 persisted checkpoint rows;
- horizons T-7 / T-3 / T-1 where available.

Use all 19 rows for the single head fit.

There is **no outer historical score used to choose or reject this head**.

Row weighting remains event-balanced:

`row_weight = 1 / eligible_row_count_for_event`

Each independent historical event therefore contributes total fit weight 1.

---

# 5. Encoder input at an attendance cutoff

For each historical/prospective cutoff:

- use genuine observations only;
- no future snapshot after cutoff;
- context limited to the final 168h before the cutoff;
- require at least 4 genuine observations;
- require at least 24h observed prefix span;
- exact timestamp dedupe;
- max one real observation per integer hour-to-kickoff bucket;
- no interpolation;
- no forward-fill.

Per timestep channels are exactly the self-supervised v1 channels:

1. `hours_to_kickoff / 1440`;
2. `available_index` relative to the event's first genuine available inventory observation;
3. `delta_hours_since_previous / 24`;
4. `delta_available_index`.

The final valid GRU hidden state is an 8-dimensional fixed representation.

---

# 6. Frozen attendance head

Model:

`Ridge regression`

Inputs:

- 8 frozen encoder hidden dimensions only.

No club/event ID.

No odds/weather/hype/context.

No hand-engineered velocity/acceleration features.

Target:

`attendance_residual_ratio = (actual_attendance - structural_p50) / structural_p50`

Eligibility requires:

`structural_p50 > 0`

Preprocessing:

- standardize each of the 8 encoder dimensions using means/stds fitted on all 19 historical fit rows;
- zero-variance std -> 1.0;
- preprocessing frozen with the head artifact.

Ridge:

- `alpha = 10.0`;
- intercept enabled;
- event-balanced row weights;
- no hyperparameter search.

The alpha is fixed before fitting and intentionally reuses the previously declared Ridge regularization scale rather than being optimized against the exposed attendance outcomes.

---

# 7. Conservative correction boundary

Predicted ratio correction is clipped to:

`[-0.10, +0.10]`

Then:

`challenger_p50 = structural_p50 * (1 + clipped_ratio)`

Physical clipping:

- lower bound 0;
- upper bound verified stadium capacity when available.

The +/-10% boundary is frozen before prospective evaluation. It is a risk-control rule, not a value selected by comparing historical candidate MAEs.

---

# 8. Historical fit artifact

Persist at minimum:

- precommit ID;
- frozen encoder identity/hash;
- exact 10 event IDs / 19 cutoff identities;
- embedding scaler means/stds;
- Ridge coefficients/intercept;
- alpha;
- correction cap;
- event-balanced fit weighting rule;
- code Git SHA;
- fit-manifest SHA256;
- `production_change=false`.

Do not persist a historical promotion decision.

The fitted head is a **prospective candidate**, not a historically validated winner.

---

# 9. Prospective shadow horizons v1

Initial attendance evidence is restricted to the familiar checkpoint horizons:

- P-7;
- P-3;
- P-1.

This avoids claiming daily P-60...P-1 attendance generalization before the head has evidence outside the historical training horizons.

Future versions may expand daily horizons only through a new precommit.

---

# 10. Immutable prospective prediction contract

For every eligible future event/checkpoint:

1. build target input strictly at the checkpoint cutoff;
2. require PIT-valid structural incumbent available by cutoff;
3. require trajectory quality gate;
4. compute frozen encoder embedding;
5. apply frozen scaler/head;
6. apply frozen +/-10% correction cap;
7. persist immutable attempt even if fail-closed;
8. persist prediction before outcome if emitted;
9. `target_values_used=false`;
10. `production_change=false`.

Use the existing daily trajectory evidence backend rather than a parallel ledger.

---

# 11. Prospective scoring

Primary comparator:

`structural incumbent P50`

Primary metric:

`event-balanced Delta MAE`

Also report:

- event count;
- club count;
- horizon-wise MAE;
- signed bias;
- median/P90 AE;
- event improvement rate;
- worst event degradation;
- correction-ratio distribution;
- cap-hit rate.

No retrospective rewriting of predictions after outcomes.

---

# 12. Evidence gate

This head is not promoted from the historical fit.

Prospective evidence accumulates until a separately defined minimum independent-event gate is met. Until that gate is agreed and reached, results remain shadow research.

The business minimum meaningful attendance Delta MAE must still be derived independently.

---

# 13. Non-negotiable guards

- encoder weights fully frozen;
- one Ridge head only;
- alpha 10 fixed;
- target residual ratio fixed;
- +/-10% cap fixed;
- exact historical fit identities fixed;
- no historical head tournament;
- only P-7/P-3/P-1 prospective horizons in v1;
- immutable future predictions before outcomes;
- production remains OFF.
