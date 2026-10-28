# Beyond Ticketing — Trajectory Lane A Result v1

Date: **2026-10-28**

Status: **REJECTED AS CANDIDATE / RETAINED AS SIMPLE BENCHMARK**

Precommit: `trajectory-lane-a-ridge-residual-v1`

Evidence class: `historical_exposed_research`

Production impact: **none**

`live_adjustment = 0`

---

## 1. Human summary

The first simple trajectory model did **not** improve the structural forecast.

Strict-forward event-balanced result:

- structural incumbent MAE: **2594.5**;
- Lane A Ridge MAE: **4153.3**;
- Delta MAE: **+1558.8**;
- relative change: **+60.1% worse**;
- independent strict-forward test events: **5**;
- event improvement rate: **20%**.

Decision:

> **Do not tune Lane A v1 after the result. Reject it as a candidate and keep it as the frozen simple benchmark for Lane B.**

This does not prove that trajectory information is useless. It shows that this fixed low-capacity engineered-feature residual formulation does not extract useful incremental signal on the current strict-forward cohort.

---

## 2. Cohort and validation

Frozen cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled independent events in the development registry;
- first 5 events establish the minimum expanding training history;
- 5 later independent events receive strict-forward outer predictions;
- 14 tested event/cutoff rows in total;
- all prefixes from one event remain in the same fold;
- no random row CV.

The outer test events were:

- Wisła Płock;
- Pogoń Szczecin;
- Śląsk Wrocław;
- Jagiellonia;
- Legia.

---

## 3. Result by horizon

| Horizon | Events | Incumbent MAE | Lane A MAE | Delta MAE |
|---|---:|---:|---:|---:|
| T-7 | 4 | 3399.0 | 4490.9 | **+1091.9** |
| T-3 | 5 | 2667.9 | 4224.7 | **+1556.8** |
| T-1 | 5 | 2314.9 | 3727.8 | **+1412.9** |

Lane A is worse at every currently evaluable horizon.

---

## 4. Result by independent event

| Event | Incumbent event MAE | Lane A event MAE | Delta MAE |
|---|---:|---:|---:|
| Wisła Płock | 407.9 | 4574.2 | **+4166.4** |
| Pogoń Szczecin | 1786.7 | 2113.0 | **+326.3** |
| Śląsk Wrocław | 6732.9 | 9881.7 | **+3148.8** |
| Jagiellonia | 975.1 | 881.5 | **-93.6** |
| Legia | 3070.2 | 3316.2 | **+246.0** |

Only one of five independent events improves.

Worst event degradation:

**+4166.4 MAE**.

---

## 5. Interpretation

The result suggests that the current engineered scalar trajectory features are not a reliable residual correction over the structural prior in this small forward cohort.

Possible reasons include:

- current independent-event sample is very small;
- the structural prior is already strong on some targets;
- handcrafted velocity/acceleration features may lose important ordering/shape information;
- inventory behaviour differs sharply between clubs/events;
- the relationship between public inventory proxy and attendance residual may be nonlinear/nonstationary.

These are hypotheses only. This result does **not** authorize post-hoc feature or alpha tuning on the same outer test events.

---

## 6. Decision

### Lane A v1

`REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

Do not:

- change Ridge alpha after seeing this result;
- remove bad events;
- add context features to repair this exact result;
- select a different feature subset against the same outer folds and call it v1.

Any revised simple trajectory learner must be a separately versioned hypothesis.

### Lane B

Continue with the already-precommitted small GRU sequence experiment.

The important comparison is now:

> **Can ordered genuine sequence representation beat both the structural incumbent and the failed Lane A engineered-feature benchmark?**

Lane A's failure is not a reason to cancel Lane B because Lane B tests a materially different representation hypothesis.

---

## 7. Machine-readable result

`ml/results/trajectory_lane_a_ridge_residual_v1_result.json`

No production change occurred.
