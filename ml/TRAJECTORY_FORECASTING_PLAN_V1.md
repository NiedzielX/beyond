# Beyond Ticketing — Daily Trajectory Forecasting Plan v1

Last updated: **2026-10-28**

Status: **ACCEPTED / RESEARCH-ONLY / START NOW**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

Operational priorities: `ml/EXECUTION_PLAN_CURRENT.md`

Production remains unchanged:

`live_adjustment = 0`

---

# 1. In plain language

Today Beyond does not fully behave like this:

`P-50 -> P-49 -> P-48 -> ... -> today -> forecast what happens next -> final attendance`

It uses trajectory information, but only partially and at selected horizons/cutoffs.

This plan changes the research direction so that **the full observed trajectory becomes a first-class model input**.

For every active event we want a new forecast every day.

Example:

- at P-30 the model sees everything genuinely known up to P-30;
- at P-29 it sees the same history plus the new P-29 evidence;
- at P-28 it sees an even longer observed prefix;
- and so on until P-1.

The model should understand not only **where demand is today**, but **how it got there**.

Two matches can have the same current inventory/demand proxy but completely different trajectories:

- one may be accelerating quickly;
- another may have been flat for a week.

Those should not automatically receive the same forecast.

---

# 2. What we are deciding now

We accept two parallel research lanes.

## Lane A — simple trajectory model

Use interpretable engineered trajectory features such as:

- current level;
- 1d / 3d / 7d change;
- velocity;
- acceleration;
- slope;
- slope change;
- volatility;
- curve similarity.

Predict a residual over the structural forecast rather than relearning attendance from scratch.

This is the benchmark.

## Lane B — high-risk sequence model

We will **not wait for a large textbook-quality dataset before testing sequence models**.

We accept the research risk and start early in shadow mode.

Initial order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact attention/Transformer encoder only if sequence modelling already looks promising.

Do not begin with a large Transformer or TFT.

The sequence lane must beat Lane A under the same PIT-safe, event-grouped evaluation.

---

# 3. Why taking this risk is reasonable

We may wait a long time before we have hundreds of perfectly labeled booking curves.

Waiting for an ideal dataset could therefore delay the most interesting model direction by many months or years.

But we must keep one distinction clear:

> **More daily rows do not mean more independent events.**

For example:

`50 events x 40 daily prefixes = 2,000 training rows`

but still only:

`50 independent events`

This means sequence models may overfit easily.

Therefore we accept **model risk**, but not **evidence risk**.

---

# 4. Non-negotiable evidence rules

1. Split by event, never by random daily rows.
2. All prefixes from one event stay in the same fold.
3. No snapshot captured after a cutoff may enter that cutoff's features.
4. No target future trajectory may enter an earlier prediction.
5. No target attendance may enter prediction construction.
6. Scalers/normalizers must be fitted inside training folds.
7. Hyperparameter/model selection must stay separate from final prospective evaluation.
8. Persist forecasts before outcomes are known.
9. Never count correlated daily rows as independent evidence.
10. Existing frozen P7/P9/Form5/Long72 experiments remain unchanged.

---

# 5. Daily inference, not daily retuning

The system should produce a new immutable forecast at each eligible daily cutoff.

The model itself remains frozen during its evaluation cohort.

Allowed:

`same frozen model + new genuine daily evidence -> new forecast`

Not allowed:

`new daily evidence -> retune model against newly exposed outcomes -> new forecast`

This gives us a useful forecast history without destroying prospective validity.

---

# 6. Canonical daily trajectory dataset

Create one PIT-safe row per event and daily cutoff.

Canonical cutoff:

`as_of_at(P-N) = kickoff_at - N * 24h`

Initial research range:

`P-60 ... P-1`

Use only data genuinely visible by the cutoff.

Missing observations stay missing.

Never manufacture history to complete the sequence.

## Required information

### Identity and lineage

- ticket_event_id;
- club_slug;
- kickoff_at;
- as_of_at;
- days_to_event;
- latest visible snapshot ID/time;
- snapshot staleness;
- source lineage;
- dataset/code version.

### Current trajectory state

- inventory/demand proxy;
- share of verified capacity;
- first visible proxy;
- days since first observation;
- observation density;
- missingness/data-quality state.

### Dynamics

- delta_1d / delta_3d / delta_7d;
- velocity_1d / velocity_3d / velocity_7d;
- acceleration;
- recent slope;
- longer slope;
- slope change;
- volatility;
- normalized curve position;
- trajectory similarity statistics.

