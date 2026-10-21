# a2 External/Ensemble Fixed-Temporal Robustness Audit v1 — Result

Date: **2026-10-21**

Status: **COMPLETED / T-30, T-7 AND T-1 PASS 4/4 ROLLING FOLDS / NO FROZEN OR PRODUCTION CHANGE**

Canonical contract:

`ml/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1.md`

Parent closure result:

`ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`

Workflow run:

`39625425854`

Job:

`119309266943`

Artifact:

`a2-external-ensemble-fixed-temporal-v1-39625425854`

Artifact ID:

`12356632426`

Artifact ZIP SHA256:

`7d9cfe2609affcb35b7c99252d42231ce1e5e55b24fbb3bb1dfd3470a0226e4e`

Result JSON SHA256:

`e6532db4bccfe567dd1eeaf3196f74d1a41a78a66eea53bc975892868ff2c900`

Run head SHA:

`55987d826fe25b486deeda281db3c7e7d44238e1`

## Runtime

Pinned runtime passed:

- NumPy `2.3.5`;
- pandas `2.2.3`;
- scikit-learn `1.8.0`;
- joblib `1.5.3`;
- CatBoost `1.2.10`;
- LightGBM `4.7.0`;
- XGBoost `3.4.1`.

Compile checks and unit checks passed.

## Protocol

No tuning or model selection occurred in this audit.

The exact contracts selected by the closure audit were replayed unchanged across four rolling folds:

1. train `2021/22` -> test `2022/23` — additional pre-selection historical fold;
2. train `2021/22 + 2022/23` -> test `2023/24` — original development-selection season;
3. train through `2023/24` -> test `2024/25` — exposed reference;
4. train through `2024/25` -> test `2025/26` — exposed reference.

The exact closure-run MAEs for folds 2-4 were hard reproduction gates at tolerance `1e-9`.

Decision gate:

`positive MAE improvement in all four rolling folds`

Paired bootstrap:

`10,000 samples per fold`

Important evidence caveat:

2024/25 and 2025/26 were already exposed reference seasons. This audit tests temporal consistency of a fixed contract; it does not turn those seasons back into unseen holdouts.

## Overall result

All three fixed candidates passed the predeclared 4/4 positive-MAE gate:

- **T-30 PASS**;
- **T-7 PASS**;
- **T-1 PASS**.

No horizon failed the exact rolling-fold gate.

This promotes them only to **robust historical challenger status**. It does not mutate current a2, Frozen Pre-Live v2 or production.

---

# T-30

Fixed contract:

`0.75 current a2 + 0.25 XGBoost depth3`

| Test season | Current a2 MAE | Candidate MAE | Improvement | Bootstrap P(improvement > 0) |
|---|---:|---:|---:|---:|
| 2022/23 | 2,157.15 | 2,151.17 | **+5.98** | 0.6353 |
| 2023/24 | 2,559.74 | 2,526.25 | **+33.50** | 0.9326 |
| 2024/25 | 1,889.37 | 1,834.43 | **+54.93** | 0.9952 |
| 2025/26 | 1,846.28 | 1,816.54 | **+29.74** | 0.9610 |

Summary:

- positive folds: **4/4**;
- mean fold MAE improvement: **+31.04**;
- relative mean improvement: **1.47%**;
- minimum fold improvement: **+5.98**;
- minimum bootstrap probability: **0.6353**;
- club-season cells improved: **50/72 = 69.44%**;
- maximum worst-event degradation across folds: **2,855.70 seats**.

Decision:

`ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`

Interpretation:

T-30 is the strongest of the three historical challengers on aggregate consistency and club-season breadth, but the average gain is still modest and event-level tail degradation remains material.

---

# T-7

Fixed contract:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

| Test season | Current a2 MAE | Candidate MAE | Improvement | Bootstrap P(improvement > 0) |
|---|---:|---:|---:|---:|
| 2022/23 | 1,984.99 | 1,964.81 | **+20.18** | 0.8630 |
| 2023/24 | 2,317.34 | 2,308.44 | **+8.90** | 0.6612 |
| 2024/25 | 1,650.97 | 1,640.70 | **+10.27** | 0.6728 |
| 2025/26 | 1,773.80 | 1,745.94 | **+27.86** | 0.9448 |

