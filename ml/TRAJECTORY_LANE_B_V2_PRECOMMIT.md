# Beyond Ticketing — Trajectory Lane B v2 Precommit

Precommit date: **2026-10-28**

Status: **PRECOMMITTED MECHANISM DIAGNOSTIC / HISTORICAL EXPOSED RESEARCH ONLY**

Precommit ID:

`trajectory-lane-b-small-gru-residual-ratio-v2`

Production impact: **none**

`live_adjustment = 0`

References:

- `ml/TRAJECTORY_LANE_B_RESULT_V1.md`;
- `ml/TRAJECTORY_LANE_B_PRECOMMIT_V1.md`;
- `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`;
- `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`.

---

# 1. Why v2 exists

Lane B v1 was technically stable but learned almost no seat correction:

- incumbent event-balanced MAE: **2594.54**;
- Lane B v1 MAE: **2595.40**;
- Delta vs incumbent: **+0.87**;
- median seed spread: **1.50 seats**;
- predicted residual corrections were only about **-0.06 to +4.33 seats** while true residuals were commonly hundreds/thousands of seats.

The narrow v2 hypothesis is:

> **v1's raw-seat residual target is poorly scaled for the frozen small-GRU/L1 optimization setup; converting the target to a dimensionless residual ratio should allow the same model to learn non-trivial correction magnitude.**

This hypothesis does **not** claim that trajectory sequence information is useful. It tests whether v1 failed before that question could be meaningfully answered.

---

# 2. Evidence status

The 10-event development cohort and its 5 strict-forward outer test events have already been exposed through Lane A v1 and Lane B v1.

Therefore every v2 result on this same cohort is explicitly:

`historical_exposed_research`

It is **diagnostic**, not unseen validation and not prospective evidence.

Even a strong v2 result cannot be called promotion-grade proof.

If v2 supports the mechanism hypothesis, the next valid step is to freeze a candidate and evaluate it on genuinely future immutable predictions/outcomes.

---

# 3. Frozen cohort and folds

Use exactly:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled independent events;
- 19 persisted checkpoint rows;
- 5 strict-forward outer test events;
- frozen fold-registry SHA256:
  `fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`.

Do not add or remove events/cutoffs for v2.

All event-prefix grouping and strict-forward rules remain unchanged.

---

# 4. Information boundary

Use exactly the same Lane B v1 input representation and global context.

No new:

- trajectory channel;
- context feature;
- odds;
- weather;
- media/hype;
- match stakes;
- club/event identity;
- capacity-normalized sequence information beyond the frozen v1 implementation semantics.

The Lane B v1 implementation note remains applicable.

---

# 5. The only material modelling change

## v1 target

`seat_residual = actual_attendance - structural_p50`

## v2 target

`residual_ratio = (actual_attendance - structural_p50) / structural_p50`

Eligibility addition:

`structural_p50 > 0`

At inference:

`predicted_seat_residual = predicted_residual_ratio * structural_p50`

and:

`challenger_p50 = structural_p50 + predicted_seat_residual`

Physical clipping remains:

- lower bound 0;
- upper bound verified stadium capacity when available.

No target clipping/winsorization is added in v2.

---

# 6. Why ratio scaling is selected

Residual ratio is deterministic for each labeled training row and does not require fitting a target scaler from the full dataset.

Benefits:

- converts targets from O(1000 seats) toward a dimensionless O(0.1) scale;
- preserves sign and relative correction magnitude;
- avoids a learned global target mean/std that could create additional fold semantics;
- keeps the architecture and optimization protocol unchanged;
- isolates the observed v1 scale/optimization failure mode.

This is preferable to simultaneously changing learning rate, epochs, loss function and architecture.

---

# 7. Frozen architecture and optimization

Keep v1 unchanged:

- PyTorch;
- one-layer GRU;
- input dimension 5;
- hidden dimension 8;
- one 8-unit ReLU MLP head;
- dropout 0.20;
- AdamW;
- learning rate `0.001`;
- weight decay `0.01`;
- weighted L1 loss, now on `residual_ratio`;
- fixed 200 epochs;
- gradient clipping 1.0;
- seeds `[17, 29, 41]`;
- median prediction across the three seeds;
- no early stopping;
- no architecture/hyperparameter search.

Event-balanced row weights remain:

`1 / eligible_prefix_count_for_event`

---

# 8. Primary diagnostic questions

V2 should answer:

1. Does target scaling produce materially non-zero predicted seat residuals?
2. Does it materially change MAE relative to Lane B v1?
3. Does it beat the structural incumbent on the exposed strict-forward cohort?
4. Is the result stable across the same frozen seeds?

The key mechanism check is not only MAE. Persist the distribution/range of predicted residual ratios and mapped seat residuals.

---

# 9. Scoring

Report:

- incumbent event-balanced MAE;
- frozen Lane A v1 MAE;
- frozen Lane B v1 MAE;
- Lane B v2 event-balanced MAE;
- Delta v2 vs incumbent;
- Delta v2 vs Lane B v1;
- Delta v2 vs Lane A;
- independent events / rows;
- MAE by horizon;
- event improvement rate;
- worst event degradation;
- seed spread;
- min/median/max predicted ratio;
- min/median/max mapped seat residual.

Aggregation remains event-balanced exactly as v1.

---

# 10. Diagnostic decision rule

## `MECHANISM_SUPPORTED`

Use only if:

- v2 predictions are no longer collapsed near zero;
- seed behavior remains acceptably stable;
- v2 improves materially over v1 on the exposed cohort;
- no evidence guard fails.

This does **not** mean the model is validated. It means the target-scaling mechanism is worth freezing for future prospective testing.

## `MECHANISM_NOT_SUPPORTED`

Use if:

- outputs remain effectively collapsed;
- v2 does not improve meaningfully over v1;
- or scaling creates unstable/harmful corrections.

Then do not launch a broad neural model sweep. Reassess the sequence/data hypothesis first.

---

# 11. Non-negotiable guards

- same 10 events / 19 checkpoint identities as v1;
- same strict-forward fold registry;
- same sequence representation;
- same global context;
- same architecture;
- same optimizer/lr/wd/epochs;
- same seeds;
- only the target/output scaling mechanism changes materially;
- no target value enters inference features;
- no future trajectory;
- no production activation;
- all v2 results labeled `historical_exposed_research`.
