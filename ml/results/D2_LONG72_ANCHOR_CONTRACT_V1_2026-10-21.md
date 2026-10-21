# d2 Long72 — Frozen Data & Anchor Contract v1 — Result

Date: **2026-10-21**

Status: **FROZEN_LONG72_DATA_AND_ANCHOR_CONTRACT / NO MODEL TRAINING / NO PRODUCTION CHANGE**

Workflow run:

`39640723942`

Evaluate-main job:

`119363463989`

Artifact:

`d2-long72-anchor-contract-v1-39640723942`

Artifact ID:

`12365352293`

Artifact ZIP SHA256:

`83082cca46b6aa78fd744f59e9fd7eaaef6e7d33e8135817bda78a201b454561`

Contract JSON SHA256:

`0083b82be7de4599574b90ed0af44e1accd1a993c1d07b7f263bfbf01f3a1a27`

Dataset CSV SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

Main SHA:

`d02cd516b17484a9bdc9d75b3a859d93945046bb`

## Frozen dataset

- independent target events: **14**;
- rows: **130**;
- event IDs: `1,3,4,5,8,9,11,12,13,14,15,17,18,19`;
- minimum hours to kickoff: `0.166041`;
- maximum hours to kickoff: `67.732495`.

Rows by band:

- `0–24h`: **50** rows / **14** events;
- `24–48h`: **45** rows / **13** events;
- `48–72h`: **35** rows / **10** events.

## Frozen anchor rule

Deterministic checkpoint hold:

- `0 < hours_to_kickoff <= 24` -> frozen Pre-Live **T-1**;
- `24 < hours_to_kickoff <= 72` -> frozen Pre-Live **T-3**.

Future checkpoint use:

`false`

Sealed Pre-Live v2 and v3 use the exact same T-3/T-1 horizon packages, therefore the 0–72h anchor contract is equivalent for both freezes.

The changed v3 T-7 package is not used in this dataset.

## Same-season b2 replay

Current-season home-attendance rows available to replay:

**39**

Forecastable Structural Prior rows at each checkpoint:

- T-3: **36/39**;
- T-1: **36/39**.

Three earliest current-season home matches were not forecastable at those PIT cutoffs because no completed current-season sporting state existed yet. They remain explicitly recorded as unforecastable; no neutral or synthetic sporting state is invented.

Frozen b2 policies:

- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

Both replay states had 13 rows meeting the maturity gate. Maximum absolute b2 correction observed in the replay was about **2,163.45 seats**.

## Capacity / source lineage

The replay uses a separate service-role capacity-registry export valid at each historical kickoff rather than extending the original 9-event Stage-0 capacity audit beyond its scope.

Input SHA256 lineage:

- events: `44f8547a134f87b665b0eeab4ca8a8acc9f18c382c0b39dca99979e763f8719d`;
- attendance: `b6327bca37e6e8685626dedf108ec58a42bad5d303e26091e6dc67f747db7518`;
- sporting: `a1843ea8f99bb7f9d9d7e1bf0f97a67e19d0fe825291653c061efa399da9914e`;
- aliases: `da729ebf7a9d44e47a5816ae8f5463c7665f45138fdb082382209721c918e171`;
- capacity registry export: `24afbac79c1c33786063ce3c36d9178c870b9557a52359169299f90f3298a51e`;
- long168 export: `431a20f3b76dab450352f064703aa71d094cfae67a4998d2fdaedfc1c17b983a`;
- v2 manifest: `8f11f201aa6eff39de02c489ceac6d00ca9d3e161f295ea3c41119ce4f5d74f4`;
- v3 manifest: `b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`.

## Stage-1 modeling boundary

The first learned long-horizon expert will target **only `24 < h <= 72`**.

Reason:

- final 24h already has the frozen Ridge/P2 research package;
- the new scientific question is whether live trajectory adds value *before* the final day;
- 24–72h contains **80 rows** across **13 independent events**;
- 48–72h still contains **10 events**, above the inherited `N=9` floor.

Stage-1 rules:

- target: live residual occupancy relative to the frozen checkpoint anchor;
- independent unit: event;
- validation: LOEO, all rows from held-out event excluded from training;
- event-balanced training/evaluation;
- correction cap: `±0.10` occupancy;
- primary metric: event-balanced MAE on 24–72h;
- mandatory separate metrics: 24–48h and 48–72h;
- no random snapshot split;
- no claim that any of these 14 historical labels is unseen prospective evidence.

## Next

`d2-long72-stage1-model-tournament-v1`

Final-24h Track-A v2/Ridge/P2 and production remain unchanged.

`live_adjustment = 0`
