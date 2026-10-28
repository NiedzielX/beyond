# Beyond Ticketing — Daily Trajectory Forecasting Plan v1

Last updated: **2026-10-28**

Status: **ACCEPTED / INFRASTRUCTURE IN PROGRESS / RESEARCH-ONLY**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

Operational priorities: `ml/EXECUTION_PLAN_CURRENT.md`

Current coverage audit: `ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`

Production remains unchanged:

`live_adjustment = 0`

---

# Part A — Human view

## 1. What we are trying to build

Beyond should increasingly forecast like this:

`P-60 -> P-59 -> ... -> P-14 -> P-13 -> today -> predicted future -> final attendance`

At every daily cutoff the system creates a new forecast using **everything genuinely observed up to that moment**.

Example:

- at P-14, use the trajectory visible by P-14;
- at P-13, add the genuine evidence that appeared since P-14 and forecast again;
- continue until P-1.

This is **daily inference**, not daily model retraining.

The model should understand not only:

> where demand appears to be today

but also:

> how it got there.

Two matches can have the same current demand/inventory proxy while one is accelerating and the other has been flat for days. They should not automatically receive the same final-attendance forecast.

---

## 2. Important reality: we do not have full P-60 trajectories yet

The 2026-10-28 live-data audit found:

- 32 Ekstraklasa events with at least one genuine pre-kickoff inventory observation;
- 14 clubs;
- median first observation only around **P-9.3**;
- 75% of observed events begin by about **P-14** or later;
- earliest observed event begins around **P-30.3**;
- current coverage is 3% at P-30, 21.9% at P-14, 61.5% at P-7, 75% at P-3 and 95% at P-1;
- current P-31...P-60 historical coverage is zero.

Therefore:

> **P-60 is the collection horizon, not a requirement that every model input contain 60 genuine daily points.**

We will not wait for an ideal dataset and we will not invent missing history.

---

## 3. What “P-50, P-49, P-48...” means in practice

We still create an exact forecast opportunity at every daily cutoff:

`as_of_at(P-N) = kickoff_at - N * 24h`

But model input is the **genuine observed prefix** available by that cutoff.

If an event really has observations from P-30 onward, the model can learn from that long history.

If the first genuine observation appears only at P-9, the model sees a shorter prefix and explicit missingness/maturity information.

Missing does **not** become zero and does **not** become an invented interpolated sale/inventory value.

---

## 4. Why we still want to risk sequence models early

Waiting for hundreds of complete booking curves could take a very long time.

We therefore accept **controlled model risk**:

- start small sequence-model research early;
- keep it shadow/research-only;
- benchmark it against a simpler trajectory model;
- never weaken PIT safety or validation just to get a good result.

The key distinction remains:

`50 events x 40 prefixes = 2,000 rows`

but still only:

`50 independent events`.

More prefixes help the model learn representations. They do not create 2,000 independent attendance outcomes.

---

# Part B — Accepted research design

## 5. Two lanes in parallel

### Lane A — simple trajectory benchmark

Use the structural attendance forecast as the anchor and learn only an incremental residual.

Conceptually:

`Structural P50 + engineered trajectory correction -> challenger P50`

Candidate inputs include:

- current proxy level / capacity share;
- change over 1d / 3d / 7d where genuinely observable;
- velocity;
- acceleration;
- observation maturity;
- snapshot density/gaps;
- short-vs-long trajectory behaviour;
- curve-similarity statistics.

Candidate model families remain deliberately restrained:

- Ridge / ElasticNet;
- small tree/boosting residual learner;
- auditable nearest-trajectory/pickup correction.

Lane A is the benchmark that sequence modelling must beat.

### Lane B — high-risk sequence model

Accepted order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact attention/Transformer encoder only if earlier sequence models show real value.

Do not begin with a large Transformer/TFT.

Recommended formulation:

`genuine observed sequence + structural prior/context -> attendance residual / final distribution`

---

## 6. Sequence input should preserve genuine observations

Because coverage is irregular, do **not** manufacture a perfectly filled 60-day vector merely to make neural-network input convenient.

