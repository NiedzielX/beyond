# Beyond Ticketing — Daily Trajectory Forecasting Plan v1

Status: **PLANNED / RESEARCH-ONLY**

Purpose: define the next MAE research direction without modifying or invalidating any frozen prospective lane.

Canonical North Star remains:

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons, with PIT-safe, reproducible evidence.**

This plan does **not** change P7, P9 v1/v2, Form5, Long72 or any other frozen/precommitted experiment. Production remains unchanged unless a later explicit promotion decision is made.

`live_adjustment = 0`

---

## 1. Problem statement

The current system uses booking/inventory trajectory only partially:

- the historical structural core is evaluated at a small set of horizons;
- P9 compresses trajectory into selected canonical hours and currently evaluates only fixed T-48/T-24 prediction windows;
- the product chart displays inventory proxy and persisted P50 forecasts together, but this is not yet a model that continuously consumes the full observed trajectory and forecasts the remaining path.

The missing research question is:

> **Does the complete point-in-time trajectory observed up to today contain enough incremental information to reduce prospective attendance MAE beyond the structural incumbent and the current fixed-window challengers?**

Target conceptual behaviour:

`P-50 -> P-49 -> P-48 -> ... -> today -> forecast remaining trajectory -> final attendance P50`

At every new daily cutoff the model must receive the whole observed prefix available at that cutoff, not only the latest point.

---

## 2. Core principle: daily inference, not daily retuning

The system should create a new immutable forecast at every eligible daily cutoff for every active event.

Example:

- P-30: use only data visible by kickoff - 30 days;
- P-29: use the same historical prefix plus the new information visible by kickoff - 29 days;
- P-28: recalculate using the longer observed prefix;
- continue until P-1 where support exists.

The model version remains frozen during an evaluation cohort.

**Allowed:** new inputs arrive and the frozen model produces a new forecast.

**Not allowed:** refitting/tuning the model every day against newly exposed outcomes during the same evaluation cohort.

Daily forecast generation therefore creates richer prospective evidence without weakening governance.

---

## 3. Canonical daily trajectory dataset

Create a PIT-safe dataset with one event/cutoff row for each integer daily horizon where genuine observations exist.

Canonical cutoff definition:

`as_of_at(P-N) = kickoff_at - N * 24h`

Initial research range:

`P-60 ... P-1`

The exact supported range may be narrower for an event depending on when genuine ticketing observation starts.

For each cutoff use only records with:

`captured_at <= as_of_at`

Never use a future snapshot to fill an earlier cutoff.

Never manufacture historical booking-curve data.

If a daily observation is unavailable, preserve it as missing and expose the reason/staleness explicitly.

### Minimum row schema

Identity / PIT lineage:

- ticket_event_id;
- club_slug;
- kickoff_at;
- as_of_at;
- days_to_event;
- latest_snapshot_id_visible_at_cutoff;
- latest_snapshot_captured_at;
- snapshot_age_hours;
- source lineage / source version;
- dataset build SHA/version.

Current trajectory state:

- inventory_proxy;
- inventory_proxy_share_of_verified_capacity;
- first_visible_inventory_proxy;
- days_since_first_visible_observation;
- raw_snapshot_count_visible;
- clean_snapshot_count_visible;
- missing_daily_points;
- observation_density;
- data-quality flags.

Trajectory dynamics, derived PIT-safely from the observed prefix only:

- delta_1d;
- delta_3d;
- delta_7d;
- velocity_1d;
- velocity_3d;
- velocity_7d;
- acceleration_1d_vs_7d;
- recent slope;
- longer-window slope;
- slope change;
- trajectory volatility;
- days since last material acceleration/deceleration;
- normalized curve position;
- similarity statistics vs completed prior PIT-safe curves.

Structural context available at cutoff:

- structural incumbent P10/P50/P90;
- relevant incumbent/model family identity;
- verified stadium capacity;
- existing PIT-safe static/context features already approved for the relevant research dataset.

No actual target attendance belongs in the inference dataset before the event outcome is genuinely known.

---

## 4. Daily forecast ledger

For every eligible `(ticket_event_id, days_to_event, model_version)` persist exactly one immutable forecast attempt.

Persist both successful predictions and fail-closed attempts.

Required fields include:

- ticket_event_id;
- days_to_event;
- exact as_of_at;
- predicted_at;
- model/precommit version;
- feature/dataset manifest SHA;
- observed-prefix start/end;
- latest visible snapshot lineage;
- incumbent P10/P50/P90;
- challenger P10/P50/P90;
- forecast status;
- fail-closed reason when no prediction is emitted;
- `target_values_used=false`;
- `production_change=false`.

