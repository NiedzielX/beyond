# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-19**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering it.

## Cold-start rule

Read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
2. `ml/CURRENT_MODEL.md`;
3. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
4. `ml/D2_STAGE2_RELIABILITY_GATING_V1.md`;
5. `ml/D2_STAGE1_MODEL_TOURNAMENT_V1.md`;
6. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
7. `ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md`;
8. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
9. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
10. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
11. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

> **Build d2 Stage 2: freeze the Stage-1 `ridge-a10` research lead and learn/govern reliability so live corrections keep most of their MAE uplift while materially reducing tail risk.**

Do not reopen a2/b2/c2 against the same exposed historical references.

Do not retune Ridge on the new Lech–Korona event.

## Canonical sequence

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> d2 Stage 1 DONE -> d2 Stage 2 ACTIVE`

## Architecture

Frozen historical pre-live layer:

`history + proven current-season regime -> Pre-Live v2 historical candidate`

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

Live layer after Stage 1:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

Frozen Stage-1 live expert:

`ridge-a10`

The current problem is reliability/tail-risk governance, not another open-ended model-family search.

## Frozen Pre-Live v2

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Canonical manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

Historical reference mean MAE:

- T-30: `1867.82`;
- T-14: `1809.45`;
- T-7: `1691.40`;
- T-3: `1682.63`;
- T-1: `1661.52`.

Freeze reproduces 20/20 exact horizon-season MAE cells at tolerance `1e-9`.

This remains a historical candidate, not a production promotion.

## a2 / b2 / c2

### a2

`CLOSED FOR CURRENT HISTORICAL DATA`

T-7 historical base:

`hist31-leaf20-l2-1`

T-30/T-14/T-3/T-1 retain their Structural Prior historical bases.

### b2

`CLOSED FOR CURRENT HISTORICAL DATA / FROZEN INTO PRE-LIVE V2`

Frozen non-zero policies:

- T-7: `ewma50-resid-k6-cap05-min3`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`.

All activate only after at least 3 earlier completed same-season home matches.

### c2 historical

`SUFFICIENTLY EVALUATED / NO HISTORICAL CONTEXT EXTENSION`

Historical contract:

`NO_CONTEXT_ALL_HORIZONS`

Forward-only rivalry / verified absences / media-hype remain prospective research.

## d2 Stage 0

Status:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

Frozen development lineage:

- 9 events;
- 30 final-24h rows;
- exact Frozen-v2 anchor.

Diagnostic:

- legacy Structural Prior event MAE: `3968.73`;
- Frozen-v2 event MAE: `4128.01`.

This small live-specific result does not reopen b2.

## d2 Stage 1 — COMPLETE

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Canonical run:

`39256585339`

Artifact ID:

`12187853899`

Artifact ZIP SHA256:

`c494ba609f3c9ee376e8285a9af975cc78d813337bd219fbaf94c7a9a336c6de`

Research lead:

`ridge-a10`

Key development metrics:

- Frozen-v2 latest MAE: `4128.01`;
- Ridge latest MAE: **`3320.39`**;
- latest improvement: **`+807.62 seats / 19.56%`**;
- Frozen-v2 event-balanced window MAE: `4128.01`;
- Ridge window MAE: **`3619.19`**;
- window improvement: **`+508.83 seats / 12.33%`**;
- latest event improvement rate: **`6/9 = 66.7%`**;
- worst latest-event degradation: **`+4326.90 seats`**.

Interpretation:

> Live evidence is useful, but raw Ridge is not safe enough because tail risk remains large.

## Chronos / TSFM decision

Stage 1 tested zero-shot:

- `amazon/chronos-2`;
- `amazon/chronos-bolt-small`.

Results:

- Ridge: `3320.39` latest MAE;
- Ridge + Chronos-2: `3428.25`;
- Ridge + Bolt-small: `3428.08`.

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same development set.

## d2 Stage 2 — ACTIVE NOW

Canonical contract:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

Freeze Stage-1 Ridge exactly:

- `alpha=10`;
- existing Stage-1 feature contract;
- median imputation within training fold;
- missing indicators;
- standardization;
- event-balanced weights;
- +/-10pp occupancy correction cap.

Do not retune the model itself in Stage 2.

Stage 2 selects a compact reliability/shrinkage policy using only the original 9-event/30-row development lineage.

Primary form:

`final = frozen_v2 + reliability * ridge_delta`

Reliability candidates may use only PIT-safe signals such as:

- observation count / span;
- time to kickoff;
- velocity / acceleration;
- trajectory stability;
- Ridge/Frozen-v2 disagreement;
- proposed correction magnitude;
- release / coverage-change flags;
- data gaps / feature quality.

Primary objective:

> retain meaningful Ridge MAE uplift while materially reducing the +4.3k-seat worst-event degradation.

## Reserved chronological holdout — DO NOT TUNE ON IT

Event ID:

`5`

Match:

`Lech Poznań vs Korona Kielce`

Kickoff:

`2026-10-18T15:30:00Z`

Actual attendance:

`37,407`

Capacity:

`43,269`

Final-24h live rows:

`4`

This event was deliberately excluded from Stage-1 model selection.

Mandatory rule:

> **Do not use event 5 in Stage-2 threshold/policy selection. Freeze Stage 2 on the original 9 events first. Then open event 5 once and score Frozen v2, raw Ridge, governed Ridge and frozen C1 v8 where compatible. No retuning afterward.**

## After event 5

- persist the result regardless of outcome;
- continue append-only prospective scoring on new completed events;
- do not silently retrain with new outcomes;
- create a new explicit retraining/version cycle if/when enough independent events exist;
- require materially more prospective evidence before production promotion.

## Frozen C1 v8

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Keep it unchanged as a prospective comparator.

## Production boundary

Production remains:

`live_adjustment = 0`

No Stage-1 or Stage-2 result automatically changes production.

## Non-negotiable CI/CD

Every material experiment:

`code -> tests/checks -> CI -> artifact -> metrics -> result doc -> decision -> canonical docs update`

Persist exact model/policy IDs, inputs, PIT semantics, event split, preprocessing, thresholds, hashes, run IDs and limitations.

## One-line instruction

> **Pre-Live v2 and Stage-1 `ridge-a10` are frozen research components. Build only d2 Stage-2 reliability/tail-risk governance on the original 9-event/30-row development set; do not inspect Lech–Korona event 5 for tuning. Freeze Stage 2 first, then score event 5 once as the first chronological holdout. Keep production and C1 v8 unchanged.**
