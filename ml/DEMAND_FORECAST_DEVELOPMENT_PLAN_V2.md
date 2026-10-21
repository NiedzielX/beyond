# Beyond Ticketing — Demand Forecast Development Plan v2

Last updated: **2026-10-21**

Status: **CANONICAL ACCURACY ROADMAP**

Canonical rules:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

Historical strategy baseline:

`ml/MODEL_DEVELOPMENT_STRATEGY.md`

Frozen prospective contract:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

Latest completed historical evidence:

- `ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`;
- `ml/results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md`.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Two rules are equally important:

1. a frozen champion/evidence package must not be mutated from exposed outcomes;
2. **R&D must not wait for prospective sample-count gates when honest historical or newly predeclared research is available now.**

A failed challenger closes the challenger, not the workstream.

---

# 1. Two parallel tracks — mandatory

## Track A — Frozen validation / promotion evidence

Frozen stack:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Track A:

- keeps Frozen Pre-Live v2 unchanged;
- keeps `ridge-a10` unchanged;
- keeps `P2-observation-maturity` unchanged;
- scores completed events append-only;
- separates `DELAYED_LABEL_HOLDOUT` from `TRUE_POST_FREEZE_PROSPECTIVE`;
- builds eventual production-promotion evidence.

## Track B — Active accuracy R&D

Track B continues now whenever an honest evaluation boundary can be declared.

It does **not** wait for a fixed number of new prospective events.

Requirements:

- new candidate/version ID;
- explicit train/development/reference boundary before tuning;
- exposed events remain labeled exposed;
- frozen Track-A stack retained as benchmark;
- no silent production write.

> **Production promotion waits for prospective evidence. R&D does not.**

---

# 2. Current frozen Track-A state

Frozen Pre-Live ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Frozen d2 package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Production:

`live_adjustment = 0`

Frozen Pre-Live v2:

| Horizon | Historical base | b2 | c2 | Frozen reference mean MAE |
|---|---|---|---|---:|
| T-30 | Structural Prior | no adjustment | no context | 1,867.82 |
| T-14 | Structural Prior | no adjustment | no context | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | no context | 1,691.40 |
| T-3 | Structural Prior | `ewma50-resid-k2-cap05-min3` | no context | 1,682.63 |
| T-1 | Structural Prior | `ewma50-resid-k6-cap05-min3` | no context | 1,661.52 |

No Track-B experiment silently mutates this freeze.

---

# 3. a2 external-family / ensemble closure — COMPLETE

The missing all-horizon external-family question is closed.

Closure run:

`39624170933`

Result:

- T-30 -> robustness;
- T-7 -> robustness;
- T-1 -> robustness;
- T-14 -> retain current a2 after mixed reference signal;
- T-3 -> retain current a2 after mixed reference signal.

---

# 4. a2 fixed-temporal robustness — COMPLETE

Run:

`39625425854`

Artifact:

`12356632426`

Result JSON SHA256:

`e6532db4bccfe567dd1eeaf3196f74d1a41a78a66eea53bc975892868ff2c900`

Exact selected contracts were replayed unchanged across four rolling folds.

## T-30

Contract:

`0.75 current a2 + 0.25 XGBoost depth3`

Fold MAE gains:

`+5.98 / +33.50 / +54.93 / +29.74`

Mean:

`+31.04 / 1.47%`

Decision:

`ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`

## T-7

Contract:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Fold gains:

`+20.18 / +8.90 / +10.27 / +27.86`

Mean:

`+16.80 / 0.87%`

Decision:

`ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`

## T-1

Contract:

`0.25 HGB hist31 + 0.50 CatBoost depth4 + 0.25 LightGBM leaves15`

Fold gains:

`+16.48 / +55.46 / +2.27 / +6.28`

Mean:

`+20.12 / 1.05%`

Decision:

`ROBUSTNESS_PASS_ALL_ROLLING_FOLDS_POSITIVE`

T-1 remains a weak-effect challenger: minimum bootstrap P(improvement > 0) was `0.5196` and the exposed-reference gains are tiny.

All three passing contracts are **robust historical challengers**, not frozen replacements.

The bounded a2 external/ensemble workstream is now closed.

---

