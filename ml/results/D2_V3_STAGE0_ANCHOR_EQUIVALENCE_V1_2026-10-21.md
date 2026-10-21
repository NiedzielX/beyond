# d2-v3 Stage 0 — Final-24h Anchor Equivalence v1 — Result

Date: **2026-10-21**

Status: **COMPLETED / V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2 / NO RETRAIN REQUIRED FROM ANCHOR CHANGE**

Canonical contract:

`ml/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1.md`

Workflow run:

`39636749440`

Evaluate-main job:

`119349434301`

Artifact:

`d2-v3-stage0-anchor-equivalence-v1-39636749440`

Artifact ID:

`12361203868`

Artifact ZIP SHA256:

`3835820769970ed4f931bdeee1c4da60415430d9c8099b34aebef83348bd49af`

Evidence hashes:

- rebuilt Frozen-v2 Stage0 JSON: `bb8a7c8ef3c719bca0c54da8961aea92d8484168b6493c768fe88c53f316985a`;
- rebuilt Frozen-v2 Stage0 CSV: `ec7aef2f458ae1db2fdaced7e0a051fe8b9035eccdb3764b0f640c6078aa6954`;
- v2-v3 equivalence JSON: `4531ee30846ef5735c611898788e29b43e2f019698cdbb53913380ad59fc57ea`;
- v2-v3 equivalence CSV: `89c0cb6c7a7d73230664a74da67172f7266bb51ac1d4f6db47a0bd13c1971cc0`.

## Decision

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

No new final-24h target is required solely because Pre-Live v3 exists.

No Stage-1 retraining is required solely because the anchor version changed.

No Stage-2 reliability reselection is required solely because the anchor version changed.

## Why

The current d2 development/replay contract is final-24h and uses the event-level **T-1 Pre-Live anchor**.

Sealed Pre-Live v3 changes T-30 and T-7, but retains the exact Frozen-v2 T-1 package:

- historical base: `structural-prior-runtime-v1-t1-hist-full`;
- current-season regime: `ewma50-resid-k6-cap05-min3`;
- historical context: `NO_CONTEXT`.

The v2/v3 T-1 expected rolling MAE vector is also identical.

Both freezes use the same historical runtime SHA and feature contract.

## Frozen development set

Exact frozen Stage-1 identities were reconstructed from the current append-only export:

- 9 events;
- 30 final-24h rows;
- event IDs: `1,3,4,8,9,12,13,14,17`;
- maximum development kickoff: `2026-10-12T18:30:00Z`.

Current append-only export at run time contained:

- 14 events;
- 50 live rows.

Five newer events were correctly kept out of the frozen Stage-1 selection set:

`5,11,15,18,19`

with 4 final-24h rows each.

## Exact Stage-0 reproduction

Frozen-v2 Stage0 replay reproduced the canonical evidence exactly:

- event MAE: `4128.012628960847`;
- legacy Structural Prior event MAE: `3968.726757294377`;
- anchor-change MAE difference: `-159.28587166647003`;
- event count: `9`;
- row count: `30`.

Stage0 JSON/CSV hashes matched the earlier canonical evidence exactly.

## Row-level v2-v3 equivalence

Hard model-level anchor rule:

- maximum absolute v3-v2 anchor-seat delta: **`0.0` seats**.

Therefore the model anchor is exactly identical on all 30 rows.

Derived values after CSV serialization/reload differed only by machine-level floating-point round-trip noise:

- max anchor occupancy delta: `1.1102230246251565e-16`;
- max target-attendance delta: `3.637978807091713e-12` seats;
- max target-occupancy delta: `1.734723475976807e-16`.

Declared serialization tolerances:

- anchor seats: exact `0.0`;
- target attendance: `<= 1e-9` seats;
- occupancy deltas: `<= 1e-12`.

All gates passed.

## Lineage

Frozen-v2 manifest SHA256:

`8f11f201aa6eff39de02c489ceac6d00ca9d3e161f295ea3c41119ce4f5d74f4`

Frozen-v3 manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Shared historical runtime SHA256:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

Shared feature contract:

`structural-prior-pit-v1+verified-capacity-v1`

## Interpretation

A new d2 Stage-1 tournament **solely because the Pre-Live freeze ID changed would be cosmetic** for the existing final-24h problem.

The live residual labels are unchanged. Therefore the existing final-24h Ridge/P2 mathematics remain valid relative to the sealed v3 T-1 anchor as well.

This does **not** promote Ridge/P2 into a new production package and does not relabel exposed events as unseen.

## Next R&D decision

Do not spend another cycle retraining the same final-24h target under a new name.

The preferred next materially different hypothesis is:

> **extend live forecasting earlier than 24 hours, ideally toward the T-7 window, so the changed Pre-Live v3 T-7 anchor can actually matter.**

First audit whether PIT-safe snapshots earlier than 24h are already retained in the source tables/export path.

If sufficient earlier snapshots do not exist, the next final-24h research must use a genuinely different target/reliability/feature hypothesis rather than a cosmetic v3 rerun.

## Production boundary

Always:

- Track-A Frozen Pre-Live v2 / Ridge / P2 unchanged;
- Frozen Pre-Live v3 remains research-only;
- no training occurred in this Stage-0 equivalence experiment;
- production unchanged;
- `live_adjustment = 0`.
