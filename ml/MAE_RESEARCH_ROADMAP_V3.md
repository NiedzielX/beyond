# Beyond Ticketing — MAE Research Roadmap v3

Last updated: **2026-10-21**

Status: **CANONICAL MAE-FIRST RESEARCH PLAN**

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at every decision-relevant horizon, while keeping every comparison point-in-time safe, reproducible and honest about evidence class.**

The target is not “build a more complex ML model”. The target is lower MAE on future matches.

Primary objective:

- lower event/fixture-balanced MAE versus the current incumbent at the same horizon.

Guardrails:

- signed bias;
- median absolute error;
- P90 absolute error;
- worst-event degradation;
- event-improvement rate;
- per-club and per-horizon stability;
- reproducible PIT-safe lineage.

Guardrails may block an unsafe model, but they must not silently replace MAE as the primary optimization objective.

---

## 2. Scientific rationale

This roadmap follows six principles from forecasting / ML literature.

### 2.1 Separate model development from final evidence

Repeated optimization against the same validation criterion can overfit model selection itself. Frozen packages and prospective evidence therefore remain immutable evaluation lanes, while new ideas are developed as new challenger versions.

Reference: Cawley & Talbot (2010), *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*, JMLR 11:2079–2107.

### 2.2 Respect time order

Random row splits are not headline evidence. Development comparisons must use event-safe and time-respecting evaluation. For the global historical model, use rolling / expanding season or fixture-origin evaluation where possible. For live trajectories, hold out complete events and add forward-event views.

Reference: Bergmeir, Hyndman & Koo (2018), *A note on the validity of cross-validation for evaluating autoregressive time series prediction*, Computational Statistics & Data Analysis 120:70–83.

### 2.3 Align training loss with the business metric

For point forecasts scored by MAE, conditional median / quantile-0.5 methods are directly aligned with absolute error. Squared-error models remain valid challengers, but MAE-native objectives must be first-class candidates.

Reference: Koenker & Hallock (2001), *Quantile Regression*, Journal of Economic Perspectives 15(4):143–156.

### 2.4 Combine genuinely different forecasts

Forecast combination can reduce error when component models carry complementary information. Test simple and regularized combinations before assuming a single champion must dominate.

References: Bates & Granger (1969), *The Combination of Forecasts*; Makridakis, Spiliotis & Assimakopoulos (2020), *The M4 Competition: 100,000 time series and 61 forecasting methods*.

### 2.5 Prefer more predictive information over decorative complexity

The existing v2.1 ablation already supports this: attendance history, seasonality, sporting state and opponent context matter. New feature families must earn inclusion through incremental out-of-sample MAE.

### 2.6 Pool information across clubs, but evaluate club stability

Beyond already has a global Ekstraklasa model. Keep exploiting pooled learning, while checking whether improvements generalize across clubs rather than coming from one large club or one season.

Reference: Montero-Manso & Hyndman (2021), *Principles and algorithms for forecasting groups of time series: Locality and globality*, International Journal of Forecasting 37(4):1632–1653.

---

## 3. Current baselines that must not be confused

### Historical / structural baseline

Current historical research champion family:

- **Global Model v2.1**;
- 1,530 Ekstraklasa matches across five complete seasons;
- 7,650 PIT feature snapshots across T-30/T-14/T-7/T-3/T-1;
- residual architecture: club-history baseline + global learned correction;
- 2024/25 and 2025/26 later-season results are already exposed historical evidence.

Do not treat those holdouts as unseen again for new challenger selection.

### Frozen final24 live package

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

This remains immutable and continues prospective validation.

### Frozen long72 live package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Development evidence:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- historical uplift `+694.51 / +18.73%`.

This package is also immutable. It collects prospective evidence; it is not the end of R&D.

---

## 4. Two-lane operating model

### Lane A — Evidence / validation

Purpose: estimate whether frozen packages work on genuinely future data.

Keep running without retuning:

1. final24 prospective scoring;
2. long72 forecast materialization before labels;
3. append-only outcome join after final attendance exists;
4. aggregate event-balanced MAE and band MAE;
5. bias / tail / event-improvement diagnostics;
6. explicit evidence class: historical-exposed, delayed-label, true post-freeze prospective.

**Lane A protects truth. It does not block Lane B.**

### Lane B — MAE R&D

Purpose: build challengers that can beat current incumbents on future fixtures.

Every material change receives a new challenger/version ID. Frozen packages are never mutated.

---

## 5. Priority order for MAE R&D

### P0 — finish immutable prospective plumbing

Implement long72 two-phase evidence capture:

