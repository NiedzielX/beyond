# Beyond Ticketing — Model Accuracy Development Instructions v2

Last updated: **2026-10-21**

Status: **CANONICAL DEVELOPMENT INSTRUCTION**

## Objective

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Mandatory constraints:

- event independence;
- PIT safety;
- reproducibility;
- tail risk and bias;
- exposed evidence stays exposed;
- frozen packages are immutable;
- no silent production activation.

A failed challenger closes the challenger, not the workstream.

---

# 1. Current frozen packages

## Track A — final24 prospective validation

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

IDs:

- Pre-Live: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- final24 package: `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

Do not mutate Track A from new outcomes.

## Track B — Pre-Live v3 research anchor

`pre-live-v3-historical-candidate-2026-10-21-v1`

Only T-30 and T-7 differ from v2. T-3/T-1 are identical to v2.

## Track B — early-live long72 research package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Manifest:

`ml/artifacts/d2_long72_stage2_p2_v1/manifest.json`

Scope:

`24 < hours_to_kickoff <= 72`

Exact architecture:

1. frozen T-3 checkpoint anchor;
2. inventory linear extrapolation expert;
3. correction cap `±0.10` occupancy;
4. `P2-observation-maturity` reliability.

P2 reliability:

- observation #1 `0.25`;
- observation #2 `0.60`;
- observation #3+ `1.00`;
- `60<h<=72` time weight `0.75`;
- `48<h<=60` time weight `0.90`;
- `24<h<=48` time weight `1.00`;
- applied reliability = minimum of observation and time weights.

Historical development MAE:

`3707.14 -> 3012.63`, improvement `+694.51 / +18.73%`.

This is research-only, not production.

---

# 2. Final24 equivalence rule

The v2/v3 final24 equivalence audit proved:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Therefore:

- do not create a cosmetic v3 final24 model version;
- do not retrain Ridge/P2 solely because the Pre-Live freeze ID changed;
- final24 Track A remains the existing frozen package.

---

# 3. Long72 data boundary

Frozen long72 dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Data:

- 14 events / 130 rows in 0–72h;
- 24–72h selector slice: 80 rows / 13 events;
- 48–72h: 35 rows / 10 events.

Anchor:

- `0<h<=24` -> T-1;
- `24<h<=72` -> T-3;
- future checkpoint use forbidden.

Same-season b2 state is horizon-specific. A historical match contributes to a checkpoint's residual state only if that checkpoint forecast was actually reconstructable at the PIT cutoff.

Never invent neutral sporting state to make an early-season forecast exist.

---

# 4. Long72 Stage-1 / Stage-2 selection rules

Stage 1 used:

- event-level LOEO;
- event-balanced training/evaluation;
- no random snapshot split;
- exposed historical labels only;
- compact candidate set;
- fixed correction cap.

Stage-1 lead:

`inventory-linear-extrapolation`

Stage 2 kept that expert fixed and only tested deterministic causal reliability policies.

Selected:

`P2-observation-maturity`

It passed the predeclared gates:

- positive uplift overall;
- positive uplift in 24–48h;
- positive uplift in 48–72h;
- >=50% retained raw uplift in each view;
- >=25% worst-degradation reduction overall and in 48–72h;
- >=25% absolute bias reduction;
- positive uplift in both already-exposed temporal subsets.

Do not switch to P4 post hoc merely because its historical tail risk is lower. The selector was frozen before results and chose P2 by overall event-balanced MAE among eligible policies.

---

# 5. Active rule — stop same-sample tuning

The long72 package is frozen.

Do not:

- retune P2 thresholds on the same 13 events;
- add new policies because a later outcome is inconvenient;
- switch to P4 using the already-opened Stage-2 evidence;
- change the expert/cap while keeping the same package ID;
- call exposed historical events unseen validation.

Any material target/model/feature/weight/policy change creates a new challenger and new package ID.

---

# 6. Active next — prospective long72 scoring

For every new eligible event with valid 24–72h PIT trajectory, preserve append-only evidence for:

1. event/kickoff identity;
2. frozen T-3 anchor;
3. raw inventory expert forecast;
4. frozen P2 reliability and forecast;
5. exact source snapshot / as-of lineage;
6. final attendance only after it becomes available;
7. whether the forecast state existed before the label was exposed.

Do not tune the frozen package from these outcomes.

Score:

- event-balanced MAE;
- 24–48h MAE;
- 48–72h MAE;
- bias;
- event improvement rate;
- worst event degradation;
- revision magnitude.

Evidence must remain append-only.

---

# 7. 72–168h rule

The early 72–168h band currently has only 8 independent eligible events.

Predeclared floor:

`N >= 9`

Therefore 72–168h remains diagnostic-only.

Do not lower the threshold.

When the floor is reached:

- freeze exact event/as-of identities first;
- define a PIT-safe T-7 anchor transition before opening results;
- create a new target/package version if semantics change.

---

# 8. Historical / current-season / context rules

Historical model research:

- temporal/event-safe splits only;
- no random split as headline evidence;
- exposed refs never used for variant selection;
- deterministic pinned dependencies;
- report MAE, median AE, tail, bias and stability.

Current-season regimes:

- are anchor-dependent;
- must be rebuilt/revalidated if the anchor changes materially;
- `NO_ADJUSTMENT` remains a valid result.

Context:

- historical c2 remains `NO_CONTEXT_ALL_HORIZONS`;
- forward context may use only genuinely PIT-safe rivalry, absence, sporting, media/search/social signals;
- never backfill later/final-state knowledge.

TSFM:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not reopen through same-data rescue tuning. Reopen only with materially more independent trajectories or a materially different predeclared hypothesis.

---

# 9. Non-negotiable experiment / CI contract

Every material experiment must have:

1. source code;
2. executable CI;
3. pinned runtime/dependencies;
4. syntax/import checks;
5. deterministic seeds where applicable;
6. exact input/data lineage;
7. declared selection/reference/prospective boundary;
8. PIT assertions;
9. frozen benchmark;
10. machine-readable evidence;
11. artifact/run/hash lineage;
12. human result under `ml/results/`;
13. explicit advance/retain/reject/insufficient decision;
14. canonical docs synchronized in the same evidence cycle;
15. no production activation without explicit reviewed promotion.

A seal/freeze job performs no selection. It only verifies and persists an already-selected fixed package.

---

# 10. Promotion boundary

Historical LOEO improvement is not production promotion.

Production requires materially more genuine forward evidence, acceptable tails/bias, reproducible frozen lineage and explicit reviewed activation.

Until then:

`live_adjustment = 0`

## Immediate instruction

> **Keep final24 Track A immutable. Keep Pre-Live v3 and long72 P2 frozen as research packages. Active work is append-only prospective long72 scoring, while 72–168h stays diagnostic until N>=9. Production remains unchanged.**
