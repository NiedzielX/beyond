# d2 Long72 Data + Anchor Contract v1 — Result

Date: **2026-10-21**

Status: **FROZEN_LONG72_DATA_AND_ANCHOR_CONTRACT / READY_FOR_STAGE1_TOURNAMENT**

Workflow run:

`39640723942`

Evaluate-main job:

`119363463989`

Main SHA:

`d02cd516b17484a9bdc9d75b3a859d93945046bb`

Artifact:

`d2-long72-anchor-contract-v1-39640723942`

Artifact ID:

`12365352293`

Artifact ZIP SHA256:

`83082cca46b6aa78fd744f59e9fd7eaaef6e7d33e8135817bda78a201b454561`

Frozen contract JSON SHA256:

`0083b82be7de4599574b90ed0af44e1accd1a993c1d07b7f263bfbf01f3a1a27`

Frozen dataset CSV SHA256:

`2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c`

## Frozen dataset

Independent events:

`14`

Event IDs:

`1,3,4,5,8,9,11,12,13,14,15,17,18,19`

Rows:

`130`

Coverage:

| Live band | Rows | Independent events |
|---|---:|---:|
| 0–24h | 50 | 14 |
| 24–48h | 45 | 13 |
| 48–72h | 35 | 10 |

Observed range:

- closest row: `0.166041h` before kickoff;
- earliest admitted row: `67.732495h` before kickoff.

## PIT anchor rule

Deterministic checkpoint hold:

- `0 < h <= 24` -> frozen Pre-Live **T-1**;
- `24 < h <= 72` -> frozen Pre-Live **T-3**.

Future checkpoint use is forbidden.

Sealed Pre-Live v2 and v3 are equivalent for T-3 and T-1, so this exact 0–72h anchor contract is valid for both freezes.

The changed v3 T-7 package is intentionally not used in this dataset because the learned 72–168h band remains below the inherited N=9 independent-event threshold.

## Current-season replay

Full 2026/27 home-attendance history available to the replay:

`39` rows.

Capacity for every historical home match is resolved from the versioned registry at the match kickoff date.

Current-season b2 replay is horizon-specific. A completed match contributes to a horizon's b2 residual state only if that horizon's Structural Prior was reconstructable at its own PIT cutoff.

For both T-3 and T-1:

- forecastable historical rows: `36/39`;
- early-season unforecastable rows: `3`;
- those rows are recorded explicitly and are **not** filled with synthetic sporting state;
- all 14 tracked live events have every checkpoint anchor required by their admitted long72 rows.

Frozen b2 variants remain unchanged:

- T-3: `ewma50 residual`, shrink `k=2`, maturity `min3`;
- T-1: `ewma50 residual`, shrink `k=6`, maturity `min3`.

## Input lineage hashes

- events export: `44f8547a134f87b665b0eeab4ca8a8acc9f18c382c0b39dca99979e763f8719d`;
- attendance export: `b6327bca37e6e8685626dedf108ec58a42bad5d303e26091e6dc67f747db7518`;
- sporting export: `a1843ea8f99bb7f9d9d7e1bf0f97a67e19d0fe825291653c061efa399da9914e`;
- aliases export: `da729ebf7a9d44e47a5816ae8f5463c7665f45138fdb082382209721c918e171`;
- capacity export: `24afbac79c1c33786063ce3c36d9178c870b9557a52359169299f90f3298a51e`;
- long168 export: `431a20f3b76dab450352f064703aa71d094cfae67a4998d2fdaedfc1c17b983a`;
- v2 manifest: `8f11f201aa6eff39de02c489ceac6d00ca9d3e161f295ea3c41119ce4f5d74f4`;
- v3 manifest: `b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`.

## Exposure boundary

All 14 labels are historical/exposed research evidence.

This dataset is suitable for event-level LOEO historical model comparison and bounded R&D selection only.

It is **not** an unseen holdout and cannot by itself justify production promotion.

## Next

Run:

`d2-long72-stage1-model-tournament-v1`

against this exact pinned dataset artifact.

Primary selection question:

> **Does live trajectory improve the anchor in the new 24–72h window?**

Primary selection metrics must therefore include event-balanced 24–72h MAE, with overall 0–72h MAE and tail risk as additional gates/diagnostics.

## Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- v3 research-only;
- long72 research-only;
- no production write;
- `live_adjustment = 0`.
