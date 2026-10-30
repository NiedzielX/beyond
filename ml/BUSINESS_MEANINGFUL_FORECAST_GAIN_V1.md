# Beyond Ticketing — Business Meaningful Forecast Gain v1

Precommit date: **2026-10-30**

Status: **PRECOMMITTED BEFORE FROZEN-TRAJECTORY ATTENDANCE OUTCOMES**

Production impact: **none**

This contract prevents Beyond from calling a statistically positive but commercially trivial attendance-forecast improvement a product win.

---

# 1. Decision principle

The scientific North Star remains prospective event-balanced attendance MAE:

`Delta MAE = challenger MAE - incumbent MAE`

Lower is better.

However:

> **Delta MAE < 0 is necessary but not sufficient for a business-meaningful result.**

A challenger must improve forecast accuracy on a scale large enough to matter for the revenue decisions Beyond is designed to support: campaign activation, sector activation, offers, packages and pricing.

This document does not claim that forecast error reduction directly causes ticket sales. Revenue attribution remains a separate causal/product validation problem.

---

# 2. Ex-ante commercial anchor

The current Beyond business model uses a **7% fill-rate uplift** assumption for incremental revenue modelling.

Current reference archetypes in the business model:

| Reference | Stadium capacity | Average attendance | Average unfilled capacity | 7% of unfilled capacity |
|---|---:|---:|---:|---:|
| Legia / top-end | 31,103 | 22,233 | 8,870 | 620.9 seats |
| Odra / 1. Liga | 11,600 | 5,419 | 6,181 | 432.7 seats |

The current reference mix used in the commercial model is 70% top-end / 30% medium-club.

Weighted action scale:

`0.70 * 620.9 + 0.30 * 432.7 = 564.4 seats`

For a stable, readable ex-ante threshold, v1 rounds this to:

> **550 seats of event-balanced MAE improvement**

This is an **accuracy-resolution threshold**, not an assertion that 550 seats of lower MAE creates 550 incremental ticket sales.

The rationale is that a forecast improvement much smaller than the scale of the commercial intervention assumed in Beyond's own business model is unlikely, by itself, to be strong evidence that the forecast layer materially improves revenue decisions.

---

# 3. Frozen business-meaningful threshold

For a given prospective decision horizon `h`:

`business_gain_h = incumbent_MAE_h - challenger_MAE_h`

The challenger passes the v1 absolute business-gain threshold only when:

`business_gain_h >= 550 seats`

Equivalent Delta-MAE form:

`Delta_MAE_h <= -550 seats`

The threshold is fixed before the relevant prospective attendance outcomes are available.

Do not lower it because an early challenger produces a smaller positive result.

---

# 4. Required risk guards

Passing the 550-seat threshold is not sufficient by itself.

At the same horizon, all of the following must also hold on genuinely prospective scored events:

1. **Event improvement rate > 50%** — the gain cannot be driven only by a minority of very large wins.
2. **Median event Delta AE < 0** — the typical event must improve, not only the mean.
3. **Challenger P90 AE <= incumbent P90 AE** — tail error must not worsen.
4. **Absolute signed bias must not worsen** — `abs(mean challenger error) <= abs(mean incumbent error)`.
5. **No retrospective predictions or backfilled missed windows are included.**
6. **Every event is weighted equally.** Multiple snapshots or prefixes from one event never become multiple independent attendance observations.

If a candidate improves average MAE but fails a guard, keep the result as research evidence and report the failed guard explicitly.

---

# 5. Horizon rule

Evaluate business meaningfulness **separately by decision horizon**.

For the active frozen-encoder candidate, report at minimum:

- P-7;
- P-3;
- P-1.

Do not average a strong late-horizon result with a weak early-horizon result and claim that the model is business-meaningful at both.

A candidate may become useful at P-1 before it becomes useful at P-7. That is a valid product finding.

An overall summary may be reported only as a secondary view and must preserve event-level weighting.

---

# 6. Evidence maturity

The first few scored events are evidence collection, not a promotion decision.

The existing prospective-diversity convention of **8 independent events / 5 clubs** is used as the earliest point at which Beyond may publish a directional business-gain readout for this v1 contract.

This is **not production eligibility** and does not override uncertainty/downside review.

Before 8 events / 5 clubs, status must remain:

`INSUFFICIENT_PROSPECTIVE_EVIDENCE`

Even after the directional gate is reached, production remains separately review-gated and OFF.

---

# 7. Decision labels

Use the following deterministic labels.

### `INSUFFICIENT_PROSPECTIVE_EVIDENCE`

Fewer than 8 independent scored events or fewer than 5 clubs at the evaluated horizon.

### `RESEARCH_POSITIVE_NOT_BUSINESS_MEANINGFUL`

Prospective `Delta MAE < 0`, but improvement is less than 550 seats.

### `BUSINESS_GAIN_WITH_RISK_GUARD_FAIL`

Prospective improvement is at least 550 seats, but one or more downside/bias guards fail.

### `BUSINESS_MEANINGFUL_REVIEW_ELIGIBLE`

Prospective improvement is at least 550 seats and every v1 risk guard passes.

This label permits a product/model review only. It does not activate production.

### `NOT_SUPPORTED`

Prospective `Delta MAE >= 0` once the directional evidence gate is reached.

---

# 8. Relationship to revenue proof

Attendance forecast accuracy and revenue uplift are different layers of evidence.

A model can pass this forecast gate and still fail to generate incremental revenue.

A later product experiment must separately test whether acting on the forecast improves outcomes such as:

- campaign conversion;
- incremental tickets sold;
- incremental GMV;
- inventory utilisation;
- pricing / offer performance.

The business model currently uses Campaign Activation and Incremental Revenue Share as monetisation mechanisms. Forecast quality is an enabling capability, not causal proof of those revenues.

---

# 9. Change-control rule

The 550-seat threshold may be replaced later only by a stronger business-derived threshold based on real pilot-club decision economics, for example explicit campaign/action thresholds supplied before evaluating the next candidate version.

Any replacement must:

1. be documented before the outcomes used to evaluate that replacement;
2. create a new version of this contract;
3. never retroactively relabel an already-scored candidate under a more favourable threshold.

---

# 10. Current application

This v1 contract applies prospectively to the current attendance challengers, including:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

At precommit time, the frozen trajectory lane has prospective predictions but **no confirmed attendance scores**.

Therefore no candidate result influenced the 550-seat threshold.

Production remains:

`live_adjustment = 0`

`production_change = false`
