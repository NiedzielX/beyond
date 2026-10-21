# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-21**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector / Price-area Decision Support MVP: IMPLEMENTED**  
> **Pre-Live v2 historical candidate: FROZEN + SEALED**  
> **d2 Stage 0: DONE**  
> **d2 Stage 1: DONE / ridge-a10 FROZEN**  
> **d2 Stage 2: DONE / P2-observation-maturity FROZEN**  
> **d2 Event 5 chronological holdout: COMPLETE**  
> **d2 prospective validation: ACTIVE IN TRACK A**  
> **Pre-Live v3 anchor/regime R&D: ACTIVE IN TRACK B**

Canonical documents:

- `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
- `ml/CURRENT_MODEL.md`;
- `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
- `ml/results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md`;
- `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
- `ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`;
- `AI_BOOTSTRAP.md`.

## Two-track rule

### Track A — frozen live validation

Keep the current v2/Ridge/P2 stack unchanged and score new outcomes append-only.

### Track B — active model R&D

Model development does **not** wait for a prospective sample-count threshold.

Current priority is Pre-Live v3 anchor/regime research because the historical anchor has new robust challenger evidence. If v3 earns a freeze, d2 must be rebuilt/revalidated against that new anchor under a new d2 version.

> **Production promotion waits for prospective evidence. R&D does not.**

## Frozen architecture — Track A

Pre-live:

`history + proven current-season regime -> Frozen Pre-Live v2`

Live:

`final_forecast(t) = frozen_pre_live_v2(t) + P2_reliability(t) * ridge_delta(t)`

Frozen IDs:

- Pre-Live v2: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- Stage-1 expert: `ridge-a10`;
- Stage-2 package: `d2-stage2-p2-observation-maturity-2026-10-19-v1`;
- Stage-2 policy: `P2-observation-maturity`.

## Production boundary

Production remains:

`live_adjustment = 0`

Structural Prior remains production incumbent.

Frozen Pre-Live v2 and d2 are research candidates.

Frozen C1 v8 remains:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Do not retune C1 v8 as part of d2.

---

# d2 Stage 0 — COMPLETE

Exact Frozen-v2 compatibility established on:

- 9 events;
- 30 final-24h rows;
- exact frozen anchor lineage.

Status:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

---

# d2 Stage 1 — COMPLETE / FROZEN

Expert:

`ridge-a10`

Frozen contract:

- target `target_live_delta_occupancy`;
- Ridge alpha `10.0`;
- median imputation inside training fold;
- missing indicators;
- standardization;
- event-balanced weights;
- raw correction cap +/-10pp occupancy.

Development:

- Frozen-v2 latest MAE `4128.01`;
- Ridge latest MAE `3320.39`;
- Ridge window MAE `3619.19`;
- worst degradation `4326.90`.

Chronos-2 / Bolt-small did not improve plain Ridge.

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

---

# d2 Stage 2 — COMPLETE / FROZEN

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Policy:

`P2-observation-maturity`

Frozen reliability:

- observation 1 `0.25`;
- observation 2 `0.60`;
- observation 3+ `1.00`;
- >18h cap `0.75`;
- >12h <=18h cap `0.90`;
- <=12h cap `1.00`.

Development result:

- latest MAE `3240.99`;
- latest uplift vs Frozen `887.02 / 21.49%`;
- window MAE `3657.65`;
- worst degradation `1081.72`;
- 75% reduction in worst degradation vs raw Ridge.

Only P2 passed all predeclared Stage-2 gates.

---

# Event 5 first chronological holdout — COMPLETE

Event:

Lech Poznań vs Korona Kielce, actual `37,407`.

| Layer | Latest error | Window MAE |
|---|---:|---:|
| Structural T-1 base | 7,669.07 | n/a |
| Frozen Pre-Live v2 | 9,832.52 | 9,832.52 |
| **Raw frozen Ridge** | **6,652.81** | **6,170.35** |
| Frozen P2 | **6,652.81** | 7,263.16 |
| persisted C1 v8 policy | 7,669.07 | 7,669.07* |

`*` C1 window sampling differs slightly from canonical d2 final-24h rows.

D2 latest improvement vs Frozen v2:

`3179.71 seats / 32.34%`

Event 5 is permanently exposed and cannot become unseen validation again.

---

# Prospective validation — ACTIVE IN TRACK A

Contract:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

For each new completed event, persist separately:

1. Structural T-1 base;
2. Frozen Pre-Live v2 / b2;
3. raw frozen Ridge;
4. frozen P2;
5. genuine persisted pre-outcome C1 comparator where available.

Track:

- latest AE;
- event-balanced window MAE;
- bias;
- max revision;
- b2 incremental effect;
- Ridge incremental effect;
- P2 incremental effect;
- reliability trajectory;
- data-quality warnings;
- evidence class.

Evidence classes:

- `DELAYED_LABEL_HOLDOUT`;
- `TRUE_POST_FREEZE_PROSPECTIVE`.

Never combine them into one headline forward sample size.

---

# Delayed-label diagnostics

Recovered labels show that frozen d2 does not improve every match:

- GKS Katowice–Pogoń: Frozen Pre-Live latest error about `1,356`, d2/P2 about `2,074`;
- Cracovia–Legia: Frozen about `434`, d2/P2 about `1,068`.

These are exposed diagnostics. Do not tune frozen Ridge/P2 from them and later call the same events unseen.

Data/capacity/truth-source blockers should be repaired as data-contract work and must not block unrelated Track-B R&D.

---

# Active Track-B anchor work — Pre-Live v3

The completed a2 external/ensemble robustness audit produced robust historical challengers at T-30, T-7 and T-1.

If a new Pre-Live v3 anchor is built, current b2 must be revalidated against it before any freeze because current-season residuals are anchor-dependent.

Do not silently move frozen d2 onto a new anchor.

---

# d2 next-generation research boundary

A new versioned d2 challenger does **not** require waiting for N future events if it can be evaluated honestly under a declared boundary.

Possible later formulations:

- remaining-demand target;
- alternative capacity-normalized residual target;
- anchor-error direction/magnitude;
- learned reliability;
- compact heterogeneous live-model ensemble;
- materially different trajectory/TSFM target.

However, once Pre-Live v3 is the active anchor candidate, the cleanest next live-model cycle is to rebuild d2 after the v3 anchor decision so the live target is defined relative to the correct anchor.

The old Ridge/P2 package remains frozen against v2 as the benchmark.

---

# Continuous-time behavior

The live engine remains continuous over time-to-kickoff.

Named T-30/T-14/T-7/T-3/T-1 points are evaluation checkpoints, not separate live-model moments.

Every meaningful forecast revision should retain:

- as-of timestamp;
- source snapshot IDs;
- anchor lineage;
- live model ID;
- reliability policy ID;
- proposed correction;
- applied correction;
- forecast before/after;
- quality/release/coverage warnings.

---

# Inventory interpretation

Public availability is a proxy, not confirmed paid sales.

Distinguish where possible:

- genuine demand movement;
- ticket releases;
- sector openings/closures;
- coverage changes;
- scrape/data anomalies.

Do not interpret every inventory decrease/increase as pure demand.

---

# Production promotion

Historical/LOEO evidence and a small number of holdouts are insufficient for production promotion.

Promotion requires materially more genuine prospective evidence, positive aggregate uplift, acceptable tail risk/bias, a frozen reproducible package and explicit reviewed approval.

Until then:

`live_adjustment = 0`

## Immediate live-engine instruction

> **Keep `d2-stage2-p2-observation-maturity-2026-10-19-v1` frozen in Track A and continue append-only prospective scoring. Do not use prospective sample-count gates to pause Track-B R&D. Active model work is the Pre-Live v3 anchor/regime cycle; if v3 later freezes, rebuild d2 against that anchor under a new version instead of silently reusing Ridge/P2.**
