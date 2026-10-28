# Beyond Ticketing — Trajectory Lane B v2 Result

Date: **2026-10-28**

Status: **MECHANISM NOT SUPPORTED / DO NOT ADVANCE**

Precommit: `trajectory-lane-b-small-gru-residual-ratio-v2`

Evidence class: `historical_exposed_research`

Production impact: **none**

`live_adjustment = 0`

---

## 1. Human summary

V2 successfully changed the scale of the learned correction, but it made the forecast materially worse.

Strict-forward exposed-cohort result:

- structural incumbent MAE: **2594.54**;
- Lane B v1 MAE: **2595.40**;
- Lane B v2 MAE: **4792.42**;
- Delta v2 vs incumbent: **+2197.88**;
- Delta v2 vs v1: **+2197.01**;
- event improvement rate: **20%**;
- worst event degradation: **+4647.90**.

Decision:

`MECHANISM_NOT_SUPPORTED`

> **Residual-ratio target scaling solved the near-zero-output problem, but did not solve the forecasting problem. It produced corrections that were too large and unreliable.**

Do not tune v2 further on this exposed cohort.

---

## 2. What changed vs v1

Lane B v1 predicted seat residuals only around:

`-0.06 ... +4.33 seats`

V2 predicted:

- median absolute seat correction: **1550.78**;
- maximum positive correction: **+6126.91**;
- maximum negative correction: **-9673.16**;
- median predicted residual ratio: **+2.68%**;
- median absolute predicted residual ratio: **9.30%**;
- range: **-59.61% ... +44.72%**.

So the target-scale hypothesis was mechanically informative:

> **Scaling was indeed a major reason v1 stayed near zero.**

But the useful-model hypothesis was not supported:

> **Once the output was allowed to move at realistic seat scale, the current small-data sequence model over-corrected badly.**

---

## 3. Result by horizon

| Horizon | Events | Incumbent MAE | Lane B v2 MAE | Delta MAE |
|---|---:|---:|---:|---:|
| T-7 | 4 | 3399.03 | 7333.22 | **+3934.20** |
| T-3 | 5 | 2667.93 | 4567.30 | **+1899.37** |
| T-1 | 5 | 2314.89 | 3421.15 | **+1106.27** |

V2 is worse at every currently evaluable horizon.

The damage is largest at T-7, where trajectory evidence is also sparsest.

---

## 4. Result by independent event

| Event ID | Incumbent event MAE | Lane B v2 event MAE | Delta MAE |
|---:|---:|---:|---:|
| 20 | 407.86 | 2611.10 | **+2203.24** |
| 10 | 1786.65 | 6062.31 | **+4275.66** |
| 23 | 6732.88 | 11380.77 | **+4647.90** |
| 21 | 975.08 | 996.41 | **+21.33** |
| 22 | 3070.21 | 2911.49 | **-158.72** |

Only one of five independent events improves.

---

## 5. Seed diagnostics

Residual-ratio spread across frozen seeds:

- median spread: **0.1374 ratio points**;
- max spread: **0.3881 ratio points**.

This is much less reassuring than v1's near-zero seat spread because ratio differences map to large seat differences once multiplied by structural P50.

V2 therefore introduces both:

- much larger correction magnitude;
- meaningfully greater practical sensitivity to initialization.

---

## 6. Interpretation

The combined v1/v2 evidence is useful:

### Lane B v1

Raw-seat target + fixed small GRU/L1 setup:

`correction ≈ 0`

Result:

- stable;
- safe;
- no incremental gain.

### Lane B v2

Residual-ratio target with everything else fixed:

`correction becomes large`

Result:

- output magnitude is no longer collapsed;
- MAE becomes materially worse;
- early-horizon errors become especially large;
- initialization differences become operationally meaningful.

Therefore:

> **Target scaling alone is not the missing solution.**

The current 10-event labeled sample is too weak to justify continuing to tune correction magnitude, loss, architecture or caps against the same exposed five outer events.

---

## 7. What we should NOT do next

Do not now try, on the same outer cohort:

- 0.5x / 0.25x shrinkage factors;
- ±5% / ±10% / ±20% correction caps;
- different learning rates;
- different epoch counts;
- Huber/SmoothL1 simply because v2 was too aggressive;
- LSTM / TCN / Transformer tournament;
- per-horizon manual correction multipliers.

Those would be increasingly direct post-hoc optimization against five already-exposed events.

Any such number could look good by chance and would have weak scientific meaning.

---

## 8. Recommended next direction

Stop supervised trajectory-model tuning on this exposed 10-event cohort.

Continue work in two evidence-safe directions:

### A. Forward prospective data collection

Keep collecting genuine daily trajectories and independent final attendance outcomes.

The key bottleneck is now clearly **independent labeled events**, not infrastructure.

### B. Target-free trajectory representation research

Use the much larger amount of unlabeled trajectory data for self-supervised tasks such as:

- predict next genuine inventory observation;
- predict short-window inventory change;
- learn trajectory-shape representations without attendance labels.

This can improve the sequence encoder without repeatedly optimizing against the same five attendance outcomes.

Only after the representation is frozen should a small attendance residual head be evaluated on genuinely future events.

---

## 9. Decision

`MECHANISM_NOT_SUPPORTED`

The sequence program itself is **not abandoned**, but the current supervised iteration loop is stopped.

Next sequence work should be:

> **target-free representation learning + future prospective attendance validation**, not more supervised tuning on the exposed cohort.

The structural model remains the incumbent.

---

## 10. Machine-readable evidence

`ml/results/trajectory_lane_b_small_gru_residual_ratio_v2_result.json`

GitHub Actions run:

`40776864173`

Artifact:

`trajectory-lane-b-v2-40776864173`

Artifact SHA256:

`119aff564d431944f792f24c80022cc06258645a5b4e69534f6b19b349e11ca9`

No production change occurred.
