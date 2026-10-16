# C1-alpha T-1 Tournament v2 — final-24h LOEO result

Date: **2026-10-16**  
Status: **aggregate uplift confirmed / not stable enough for blanket activation**

## Protocol

- 9 completed Ekstraklasa events;
- final 24h only (`T-1 -> kickoff`);
- 30 PIT-valid trajectory rows;
- frozen current T-1 Structural Prior as incumbent;
- Leave-One-Event-Out validation;
- equal event weighting;
- compact/lean feature sets;
- generic and club-aware variants;
- residual-occupancy and direct-occupancy targets;
- no random snapshot split.

GitHub Actions run: `38886352158`  
Evidence artifact: `c1-alpha-t1-tournament-v2-38886352158`

## Incumbent

T-1 Structural Prior / zero correction:

**MAE = 3,968.7**

The same T-1 prior is held constant through the final-24h window for each event.

## Best candidate

`ridge_directocc_compact_generic_a10`

Target:

`direct final occupancy`

Result:

- Live MAE: **2,929.3**;
- absolute uplift vs Structural Prior: **1,039.4**;
- relative improvement: **26.19%**;
- event improvement rate: **4 / 9 = 44.44%**;
- first-row MAE: **2,810.3**;
- latest-row MAE: **3,046.6**;
- worst single-event degradation: **4,748.6**.

The direct-occupancy Ridge family clearly led the v2 leaderboard. Next alternatives were approximately 2,963–3,036 MAE.

## Per-event behaviour of the best candidate

| Event | Structural Prior MAE | Live MAE | Outcome |
|---|---:|---:|---|
| Lech — Raków | 5,031 | 9,780 | worse |
| Lech — Jagiellonia | 6,692 | **1,389** | much better |
| Lech — Radomiak | 11,364 | **4,992** | much better |
| Jagiellonia — Górnik | **87** | 504 | slightly worse |
| Pogoń — Korona | **89** | 1,391 | worse |
| Cracovia — Zagłębie | 1,097 | **917** | better |
| Śląsk — Lech | 9,723 | **2,671** | much better |
| GKS Katowice — Wieczysta | **783** | 2,400 | worse |
| Legia — Wisła Kraków | **852** | 2,321 | worse |

## Interpretation

The live ticketing signal is real: a simple regularized model reduced aggregate MAE by more than 26% and dramatically repaired several large Structural Prior misses.

However, unconditional replacement is unsafe. The model also damages several events where the Structural Prior is already excellent.

This is exactly the pattern expected from a **gating/blending problem**:

- when Structural Prior is already close, preserve it;
- when live evidence strongly disagrees and is credible, apply a correction;
- avoid forcing the live model to replace the incumbent on every event.

## Decision

Do **not** activate v2 as the production live correction.

Proceed immediately to:

### C1-alpha T-1 Gated/Blended v3

Use the v2 winner as the base live estimate and learn/select, using training events only, when/how strongly to blend it with Structural Prior.

Validation must be nested Leave-One-Event-Out:

1. hold one event out as the outer test;
2. use inner whole-event validation on the remaining events to choose the gating/blending policy;
3. refit the base live model on all outer-training events;
4. apply the selected policy to the untouched outer event;
5. repeat for every event.

No outer-event outcome may influence policy selection.

Primary objective remains lowest stable event-level MAE, with explicit worst-event degradation.

Target remains:

- **<1,900 MAE** first;
- <1,700 next;
- stretch <1,500.
