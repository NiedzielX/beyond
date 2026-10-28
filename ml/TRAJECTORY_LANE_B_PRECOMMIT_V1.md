# Beyond Ticketing — Trajectory Lane B Precommit v1

Precommit date: **2026-10-28**

Status: **PRECOMMITTED DEVELOPMENT PROTOCOL / HIGH-RISK RESEARCH-ONLY**

Precommit ID:

`trajectory-lane-b-small-gru-residual-v1`

Production impact: **none**

`live_adjustment = 0`

References:

- `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`;
- `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`;
- `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`.

---

# 1. Question

> **Does reading the ordered genuine trajectory reduce attendance MAE beyond Lane A's engineered trajectory summaries?**

This is intentionally a small first sequence model. The purpose is to test whether sequence representation itself adds signal, not to search neural architectures.

---

# 2. Target

Same target as Lane A:

`residual = actual_attendance - structural_incumbent_p50`

Prediction:

`challenger_p50 = structural_incumbent_p50 + predicted_residual`

Physical clipping:

- lower bound 0;
- upper bound verified stadium capacity only when genuinely available.

No target attendance is visible during representation construction or inference.

---

# 3. Dataset eligibility

Use exactly the same primary cohort as Lane A under `trajectory-feature-contract-v1`:

- P-60...P-1;
- PIT-valid structural incumbent;
- >=4 clean genuine snapshots;
- >=24h genuine observation window;
- canonical `signal_readiness=ready`;
- no future target trajectory;
- no target outcome during representation building.

Training/scoring rows additionally require genuine confirmed attendance after the target cutoff chronology.

Lane B is not allowed to expand eligibility relative to Lane A in v1.

---

# 4. Sequence representation

Use the frozen executable representation from:

`ml/demand_engine/trajectory_feature_contract_v1.py`

Per genuine timestep:

1. `hours_to_kickoff`;
2. `available_index`;
3. `available_share_of_capacity` when available;
4. `delta_hours_since_previous`;
5. `delta_available_index`.

Sequence rules:

- genuine observations only;
- only `captured_at <= as_of_at`;
- exact timestamp duplicates keep highest snapshot ID;
- at most one real observation per integer hour-to-kickoff bucket;
- no interpolation;
- no forward-fill;
- chronological order;
- padding requires an explicit mask/length;
- padded zero is never interpreted as a genuine observation.

If the first genuine available total is <=0, the sequence fails closed as `MODEL_INPUT_INSUFFICIENT`.

---

# 5. Global context

Use only the frozen Lane B global context:

- days_to_event;
- snapshot_age_minutes;
- clean_snapshot_count;
- observation_window_hours;
- max_visible_gap_hours;
- structural_incumbent_p50;
- structural_incumbent_p50_share_of_capacity when available;
- verified-capacity-available flag;
- sequence length.

No club/event identity is a learnable input.

No P11 odds, weather, hype, match-stakes, Form5 or P4 context in v1.

---

# 6. Fixed preprocessing

## Sequence channels

Deterministic transforms before fold-local scaling:

- `hours_to_kickoff_scaled = hours_to_kickoff / 1440`;
- `delta_hours_scaled = delta_hours_since_previous / 24`.

For remaining continuous sequence channels:

- missing capacity share gets numeric 0 plus an explicit capacity-available global flag;
- first-step `delta_hours_since_previous` and `delta_available_index` are numeric 0, with sequence position/mask preserving first-step semantics.

No fabricated observation is created by this fill.

Fold-local standardization is allowed only if fit on outer-train sequence values. If used, the exact scaler statistics must be persisted in the run manifest.

## Global context

- median imputation for nullable numeric global fields from outer-train only;
- explicit missing indicators for nullable numeric fields;
- standardization from outer-train only;
- booleans encoded 0/1.

No full-dataset preprocessing fit.

---

# 7. Fixed model architecture

Framework:

`PyTorch`

Sequence encoder:

- one-layer GRU;
- input dimension = 5;
- hidden dimension = 8;
- `batch_first=true`;
- bidirectional = false;
- dropout = 0 inside GRU because one recurrent layer only.

Head:

- concatenate final valid GRU hidden state with processed global-context vector;
- linear layer -> 8 hidden units;
- ReLU;
- dropout 0.20;
- linear -> one scalar residual.

No attention.

No Transformer.

No architecture search in v1.

---

# 8. Fixed optimization

Loss:

`weighted L1 / MAE loss on attendance residual`

Optimizer:

`AdamW`

Frozen parameters:

- learning rate = `0.001`;
- weight decay = `0.01`;
- batch size = all available outer-train rows when <=128, otherwise 128;
- max epochs = 200;
- gradient clipping = 1.0.

Random seeds:

`[17, 29, 41]`

For every outer fold, train exactly three models with the frozen seeds and use the **median residual prediction** across the three seeds.

This stabilizes small-sample neural variance without architecture/hyperparameter selection.

No seed is selected after observing test performance.

---

# 9. Event-balanced training weights

Same principle as Lane A.

If event `e` contributes `n_e` eligible prefix rows in the outer training fold:

`row_weight = 1 / n_e`

Weighted MAE is normalized so each independent event contributes equal total weight.

Longer trajectories must not dominate merely because they generate more P-N rows.

---

# 10. Training protocol

To avoid using the tiny outer-test cohort for early stopping or architecture selection, v1 uses a deterministic fixed-epoch schedule.

For each outer fold and each frozen seed:

1. initialize model from the frozen seed;
2. fit preprocessing on outer-train only;
3. train exactly 200 epochs;
4. never inspect outer-test loss during training;
5. emit predictions once after training completes.

No early stopping in v1.

Any future early-stopping design requires a new version with an explicit inner temporal validation contract.

---

# 11. Validation

Use exactly `trajectory-validation-fold-contract-v1`:

- strict expanding temporal event folds;
- same-kickoff targets held out together;
- minimum 5 prior train events;
- minimum 4 prior train clubs;
- all prefixes from one event stay together;
- identical eligible event/cutoff identities to Lane A.

Random row-level CV is prohibited.

---

# 12. Scoring

Report three comparisons:

1. structural incumbent vs Lane B;
2. structural incumbent vs Lane A;
3. **Lane A vs Lane B** on identical test identities.

Primary Lane B question:

`Delta MAE_B_vs_A = Lane B event-balanced MAE - Lane A event-balanced MAE`

Desired:

`Delta MAE_B_vs_A < 0`

Required diagnostics:

- independent events;
- clubs;
- prefix rows as non-independent support only;
- horizon-wise MAE;
- signed bias;
- median AE;
- P90 AE;
- event improvement rate;
- worst event degradation;
- seed spread diagnostics.

Event-balanced aggregation is identical to Lane A: first average cutoff error within event, then average independent event errors.

---

# 13. Advance rule

Lane B earns further sequence research only if all are true:

1. strict-forward Lane B beats the structural incumbent;
2. strict-forward Lane B beats Lane A on identical event/cutoff identities;
3. the result is not solely one-event driven;
4. seed spread does not indicate clearly unstable predictions;
5. no PIT/leakage assertion fails;
6. downside is reviewed explicitly.

With current small-N evidence, even a win remains research evidence, not production proof.

If Lane A wins, prefer Lane A and do not escalate to Transformer complexity.

---

# 14. Self-supervised work is separate

No self-supervised pretraining enters this first Lane B v1 result.

Self-supervised trajectory representation research may run later under a separate precommit so its contribution can be measured independently.

---

# 15. Non-negotiable guards

- same event/cutoff cohort as Lane A;
- no target future trajectory;
- no target outcome in representation/inference;
- no random row CV;
- no club/event identity as input;
- no architecture/hyperparameter sweep against outer tests;
- no forward-filled fake sequence;
- no post-result seed selection;
- `production_change=false`;
- `live_adjustment=0`.
