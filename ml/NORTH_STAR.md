# Beyond Ticketing — Product & ML North Star

Last updated: **2026-10-18**

## Single objective

Build the best possible **live demand decision system** for football ticketing.

Beyond must not only forecast final attendance. It must tell the club:

1. where the event is likely to finish;
2. which sector / price area is underperforming or outperforming;
3. what is likely to remain publicly available if the current trajectory continues;
4. which commercial action is worth testing — especially price;
5. eventually, what happened after the club acted.

The forecasting layer remains the analytical foundation. Product value is created when that forecast becomes a useful decision before kickoff.

For forecasting quality, the immediate objective is:

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Accuracy work must not be optimized for quickly completing roadmap labels.

## Core product question

For every active event and every point in time before kickoff:

> **What is happening, why is it happening, where is the problem/opportunity, what happens if nothing changes, and what should the club test now?**

## Forecasting architecture

### Pre-Live Model v2

`historical demand + current-season regime + match context -> strongest possible pre-live forecast`

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / revised forecast`

This architecture means:

- a/b/c jointly build the strongest possible pre-live estimate;
- d) updates that estimate continuously with live evidence;
- T-30/T-14/T-7/T-3/T-1 are evaluation checkpoints, not the only moments the forecast may change.

## Model-development workstreams — canonical meaning

### a) Historical data — optimize the incumbent

Historical Structural Prior remains the production baseline until a challenger proves better.

Immediate focus:

- feature contribution / ablation;
- evidence-based noisy-feature removal;
- recency weighting;
- horizon-specific model-family challengers;
- residual / club calibration;
- validated ensembles where justified.

**Cel:** mocniejszy baseline bez komplikowania modelu bez evidence.

### b) Current season — model regime change

Current-season information already exists in Structural Prior, but the workstream is not exhausted.

`Current Season Adjustment v1` tested one specific post-model correction and was `NOT PROVEN`.

Next focus:

- residual-based current-season regime;
- actual-vs-expected demand ratio;
- EWMA / rolling residuals;
- sample-size-aware shrinkage;
- hierarchical regime signals where justified.

**Cel:** model szybciej reaguje na zmianę realiów w danym sezonie względem własnego expected demand.

### c) Match context — explain this fixture

Structural Prior already includes substantial PIT-safe opponent/form/table/rest context.

`Future Fixture Context v1` tested one specific future-fixture/cannibalization hypothesis and was `NOT PROVEN`.

Next focus:

- match stakes / title-Europe-relegation relevance;
- sequence-aware streaks;
- rivalry / derby / exceptional opponent draw where deterministic;
- squad availability only with reliable historical PIT data.

**Cel:** model rozumie, dlaczego konkretny mecz może różnić się od klubu/sezonu baseline.

### d) Live demand — continuous evidence

Interpret what is happening in ticketing now.

Focus after Pre-Live v2 freeze:

- inventory from the earliest sales moment;
- continuous time-to-kickoff;
- velocity;
- acceleration;
- sector / price-area movement;
- scarcity;
- release / replenishment activity;
- anomalies;
- source quality;
- delta / remaining-demand / reliability-weighted live correction;
- forecast update after every meaningful new snapshot.

**Cel:** mieć forecast, który żyje razem ze sprzedażą.

## Active model-development order

`a2 baseline optimization -> b2 current-season regime -> c2 match context -> freeze Pre-Live v2 -> d2 continuous live updater`

Frozen C1 v8 prospective collection continues in parallel.

## Interpretation principle

> **A failed challenger closes the challenger, not the whole workstream.**

Therefore:

- `Current Season Adjustment v1 NOT PROVEN` does not mean current-season modeling is complete;
- `Future Fixture Context v1 NOT PROVEN` does not mean match-context modeling is complete;
- weak raw Live does not mean live evidence is useless;
- synthetic data improving a model does not create new independent evidence.

A workstream may be called exhausted only when remaining realistic hypotheses are explicitly tested, blocked by missing data, or deliberately deprioritized with rationale.

## Live correction

Live correction remains part of **d) Live demand**.

New preferred concept:

`Final Forecast(t) = Pre-Live v2(t) + reliability(t) * live_delta(t)`

Alternative challengers such as remaining-demand prediction or reliability-weighted blending are allowed.

The next live layer should revise the strongest frozen pre-live baseline rather than relearn the whole attendance target from a tiny live sample by default.

Frozen C1 v8 remains unchanged as a prospective comparator.

## Sector / price-area decision layer

Current implemented direction:

`sector diagnosis -> no-action projection -> real price-area scenario -> guarded recommendation`

Public seat-map inventory is a **demand proxy, not confirmed paid sales**. Sector projections and event attendance must not be forced into a false 1:1 mapping.

## Dynamic pricing

Dynamic pricing decision support is a first-class product capability.

Current E0 supports assumption-based scenarios and guarded recommendations. It does **not** claim learned elasticity or causal uplift.

Automatic production price changes are not allowed:

`auto_price_change_allowed = false`

Mixed-price sectors must be split into real price areas instead of using a fake weighted executable price.

## Current evidence boundary

Historical Structural Prior is mature and benchmarked, but not declared fully optimized.

Historical reference MAE is roughly **1.65k–1.89k** depending on horizon/season.

C1 v8 is still:

`EXPERIMENTAL_SHADOW`

Current historical C1 evidence:

- raw Live LOEO: **2,929.3 MAE**;
- conservative train-only synthetic Live LOEO: **2,261.5 MAE**;
- stress train-only synthetic Live LOEO: **2,498.8 MAE**;
- four-event chronological Prior: **452.8 MAE**;
- four-event chronological raw Live: **2,103.7 MAE**;
- frozen v8 final: **452.8 MAE**, PRIOR in **16/16 rows**.

Interpretation:

- synthetic augmentation helps raw Live;
- raw Live is not a universal replacement for Prior;
- frozen v8 safely rejected weak Live on the current retrospective forward events;
- this does not prove prospective live accuracy or prove that v8 will switch correctly when Live is genuinely better.

Until independent prospective completed events are scored, there is no confirmed prospective live MAE.

Production remains:

`live_adjustment = 0`

Do not present replay/walk-forward as production accuracy.

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong pricing / demand intervention window;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final estimate / calibration.

Early actionability remains first-class even though live reasoning should become continuous between these checkpoints.

## Evaluation dimensions

### Forecast quality

Primary:

- MAE.

Required supporting dimensions:

- WAPE where meaningful;
- median absolute error;
- bias;
- p90/tail error;
- worst-event degradation;
- event-improvement rate;
- stability across clubs / seasons / horizons.

### Live demand quality

- forecast revision quality;
- incremental uplift over the correct frozen pre-live incumbent;
- first-detection lead time;
- stability under release / coverage changes;
- maximum harmful revision;
- correction/blend usage rate;
- quality conditional on observation count / time-to-kickoff where possible.

### Sector decision quality

- correctness of underperformance direction;
- sector no-action projection error;
- false alarm rate;
- time-to-action;
- price-area recommendation consistency.

### Pricing / intervention quality

Before learned pricing:

- scenario consistency;
- guardrail adherence;
- recommendation stability;
- explicit separation of simulated vs observed outcomes.

After real intervention evidence matures:

- incremental tickets;
- incremental revenue / contribution;
- ROI;
- price elasticity calibration;
- uplift uncertainty;
- recommendation expected value.

## Point-in-time integrity

Every feature must exist at forecast time.

No future leakage.

No random split of snapshots from the same event across train/test.

Synthetic rows are train-only and never independent real events.

Exposed historical reference seasons must be labeled honestly as exposed evidence.

## Engineering accuracy / CI/CD

Canonical model results require a complete reproducible chain:

`code -> tests/checks -> CI workflow -> artifact -> metrics -> result doc -> decision -> canonical docs update`

Never omit details required to reproduce a result:

- feature definitions;
- source data/version;
- as-of rules;
- missingness/imputation;
- normalization;
- weights/caps/shrinkage/thresholds;
- hyperparameters;
- random seed;
- train/dev/holdout sets;
- exclusions;
- model/feature-contract IDs;
- artifact/run IDs and hashes;
- evidence limitations.

No undocumented local result becomes canonical.

No silent retuning on the same holdout.

CI success does not automatically promote production.

Full rules:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

## Parallel product work

While Pre-Live v2 is being optimized:

- continue prospective C1 evidence without retuning frozen v8;
- improve scraping/data-quality infrastructure where useful;
- keep E0 pricing assumption-based and human-reviewed until real intervention evidence exists;
- collect intervention outcomes when they become real;
- calibrate probabilistic P10/P50/P90 only when evidence supports it.

## Product value statement

**Beyond powinien łączyć dane historyczne, aktualny sezon, context meczu i live demand, żeby forecast żył razem ze sprzedażą — a potem przekładać ten sygnał na bezpieczne decyzje sektorowe i cenowe przed kickoffem.**

## One-line instruction

> **Optimize for honest MAE reduction, not roadmap completion: build and freeze the strongest reproducible Pre-Live v2 from history + current-season regime + match context, then build the continuous live updater against it, while preserving complete CI/CD evidence and the broader sector/pricing decision product.**
