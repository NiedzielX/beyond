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

### Layer 1 — Frozen Pre-Live Model v2

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

### Layer 2 — d2 Continuous Live Updater

Stage-1 research lead:

`ridge-a10`

Current architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

The live layer must not be designed as an unrelated second forecast that competes with a weaker or moving pre-live baseline. It should learn how much trustworthy live evidence should revise the frozen Pre-Live v2 estimate.

Alternative formulations such as remaining-demand prediction or governed blending remain valid future challenger families, but they must follow the same evidence rules and must not be introduced as post-hoc rescue against exposed holdouts.

---

## 2. Current status of a2 / b2 / c2 / d2

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> d2 Stage 1 DONE -> d2 Stage 2 ACTIVE`

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

Historical c2 contract:

`NO_CONTEXT_ALL_HORIZONS`

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

Reference mean historical MAE across exposed 2024/25 + 2025/26:

- T-30: `1867.82`;
- T-14: `1809.45`;
- T-7: `1691.40`;
- T-3: `1682.63`;
- T-1: `1661.52`.

Freeze gate:

- 5/5 unit tests PASS;
- frozen historical input hash PASS;
- **20/20 exact horizon-season MAE reproduction cells PASS at tolerance 1e-9**;
- freshly generated manifest vs committed manifest byte-for-byte comparison PASS;
- manifest SHA lock PASS.

### d2 Stage 0

Status:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

Development lineage:

- 9 events;
- 30 final-24h rows;
- exact Frozen-v2 anchor.

### d2 Stage 1

Status:

`COMPLETED / ridge-a10 RESEARCH LEAD`

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Development metrics:

- Frozen-v2 latest MAE: `4128.01`;
- Ridge latest MAE: **`3320.39`**;
- latest improvement: **`+807.62 seats / 19.56%`**;
- Frozen-v2 event-balanced window MAE: `4128.01`;
- Ridge window MAE: **`3619.19`**;
- window improvement: **`+508.83 seats / 12.33%`**;
- latest event improvement rate: **`66.7%`**;
- worst latest-event degradation: **`+4326.90 seats`**.

### d2 Stage 2

Status:

`ACTIVE — RELIABILITY / TAIL-RISK GATING`

Canonical contract:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

Stage 2 freezes the Stage-1 Ridge expert and governs its correction. It is not an open-ended model-family tournament.

---

## 3. Required development order and reopening rule

Current order:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> Stage 0 DONE -> Stage 1 DONE -> Stage 2 ACTIVE -> event 5 HOLDOUT -> prospective accumulation -> promotion decision`

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

### 6.4 Future fixture context

Future Fixture Context v1 is `NOT PROVEN`.

Do not keep retuning the same formulation against the same exposed reference seasons.

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

The strongest reproducible historical pre-live configuration must be frozen before learned live training.

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

The live layer must learn correction against this stable baseline, not chase a moving incumbent.

If a2/b2/c2 source files or evidence change materially, a new explicit freeze version is required.

---

## 8. d2 — Continuous Live Updater general contract

Goal:

> **Make the forecast live continuously with demand evidence from the first usable sales observation until kickoff.**

### 8.1 Continuous time, not five model moments

T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints.

They are not the only times when the model may update.

The model should use continuous `time_to_kickoff` and meaningful snapshots such as T-32, T-25, T-20, T-11.5, T-4.2 and any other valid observation time.

### 8.2 Start from the earliest usable sales evidence

Collect inventory / coverage / price-area state from the first available reliable sales moment.

Do not wait for T-30 if sales started earlier.

### 8.3 Prediction formulations

Allowed challenger formulations include:

- delta vs Frozen Pre-Live v2;
- capacity-normalized delta;
- remaining-demand prediction;
- reliability-weighted blend between Pre-Live and live estimate.

A second unrelated direct final-attendance forecast may be benchmarked, but it is not the default architecture.

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

### 8.7 Frozen C1 v8 remains frozen

The current C1 v8 prospective package remains unchanged during d2 development.

New d2 work has its own IDs, evidence and governance.

Do not silently tune C1 v8 thresholds or artifact while developing d2.

