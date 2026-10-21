# Beyond Ticketing — Model Promotion Governance v1

Last updated: **2026-10-21**

Status: **ACTIVE / NO AUTOMATIC PRODUCTION IMPACT**

## Purpose

Promotion Governance separates:

1. research signal;
2. evidence gate;
3. frozen candidate package;
4. human review;
5. explicit production activation.

Crossing an evidence gate never changes production P50 automatically.

## Primary promotion metric

Primary point-forecast criterion:

- challenger prospective MAE must be lower than incumbent prospective MAE on the declared evaluation population.

Required guardrails:

- signed bias;
- median AE;
- P90 AE;
- worst-event degradation;
- event-improvement rate;
- club/horizon stability;
- reproducible PIT-safe lineage.

Guardrails may block promotion. They do not silently replace MAE as the primary optimization objective.

## Evidence classes

Promotion logic must distinguish:

- `historical_exposed_research`;
- `historical_forward_fold`;
- `delayed_label_precommitted`;
- `true_post_freeze_prospective`.

Historical uplift alone is not production promotion evidence.

Previously inspected historical holdouts must never be reclassified as unseen.

## Package creation rule

A production-review candidate may be frozen only when all conditions are true:

- a challenger/package was frozen before the decisive future labels were used;
- forecast states were materialized before label exposure where the data flow allows it;
- `decision_status = promotable`;
- `evidence_signal = positive`;
- the declared prospective evidence gate is met;
- challenger MAE is lower than incumbent MAE;
- uplift versus incumbent is positive;
- if a bias-control MAE exists, challenger also beats the bias control;
- PIT/lineage/reproducibility checks pass;
- tail/bias guardrails are acceptable;
- no automatic activation path exists.

The package starts as `ready_for_review`.

## Frozen evidence

Each package freezes:

- category and challenger/package ID;
- primary validation protocol;
- evidence class;
- evaluation population and dates;
- event and club counts;
- incumbent/challenger MAE;
- absolute and relative `ΔMAE`;
- uncertainty interval for `ΔMAE` when available;
- median AE and P90 AE;
- bias;
- event-improvement rate;
- worst-event degradation;
- per-club/per-horizon diagnostics;
- code/data/package hashes;
- full scorecard row;
- decision reason and next action.

Frozen evidence is immutable. Later refreshes cannot rewrite already-reviewed evidence.

## Uncertainty rule

For serious promotion decisions, a point estimate of `ΔMAE` is not enough by itself.

Where sample size permits, report uncertainty using the event/fixture as the independent resampling unit.

Do not bootstrap trajectory rows as if they were independent matches.

## Manual review

Review remains explicit and auditable.

Allowed decisions:

- `approved_for_promotion`;
- `rejected`.

Approval still does not activate production automatically.

## No automatic activation

`auto_activation_allowed` remains false.

A separate explicit production-activation step is required after review.

## Current frozen evidence lanes

### Final24

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Status: prospective evidence accumulation.

### Long72

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical development uplift:

`3707.14 -> 3012.63`, `+18.73%`.

Status: historical-exposed research package; genuine prospective evidence still required.

### Historical/global model

Global Model v2.1 has strong historical later-season evidence but does not become production merely from those historical results.

Future challengers must increasingly use rolling/forward historical evaluation and genuine future 2026/27 evidence.

## R&D separation

Promotion gates must never become a reason to stop model development.

Frozen packages collect evidence in the background while new challenger versions are developed under `ml/MAE_RESEARCH_ROADMAP_V3.md`.

A new challenger must not overwrite or retune the frozen candidate it is trying to beat.

## Production boundary

Production remains unchanged until explicit reviewed activation:

`live_adjustment = 0`
