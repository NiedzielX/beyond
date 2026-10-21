# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-21**

Status: **TRACK-A V2 FROZEN VALIDATION + TRACK-B V3 FROZEN RESEARCH ANCHOR + LONG-HORIZON LIVE R&D NEXT**

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Two parallel tracks

### Track A — frozen validation

Current forward-evidence stack remains unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Track A continues append-only delayed-label / true-post-freeze scoring.

### Track B — active R&D

Frozen research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

The final-24h v2/v3 anchor-equivalence audit is complete and proves that the current final-24h live target is unchanged.

Active next work:

`d2-long-horizon-live-v1 — extend live evidence earlier than 24h under a separate additive data contract`

> **Production promotion waits for prospective evidence. R&D does not.**

---

# Production boundary

Production bundle remains:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

No research freeze below is production activation.

---

# Track A — Frozen Pre-Live v2

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

| Horizon | Historical base | b2 regime | c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,867.82 |
| T-14 | Structural Prior | `NO_ADJUSTMENT` | `NO_CONTEXT` | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | 1,691.40 |
| T-3 | Structural Prior | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` | 1,682.63 |
| T-1 | Structural Prior | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` | 1,661.52 |

Frozen d2:

- Stage-1 expert `ridge-a10`;
- Stage-2 package `d2-stage2-p2-observation-maturity-2026-10-19-v1`;
- policy `P2-observation-maturity`.

This remains the current prospective-validation stack.

---

# Track B — Frozen Pre-Live v3 research candidate

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Exact v3 contract:

| Horizon | Historical base | current-season regime |
|---|---|---|
| T-30 | `0.75 current a2 + 0.25 XGBoost depth3` | `NO_ADJUSTMENT` |
| T-14 | exact v2 T-14 package | `NO_ADJUSTMENT` |
| T-7 | `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15` | `ewma50-resid-k4-cap05-min2` |
| T-3 | exact v2 T-3 package | `ewma50-resid-k2-cap05-min3` |
| T-1 | exact v2 T-1 package | `ewma50-resid-k6-cap05-min3` |

Historical c2 remains `NO_CONTEXT_ALL_HORIZONS`.

Package audit:

- 20-cell mean MAE `1934.04 -> 1924.64`;
- improvement `+9.39 / +0.49%`;
- T-30 positive in 4/4 rolling folds;
- T-7 positive in 4/4;
- T-14/T-3/T-1 reproduce v2 exactly.

V3 is research-only and does not replace Track A.

---

# d2-v3 Stage 0 — FINAL-24H EQUIVALENCE COMPLETE

Result:

`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`

Run:

`39636749440`

Artifact ID:

`12361203868`

Decision:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Exact frozen development set:

- 9 events;
- 30 final-24h rows;
- IDs `1,3,4,8,9,12,13,14,17`.

Why equivalence holds:

- existing d2 Stage 0 anchors final-24h rows on T-1;
- v3 T-1 is exactly the v2 T-1 package;
- v2/v3 T-1 expected rolling MAEs and historical input lineage are identical.

Hard row-level result:

- maximum absolute anchor-seat delta: **`0.0` seats**.

Only CSV floating round-trip noise remains in derived values:

- target attendance max delta `3.637978807091713e-12` seats;
- target occupancy max delta `1.734723475976807e-16`.

## Consequence

Do **not** rerun or rename the same final-24h Ridge/P2 model merely because the Pre-Live freeze ID changed.

For the current final-24h problem definition, the residual target is numerically unchanged.

---

# Long-horizon live data readiness — CONFIRMED

A direct PIT-safe data audit of current Supabase snapshot history shows that the next materially different experiment is feasible.

Across the current 14 labeled, capacity-resolved Ekstraklasa events eligible under the C1 export contract:

- 13/14 have valid PIT trajectory rows beyond 24h;
- 10/14 have valid rows beyond 48h;
- 8/14 have valid rows in the 72–168h window.

Examples with valid ~7-day trajectories include event IDs:

`1,3,4,5,15,18,19`

and event `11` reaches about 90h.

The existing `get_live_trajectory_features_v1_1_asof` function already validates PIT state on these earlier snapshots.

The current exporter is the limiting contract: `v7-final24` deliberately filters to the final 24 hours.

---

# Active Track-B next workstream — d2-long-horizon-live-v1

Do not mutate `v7-final24`.

Create an additive research export for up to 168h before kickoff using the same:

- eligible-event rules;
- verified capacity contract;
- `get_live_trajectory_features_v1_1_asof` PIT feature function;
- latest snapshot per event x 6h bucket sampling.

The long-horizon dataset must preserve coverage/missingness explicitly rather than pretending every event has a full 7-day trajectory.

## First research questions

1. What is the best honest live start window supported by the data: 48h, 72h or 168h?
2. Does live trajectory add MAE value before final-24h?
3. Can the changed v3 T-7 anchor improve the earlier live problem?
4. Should the live anchor be checkpoint-based, piecewise, or another predeclared continuous transition?

## Evidence boundary

The original 9-event development set remains exposed historical development lineage.

Newer labeled events `5,11,15,18,19` are already exposed and must remain labeled as such. They may be used only under a newly declared chronological research split; they cannot be called unseen holdouts after inspection.

No random snapshot split.

Event remains the independent unit.

---

# Prospective evidence classes

Track-A cutoff:

`2026-10-19T19:11:01Z`

- `DELAYED_LABEL_HOLDOUT`: diagnostic only;
- `TRUE_POST_FREEZE_PROSPECTIVE`: genuine forward-promotion evidence.

Track-A scoring continues independently of long-horizon Track-B R&D.

---

# Immediate development decision

> **Keep v2/Ridge/P2 frozen for Track-A evidence. Keep v3 sealed as a research anchor. Do not retrain the same final-24h model: the v2/v3 final-24h anchor is exactly equivalent. Active R&D moves to an additive earlier-than-24h live data contract and long-horizon experiment, with production unchanged.**
