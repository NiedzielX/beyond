# Beyond Ticketing — Model Accuracy Development Instructions v2

Last updated: **2026-10-19**

Status: **CANONICAL DEVELOPMENT INSTRUCTION**

This file defines how Beyond forecasting development must be conducted.

The objective is not to move through workstreams quickly. The objective is:

> **Reduce forecasting error as far as we can with honest, reproducible evidence before treating the model as mature.**

MAE reduction is the primary model-development KPI. Other metrics are required for safety and diagnosis, but no workstream should ever be considered complete only because one implementation idea failed.

---

## 1. Core architecture

Beyond forecasting is developed as two connected layers.

### Layer 1 — Pre-Live Model v2

The strongest possible pre-live forecast combines:

- **a) historical demand data**;
- **b) current-season regime**;
- **c) match context where proven and historically PIT-safe**.

Conceptually:

`history + current-season regime + match context -> pre-live forecast`

For the current historical dataset, the sealed Pre-Live v2 candidate contains proven a2+b2 improvements and no additional frozen historical c2 extension.

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Canonical manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

### Layer 2 — Continuous Live Updater v2

Live demand updates the frozen pre-live anchor.

Conceptually:

`frozen pre-live forecast + live trajectory + inventory state + time-to-kickoff + reliability -> live delta / revised forecast`

The live layer must not be designed as an unrelated second forecast that competes with a weaker or moving pre-live baseline. It should learn how much trustworthy live evidence should revise the frozen Pre-Live v2 estimate.

Primary concept:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * live_delta(t)`

Alternative formulations such as remaining-demand prediction or governed blending are allowed as challengers, but they must follow the same evidence rules.

---

## 2. Current status of a2 / b2 / c2 / d2

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 ACTIVE`

### a2 — Historical data

Status: **CLOSED FOR CURRENT HISTORICAL DATA**.

The workstream was not closed after one challenger. It included:

- feature contribution / ablation;
- season-recency weighting;
- internal estimator-family challengers;
- external CatBoost / LightGBM / XGBoost challengers for T-7;
- horizon-specific optimization;
- T-7 robustness / fixed temporal audit;
- stronger multi-fold selection for unresolved horizons;
- persistent cross-season club calibration under two materially different fixed formulations.

Final historical base state:

- T-30: retained Structural Prior incumbent;
- T-14: retained Structural Prior incumbent;
- T-7: `hist31-leaf20-l2-1`;
- T-3: retained Structural Prior incumbent;
- T-1: retained Structural Prior incumbent.

T-7 fixed temporal audit improves MAE in **4/4 rolling folds**, mean **+104.66 MAE**.

Do not restart the same a2 grids on the same exposed historical references unless materially new data or a materially new hypothesis exists.

### b2 — Current season

Status: **CLOSED FOR CURRENT HISTORICAL DATA / FROZEN INTO PRE-LIVE V2**.

The earlier `Current Season Adjustment v1` was not sufficient. b2 continued with a materially different formulation based on same-season actual-vs-own-model residuals.

Critical PIT rule:

`prior kickoff + 3h <= current forecast as_of`

Frozen policies:

- T-30: `NO_ADJUSTMENT`;
- T-14: `NO_ADJUSTMENT`;
- T-7: `ewma50-resid-k6-cap05-min3`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

Non-zero policies activate only after at least **3 earlier completed same-season home matches**.

Final fixed four-fold temporal audit mean MAE gains:

- T-7: **+51.47**;
- T-3: **+70.44**;
- T-1: **+69.54**.

Known limitations remain explicit:

- max observed harmful event regression: **+2,760.55 seats**;
- event improvement rate is below 50% in several folds;
- club-level heterogeneity remains material;
- correction cap remains +/-5% verified capacity.

Do not retune b2 against the same exposed historical references.

### c2 — Historical match context

Status: **SUFFICIENTLY EVALUATED FOR CURRENT HISTORICAL DATA / NO HISTORICAL CONTEXT EXTENSION FROZEN**.