---

## 9. d2 Stage-1 frozen expert contract

Stage-1 research lead:

`ridge-a10`

Frozen contract:

- target = `target_live_delta_occupancy`;
- `Ridge(alpha=10.0)`;
- median imputation within training fold;
- missing indicators;
- standardization;
- event-balanced sample weights;
- event-level LOEO;
- final raw live correction clipped to +/-10pp occupancy.

Do not retune these during Stage 2.

Changing alpha, feature contract, target, preprocessing or correction cap creates a new model challenger/version outside Stage-2 policy selection.

---

## 10. Time-Series Foundation Model boundary

Stage 1 tested zero-shot:

- `amazon/chronos-2`;
- `amazon/chronos-bolt-small`.

Both were used only to forecast causal public `available_share_of_capacity` trajectory.

Final attendance / residual labels never entered the TSFM context.

Results:

- plain Ridge latest MAE: `3320.39`;
- Ridge + Chronos-2: `3428.25`;
- Ridge + Chronos-Bolt-small: `3428.08`.

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same frozen 9-event development lineage.

Reopen the TSFM family only with materially more independent trajectory events or a materially new predeclared hypothesis.

---

## 11. d2 Stage-2 reliability / tail-risk contract

Canonical plan:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

Goal:

> **Preserve a meaningful share of Ridge's MAE uplift while materially reducing the +4326.90-seat worst-event degradation.**

Preferred architecture:

`final = frozen_v2 + reliability * ridge_delta`

where:

`0 <= reliability <= 1`

### 11.1 Immutable development boundary

Events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Rows:

`30`

Independent unit:

`event`

Primary validation:

`LOEO`

### 11.2 Allowed reliability signals

Only PIT-safe evidence available at exact forecast time, including:

- observation count;
- observation span;
- time to kickoff;
- trajectory stability / volatility;
- velocity;
- acceleration;
- disagreement between Ridge and Frozen v2;
- absolute proposed correction size;
- release/replenishment flag;
- coverage-change flag;
- unexplained inventory increase flag;
- data-gap flag;
- signal/feature-quality state;
- sector coverage quality where already available PIT-safe.

### 11.3 Compact predeclared policy family

At minimum compare:

- `P0` Frozen-v2 only;
- `P1` raw Ridge;
- `P2` observation-maturity gating;
- `P3` disagreement/correction-magnitude shrinkage;
- `P4` data-quality gating;
- `P5` compact combined reliability policy.

Do not create a large threshold zoo.

### 11.4 Advancement criteria

A Stage-2 policy may advance only if it:

- improves latest-row MAE vs Frozen v2;
- improves event-balanced window MAE vs Frozen v2;
- retains meaningful raw-Ridge uplift;
- materially reduces raw-Ridge worst-event degradation;
- does not introduce unacceptable bias;
- remains stable under event-level LOEO;
- is fully versioned/reproducible;
- is selected before the reserved holdout is opened.

If none passes, retain Ridge as research lead but do not promote it.

---

## 12. Reserved chronological holdout rule

Reserved event:

- event ID `5`;
- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 final-24h live rows.

This event was deliberately excluded from Stage-1 selection.

Mandatory rule:

> **Do not use event 5 to select Stage-2 features, thresholds, weights or policy. Freeze Stage 2 first. Then score event 5 exactly once.**

After freeze compare:

1. Frozen Pre-Live v2;
2. raw frozen Ridge;
3. frozen Stage-2 governed Ridge;
4. frozen C1 v8 where contract-compatible.

No retuning after opening the holdout.

A holdout validates a frozen decision; it does not become tuning data retroactively.

---

## 13. Accuracy scorecard — mandatory for every serious challenger

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

For Stage 2 additionally report:

- retained share of raw Ridge uplift;
- reduction in worst-event degradation versus raw Ridge.

A lower global mean MAE with unacceptable tail risk must be called out explicitly.

---

## 14. CI/CD and reproducibility — NON-NEGOTIABLE

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

### 14.1 Exact details that must never be omitted

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
- evidence limitations.

