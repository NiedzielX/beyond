# Beyond Ticketing — d2 Stage 1 Model Tournament v1 — Result

Date: **2026-10-19**

Status: **COMPLETED / RESEARCH LEAD SELECTED / NO PRODUCTION CHANGE**

## Decision

Stage 1 selected:

`ridge-a10`

as the d2 **research lead** on the frozen 9-event / 30-row development set.

This is not a production champion and does not change production.

Production remains:

`live_adjustment = 0`

Frozen C1 v8 remains unchanged.

## Parent lineage

Frozen Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Stage 0 status:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

Development events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Development rows:

`30`

Independent evaluation unit:

`event`

Validation:

`Leave-One-Event-Out`

Training weights:

`event-balanced`

## Canonical CI evidence

Workflow run:

`39256585339`

Main commit:

`3e95f0025d381eb1bed4a2e00744466b17d21dea`

Artifact:

`d2-stage1-model-tournament-v1-39256585339`

Artifact ID:

`12187853899`

Artifact ZIP SHA256:

`c494ba609f3c9ee376e8285a9af975cc78d813337bd219fbaf94c7a9a336c6de`

Evidence hashes:

- split manifest: `5591880cff101ed316c4acae87fb0cb549ef9d5a987126b63245e154adb5a822`;
- Stage 0 JSON: `bb8a7c8ef3c719bca0c54da8961aea92d8484168b6493c768fe88c53f316985a`;
- Stage 0 CSV: `ec7aef2f458ae1db2fdaced7e0a051fe8b9035eccdb3764b0f640c6078aa6954`;
- Stage 1 JSON: `a666c57631756245245511ec11b40673aa7fb2c6cbb23303fb019993130fae4c`;
- Stage 1 predictions CSV: `df7cacd7a116c418f869ef6890f1bec289238c1af0f561e18a13b83c0b1f5783`.

## Development-set split integrity

The append-only C1 exporter had grown to:

- 10 completed events;
- 34 final-24h rows.

Stage 1 did **not** expand its development set after seeing the new outcome.

The exact committed 9-event / 30-row development set was reconstructed by `(ticket_event_id, as_of_at)` identity from the frozen C1 contract.

New event:

- event ID `5`;
- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 live rows.

was separated as a **new holdout candidate** and was not used for Stage-1 model selection.

Rule:

> Event 5 must remain untouched while Stage 2 reliability/gating is designed and frozen on the original 9-event development set.

## Stage 1 leaderboard

| Candidate | Latest-row MAE | Improvement vs Frozen v2 | Event-balanced window MAE | Window improvement | Latest event improvement rate | Worst latest-event degradation |
|---|---:|---:|---:|---:|---:|---:|
| Frozen v2 / zero correction | 4,128.01 | 0.00 | 4,128.01 | 0.00 | 0.0% | 0.00 |
| Train-fold bias | 4,655.98 | -527.97 | 4,655.98 | -527.97 | 22.2% | 1,554.36 |
| Inventory linear extrapolation | 3,869.68 | +258.33 | 3,701.05 | +426.97 | 44.4% | 3,100.60 |
| **Ridge `alpha=10`** | **3,320.39** | **+807.62** | **3,619.19** | **+508.83** | **66.7%** | **4,326.90** |
| Huber `alpha=0.01` | 4,567.83 | -439.81 | 5,135.08 | -1,007.07 | 22.2% | 4,370.80 |
| HistGradientBoosting | 4,186.11 | -58.10 | 4,084.01 | +44.00 | 33.3% | 4,326.90 |
| Ridge + Chronos-2 | 3,428.25 | +699.76 | 3,645.19 | +482.82 | 66.7% | 4,326.90 |
| Ridge + Chronos-Bolt-small | 3,428.08 | +699.93 | 3,658.58 | +469.43 | 66.7% | 4,326.90 |

Relative latest-row MAE improvement for Ridge versus Frozen v2:

`807.62 / 4128.01 = 19.56%`

Relative event-balanced window MAE improvement:

`508.83 / 4128.01 = 12.33%`

Mean absolute Ridge revision:

`1,737.45 seats`

## Ridge research-lead contract

Candidate ID:

`ridge-a10`

Target:

`target_live_delta_occupancy`

Preprocessing:

- numeric live features only;
- median imputation within training fold;
- missing-value indicators;
- standardization;
- Ridge `alpha=10.0`;
- event-balanced sample weights.

Final revision remains clipped to:

`+/-10 percentage points occupancy`

No event outside the held-out LOEO fold contributes outcome information to that fold.

## TSFM / Chronos decision

Chronos-2 and Chronos-Bolt-small both ran successfully under the causal zero-shot inventory-trajectory contract.

TSFM-ready rows:

- Chronos-2: `21/30`;
- Chronos-Bolt-small: `21/30`.

Both TSFM-assisted candidates improved Frozen v2, but **both were worse than the matching plain Ridge candidate**:

- Chronos-2 latest MAE: `3428.25` vs Ridge `3320.39`;
- Bolt-small latest MAE: `3428.08` vs Ridge `3320.39`.

Therefore:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Decision:

> Close the Stage-1 Chronos challenger. Do not fine-tune Chronos, add Lag-Llama, or add NeuralProphet on the same 9-event development set. Reopen the TSFM family only with materially more independent trajectory events or a materially new hypothesis.

## Critical risk

Ridge improves average MAE materially, but tail risk is still too high.

Worst latest-event degradation versus Frozen v2:

`+4,326.90 seats`

Therefore the next problem is **not primarily finding a more complex prediction model**.

The next problem is:

> **When should the live correction be trusted, reduced, or suppressed?**

This moves d2 to Stage 2 reliability / tail-risk governance.

## Next stage

Canonical next step:

`d2 Stage 2 — Reliability / Tail-Risk Gating`

Contract:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

Stage 2 must be designed and selected only on the frozen 9-event / 30-row development lineage.

Only after the Stage-2 policy is frozen may event `5` Lech–Korona be opened as a chronological/prospective holdout.

## Production boundary

No production change.

No automatic promotion.

No C1 v8 change.

No Pre-Live v2 change.

`live_adjustment = 0`
