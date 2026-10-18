# Beyond Ticketing — Model Accuracy Development Instructions v2

Last updated: **2026-10-18**

Status: **CANONICAL DEVELOPMENT INSTRUCTION**

This file defines how Beyond forecasting development must be conducted from now on.

The immediate objective is not to move through workstreams quickly. The immediate objective is:

> **Reduce forecasting error as far as we can with honest, reproducible evidence before treating the model as mature.**

MAE reduction is the primary model-development KPI. Other metrics are required for safety and diagnosis, but no workstream should be considered complete only because one implementation idea failed.

---

## 1. Core architecture

Beyond forecasting should be developed as two connected layers.

### Layer 1 — Pre-Live Model v2

The strongest possible pre-live forecast combines:

- **a) historical demand data**;
- **b) current-season regime**;
- **c) match context**.

Conceptually:

`history + current-season regime + match context -> pre-live forecast`

This layer must be optimized first.

### Layer 2 — Continuous Live Updater v2

Live demand then updates the best available pre-live forecast.

Conceptually:

`pre-live forecast + live trajectory + inventory state + time-to-kickoff + reliability -> live delta / revised forecast`

The live layer should not be designed as an unrelated second forecast that competes with a weaker pre-live baseline. It should learn how much trustworthy live evidence should revise the best pre-live estimate.

Final concept:

`final_forecast(t) = pre_live_forecast(t) + reliability(t) * live_delta(t)`

Alternative formulations such as remaining-demand prediction or governed blending are allowed as challengers, but they must follow the same evidence rules.

---

## 2. Current status of a/b/c/d

### a) Historical data

Status: **MATURE INCUMBENT / NOT FULLY OPTIMIZED**.

The existing Structural Prior is the strongest current production component and must be preserved as incumbent until a challenger proves improvement.

However, historical-model tuning is no longer deferred automatically until after live work. It is part of the immediate Pre-Live v2 optimization pass.

### b) Current season

Status: **PARTIALLY TESTED / NOT EXHAUSTED**.

`Current Season Adjustment v1` tested one explicit post-model correction based on current-season level versus historical norm. It did not improve holdout MAE and must not be promoted.

That result means only:

> **that specific adjustment formulation is not proven.**

It does **not** mean the current-season workstream is complete.

The next b) work must test better representations of regime change, especially residual-based signals relative to the incumbent forecast.

### c) Match context

Status: **AUDITED + ONE CHALLENGER TESTED / NOT EXHAUSTED**.

The existing feature store already includes substantial PIT-safe context. `Future Fixture Context v1` tested one remaining hypothesis around future-home-fixture timing / attractiveness / cannibalization and did not improve holdout MAE.

That result means only:

> **that specific future-fixture formulation is not proven.**

It does **not** mean match context is complete.

Further context challengers are allowed where the data can be reconstructed point-in-time safely.

### d) Live demand

Status: **IMPORTANT, BUT NEW LIVE MODEL DEVELOPMENT FOLLOWS PRE-LIVE v2 OPTIMIZATION**.

Frozen C1 v8 stays frozen and continues prospective shadow collection in parallel.

New live work must be a separately governed challenger and must not silently retune frozen v8.

---

## 3. Required development order

The active accuracy roadmap is:

`a2 baseline optimization -> b2 current-season regime -> c2 match context -> freeze Pre-Live v2 -> d2 continuous live updater`

This replaces the simplified sequence:

`b -> c -> d -> tuning a`

because a stronger incumbent should be established before training later correction layers against it.

---

## 4. a2 — Historical baseline optimization

Goal:

> **Get the strongest possible PIT-safe pre-live baseline before adding new correction layers.**

Required experiment families:

### 4.1 Feature contribution / ablation

For every horizon separately:

- measure contribution of major feature groups;
- remove noisy or redundant groups only when holdout evidence supports removal;
- test interactions only when they are available at forecast time;
- preserve a complete feature-contract audit.

