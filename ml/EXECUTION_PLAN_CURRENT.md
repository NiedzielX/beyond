# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-25**

Status: **CURRENT EXECUTION ORDER**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

## Priority 0 — protect evidence integrity

- Branch reconciliation is complete; do not repeat it.
- P7 frozen tournament is complete; do not retune/rerun its inspected candidate set.
- P9a target-free freeze audit is complete; do not open a learner from it.
- Preserve frozen Long72 and P4a contracts.
- P11a genuine capture is active; never backfill closing odds.
- Do not infer promotion from price movement.
- Do not treat missing absence rows as confirmed availability.
- Do not reopen the existing weather mechanism.
- Do not reopen P10/P10b.
- Do not enable production.

## Priority 1 — precommit P7 prospective follow-up

P7 produced a meaningful point gain but uncertainty remains wide:

- anchor MAE: 7409.79;
- challenger MAE: 6339.99;
- point improvement: 1069.80 / 14.44%;
- event/fold improvement rate: 80% / 80%;
- 95% event-block interval: `[-2566.13, +174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`.

The old tournament is now exposed evidence.

Next allowed P7 work is therefore **not** another candidate sweep. Build a separate prospective validation contract for the already-selected mechanism `gbr-l1-depth2-n50-lr003` before any new qualifying Long168 outcomes are opened.

The prospective lane must predeclare:

1. frozen mechanism and hyperparameters;
2. eligible future event/as-of rule;
3. prediction persistence before attendance is available;
4. frozen Structural Prior comparator;
5. event as independent unit;
6. MAE, bias, event-improvement, P90/worst degradation and event-block uncertainty reporting;
7. no model retuning from incoming outcomes;
8. `production_activation_allowed=false`;
9. `live_adjustment=0`.

## Priority 2 — preserve P11a scheduled PIT accumulation

First genuine capture is complete and audited.

Current readiness:

- raw rows: 34;
- genuine events: 2;
- events with >=3 bookmakers: 2;
- 24h / 72h / 168h coverage: 2 / 1 / 0;
- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- model precommitted: false.

Scheduled capture is enabled:

`17 */6 * * *`

Do not change cadence based on attendance results. Audit coverage/lineage as the sample grows.

Canonical evidence: `ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`.

## Priority 3 — preserve P11b/P11d context collection

### P11b price

Live function:

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)`

It is PIT-safe and target-free.

Current status:

- event 6: `PRICE_CONTEXT_READY`;
- event 22: `PRICE_AREA_ONLY`;
- no explicit promotion source;
- promotion remains null;
- no attendance model opened.

Continue collecting real price context. Do not create synthetic promotion labels.

### P11c absences

Only one active verified row / one team exists. Continue collection only.

### P11d weather

Existing mechanism is `research_only_no_uplift`. Do not repeat it.

### P11d media attention

Prospective-only collection continues. Current feature variance is insufficient for evaluation. Do not force an ablation.

Canonical audit: `ml/P11_CONTEXT_AUDIT_2026-10-25.md`.

## Priority 4 — continue Long72 prospective evidence

Current genuine state:

- scored events: 2;
- anchor MAE: 9069.52;
- frozen package MAE: 7641.71;
- point improvement: 1427.80 / 15.74%;
- n=2 only.

Continue frozen scoring as new genuine outcomes arrive. No retuning or post-hoc calibration.

## Priority 5 — accumulate P9 full-168h coverage

Current coverage:

- 168h: 5/9 events / 5 clubs;
- 72h: 9 / 7;
- 48h: 12 / 7;
- 24h: 15 / 9.

Full P9 remains `DATA_BOUND`.

Blocked until 9/9 + separate learner precommit:

- learner selection;
- hyperparameter selection;
- fitting;
- opening learner result comparisons.

P9a T-24/T-48 freeze audit is already complete.

## Priority 6 — accumulate P4a labels

Current:

- READY events: 5;
- genuine labels: 2;
- distinct labeled previous-home-spacing values: 2;
- required: >=9 labeled AND >=3 distinct labeled values.

Gate remains closed.

## Priority 7 — business minimum meaningful ΔMAE

Framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

Derive the threshold from actual forecast-driven decisions, not from the challenger results it will judge.

Until approved and precision is sufficient, `ROBUST_RESEARCH_ADVANCE` remains unavailable.

## Priority 8 — P12 only after higher-value lanes

P12 pre-plan exists:

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

Do not start a regime-aware challenger until the target-free audit establishes a stable mechanism and higher-priority P9/P11 work is sufficiently mature.

## Completed in this execution cycle

- P7 frozen tournament executed and recorded.
- P9a T-24/T-48 target-free freeze completed.
- P11 runtime synchronized and first genuine capture completed.
- P11 schedule enabled after successful audit.
- P11 readiness messaging corrected.
- P11b price context `as-known` function deployed and verified against current and historical cutoffs.
- P11c/P11d target-free source audit completed.
- existing weather loop correctly classified as no-uplift rather than restarted.

## Closed loops

Do not reopen without a materially new mechanism:

- P10/P10b fixed pooled-HGB tuning;
- old estimator-only sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple calibration;
- existing weather mechanism;
- blind post-hoc calibration.

## Next meaningful milestones

1. P7 prospective follow-up contract frozen before new labels;
2. P11a gains genuine multi-horizon / multi-event coverage;
3. additional Long72 prospective outcomes are scored;
4. P9 reaches full 9/9 168h coverage;
5. P4a reaches 9 labeled / 3 distinct values;
6. media attention gains sufficient prospective variance/eligible events;
7. business minimum meaningful ΔMAE is approved.
