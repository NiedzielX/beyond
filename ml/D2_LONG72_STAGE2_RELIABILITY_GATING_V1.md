# d2 Long72 Stage 2 — Reliability / Tail-Risk Gating v1

Last updated: **2026-10-21**

Status: **PREDECLARED / READY TO RUN / HISTORICAL R&D ONLY**

Parent result:

`ml/results/D2_LONG72_STAGE1_MODEL_TOURNAMENT_V1_2026-10-21.md`

Frozen Stage-1 research lead:

`inventory-linear-extrapolation`

## Purpose

Stage 1 proved that live inventory trajectory has useful historical signal in `24–72h`, but the raw rule still has large positive bias, material worst-event degradation and strong temporal heterogeneity.

Stage 2 does **not** retrain or replace the Stage-1 expert.

It tests whether a small fixed set of causal reliability policies can keep a material share of the MAE gain while reducing tail harm and bias.

## Pinned inputs

Frozen long72 artifact:

- artifact ID `12365352293`;
- ZIP SHA256 `83082cca46b6aa78fd744f59e9fd7eaaef6e7d33e8135817bda78a201b454561`;
- dataset CSV SHA256 `2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`.

Frozen Stage-1 evidence artifact:

- artifact ID `12365399256`;
- ZIP SHA256 `e73ffe55d1c83b7a37fb50109c909f22d1a075a6b1de8f42c89364523399dfbb`;
- Stage-1 JSON SHA256 `f19ea1378d0f8b07007bf45c2ab7f3fa20ebb3c53e32afa4548723336b71358a`;
- Stage-1 predictions CSV SHA256 `33de331d2c3bf1e385f513c7fa7e28aa8b454a4d49cfe00d48163e6c083a6df5`.

Stage 2 must hard-fail if any pinned hash or canonical raw-lead metric drifts.

## Evidence boundary

Scope:

`24 < hours_to_kickoff <= 72`

Independent events:

`13`

Rows:

`80`

All labels are already exposed historical R&D evidence.

Stage 2 is policy selection on historical evidence only. It cannot create unseen or prospective evidence and cannot promote production.

## Frozen raw-lead reference

Canonical raw inventory values that must reproduce before policies are scored:

- overall 24–72h MAE: `3254.6809517243155`;
- overall uplift vs anchor: `+452.4572219222955`;
- 24–48h uplift: `+675.3308228020314`;
- 48–72h uplift: `+675.6771220422229`;
- overall worst-event degradation: `3100.60`;
- 48–72h worst-event degradation: `3741.7941628246845`;
- absolute event-balanced bias: `1458.934971360056`.

## Reliability formula

For every row:

`final_delta_occupancy = reliability * frozen_inventory_delta_occupancy`

`forecast = clip(anchor_p50 + final_delta_occupancy * capacity, 0, capacity)`

Reliability is bounded to `[0,1]` and may use only causal information available at the row `as_of_at`.

Outcome labels are used only for scoring after the policy prediction is created.

## Fixed policy set

### P0 — anchor

`reliability = 0`

No early-live correction.

### P1 — raw inventory

`reliability = 1`

Exact frozen Stage-1 lead.

### P2 — observation maturity

Reuse the final24 P2 observation-maturity shape, scaled to the earlier 24–72h window.

Observation index weight:

- first admitted early-live observation: `0.25`;
- second: `0.60`;
- third and later: `1.00`.

Time weight:

- `60–72h`: `0.75`;
- `48–60h`: `0.90`;
- `24–48h`: `1.00`.

Final reliability:

`min(observation_weight, time_weight)`

### P3 — correction magnitude

Use the same fixed occupancy-correction bands as final24 Stage 2:

- `|delta| <= 2.5pp` -> `1.00`;
- `<= 5.0pp` -> `0.80`;
- `<= 7.5pp` -> `0.55`;
- `> 7.5pp` -> `0.35`.

### P4 — data quality

Start at `1.00`.

Soft warning -> cap at `0.50`:

- release activity;
- sector coverage change;
- max visible gap >12h.

Hard warning -> cap at `0.25`:

- signal not ready;
- feature quality not good;
- data gap detected;
- unexplained inventory increase.

### P5 — combined reliability

`min(P2, P3, P4)`

No additional coefficients are fitted.

## Advancement gates

P0 and P1 are references and cannot be selected as a new Stage-2 policy.

A Stage-2 policy is eligible only when **all** conditions pass:

1. MAE improvement vs anchor remains positive overall 24–72h;
2. MAE improvement remains positive in 24–48h;
3. MAE improvement remains positive in 48–72h;
4. retains at least **50%** of raw Stage-1 uplift overall;
5. retains at least **50%** of raw Stage-1 uplift in 24–48h;
6. retains at least **50%** of raw Stage-1 uplift in 48–72h;
7. reduces overall worst-event degradation by at least **25%** vs raw inventory;
8. reduces 48–72h worst-event degradation by at least **25%**;
9. reduces absolute overall bias by at least **25%**;
10. historical uplift is positive on the original exposed Stage-1 subset;
11. historical uplift is positive on the later exposed subset.

These gates are fixed before opening Stage-2 policy results.

If no policy passes:

`RAW_INVENTORY_RETAINED_NO_STAGE2_POLICY_PASSED`

This means the Stage-2 reliability challenger is not proven. It does **not** close long-horizon R&D.

## Ranking among eligible policies

1. lowest overall 24–72h event-balanced MAE;
2. lowest 48–72h event-balanced MAE;
3. lowest overall worst-event degradation;
4. policy ID tie-break.

## What Stage 2 may conclude

### `STAGE2_RELIABILITY_POLICY_SELECTED`

A bounded historical reliability policy improves the risk/accuracy trade-off enough to become the current long72 historical research package.

It still requires future prospective / chronological evidence before promotion.

### `RAW_INVENTORY_RETAINED_NO_STAGE2_POLICY_PASSED`

None of the fixed reliability policies passes all gates.

Keep raw inventory as the historical Stage-1 lead, but do not freeze it as a production candidate. Move to a materially different long72 reliability/target hypothesis rather than relaxing gates on the same evidence.

## Production boundary

Always:

- Track-A Frozen Pre-Live v2 / final24 Ridge / P2 unchanged;
- Frozen Pre-Live v3 research-only;
- long72 research-only;
- no production write;
- `live_adjustment = 0`.