After genuine attendance arrives, score each previously persisted forecast without recomputing it.

---

## 5. Evaluation view: MAE as a curve, not one number

Primary governance metric remains prospective event-balanced MAE, but trajectory work must expose MAE by horizon.

Minimum reporting:

| Horizon | Incumbent MAE | Challenger MAE | Delta MAE | Event count | Club count |
|---|---:|---:|---:|---:|---:|
| P-30 | | | | | |
| P-21 | | | | | |
| P-14 | | | | | |
| P-7 | | | | | |
| P-3 | | | | | |
| P-1 | | | | | |

Also report:

- event-balanced MAE across precommitted horizon bands;
- signed bias;
- event improvement rate;
- median event AE;
- P90 event AE;
- worst event degradation;
- per-club downside;
- forecast stability between consecutive days;
- calibration / interval coverage for P10-P90 when available.

Daily rows from the same event are **not independent events**. Never treat a large number of daily rows as a large independent evaluation sample.

---

## 6. Model strategy: run two lanes in parallel

Waiting for a theoretically ideal dataset may delay learning for too long. Therefore use a controlled two-lane strategy.

### Lane A — conservative / high-signal baseline

Goal: establish the value of trajectory information with models that are difficult to overfit and easy to audit.

Candidate family:

1. structural incumbent + regularized residual model;
2. Ridge / ElasticNet on PIT-safe trajectory features;
3. small tree-based residual learner (for example the same restrained model families already used elsewhere in the repository);
4. nearest-trajectory / curve-similarity residual correction.

Primary target:

`attendance - structural_incumbent_P50`

Prefer predicting a residual/correction rather than learning attendance from scratch. The structural incumbent already contains substantial information and gives the trajectory model a stronger prior.

This lane is the benchmark that any sequence model must beat.

### Lane B — high-risk sequence research

Start this lane **before** the dataset is conventionally considered large enough, but keep it shadow/research-only.

The purpose is to learn whether representation learning over the full observed prefix can extract signal that engineered features miss.

Candidate progression:

1. small GRU;
2. small LSTM;
3. temporal convolutional network (TCN);
4. compact attention/Transformer-style encoder;
5. only later, more complex architectures such as TFT-style models if the evidence justifies them.

Do not begin with a large Transformer.

The first sequence challengers should be deliberately small and strongly regularized.

Recommended formulation:

`observed trajectory prefix + structural prior/context -> residual correction / final attendance distribution`

not:

`raw trajectory -> attendance from scratch`

---

## 7. Why sequence models are worth testing despite limited labels

The risk is real: daily rows do not create independent matches, and a high-capacity sequence model can memorize clubs/events quickly.

However, waiting for hundreds or thousands of perfect labeled booking curves may be commercially unrealistic.

Therefore the correct strategy is **controlled research risk**, not indefinite waiting.

Possible ways to make limited data more useful without leaking targets:

### A. Pool trajectories across clubs

Train one global sequence representation rather than separate club-specific deep models. Preserve club/context identity as features rather than fragmenting the sample.

### B. Use every genuine prefix for representation learning

One completed event can provide many valid prefixes:

`P-30 prefix`, `P-29 prefix`, ..., `P-1 prefix`.

These are useful training examples but remain grouped under the same event for all splits, bootstraps and evaluation.

### C. Self-supervised trajectory pretraining

Use genuine unlabeled inventory trajectories to learn representations without requiring final attendance labels.

Examples of target-free pretraining tasks:

- predict the next observed inventory point from the historical prefix;
- reconstruct masked historical trajectory points using only observations that would be available within the training sequence;
- classify/cluster trajectory shape;
- predict future inventory-proxy change on completed historical sequences.

A later attendance head can then be trained on the smaller labeled attendance cohort.

Any pretraining implementation must preserve chronology and must never expose a target event's future trajectory to its own earlier inference cutoff.

### D. Residual learning against structural prior

Reduce the problem complexity by asking the sequence model to learn only the part the structural model misses.

### E. Strong regularization and tiny capacity

For early experiments prefer:

- small hidden dimensions;
- few layers;
- dropout / weight decay;
- early stopping based on event-grouped validation;
- no architecture/hyperparameter sweep on the final prospective cohort.

---

