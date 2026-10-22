# D2 Long72 Convex Shrinkage v1 — 2026-10-22

## Purpose

P6 showed that frozen Long72 live/P2 materially reduces historical MAE versus the structural anchor, but also changes full-development-sample bias from about `-243` seats to `+917` seats.

P5a asks a narrower follow-up question:

> Can a simple convex shrinkage between the structural anchor and frozen live/P2 preserve most of the MAE uplift while improving robustness?

This is not a new model fit and does not alter the frozen P2 package.

## Immutable input

Frozen package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Predictions SHA256:

`489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b`

Input:

- 80 rows;
- 13 independent events;
- `24 < h <= 72`;
- historical exposed research only.

## Candidate family

For each row:

`blend(w) = structural_anchor + w * (frozen_P2 - structural_anchor)`

Predeclared fixed weights:

- `w=0.00` — structural anchor;
- `w=0.25`;
- `w=0.50`;
- `w=0.75`;
- `w=1.00` — frozen P2.

A separate `train-selected-weight` policy chooses among the same weights using only strictly earlier events.

Selector inside each training fold:

1. lowest event-balanced train MAE;
2. tie -> smaller weight.

No held-out event is used to choose its weight.

## Validation

Strict forward-event expanding validation from `temporal_validation_v1`:

- minimum training events: `5`;
- held-out events: `8`;
- each test event occurs strictly after all of its train events;
- trajectory rows are never treated as independent observations.

Train-selected weights by held-out event:

| Test event | Selected weight |
|---:|---:|
| 9 | 1.00 |
| 17 | 0.75 |
| 14 | 0.75 |
| 15 | 0.50 |
| 18 | 0.75 |
| 11 | 0.75 |
| 19 | 0.75 |
| 5 | 1.00 |

## Strict forward-event result

| Candidate | Event-balanced MAE | Bias | ΔMAE vs anchor | Event win rate vs anchor |
|---|---:|---:|---:|---:|
| Structural / `w=0.00` | 3180.22 | -2309.23 | 0.00 | 0.0% |
| `w=0.25` | 2974.89 | -1932.68 | -205.33 | 62.5% |
| `w=0.50` | 2776.51 | -1556.14 | -403.70 | 62.5% |
| `w=0.75` | 2614.46 | -1179.59 | -565.76 | 62.5% |
| **Frozen P2 / `w=1.00`** | **2472.30** | **-803.04** | **-707.92** | 50.0% |
| Train-selected weight | 2564.22 | -1081.97 | -616.00 | 50.0% |

Primary MAE selector therefore keeps **full frozen P2 (`w=1.00`)**.

The train-selected shrinkage policy is `+91.92` seats worse MAE than frozen P2 on the strict forward-event evaluation set.

Paired event-block bootstrap for `train-selected - frozen P2`:

- `ΔMAE = +91.92` seats;
- 95% interval `[-126.79, +324.24]`;
- `P(train-selected < P2) = 0.2154`.

There is no evidence that the adaptive shrinkage policy improves P2.

## Forward-event uncertainty versus structural anchor

For frozen P2 on the 8 held-out events:

- `ΔMAE = -707.92` seats;
- 95% paired event-block interval `[-1890.61, +362.00]`;
- `P(ΔMAE < 0) = 0.8942`.

The point estimate remains strong, but the small independent-event count keeps uncertainty wide.

## Descriptive full 13-event blend curve

This is descriptive only, not the headline selector:

| Weight | Event-balanced MAE | Bias |
|---:|---:|---:|
| 0.00 | 3707.14 | -242.63 |
| 0.25 | 3475.36 | +47.29 |
| 0.50 | 3247.87 | +337.21 |
| 0.75 | 3101.69 | +627.13 |
| 1.00 | **3012.63** | +917.05 |

The full-sample curve demonstrates a real MAE/bias trade-off, but the north star remains MAE and the forward-event evaluation does not justify replacing frozen P2 with a shrunk correction.

## Decision

**RETAIN FROZEN P2 — NO SHRINKAGE REPLACEMENT.**

What we learned:

1. reducing the live correction monotonically reduces the full-sample positive bias;
2. it also gives back too much MAE improvement;
3. train-only adaptive weighting does not beat full P2 out of sample;
4. therefore simple anchor/live shrinkage is not the next MAE win.

P5 is not fully closed: the higher-value combination experiment remains **structural + genuinely different PIT-safe context + live** once P4 has enough forward schedule-as-known evidence.

## Production boundary

- frozen P2 unchanged;
- no production activation;
- no learned weight deployed;
- `live_adjustment = 0`;
- `promotion_allowed = false`.
