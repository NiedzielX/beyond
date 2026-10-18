# Beyond Ticketing — Demand Forecast Development Plan v2

Last updated: **2026-10-18**

This is the current development plan for improving attendance / demand forecasting quality.

The order is intentional: first measure the current model honestly, then improve the strongest missing signal layers. Do not rebuild the whole stack before proving where the error comes from.

## 1. Validate the current model first

Before adding more features, establish how good the current live model really is on matches it did not see during training or tuning.

### Development

- run **Leave-One-Event-Out** on completed events with usable live history;
- for each held-out event, train/tune without that event;
- reconstruct historical T-7 / T-3 / T-1 states using only data that existed at that moment;
- compare on the same event/horizon pairs:
  - Structural Prior;
  - Live expert / C1;
  - final selection policy;
- calculate MAE, bias and per-event degradation;
- run a second **chronological walk-forward** test;
- report event count separately from snapshot-row count.

### Goal

Answer one question honestly:

> Is the current live model actually closer to ~2k, ~3k or worse on unseen events?

This validation is not a replacement for prospective evidence, but it is the best available historical approximation of a real deployment test.

## 2. b) Current season — strengthen it

The model already uses current-season information, but it should react faster to a club whose demand level has changed compared with historical seasons.

### Development

- add an explicit **current season adjustment**;
- give recent home matches more influence than old seasons;
- measure whether the club is currently running above/below its historical attendance baseline;
- update the adjustment after every completed match;
- test recency-weighting variants under leakage-safe rolling validation.

### Goal

Make the model adapt faster when the current season behaves differently from the long-term history.

## 3. c) Match context — expand it

The model should understand why this specific fixture may create more or less demand than the historical baseline.

### Development

- strengthen opponent attractiveness / opponent strength features;
- add **future fixture attractiveness**;
- add fixture cannibalization: whether a more attractive home match is coming shortly after the current one;
- add fixture congestion / density of home matches;
- retain and improve form / league-position features for both teams;
- where reliable point-in-time data exists, add squad context:
  - injuries;
  - suspensions;
  - key-player availability;
  - major transfers / squad-strength changes;
- every historical context feature must be reconstructable as-of the forecast timestamp.

### Goal

Make the model understand why a particular match should overperform or underperform the club's normal demand level.

## 4. d) Live demand — develop most aggressively

Live ticketing evidence should continuously revise the pre-match expectation instead of being thought of only as five static forecast checkpoints.

### Development

- collect public inventory from the earliest available sales moment;
- continuously calculate:
  - availability index;
  - net inventory movement;
  - 6h / 24h / 72h / 7d velocity;
  - acceleration / deceleration;
  - sector movement;
  - price-area movement;
  - release / coverage anomalies;
- update the internal forecast after each meaningful new snapshot;
- keep T-30 / T-14 / T-7 / T-3 / T-1 as **evaluation checkpoints**, not as the only moments when the model can reason;
- let live correction modify the Structural Prior only when the live signal is reliable enough;
- compare continuous live revisions against the incumbent Structural Prior on exactly matched point-in-time evidence;
- keep public inventory semantics explicit: it is a demand proxy, not confirmed paid sales.

### Goal

Have a forecast that evolves with real observed demand throughout the sales cycle.

## 5. a) Historical data — tune, do not rebuild

Historical data remains the baseline layer. It is already the most mature part of the stack, so the objective is targeted improvement rather than a rewrite.

### Development

- keep the current Structural Prior architecture as incumbent;
- measure feature contribution and stability by horizon;
- remove noisy / unstable features that do not improve out-of-sample MAE;
- test stronger recency weighting so newer seasons matter more than older seasons;
- keep all challenger tests rolling-origin / point-in-time safe;
- promote only when paired evaluation improves the incumbent without unacceptable tail degradation.

### Goal

Improve the baseline without adding unnecessary model complexity.

# Development order

1. **Validate current model — LOEO + chronological walk-forward**
2. **b) Current season adjustment**
3. **c) Match context / future-fixture cannibalization / squad context**
4. **d) Continuous live demand correction**
5. **a) Historical Structural Prior tuning**

# What is already implemented today

## a) Historical data

**Implemented / mature.**

- five Ekstraklasa seasons;
- 1,530 matches;
- five Structural Prior horizons;
- historical MAE roughly 1.65k–1.89k on the exposed 2024/25–2025/26 reference seasons depending on horizon.

Needs targeted tuning, not replacement.

## b) Current season

**Implemented partially.**

Current-season / recent host information exists, but there is no sufficiently explicit, strongly governed current-season adjustment layer yet.

## c) Match context

**Implemented partially.**

Form, table / football context and schedule-related features exist in parts of the Structural Prior. Future-fixture cannibalization and robust squad context are not yet implemented as first-class governed features.

## d) Live demand

**Implemented and running, but not yet maximized.**

- live inventory collection exists;
- trajectory / velocity features exist;
- C1 v8 runs prospectively in shadow;
- sector and price-area trajectories / E0 pricing decision support exist;
- production attendance forecast still keeps `live_adjustment = 0` until an explicit promotion decision.

The next forecasting improvement is to make live demand revision more continuous and to validate it honestly on held-out historical events plus future prospective outcomes.

# Current evidence boundary

As of 2026-10-18:

- C1 v8 status: `EXPERIMENTAL_SHADOW`;
- prospective prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- validation state: `AWAITING_FIRST_PROSPECTIVE_SCORE`;
- therefore there is **no confirmed prospective live MAE yet**.

Development replay numbers around 2.0k–2.7k are development evidence only and must not be presented as independent production accuracy.

# Non-negotiable evaluation rules

- no future leakage;
- no random row split across snapshots from the same event;
- event is the independent evaluation unit;
- multiple snapshots from one event do not count as multiple matches;
- all features must be reconstructable as-of the forecast timestamp;
- tune and evaluate separately when necessary; do not select thresholds using the held-out event;
- compare challengers against the exact incumbent on the same event/horizon pairs;
- do not call replay prospective validation;
- do not promote C1 automatically.