1. materialize forecast before final attendance is available;
2. store anchor, raw inventory forecast, P2 forecast, reliability, event/as-of lineage, code/package hashes;
3. later attach outcome without recomputing the forecast;
4. update append-only scorecard.

This is required evidence infrastructure, not a reason to pause model research.

### P1 — make forward / rolling validation canonical for challengers

For historical/global challengers:

- keep season-blocked evaluation;
- add rolling / expanding-origin folds;
- never use future-season rows to train an earlier-season forecast;
- report results per fold, per horizon and aggregate;
- mark 2024/25 and 2025/26 as exposed historical evidence for all future iterations because they have already influenced research decisions.

For live-ticket challengers:

- retain complete-event LOEO diagnostics;
- add forward-event evaluation ordered by kickoff date;
- no random snapshot split as headline evidence.

Selection rule:

> A challenger should not advance only because it wins one exposed aggregate. It should show lower MAE across time-respecting views or provide a strong predeclared reason for a targeted horizon.

### P2 — MAE-native challenger tournament

Keep the existing strong residual architecture and test loss functions aligned with MAE.

Minimum challenger set per relevant horizon:

- current HistGradientBoosting/XGBoost incumbent;
- LAD / median regression where practical;
- quantile regression with `q=0.50`;
- tree boosting with absolute-error / quantile objective;
- robust residual linear model;
- simple inventory rule for live horizons;
- no-change / anchor control.

Do not expand hyperparameter search indiscriminately. Small, hypothesis-driven tournaments are preferred because model-selection overfitting is itself a risk.

### P3 — incremental context features over Global Model v2.1

Sporting context is already part of v2.1 and has positive ablation signal. Next context research must focus on genuinely new PIT-safe information.

Priority feature families:

1. **fixture substitution / cannibalization**
   - days to next home match;
   - next-home opponent attractiveness;
   - next-home competition/importance;
   - fixture density 7/14/30d;
   - previous-home proximity;
2. **availability / squad context**
   - verified absences known at `as_of_at`;
   - important-player availability where source history is reconstructable;
3. **match importance / rivalry**
   - predeclared rivalry/derby flag;
   - relegation/title/european-stakes state known at `as_of_at`;
4. **weather**
   - forecast available at the forecast origin, never realized future weather;
5. **hype / attention**
   - PIT-safe search/media/social measures only.

Every family requires ablation against the same incumbent and the same temporal folds.

### P4 — forecast combination / stacking

Do not assume the best single model is optimal.

Build component forecasts from materially different information sources:

- Global Model v2.1 structural forecast;
- MAE-native residual challenger;
- context challenger;
- live inventory / long72 signal;
- final24 live signal where in scope.

Test in this order:

1. simple mean;
2. median;
3. fixed convex weights;
4. MAE-optimized convex weights learned only inside development folds;
5. regularized stacker only if simpler combinations fail.

Combination weights must be learned inside each training fold. No weight may be selected on the final evaluation fold.

### P5 — live-ticket signal as incremental correction over the strong structural model

Do not evaluate live ticketing primarily against an obsolete weak baseline.

The scientific question becomes:

> **Does PIT live inventory reduce MAE after Global Model v2.1 / the current structural forecast has already explained historical demand?**

Model the live signal primarily as a residual correction with reliability/shrinkage, and compare:

- structural only;
- structural + raw live correction;
- structural + reliability-gated live correction;
- structural + context + live ensemble.

### P6 — uncertainty around MAE improvement

For every serious challenger report uncertainty around `ΔMAE`, not only a point estimate.

Preferred unit: match/event, not trajectory row.

Use event/fixture-block bootstrap or an equivalent resampling method that preserves event independence. Report at least:

- challenger MAE;
- incumbent MAE;
- `ΔMAE`;
- relative `ΔMAE`;
- interval for `ΔMAE`;
- event-improvement rate;
- per-club distribution.

Do not interpret a positive historical point estimate on a very small live sample as precise evidence.

### P7 — 72–168h expansion

Current coverage remains `8` independent events above 72h against the predeclared start floor `N>=9`.

When `N>=9`:

1. freeze exact eligible event/as-of identities before opening model results;
2. define the PIT-safe T-7 anchor transition;
3. start with simple / strongly regularized challengers;
4. include MAE-native loss candidates;
5. validate with event-safe + forward-event views;
6. keep this a separate challenger family; do not mutate long72 P2.

`N=9` is a start threshold, not proof of adequacy.

### P8 — club calibration / global-model stability

The global model already pools all Ekstraklasa clubs. Next research should ask whether a small club-specific calibration improves MAE without destroying pooled generalization.

