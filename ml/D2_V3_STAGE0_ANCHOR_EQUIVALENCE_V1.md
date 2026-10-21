# d2-v3 Stage 0 — Final-24h Anchor Equivalence v1

Last updated: **2026-10-21**

Status: **COMPLETED — V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2**

Canonical result:

`ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`

Workflow run:

`39636749440`

Artifact ID:

`12361203868`

Artifact ZIP SHA256:

`3835820769970ed4f931bdeee1c4da60415430d9c8099b34aebef83348bd49af`

## Decision

The existing d2 final-24h problem does **not** change when moving from the sealed v2 Pre-Live anchor to sealed v3.

Reason:

- current d2 Stage 0 anchors final-24h rows on T-1 only;
- sealed v3 intentionally retains the exact v2 T-1 package;
- v2/v3 T-1 contracts and historical input lineage are identical;
- exact frozen 9-event / 30-row Stage-0 replay was reproduced;
- maximum v3-v2 anchor-seat delta is exactly `0.0` on all rows.

Derived target values after CSV round-trip differ only by floating-point serialization noise:

- max target-attendance delta: `3.637978807091713e-12` seats;
- max target-occupancy delta: `1.734723475976807e-16`;
- max anchor-occupancy delta: `1.1102230246251565e-16`.

## Consequence

Do **not** create a cosmetic new Stage-1 model version solely because Pre-Live v3 has a new freeze ID.

The final-24h residual target is numerically unchanged, so the current Ridge/P2 mathematics remain valid for this exact problem definition.

This does not promote or mutate the Track-A v2/Ridge/P2 package.

## Next R&D

Move to a materially different live hypothesis.

Preferred direction:

> **extend live forecasting earlier than 24h, toward the T-7 window, so the changed v3 T-7 anchor can actually matter.**

Data-readiness audit on 2026-10-21 confirmed that PIT-safe snapshot history already exists beyond final-24h; the next workstream should create an additive long-horizon export/data contract without changing `v7-final24` lineage.

## Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- v3 research-only;
- no model training occurred in this Stage-0 audit;
- no production write;
- `live_adjustment = 0`.
