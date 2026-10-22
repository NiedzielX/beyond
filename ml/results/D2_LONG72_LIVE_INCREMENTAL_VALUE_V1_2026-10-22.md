# D2 Long72 Live Incremental Value v1 — 2026-10-22

## Research question

> Does the frozen PIT live-inventory correction reduce MAE after the frozen structural Long72 anchor has already explained demand?

This is P6 from `ml/MAE_RESEARCH_ROADMAP_V3.md`.

No new model is fitted. No frozen policy is retuned. The experiment only compares the already-frozen structural anchor to the already-frozen `P2-observation-maturity` forecast.

## Immutable input

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Stage2 artifact:

- workflow run `39644319080`;
- artifact `12366826274`;
- artifact ZIP SHA256 `c750cf385b2c6b6f05fabceaf68ff323a66235862967900419be421f7cdcb4ae`;
- Stage2 result SHA256 `a9daa834e15b4f313b15c3e809033b7d79e4ed4357f61a8f5071e6bf20359d8c`;
- Stage2 predictions SHA256 `489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b`.

Evaluation scope:

- `24 < hours_to_kickoff <= 72`;
- 80 P2 rows;
- 13 independent events;
- evidence class `historical_exposed_research`.

## Method

Paired event-block bootstrap:

- independent unit = event, never trajectory row;
- each event is first collapsed to its own mean absolute error;
- 5,000 paired bootstrap resamples;
- seed `42`;
- `ΔMAE = live/P2 MAE - structural-anchor MAE`;
- negative `ΔMAE` means live inventory improves MAE.

The uncertainty interval is descriptive historical evidence. It is not a replacement for genuine prospective validation.

## Result — overall 24–72h

| Metric | Structural anchor | Structural + frozen live/P2 |
|---|---:|---:|
| Event-balanced MAE | 3707.14 | 3012.63 |
| Event-balanced bias | -242.63 | +917.05 |

Incremental live value:

- `ΔMAE = -694.51` seats;
- relative MAE improvement = `18.73%`;
- event improvement rate = `61.54%`;
- 95% paired event-block interval for `ΔMAE` = `[-1549.89, +148.05]`;
- `P(ΔMAE < 0) = 0.9500`.

Decision:

**HISTORICAL LIVE UPLIFT PROMISING, NOT UNCERTAINTY-CONCLUSIVE.**

The point estimate is large and useful, but with only 13 independent events the 95% interval still crosses zero.

## Result — 24–48h

- events: `13`;
- rows: `45`;
- anchor MAE `3707.14`;
- live/P2 MAE `2752.56`;
- `ΔMAE = -954.58`;
- relative improvement `25.75%`;
- event improvement rate `61.54%`;
- 95% interval `[-2001.66, +13.10]`;
- `P(ΔMAE < 0) = 0.9730`.

This is the strongest band. The interval comes very close to staying fully below zero, but still crosses zero slightly.

## Result — 48–72h

- events: `10`;
- rows: `35`;
- anchor MAE `4592.38`;
- live/P2 MAE `3927.67`;
- `ΔMAE = -664.71`;
- relative improvement `14.47%`;
- event improvement rate `70.00%`;
- 95% interval `[-1463.31, +241.98]`;
- `P(ΔMAE < 0) = 0.9292`.

The early-live band is promising but materially less certain.

## Bias interpretation

A critical guardrail appears in this formal comparison:

- structural anchor event-balanced bias: `-242.63` seats;
- live/P2 event-balanced bias: `+917.05` seats.

The live correction improves absolute error on average but shifts the forecast toward systematic overprediction.

This means the next live-R&D question is not simply "use more inventory correction". It is:

> Can we retain most of the live MAE uplift while shrinking the positive bias and tail degradation?

Any future live challenger should therefore compare against this frozen P2 package and report MAE **plus** bias/tail guardrails.

## Scientific interpretation

P6 is no longer an unanswered hypothesis.

Historical exposed evidence says:

1. live inventory contains incremental information beyond the structural anchor;
2. the observed MAE gain is large enough to keep developing;
3. sample uncertainty is still material at `N=13`;
4. the correction introduces a strong positive bias;
5. genuine Long72 prospective evidence remains required before promotion.

## Production boundary

- no frozen artifact changed;
- no P2 policy changed;
- no production activation;
- `live_adjustment = 0` remains unchanged;
- `promotion_allowed = false`.
