# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-21**

Status: **FROZEN V2 VALIDATION + ACTIVE PRE-LIVE V3 R&D**

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Two parallel tracks

### Track A — frozen validation

Current frozen research stack:

`Frozen Pre-Live v2 + P2 reliability * frozen Ridge live residual`

Track A is append-only evidence collection. It does not retrain from new outcomes.

### Track B — active accuracy R&D

Track B continues now under new versioned experiments and does **not** wait for a prospective event-count gate.

Current Track-B state:

- all-horizon external-family/heterogeneous-ensemble closure audit — COMPLETE;
- T-30/T-7/T-1 fixed-temporal robustness — COMPLETE, all three PASS 4/4;
- **active next: Pre-Live v3 historical-anchor + current-season-regime revalidation**;
- PIT-safe context collection continues in parallel;
- d2 will be rebuilt against v3 only if v3 later earns a freeze.

> **Production promotion waits for prospective evidence. R&D does not.**

---

# Production boundary

Production bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

No research evidence below automatically changes production.

---

# Frozen Pre-Live v2 — Track A

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

| Horizon | Historical base | b2 regime | c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,691.40** |
| T-3 | Structural Prior | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | **1,682.63** |
| T-1 | Structural Prior | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | **1,661.52** |

This freeze remains sealed and unchanged.

---

# a2 external/ensemble R&D — COMPLETE

Closure result:

`ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`

Run `39624170933`, artifact `12356162577`.

Fixed-temporal robustness result:

`ml/results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md`

Run `39625425854`, artifact `12356632426`.

Result JSON SHA256:

`e6532db4bccfe567dd1eeaf3196f74d1a41a78a66eea53bc975892868ff2c900`

Artifact ZIP SHA256:

`7d9cfe2609affcb35b7c99252d42231ce1e5e55b24fbb3bb1dfd3470a0226e4e`

## Robust historical challengers

### T-30

`0.75 current a2 + 0.25 XGBoost depth3`

Rolling-fold MAE gains:

`+5.98 / +33.50 / +54.93 / +29.74`

Mean:

`+31.04 / 1.47%`

Club-season cells improved `50/72`; worst event degradation `2,855.70`.

### T-7

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Rolling-fold gains:

`+20.18 / +8.90 / +10.27 / +27.86`

Mean:

`+16.80 / 0.87%`

Club-season cells improved `42/72`; worst event degradation `1,632.41`.

### T-1

`0.25 HGB hist31 + 0.50 CatBoost depth4 + 0.25 LightGBM leaves15`

Rolling-fold gains:

`+16.48 / +55.46 / +2.27 / +6.28`

Mean:

`+20.12 / 1.05%`

Club-season cells improved `38/72`; worst event degradation `2,309.70`.

Weakest paired-bootstrap P(improvement > 0) is `0.5196`, so T-1 in particular remains a modest-effect challenger rather than a proven large uplift.

### Not advanced

- T-14: current a2 retained after mixed exposed references;
- T-3: current a2 retained after mixed exposed references.

The bounded a2 external-family/ensemble gap is closed.

---

# Active Track-B candidate — Pre-Live v3

Historical v3 candidate base:

| Horizon | Proposed historical v3 base |
|---|---|
| T-30 | robust T-30 ensemble |
| T-14 | current a2 Structural Prior |
| T-7 | robust T-7 ensemble |
| T-3 | current a2 Structural Prior |
| T-1 | robust T-1 ensemble |

This is **not frozen yet**.

Before any v3 freeze, current-season regime must be revalidated against the new historical anchors.

Why:

> b2 residual policies were selected relative to the old historical bases. Carrying them unchanged into v3 without an audit would change the meaning of the residual correction.

Required v3 experiment:

1. new historical base only;
2. old frozen b2 formulation applied unchanged on the new anchor as a fixed comparator;
3. newly selected current-season-regime challenger under a declared temporal boundary;
4. Frozen Pre-Live v2 as unchanged benchmark;
5. no prospective event tuning;
6. fixed-temporal validation before any new freeze ID.

If v3 later freezes, d2 must be rebuilt/revalidated against the v3 anchor under a new d2 version.

---

# Frozen d2 package — Track A

## Stage 1 expert

`ridge-a10`

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

Development:

- latest MAE `3240.99`;
- uplift `887.02 / 21.49%`;
- window MAE `3657.65`;
- worst degradation `1081.72`.

Frozen Ridge/P2 remain tied to Frozen Pre-Live v2 and are not retuned event by event.

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

Event 5 is permanently exposed.

---

# Prospective evidence classes

Stage-2 freeze cutoff:

`2026-10-19T19:11:01Z`

- `DELAYED_LABEL_HOLDOUT`: diagnostic only, not genuine forward promotion N;
- `TRUE_POST_FREEZE_PROSPECTIVE`: may contribute to genuine forward promotion evidence.

Never combine these classes into one headline prospective sample size.

Delayed-label evidence already shows frozen d2 is not uniformly beneficial match-by-match, including GKS–Pogoń and Cracovia–Legia. Those exposed outcomes may generate future hypotheses but cannot be used for post-hoc Ridge/P2 tuning and then treated as unseen evidence.

---

# Context research

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

Forward PIT-safe collection/research continues for verified rivalry, absences, sporting context, media/GDELT and valid hype/search/social signals.

---

# Immediate development decision

> **Keep Frozen Pre-Live v2 / Ridge / P2 unchanged for Track-A validation. Active Track-B work is now the separately versioned Pre-Live v3 historical-anchor + current-season-regime revalidation. Do not wait for prospective N. Production remains unchanged.**