Preferred Lane B representation is a variable-length sequence of genuine observations available by the daily cutoff, for example:

`[(hours_to_kickoff, normalized_proxy, delta_time, quality), ...]`

plus:

- days-to-event / exact cutoff;
- structural P50 and allowed structural/context inputs;
- sequence length / padding mask;
- missingness/data-quality indicators.

Padding is implementation machinery only. A padded zero must never mean genuine zero inventory.

The model may also use a precommitted daily-resampled representation later, but only if its imputation/interpolation semantics are explicitly PIT-safe and tested separately.

---

## 7. Self-supervised learning is especially relevant

We have more trajectory observations than genuine attendance labels.

Lane B may therefore learn trajectory representations from target-free tasks such as:

- predict the next genuine proxy observation;
- predict short-window proxy change;
- learn/cluster curve-shape representations;
- chronology-safe masked/reconstruction tasks on training sequences.

Then attach a smaller attendance/residual head using genuinely labeled events.

This may improve representation learning, but it does **not** increase independent-event count for final attendance evaluation.

---

# Part C — Non-negotiable evidence contract

## 8. Daily inference, not daily retuning

Allowed:

`same frozen model + new genuine prefix -> new forecast`

Not allowed:

`newly exposed outcomes -> retune the same evaluation model -> rewrite future/earlier evidence`

A model version remains frozen through its evaluation cohort.

---

## 9. Event independence

1. Event/match is the independent evaluation unit.
2. All prefixes/cutoffs from one event stay in one fold.
3. Random daily-row/snapshot split is forbidden as headline evidence.
4. Scalers/normalizers are fitted inside training folds.
5. Uncertainty/bootstrap operates at event block level.

---

## 10. PIT safety

For a target forecast at `as_of_at`:

- every target snapshot must satisfy `captured_at <= as_of_at`;
- no future target trajectory may enter an earlier cutoff;
- no target attendance may be used;
- no future odds/context/lineup information may be used unless genuinely known by cutoff;
- structural/incumbent forecasts must genuinely have existed by cutoff;
- missing/hidden inventory is not zero;
- no historical reconstruction may be called prospective.

Existing P7/P9/Form5/Long72 frozen contracts remain unchanged.

---

# Part D — Infrastructure contract

## 11. Canonical daily trajectory dataset

Canonical code:

`ml/demand_engine/daily_trajectory_dataset.py`

It creates exact rows from P-60 to P-1 while preserving unavailable history as missing.

It deliberately reuses:

`ml/demand_engine/live_trajectory_feature_store.py`

rather than creating a second definition of trajectory semantics.

Current guarantees:

- exact daily cutoffs;
- future snapshots excluded;
- missing rows preserved;
- structural prior attached only if it genuinely existed by cutoff;
- inventory remains explicitly `demand_proxy_not_confirmed_sales`.

Tests:

`ml/demand_engine/test_daily_trajectory_dataset.py`

Demand Engine smoke CI passed after integration on 2026-10-28.

---

## 12. Immutable prospective ledger

Live private tables:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

For each eligible `(ticket_event_id, days_to_event, model_version)` persist at most one immutable attempt.

Persist successful and fail-closed attempts.

The persistence contract records, among other things:

- event;
- daily horizon / exact as-of;
- model/precommit version;
- dataset manifest SHA;
- observed prefix lineage;
- latest source snapshot lineage;
- incumbent forecast;
- status/reason;
- challenger forecast if emitted;
- `target_values_used=false`;
- `production_change=false`.

Writes are controlled through RPC rather than direct `service_role` table insert.

Canonical SQL:

`supabase/sql/daily_trajectory_prospective_evidence_v1.sql`

---

## 13. Post-outcome scoring and MAE curve

Scoring only happens after genuine attendance exists and was confirmed after the immutable prediction timestamp.

Live functions:

- `public.score_daily_trajectory_completed_v1()`;
- `public.daily_trajectory_mae_by_horizon_v1()`.

Minimum reporting by horizon:

| Horizon | Incumbent MAE | Challenger MAE | Delta MAE | Events | Clubs |
|---|---:|---:|---:|---:|---:|
| P-30 | | | | | |
| P-21 | | | | | |
| P-14 | | | | | |
| P-7 | | | | | |
| P-3 | | | | | |
| P-1 | | | | | |

Also report:

- signed bias;
- median AE;
- P90 AE;
- event improvement rate;
- worst event degradation;
- per-club downside;
- forecast revision/stability;
- P10/P90 coverage when available.

Always show support counts next to an MAE. A result on 2–7 events is not equivalent to one backed by substantially more independent events.

---

# Part E — Execution

## 14. Completed infrastructure as of 2026-10-28

- [x] canonical PIT-safe daily dataset builder/contract;
- [x] future-snapshot / structural-prior leakage tests;
- [x] Demand Engine CI integration and green run;
- [x] live data coverage/missingness audit;
- [x] immutable daily attempt ledger;
- [x] immutable daily prediction ledger;
- [x] post-outcome immutable score ledger;
- [x] horizon-wise MAE backend;
- [x] security/permission verification for the new ledger;
- [x] Supabase security/performance advisor check; new FK index issue fixed.

No synthetic daily prediction was inserted to claim progress.

---

## 15. Next execution steps

1. Protect all current P9/Form5/P7 prospective evidence first.
2. Freeze the shared **Trajectory Feature Contract v1** for Lane A/B.
3. Build the event-grouped development dataset/export using the canonical daily builder.
4. Define one fixed event-grouped validation split/fold registry shared by Lane A and Lane B.
5. Precommit Lane A development protocol.
6. Precommit the first small Lane B sequence protocol.
7. Run Lane A and Lane B on identical eligible events/cutoffs.
8. Report support + horizon-wise MAE, not one optimistic aggregate.
9. Start prospective daily shadow inference for the frozen winner(s) before future outcomes are known.
10. Keep collecting longer prefixes forward; do not delay research waiting for complete P-60 history.

---

## 16. First model comparison

The first clean comparison should remain:

### Lane A

`Structural P50 + engineered trajectory residual model`

versus

### Lane B

`Structural P50 + small sequence encoder residual model`

Same:

- events;
- cutoffs;
- folds;
- PIT rules;
- incumbent;
- primary metric;
- scoring.

Core question:

> **Does reading the ordered trajectory itself reduce true attendance error beyond what engineered trajectory features already capture?**

---

## 17. Decision rule

### Lane A wins / Lane B does not

Use the simpler trajectory approach. Do not add sequence complexity.

### Both win and Lane B materially beats Lane A

Continue sequence research and require genuine prospective confirmation.

### Both fail

Diagnose proxy quality, coverage, independent-event count and structural-incumbent strength before starting another model tournament.

### Historical/grouped win but prospective loss

Prospective evidence wins.

---

# 18. Relationship to P9

P9 is not replaced.

P9 asks:

`curve similarity -> fixed prior neighbors -> residual correction at T-48/T-24`

Daily trajectory research asks:

`full genuine prefix -> evolving forecast across many daily horizons`

P9 v1/v2 remain frozen and separately auditable.

---

# 19. Product direction

The dashboard should eventually distinguish clearly:

1. observed inventory/demand proxy;
2. today / as-of boundary;
3. predicted future proxy trajectory;
4. predicted final attendance P10/P50/P90.

Conceptually:

`observed prefix | today | predicted remaining path -> final attendance`

The next day, new genuine information replaces the previous expectation and the remaining forecast is recalculated.

Inventory proxy must never be presented as confirmed paid ticket sales.

---

# 20. Accepted research decision

> **YES — test sequence models early.**

More precisely:

> **Take controlled model risk in research; never take shortcuts with PIT safety, event independence or prospective evidence.**

The objective is not to prove that a GRU/LSTM/Transformer can fit existing curves.

The objective is to prove that sequence representation reduces **true prospective event-balanced attendance MAE** beyond the structural incumbent and simpler trajectory models.