The workstream was not closed after Future Fixture Context v1 failed.

Historical c2 subsequently evaluated, incrementally over the frozen a2+b2 stack:

- sequence-aware winning / unbeaten / losing streaks;
- recent points acceleration / deceleration;
- home-specific sequence signals;
- current-table stakes / pressure;
- sequence + stakes interaction.

Result:

- T-30/T-14/T-7/T-3 selected `NO_CONTEXT` on development;
- T-1 selected `sequence_stakes` on development, but worsened both exposed references with mean reference delta **-36.97 MAE**.

Historical c2 contract is therefore:

`NO_CONTEXT_ALL_HORIZONS`

This does **not** mean context has no product value.

Forward-only context remains prospective research/shadow because complete multi-season historical PIT truth does not exist for:

- verified rivalry / derby mapping where historical availability is not versioned;
- injuries / suspensions / expected XI / key-player availability;
- media attention / mention acceleration;
- search / social / hype signals where valid PIT history does not exist.

Do not backfill these features from present-day or final-state sources.

### Pre-Live v2 historical candidate

Status: **FROZEN / SEALED / REPRODUCIBLE / NOT PRODUCTION**.

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Manifest SHA256:

`44c911d1ac8b1bf6870ed31e1a636b9b8374d8c8da2d57ba3b4fb5b4aaba4d3c`

Freeze gate:

- 5/5 unit tests PASS;
- frozen historical input hash PASS;
- **20/20 exact horizon-season MAE reproduction cells PASS at tolerance 1e-9**;
- freshly generated manifest vs committed manifest byte-for-byte comparison PASS;
- manifest SHA lock PASS.

Reference mean historical MAE across exposed 2024/25 + 2025/26:

- T-30: `1867.82`;
- T-14: `1809.45`;
- T-7: `1691.40`;
- T-3: `1682.63`;
- T-1: `1661.52`.

This is a historical candidate lineage boundary, not a production promotion.

### d2 — Live demand

Status: **ACTIVE NOW**.

New learned live development must use the immutable frozen Pre-Live v2 lineage as its anchor.

Frozen C1 v8 remains frozen and continues prospective shadow collection in parallel.

New d2 work is a separately governed challenger and must not silently retune or overwrite C1 v8.

---

## 3. Required development order