## 8. Non-negotiable leakage rules for daily/sequence models

1. Split by event, never random daily rows.
2. Prefer temporal and club-aware validation (LOEO/LOCO or equivalent grouped designs) depending on the research question.
3. All prefixes from one target event stay in the same fold.
4. No snapshot with `captured_at > as_of_at` enters target features.
5. No target attendance enters prediction building.
6. No target future trajectory enters an earlier target cutoff.
7. Any normalization/scaler fitted from training data must be fitted inside the training fold.
8. Hyperparameter/model selection must remain separate from the final prospective evaluation cohort.
9. Immutable prospective predictions must exist before outcomes are opened.
10. Never count correlated daily rows as independent evidence when reporting confidence or readiness.

---

## 9. Forecast-the-curve extension

The long-term product model should not be restricted to a single final attendance number.

At each daily cutoff it should eventually be able to emit:

- expected next-day inventory/demand proxy;
- expected remaining trajectory;
- final attendance P10/P50/P90.

Example at P-14:

`observed P-30 ... P-14 -> predicted P-13 ... P-1 -> final attendance distribution`

At P-13 the genuine P-13 observation replaces the previous predicted P-13 and the remaining path is recalculated.

This is a later extension. The first success criterion remains lower prospective final-attendance MAE.

---

## 10. Product/dashboard consequence

The chart should evolve from two visually adjacent series into an explicit observed-vs-forecast trajectory view.

Target display:

- solid line: genuinely observed inventory/demand proxy prefix;
- dashed future line: model-predicted remaining proxy trajectory (when supported);
- separate final attendance distribution/P50;
- vertical `today/as-of` boundary;
- visible forecast revision versus previous daily cutoff;
- explicit statement that inventory proxy is not confirmed ticket sales.

The UI must never imply that `capacity - publicly available inventory` is confirmed paid attendance.

---

## 11. Execution order

### Now — do not wait for current P9 scoring

1. Preserve all currently frozen prospective lanes unchanged.
2. Materialize the canonical daily trajectory dataset.
3. Persist immutable daily forecast/attempt rows for active events using the current incumbent where available.
4. Add horizon-wise MAE reporting infrastructure.
5. Audit observation density and missingness by event/club/horizon.

These steps create evidence and do not require changing the production model.

### Next — conservative trajectory challenger

6. Precommit a simple residual trajectory baseline (Lane A).
7. Evaluate with event-grouped historical validation where PIT support is honest.
8. Begin prospective daily shadow predictions before target outcomes exist.

### In parallel — intentionally risky sequence lane

9. Build a very small sequence challenger (GRU/LSTM/TCN first).
10. Benchmark it against Lane A under identical grouped/PIT-safe splits.
11. Investigate target-free/self-supervised trajectory pretraining.
12. Only test a compact Transformer-style architecture if the smaller sequence models show that sequential representation itself adds signal.

### Promotion boundary

13. Score frozen challengers only after genuine outcomes.
14. Compare horizon-wise and event-balanced Delta MAE plus event-level downside.
15. Do not promote based on training fit, row count, one event, or one favorable horizon.
16. Production change requires a separate reviewed decision.

---

## 12. Decision rule on 'risking' deep sequence models

Decision: **YES — test them early, but as a separate high-risk research lane.**

Reasoning:

- waiting for a conventionally large labeled dataset may take too long;
- the cost of a shadow experiment is low compared with the potential signal from full trajectory shape;
- we can exploit many genuine prefixes and unlabeled trajectory data for representation learning;
- but correlated prefixes do not solve the independent-event sample-size problem;
- therefore a deep model must earn its place by beating simple trajectory baselines on event-grouped and then prospective evidence.

The objective is not to prove that a Transformer/LSTM can fit the existing curves.

The objective is to prove that sequential representation reduces **true prospective event-balanced attendance MAE** beyond the structural incumbent and simpler trajectory challengers.

---

## 13. Immediate research hypothesis

Primary new hypothesis:

> **A PIT-safe model that consumes the full observed daily inventory/demand trajectory prefix and predicts a residual over the structural attendance prior will reduce prospective MAE, particularly at medium/late horizons, compared with models that use only sparse fixed horizons or the latest snapshot.**

Secondary high-risk hypothesis:

> **A small sequence encoder pretrained or trained on genuine booking-curve prefixes can extract incremental trajectory-shape information that engineered velocity/acceleration features fail to capture.**

Both hypotheses must be evaluated prospectively and independently from currently frozen lanes.