At minimum evaluate groups covering:

- home demand history;
- current-season demand features already inside Structural Prior;
- opponent demand history;
- pair history;
- sporting form;
- table state;
- calendar / timing;
- capacity-related normalization;
- rest / congestion;
- explicit importance interactions.

### 4.2 Season recency weighting

Test whether newer seasons should receive higher weight than older seasons.

Candidate weighting must be explicit and frozen before holdout scoring, for example:

- uniform;
- linear recency;
- exponential decay;
- bounded recent-season emphasis.

Do not tune weighting directly against final exposed holdouts repeatedly.

### 4.3 Model-family challengers

The current champions use ExtraTrees / GradientBoosting / HistGradientBoosting. These are incumbents, not assumptions.

Allowed challenger families include, where technically appropriate:

- CatBoost;
- LightGBM;
- XGBoost;
- regularized linear / GAM-style baselines;
- calibrated ensembles of independently validated candidates.

Every new dependency must be pinned in CI.

### 4.4 Horizon-specific optimization

T-30, T-14, T-7, T-3 and T-1 may need different:

- feature subsets;
- model families;
- regularization;
- recency weighting;
- calibration.

Do not force one configuration across all horizons only for implementation convenience.

### 4.5 Club calibration / hierarchy

Test whether systematic club-level residual patterns remain after Structural Prior.

Any calibration must be:

- PIT-safe;
- shrunk for low sample sizes;
- evaluated out-of-sample;
- prevented from memorizing clubs or seasons without generalization.

---

## 5. b2 — Current-season regime modeling

Goal:

> **Detect whether the current season is systematically running above or below what the incumbent model already expects.**

Do not repeat only the previous `current season mean vs historical norm` correction.

Priority challengers:

### 5.1 Residual regime index

For completed prior home matches in the same season, compute forecast residuals against the incumbent available at that historical as-of.

Candidate signals:

- mean residual;
- median residual;
- attendance ratio `actual / expected`;
- EWMA residual;
- rolling last 3 / 5 residuals;
- robust residual excluding obvious one-off extreme events.

This answers:

> Is this club currently selling / drawing materially above or below what our own model expected?

### 5.2 Hierarchical shrinkage

Current-season regime signals must shrink toward zero when evidence is limited.

Potential evidence hierarchy:

`club current season -> club historical residual behavior -> league current season -> zero`

No unrestricted correction from one or two matches.

### 5.3 Season-stage sensitivity

The same residual may have different reliability after:

- 2 home matches;
- 5 home matches;
- 10 home matches.

Reliability / shrinkage should reflect sample size.

### 5.4 Promotion condition

Current-season regime features should be promoted only if they improve out-of-sample MAE without unacceptable tail degradation.

A development-season win followed by holdout degradation is not sufficient.

---

## 6. c2 — Match-context modeling

Goal:

> **Explain why this specific match should differ from the club / season demand baseline.**

The existing PIT-safe context already includes opponent draw, pair history, PPG, GD/game, form, table position and past congestion. Do not add duplicate features without evidence.

Priority candidate gaps:

### 6.1 Match stakes / competition importance

Test PIT-safe formulations of:

- title-race relevance;
- European qualification relevance;
- relegation relevance;
- points-gap pressure;
- late-season importance interactions;
- must-win / direct-rival approximations.

### 6.2 Streak representation

Current `last-5` aggregates may not represent sequence shape.

Test bounded PIT-safe signals such as:

- winning streak length;
- unbeaten streak length;
- losing streak length;
- recent points acceleration / deceleration;
- home-specific sporting streak where justified.

### 6.3 Rivalry / derby / exceptional opponent draw

Where a reliable deterministic mapping exists, test:

- derby / rivalry flags;
- exceptional national draw;
- opponent demand percentile versus ordinary opposition.

Do not hand-label outcomes after seeing attendance.

### 6.4 Future fixture context

The existing Future Fixture Context v1 result is `NOT PROVEN`.

