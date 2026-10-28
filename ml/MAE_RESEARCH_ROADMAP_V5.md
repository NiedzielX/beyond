# Beyond Ticketing — MAE Research Roadmap v5

Last updated: **2026-10-28**

Status: **CANONICAL MAE RESEARCH STRATEGY**

Supersedes the strategic direction in `ml/MAE_RESEARCH_ROADMAP_V4.md`.

Operational source of truth remains:

`ml/EXECUTION_PLAN_CURRENT.md`

Detailed trajectory design:

`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary decision metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction:

`Delta MAE < 0`

This means that readiness, snapshot counts, training rows, prediction counts and model complexity are not success metrics. They only enable experiments.

Production remains unchanged unless a separate reviewed promotion decision is made:

`live_adjustment = 0`

---

# 2. What changed in v5

The previous roadmap correctly identified booking-curve shape as a major missing source of signal. P9 implemented the first auditable version of that idea, but it is intentionally narrow:

- selected canonical trajectory points;
- nearest-curve similarity;
- fixed T-48/T-24 prospective windows;
- residual correction over an incumbent forecast.

The next research step is broader and more product-aligned:

> **Treat the complete observed daily trajectory of an event as a first-class forecasting object.**

Target behaviour:

`P-60 -> P-59 -> ... -> P-2 -> P-1 -> final attendance`

At each daily cutoff the model should see the complete trajectory prefix genuinely available at that time and produce a new immutable forecast.

This is **daily inference**, not daily retuning.

The second strategic change is deliberate acceptance of controlled model risk:

> **Do not wait for a conventionally large labeled trajectory dataset before testing sequence models. Test small sequence models early in a separate shadow research lane, while keeping simple trajectory models as the benchmark.**

This is a research-risk decision, not a relaxation of evidence quality.

---

# 3. Scientific rules that do not change

1. Event/fixture is the independent evaluation unit.
2. All rows/prefixes from one event stay in the same train/test fold.
3. Random daily-row or snapshot splitting is forbidden as headline evidence.
4. Every target feature must satisfy point-in-time availability at the forecast cutoff.
5. No target future trajectory may enter an earlier target cutoff.
6. No target attendance may enter prediction construction.
7. Frozen prospective lanes remain immutable after their evaluation outcomes become available.
8. Failed/insufficient experiments are valid evidence and must not be silently repaired.
9. No historical backfill may be described as prospective evidence.
10. Any new learner/model/target/feature contract requires a new version/precommit.
11. MAE remains the primary point-forecast selector.
12. Event-level downside, bias, median AE, P90 AE, improvement rate and uncertainty remain mandatory guardrails.
13. No research result activates production automatically.

---

# 4. Two different jobs: evidence collection and model development

Beyond must do both at the same time without mixing them.

## A. Protect existing prospective evidence

Current frozen/precommitted lanes remain unchanged:

- P7 prospective;
- P9 v1;
- P9 Family Fallback v2;
- Form5 prospective;
- Long72 frozen package;
- P11/P4a genuine evidence collection.

Do not mutate these lanes to make the next model better.

## B. Build the next research capability in parallel

The new daily trajectory program may start now because creating PIT-safe datasets, immutable daily forecast ledgers and research-only challengers does not invalidate frozen lanes.

The rule is:

> **Frozen validation protects truth. It does not prohibit new separately versioned research.**

---

# 5. Daily trajectory program — highest-priority new model direction

Detailed contract:

`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

## 5.1 Core question

> **Does the full trajectory observed up to today improve final-attendance MAE beyond the structural incumbent and sparse/fixed-horizon trajectory methods?**

Current models often know either selected horizons, the latest state, or a compressed curve representation.

The new model should explicitly distinguish events such as:

- same current inventory/demand level, but strong recent acceleration;
- same current level, but prolonged plateau;
- late inventory release;
- smooth steady pickup;
- unusually volatile trajectory.

A single current value cannot represent these behaviours.

## 5.2 Daily inference contract

For every eligible event and daily cutoff:

`as_of_at(P-N) = kickoff_at - N * 24h`

Initial target range:

`P-60 ... P-1`

At P-20, use only observations available by P-20.

At P-19, use the longer genuine prefix available by P-19.

Persist a new immutable forecast/attempt at each eligible cutoff.

Do **not** refit the same evaluation model every day.

---

# 6. First infrastructure deliverable: canonical daily trajectory dataset

Before arguing about model architecture, build the dataset correctly.

For every `(event, daily cutoff)` persist or materialize PIT-safe features including:

### Identity and lineage

- ticket event;
- club;
- kickoff;
- exact cutoff/as-of timestamp;
- latest visible source snapshot;
- source/capture lineage;
- snapshot staleness;
- dataset/code version.

