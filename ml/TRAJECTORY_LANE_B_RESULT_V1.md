# Beyond Ticketing — Trajectory Lane B Result v1

Date: **2026-10-28**

Status: **DO NOT ADVANCE / RETAIN AS DIAGNOSTIC EVIDENCE**

Precommit: `trajectory-lane-b-small-gru-residual-v1`

Evidence class: `historical_exposed_research`

Production impact: **none**

`live_adjustment = 0`

---

## 1. Human summary

Lane B v1 answered the sequence question more positively than Lane A, but it still did **not** beat the structural incumbent.

Strict-forward event-balanced result:

- structural incumbent MAE: **2594.54**;
- frozen Lane A MAE: **4153.34**;
- Lane B small-GRU MAE: **2595.40**;
- Lane B vs incumbent: **+0.87 MAE worse**;
- Lane B vs Lane A: **-1557.94 MAE better**;
- independent outer test events: **5**;
- outer test prefix rows: **14**;
- event improvement rate vs incumbent: **40%**.

Decision:

> **Lane B v1 does not advance. It almost exactly reproduces the structural incumbent but does not improve it.**

This is importantly different from Lane A's failure. Lane A materially damaged the forecast. Lane B learned to make almost no correction at all.

---

## 2. Result by horizon

| Horizon | Events | Incumbent MAE | Lane B MAE | Delta MAE |
|---|---:|---:|---:|---:|
| T-7 | 4 | 3399.03 | 3399.83 | **+0.81** |
| T-3 | 5 | 2667.93 | 2668.20 | **+0.27** |
| T-1 | 5 | 2314.89 | 2315.89 | **+1.00** |

Lane B is extremely close to the incumbent at every evaluable horizon, but slightly worse at all three.

---

## 3. Result by independent event

| Event ID | Incumbent event MAE | Lane B event MAE | Delta MAE |
|---:|---:|---:|---:|
| 20 | 407.86 | 411.29 | **+3.42** |
| 10 | 1786.65 | 1785.39 | **-1.27** |
| 23 | 6732.88 | 6735.77 | **+2.89** |
| 21 | 975.08 | 971.81 | **-3.27** |
| 22 | 3070.21 | 3072.75 | **+2.55** |

Two of five independent events improve; three degrade slightly.

Worst event degradation:

**+3.42 MAE**.

This downside is tiny compared with Lane A, but there is still no net gain.

---

## 4. Seed stability

Frozen seeds:

`17 / 29 / 41`

Diagnostics:

- median prediction spread across seeds: **1.50 seats**;
- maximum spread: **2.63 seats**.

Interpretation:

> **The result is highly stable across seeds.**

The model did not fail because one random initialization produced a bad model.

---

## 5. Critical diagnostic: the model learned almost zero residual

The actual attendance residual target is often hundreds or thousands of seats away from structural P50.

However, Lane B predicted residual corrections only around:

**-0.06 to +4.33 seats**.

Examples:

- event20 T-1: **+3.29**;
- event20 T-3: **+3.56**;
- event10 T-7: **-0.06**;
- event22 T-1: **+4.33**.

Therefore Lane B's final forecast is practically:

`challenger P50 ≈ structural P50`

This explains why its MAE almost exactly matches the incumbent.

---

## 6. What this result supports

The evidence supports the following statements:

1. **Lane B v1 is much safer than Lane A v1.** It does not introduce the large harmful corrections seen in Ridge.
2. **The GRU training is deterministic/stable enough under the frozen seeds.** Seed variance is tiny.
3. **Lane B v1 does not demonstrate useful incremental trajectory signal yet.** It does not beat the incumbent.
4. **The first Lane B training formulation appears unable to learn the scale of the residual correction.**

The fourth point is a mechanistic diagnosis, not a proven causal fact. The strongest evidence is that targets are on the scale of hundreds/thousands of seats while the learned output remains near zero despite stable training.

---

## 7. Most plausible v1 failure mechanism

Lane B v1 directly predicts the raw seat residual:

`actual attendance - structural P50`

The residual target can be several thousand seats.

The frozen learner starts with neural outputs near zero and uses:

- L1 loss;
- learning rate 0.001;
- 200 fixed epochs;
- very small network;
- very small independent-event sample.

For L1 loss, gradient magnitude does not grow with the size of the target error in the same way squared-error gradients do.

A plausible result is exactly what we observe: the network moves consistently but only by a few seats, never reaching the scale of the true residual.

This does **not** prove that sequence representation contains useful attendance signal. It means v1 did not provide a meaningful test of residual magnitude learning.

---

## 8. Decision

`DO_NOT_ADVANCE`

Do not:

- increase epochs after seeing this result and still call it v1;
- increase learning rate after seeing this result and still call it v1;
- select a different seed;
- switch to LSTM/TCN/Transformer on the same outer outcomes as an unversioned retry;
- add context features to repair v1;
- claim Lane B beat the incumbent.

The correct next step is a **new versioned hypothesis**, not post-result tuning.

---

## 9. Recommended next hypothesis

The cleanest next experiment changes one major mechanism only:

> **Normalize the residual target to a dimensionless ratio before training, while keeping the sequence representation and small-GRU architecture fixed.**

Example:

`residual_ratio = (actual_attendance - structural_p50) / structural_p50`

At inference:

`seat_residual = predicted_residual_ratio * structural_p50`

Why this is attractive:

- deterministic scaling;
- no full-dataset target statistic is needed;
- no fold leakage from a learned target scaler;
- target becomes closer to O(0.1) rather than O(1000);
- architecture, optimizer, seeds and sequence representation can remain unchanged;
- it directly tests the observed v1 failure mode instead of launching a model tournament.

Any such experiment must be **Lane B v2** and the existing 5 outer events are already exposed, so its result is diagnostic historical research evidence, not unseen confirmation.

---

## 10. Machine-readable evidence

`ml/results/trajectory_lane_b_small_gru_residual_v1_result.json`

GitHub Actions run:

`40775838909`

Artifact:

`trajectory-lane-b-v1-40775838909`

Artifact SHA256:

`80e63f28a35c4a2a95c9fd908f3a85c1fcf9e9dc153411bd2ce9edb773ff5293`

No production change occurred.
