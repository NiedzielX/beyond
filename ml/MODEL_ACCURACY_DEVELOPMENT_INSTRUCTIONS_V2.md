# Beyond Ticketing — Model Accuracy Development Instructions v2

Last updated: **2026-10-21**

Status: **CANONICAL DEVELOPMENT INSTRUCTION**

## Objective

> **Reduce forecasting error as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Primary development KPI:

`MAE`

Mandatory constraints:

- tail risk;
- bias;
- event independence;
- point-in-time safety;
- reproducibility;
- honest treatment of exposed evidence;
- no silent production activation.

A failed challenger closes the challenger, not the workstream.

---

# 1. Parallel-track rule

## Track A — frozen validation / promotion evidence

Current frozen forward-evidence stack:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Use it unchanged on new events.

Purpose:

- measure real forward behavior;
- preserve independent evidence;
- support eventual production promotion;
- diagnose component failures without post-hoc tuning.

## Track B — active accuracy R&D

Continue research whenever an honest evaluation boundary exists.

Track B does **not** wait for a fixed prospective event count.

Current research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Active next work:

`d2-v3 Stage 0 exact final-24h anchor equivalence/replay`

> **Production promotion waits for prospective evidence. R&D does not.**

---

# 2. Track-A frozen architecture

## Frozen Pre-Live v2

Freeze:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

Frozen b2:

- T-30 `NO_ADJUSTMENT`;
- T-14 `NO_ADJUSTMENT`;
- T-7 `ewma50-resid-k6-cap05-min3`;
- T-3 `ewma50-resid-k2-cap05-min3`;
- T-1 `ewma50-resid-k6-cap05-min3`.

## Frozen d2

Expert:

`ridge-a10`

Reliability:

`P2-observation-maturity`

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

This package remains immutable during Track-A evidence accumulation.

---

# 3. Track-B frozen Pre-Live v3 research anchor

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Status:

`FROZEN_HISTORICAL_RESEARCH_CANDIDATE`

Production / Track-A replacement:

`false`

## Exact v3 horizon contract

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`, `NO_ADJUSTMENT`;
- T-14: exact v2 T-14 package;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`, `ewma50-resid-k4-cap05-min2`;
- T-3: exact v2 T-3 package;
- T-1: exact v2 T-1 package.

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

## Package evidence

20-cell mean MAE:

- v2 `1934.04`;
- v3 `1924.64`;
- gain `+9.39 / +0.49%`.

T-30 improved v2 in all four rolling folds:

`+5.98 / +33.50 / +54.93 / +29.74`

T-7:

`+10.92 / +11.18 / +13.71 / +27.88`

T-14/T-3/T-1 reproduce v2 exactly.

## Interpretation

V3 is an immutable research anchor, not production and not a replacement for Track-A v2.

The reference seasons are exposed historically and T-30/T-7 still have material event-level tail regressions.

---

# 4. Why package-level validation is mandatory

A promising component is not enough.

Example: the T-1 historical ensemble passed an earlier four-fold anchor-only audit, but after current-season regime revalidation the full candidate package was:

- 2024/25 `+1.92` MAE vs v2;
- 2025/26 `-15.39`.

Therefore v3 retains the exact v2 T-1 package.

General rule:

> **Validate the complete package against the frozen incumbent before creating a new freeze.**

---

# 5. Historical model R&D rules

Required:

- no random split as headline evidence;
- training only on earlier seasons/events;
- development boundary declared before tuning;
- exposed references never used for variant/weight selection;
- PIT-reconstructable features only;
- deterministic pinned dependencies;
- MAE plus median AE, p90/worst event, bias and stability;
- a material target/model/feature/weight/policy change creates a new version.

A freeze/seal job performs **no selection**. It only reproduces an already-selected fixed package and persists hashes/lineage.

---

# 6. Current-season regime rules

A same-season residual regime is anchor-dependent.

If the historical anchor changes, do not silently inherit the prior b2 policy.

Recalculate residual state relative to the new anchor and revalidate the policy under the declared historical boundary.

`NO_ADJUSTMENT` is always a valid outcome when the regime layer does not add stable incremental value.

V3 demonstrated this:

- T-30 -> `NO_ADJUSTMENT`;
- T-7 -> policy changed from v2 `k6/min3` to v3 `k4/min2`;
- T-3/T-1 retained exact v2 packages.

---

# 7. c2/context rules

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

Forward context R&D is allowed when sources are genuinely PIT-safe, e.g.:

- verified rivalry/derby;
- verified absences/suspensions;
- expected XI/key-player availability;
- sporting context;
- media attention;
- valid search/social/hype signals.

Never reconstruct historical context from later/final-state knowledge.

---

# 8. d2-v3 rule — prove anchor difference before retraining

The current d2 final-24h model was trained against Frozen Pre-Live v2.

V3 changes T-30 and T-7, but **T-1 is exactly unchanged from v2**.

Therefore do not assume a new d2 target exists merely because the Pre-Live freeze ID changed.

## Stage 0 mandatory equivalence replay

On the exact frozen 9-event / 30-row d2 development set, reconstruct per row:

1. v2 anchor;
2. v3 anchor;
3. seat delta;
4. occupancy-share delta;
5. v2 live residual target;
6. v3 live residual target.

Hard assertions:

- exact event/as-of row identity;
- exact capacities and outcome labels;
- no future interpolation/outcome leakage;
- no newly completed event enters model selection.

Predeclared hypothesis:

`v3_anchor == v2_anchor on all final-24h d2 rows`

because the existing final-24h anchor may resolve to T-1.

### If exact equivalence holds

Decision:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Then:

- do not rerun a cosmetic Stage-1 tournament;
- retain existing d2 target/model lineage for the final-24h problem;
- next R&D must be materially different: longer live horizon, new target, learned reliability or richer PIT-safe live features.

### If anchors differ

Create a new `d2-v3` target and model/policy IDs, then rerun Stage 1 / Stage 2.

---

# 9. If d2-v3 target differs — Stage 1

Benchmark:

`v3-zero-correction`

External comparator:

frozen v2/Ridge/P2.

Rules:

- event is the independent unit;
- LOEO / event-balanced evaluation;
- no random snapshot split;
- compact materially distinct candidate set;
- no same-data TSFM rescue tuning;
- correction caps and preprocessing declared before evaluation.

A changed target alone creates a new model identity even if Ridge alpha 10 wins again.

---

# 10. Reliability / tail governance

If a new Stage-1 expert is warranted, reliability must be revalidated under a new policy ID.

Possible PIT-safe signals:

- observation count/span;
- time to kickoff;
- correction magnitude;
- live velocity/acceleration;
- stability/data-quality state;
- disagreement magnitude.

Existing P2 remains a benchmark, not an inherited policy.

---

# 11. TSFM boundary

Stage-1 Chronos-2 and Bolt-small did not beat plain Ridge.

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

No same-data rescue tuning and no automatic model zoo.

Reopen only with materially more independent trajectories or a materially different predeclared target/use.

---

# 12. Prospective evidence classes

Track-A cutoff:

`2026-10-19T19:11:01Z`

- `DELAYED_LABEL_HOLDOUT`: diagnostics, not genuine forward promotion N;
- `TRUE_POST_FREEZE_PROSPECTIVE`: may contribute to production-promotion evidence.

Never combine them into one headline prospective sample size.

New Track-A outcomes remain exposed and cannot later be called unseen validation for a tuned package.

---

# 13. Data-quality blockers

Missing attendance, capacity, fixture or source coverage is a data-contract problem.

Rules:

- repair trusted source coverage;
- record provenance;
- never infer attendance from inventory;
- do not use blockers as a reason to pause unrelated Track-B R&D.

---

# 14. Non-negotiable experiment/CI contract

Every material experiment must have:

1. source code;
2. executable CI workflow;
3. pinned runtime/dependencies;
4. syntax/import checks;
5. deterministic seeds where applicable;
6. exact input/data lineage;
7. explicit selection/reference boundary;
8. PIT assertions;
9. frozen incumbent benchmark;
10. machine-readable evidence;
11. artifact/run/hash lineage;
12. human-readable result under `ml/results/`;
13. explicit advance/retain/reject/insufficient decision;
14. canonical docs synchronized in the same evidence cycle;
15. no production activation unless explicitly reviewed.

---

# 15. Promotion boundary

Historical/LOEO improvement is not production promotion.

Production requires materially more genuine prospective evidence, positive aggregate uplift, acceptable tails/bias, a reproducible frozen package and explicit reviewed promotion.

Until then:

`live_adjustment = 0`

## Immediate instruction

> **Keep v2/Ridge/P2 frozen for Track-A evidence. Pre-Live v3 is sealed as the Track-B research anchor. Run d2-v3 Stage 0 exact final-24h anchor equivalence before retraining anything; only create a new d2-v3 model target if the anchor actually differs. Production remains unchanged.**