### Current demand/inventory state

- inventory/demand proxy;
- proxy as share of verified capacity;
- first visible proxy;
- age of observed booking window;
- observation density;
- missingness/data-quality state.

### Trajectory dynamics

- 1d / 3d / 7d change;
- 1d / 3d / 7d velocity;
- acceleration;
- recent and longer slope;
- slope change;
- volatility;
- normalized position on the observed curve;
- similarity to completed prior PIT-safe curves.

### Structural anchor

- structural incumbent P10/P50/P90;
- incumbent source/family;
- verified stadium capacity;
- other explicitly PIT-safe context approved for the model version.

Missing data remain missing. Do not fabricate a P-37 value merely to obtain a complete daily sequence.

---

# 7. Second infrastructure deliverable: immutable daily forecast ledger

Every daily model attempt must be auditable even when no prediction can be produced.

Persist at minimum:

- event;
- daily horizon;
- exact as-of;
- prediction timestamp;
- model/precommit version;
- input/dataset manifest hash;
- observed prefix range;
- latest source snapshot lineage;
- incumbent forecast;
- challenger forecast;
- status/fail-closed reason;
- `target_values_used=false`;
- `production_change=false`.

After the event finishes and genuine attendance becomes available, score the already-persisted forecast. Never rebuild the historical prediction after seeing the target.

---

# 8. MAE must become a horizon curve

One overall MAE is not enough to understand whether the product is becoming useful earlier.

Required reporting includes:

| Horizon | Incumbent MAE | Challenger MAE | Delta MAE | Independent events | Clubs |
|---|---:|---:|---:|---:|---:|
| P-30 | | | | | |
| P-21 | | | | | |
| P-14 | | | | | |
| P-7 | | | | | |
| P-3 | | | | | |
| P-1 | | | | | |

Also report precommitted horizon bands such as long/medium/late windows where useful.

The strategic product question becomes:

> **How early before kickoff can Beyond achieve a useful level of forecast accuracy, and how quickly does accuracy improve as genuine demand evidence arrives?**

Daily rows from one event never count as independent events.

---

# 9. Model program: two lanes in parallel

## Lane A — simple trajectory models

Purpose:

- establish whether trajectory information itself contains incremental signal;
- create a hard-to-beat, low-variance benchmark;
- keep interpretation straightforward.

Start with residual learning over the structural incumbent:

`target = actual attendance - structural incumbent P50`

Candidate families should remain deliberately small:

1. Ridge / ElasticNet trajectory residual model;
2. restrained tree/boosting residual model with MAE-aligned objective where feasible;
3. nearest-trajectory / pickup residual method;
4. small fixed combinations if independently justified.

Lane A is the benchmark for sequence models.

## Lane B — high-risk sequence models

Decision: **start early rather than waiting for an ideal dataset**.

Purpose:

> test whether the ordered full trajectory contains signal that handcrafted slope/velocity/acceleration features fail to capture.

Initial architecture order:

1. small GRU;
2. small LSTM;
3. small temporal convolutional network (TCN);
4. compact attention/Transformer encoder only after the earlier models establish that sequence representation is promising.

Do not begin with a large Transformer/TFT.

Recommended formulation:

`observed trajectory prefix + structural prior/context -> residual correction / final attendance distribution`

Do not force the network to relearn the entire structural attendance problem from scratch.

---

# 10. Why it is rational to test sequence models with limited labels

The labeled-event sample will remain small for some time. Waiting for a textbook-sized dataset may delay useful learning by many months or years.

Therefore Beyond accepts **controlled research risk**.

However:

- 50 events with 40 daily prefixes are still 50 independent events, not 2,000 independent events;
- a deep model can memorize club/event patterns;
- training fit is not evidence;
- random-row cross-validation is especially dangerous here.

The sequence lane must therefore beat Lane A under identical event-grouped/PIT-safe evaluation and then survive prospective validation.

---

# 11. Use unlabeled trajectories through self-supervised learning

A major opportunity is that trajectory observations are more abundant than final attendance labels.

Research-only pretraining may use target-free tasks such as:

- predict the next genuine inventory/proxy observation from the observed prefix;
- predict future proxy change over a fixed short window;
- reconstruct masked *historical sequence inputs* within a training sequence under a chronology-safe design;
- learn representations of trajectory shape.

Then train a smaller attendance/residual head using genuinely labeled events.

Important distinction:

> **Self-supervised pretraining can increase representation learning data, but it does not increase the number of independent events in final attendance evaluation.**

All leakage rules still apply.

---

# 12. P9 remains valuable and must not be overwritten

P9 is not obsolete.

P9 answers a narrower, highly auditable question:

