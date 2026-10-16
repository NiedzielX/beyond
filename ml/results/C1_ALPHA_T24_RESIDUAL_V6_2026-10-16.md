# C1-alpha T-24 Residual v6 — event-level LOEO / LOCO result

Date: **2026-10-16**  
Status: **completed / reject T-24-only as primary C1 direction**

## Purpose

v6 deliberately reduced the problem to one independent row per completed event.

The question was:

> Can the PIT-safe T-24 `hybrid_v6` ticketing signal directly correct the current frozen T-1 Structural Prior without using duplicated trajectory rows?

## Protocol

- 9 completed Ekstraklasa events;
- 7 home clubs;
- one independent row per event;
- 8/9 events with PIT-safe T-24 `hybrid_v6`;
- current frozen T-1 Structural Prior as incumbent;
- primary validation: Leave-One-Event-Out (LOEO);
- secondary validation: Leave-One-Home-Club-Out (LOCO);
- low-dimensional feature sets only;
- Ridge / Huber challengers;
- targets: residual ratio, occupancy residual and direct occupancy;
- bias-only controls;
- no random row split;
- no outcome-derived feature input.

Lightweight event export:

`c1-alpha-event-training-export-v1`

GitHub Actions run:

`38890267787`

Evidence artifact:

`c1-alpha-t24-residual-v6-38890267787`

Artifact ID:

`12041237264`

Artifact SHA256:

`2d2332a6b8c438dcec9f9f7a43d5a3e59947128c6355e42ec9d05c9ac2f49873`

## Best LOEO candidate

`ridge_direct_occupancy_hybrid_a10`

Target:

`direct_occupancy`

### LOEO result

- Structural Prior MAE: **3,968.7**;
- challenger MAE: **3,873.2**;
- absolute uplift: **95.6**;
- relative improvement: **2.41%**;
- event improvement rate: **5 / 9 = 55.56%**;
- worst-event degradation: **3,564.2**;
- median absolute error: **3,358.7**;
- bias: **+213.1**.

This technically beats the incumbent in LOEO, but the improvement is too small and unstable to justify a C1 candidate.

## LOCO result for the same candidate

- Structural Prior MAE: **3,968.7**;
- challenger MAE: **3,989.8**;
- absolute uplift: **-21.0**;
- relative improvement: **-0.53%**;
- event improvement rate: **3 / 9 = 33.33%**;
- worst-event degradation: **3,564.2**;
- bias: **+1,339.4**.

The candidate does **not** generalize across unseen home clubs.

## LOEO event behaviour

| Event | Hybrid source | Structural Prior error | v6 error | Result |
|---|---|---:|---:|---|
| Lech — Raków | raw_v6 | 5,031.1 | 4,864.8 | slight improvement |
| Lech — Jagiellonia | raw_v6 | 6,691.8 | 5,216.0 | improvement |
| Lech — Radomiak | raw_v6 | 11,364.5 | 11,199.8 | slight improvement |
| Jagiellonia — Górnik | matched_v6 | **86.9** | 3,267.3 | much worse |
| Pogoń — Korona | matched_v6 | **89.1** | 534.8 | worse |
| Cracovia — Zagłębie | matched_v6 | 1,096.5 | **28.8** | much better |
| Śląsk — Lech | missing | 9,723.4 | **3,358.7** | much better |
| GKS Katowice — Wieczysta | matched_v6 | **783.4** | 1,972.4 | worse |
| Legia — Wisła Kraków | matched_v6 | **851.7** | 4,415.9 | much worse |

## Oracle diagnostic

Outcome-aware oracle choosing between Structural Prior and the v6 challenger:

- Structural Prior: **3,968.7 MAE**;
- v6 challenger: **3,873.2 MAE**;
- oracle prior-or-v6: **2,942.1 MAE**.

This is a key negative diagnostic.

The v2 pair — Structural Prior plus the full final-24h live expert — had an oracle around **1,867.9 MAE**.

Therefore compressing the live evidence to a single T-24 `hybrid_v6` row discards a substantial amount of the complementary information contained in the full final-24h trajectory.

## Decision

**Reject v6 as the primary C1 direction.**

Do not freeze or deploy `ridge_direct_occupancy_hybrid_a10`.

Do not continue optimizing a T-24-only challenger.

The strongest honest aggregate challenger remains the v2 full final-24h expert:

`ridge_directocc_compact_generic_a10`

with approximately:

- Structural Prior: **3,968.7 MAE**;
- v2 live: **2,929.3 MAE**;
- relative improvement: **26.19%**;
- but material event-level instability.

The main R&D opportunity remains the v2 expert pair because its non-deployable oracle switch is approximately **1,867.9 MAE**.

## Next step — v7 expert reliability diagnostic

Do not add another high-dimensional stacker yet.

Build an event-level diagnostic around the existing v2 pair and answer:

> **What PIT-observable characteristics distinguish events where Structural Prior should be trusted from events where the final-24h live expert should take over?**

For each event derive one diagnostic row containing, without outcome leakage in feature construction:

- current Structural Prior P50 and expected occupancy;
- current-season prior maturity: round number / completed home evidence available before T-1;
- v2 live estimate at the earliest final-24h observation;
- v2 live estimate at the latest pre-kickoff observation;
- prior-vs-live disagreement magnitude and direction;
- live prediction stability across final 24h: range / standard deviation / slope;
- live observation-window length and snapshot count;
- signal readiness / feature quality;
- matched-sector vs raw-only regime;
- release / sector-coverage flags.

Actual outcome and oracle expert label may be included **only as evaluation/diagnostic labels**, never as predictors.

Use this diagnostic to define the next predeclared reliability policy. The goal is to approach the v2 oracle without tuning rules directly to held-out outcomes.
