# Beyond Ticketing — d2 Stage 2 Reliability / Tail-Risk Gating v1 — Result

Date: **2026-10-19**

Status: **COMPLETED / P2 OBSERVATION MATURITY SELECTED / FROZEN RESEARCH CANDIDATE / NO PRODUCTION CHANGE**

## Decision

Selected Stage-2 policy:

`P2-observation-maturity`

Frozen research package ID:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Stage 2 advances this policy around the frozen Stage-1 expert:

`ridge-a10`

Production remains unchanged:

`live_adjustment = 0`

## Canonical CI evidence

Workflow run:

`39308629738`

Main commit:

`4dc653f0f021c4b05aecadc985d55b69afa1dc11`

Artifact:

`d2-stage2-reliability-gating-v1-39308629738`

Artifact ID:

`12214478156`

Artifact ZIP SHA256:

`b4ae9183f398a8cd13542390ce05734f050697e903d34242d793b28854bf9296`

Evidence hashes:

- split manifest: `5591880cff101ed316c4acae87fb0cb549ef9d5a987126b63245e154adb5a822`;
- Stage-0 JSON: `bb8a7c8ef3c719bca0c54da8961aea92d8484168b6493c768fe88c53f316985a`;
- Stage-0 CSV: `ec7aef2f458ae1db2fdaced7e0a051fe8b9035eccdb3764b0f640c6078aa6954`;
- Stage-2 JSON: `1190e3ef033d31323d94b67a4055b06aa3c9fedfd353c0065c9cbe67d5c07a53`;
- Stage-2 predictions CSV: `37de034c59bfb47e2aaec6f6ee4185f69228e0272baa13f319d35c4aad65bd83`.

## Frozen development boundary

Development events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Rows:

`30`

Independent unit:

`event`

Validation:

`LOEO_STAGE1_RIDGE_THEN_CAUSAL_POLICY`

Reserved holdout event `5` was present only in the append-only exporter and explicitly excluded from selection.

Current exporter at run time:

- 10 completed events;
- 34 final-24h rows.

Frozen Stage-2 development set remained exactly 9 events / 30 rows.

## Frozen Stage-1 expert

Expert:

`ridge-a10`

Stage-2 reproduction checks passed for:

- Frozen-v2 latest MAE: `4128.012628960847`;
- raw Ridge latest MAE: `3320.3922579543546`;
- raw Ridge event-balanced window MAE: `3619.185330638812`;
- raw Ridge worst latest-event degradation: `4326.9000000000015`.

Ridge was not retuned.

## Policy tournament

| Policy | Latest MAE | Latest uplift vs Frozen v2 | Window MAE | Window uplift | Worst latest-event degradation | p90 degradation | Mean reliability |
|---|---:|---:|---:|---:|---:|---:|---:|
| P0 Frozen v2 | 4,128.01 | 0.00 | 4,128.01 | 0.00 | 0.00 | 0.00 | 0.000 |
| P1 Raw Ridge | 3,320.39 | +807.62 | **3,619.19** | **+508.83** | 4,326.90 | 1,683.09 | 1.000 |
| **P2 Observation maturity** | **3,240.99** | **+887.02** | 3,657.65 | +470.36 | **1,081.72** | 1,034.05 | 0.682 |
| P3 Correction magnitude | 3,754.30 | +373.72 | 3,900.57 | +227.44 | 1,514.42 | **957.05** | 0.702 |
| P4 Data quality | 3,821.93 | +306.08 | 3,986.70 | +141.31 | 1,081.72 | **625.20** | 0.475 |
| P5 Combined reliability | 3,805.79 | +322.22 | 3,965.32 | +162.69 | 1,081.72 | **625.20** | 0.403 |

Eligible policy IDs under the frozen gates:

`[P2-observation-maturity]`

No other policy passed all advancement requirements.

## P2 result

Latest-row MAE:

`3240.98832774145`

Improvement vs Frozen Pre-Live v2:

`887.0243012193969 seats`

Relative improvement vs Frozen Pre-Live v2:

**21.49%**

Additional latest-row improvement vs raw Ridge:

`79.4039302129046 seats`

Relative latest-row improvement vs raw Ridge:

**2.39%**

Event-balanced window MAE:

`3657.652928009208`

Window improvement vs Frozen Pre-Live v2:

`470.35970095163793 seats`

Relative window improvement vs Frozen v2:

**11.39%**

P2 is `38.47 seats` worse than raw Ridge on event-balanced window MAE, but retains:

**92.44%** of raw Ridge window uplift.

Worst latest-event degradation:

`1081.7249999999985 seats`

Reduction vs raw Ridge:

**75.00%**

p90 latest-event degradation:

`1034.0510489664289 seats`

Reduction vs raw Ridge p90:

**38.56%**

Mean reliability across all development rows:

`0.6816666666666668`

## Frozen P2 contract

P2 uses no fitted threshold search and no outcome information.

Observation-index weight:

- first observation: `0.25`;
- second observation: `0.60`;
- third or later: `1.00`.

Time-to-kickoff cap:

- `hours_to_kickoff > 18`: `0.75`;
- `12 < hours_to_kickoff <= 18`: `0.90`;
- `hours_to_kickoff <= 12`: `1.00`.

Final reliability:

`min(observation_index_weight, time_weight)`

Forecast:

`final_forecast = frozen_v2 + reliability * ridge_delta`

The underlying raw Ridge correction remains capped to +/-10pp occupancy by the frozen Stage-1 contract.

## Advancement gates

Frozen before canonical scoring:

- retained latest uplift >= `50%`;
- retained window uplift >= `50%`;
- worst-degradation reduction >= `25%`;
- both latest-row and event-balanced window MAE must beat Frozen v2.

P2 achieved:

- retained latest uplift: **109.83%**;
- retained window uplift: **92.44%**;
- worst-degradation reduction: **75.00%**;
- latest MAE better than Frozen v2: yes;
- window MAE better than Frozen v2: yes.

Decision:

`STAGE2_RELIABILITY_POLICY_SELECTED`

## Interpretation

Stage 2 materially improves the risk/return profile of d2.

The key failure mode of raw Ridge was over-trusting very early trajectories. Observation maturity fixes that failure without needing a more complex model:

- raw Ridge average latest MAE improves materially over Frozen v2;
- P2 improves latest MAE further;
- P2 dramatically reduces worst-event harm;
- P2 preserves most of the trajectory-window uplift.

This is stronger evidence than Stage 1 alone, but it is still development evidence on the original 9 completed events.

## Reserved chronological holdout

Event `5` remains the next evaluation target:

- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- stadium capacity `43,269`;
- 4 final-24h rows.

Stage 2 was selected without using this event.

Now that P2 is frozen, event 5 may be opened exactly once as the first chronological holdout.

Compare:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen `P2-observation-maturity` governed Ridge;
4. frozen C1 v8 where contract-compatible.

No retuning after opening event 5.

## Production boundary

No production change.

No automatic promotion.

Frozen Pre-Live v2 unchanged.

Frozen C1 v8 unchanged.

`live_adjustment = 0`
