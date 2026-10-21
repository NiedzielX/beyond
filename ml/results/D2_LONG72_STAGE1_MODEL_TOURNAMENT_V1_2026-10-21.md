# d2 Long72 Stage 1 — Early-Live Model Tournament v1 — Result

Date: **2026-10-21**

Status: **COMPLETED / RESEARCH LEAD = INVENTORY LINEAR EXTRAPOLATION / NO PRODUCTION CHANGE**

Workflow run:

`39642620259`

Evaluate-main job:

`119369990559`

Artifact:

`d2-long72-stage1-model-tournament-v1-39642620259`

Artifact ID:

`12365399256`

Artifact ZIP SHA256:

`e73ffe55d1c83b7a37fb50109c909f22d1a075a6b1de8f42c89364523399dfbb`

Stage-1 JSON SHA256:

`f19ea1378d0f8b07007bf45c2ab7f3fa20ebb3c53e32afa4548723336b71358a`

Predictions CSV SHA256:

`33de331d2c3bf1e385f513c7fa7e28aa8b454a4d49cfe00d48163e6c083a6df5`

Frozen long72 dataset SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

## Evaluation contract

- scope: `24 < hours_to_kickoff <= 72` only;
- rows: **80**;
- independent events: **13**;
- 48–72h band: **35 rows / 10 events**;
- target: occupancy residual versus frozen T-3 checkpoint anchor;
- validation: Leave-One-Event-Out;
- event-balanced training and MAE evaluation;
- maximum live correction: `±0.10` occupancy;
- all historical outcome labels are exposed research evidence;
- final24 Ridge/P2 is outside this selector and remains unchanged.

## Candidate set

1. anchor zero correction;
2. train-fold bias;
3. inventory linear extrapolation;
4. Ridge alpha 10;
5. Ridge alpha 30;
6. Huber;
7. small HistGradientBoosting absolute-error model.

A challenger was eligible only if it improved event-balanced MAE in all three predeclared views:

- overall 24–72h;
- 24–48h;
- 48–72h.

## Leaderboard

| Candidate | 24–72h MAE | Overall uplift | 24–48 uplift | 48–72 uplift | Eligible |
|---|---:|---:|---:|---:|---|
| Anchor / zero correction | 3,707.14 | 0.00 | 0.00 | 0.00 | baseline |
| **Inventory linear extrapolation** | **3,254.68** | **+452.46** | **+675.33** | **+675.68** | **yes** |
| Ridge alpha 30 | 3,473.54 | +233.59 | +205.21 | +527.32 | yes |
| Ridge alpha 10 | 3,500.53 | +206.61 | +206.70 | +502.00 | yes |
| Train-fold bias | 3,915.67 | -208.53 | -208.53 | -265.46 | no |
| Huber | 4,312.99 | -605.85 | -425.48 | -484.21 | no |
| HGB | 4,631.79 | -924.66 | -1,136.93 | -604.96 | no |

Decision:

`RESEARCH_LEAD = inventory-linear-extrapolation`

## Lead performance

### Overall 24–72h

- anchor MAE: **3,707.14**;
- inventory MAE: **3,254.68**;
- absolute MAE improvement: **+452.46 seats**;
- relative improvement: **+12.21%**;
- event improvement rate: **46.15%**;
- worst event degradation: **3,100.60 seats**;
- event-balanced bias: **+1,458.93 seats**;
- mean absolute revision: **2,323.83 seats**.

### 24–48h

- anchor MAE: **3,707.14**;
- inventory MAE: **3,031.81**;
- improvement: **+675.33 / +18.22%**;
- worst event degradation: **3,100.60 seats**.

### 48–72h

- anchor MAE: **4,592.38**;
- inventory MAE: **3,916.71**;
- improvement: **+675.68 / +14.71%**;
- event improvement rate: **60%**;
- worst event degradation: **3,741.79 seats**.

## Temporal/exposure heterogeneity

The research lead is not stable across the two already-exposed historical subsets.

### Original frozen Stage-1 IDs

8 early-live events / 40 rows:

- anchor MAE: **3,301.03**;
- inventory MAE: **3,786.54**;
- change: **-485.52 MAE** — worse than anchor.

### Later exposed IDs

5 events / 40 rows:

- anchor MAE: **4,356.92**;
- inventory MAE: **2,403.70**;
- change: **+1,953.22 MAE**.

This heterogeneity is a known Stage-1 limitation and must be addressed explicitly in Stage 2. Neither subgroup is an unseen holdout.

## Interpretation

Early ticket trajectory contains real predictive value before the final 24 hours: the transparent inventory extrapolation beats the frozen pre-live anchor in both time bands and beats all learned challengers under the predeclared selector.

However the raw rule is not acceptable as a frozen early-live package yet because:

- positive bias is large;
- event-level tail degradation is material;
- fewer than half of events improve overall;
- historical subset behavior is strongly heterogeneous.

Therefore Stage 1 closes with a **research lead**, not a promotion candidate.

## Next

`d2-long72-stage2-reliability-gating-v1`

Stage 2 must keep the Stage-1 expert fixed and test a small predeclared set of causal reliability policies around its proposed correction.

Minimum advancement requirements:

- remain better than anchor overall, 24–48h and 48–72h;
- retain a material share of the raw Stage-1 uplift;
- materially reduce worst-event degradation;
- return to positive uplift on both exposed temporal subsets;
- no production write.

Track-A v2/Ridge/P2 remains unchanged.

`live_adjustment = 0`
