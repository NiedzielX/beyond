# C1-alpha T-1 Hybrid Gate v5 — nested LOEO result

Date: **2026-10-16**  
Status: **hybrid signal useful, target not reached**

## Protocol

- 9 completed Ekstraklasa events;
- final 24h / T-1 Structural Prior;
- 30 PIT-valid trajectory rows;
- 8/9 events have PIT-safe `hybrid_v6` at T-24h;
- missing hybrid signal remains explicit;
- base live expert frozen to v2 winner `ridge_directocc_compact_generic_a10`;
- outer Leave-One-Event-Out;
- base-live estimates for meta training produced by inner LOEO only;
- no outer-event outcome in base/meta training;
- candidate meta models: direct-occupancy Ridge/Huber, soft/hard logistic gates, learned blend-weight regressors, shallow tree variants.

Training export:

`c1-alpha-training-export-v2`

Hybrid contract:

`hybrid_v6 = matched-sector 6h velocity pct-of-first per hour, raw 6h velocity fallback`

PIT rule:

`feature_snapshot_captured_at <= T-24h checkpoint`

GitHub Actions run: `38888605092`  
Evidence artifact: `c1-alpha-t1-hybrid-gate-v5-38888605092`  
Artifact ID: `12040552651`

## Incumbent

T-1 Structural Prior:

**3,968.7 MAE**

## Best v5 candidate

`stack_ridge_hybrid_full_a10`

Mode:

`direct occupancy`

Result:

- Live MAE: **3,073.8**;
- absolute uplift: **895.0**;
- relative improvement: **22.55%**;
- event improvement rate: **4 / 9 = 44.44%**;
- first-row MAE: **3,008.2**;
- latest-row MAE: **3,141.4**;
- worst-event degradation: **4,658.8**.

Targets:

- beats Structural Prior: **YES**;
- `<1900 MAE`: **NO**;
- `<1700 MAE`: **NO**;
- `<1500 MAE`: **NO**.

## Per-event behaviour

| Event | Hybrid source | Structural Prior MAE | v5 MAE | Result |
|---|---|---:|---:|---|
| Lech — Raków | raw_v6 | 5,031 | 9,690 | worse |
| Lech — Jagiellonia | raw_v6 | 6,692 | **641** | much better |
| Lech — Radomiak | raw_v6 | 11,364 | **9,513** | better |
| Jagiellonia — Górnik | matched_v6 | **87** | 2,681 | worse |
| Pogoń — Korona | matched_v6 | **89** | 783 | worse |
| Cracovia — Zagłębie | matched_v6 | 1,097 | **683** | better |
| Śląsk — Lech | missing | 9,723 | **191** | much better |
| GKS Katowice — Wieczysta | matched_v6 | **783** | 2,496 | worse |
| Legia — Wisła Kraków | matched_v6 | **852** | 986 | slightly worse |

## Interpretation

`hybrid_v6` adds real information, but a high-dimensional stacked model is still not the right formulation for the current small-N dataset.

The pattern is now clear:

- Structural Prior is extremely strong on several later events;
- live ticketing information is dramatically better on several large Structural Prior misses;
- complex stackers struggle to learn this expert-selection boundary from only 9 independent events;
- adding more row-level features does not solve the independence problem.

The non-deployable oracle prior-vs-v2-live switch remains approximately **1,868 MAE**. The remaining gap is therefore still predominantly expert selection / calibration, not lack of signal.

## Decision

Do not activate v5 as production live correction.

Do not continue adding more stacking layers.

Proceed to **C1-alpha T-24 Residual Challenger v6** — a deliberately simpler event-level experiment:

1. one independent row per event at T-24h;
2. current frozen T-1 Structural Prior as the baseline prediction;
3. target = actual residual ratio / occupancy residual versus current Structural Prior;
4. primary signal = `hybrid_v6`;
5. optional low-dimensional PIT-safe context only: hybrid source, Structural Prior occupancy, current-season home-evidence count / round;
6. grouped LOEO and, where feasible, LOCO;
7. small predeclared Ridge/Huber grid plus bias-only control;
8. no full-trajectory row duplication.

This directly tests whether the earlier Ticketing Challenger idea can calibrate the **current Structural Prior**, rather than the legacy baseline it originally used.
