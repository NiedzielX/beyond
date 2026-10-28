# Beyond Ticketing — Trajectory Validation Fold Contract v1

Frozen for development: **2026-10-28**

Status: **FROZEN DEVELOPMENT VALIDATION CONTRACT / RESEARCH-ONLY**

Contract ID:

`trajectory-validation-fold-contract-v1`

Applies to:

- Lane A simple trajectory residual models;
- Lane B sequence trajectory models.

Feature boundary:

`ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`

---

# 1. Why this contract exists

Current labeled trajectory evidence is small.

As of 2026-10-28, the current checkpoint audit under the shared input gate shows:

| Horizon | Shared input-ready events | Labeled ready events |
|---|---:|---:|
| T-30 | 0 | 0 |
| T-14 | 1 | 0 |
| T-7 | 7 | 4 |
| T-3 | 9 | 5 |
| T-1 | 10 | 10 |

This makes random cross-validation especially dangerous.

A model could appear accurate simply because another prefix from the same event, or a later event from the future, leaked into training.

Therefore the first trajectory comparison uses **strict expanding temporal event folds**.

---

# 2. Independent unit

The independent unit is `ticket_event_id`.

All daily prefixes/cutoffs from one event stay together.

Never place P-14 of one event in train and P-7/P-1 of the same event in validation/test.

Daily row count is not independent-event count.

---

# 3. Primary development validation

Primary method:

> **strict expanding temporal event folds**

For each test kickoff group:

- training events have `kickoff_at < test_kickoff_at`;
- events with the exact same kickoff timestamp are kept in the same test group and cannot train one another;
- all eligible rows/prefixes from a train event are train-only;
- all eligible rows/prefixes from a test event are test-only.

Minimum fold support:

- at least **5 independent train events**;
- at least **4 distinct train clubs**.

A kickoff group before those minima is `NOT_EVALUABLE` for primary forward scoring rather than being forced into a weak fold.

---

# 4. Why not ordinary LOEO as primary

Leave-one-event-out can be a useful diagnostic, but ordinary LOEO may train an early historical target using labels from later events.

That answers a weaker question than the real prospective use case.

Therefore:

- strict forward folds = primary development evidence;
- LOEO = optional diagnostic only;
- LOCO = optional club-generalization diagnostic only;
- random row-level CV = prohibited.

A favorable LOEO/LOCO result cannot override a weak strict-forward result.

---

# 5. Shared registry for Lane A and Lane B

Lane A and Lane B must use the **same frozen fold registry** for a comparison run.

A fold registry manifest must contain:

- contract ID;
- exact eligible event IDs;
- club slug for grouping/diagnostics;
- kickoff timestamp;
- fold ID;
- train event IDs;
- test event IDs;
- train club count;
- train event count;
- test event count;
- code Git SHA;
- feature contract ID;
- dataset manifest/hash.

Lane A and Lane B results are not directly comparable if their event identities/folds differ.

---

# 6. Daily horizons inside a fold

Once an event is assigned to train or test, **all eligible P-N rows for that event inherit the event assignment**.

A model may train on multiple prefixes from train events.

This increases training examples but does not change independent-event counts.

Primary scoring must still report:

- independent test events;
- clubs;
- MAE by horizon;
- event-balanced aggregate according to the model precommit.

---

# 7. Preprocessing inside folds

For every fold:

- numeric imputation is fit on train rows only;
- missing indicators are created deterministically;
- encoders are fit on train rows only;
- standardization/scaling is fit on train rows only;
- sequence padding/masks do not learn from test labels;
- early stopping/model selection may use only a train-derived inner validation scheme, never the outer test outcomes.

Do not preprocess once on the full dataset before fold assignment.

---

# 8. Model selection boundary

Outer strict-forward test outcomes are evidence, not a tuning surface.

Do not run a broad architecture/hyperparameter tournament and choose the winner based on the same outer test events.

For the first comparison:

- Lane A candidate set remains small/precommitted;
- Lane B architecture set remains deliberately small;
- any hyperparameter selection must occur inside training data or in a separately exposed research cohort;
- a candidate chosen for prospective shadow inference must be frozen before future target outcomes.

---

# 9. Sparse-horizon rule

A horizon may be technically scored but still be too sparse for a meaningful conclusion.

Always show support next to MAE.

Current T-30/T-14 data are collection-first, not evidence-ready.

Do not pool sparse early horizons with later horizons in a way that hides their support difference unless the aggregation rule was explicitly precommitted.

---

# 10. Current implication

With the present sample, the first meaningful strict-forward model development is likely to be driven by later horizons/events.

That is acceptable.

The correct response to sparse early history is:

- continue genuine forward collection;
- use variable-length prefixes;
- keep the same event-safe fold rule;
- avoid overclaiming.

It is **not** to backfill missing P-30/P-60 trajectories or switch to random daily-row CV.

---

# 11. Frozen decision

> **For the first Lane A vs Lane B trajectory comparison, use one deterministic expanding temporal event-fold registry with minimum 5 prior train events and 4 train clubs. Same-kickoff events stay together. All prefixes from an event inherit the same fold.**

Any change to these primary fold semantics requires a new contract version.
