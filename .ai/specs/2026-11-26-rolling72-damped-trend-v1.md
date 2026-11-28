# Rolling72 fixed damped-trend shadow — prospective precommit

Date/precommit clock: 2026-11-26 UTC (document preparation; capture the actual
DB activation clock separately).
Status: **PROPOSED / NOT ACTIVATED / NO OUTCOMES OBSERVED UNDER THIS VERSION**.
Parent contracts: [fresh paired PERS–drift24 precommit](2026-11-24-rolling72-fresh-paired-drift24.md)
and [paired drift24 runtime](2026-11-25-rolling72-paired-drift24-runtime.md).
This is an additive, future-only research lane; it does not amend either
parent contract, any frozen series, or product behavior.

## Question and scope

Does one fixed, conservative geometric damping of the already-declared
drift24 slope improve future public availability forecasts over PERS on new
paired observations? Does it add value over the fixed drift24 comparator?
The first contrast is the predeclared decision contrast; the second is a
separately reported incremental comparison. This forecasts the registered
`available_total_seats` source measure only. It is not a sales, demand,
attendance, revenue, or intervention-effect forecast. `live_adjustment=0`
remains unchanged.

The evaluation cohort begins only after this version is separately reviewed,
frozen and activated, and uses new source opportunities first known after
activation. No old PERS, drift24, B, E5, or other frozen/exposed issue, target,
label, or score enters this cohort. Old source seals may be read solely as
then-known event history under the parent source contract; they do not create
an issue, paired outcome, or retrospective forecast. Never edit, reissue,
relabel, or rescore a frozen series. A changed formula, damping constant,
eligibility rule, target, or decision threshold requires a new version and a
new future cohort.

## Fixed methods and coordinates

Create a new comparator identity, e.g. `rolling72-mvp-paired-damped-trend-v1`,
with one immutable bundle per eligible new source opportunity. Each bundle
contains all three methods—PERS, fixed drift24, and fixed damped trend—at the
same actual `issued_at`, with the same registered event, origin seal,
projection reference, target times, and eventual target seal IDs. These are
new shadow rows; they neither overwrite nor attach predictions to the existing
PERS or drift24 lanes. Horizons are exactly +24, +48, and +72 elapsed hours.
Kickoff eligibility and per-horizon null handling follow the parent runtime.

PERS is the origin level, preserving true numeric zero. The drift24 control is
the exact fixed B/LAD anchor, elapsed-time slope, age correction, zero lower
clamp, no upper cap, and support/fallback policy specified in the parent
precommit/runtime; it is recomputed only inside this new paired bundle from
the same validated origin and then-known history. Do not select or alter its
anchor window, source-break semantics, clock, or fallback based on outcomes.

The only challenger is the following one fixed damping of that same slope:

```text
phi = 0.80                         # fixed before first issue; no fitting
t_h = h + age_hours                # elapsed hours, h in {24, 48, 72}
effective_hours(t_h) = 24 * (1 - phi ** (t_h / 24)) / (1 - phi)
DAMPED_h = max(0, origin.available_total
                   + slope24 * effective_hours(t_h))
```

`slope24` is exactly `(origin.available_total - anchor.available_total) /
elapsed_hours`, and `age_hours` is exactly the parent's projection-reference
age. Use the parent's real projection-reference and actual issue clocks and
90-second bound; `target_at = issued_at + h`. Apply the formula in float8 with
no rounding or upper-capacity clamp. `phi=0.80` means each additional 24-hour
block carries 80% of the previous block's slope contribution, while the first
24-hour block retains the undamped slope; the geometric sum above defines the
extension for fractional elapsed hours and avoids ambiguous rounding to day
steps. For example, with zero age the trend contribution uses 24 effective
hours at +24, 43.2 at +48, and 58.56 at +72. These
illustrations specify the formula, not expected errors.

If source/anchor/break/scope support for the slope fails while the origin is
valid, the damped full policy falls back to the same numeric PERS origin and
records `FALLBACK_PERS` with the parent's fixed reason. Invalid current origin
makes all methods unavailable. Fallback remains in the primary full-policy
comparison; supported-only estimates are diagnostic. First-point issues still
produce PERS plus paired fallback values. Do not adapt phi by event, club,
horizon, history length, residual, exposed results, or support level.

## Scope, target pairing, and coverage

Use the parent runtime's exact source-known-at, committed-read, issue-clock,
latest-attempt/no-backtracking, immutable-label, and target-seal rules. One
accepted common future target ID/value scores all three methods. A selected
newer invalid, stale, non-ready, or unknown-order attempt cannot be replaced
by an older ready snapshot. A valid scope change at target remains scored and
is flagged; report the predeclared stable-scope sensitivity separately. Never
interpret inventory-pool or sector-count changes as sales. Origin-to-anchor
membership requirements and source-break rules remain those fixed in the
parent drift24 recipe.

For each horizon publish all eligible opportunities, actual issues, refusals
and unattempted opportunities, PERS numeric forecasts, drift support/fallback,
damped support/fallback, outside-kickoff and unavailable counts, target
future/due/matured states, accepted shared labels, and missing/stale/invalid/
unknown-order labels. Report forecast coverage as numeric full-policy issues
divided by valid pre-kickoff opportunities and scoring coverage as accepted
common labels divided by matured eligible targets. Preserve late-start gaps;
missingness is never zero. A zero denominator yields null. Report scope flags
and both full-cohort and stable-scope sensitivity; do not filter scope changes
out of the primary score.

