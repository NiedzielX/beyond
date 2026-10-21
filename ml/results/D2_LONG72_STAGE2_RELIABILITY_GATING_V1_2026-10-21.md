# d2 Long72 Stage 2 — Reliability Gating v1 — Result

Date: **2026-10-21**

Status: **COMPLETED / P2-OBSERVATION-MATURITY SELECTED / RESEARCH-ONLY**

Workflow run:

`39644319080`

Evaluate-main job:

`119375984602`

Artifact:

`d2-long72-stage2-reliability-gating-v1-39644319080`

Artifact ID:

`12366826274`

Artifact ZIP SHA256:

`c750cf385b2c6b6f05fabceaf68ff323a66235862967900419be421f7cdcb4ae`

Stage-2 JSON SHA256:

`a9daa834e15b4f313b15c3e809033b7d79e4ed4357f61a8f5071e6bf20359d8c`

Stage-2 predictions SHA256:

`489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b`

Parent Stage-1 artifact ID:

`12365399256`

Frozen long72 dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

## Decision

`STAGE2_RELIABILITY_POLICY_SELECTED`

Selected policy:

`P2-observation-maturity`

Stage-1 expert remains fixed:

`inventory-linear-extrapolation`

No model family, target or data split was changed during Stage 2.

## Exact selected policy

Reliability is the minimum of an observation-maturity weight and a time-to-kickoff weight.

Observation maturity:

- observation index 1 -> `0.25`;
- observation index 2 -> `0.60`;
- observation index >=3 -> `1.00`.

Time-to-kickoff:

- `60 < h <= 72` -> `0.75`;
- `48 < h <= 60` -> `0.90`;
- `24 < h <= 48` -> `1.00`.

Applied reliability:

`min(observation_weight, time_weight)`

Final early-live forecast:

`anchor_p50 + reliability * inventory_delta_occupancy * capacity`

The Stage-1 inventory correction remains capped at `±0.10` occupancy before Stage-2 reliability is applied.

## Primary result — 24–72h

Frozen anchor:

**3,707.14 MAE**

Raw Stage-1 inventory expert:

**3,254.68 MAE**

Selected P2 package:

**3,012.63 MAE**

P2 improvement versus anchor:

- **+694.51 seats MAE**;
- **+18.73%** relative improvement.

P2 also improves on the raw Stage-1 expert by about **242.05 MAE**.

Event-level behavior:

- event improvement rate: **61.54%**;
- worst event degradation: **1,488.34 seats**;
- event-balanced bias: **+917.05 seats**;
- mean absolute revision: **1,699.81 seats**.

Compared with raw Stage 1:

- worst-event degradation reduced by **52.0%** (`3100.60 -> 1488.34`);
- absolute bias reduced by **37.1%** (`1458.93 -> 917.05`);
- overall uplift retained at **153.5%** because the reliability policy improves aggregate MAE beyond the raw expert.

## 24–48h band

Anchor MAE:

**3,707.14**

P2 MAE:

**2,752.56**

Improvement:

- **+954.58 seats**;
- **+25.75%**.

Worst event degradation:

**1,504.80 seats**

Raw Stage-1 uplift retained:

**141.35%**

## 48–72h band

Anchor MAE:

**4,592.38**

P2 MAE:

**3,927.67**

Improvement:

- **+664.71 seats**;
- **+14.47%**.

Event improvement rate:

**70%**

Worst event degradation:

**2,413.28 seats**

Raw Stage-1 uplift retained:

**98.38%**

Worst-event degradation reduction versus raw Stage 1:

**35.5%**

## Temporal-subset stability

The raw Stage-1 expert was unstable across already-exposed historical subsets:

- original Stage-1 subset: **-485.52 MAE** versus anchor;
- later exposed subset: **+1,953.22 MAE**.

P2 restores positive uplift in both:

### Original exposed subset

- anchor MAE: **3,301.03**;
- P2 MAE: **3,197.47**;
- improvement: **+103.55**.

### Later exposed subset

- anchor MAE: **4,356.92**;
- P2 MAE: **2,716.88**;
- improvement: **+1,640.04**.

Neither subset is an unseen holdout. This is a development-stability diagnostic only.

## Gate result

P2 passed all predeclared Stage-2 gates:

- positive uplift overall 24–72h: PASS;
- positive uplift 24–48h: PASS;
- positive uplift 48–72h: PASS;
- retain >=50% raw uplift in every view: PASS;
- reduce worst degradation >=25% overall: PASS;
- reduce worst degradation >=25% in 48–72h: PASS;
- reduce absolute bias >=25%: PASS;
- positive uplift in original exposed subset: PASS;
- positive uplift in later exposed subset: PASS.

Other eligible policies:

- `P3-correction-magnitude`;
- `P4-data-quality`;
- `P5-combined-reliability`.

P2 won the predeclared selector because it had the lowest overall 24–72h event-balanced MAE among eligible policies.

## Important comparison

`P4-data-quality` has materially lower tail risk than P2:

- overall MAE: `3070.35`;
- overall uplift: `+636.79`;
- worst degradation: `775.15`;
- bias: `+652.48`.

However the selector was frozen before results and ranks eligible policies by overall MAE first. Therefore P2 remains the selected research policy; P4 is retained as a relevant tail-risk alternative, not substituted post hoc.

## Evidence boundary

All 13 Stage-2 events are historical exposed research evidence.

This result is **not** prospective promotion evidence.

The long72 package is therefore eligible for an immutable **research package freeze**, not production activation.

## Recommended research package

Package ID:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Composition:

- scope: `24 < h <= 72`;
- frozen checkpoint anchor: T-3;
- Stage-1 expert: inventory linear extrapolation;
- Stage-1 occupancy correction cap: `±0.10`;
- Stage-2 policy: `P2-observation-maturity`;
- Track-A final24 package remains separate and unchanged.

## Next evidence

The next high-value evidence is prospective/append-only scoring of the frozen early-live package on future completed events with valid 24–72h trajectories.

Do not tune the package from those outcomes.

The 72–168h band remains diagnostic-only until independent-event coverage reaches the predeclared `N=9` floor.

## Production boundary

Always:

- Track-A Frozen Pre-Live v2 / final24 Ridge / final24 P2 unchanged;
- long72 package research-only;
- Frozen Pre-Live v3 research-only;
- production unchanged;
- `live_adjustment = 0`.
