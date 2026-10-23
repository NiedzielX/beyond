# Beyond Ticketing — MAE Research Roadmap v4

Last updated: **2026-10-23**

Status: **CANONICAL CANDIDATE — LITERATURE-GROUNDED MAE-FIRST PLAN**

Supersedes the strategic priority order in `ml/MAE_RESEARCH_ROADMAP_V3.md` after merge. Existing frozen P4a/P7 experiment contracts remain unchanged.

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons by adding genuinely new predictive information, while preserving PIT safety, event independence, reproducibility and honest evidence classes.**

The next phase is deliberately **not** another broad estimator/hyperparameter search. Current methodology is already strong; the largest remaining opportunity is better representation of demand evolution and broader PIT-safe information.

Production remains unchanged:

`live_adjustment = 0`

---

# 2. Scientific rules that do not change

1. Frozen evidence packages remain immutable.
2. Every material feature/model/weight/target change creates a new challenger/version.
3. Event/match is the independent unit; trajectory rows and horizons from one match cannot leak across train/test.
4. Time-respecting folds are mandatory; random row/snapshot splits are never headline evidence.
5. Target/outcome data are opened only after the experiment protocol and identities are frozen where prospective evidence is possible.
6. MAE remains the primary point-forecast selector; median AE, P90 AE, bias, worst-event degradation, event-improvement rate and fold stability remain guardrails.
7. Every serious experiment reports uncertainty for `ΔMAE` using the event/match as the resampling unit.
8. New signal families are ablated against the same incumbent before combination.
9. Small positive point gains are not automatically interpreted as robust progress.
10. No research result activates production automatically.

---

# 3. Priority change after literature + repo gap audit

The model program now prioritizes four gaps:

1. **P9 — Booking Curve / Trajectory Shape** — highest-priority new live representation.
2. **P10 — Pooled Horizon Global Model** — immediate historical cross-learning experiment.
3. **P11 — Match Attractiveness / Commercial Context** — odds/quality/stakes first, then price/promotion and lineup/star/absence.
4. **Governance v2 — Minimum Meaningful MAE Improvement** — distinguish noisy point gains from robust research advancement.

P4a and P7 continue exactly as precommitted. P9/P10 may progress in parallel because they are separate R&D versions and do not mutate frozen evidence packages.

---

# 4. P9 — Booking Curve / Trajectory Shape

## 4.1 Why this is the largest current gap

Long72/P2 already uses:

- public inventory level;
- velocity over several windows;
- acceleration;
- observation maturity;
- linear extrapolation;
- anomaly/release flags.

The repo also already contains a PIT-safe trajectory feature store and a descriptive trajectory-gap layer:

- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/trajectory_gap.py`;
- related SQL/tests.

Therefore P9 is **not** “build trajectory data from scratch”.

The missing representation is:

> **How does the complete observed path of the current event compare with historical demand paths at the same point in the booking window, and what remaining pickup did genuinely prior/comparable events exhibit from that state?**

Target conceptual pipeline:

`PIT snapshots -> normalized trajectory -> comparable historical curves -> curve distance / similarity -> pickup distribution -> remaining-demand estimate -> structural residual challenger`

This is intentionally different information from simply adding another regression on `velocity_6h`, `velocity_24h`, etc.

## 4.2 Literature rationale

Revenue-management research treats the booking path itself as forecasting information. Dynamic booking-horizon methods use early observations to update the expected remainder of the curve, and pickup approaches have repeatedly been competitive/robust in booking-window forecasting.

Relevant literature:

- Weatherford, L. R. & Kimes, S. E. (2003), **A comparison of forecasting methods for hotel revenue management**, *International Journal of Forecasting*, 19(3), 401–415. DOI: `10.1016/S0169-2070(02)00011-0`.
- Lee, M. et al. (2011), **Booking horizon forecasting with dynamic updating: A case study of hotel reservation data**, *International Journal of Forecasting*. DOI: `10.1016/j.ijforecast.2010.10.004`.
- Webb, T. et al. (2020), **Revenue management forecasting: The resiliency of advanced booking methods given dynamic booking windows**, *International Journal of Hospitality Management*, 89, 102590. DOI: `10.1016/j.ijhm.2020.102590`.
- Takagi, S. et al. (2026), **Time Series Forecasting of Sports Ticket Sales with Venue-Independent Fan Segments**, DATA 2026, pp. 694–703. DOI: `10.5220/0015193800004091`.

The 2026 sports-ticket paper is especially relevant to representation design: short sports-sales sequences and venue heterogeneity make raw total-sales trajectories difficult to transfer; alternative decompositions can improve generalization. Beyond does **not** copy its LSTM design blindly because our data semantics differ and our sample is currently much smaller.

## 4.3 P9 v1 precommit direction

### Independent unit

`ticket_event`

### Canonical trajectory representation

Use only observations visible by target `as_of_at`.

Initial fixed canonical grid in hours before kickoff:

`168, 144, 120, 96, 72, 60, 48, 36, 24, 18, 12, 6`

At any forecast cutoff, only grid points already observable at that cutoff may be populated. No future point from the target trajectory may be interpolated backward.

Normalize inventory using both where available:

- first-visible public inventory (`available_index`);
- stadium/public-seat-map capacity share.

Raw inventory remains explicitly a **demand proxy, not confirmed paid sales**.

### Historical similarity

First candidate family uses a simple, auditable distance before any deep sequence model:

- weighted L1 distance over overlapping observed canonical points;
- require a minimum overlap count;
- references must be different events;
- references must satisfy PIT/data-quality rules;
- reference outcomes/pickup may only be used in training/reference construction, never in target feature construction.

### Pickup estimate

For the nearest historical reference pool, estimate a robust remaining pickup distribution using median/quantiles rather than one-neighbor extrapolation.

Output examples:

- `curve_similarity_distance`;
- `reference_event_count`;
- `reference_club_count`;
- `median_remaining_pickup_share`;
- pickup Q25/Q75;
- `trajectory_shape_gap`;
- `remaining_demand_estimate`.

### Challenger

Do **not** replace the structural forecast directly with inventory math.

Use:

`strong structural/pre-live anchor -> P9 trajectory/pickup residual correction -> MAE evaluation`

### Research sequence

1. target-free representation + leakage tests;
2. descriptive reference-curve audit;
3. freeze v1 representation before looking at model result matrix;
4. simple residual challenger first;
5. only then consider richer sequence models if sample size justifies them.

Deep LSTM/Transformer work is explicitly **not** P9 v1. The Takagi et al. result is evidence for representation value, not a license to overfit a small Beyond sample.

---

# 5. P10 — Pooled Horizon Global Model

## 5.1 Hypothesis

Current Structural Prior research effectively learns separate horizon models for T-30/T-14/T-7/T-3/T-1.

The five-season PIT store contains approximately:

`1,530 matches × 5 horizons = 7,650 PIT rows`

Hypothesis:

> **A single model trained across all PIT horizons can exploit cross-horizon regularities and reduce OOS MAE compared with horizon-local training, provided all rows of one match remain in the same fold and match contribution is balanced.**

This is a natural application of global forecasting: pooled/global models may generalize better because shared parameters can learn across related forecasting tasks rather than estimating an independent function for each task.

Literature:

- Montero-Manso, P. & Hyndman, R. J. (2021), **Principles and algorithms for forecasting groups of time series: Locality and globality**, *International Journal of Forecasting*, 37(4), 1632–1653. DOI: `10.1016/j.ijforecast.2021.03.004`.

## 5.2 Non-negotiable leakage rule

**All five PIT rows for the same `match_key` stay together.**

Forbidden example:

- train on target-match T-30;
- evaluate target-match T-7.

Season/group folds must block the complete match, and any future within-season experiment must use match/event identities as groups.

## 5.3 P10 v1 fixed design

### Input

Canonical structural PIT feature store.

### New pooled feature

- numeric `horizon_days` / hours-to-kickoff representation;
- existing PIT-safe structural features;
- existing home/away club categories.

### Training weight

Each match receives equal total weight. With five eligible horizons, each row receives `1/5` of that match's total training weight.

### Candidate family

Keep v1 intentionally small:

1. pooled `HistGradientBoostingRegressor(loss='absolute_error')` residual model;
2. horizon-local equivalent as the controlled comparator.

No broad hyperparameter sweep in P10 v1.

### Validation

Use strict expanding season folds and persist match identities + SHA.

Primary comparisons:

- pooled vs horizon-local MAE overall, with equal match/horizon contribution;
- per-horizon MAE;
- per-season/fold MAE;
- per-club diagnostics;
- bias, median AE, P90 AE;
- paired match-block uncertainty for `ΔMAE`.

P10 may run immediately on historical R&D data. Historical seasons already inspected remain **exposed research evidence**; P10 does not create a new unseen holdout by relabeling old data.

---

# 6. P11 — Match Attractiveness / Commercial Context

## 6.1 Literature-grounded rationale

A systematic review of stadium-attendance demand research catalogued 195 manuscripts / 235 empirical studies and shows a broad recurring demand specification around match/team quality, outcome uncertainty, pricing, substitutes, timing and other event context.

- Schreyer, D. & Ansari, P. (2022), **Stadium Attendance Demand Research: A Scoping Review**, *Journal of Sports Economics*, 23(6), 749–788. DOI: `10.1177/15270025211000404`.

Portuguese football evidence also identifies cost, habit persistence, expected quality, team performance and outcome uncertainty as important explanatory variables:

- Martins, A. M. & Cró, S. (2018), **The Demand for Football in Portugal: New Insights on Outcome Uncertainty**, *Journal of Sports Economics*, 19(4), 473–497. DOI: `10.1177/1527002516661602`.

## 6.2 What Beyond already has

Existing structural/PIT context already includes substantial information such as:

- home-demand/attendance history;
- opponent demand;
- table position / PPG;
- recent form;
- season/calendar/timing;
- rest/congestion;
- home-opponent history;
- P4 fixture spacing.

The repository also already contains scaffolding for:

- verified absences;
- rivalry mapping;
- match stakes;
- price observations / pricing context;
- weather study;
- media attention.

P11 must reuse and harden these sources rather than create duplicate feature stores.

## 6.3 Priority order

New P11 work is prioritized by closeness to the attendance-demand mechanism and PIT availability:

### P11a — Market-implied match quality / outcome uncertainty / stakes

Highest priority.

Candidates:

- PIT bookmaker implied home/draw/away probabilities;
- implied match balance / uncertainty;
- favorite strength;
- expected quality proxy;
- verified competition/match stakes;
- rivalry flag.

Odds must be captured **as known at the forecast cutoff**. Closing odds cannot be backfilled to T-7/T-3/T-1.

### P11b — Price / promotion context

Use existing price-observation infrastructure where coverage is genuine.

Candidates:

- PIT minimum/median visible price;
- price-tier mix;
- price change since earlier cutoff;
- promotion/discount flag only when evidenced before cutoff.

Do not infer ticket price from remaining inventory.

### P11c — Lineup / star strength / verified absences

Use only information announced/verified by `as_of_at`.

Potential representation:

- expected/confirmed starter strength;
- star-player availability;
- absence-weighted squad strength.

### P11d — Weather and attention/hype

Remain useful later families, but follow P11a–c unless data quality makes an earlier family impossible.

Every family requires a separate controlled ablation before it may enter a combination model.

---

# 7. Governance v2 — Minimum Meaningful Improvement

## 7.1 Problem

A rule such as:

`ΔMAE < 0 + >50% events improved + >50% folds improved`

is useful for a research point estimate but is not sufficient to describe a tiny/noisy gain as robust progress.

Repeatedly choosing the best result from noisy finite-sample estimates can itself overfit the model-selection criterion.

Literature:

- Cawley, G. C. & Talbot, N. L. C. (2010), **On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation**, *Journal of Machine Learning Research*, 11, 2079–2107.

## 7.2 New decision vocabulary

### `NO_RESEARCH_GAIN`

No positive MAE point gain, or basic stability guardrails fail.

### `POINT_GAIN_UNCERTAINTY_LIMITED`

A challenger has a positive point gain and may justify continued research, but evidence is not yet precise/practically large enough to call robust advancement.

Examples:

- bootstrap interval still includes no gain;
- evaluation N is very small;
- gain is smaller than the business-defined meaningful threshold;
- the meaningful threshold is not yet defined.

### `ROBUST_RESEARCH_ADVANCE`

Reserved for a challenger that passes **all** predeclared conditions, including:

1. positive MAE point gain;
2. event/fold stability guardrails;
3. practically meaningful absolute improvement;
4. precision requirement for `ΔMAE`;
5. PIT/lineage/reproducibility gates.

This is still a **research** status, not automatic production promotion.

## 7.3 Minimum practically meaningful ΔMAE

Do **not** hardcode an arbitrary value such as `100 seats` or `3%` merely to complete the framework.

The threshold must be derived from club/business decision value, for example:

- transport/staffing/food/security decisions affected by forecast error;
- operational cost of over- vs under-forecasting;
- action thresholds where a forecast improvement changes a real decision;
- potentially asymmetric error cost if validated with business stakeholders.

Until an approved threshold exists:

> **No new experiment may emit `ROBUST_RESEARCH_ADVANCE`; the strongest allowed positive state is `POINT_GAIN_UNCERTAINTY_LIMITED`.**

## 7.4 Precision

Default robust interpretation should require the event-block uncertainty interval for `challenger_mae - incumbent_mae` to be below zero, unless a future experiment precommits another justified precision criterion.

Small-N start gates are not precision gates.

Example: P7 `N=9` with minimum five training events provides only about four strict forward held-out events when kickoffs are distinct. That is enough to start research, not enough to believe a small uplift.

Frozen P4a/P7 scorecard rules are not rewritten retroactively. Governance v2 is a separate interpretation/promotion layer for P9/P10+ and for any later review of earlier experiment results.

---

# 8. P12 — Demand Regime / Capacity / Commercial Constraints

Lower priority than P9–P11 but retained explicitly so it is not forgotten.

Observed public inventory and attendance can be constrained/censored by:

- capacity;
- sector releases/holds;
- complimentary allocations;
- re-opened inventory;
- no-shows;
- seat-map coverage changes.

Future audit:

- constrained / near-sellout vs unconstrained events;
- whether live-signal MAE differs by regime;
- whether separate interpretation/shrinkage is justified.

Current release/coverage anomaly flags remain mandatory inputs to data-quality decisions.

---

# 9. Execution order

## Continue frozen/data-bound work unchanged

- P4a previous-home spacing;
- P7 Long168;
- final24/Long72 prospective scoring;
- schedule/context sidecars.

## Start now in R&D lane

### Track A — P9

1. implement canonical target-free curve representation;
2. implement PIT-safe historical similarity/pickup primitives;
3. regression tests for target-future leakage and self-event exclusion;
4. inspect genuine completed-event coverage;
5. precommit first learnable P9 candidate only after coverage audit.

### Track B — P10

1. implement pooled-horizon benchmark now;
2. ensure complete match blocking;
3. equal total training weight per match;
4. compare against horizon-local equivalent under identical folds/features;
5. report uncertainty and governance-v2 status.

### Track C — P11 data readiness

1. audit existing stakes/rivalry/absence/pricing infrastructure;
2. design PIT odds capture before attempting model use;
3. define availability/coverage thresholds before ablation.

### Track D — business threshold

Define the minimum meaningful MAE improvement from actual downstream decisions. This is governance/data-product work, not a value to optimize from the same model scorecard.

---

# 10. What not to do

Do not:

- retune frozen Long72/P2 on the same development events;
- add another large estimator sweep before testing P9/P10 information hypotheses;
- use target-event future trajectory points;
- put multiple horizons from one match on opposite sides of a fold;
- backfill closing odds/final lineup/final weather into an earlier cutoff;
- call a tiny positive point estimate robust improvement;
- define the meaningful-MAE threshold from the experiment result it will judge;
- activate production from historical/exposed research evidence.

---

# 11. One-line handoff

> **The next accuracy phase is representation-first, not tuning-first: P9 learns booking-curve/pickup shape from PIT trajectories, P10 pools the 7,650 historical horizon snapshots with strict match blocking, P11 adds economically grounded match/commercial context, and Governance v2 prevents tiny/noisy ΔMAE gains from being mistaken for robust progress. P4a/P7 stay frozen and production stays off.**