# 5. Track B priority 1 — Pre-Live v3 challenger — ACTIVE NOW

Proposed historical v3 base:

| Horizon | Candidate historical base |
|---|---|
| T-30 | robust T-30 ensemble |
| T-14 | current a2 Structural Prior |
| T-7 | robust T-7 ensemble |
| T-3 | current a2 Structural Prior |
| T-1 | robust T-1 ensemble |

This is not yet a frozen package.

## Mandatory current-season-regime revalidation

Existing b2 policies were fitted/selected against the old historical bases. They must not be silently carried into v3.

The next versioned experiment must compare:

1. new robust historical base only;
2. existing frozen b2 formulation applied unchanged to the new anchor as a fixed comparator;
3. a newly selected current-season-regime challenger under a declared historical temporal split;
4. Frozen Pre-Live v2 as unchanged benchmark.

Selection must not use event-5 or later prospective/delayed-label d2 outcomes.

## v3 advancement requirements

A Pre-Live v3 candidate must:

- improve the relevant horizon/season MAE under the declared temporal protocol;
- pass a fixed-temporal robustness audit;
- preserve exact model/source/version lineage;
- quantify tail risk and bias;
- receive a new freeze ID only after the complete package is reproducible.

If the b2 layer does not add stable value on a new anchor, v3 may legitimately choose no current-season adjustment for that horizon.

---

# 6. Track A — frozen d2 validation continues in parallel

Stage-1 expert:

`ridge-a10`

Development:

- Frozen-v2 latest MAE `4128.01`;
- Ridge latest MAE `3320.39`;
- uplift `807.62 / 19.56%`;
- Ridge window `3619.19`;
- worst latest-event degradation `4326.90`.

Stage-2 package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Development:

- latest MAE `3240.99`;
- uplift vs Frozen `887.02 / 21.49%`;
- window MAE `3657.65`;
- worst degradation `1081.72`.

Event 5 is permanently exposed.

Delayed-label diagnostics such as GKS–Pogoń and Cracovia–Legia remain diagnostic only and cannot trigger post-hoc changes to frozen Ridge/P2.

---

# 7. d2 after Pre-Live v3

Do not silently attach the current live expert to a new anchor.

If Pre-Live v3 later freezes:

1. create a new d2 version;
2. rebuild/revalidate the live residual target relative to v3;
3. retest candidate live experts/reliability under a declared boundary;
4. retain v2/Ridge/P2 as frozen Track-A comparator.

Separately versioned d2 hypotheses may include:

- remaining-demand target;
- alternative normalized residual target;
- anchor-error direction/magnitude;
- learned reliability;
- compact heterogeneous live-model ensembles;
- materially different TSFM use/target.

---

# 8. Prospective c2/context research — parallel

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

Forward PIT-safe context collection continues for:

- verified rivalry/derby;
- verified absences/suspensions;
- sporting context;
- media/GDELT attention;
- hype/search/social where source semantics are valid.

No historical backfill from final-state knowledge.

---

# 9. What waits and what does not

## Must wait

Only evidence that genuinely does not yet exist:

- future post-freeze match outcomes;
- future live ticket trajectories;
- forward-only context observations.

## Must not wait

- Pre-Live v3 anchor/regime research;
- bounded historical experiments;
- new versioned target/model/ensemble hypotheses;
- PIT-safe feature engineering;
- CI/reproducibility hardening;
- context-collection infrastructure.

---

# 10. Promotion boundary

Production promotion requires materially more genuine prospective evidence, positive aggregate uplift, acceptable tail risk and bias, a reproducible frozen package and explicit reviewed promotion.

Until then:

`live_adjustment = 0`

---

# 11. Immediate work order

1. **start Pre-Live v3 historical-anchor + current-season-regime revalidation**;
2. keep frozen d2 prospective scoring running in parallel;
3. repair readiness/capacity/truth-source blockers without using them as R&D gates;
4. continue PIT-safe context collection;
5. if v3 passes its full gates, create a new freeze ID;
6. only then rebuild d2 against the new anchor under a new version.

## One-line rule

> **Frozen validation protects evidence integrity. It does not pause model development. Active R&D is now Pre-Live v3.**