Do not keep retuning the same formulation against the same exposed reference seasons.

A materially different future-fixture hypothesis may be tested only with a clearly distinct contract and rationale.

### 6.5 Squad availability

Potentially useful:

- injuries;
- suspensions;
- expected XI;
- key-player availability.

But these may be added only if a reliable historical point-in-time source exists.

Do **not** backfill historical squad context using present-day or final-state sources.

---

## 7. Freeze Pre-Live v2 before new d2 training

After a2 + b2 + c2 challengers are evaluated, select the strongest reproducible pre-live configuration.

Freeze:

- feature contract;
- model family and hyperparameters;
- training protocol;
- weighting;
- calibration;
- data versions;
- artifact hashes;
- per-horizon model IDs.

Only then should the next learned live updater be trained against it.

Reason:

> The live layer should learn residual correction against the strongest stable pre-live baseline, not chase a moving incumbent.

Frozen C1 v8 remains available as a historical/prospective comparator and must not be rewritten into the new model silently.

---

## 8. d2 — Continuous Live Updater

Goal:

> **Make the forecast live continuously with demand evidence from the first usable sales observation until kickoff.**

### 8.1 Continuous time, not five model moments

T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints.

They are not the only times when the model may update.

The model should use continuous `time_to_kickoff` and meaningful snapshots such as T-32, T-25, T-20, T-11.5, T-4.2 etc.

### 8.2 Start from the earliest usable sales evidence

Collect inventory / coverage / price-area state from the first available sales moment.

Do not wait for T-30 if sales started earlier.

### 8.3 Predict correction or remaining demand

Preferred challenger formulations:

- `delta vs Pre-Live v2`;
- remaining-demand prediction;
- reliability-weighted blend between Pre-Live and Live estimate.

A second unrelated direct final-attendance forecast may still be benchmarked, but it is no longer the default architecture.

### 8.4 Reliability must be explicit

Live weight / correction strength may depend on:

- number of valid observations;
- observation span;
- time to kickoff;
- trajectory stability;
- velocity;
- acceleration;
- coverage completeness;
- release / inventory expansion events;
- sector consistency;
- price-area consistency;
- disagreement with Pre-Live;
- known data-quality warnings.

### 8.5 Inventory is a proxy

Public seat-map availability is not confirmed paid sales.

The model must distinguish as far as possible:

- demand movement;
- ticket releases;
- sector opening/closure;
- seat-map coverage changes;
- scraping/data anomalies.

### 8.6 Frozen v8 remains frozen

The current C1 v8 prospective package remains unchanged during prospective collection.

New d2 work is a new challenger with its own IDs, evidence and governance.

---

## 9. Accuracy scorecard — mandatory for every serious challenger

Primary metric:

- **MAE**.

Also report at minimum:

- median absolute error;
- bias;
- WAPE where meaningful;
- p90 absolute error or another explicit tail metric;
- worst-event degradation versus incumbent;
- percentage of events improved;
- result per horizon;
- result per season;
- result per club where sample size permits;
- event count and row count.

For live challengers additionally report:

- event-level MAE;
- latest-row MAE;
- trajectory-window MAE;
- revision frequency;
- maximum harmful revision;
- share of times the live layer changes the incumbent;
- performance conditional on observation count / time-to-kickoff where possible.

A lower global mean MAE with unacceptable tail risk must be called out explicitly.

---

## 10. CI/CD and reproducibility — NON-NEGOTIABLE

Model development must maintain full engineering accuracy.

**Do not skip details. Do not rely on undocumented notebook/manual results. Do not summarize away implementation facts needed to reproduce a result.**

Every material experiment must have:

1. committed source code;
2. an executable CI workflow;
3. pinned runtime dependencies;
4. syntax/import validation;
5. deterministic seeds where applicable;
6. explicit input data/artifact versions;
7. explicit train/development/holdout split;
8. point-in-time assertions;
9. incumbent benchmark assertions;
10. machine-readable result artifact, preferably JSON;
11. artifact name, run ID and hash where available;
12. concise human-readable result document committed to `ml/results/`;
13. explicit decision: promote / retain as challenger / reject / insufficient evidence;
14. update of canonical state documents in the same development cycle;
15. no production activation unless an explicit promotion step allows it.

### 10.1 Exact details that must never be omitted

For every challenger document the exact:

- feature definitions;
- source tables/files;
- as-of availability rules;
- missing-value behavior;
- imputation;
- normalization;
- caps / clipping;
- weights;
- shrinkage;
- thresholds;
- hyperparameters;
- random seed;
- train seasons/events;
- development seasons/events;
- holdout seasons/events;
- excluded rows/events and reason;
- model ID;
- feature-contract ID;
- data version;
- benchmark version;
- known evidence limitations.

If one of these changes, treat the resulting model as a new challenger version.

### 10.2 Benchmark integrity

The incumbent score used in an experiment must be generated or hard-asserted from the exact incumbent contract being compared.

Do not compare a challenger against a numerically similar but differently trained baseline.

### 10.3 No future leakage

Every feature must exist at the historical forecast timestamp.

The event is the independent evaluation unit.

Do not random-split snapshots from the same event across train and test.

Synthetic rows are train-only and never count as independent evidence.

### 10.4 No silent retuning

Do not change thresholds, features, hyperparameters or gates after looking at the same holdout and then describe the same holdout as unseen validation.

Exposed reference seasons remain useful regression evidence, but must be labeled honestly.

### 10.5 CI before claim

No benchmark result becomes canonical merely because it was observed locally or in an interactive session.

A canonical result requires an executable, reproducible run and persisted evidence.

### 10.6 CD / production safety

CI success does not mean automatic production promotion.

Production forecasting remains unchanged until explicit promotion criteria are met and the production artifact/version is intentionally changed.

---

## 11. Interpretation rule: hypothesis vs workstream

This rule is mandatory:

> **A failed challenger closes the challenger, not the whole workstream.**

Examples:

- `Current Season Adjustment v1 NOT PROVEN` does not mean b) is complete;
- `Future Fixture Context v1 NOT PROVEN` does not mean c) is complete;
- weak raw Live does not mean live evidence is useless;
- successful synthetic augmentation does not create new independent matches.

A workstream may be marked exhausted only when the remaining realistic hypotheses are explicitly listed and either tested, blocked by unavailable data, or deliberately deprioritized with rationale.

---

## 12. Current evidence boundary

Known current evidence remains:

- Structural Prior is the production incumbent;
- five horizons are executable;
- historical reference MAE is roughly 1.65k–1.89k depending on horizon/season;
- raw C1 Live has small-sample generalization problems;
- train-only synthetic trajectory augmentation improved raw Live in historical validation;
- frozen v8 safely fell back to Prior on the four current chronological forward events;
- there is still no confirmed prospective live MAE until prospective completed events are scored;
- production `live_adjustment = 0` remains unchanged unless explicitly promoted.

Do not present development replay as production accuracy.

---

## 13. Immediate work order

1. **a2 — Structural Prior / Pre-Live baseline optimization.**
2. **b2 — residual-based current-season regime challengers.**
3. **c2 — additional PIT-safe match-context challengers.**
4. **Freeze Pre-Live v2.**
5. **d2 — Continuous Live Updater against frozen Pre-Live v2.**
6. Continue frozen C1 v8 prospective scoring in parallel.
7. Do not promote production live adjustment without explicit evidence and governance.

---

## 14. One-line instruction for every new AI / engineering session

> **Do not optimize for finishing roadmap labels. Optimize for honest MAE reduction. Build the strongest reproducible Pre-Live v2 from history + current-season regime + match context, then build a continuous live updater against that frozen baseline. Keep CI/CD evidence complete, point-in-time safe and fully reproducible; never skip implementation details or treat one failed challenger as a completed workstream.**
