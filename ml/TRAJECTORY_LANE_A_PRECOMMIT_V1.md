# Beyond Ticketing — Trajectory Lane A Precommit v1

Precommit date: **2026-10-28**

Status: **PRECOMMITTED DEVELOPMENT PROTOCOL / RESEARCH-ONLY**

Precommit ID:

`trajectory-lane-a-ridge-residual-v1`

Production impact: **none**

`live_adjustment = 0`

References:

- `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`;
- `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`;
- `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`.

---

# 1. Question

> **Do explicit PIT-safe trajectory summaries improve final-attendance MAE beyond the structural incumbent?**

Lane A is deliberately simple. It is the benchmark that Lane B must beat before sequence-model complexity is justified.

---

# 2. Target

For every eligible labeled event/cutoff:

`residual = actual_attendance - structural_incumbent_p50`

Prediction:

`challenger_p50 = structural_incumbent_p50 + predicted_residual`

Final P50 is clipped only to the physically valid interval:

`[0, verified_stadium_capacity]`

when verified capacity exists; otherwise only lower-bound at zero.

No target attendance is available to the feature builder or inference path.

---

# 3. Dataset eligibility

Use exactly `trajectory-feature-contract-v1` primary eligibility:

- P-60...P-1;
- PIT-valid structural incumbent;
- >=4 clean genuine snapshots;
- >=24h genuine observation window;
- canonical `signal_readiness=ready`;
- no future target trajectory;
- no target outcome during representation building.

Training/scoring rows additionally require a genuine confirmed `actual_attendance` after the prediction/cutoff chronology.

No relaxed support cohort is allowed in v1.

---

# 4. Input features

Use the frozen Lane A fields from `trajectory_feature_contract_v1.py`.

Numeric:

- days_to_event;
- available_index;
- available_share_of_capacity;
- velocity_6h_pct_of_first_per_hour;
- velocity_24h_pct_of_first_per_hour;
- velocity_72h_pct_of_first_per_hour;
- velocity_7d_pct_of_first_per_hour;
- acceleration_6h_vs_24h;
- acceleration_24h_vs_72h;
- acceleration_72h_vs_7d;
- snapshot_age_minutes;
- clean_snapshot_count;
- observation_window_hours;
- max_visible_gap_hours;
- structural_incumbent_p50;
- structural_incumbent_p50_share_of_capacity.

Quality/boolean:

- feature_quality;
- data_gap_detected;
- release_activity_flag;
- sector_coverage_change_flag;
- unexplained_inventory_increase_flag.

`signal_readiness` is persisted for audit but excluded from the fitted design matrix because it is constant (`ready`) in the primary cohort.

No club ID/name, event ID, provider ID, odds, weather, hype, match-stakes, Form5 or P4 context enters v1.

---

# 5. Fixed preprocessing

All preprocessing is fitted inside each outer training fold only.

Numeric:

1. add explicit missing indicator for every nullable numeric feature;
2. median imputation from outer-train rows only;
3. standardization using outer-train mean/std only.

Boolean:

- map false/true to 0/1;
- missing stays a separate missing-indicator signal.

Categorical `feature_quality`:

- one-hot encode categories observed in training;
- unseen test category maps to all-zero category indicators;
- no full-dataset category discovery.

No target-derived preprocessing.

---

# 6. Fixed learner

Model:

`sklearn.linear_model.Ridge`

Frozen parameters:

- `alpha = 10.0`;
- `fit_intercept = true`;
- default exact numerical solver selected by scikit-learn `auto`;
- no alpha sweep;
- no feature-selection sweep;
- no post-result coefficient pruning.

Why Ridge:

- tiny independent-event sample;
- correlated trajectory features;
- low variance / strong regularization;
- auditable benchmark;
- no need for a model tournament before testing whether trajectory signal exists at all.

Any alternate alpha or learner requires a new version/precommit.

---

# 7. Event-balanced training weights

Daily prefixes from one event are correlated.

For an outer training fold, if event `e` contributes `n_e` eligible rows, every row from that event receives:

`sample_weight = 1 / n_e`

Therefore each independent event contributes total training weight `1`, regardless of how many eligible P-N rows it has.

Do not let longer observed trajectories dominate solely because they contain more rows.

---

# 8. Validation

Primary validation is exactly `trajectory-validation-fold-contract-v1`:

- strict expanding temporal event folds;
- only earlier-kickoff events may train a later target;
- same-kickoff events are held out together;
- minimum 5 prior train events;
- minimum 4 prior train clubs;
- all prefixes from an event stay in one fold.

No random CV.

LOEO/LOCO may be reported as secondary diagnostics only and may not override the strict-forward result.

---

# 9. Scoring

Primary model-development comparison:

- incumbent event-balanced MAE;
- Lane A event-balanced MAE;
- `Delta MAE = Lane A MAE - incumbent MAE`.

Required diagnostics:

- independent test events;
- clubs;
- row/prefix count as non-independent support only;
- MAE by available horizon;
- signed bias;
- median AE;
- P90 AE;
- event improvement rate;
- worst event degradation.

## Event-balanced aggregation

Within each independent test event:

1. calculate absolute error for each eligible tested cutoff;
2. average those cutoff errors to one event-level error;
3. average event-level errors across independent events.

This prevents events with more eligible horizons from dominating the headline MAE.

Horizon-specific MAE remains separately reported.

---

# 10. Advance rule

Lane A may advance to candidate-freeze consideration only if:

1. strict-forward `Delta MAE < 0`;
2. result is not driven by one event only;
3. worst-event degradation is reviewed and not clearly unacceptable;
4. support counts are shown explicitly;
5. no PIT/leakage assertion fails.

Because the independent-event sample is small, a positive development result is **research evidence**, not production proof.

No production activation follows automatically.

---

# 11. Non-negotiable guards

- no future target snapshot;
- no target outcome in features/inference;
- no random row CV;
- no event-prefix crossing folds;
- no feature-family expansion after seeing outer test results;
- no alpha tuning against outer test events;
- no backfilled fake daily history;
- `production_change=false`;
- `live_adjustment=0`.
