# Beyond Ticketing — d2 Prospective Score v1 — Initial Run

Date: **2026-10-19**

Status: **GREEN / NO NEW ELIGIBLE EVENTS / SCHEDULED PROSPECTIVE SCORING ACTIVE**

## Purpose

Validate the frozen prospective scoring pipeline end-to-end after the first chronological holdout was persisted.

This run is infrastructure/evidence validation only. It does not create a new model result because there is no new unseen completed event beyond registered event 5.

## Canonical run

Workflow:

`d2 Prospective Score v1`

Run ID:

`39312944826`

Main SHA:

`5ce2e8e7bfd5b197510108f441c11a75257fd0c8`

Artifact:

`d2-prospective-score-v1-39312944826`

Artifact ID:

`12215847975`

Artifact ZIP SHA256:

`ca470b8f18eddabb8c9f4664baff75a776bb6e64d3e50379f6836c22f3b795cc`

Evidence hashes:

- split manifest: `5591880cff101ed316c4acae87fb0cb549ef9d5a987126b63245e154adb5a822`;
- development Stage-0 JSON: `bb8a7c8ef3c719bca0c54da8961aea92d8484168b6493c768fe88c53f316985a`;
- development Stage-0 CSV: `ec7aef2f458ae1db2fdaced7e0a051fe8b9035eccdb3764b0f640c6078aa6954`;
- prospective score JSON: `9450086fb7f97d33e421cccfe07e8f5b6398721cd3358c090cb92326d2111d00`;
- prospective rows CSV: `8274ae67ebd1430a45031abcdbd771a748e56a7d15fabf1abd9e8191ba85a983`;
- prospective registry: `0d9901c749bf4e7ee18262a5f204efd69f909907a9aeac47e939547e8852827a`;
- frozen Stage-2 manifest: `8d04defd1400ca9aadd19abba8b4ba8a0f3ed8c2bad56d8c0b88c5aa79cf7083`.

## Current exporter state

Exporter metadata at run time:

- completed/tracked events: `10`;
- live rows: `34`.

Frozen Ridge training lineage remained exactly:

- event IDs `[1, 3, 4, 8, 9, 12, 13, 14, 17]`;
- 9 events;
- 30 rows.

The only exporter event outside frozen development remained:

`event 5`

Event 5 is already registered as a completed/exposed prospective event and therefore was correctly excluded from new-unseen scoring.

## Prospective result

Status:

`NO_NEW_ELIGIBLE_EVENTS`

New candidate event IDs:

`[]`

Scored events:

`[]`

Blocked events:

`[]`

This is the expected result.

The pipeline did not re-score event 5 as unseen and did not add any prospective outcome to Ridge training.

## Frozen lineage assertions

The hard evidence gate confirmed:

- `production_change = false`;
- `promotion_allowed = false`;
- `model_training_on_prospective_outcomes = false`;
- `policy_retuning_performed = false`;
- Stage-1 expert remains `ridge-a10`;
- Stage-2 package remains `d2-stage2-p2-observation-maturity-2026-10-19-v1`;
- Stage-2 policy remains `P2-observation-maturity`;
- development IDs remain exactly the frozen nine;
- registry contains event `5` as already exposed;
- no development or registered event may appear in a new scored set.

## Operational state

The workflow is now active on:

- `workflow_dispatch`;
- relevant `main` pushes;
- daily schedule at `05:23 UTC`.

A future run with no new completed event remains green with `NO_NEW_ELIGIBLE_EVENTS`.

When a new eligible completed event appears, the scorer will:

1. keep Ridge training fixed to the original 9/30 development set;
2. reconstruct Structural T-1 and Frozen-v2/b2 PIT-safely;
3. score raw frozen Ridge;
4. apply frozen P2 without retuning;
5. upload event/row evidence;
6. leave C1 as a separate pre-outcome persisted-evidence join;
7. never commit/retrain automatically.

A separate reviewed evidence cycle must persist a newly scored event and add it to the registry.

## Production boundary

No production change.

`live_adjustment = 0`

## Decision

`PROSPECTIVE_SCORER_ACTIVE_WAIT_FOR_NEXT_INDEPENDENT_COMPLETED_EVENT`