`booking-curve similarity -> prior residuals -> incumbent correction at T-48/T-24`

The daily trajectory program asks a different question:

`full observed prefix -> daily evolving residual forecast across many horizons`

Therefore:

- continue P9 v1/v2 exactly as precommitted;
- score them honestly;
- use their results as evidence about curve similarity and support;
- do not merge P9 and future trajectory learner evidence into one result.

---

# 13. Existing rejected lanes stay rejected

Do not reopen on the same outcomes without materially new information/mechanism:

- Live Ticketing challenger as previously implemented;
- Sporting Match Stakes candidate;
- timing context candidate;
- existing weather point-forecast mechanism;
- Hype/Attention 48h hypothesis;
- old estimator sweeps;
- any post-hoc tuning of frozen evidence.

A full daily trajectory model is a genuinely new representation and is therefore allowed despite earlier live-ticketing rejection.

---

# 14. Context features remain secondary to trajectory validation

P11 odds and other PIT-safe context may later complement a successful trajectory model, but do not start another broad feature tournament now.

First answer:

1. does daily trajectory add value?
2. does an explicit sequence representation add value beyond engineered trajectory features?
3. at which horizons is the gain meaningful?

Only then evaluate combinations with odds/context as separately versioned challengers.

---

# 15. Business minimum meaningful Delta MAE

The numerical threshold remains unresolved and must be derived independently of model results.

Do not call a tiny improvement robust merely because `Delta MAE < 0`.

Business work should connect forecast error reductions to decisions such as:

- staffing;
- security;
- catering;
- transport/logistics;
- marketing/ticketing intervention timing;
- other capacity/operations decisions.

Until this threshold is agreed, positive small-N experiments remain research evidence rather than production-grade proof.

---

# 16. Execution order

## Immediate — protect current evidence

1. Protect every genuine P9 v1/v2 T-48/T-24 window.
2. Protect Form5 prospective T-24 captures.
3. Score P7/P9 only after genuine outcomes.
4. Continue P11/P4a genuine accumulation.
5. Keep Long72 frozen and operationally healthy.

## Start now — trajectory infrastructure

6. Materialize the canonical daily trajectory dataset.
7. Create immutable daily forecast/attempt persistence.
8. Add horizon-wise MAE reporting.
9. Audit data density/missingness by event, club and horizon.

## Then — model research, in parallel

10. Precommit and run Lane A simple trajectory residual challenger.
11. Precommit and run a small Lane B sequence challenger under the same event-grouped folds.
12. Investigate target-free/self-supervised trajectory pretraining.
13. Begin prospective daily shadow inference before relevant outcomes are available.

## Only after evidence

14. Compare prospective horizon-wise and event-balanced Delta MAE.
15. Check downside and uncertainty.
16. Decide whether sequence modelling earns further complexity.
17. Only then consider richer context combinations or larger sequence architectures.
18. Production remains a separate reviewed decision.

---

# 17. Decision tree for the trajectory program

### Case A — Lane A improves MAE, Lane B does not

Use the simpler trajectory representation. Do not add deep-model complexity.

### Case B — both improve, Lane B materially beats Lane A

Continue sequence research and test whether the gain survives prospective evidence.

### Case C — both fail

Do not hyperparameter-search until something wins. Diagnose whether the problem is:

- inventory proxy quality;
- insufficient independent events;
- missing trajectory coverage;
- structural incumbent already captures most useful signal;
- mismatch between inventory proxy and actual attendance.

Then design one new hypothesis.

### Case D — historical/grouped result is strong but prospective result fails

Prospective evidence wins. Keep the research result documented, but do not promote.

---

# 18. Long-term product direction

Beyond should eventually present not just one final number, but an evolving forecast story:

`observed trajectory -> today/as-of -> predicted remaining trajectory -> final P10/P50/P90`

At each new day:

- the new genuine observation replaces yesterday's predicted next point;
- the remaining path is recalculated;
- the final attendance forecast is revised;
- the revision and its cause are auditable.

The dashboard must always distinguish:

- observed inventory/demand proxy;
- predicted future proxy trajectory;
- predicted final attendance;
- actual attendance after the event.

Inventory proxy must never be presented as confirmed paid ticket sales.

---

# 19. Agent rule

When choosing the next research task, ask in this order:

1. Does it protect an already-open prospective evidence window?
2. Does it improve PIT-safe daily trajectory evidence/infrastructure?
3. Does it test a precommitted trajectory hypothesis under event-safe validation?
4. Does it add genuinely new information not already rejected?
5. Is it more likely to reduce prospective MAE than the current alternatives?

Do not choose work because it is technologically interesting.

Choose work because it can produce honest evidence about lower future MAE.