## Locked evaluation and decision

For every horizon, use the identical accepted event × bundle × horizon ×
target-seal set across all three methods. Compute absolute error per target,
then per-event MAE, then the equal-event mean. Report event-balanced MAE,
signed bias, event-level P90 and worst-event MAE, paired event counts, club
counts, support/fallback mix, and both coverage measures. No snapshot-level
bootstrap or event-size weighting.

**Primary contrast:** full-policy damped trend (including PERS fallback)
versus PERS at +72. At the fixed review floor of at least 30 new independent
events across at least 8 clubs with eligible paired +72 outcomes, support is
`SUPPORTED` only when damped-trend event-balanced +72 MAE is at least 10%
lower than PERS, the 95% paired event-bootstrap interval for
`damped_trend - PERS` lies entirely below zero, and +24 and +48 point MAEs do
not exceed PERS. Use 10,000 event resamples and seed 42. Below the floor is
`PARTIAL`; absent +72 support or a missing guardrail comparison is `UNKNOWN`;
with adequate support but any failed criterion report `NOT_SUPPORTED`.
Always retain and report every eligible event and all three horizons. This
30-event/8-club floor is the project review gate, not a literature-derived
sample-size guarantee, pass guarantee, or proof of precise club-level effects.
Include fixed leave-one-event-out and leave-one-club-out sensitivity summaries
at review; they are robustness diagnostics only and do not alter the primary
cohort, weightings, support floor, or decision rule.

**Incremental contrast:** separately report the same paired event-balanced
MAE, signed delta, and 95% event-bootstrap interval for damped trend versus
full-policy drift24 on the exact same paired target set, by horizon. Do not
substitute this contrast for the primary PERS decision, combine cohorts, or
invent a second promotion threshold after seeing outcomes. A missing or
different target set is explicitly `UNPAIRED` with null delta. Publish
drift24 and damped-trend coverage/fallback side by side so a coverage change
cannot masquerade as an accuracy gain. No model selection by horizon.

Report bootstrap reproducibly: resample independent event IDs with
replacement, keeping all rows of each sampled event together; recompute each
method's equal-event MAE and paired delta in each replicate; use the fixed
percentile 2.5th/97.5th endpoints. If a resample lacks a score for a required
horizon, use the exact supported event cohort's event aggregates, not row
resampling. Record implementation hash and seed. Do not change the evaluator
or decision rule after first outcome access.

## Literature and limits

This is a simple testable Beyond hypothesis, not a result established by
literature. The checked author materials for Hyndman and Athanasopoulos,
*Forecasting: Principles and Practice*, 3rd ed., include the trend-methods
chapter/slides (including damped-trend methods) and rolling-origin time-series
cross-validation: [trend methods, chapter 8.2](https://github.com/robjhyndman/fpp3_slides/blob/main/8-2-trend.Rmd)
and [time-series cross-validation, chapter 5.10](https://github.com/robjhyndman/fpp3_slides/blob/main/5-10-tscv.Rmd).
The project review records that these source files were read; it supports
damping as a recognized forecasting construction and rolling-origin testing
as an evaluation design, not this value of `phi`, transfer to ticket inventory,
or an expected improvement. The exact fixed `phi=0.80` is a conservative
predeclared engineering choice for this one prospective falsification test,
not a fitted/optimized estimate or a literature-derived optimum. See the
[checked literature review](../../ml/ROLLING_72H_LITERATURE_REVIEW_2026-11-08.md)
and its access limitations. The checked review of booking-curve code also
notes that a damped extrapolation correction was introduced after test
performance was seen; that exposed-evidence adjustment is specifically not
reused or used to choose this formula ([review](../../ml/ROLLING_72H_GITHUB_INSPIRATION_REVIEW_2026-11-18.md)).

No source cited here guarantees 10% improvement, 1200-seat MAE, or transfer
from booking curves to public availability. The experiment says nothing about
attendance, latent demand, or effects of price, promotion, advertising, or
pool policy. Those states remain unknown absent contemporaneous evidence.

## Implementation boundary and release state

This document authorizes preparation of a prospective protocol only. It does
not activate the lane, authorize code/SQL/jobs, alter a live DB, schedule a
cycle, or grant access to existing result series. Before any first issue, the
root owner must review this precommit, freeze the exact implementation and
evaluator hashes, validate in a dedicated isolated PG16 test DB, receive
independent review, and separately activate the new version. A future-only
execution must prove new issue persistence independently of the later MAE
review. No outcome may be inspected for this version until the fixed methods,
coverage denominators, score selector and evaluator are frozen.

Implementation must be additive and service-only, preserve existing tables,
lanes, grants, jobs and frozen rows, and use no retro-prediction. Tests must
cover formula values at 24/48/72 and fractional age; positive/negative/zero
slope; lower clamp and zero level; exact equality to drift24 when phi=1 in a
test-only algebra check; fallback and true-zero distinction; shared clocks and
target IDs; independent kickoff nulls; source breaks and membership; valid
changed-scope scoring; latest-invalid/no-backtracking and unknown-order
refusal; coverage denominators/missing labels; paired identical-target gates;
unequal event size, event bootstrap determinism and thresholds; immutable
parent PERS/drift24/E5 isolation and append-only ACLs. Synthetic cases validate
contracts only and are never included in prospective evidence.
