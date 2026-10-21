# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-21**

This is the canonical short-form model state.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Two parallel tracks

### Track A — frozen validation

Current frozen research stack:

`history + frozen current-season regime -> Frozen Pre-Live v2`

then:

`Frozen Pre-Live v2 + P2 reliability * frozen Ridge live residual -> d2 forecast`

Track A is append-only evidence collection. It does not retrain from new outcomes.

### Track B — active accuracy R&D

Track B continues now under new versioned experiments and does **not** wait for a prospective event-count gate.

Current Track-B work:

- all-horizon external-family/heterogeneous-ensemble closure audit COMPLETE;
- T-30/T-7/T-1 exact ensemble contracts in fixed-temporal robustness audit;
- next after robustness: separately versioned historical/Pre-Live challenger if warranted, plus new d2 formulation research and PIT-safe context research.

> **Production promotion waits for prospective evidence. R&D does not.**

---

# Production boundary

Production Structural Prior remains unchanged.

Production bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

No research evidence below automatically changes production.

---

# Frozen Pre-Live v2

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Historical contract:

| Horizon | Historical base | b2 regime | c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,691.40** |
| T-3 | Structural Prior | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | **1,682.63** |
| T-1 | Structural Prior | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,661.52** |

The freeze remains sealed. Track-B historical experiments do not mutate it.

---

# Active historical challenger evidence

## a2 External Model + Ensemble Closure — COMPLETE

Canonical result:

`ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`

Run `39624170933`, artifact `12356162577`.

Result JSON SHA256:

`dc2b65359e4841ba84d2bb51485c8b9da68816a33f9413f9208943fecaecf88a`

The bounded missing question — external families/heterogeneous ensembles at all five horizons — was tested under one fixed historical protocol.

### Advancing to fixed-temporal robustness

**T-30**

Selected ensemble:

`0.75 current a2 + 0.25 XGBoost depth3`

Reference gains vs current a2:

- 2024/25 `+54.93` MAE;
- 2025/26 `+29.74`.

**T-7**

Selected ensemble:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Reference gains:

- 2024/25 `+10.27`;
- 2025/26 `+27.86`.

**T-1**

Selected ensemble:

`0.25 HGB hist31 + 0.50 CatBoost depth4 + 0.25 LightGBM leaves15`

Reference gains:

- 2024/25 `+2.27`;
- 2025/26 `+6.28`.

The T-1 effect is extremely small on references and tail degradation remains material.

### Closed for this challenger formulation

- T-14: mixed refs `+58.02 / -2.58`;
- T-3: mixed refs `-2.80 / +30.54`.

Current a2 is retained there.

## Fixed-temporal robustness — ACTIVE

Contract:

`ml/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1.md`

The exact selected T-30/T-7/T-1 contracts are replayed unchanged across four rolling folds: 2022/23, 2023/24, 2024/25, 2025/26.

Pass rule:

`positive MAE improvement in all four rolling folds`

A pass qualifies the horizon only for a separately versioned next historical / Pre-Live challenger. It does not alter this file's frozen Pre-Live v2 state automatically.

---

# Frozen d2 package

## Stage 1 expert

`ridge-a10`

Contract:

- target `target_live_delta_occupancy`;
- Ridge `alpha=10`;
- median imputation within fold;
- missing indicators;
- standardization;
- event-balanced weights;
- raw correction cap +/-10pp occupancy.

Development:

- Frozen latest MAE `4128.01`;
- Ridge latest `3320.39`;
- latest uplift `807.62 / 19.56%`;
- Ridge window `3619.19`;
- worst latest-event degradation `4326.90`.

## Stage 2 policy

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Policy:

`P2-observation-maturity`

Reliability:

- obs1 `0.25`;
- obs2 `0.60`;
- obs3+ `1.00`;
- >18h cap `0.75`;
- >12h <=18h cap `0.90`;
- <=12h cap `1.00`.

Development:

- P2 latest MAE `3240.99`;
- uplift `887.02 / 21.49%`;
- window MAE `3657.65`;
- worst degradation `1081.72`.

Frozen Ridge/P2 are Track-A evidence objects and are not retuned event by event.

---

# Event 5 chronological holdout

Lech Poznań vs Korona Kielce, actual `37,407`.

| Layer | Latest error |
|---|---:|
| Structural T-1 base | 7,669.07 |
| Frozen Pre-Live v2 | 9,832.52 |
| Raw frozen Ridge | **6,652.81** |
| Frozen P2 | **6,652.81** |
| Persisted C1 v8 | 7,669.07 |

b2 moved the anchor down by `2,163.45` seats and worsened this event's pre-live error by the same amount versus Structural T-1.

Event 5 is permanently exposed.

---

# Prospective evidence classes

Stage-2 freeze cutoff:

`2026-10-19T19:11:01Z`

## `DELAYED_LABEL_HOLDOUT`

Kickoff at/before cutoff. Useful for diagnostics but not genuine forward promotion N.

## `TRUE_POST_FREEZE_PROSPECTIVE`

Kickoff after cutoff. This class may contribute to genuine forward promotion evidence.

Never combine these classes into one headline prospective sample size.

---

# Delayed-label diagnostics

Recovered labels already show frozen d2 does not improve every match:

- GKS Katowice–Pogoń: Frozen Pre-Live latest error about `1,356`; d2/P2 about `2,074`;
- Cracovia–Legia: Frozen about `434`; d2/P2 about `1,068`.

These outcomes remain exposed diagnostics. They cannot be used to tune Ridge/P2 and later be called unseen validation.

---

# d2 next-generation Track-B research

New, separately versioned research is allowed now without waiting for a prospective N threshold, provided the evaluation boundary is predeclared.

Priority formulations:

- remaining-demand target;
- alternative capacity-normalized live residual target;
- anchor-error direction + magnitude;
- learned reliability;
- compact heterogeneous live-model ensemble;
- materially different trajectory representation/TSFM use.

The existing frozen d2 stack remains the benchmark.

---

# Context research

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

Forward PIT-safe context collection continues for:

- verified rivalry;
- verified absences;
- sporting context;
- media/GDELT attention;
- hype/search/social where source semantics are valid.

No backfilling from final-state knowledge.

---

# TSFM boundary

Stage-1 Chronos-2 and Bolt-small lost to plain Ridge.

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune the same failed formulation on exposed data. Reopen only with materially more independent trajectories or a materially different predeclared target/use.

---

# Immediate development decision

**Keep Frozen Pre-Live v2 / Ridge / P2 unchanged for Track-A validation. Continue Track-B R&D now. Finish the exact T-30/T-7/T-1 fixed-temporal ensemble audit; only robust horizons may enter a new versioned historical/Pre-Live challenger. Keep prospective scoring and PIT-safe context collection running in parallel. Production remains unchanged.**