Candidates:

- global model only;
- global + shrinkage club residual;
- global + home-club calibration;
- global + opponent calibration.

Only advance if improvement survives rolling-season evaluation and is not concentrated in one club.

---

## 6. Evaluation contract

For every new challenger, report:

### Primary

- event/fixture-balanced MAE by horizon;
- aggregate MAE only with an explicit weighting rule.

### Required secondary diagnostics

- median AE;
- P90 AE;
- signed bias;
- worst-event degradation;
- event-improvement rate;
- club-level MAE deltas;
- season/fold MAE deltas;
- correction magnitude where applicable.

### Evidence labels

Use only:

- `historical_exposed_research`;
- `historical_forward_fold`;
- `delayed_label_precommitted`;
- `true_post_freeze_prospective`.

Never describe previously inspected historical seasons as unseen.

---

## 7. Challenger promotion logic

A challenger may become the new **research champion** when:

1. its selection protocol was declared before looking at the final comparison;
2. PIT safety passes;
3. it lowers MAE on the primary time-respecting development view;
4. improvement is not explained by one event/club/fold only;
5. bias/tail behavior is acceptable;
6. all artifacts and hashes are reproducible.

A **production** promotion remains separate and requires genuine future evidence plus explicit review.

Historical research-champion status never implies production activation.

---

## 8. Immediate execution sequence

Work in parallel; do not wait for future matches before starting R&D.

### Now

1. finish long72 immutable forecast materialization + append-only scorer;
2. implement canonical forward/rolling validation utilities;
3. run MAE-native residual tournament on the global historical benchmark;
4. build `ΔMAE` uncertainty reporting by event/fixture block;
5. define and materialize PIT-safe fixture-cannibalization features;
6. rerun controlled context ablations;
7. build simple forecast-combination tournament;
8. measure live-ticket incremental value over the strongest structural/global forecast;
9. continue long168 data accumulation and trigger the 72–168h experiment at `N>=9`;
10. keep 2026/27 fixtures as genuine prospective evidence for newly frozen challengers.

### Do not spend cycles on

- retuning frozen final24 or long72 P2 on their development events;
- cosmetic v2/v3 final24 retraining;
- broad blind hyperparameter sweeps;
- complexity without incremental information;
- treating one historical best score as production evidence;
- waiting idly for prospective labels.

---

## 9. Implementation / CI rule

Every material experiment follows:

`hypothesis -> PIT contract -> code -> tests -> forward/event-safe evaluation -> artifact -> hashes -> result doc -> decision -> canonical docs`

Required in CI:

- deterministic seeds where applicable;
- pinned dependencies;
- input/data hashes;
- target leakage assertions;
- as-of / kickoff ordering assertions;
- no target-event self-history leakage;
- fold boundaries persisted;
- machine-readable scorecard;
- human-readable result;
- explicit advance / retain / reject / insufficient decision.

---

## 10. Literature anchors

1. Cawley, G. C. & Talbot, N. L. C. (2010). *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*. JMLR, 11, 2079–2107. https://www.jmlr.org/papers/v11/cawley10a.html
2. Bergmeir, C., Hyndman, R. J. & Koo, B. (2018). *A note on the validity of cross-validation for evaluating autoregressive time series prediction*. Computational Statistics & Data Analysis, 120, 70–83. https://doi.org/10.1016/j.csda.2017.11.003
3. Koenker, R. & Hallock, K. F. (2001). *Quantile Regression*. Journal of Economic Perspectives, 15(4), 143–156. https://doi.org/10.1257/jep.15.4.143
4. Bates, J. M. & Granger, C. W. J. (1969). *The Combination of Forecasts*. Journal of the Operational Research Society, 20(4), 451–468. https://doi.org/10.1057/jors.1969.103
5. Makridakis, S., Spiliotis, E. & Assimakopoulos, V. (2020). *The M4 Competition: 100,000 time series and 61 forecasting methods*. International Journal of Forecasting, 36(1), 54–74. https://doi.org/10.1016/j.ijforecast.2019.04.014
6. Montero-Manso, P. & Hyndman, R. J. (2021). *Principles and algorithms for forecasting groups of time series: Locality and globality*. International Journal of Forecasting, 37(4), 1632–1653. https://doi.org/10.1016/j.ijforecast.2021.03.004

---

## One-line handoff

> **Protect frozen packages as evidence, but spend R&D capacity on new MAE-first challengers: time-respecting validation, MAE-native losses, new PIT-safe context, forecast combinations, and incremental live corrections over the strongest global structural model.**