The canonical accuracy roadmap is now:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 ACTIVE`

Historical a2/b2/c2 may be reopened only if at least one of the following is true:

- materially new historical data becomes available;
- a materially new hypothesis exists that was not already represented by the completed work;
- genuine prospective evidence reveals a systematic failure mode that justifies a new challenger;
- previously unavailable PIT-safe context becomes historically reconstructable without leakage.

Do not reopen old grids simply because d2 is difficult or because an exposed holdout can be improved by post-hoc tuning.

---

## 4. a2 — Historical baseline optimization contract

Goal:

> **Get the strongest possible PIT-safe pre-live baseline before adding new correction layers.**

The required experiment families below define what a complete a2 investigation means. For the current dataset they have been executed sufficiently to close a2.

### 4.1 Feature contribution / ablation

For every horizon separately:

- measure contribution of major feature groups;
- remove noisy or redundant groups only when development/reference evidence supports removal;
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

Incumbent families are not assumptions.

Allowed challenger families include, where technically appropriate:

- HistGradientBoosting / GradientBoosting variants;
- ExtraTrees / RandomForest variants;
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

Current evidence does not support adding persistent cross-season club calibration to the frozen Pre-Live v2 stack.

---

## 5. b2 — Current-season regime modeling contract

Goal:

> **Detect whether the current season is systematically running above or below what the incumbent model already expects.**

Do not repeat only the previous `current season mean vs historical norm` correction.

### 5.1 Residual regime index

For completed prior home matches in the same season, compute forecast residuals against the correct incumbent available at that historical as-of.

Candidate signals may include:

- mean residual;
- median residual;
- attendance ratio `actual / expected`;
- EWMA residual;
- rolling last 3 / 5 residuals;
- robust residual excluding obvious one-off extreme events.

This answers:

> Is this club currently drawing materially above or below what our own model expected?

### 5.2 Hierarchical shrinkage

Current-season regime signals must shrink toward zero when evidence is limited.

Potential evidence hierarchy:

`club current season -> club historical residual behavior -> league current season -> zero`

No unrestricted correction from one or two matches.

### 5.3 Season-stage sensitivity

Reliability / shrinkage must reflect sample size.

Current frozen b2 evidence supports activation only after at least **3 earlier completed same-season home matches** for T-7/T-3/T-1.

### 5.4 Promotion condition

Current-season regime features should be retained only if they improve out-of-sample MAE without unacceptable unreported tail degradation.

A development-season win followed by holdout degradation is not sufficient.

Current b2 is frozen as a historical candidate layer, not promoted to production.

---

## 6. c2 — Match-context modeling contract

Goal:

> **Explain why this specific match should differ from the club / season demand baseline.**

The existing PIT-safe historical context already includes substantial information such as opponent draw, pair history, PPG, GD/game, form, table position and past congestion. Do not add duplicate features without evidence.

### 6.1 Match stakes / competition importance

PIT-safe formulations may include:

- title-race relevance;
- European qualification relevance;
- relegation relevance;
- points-gap pressure;
- late-season importance interactions;
- must-win / direct-rival approximations.

Current historical sequence/stakes extension did not prove incremental uplift over frozen a2+b2.

### 6.2 Streak representation

Potential bounded PIT-safe signals include:

- winning streak length;
- unbeaten streak length;
- losing streak length;
- recent points acceleration / deceleration;
- home-specific sporting streak where justified.

These were tested in Context Extension v2 and did not produce a historical extension to freeze.

### 6.3 Rivalry / derby / exceptional opponent draw

Where a reliable deterministic PIT mapping exists, test:

- derby / rivalry flags;
- exceptional national draw;
- opponent demand percentile versus ordinary opposition.

Do not hand-label outcomes after seeing attendance.

For the current historical dataset, forward rivalry research remains prospective/shadow rather than retrospectively backfilled.

### 6.4 Future fixture context

Future Fixture Context v1 is `NOT PROVEN`.

Do not keep retuning the same formulation against the same exposed reference seasons.

A materially different future-fixture hypothesis may be tested only with a clearly distinct contract, rationale and PIT-safe data history.

### 6.5 Squad availability

Potentially useful:

- injuries;
- suspensions;
- expected XI;
- key-player availability.

These may be added only if a reliable historical point-in-time source exists.

Do **not** backfill historical squad context using present-day or final-state sources.

---

## 7. Pre-Live v2 freeze contract

The strongest reproducible historical pre-live configuration must be frozen before new learned live training.

Freeze must persist:

- feature contract;
- model family and hyperparameters;
- training protocol;
- weighting;
- calibration;
- data versions;
- artifact hashes;
- per-horizon model IDs;
- exact benchmark cells;
- known limitations.

Current freeze:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Reason:

> The live layer must learn residual correction against the strongest stable pre-live baseline, not chase a moving incumbent.

Frozen C1 v8 remains available as a historical/prospective comparator and must not be rewritten into the new model silently.

If a2/b2/c2 source files or evidence change materially, a new explicit freeze version is required. Do not mutate the existing freeze lineage silently.

---

## 8. d2 — Continuous Live Updater

Goal:

> **Make the forecast live continuously with demand evidence from the first usable sales observation until kickoff.**

### 8.1 Continuous time, not five model moments

T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints.

They are not the only times when the model may update.

The model should use continuous `time_to_kickoff` and meaningful snapshots such as T-32, T-25, T-20, T-11.5, T-4.2 and any other valid observation time.

### 8.2 Start from the earliest usable sales evidence

Collect inventory / coverage / price-area state from the first available reliable sales moment.

Do not wait for T-30 if sales started earlier.

### 8.3 Predict correction or remaining demand

Preferred challenger formulations:

- `delta vs frozen Pre-Live v2`;
- capacity-normalized delta;
- remaining-demand prediction;
- reliability-weighted blend between Pre-Live and Live estimate.

A second unrelated direct final-attendance forecast may still be benchmarked, but it is no longer the default architecture.

Primary target direction:

`live_delta = actual_attendance - frozen_pre_live_v2_p50`

Final candidate concept:

`d2_p50 = clip(frozen_pre_live_v2_p50 + predicted_live_delta, 0, capacity)`

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

### 8.6 Event independence

Training rows may be `event x as_of_timestamp`, but the independent evaluation unit is the event.

Rules:

- all snapshots from one event stay in the same validation fold;
- no random snapshot-row train/test split;
- LOEO is primary while event N is small;
- use event-balanced weighting or equivalent so high-frequency events do not dominate;
- no future snapshot information may enter earlier rows.

### 8.7 Frozen v8 remains frozen

The current C1 v8 prospective package remains unchanged during prospective collection.

New d2 work is a new challenger with its own IDs, evidence and governance.

Do not silently tune C1 v8 thresholds or artifact while developing d2.

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

- `Current Season Adjustment v1 NOT PROVEN` did not complete b2;
- `Future Fixture Context v1 NOT PROVEN` did not complete c2;
- weak raw Live does not mean live evidence is useless;
- successful synthetic augmentation does not create new independent matches.

A workstream may be marked exhausted only when the remaining realistic hypotheses are explicitly listed and either:

- tested;
- blocked by unavailable PIT-safe data;
- deliberately deferred with rationale;
- or superseded by a stronger validated formulation.

That is the basis on which a2, b2 and historical c2 are now closed for the current dataset.

Closure is **dataset/hypothesis scoped**, not permanent. New data or genuinely new evidence may reopen them.

---

## 12. Current evidence boundary

Known current evidence:

- Structural Prior remains the production incumbent;
- five pre-live horizons are executable;
- frozen historical Pre-Live v2 candidate is sealed and reproducible;
- historical reference mean MAE is 1.66k–1.87k depending on horizon;
- b2 materially improves T-7/T-3/T-1 historical MAE under four-fold fixed audits;
- no historical c2 extension is frozen from the current dataset;
- raw C1 Live has small-sample generalization problems;
- train-only synthetic trajectory augmentation improved raw Live in historical validation;
- frozen v8 safely fell back to Prior on the four current chronological forward events;
- prospective independent completed-event evidence remains required for production live promotion;
- production `live_adjustment = 0` remains unchanged unless explicitly promoted.

Do not present development replay or exposed historical references as confirmed production/prospective accuracy.

---

## 13. Immediate work order

1. **d2 — Continuous Live Updater against frozen Pre-Live v2.**
2. Reproduce/use freeze ID `pre-live-v2-historical-candidate-2026-10-18-v1` as the primary anchor in d2 datasets and leaderboards.
3. Build a continuous event x as-of feature table with strict PIT semantics and event-level independence.
4. Run a small predeclared learned-model tournament rather than an open-ended model zoo.
5. Evaluate primarily by LOEO while independent completed live-event N remains small.
6. Report MAE, bias, tail, worst-event degradation, revision magnitude, event improvement rate and time-to-kickoff behavior.
7. Continue frozen C1 v8 prospective scoring in parallel without retuning it.
8. Continue forward-only rivalry / absence / hype context collection prospectively where valid.
9. Do not reopen a2/b2/c2 against the same exposed historical references without materially new data/hypothesis.
10. Do not promote production live adjustment without explicit prospective evidence and governance.

---

## 14. One-line instruction for every new AI / engineering session

> **Pre-Live v2 historical candidate is sealed. Do not restart historical a2/b2/c2 tuning on the same exposed data. Optimize honest MAE reduction by building d2 as a continuous PIT-safe live residual updater against freeze ID `pre-live-v2-historical-candidate-2026-10-18-v1`; keep C1 v8 frozen, keep CI/CD evidence complete, never skip implementation details, and reopen earlier workstreams only for materially new data or hypotheses.**
