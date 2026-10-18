# Beyond Ticketing — Product & ML North Star

Last updated: **2026-10-18**

## Single objective

Beyond is a **live demand decision system**.

For forecasting quality, the immediate objective is:

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Accuracy work must not be optimized for quickly completing roadmap labels.

## Forecasting architecture

### Pre-Live Model v2

`historical demand + current-season regime + match context -> strongest possible pre-live forecast`

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / revised forecast`

This architecture means:

- a/b/c are jointly responsible for the strongest possible pre-live estimate;
- d) should update that estimate continuously with live evidence;
- T-30/T-14/T-7/T-3/T-1 are evaluation checkpoints, not the only moments the forecast may change.

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

## Accuracy before complexity

A more complex model is valuable only if it produces reproducible out-of-sample improvement.

Every new feature/model family must justify itself through the standard scorecard.

Primary metric:

- MAE.

Required supporting evidence:

- median AE;
- bias;
- WAPE where meaningful;
- tail/worst-event degradation;
- event-improvement rate;
- horizon/season breakdown;
- club breakdown where sample size permits.

## Point-in-time integrity

Every feature must exist at forecast time.

No future leakage.

No random split of snapshots from the same event across train/test.

Synthetic rows are train-only and never independent real events.

Exposed historical reference seasons must be labeled honestly as exposed evidence.

## Engineering accuracy

Canonical model results require a complete reproducible chain:

`code -> CI -> artifact -> metrics -> result -> decision -> canonical docs`

Never omit details required to reproduce the result:

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
- limitations.

No undocumented local result becomes canonical.

CI success does not automatically promote production.

## Current production boundary

Structural Prior remains incumbent.

Production remains:

`live_adjustment = 0`

Frozen C1 v8 remains:

`EXPERIMENTAL_SHADOW`

Do not present replay/walk-forward results as confirmed prospective production accuracy.

## Product direction after forecast quality

Once forecasting quality is strong enough, Beyond should use the same live state to support decisions:

- event attendance outlook;
- sector under/over-performance;
- no-action projections;
- guarded price-area scenarios;
- human-reviewed interventions;
- eventually intervention outcome learning.

Public seat-map availability remains a **demand proxy, not confirmed paid sales**.

## Canonical instruction

Full model-development rules live in:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

Every new AI/engineering session must preserve this direction unless an explicit product decision changes it.
