# P9a Booking Curve — Main Target-Free Freeze Audit

Date: **2026-10-25**

Status: **COMPLETE / TARGET-FREE / MODEL STILL BLOCKED**

Production: **UNCHANGED**

Workflow run: `40197782502`

Artifact: `p9a-target-free-freeze-v1-40197782502`

Artifact ID: `12600099880`

Artifact ZIP SHA256: `33a1aa5c4604600a922a89d24a8ad03b0e636aaef8f7d913c8755e8779de5c54`

## Audit guarantees

Both T-24 and T-48 passed the hard target-free gates:

- `target_values_opened=false`;
- `model_training_performed=false`;
- `production_change=false`;
- no target-event future trajectory point used;
- target snapshot max age remains 6h;
- reference/snapshot/incumbent identities are frozen deterministically;
- learner remains blocked pending a separate precommit and valid comparator sample.

No labels were opened by this audit.

## T-24

Manifest SHA256:

`738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`

- input targets: **19**;
- reference catalog events: **20**;
- representation ready: **16**;
- freeze ready: **12**;
- comparator ready: **9**.

Freeze-ready event IDs:

`[9, 14, 7, 15, 18, 11, 19, 5, 20, 10, 16, 23]`

Comparator-ready event IDs:

`[15, 18, 11, 19, 5, 20, 10, 16, 23]`

## T-48

Manifest SHA256:

`ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`

- input targets: **16**;
- reference catalog events: **20**;
- representation ready: **13**;
- freeze ready: **10**;
- comparator ready: **7**.

Freeze-ready event IDs:

`[7, 15, 18, 11, 19, 5, 20, 10, 16, 23]`

Comparator-ready event IDs:

`[11, 19, 5, 20, 10, 16, 23]`

## Decision

P9a has completed its current purpose: the main target-free T-24/T-48 representation and identity audit is reproducible and frozen.

Do **not** interpret this as permission to fit/open a P9 learner. The full-window P9 program remains data-bound at **5/9 complete 168h reference events**, and any first learnable candidate requires a separate precommit before labels/results are opened.
