# d2 Long72 Stage 1 — Model Tournament v1

Last updated: **2026-10-21**

Status: **PREDECLARED / READY TO RUN / HISTORICAL R&D ONLY**

Pinned input:

- artifact ID `12365352293`;
- dataset SHA256 `2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`;
- contract SHA256 `0083b82be7de4599574b90ed0af44e1accd1a993c1d07b7f263bfbf01f3a1a27`;
- 14 events / 130 rows;
- exact event IDs `1,3,4,5,8,9,11,12,13,14,15,17,18,19`.

## Question

> **Does live ticket trajectory improve the PIT Pre-Live checkpoint anchor in the new 24–72h window?**

This is not a rerun of final-24h d2. The new learned window starts earlier and uses checkpoint hold:

- `0 < h <= 24` -> T-1;
- `24 < h <= 72` -> T-3.

## Evidence class

All 14 outcomes are already exposed historical research evidence.

Validation:

`event-level LOEO`

All rows from the held-out event remain together.

No random snapshot split.

No candidate may claim unseen holdout or prospective evidence.

## Target

Primary supervised target:

`actual_attendance / capacity - checkpoint_anchor_p50 / capacity`

Final row forecast:

`clip(anchor_p50 + predicted_delta_occupancy * capacity, 0, capacity)`

Correction cap:

`±10 percentage points occupancy`

## Candidate set

Reuse the bounded Stage-1 family set rather than opening another model zoo:

1. `frozen-v2-zero-correction` — checkpoint anchor only;
2. `train-fold-bias`;
3. `inventory-linear-extrapolation`;
4. `ridge-a10`;
5. `huber-a001`;
6. `histgbr-abs-l7-leaf5-l2-10`;
7. `ridge-a10-plus-chronos2`;
8. `ridge-a10-plus-bolt-small`.

The naming `frozen-v2-zero-correction` is retained for code compatibility; in this experiment its numeric anchor is the frozen long72 T-3/T-1 checkpoint hold, which is equivalent under sealed v2 and v3 in this window.

## Learned-model runtime

Same Stage-1 parameters as already audited:

- Ridge `alpha=10`;
- Huber `epsilon=1.35`, `alpha=0.01`, `max_iter=1000`;
- HistGradientBoosting absolute-error, learning rate `0.05`, `100` iterations, `max_leaf_nodes=7`, `min_samples_leaf=5`, L2 `10`, seed `42`;
- event-balanced training weights.

TSFM runtime remains pinned:

- `chronos-forecasting==2.3.2`;
- Chronos-2 `amazon/chronos-2` revision `95a9710e2596287d08352589f42634fa5abdf0a7`;
- Chronos-Bolt-small `amazon/chronos-bolt-small` revision `0e96a1377adca89eebae3bbde4f859dc3b9f4b46`.

TSFM target remains causal inventory only:

`available_share_of_capacity`

Final attendance/residual labels never enter TSFM context.

## Primary metrics

Report event-balanced MAE for:

- full `0–72h`;
- `0–24h`;
- `24–48h`;
- `48–72h`;
- combined **`24–72h`**.

Also report:

- event improvement rate;
- worst event degradation;
- latest-row MAE as diagnostic continuity with original d2;
- revision magnitude and bias.

## Predeclared research selector

A challenger is eligible only if:

1. full `0–72h` event-balanced MAE improves vs anchor;
2. combined `24–72h` event-balanced MAE improves vs anchor;
3. `48–72h` event-balanced MAE is non-worse vs anchor.

Among eligible candidates rank by:

1. lowest `24–72h` event-balanced MAE;
2. lowest `48–72h` event-balanced MAE;
3. lowest full `0–72h` event-balanced MAE;
4. lowest worst-event degradation in `24–72h`;
5. candidate ID tie-break.

If nobody passes, retain zero correction as research lead.

## Interpretation

A winner means only:

`LONG72_HISTORICAL_RESEARCH_LEAD`

It does not replace Track-A Frozen v2/Ridge/P2 and does not enter production.

If the lead materially improves early MAE but has unacceptable event tail risk, next work is reliability/gating for long72 rather than blind retraining.

If no challenger improves the anchor, close this candidate family for long72 and move to a materially different early-live target/feature hypothesis.

## Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- v3 research-only;
- long72 research-only;
- promotion not allowed from this experiment;
- production `live_adjustment = 0`.
