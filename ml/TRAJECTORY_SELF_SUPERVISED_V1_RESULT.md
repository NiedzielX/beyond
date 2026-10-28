# Beyond Ticketing — Self-Supervised Trajectory v1 Result

Date: **2026-10-28**

Status: **REPRESENTATION SUPPORTED / ENCODER FREEZE JUSTIFIED**

Precommit: `trajectory-self-supervised-24h-delta-v1`

Evidence class: `target_free_temporal_validation`

Production impact: **none**

`live_adjustment = 0`

---

## 1. Human summary

The target-free GRU learned trajectory dynamics that generalize to temporally later events better than the frozen zero-change baseline.

Validation result:

- zero-change event-balanced MAE: **0.09172**;
- GRU event-balanced MAE: **0.06290**;
- absolute Delta MAE: **-0.02883**;
- relative improvement: **31.4%**;
- validation events improved: **5 / 5**;
- validation pairs: **168**;
- validation events: **5**.

Decision:

`REPRESENTATION_SUPPORTED`

> **This is evidence that the encoder learned reusable inventory-trajectory dynamics. It is not evidence that attendance MAE improves.**

The next safe step is to freeze the encoder before any attendance-head experiment.

---

## 2. Frozen sample

Data cutoff:

`2026-10-28T22:09:43.958409Z`

Usable sample:

- 26 events / 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / **3397 train pairs**;
- 5 later validation events / **168 validation pairs**.

No attendance labels were used.

No structural P50 was used.

No club/event identity was a model feature.

---

## 3. Validation by event

| Event | Club | Pairs | Zero-change MAE | Model MAE | Delta |
|---:|---|---:|---:|---:|---:|
| 447 | Raków | 35 | 0.07364 | 0.06376 | **-0.00989** |
| 449 | Górnik Zabrze | 34 | 0.11637 | 0.09497 | **-0.02141** |
| 450 | Legia | 35 | 0.11851 | 0.07690 | **-0.04161** |
| 451 | Lech | 29 | 0.05476 | 0.03370 | **-0.02106** |
| 452 | Pogoń Szczecin | 35 | 0.09533 | 0.04516 | **-0.05017** |

All five temporally later validation events improve.

This matters because the aggregate gain is not driven by one event.

---

## 4. What the model learned

Target:

`normalized inventory change approximately 24h later`

The frozen zero-change baseline predicts:

`delta = 0`

The GRU produces non-collapsed predictions and materially reduces validation error.

Target distribution on validation:

- median: **-0.01525**;
- median absolute: **0.00482**;
- min: **-0.38593**;
- max: **+0.10100**.

Prediction distribution:

- median: **-0.10106**;
- median absolute: **0.10106**;
- min: **-0.18154**;
- max: **-0.01242**.

Signed bias:

**-0.06759**.

The encoder is therefore not simply predicting zero. However, the negative bias is material and must be understood before any downstream attendance interpretation.

---

## 5. Why this result is different from Lane B v1/v2

Lane B v1/v2 tried to learn final-attendance residuals from only 10 labeled events.

Self-supervised v1 instead learns trajectory mechanics from thousands of target-free pairs:

- **3397** train pairs;
- **168** validation pairs;
- no attendance targets.

This gives the sequence encoder much more direct evidence about how inventory trajectories evolve without repeatedly optimizing against the same small attendance sample.

---

## 6. What this result DOES support

It supports:

> **The trajectory sequence contains learnable temporal structure that generalizes to later events better than a zero-change baseline under the frozen v1 task.**

It justifies:

- freezing the encoder weights;
- treating the encoder as a candidate representation for downstream experiments;
- continuing forward collection of trajectory and attendance outcomes.

---

## 7. What this result DOES NOT support

It does **not** prove:

- lower attendance MAE;
- production readiness;
- that the encoder should directly correct structural P50;
- that a specific attendance head will work;
- that the inventory proxy equals ticket sales or attendance.

Those require a separately precommitted downstream attendance experiment and ultimately genuine future attendance outcomes.

---

## 8. Next step

Freeze this exact encoder before using attendance labels.

Then define a **small downstream attendance-head protocol** with the encoder frozen.

The next attendance evidence must be prospective:

1. frozen encoder;
2. frozen attendance head;
3. immutable daily predictions before outcomes;
4. future independent events;
5. compare against structural incumbent using event-balanced MAE.

Do not fine-tune the encoder against the exposed 10-event attendance cohort and call the result independent evidence.

---

## 9. Frozen artifact lineage

GitHub Actions run:

`40778526102`

Artifact:

`trajectory-self-supervised-v1-40778526102`

Artifact ID:

`12856440874`

Artifact SHA256:

`0497ae7d00a380857a5e04d9d080ff53af60fbaf112d778c56ca0a27c4132ad3`

Result JSON SHA256:

`c82654792918de699d7b0a184c2e311048412ef1433532fcf93452bffd20a70f`

Encoder `.pt` SHA256:

`3740ba690f75623b4722d28c4084f6062c36cc8dd22e5020c1a5135d4d6f1e2e`

Machine-readable result:

`ml/results/trajectory_self_supervised_24h_delta_v1_result.json`

No production change occurred.
