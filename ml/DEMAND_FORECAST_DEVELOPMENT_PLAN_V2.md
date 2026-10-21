# Beyond Ticketing — Demand Forecast Development Plan v2

Last updated: **2026-10-21**

Status: **CANONICAL ACCURACY ROADMAP**

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Two rules are mandatory:

1. frozen evidence packages are immutable;
2. **R&D does not wait for prospective sample-count gates when honest research can be run now.**

A failed challenger closes the challenger, not the workstream.

---

# 1. Parallel tracks

## Track A — frozen validation / promotion evidence

Current stack:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Purpose:

- delayed-label diagnostics;
- true post-freeze prospective evidence;
- eventual production-promotion evidence.

Track A remains unchanged.

## Track B — active accuracy R&D

A new pre-live research anchor is now sealed:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Active next work:

`d2-v3 — rebuild/revalidate live updater against Frozen Pre-Live v3`

> **Production promotion waits for prospective evidence. R&D does not.**

---

# 2. Track-A frozen v2

Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Frozen d2:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Production:

`live_adjustment = 0`

Do not mutate this stack from new outcomes.

---

# 3. Pre-Live v3 historical R&D — COMPLETE AND SEALED

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Freeze result:

`ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`

## Exact v3 package

| Horizon | historical base | current-season regime |
|---|---|---|
| T-30 | `0.75 current a2 + 0.25 XGBoost depth3` | `NO_ADJUSTMENT` |
| T-14 | exact v2 horizon base | `NO_ADJUSTMENT` |
| T-7 | `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15` | `ewma50-resid-k4-cap05-min2` |
| T-3 | exact v2 horizon base | `ewma50-resid-k2-cap05-min3` |
| T-1 | exact v2 horizon base | `ewma50-resid-k6-cap05-min3` |

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

## Evidence chain

### a2 external/ensemble closure

Run `39624170933`.

### a2 fixed-temporal robustness

Run `39625425854`.

### v3 current-season-regime revalidation

Run `39627633502`.

Outcome:

- T-30 advance with `NO_ADJUSTMENT`;
- T-7 advance with `ewma50-resid-k4-cap05-min2`;
- T-14/T-3/T-1 retain Frozen-v2 horizon package.

### v3 fixed-temporal package audit

Run `39628607689`.

T-30 gains vs v2:

`+5.98 / +33.50 / +54.93 / +29.74`

T-7 gains:

`+10.92 / +11.18 / +13.71 / +27.88`

T-14/T-3/T-1 exact v2 reproduction.

20-cell mean MAE:

`1934.04 -> 1924.64`

Improvement:

`+9.39 / +0.49%`

### v3 freeze seal

Run `39633561065`.

Artifact ID `12360033160`.

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Status:

`FROZEN_HISTORICAL_RESEARCH_CANDIDATE`

---

# 4. Important v3 interpretation

V3 is not an all-horizon rewrite.

Only T-30 and T-7 changed after package-level evidence.

T-1 was deliberately rejected from v3 even after historical-anchor robustness because the full package vs Frozen v2 was mixed:

- 2024/25 `+1.92`;
- 2025/26 `-15.39`.

This is why package-level revalidation matters.

V3 remains research-only because:

- references are exposed historically;
- aggregate gain is modest;
- tail risk remains material;
- no fresh prospective v3 evidence exists yet.

---

# 5. Track-B priority 1 — d2-v3 — ACTIVE NOW

The live residual target must be rebuilt because the anchor changed.

Do not silently reuse `ridge-a10` or P2 from v2.

## Stage 0 — v3 anchor replay

Reconstruct exact v3 anchors for the frozen d2 development set:

- 9 independent events;
- 30 final-24h live rows;
- preserve event/as-of identity;
- no future interpolation;
- no outcome leakage into live features.

Compare:

- v2 Frozen Pre-Live anchor;
- v3 Frozen research anchor;
- actual attendance.

This creates the new d2-v3 target.

## Stage 1 — compact live-model tournament

Required benchmark:

`v3-zero-correction`

Also retain the old v2/Ridge/P2 stack as an external research comparator.

Candidate families should remain compact and materially different, for example:

- Ridge;
- Huber;
- HGB / LightGBM / CatBoost only where sample size supports them;
- transparent inventory extrapolation;
- explicitly governed ensemble only if predeclared.

No random snapshot split.

Primary unit:

`event`

Selection:

`LOEO / event-balanced`

## Stage 2 — reliability / tail governance

After the Stage-1 expert is frozen, revalidate reliability against v3.

Potential signals:

- observation count;
- observation span;
- time to kickoff;
- correction magnitude;
- live velocity/acceleration;
- stability / data-quality flags;
- disagreement magnitude.

The existing P2 policy is a benchmark, not an inherited policy.

## TSFM boundary

Old Stage-1 Chronos/Bolt formulation remains closed.

Reopen only if d2-v3 defines a materially different trajectory target/use or materially more independent live trajectories exist.

---

# 6. Track-A prospective validation continues

While d2-v3 R&D runs:

- continue scoring v2/Ridge/P2 append-only;
- preserve `DELAYED_LABEL_HOLDOUT` vs `TRUE_POST_FREEZE_PROSPECTIVE`;
- do not mutate Track-A from the scored outcomes;
- repair truth/capacity/readiness blockers separately.

---

# 7. Context research — parallel

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

Forward PIT-safe collection continues for rivalry, verified absences, sporting context, media/GDELT and valid hype/search/social signals.

Do not backfill final-state knowledge into historical training.

---

# 8. What waits and what does not

## Must wait

Only genuinely future evidence:

- future outcomes;
- future trajectories;
- forward-only context observations.

## Must not wait

- d2-v3 anchor replay;
- d2-v3 model tournament;
- reliability research;
- PIT-safe feature work;
- CI/reproducibility work;
- context ingestion infrastructure.

---

# 9. Promotion boundary

Neither v3 nor future d2-v3 historical/LOEO success is automatic production promotion.

Production requires materially more genuine prospective evidence, acceptable tail risk/bias, a reproducible frozen package and explicit reviewed activation.

Until then:

`live_adjustment = 0`

---

# 10. Immediate work order

1. **start d2-v3 Stage 0 exact anchor replay**;
2. create the new live residual target against v3;
3. run compact event-level Stage-1 tournament;
4. revalidate reliability/tail governance under new IDs;
5. keep Track-A v2 prospective scoring running in parallel;
6. continue PIT-safe context collection;
7. do not activate production.

## One-line rule

> **Pre-Live v3 is sealed. Active R&D moves immediately to d2-v3; Track-A v2/Ridge/P2 remains frozen and production remains unchanged.**
