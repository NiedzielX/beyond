# Beyond Ticketing — Model Accuracy Development Instructions v3

Last updated: **2026-10-28**

Status: **CANONICAL DEVELOPMENT INSTRUCTION**

Aligned to:

- `ml/MAE_RESEARCH_ROADMAP_V5.md`;
- `ml/EXECUTION_PLAN_CURRENT.md`;
- `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`.

Supersedes `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md` for new work.

---

# 1. Objective

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons with honest, reproducible, point-in-time-safe evidence.**

Primary selector:

`Delta MAE = challenger MAE - incumbent MAE`

Desired:

`Delta MAE < 0`

Mandatory constraints:

- event/fixture independence;
- time-respecting validation;
- PIT safety;
- reproducibility;
- explicit evidence classes;
- immutable frozen packages;
- no silent production activation.

Production remains:

`live_adjustment = 0`

---

# 2. Priority rule

Before starting model work, ask:

1. Is there a genuine prospective window that must be protected now?
2. Is the requested work compatible with frozen experiment contracts?
3. Does it improve the canonical daily trajectory evidence/infrastructure?
4. Is it a precommitted hypothesis likely to reduce prospective MAE?
5. Is it genuinely new information/mechanism rather than reopening a rejected lane?

Protected evidence work has priority over convenience or novelty.

---

# 3. Independent unit

The independent evaluation unit is the **event/match**.

Never confuse row count with independent evidence.

Example:

`50 events x 40 daily trajectory prefixes = 2,000 rows`

still means:

`50 independent events`

Therefore:

- all prefixes/horizons from one event stay in the same fold;
- random snapshot/daily-row split is forbidden as headline evidence;
- uncertainty/bootstrap uses event blocks;
- readiness/promotion counts independent events, not trajectory rows.

---

# 4. PIT contract for daily trajectory models

For a prediction at cutoff `as_of_at`:

- every target snapshot must satisfy `captured_at <= as_of_at`;
- no future target trajectory point may enter an earlier cutoff;
- no target attendance may be visible;
- no future context/odds/lineup information may be visible unless genuinely known at cutoff;
- any normalization/scaler/statistics learned from data must be fitted within the training fold;
- missing observations remain missing unless a precommitted, PIT-safe imputation method is used.

Never manufacture trajectory history to create complete sequences.

---

# 5. Daily inference rule

Create immutable forecasts at eligible daily horizons using a frozen model version.

Allowed:

`frozen model + new genuine prefix -> new daily forecast`

Forbidden:

`new outcome -> retune same evaluation learner -> rewrite earlier/daily forecast`

Daily inference should produce an auditable history of forecast revisions.

---

# 6. Default modelling architecture

Prefer residual learning over the strongest valid structural incumbent.

Default target:

`attendance residual = actual attendance - structural incumbent P50`

Rationale:

- structural model already captures substantial attendance information;
- new trajectory models should prove incremental value;
- residual formulation reduces the amount of signal the new learner must discover;
- comparison against incumbent remains direct.

A from-scratch attendance model requires explicit justification and a separate version.

---

# 7. Lane A — simple trajectory benchmark

Every serious sequence experiment needs a simple trajectory comparator.

Candidate families:

- Ridge;
- ElasticNet;
- MAE/quantile-aligned linear models where feasible;
- restrained tree/boosting residual models;
- nearest-curve / pickup residual methods.

Typical PIT-safe trajectory features:

- current proxy level;
- proxy/capacity share;
- delta 1d/3d/7d;
- velocity 1d/3d/7d;
- acceleration;
- short/long slope;
- slope change;
- volatility;
- observation maturity/density;
- normalized curve position;
- curve-similarity statistics.

Keep candidate search small and hypothesis-driven.

---

# 8. Lane B — high-risk sequence research

Decision: sequence research may start before the labeled dataset is conventionally large.

Initial architecture order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact attention/Transformer encoder only after sequence value is demonstrated.

Early sequence models should use:

- low hidden dimension;
- few layers;
- dropout/weight decay;
- early stopping using event-grouped validation;
- deterministic seeds where possible;
- explicit capacity/parameter reporting.

Do not launch a broad architecture/hyperparameter tournament on the final evaluation cohort.

Sequence models must beat Lane A under the same folds/cutoffs before extra complexity is justified.

