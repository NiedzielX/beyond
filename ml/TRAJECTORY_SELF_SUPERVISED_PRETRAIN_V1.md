# Beyond Ticketing — Self-Supervised Trajectory Pretraining v1

Precommit date: **2026-10-28**

Status: **PRECOMMITTED TARGET-FREE RESEARCH**

Precommit ID:

`trajectory-self-supervised-24h-delta-v1`

Frozen data cutoff:

`2026-10-28T22:09:43.958409Z`

Production impact: **none**

`live_adjustment = 0`

---

# 1. Why this starts now

The first supervised trajectory experiments are closed:

- Lane A v1 materially worsened MAE;
- Lane B v1 learned almost zero correction;
- Lane B v2 unlocked correction magnitude but materially over-corrected.

The current labeled attendance sample is only 10 events and its 5 strict-forward outer test events are now exposed.

Continuing to tune supervised correction magnitude, caps, loss functions or sequence architectures on those same five events would increasingly optimize against known answers.

However, trajectory data are much richer than attendance labels.

At the frozen data cutoff, the target-free trajectory corpus contains:

- **32** events with genuine pre-kickoff sequences;
- **14** clubs;
- **4869** genuine hourly-bucket observations;
- **4837** generic next-observation pairs;
- **4227** clean ~24h future-observation pairs across **29 events / 12 clubs**.

This makes target-free representation learning the next evidence-safe direction.

---

# 2. Research question

> **Can a small GRU learn reusable trajectory dynamics by predicting the genuine normalized inventory movement approximately 24 hours ahead, without using attendance labels?**

This is not an attendance model.

The purpose is to learn a trajectory encoder before using future attendance outcomes for evaluation.

---

# 3. Frozen event split

The split is chronological by event kickoff and frozen before any self-supervised validation result.

## Training events — 24

`[3, 1, 4, 12, 8, 9, 17, 14, 15, 18, 11, 19, 5, 20, 10, 16, 23, 21, 22, 443, 446, 6, 444, 445]`

Current ~24h pairs: **3940**.

## Validation events — 5

`[447, 449, 450, 451, 452]`

Current ~24h pairs: **287**.

Validation clubs:

- Raków;
- Górnik Zabrze;
- Legia;
- Lech;
- Pogoń Szczecin.

No event may appear in both train and validation.

The frozen cutoff prevents later snapshots from silently changing this v1 result.

---

# 4. Raw sequence semantics

Use only genuine pre-kickoff inventory snapshots that satisfy:

- `captured_at <= frozen_data_cutoff`;
- `captured_at < kickoff_at`;
- `available_total` is non-null and non-negative.

Cleaning follows the trajectory v1 semantics:

1. exact timestamp duplicate -> highest snapshot ID;
2. at most one genuine observation per integer hour-to-kickoff bucket -> latest genuine row in bucket;
3. chronological order;
4. no interpolation;
5. no forward-fill;
6. hidden/unknown inventory never becomes zero.

---

# 5. Fixed 24h target-pair construction

For each source observation, find a later genuine observation from the same event with elapsed time:

`18h <= elapsed <= 30h`

Choose the candidate closest to exactly 24h, then earliest timestamp as deterministic tie-break.

Current frozen pair audit:

- pairs: **4227**;
- median elapsed: **24.00h**;
- P10 elapsed: **23.69h**;
- P90 elapsed: **24.15h**.

This prevents the task from primarily learning scraper cadence.

---

# 6. Input prefix

For each source observation, the encoder sees genuine observations from the same event up to and including the source observation.

Maximum context:

`168 hours before source observation`

Minimum usable prefix:

- at least 4 genuine hourly-bucket observations;
- at least 24h observed prefix span.

Per timestep channels:

1. `hours_to_kickoff / 1440`;
2. `available_index = available_total / first_available_total_in_event_sequence`;
3. `delta_hours_since_previous / 24`;
4. `delta_available_index`.

No structural P50.

No attendance.

No club ID.

No event ID as model input.

No odds/weather/context.

---

# 7. Target

Target is the future normalized inventory movement:

`delta_available_index_24h = future_available_index - source_available_index`

This is entirely target-free with respect to final attendance.

Zero-change baseline:

`predicted_delta_available_index_24h = 0`

The model must beat this baseline on frozen validation events to demonstrate useful trajectory-dynamics learning.

---

# 8. Event-balanced pair weighting

Events have very different numbers of trajectory observations.

If event `e` contributes `n_e` training pairs:

`pair_weight = 1 / n_e`

Therefore every independent event contributes total training weight 1.

The self-supervised headline validation metric is also event-balanced:

1. calculate pair MAE within each validation event;
2. average to one event-level MAE;
3. average event-level MAEs across the five validation events.

Pair count is training support, not independent-event evidence.

---

# 9. Frozen model

Framework:

`PyTorch`

Encoder:

- one-layer GRU;
- input dimension 4;
- hidden dimension 8;
- `batch_first=true`;
- unidirectional.

Prediction head:

- final valid GRU hidden state;
- linear 8 -> 8;
- ReLU;
- dropout 0.20;
- linear 8 -> 1 predicted 24h delta index.

No attention.

No Transformer.

No architecture search.

---

# 10. Frozen optimization

- loss: event-balanced weighted L1/MAE on `delta_available_index_24h`;
- optimizer: AdamW;
- learning rate: `0.001`;
- weight decay: `0.01`;
- batch size: 128;
- epochs: 100;
- gradient clipping: 1.0;
- random seed: **17**;
- no early stopping;
- no hyperparameter selection using validation results.

The single seed avoids choosing a favorable representation after validation.

---

# 11. Validation reporting

Report:

- train events / clubs / pairs;
- validation events / clubs / pairs;
- zero-change event-balanced MAE;
- model event-balanced MAE;
- Delta MAE vs zero-change;
- pair-weighted diagnostic MAE;
- per-validation-event MAE;
- target distribution;
- prediction distribution;
- signed bias.

Evidence label:

`target_free_temporal_validation`

This evidence supports trajectory representation learning only. It is not attendance-forecast evidence.

---

# 12. Advance rule

## `REPRESENTATION_SUPPORTED`

Use only if:

- validation event-balanced MAE is lower than the zero-change baseline;
- improvement is not solely one validation event;
- predictions are not collapsed to zero;
- no data/fold guard fails.

Then freeze the encoder artifact before using future attendance outcomes.

## `REPRESENTATION_NOT_SUPPORTED`

Use if:

- model fails to beat zero-change baseline;
- improvement is isolated to one event;
- or the model is unstable/pathological.

Do not tune against the same five validation events. Any material change becomes v2.

---

# 13. Relationship to attendance forecasting

A successful self-supervised encoder does **not** mean attendance MAE improves.

The safe downstream sequence is:

1. learn trajectory representation without attendance;
2. freeze encoder;
3. define/freeze a small attendance head using allowed historical labels;
4. create immutable future daily predictions before outcomes;
5. judge attendance value only on genuinely future independent events.

Prospective attendance evidence remains the final authority.

---

# 14. Non-negotiable guards

- frozen data cutoff `2026-10-28T22:09:43.958409Z`;
- no attendance labels anywhere in pretraining inputs/targets;
- no event overlap between train and validation;
- no later snapshots after frozen cutoff;
- no forward-fill/interpolation;
- no post-result architecture/hyperparameter tuning and still call it v1;
- production remains OFF.