### Structural anchor

- incumbent P10/P50/P90;
- incumbent family/version;
- verified capacity;
- approved PIT-safe context for that model version.

---

# 7. Immutable daily forecast ledger

For each eligible:

`(ticket_event_id, days_to_event, model_version)`

persist exactly one immutable attempt.

Persist both:

- successful predictions;
- fail-closed attempts.

Minimum lineage:

- event;
- daily horizon;
- exact as_of_at;
- predicted_at;
- model/precommit version;
- dataset/feature manifest SHA;
- observed prefix range;
- latest source snapshot lineage;
- incumbent forecast;
- challenger forecast;
- status/fail reason;
- `target_values_used=false`;
- `production_change=false`.

Once real attendance is known, score the stored forecast. Never regenerate it after the fact.

---

# 8. MAE should be viewed as a curve

We still need one event-balanced primary MAE for governance, but product/research analysis must show accuracy by horizon.

Minimum reporting:

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
- forecast revision/stability between consecutive days;
- P10/P90 coverage when available.

The useful product question is not only:

> What is our MAE?

but also:

> **How early before kickoff does Beyond become meaningfully accurate?**

---

# 9. Sequence learning with limited attendance labels

We have more trajectory observations than final attendance labels.

Therefore Lane B may use target-free/self-supervised pretraining.

Possible tasks:

- predict the next genuine proxy observation from the prefix;
- predict short-horizon proxy change;
- learn representations of curve shape;
- chronology-safe masked/reconstruction tasks on training sequences.

Then use the learned representation together with the structural prior to predict:

`attendance residual = actual attendance - structural P50`

This can help representation learning, but it does **not** increase the number of independent events in final evaluation.

---

# 10. First model comparison

The clean first comparison should be:

## Lane A

`Structural P50 + engineered trajectory residual model`

versus

## Lane B

`Structural P50 + small sequence encoder residual model`

Both use:

- the same eligible events;
- the same event-grouped folds;
- the same PIT cutoffs;
- the same primary metric;
- the same downstream scoring rules.

The core question is:

> **Does reading the sequence itself add signal beyond velocity/acceleration/slope features?**

---

# 11. Relationship to P9

Do not replace or rewrite P9.

P9 remains a separate frozen experiment:

`curve similarity -> fixed historical neighbors -> residual correction at T-48/T-24`

This plan asks a different question:

`full observed daily prefix -> evolving forecast across many horizons`

P9 v1/v2 evidence must remain separately auditable.

---

# 12. Product direction

The dashboard should eventually distinguish four things clearly:

1. **observed inventory/demand proxy**;
2. **today / as-of boundary**;
3. **predicted future proxy trajectory**;
4. **predicted final attendance P10/P50/P90**.

Conceptually:

`observed P-30 ... P-14 | today | predicted P-13 ... P-1 -> final attendance`

The next day, the real P-13 observation replaces yesterday's predicted P-13 and the remaining path is recalculated.

Inventory proxy must never be presented as confirmed paid ticket sales.

---

# 13. Execution order

## Start now

1. Preserve all frozen prospective lanes unchanged.
2. Materialize the canonical daily trajectory dataset.
3. Create immutable daily forecast/attempt persistence.
4. Add horizon-wise MAE reporting.
5. Audit observation density/missingness by event/club/horizon.

## Then, in parallel

6. Precommit Lane A simple trajectory challenger.
7. Precommit a small Lane B sequence challenger.
8. Run both under identical event-grouped/PIT-safe validation.
9. Investigate self-supervised trajectory pretraining.
10. Start prospective daily shadow inference before outcomes are known.

## Decision

11. Score only genuine frozen predictions.
12. Compare horizon-wise and event-balanced Delta MAE.
13. Compare downside/uncertainty.
14. Increase model complexity only if sequence representation materially beats Lane A.
15. Production remains a separate reviewed decision.

---

# 14. Accepted research decision

> **YES — test sequence models early.**

But the acceptance is specifically:

> **Take controlled model risk in research; do not take shortcuts with PIT safety, event independence or prospective evidence.**

The objective is not to demonstrate that an LSTM/Transformer can fit the existing curves.

The objective is to prove that sequence representation reduces **true prospective event-balanced attendance MAE** beyond the structural incumbent and simpler trajectory models.