Summary:

- positive folds: **4/4**;
- mean fold MAE improvement: **+16.80**;
- relative mean improvement: **0.87%**;
- minimum fold improvement: **+8.90**;
- minimum bootstrap probability: **0.6612**;
- club-season cells improved: **42/72 = 58.33%**;
- maximum worst-event degradation across folds: **1,632.41 seats**.

Decision:

`ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`

Interpretation:

T-7 is directionally consistent across all four folds and has the smallest maximum tail degradation of the three passing challengers, but its mean uplift is below 1%.

---

# T-1

Fixed contract:

`0.25 HGB hist31 + 0.50 CatBoost depth4 + 0.25 LightGBM leaves15`

| Test season | Current a2 MAE | Candidate MAE | Improvement | Bootstrap P(improvement > 0) |
|---|---:|---:|---:|---:|
| 2022/23 | 1,913.99 | 1,897.51 | **+16.48** | 0.6946 |
| 2023/24 | 2,347.99 | 2,292.53 | **+55.46** | 0.9602 |
| 2024/25 | 1,651.73 | 1,649.47 | **+2.27** | 0.5196 |
| 2025/26 | 1,742.84 | 1,736.56 | **+6.28** | 0.6123 |

Summary:

- positive folds: **4/4**;
- mean fold MAE improvement: **+20.12**;
- relative mean improvement: **1.05%**;
- minimum fold improvement: **+2.27**;
- minimum bootstrap probability: **0.5196**;
- club-season cells improved: **38/72 = 52.78%**;
- maximum worst-event degradation across folds: **2,309.70 seats**.

Decision:

`ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`

Interpretation:

T-1 passes the predeclared gate, but the two exposed-reference gains are very small and the weakest fold has bootstrap support close to 0.5. Treat this as a legitimate candidate, not a proven large improvement.

---

# Decision

The bounded a2 external-family/heterogeneous-ensemble gap is now closed.

Historical challenger outcome:

- T-30: **robust challenger**;
- T-14: current a2 retained;
- T-7: **robust challenger**;
- T-3: current a2 retained;
- T-1: **robust challenger with weak effect-size caveat**.

The correct next R&D step is **not** to overwrite Frozen Pre-Live v2.

Instead start a separately versioned Pre-Live v3 challenger cycle with the historical layer:

- T-30 -> exact robust ensemble;
- T-14 -> current a2 base;
- T-7 -> exact robust ensemble;
- T-3 -> current a2 base;
- T-1 -> exact robust ensemble.

Before a Pre-Live v3 freeze can exist, the current-season regime must be revalidated against the new anchors. Existing b2 residual policies were derived relative to the old historical bases and cannot be silently carried over.

Required next experiment:

> **Pre-Live v3 / current-season-regime revalidation on the new robust historical anchors.**

That cycle must compare:

1. new historical base only;
2. existing frozen b2 policy applied to the new anchor as a fixed comparator;
3. newly selected current-season-regime challenger under a declared historical temporal boundary;
4. Frozen Pre-Live v2 as the unchanged benchmark.

Only after the new anchor + regime package passes its own historical/fixed-temporal gates may it receive a new freeze ID.

The frozen d2 Ridge/P2 package remains attached to Frozen Pre-Live v2 for Track-A prospective evidence. If Pre-Live v3 is later frozen, d2 must be rebuilt/revalidated against that new anchor under a new d2 version rather than silently reusing the old live expert.

## Production boundary

Always:

- current a2 frozen state unchanged;
- Frozen Pre-Live v2 unchanged;
- frozen b2 unchanged;
- historical c2 remains `NO_CONTEXT_ALL_HORIZONS`;
- frozen Ridge/P2 unchanged;
- `production_change = false`;
- production `live_adjustment = 0`.
