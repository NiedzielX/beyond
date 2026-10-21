# d2 Long-Horizon Live Coverage Audit v1 — Result

Date: **2026-10-21**

Status: **COMPLETED / LONG_HORIZON_DATA_CONTRACT_READY / FIRST LEARNED WINDOW = 72H**

Canonical plan:

`ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md`

Workflow run:

`39638563805`

Evaluate-main job:

`119355910608`

Artifact:

`d2-long-horizon-export-v1-39638563805`

Artifact ID:

`12363731756`

Artifact ZIP SHA256:

`603933f21f8590f8a2a5efd8f223fbe995177c55b2fe6885b089eeb3223fc2c6`

Export JSON SHA256:

`b66ebf8699dac70be7135b4debe282aec3eb562dc55c67550e697c99c096a668`

Coverage audit JSON SHA256:

`5e7505797c52e8d86406942abeef9adca9232f75f1935319861355b2b202a2d1`

Main SHA:

`c6db582c4577c2a2f6f1bb3202acae69e1c3e872`

## Export contract

Version:

`d2-long-horizon-168-rows-v1`

Gateway route:

`v8-long168`

Sampling:

- maximum window: `168h` before kickoff;
- cadence: `6h`;
- one latest source snapshot per event x 6h bucket;
- PIT feature function: `get_live_trajectory_features_v1_1_asof`;
- same C1 Ekstraklasa / completed-outcome / verified-capacity eligibility as `v7-final24`.

The existing `v7-final24` export was not modified.

## End-to-end validation

Main-only GitHub OIDC access passed.

The additive export returned:

- **14 independent labeled events**;
- **240 live rows**;
- all rows `point_in_time_validated = true`;
- all rows have a non-null source feature snapshot;
- event x 6h bucket identities are unique.

Status:

`LONG_HORIZON_DATA_CONTRACT_READY`

## Coverage

Independent events with usable PIT rows beyond each boundary:

- beyond 24h: **13**;
- beyond 48h: **10**;
- beyond 72h: **8**.

The minimum independent-event threshold was frozen **before this decision** at:

`N = 9`

Source of the threshold:

`existing frozen d2 Stage-1 development event count`

Candidate learned windows:

| Candidate max live window | Independent events with earlier coverage | Readiness |
|---|---:|---|
| 48h | 13 | READY |
| 72h | 10 | **READY** |
| 168h | 8 | BELOW N=9 |

Decision:

`BUILD_FIRST_LONG_HORIZON_MODEL_TO_72H`

The 72–168h band remains:

`DIAGNOSTIC_ONLY_BELOW_EVENT_THRESHOLD`

## Why 72h

72h is the longest candidate window that satisfies the inherited N=9 independent-event floor.

We do **not** lower the threshold to 8 merely so the T-7 / 168h band can be modeled immediately.

This prevents selecting the research horizon to fit the currently available sample.

## Anchor implication

For the first learned long-horizon experiment, the deterministic checkpoint-hold anchor contract should be:

- `0 < hours_to_kickoff <= 24` -> Frozen Pre-Live **T-1** anchor;
- `24 < hours_to_kickoff <= 72` -> Frozen Pre-Live **T-3** anchor.

This mapping uses only a checkpoint already available at the row as-of time.

Do not use future T-1 prediction for rows earlier than T-1.

Because sealed v3 T-3 and T-1 are identical to Frozen v2, the first 72h learned experiment primarily tests the **incremental value of starting live trajectory updates earlier**, not the v3 T-7 anchor change.

The changed v3 T-7 anchor becomes relevant only in the `72–168h` band, which remains diagnostic until independent-event coverage reaches the predeclared threshold.

## Exposure boundary

The historical labeled event pool is already exposed research evidence.

Original frozen d2 development IDs:

`1,3,4,8,9,12,13,14,17`

Later labeled/exposed IDs include:

`5,11,15,18,19`

They may be used in explicitly labeled historical LOEO / chronological research, but must not be described as unseen prospective holdouts.

No random snapshot split is allowed.

Independent unit remains:

`event`

## Next required step

Create a fixed **d2-long72 data + anchor contract** before model fitting:

1. filter additive export to `0 < hours_to_kickoff <= 72`;
2. reconstruct T-3/T-1 checkpoint-hold anchor per row;
3. join exact outcomes/capacity and existing PIT live features;
4. persist event/as-of identities and coverage;
5. hard-assert no future checkpoint use;
6. freeze the machine-readable long72 dataset contract;
7. only then run Stage-1 learned-model tournament.

## Production boundary

Always:

- Track-A Frozen Pre-Live v2 / Ridge / P2 unchanged;
- Frozen Pre-Live v3 remains research-only;
- long-horizon work research-only;
- production unchanged;
- `live_adjustment = 0`.