If one of these changes, treat the resulting model as a new challenger version.

### 14.2 Benchmark integrity

The incumbent score used in an experiment must be generated or hard-asserted from the exact incumbent contract being compared.

Do not compare a challenger against a numerically similar but differently trained baseline.

### 14.3 No future leakage

Every feature must exist at the historical forecast timestamp.

The event is the independent evaluation unit.

Do not random-split snapshots from the same event across train and test.

Synthetic rows are train-only and never count as independent evidence.

### 14.4 No silent retuning

Do not change thresholds, features, hyperparameters or gates after looking at the same holdout and then describe the same holdout as unseen validation.

Exposed evidence remains useful regression evidence, but must be labeled honestly.

Event 5 must not be used for Stage-2 selection.

Future completed events remain prospective scoring evidence until a separately versioned retraining cycle is explicitly declared.

### 14.5 CI before claim

No benchmark result becomes canonical merely because it was observed locally or in an interactive session.

A canonical result requires an executable, reproducible run and persisted evidence.

### 14.6 CD / production safety

CI success does not mean automatic production promotion.

Production forecasting remains unchanged until explicit promotion criteria are met and the production artifact/version is intentionally changed.

---

## 15. Interpretation rule: hypothesis vs workstream

Mandatory:

> **A failed challenger closes the challenger, not the whole workstream.**

Examples:

- `Current Season Adjustment v1 NOT PROVEN` did not complete b2;
- `Future Fixture Context v1 NOT PROVEN` did not complete c2;
- weak raw Live did not mean live evidence was useless;
- successful synthetic augmentation did not create new independent matches;
- Chronos losing to Ridge does not close d2;
- one good holdout does not prove production readiness;
- one bad holdout does not automatically invalidate the entire live workstream.

A workstream may be marked exhausted only when remaining realistic hypotheses are explicitly tested, blocked, deferred with rationale or superseded by a stronger validated formulation.

Closure is dataset/hypothesis scoped, not permanent.

---

## 16. Current evidence boundary

Known current evidence:

- Structural Prior remains production incumbent;
- frozen historical Pre-Live v2 is sealed and reproducible;
- b2 improves T-7/T-3/T-1 historical MAE under fixed four-fold audits;
- no historical c2 extension is frozen;
- frozen C1 v8 remains experimental shadow;
- Stage-0 exact Frozen-v2 live replay is reproducible;
- Stage-1 Ridge materially improves average live development MAE;
- raw Ridge still has material tail risk;
- Stage-1 Chronos/Bolt features do not improve Ridge;
- event 5 is reserved outside model/policy selection;
- genuinely prospective completed-event evidence remains required for production promotion;
- production `live_adjustment = 0` remains unchanged.

Do not present development LOEO as confirmed production/prospective accuracy.

---

## 17. Immediate work order

1. **Freeze `ridge-a10` exactly as selected in Stage 1.**
2. Build Stage-2 reliability/tail-risk policies only on the original 9-event/30-row development lineage.
3. Keep the Stage-2 policy family compact: P0-P5 from `ml/D2_STAGE2_RELIABILITY_GATING_V1.md`.
4. Select using both MAE uplift and tail-risk reduction, not mean MAE alone.
5. Persist exact policy code, tests, CI, JSON evidence, hashes and result doc.
6. Freeze the selected Stage-2 policy before opening event 5.
7. Score Lech–Korona event 5 once against Frozen v2, raw Ridge, governed Ridge and frozen C1 v8 where compatible.
8. Do not retune after opening event 5.
9. Continue append-only prospective scoring on later completed events.
10. Keep C1 v8, Pre-Live v2 and production unchanged unless a separate explicit promotion/version process occurs.

---

## 18. One-line instruction for every new AI / engineering session

> **Pre-Live v2 and Stage-1 `ridge-a10` are frozen research components. Build d2 Stage-2 reliability/tail-risk governance only on the original 9-event/30-row development lineage; do not use Lech–Korona event 5 for tuning. Freeze Stage 2 first, score event 5 once as chronological holdout, keep prospective evidence append-only, and keep production/C1 v8 unchanged.**