---

# 9. Self-supervised trajectory research

Allowed target-free pretraining tasks include:

- next genuine proxy observation prediction;
- short-window proxy-change prediction;
- chronology-safe representation learning;
- masked/reconstruction tasks that do not expose target future information at an earlier inference cutoff.

A later attendance/residual head may use learned representations.

Do not claim that self-supervised prefixes increase the number of independent attendance evaluation events.

---

# 10. Validation hierarchy

## Historical/grouped development

Use event-grouped, time-respecting folds.

Depending on the research question use:

- expanding/rolling event folds;
- LOEO diagnostic;
- LOCO diagnostic;
- season/time blocks where applicable.

Persist exact fold identities.

## Prospective validation

Required for promotion-quality evidence:

- precommit model/version/cutoffs;
- persist immutable predictions before outcomes;
- score only after genuine outcomes;
- never recompute historical predictions after target exposure.

Prospective evidence outranks favorable historical/grouped results when they disagree.

---

# 11. MAE reporting

Report both aggregate and horizon-wise performance.

Required core metrics:

- incumbent MAE;
- challenger MAE;
- absolute Delta MAE;
- relative Delta MAE;
- signed bias;
- median AE;
- P90 AE;
- event improvement rate;
- worst event degradation;
- per-club diagnostics;
- event-block uncertainty interval.

For daily trajectory models also report MAE at predefined horizons/bands, including at least representative points such as:

- P-30;
- P-21;
- P-14;
- P-7;
- P-3;
- P-1.

Do not optimize only one favorable horizon unless that horizon was precommitted as the primary decision point.

---

# 12. Forecast revision diagnostics

Daily inference should also measure:

- change in P50 since previous daily cutoff;
- forecast stability/volatility;
- whether new evidence moved the forecast in the correct direction after outcome is known;
- P10/P90 interval coverage where available.

These are diagnostics, not replacements for MAE.

---

# 13. Inventory semantics

Public inventory is a **demand proxy**, not confirmed paid ticket sales.

Never create attendance labels from:

- public inventory;
- capacity minus inventory;
- forecast values;
- hidden/unknown inventory.

Unknown inventory is not zero.

A model may learn from proxy trajectories only under explicit PIT-safe lineage.

---

# 14. Rejected-lane rule

Do not reopen the same mechanism on the same exposed outcomes merely with a different estimator/window.

Currently closed/rejected directions include the previously evaluated versions of:

- Live Ticketing challenger;
- Sporting Match Stakes;
- timing context;
- weather point forecast;
- Hype/Attention 48h;
- old broad estimator sweeps.

The daily trajectory program is allowed because it is a materially different representation/modeling contract.

---

# 15. Experiment/CI contract

Every material experiment must have:

1. explicit hypothesis;
2. source code;
3. executable tests/CI;
4. pinned runtime/dependencies where applicable;
5. deterministic seeds where applicable;
6. exact data lineage/manifests/hashes;
7. declared target/PIT semantics;
8. leakage assertions;
9. as-of/kickoff ordering assertions;
10. persisted train/evaluation identities;
11. frozen incumbent comparator;
12. machine-readable scorecard;
13. artifact/run/hash lineage;
14. human-readable result document;
15. explicit advance/retain/reject/insufficient decision;
16. canonical docs synchronized in the same evidence cycle;
17. no production activation without explicit reviewed promotion.

---

# 16. Evidence labels

Use explicit states such as:

- `historical_exposed_research`;
- `historical_forward_fold`;
- `delayed_label_precommitted`;
- `true_post_freeze_prospective`.

Do not describe already-inspected data as unseen.

---

# 17. Business meaning

A negative Delta MAE is necessary but may not be sufficient.

The numerical minimum meaningful Delta MAE remains to be derived independently from real club decisions.

Until then:

- tiny point improvements do not automatically mean robust success;
- small-N positive results remain research evidence;
- production promotion requires separate review.

---

# 18. Immediate development instruction

> **Protect P7/P9/Form5 prospective evidence while building the canonical daily trajectory dataset and immutable daily forecast ledger. Then compare a simple residual trajectory model against a small sequence residual model under identical event-grouped/PIT-safe folds. Start sequence research early, but do not relax evidence quality.**
