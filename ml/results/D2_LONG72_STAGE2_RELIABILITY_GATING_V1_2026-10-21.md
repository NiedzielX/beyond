# d2 Long72 Stage 2 — Reliability / Tail Governance v1 — Result

Date: **2026-10-21**

Status: **COMPLETED / P2-OBSERVATION-MATURITY SELECTED / HISTORICAL RESEARCH PACKAGE / NO PRODUCTION CHANGE**

Workflow run:

`39644319080`

Evaluate-main job:

`119375984602`

Main SHA:

`7369d87f3d9fb8fe722da4eddacf5436098223d6`

Artifact:

`d2-long72-stage2-reliability-gating-v1-39644319080`

Artifact ID:

`12366826274`

Artifact ZIP SHA256:

`c750cf385b2c6b6f05fabceaf68ff323a66235862967900419be421f7cdcb4ae`

Stage-2 JSON SHA256:

`a9daa834e15b4f313b15c3e809033b7d79e4ed4357f61a8f5071e6bf20359d8c`

Stage-2 predictions CSV SHA256:

`489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b`

Frozen Stage-1 predictions SHA256:

`33de331d2c3bf1e385f513c7fa7e28aa8b454a4d49cfe00d48163e6c083a6df5`

Frozen long72 dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

## Decision

`STAGE2_RELIABILITY_POLICY_SELECTED`

Selected policy:

`P2-observation-maturity`

Eligible policies:

- `P2-observation-maturity`;
- `P3-correction-magnitude`;
- `P4-data-quality`;
- `P5-combined-reliability`.

The selector chose P2 because it delivered the lowest event-balanced 24–72h MAE among all policies that passed every predeclared accuracy, tail, bias and temporal-subset gate.

## Frozen Stage-1 expert

Stage 2 did not retrain the live expert.

Frozen expert:

`inventory-linear-extrapolation`

Stage-1 raw inventory reference:

- anchor MAE: `3707.1382`;
- raw inventory MAE: `3254.6810`;
- uplift vs anchor: `+452.4572 / +12.21%`;
- event improvement rate: `46.15%`;
- bias: `+1458.9350 seats`;
- worst event degradation: `3100.60 seats`.

## Selected P2 policy

Reliability is causal and deterministic.

Observation maturity weight:

- first admitted early-live observation: `0.25`;
- second observation: `0.60`;
- third and later: `1.00`.

Time-to-kickoff weight:

- `60–72h`: `0.75`;
- `48–60h`: `0.90`;
- `24–48h`: `1.00`.

Applied reliability:

`min(observation_weight, time_weight)`

Forecast:

`anchor_p50 + reliability * frozen_inventory_delta_occupancy * capacity`

clipped to `[0, capacity]`.

No outcome label enters policy logic.

## P2 — overall 24–72h

- anchor MAE: **`3707.14`**;
- P2 MAE: **`3012.63`**;
- improvement vs anchor: **`+694.51 seats`**;
- relative improvement: **`+18.73%`**;
- improvement over raw Stage-1 inventory MAE: **`242.05 seats`**;
- event improvement rate: **`61.54%` = 8/13 events**;
- event-balanced bias: **`+917.05 seats`**;
- mean absolute revision: `1699.81 seats`;
- worst event degradation: **`1488.34 seats`**.

Compared with raw Stage 1:

- retained uplift share: **`153.50%`** — the reliability policy improves MAE more than raw inventory;
- worst-event degradation reduction: **`52.00%`**;
- absolute bias reduction: **`37.14%`**.

## P2 — 24–48h

- anchor MAE: `3707.14`;
- P2 MAE: **`2752.56`**;
- improvement: **`+954.58 / +25.75%`**;
- event improvement rate: `61.54%`;
- worst event degradation: `1504.80 seats`;
- retained raw Stage-1 uplift share: **`141.35%`**.

## P2 — 48–72h

- anchor MAE: `4592.38`;
- P2 MAE: **`3927.67`**;
- improvement: **`+664.71 / +14.47%`**;
- event improvement rate: **`70% = 7/10 events`**;
- worst event degradation: **`2413.28 seats`**;
- retained raw Stage-1 uplift share: **`98.38%`**;
- worst-event degradation reduction vs raw inventory: **`35.50%`**.

## Temporal / exposed-subset stability

Raw inventory was strongly heterogeneous:

- original exposed subset: `-485.52 MAE` vs anchor;
- later exposed subset: `+1953.22 MAE`.

P2 changes both subsets to positive historical uplift:

### Original exposed Stage-1 subset

- anchor MAE: `3301.03`;
- P2 MAE: **`3197.47`**;
- improvement: **`+103.55 MAE`**.

### Later exposed subset

- anchor MAE: `4356.92`;
- P2 MAE: **`2716.88`**;
- improvement: **`+1640.04 MAE`**.

Neither subset is unseen or prospective. This is historical stability evidence only.

## Other eligible policies

### P3 — correction magnitude

- overall MAE `3326.39`;
- uplift `+380.75`;
- bias `+389.14`;
- worst degradation `1085.21`;
- original subset `+200.32`;
- later subset `+669.43`.

P3 controls risk aggressively but gives up too much MAE versus P2.

### P4 — data quality

- overall MAE `3070.35`;
- uplift `+636.79`;
- bias `+652.48`;
- worst degradation `775.15`;
- 48–72h uplift `+823.93`;
- original subset `+92.26`;
- later subset `+1508.03`.

P4 is the strongest tail-risk alternative, but P2 has lower overall MAE under the predeclared selector.

### P5 — combined reliability

- overall MAE `3375.22`;
- uplift `+331.92`;
- bias `+270.04`;
- worst degradation `775.15`;
- original subset `+132.03`;
- later subset `+651.74`.

P5 is conservative but sacrifices too much accuracy.

## Interpretation

The Stage-1 early inventory signal survives stronger risk governance.

More importantly, **P2 improves both accuracy and stability at the same time**:

- lower MAE than raw inventory;
- more events improved;
- materially smaller tail degradation;
- materially smaller bias;
- positive result on both already-exposed historical subsets.

This is enough to seal a **historical long72 research package**.

It is **not** enough for production promotion because all 13 evaluated events are historical/exposed research evidence.

## Historical package to seal

Package ID:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Components:

- window: `24–72h`;
- anchor: frozen T-3 checkpoint hold;
- expert: `inventory-linear-extrapolation`;
- reliability policy: `P2-observation-maturity`;
- correction cap inherited from Stage 1: `±10pp occupancy` before reliability scaling;
- evidence class: `EXPOSED_HISTORICAL_R_AND_D`;
- production allowed: `false`.

## Next

1. seal the package manifest with exact Stage-1 / Stage-2 lineage;
2. create a forward-scoring contract that applies this package without retuning;
3. score genuinely new eligible events prospectively;
4. keep final24 Track-A Ridge/P2 unchanged;
5. reopen 72–168h / T-7-aware learned R&D only after independent-event coverage reaches the frozen N=9 threshold.

## Production boundary

Always:

- Track-A Frozen Pre-Live v2 / final24 Ridge / P2 unchanged;
- Frozen Pre-Live v3 remains research-only;
- long72 P2 package remains research-only until forward evidence exists;
- production unchanged;
- `live_adjustment = 0`.
