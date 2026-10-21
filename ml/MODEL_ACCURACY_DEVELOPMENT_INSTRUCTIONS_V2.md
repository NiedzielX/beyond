# Beyond Ticketing — Model Accuracy Development Instructions v2

Last updated: **2026-10-21**

Status: **CANONICAL DEVELOPMENT INSTRUCTION — ALIGNED TO `ml/MAE_RESEARCH_ROADMAP_V3.md`**

## Objective

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with honest, reproducible, point-in-time-safe evidence.**

Mandatory constraints:

- event / fixture independence;
- time-respecting validation;
- PIT safety;
- reproducibility;
- explicit evidence classes;
- frozen packages are immutable;
- no silent production activation.

A failed challenger closes the challenger, not the workstream.

---

# 1. Primary metric hierarchy

Primary selector:

- event/fixture-balanced MAE at the target horizon or predeclared horizon aggregate.

Required guardrails:

- median absolute error;
- P90 absolute error;
- signed bias;
- worst-event degradation;
- event-improvement rate;
- per-club stability;
- per-fold / per-season stability.

Guardrails may reject an unsafe challenger, but they must not replace MAE as the hidden primary objective.

---

# 2. Current frozen packages

## Final24

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Do not mutate from prospective outcomes.

## Pre-Live v3

`pre-live-v3-historical-candidate-2026-10-21-v1`

Research-only.

## Long72

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Exact architecture:

1. frozen T-3 anchor;
2. inventory-linear-extrapolation;
3. `±0.10` occupancy cap;
4. P2 observation-maturity reliability.

Historical development MAE:

`3707.14 -> 3012.63`, improvement `+694.51 / +18.73%`.

Do not retune on the same 13 development events.

---

# 3. Historical/global baseline

Global Model v2.1 is the current strong structural research baseline:

- 1,530 Ekstraklasa matches;
- five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- residual architecture: club-history baseline + global learned correction.

2024/25 and 2025/26 are already exposed research evidence. Never label them unseen for new variants.

---

# 4. Validation rules

## Historical/global challengers

Required:

- season-blocked or rolling/expanding-origin validation;
- future seasons/events never enter earlier training folds;
- fold definitions are persisted as artifacts;
- report per horizon, fold/season and club;
- no random row split as headline evidence.

## Live-ticket challengers

Required:

- complete event is the independent unit;
- LOEO may be used as a diagnostic;
- add forward-event validation ordered by kickoff;
- no random snapshot split as headline evidence.

## Selection-bias rule

Do not repeatedly optimize a large candidate space against the same evaluation matrix. Prefer small, hypothesis-driven tournaments with predeclared selectors.

---

# 5. Loss alignment

Because the primary point-forecast metric is MAE, every serious tournament must include MAE-native candidates when technically feasible:

- LAD / median regression;
- quantile regression `q=0.50`;
- tree boosting with absolute-error / quantile objective.

Squared-error models may remain challengers/controls if they empirically reduce future MAE.

Training loss is not itself the business KPI; out-of-sample MAE remains the decision metric.

---

# 6. Forecast combination rules

Forecast combinations are first-class challengers when component forecasts contain genuinely different information.

Test in order:

1. simple mean;
2. median;
3. fixed convex weights;
4. MAE-optimized convex weights;
5. regularized stacker only if simpler blends fail.

Rules:

- weights are learned only within training folds;
- the evaluation fold cannot influence weights;
- components should not be cosmetic hyperparameter variants only;
- always compare to the best single component.

---

# 7. Context rules

Existing useful context inside the global model includes attendance history, opponent demand, timing/seasonality, sporting state and home-opponent history.

Priority new PIT-safe hypotheses:

1. next-home-fixture substitution/cannibalization;
2. fixture density / spacing;
3. verified absences known at `as_of_at`;
4. rivalry / match stakes known at `as_of_at`;
5. forecast weather available at the PIT cutoff;
6. PIT-safe search/media/social attention.

Every new family requires controlled ablation versus the same incumbent and fold structure.

Never use:

- realized future weather for an earlier forecast;
- final table state at an earlier point;
- later-announced absences;
- hindsight labels encoded as context.

---

# 8. Live-ticket rules

Live inventory is a demand proxy, not automatically confirmed sales.

The main scientific question is incremental value over the strongest structural forecast:

`structural forecast -> residual live correction -> reliability/shrinkage -> final challenger`

Always compare:

- structural only;
- structural + raw live correction;
- structural + gated live correction;
- structural + context + live combination where justified.

---

# 9. Uncertainty around MAE improvement

For every serious challenger report uncertainty for `ΔMAE`.

Independent resampling unit:

- event/fixture, not trajectory row.

Required outputs:

- incumbent MAE;
- challenger MAE;
- absolute `ΔMAE`;
- relative `ΔMAE`;
- block/event interval for `ΔMAE`;
- event-improvement rate;
- per-club distribution.

Do not claim precision from a small live sample based only on a point estimate.

---

# 10. 72–168h rule

At last audit only `8` independent events had valid data beyond 72h.

Research-start floor:

`N>=9`

When reached:

- freeze exact event/as-of identities first;
- define PIT-safe T-7 anchor transition;
- begin with simple/regularized models;
- include MAE-native objectives;
- evaluate with event-safe and forward-event views;
- use a new challenger/package ID.

`N=9` starts research; it is not a promotion gate.

---

# 11. Non-negotiable experiment / CI contract

Every material experiment must have:

1. explicit hypothesis;
2. source code;
3. executable CI;
4. pinned runtime/dependencies;
5. deterministic seeds where applicable;
6. exact data lineage / hashes;
7. declared target and PIT semantics;
8. target-leakage assertions;
9. as-of/kickoff ordering assertions;
10. persisted train/evaluation fold identities;
11. frozen incumbent benchmark;
12. machine-readable scorecard;
13. artifact/run/hash lineage;
14. human-readable result under `ml/results/`;
15. explicit advance / retain / reject / insufficient decision;
16. canonical docs synchronized in the same evidence cycle;
17. no production activation without explicit reviewed promotion.

A freeze/seal job performs no selection. It verifies and persists an already-selected package.

---

# 12. Evidence labels

Use only explicit evidence classes such as:

- `historical_exposed_research`;
- `historical_forward_fold`;
- `delayed_label_precommitted`;
- `true_post_freeze_prospective`.

Do not use “unseen” for data that has already influenced model or feature decisions.

---

# 13. Immediate instruction

> **Keep frozen final24/long72 packages immutable for evidence. In parallel, optimize new challengers for true MAE using forward validation, MAE-native losses, PIT-safe feature ablations and forecast combinations over the strongest structural/global model.**
