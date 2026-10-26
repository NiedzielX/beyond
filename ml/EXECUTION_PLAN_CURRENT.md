# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-26**

Status: **CURRENT SOURCE OF TRUTH**

Canonical research strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`.

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons, with PIT-safe, reproducible evidence.**

Primary decision metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

The desired direction is `ΔMAE < 0`.

Readiness counters such as T-168 coverage, number of labels, support-ready targets, clubs, snapshot counts, odds rows and prediction rows are **leading indicators / evidence-enablers only**. They are not the objective.

Production remains unchanged:

`live_adjustment = 0`

No research lane may activate production automatically.

## Research decision rules

1. Prefer prospective evidence over historical reconstruction whenever the historical PIT contract cannot be proven.
2. Never relax a gate merely to obtain a model result.
3. Never tune a challenger after opening the target outcomes used to judge that challenger.
4. A lane that cannot produce a valid MAE comparison is `NOT_EVALUABLE`, not a win and not a loss.
5. Before starting a new hypothesis, compare its expected MAE value against the active frozen prospective lanes and the cost of delaying those lanes.
6. Promotion requires a meaningful prospective MAE gain plus acceptable event-level risk; point gain alone is insufficient.
7. Preserve `live_adjustment=0` until a separate production decision is explicitly approved.

## Priority 0 — protect data and evidence integrity

- Multi-source ticketing ingestion remains a reliability guardrail, not the North Star.
- Current league source coverage remains protected by RoboTicket + Stellis + schedule watchdog/buffer/promotion mechanisms.
- Preserve original `captured_at`; never manufacture PIT history during promotion/backfill.
- Never backfill booking curves, odds, context or forecasts and call them prospective.
- Hidden/unknown ticket availability must never become zero.
- Original P7 tournament remains frozen; do not retune/rerun it.
- Long72, P4a and P11 contracts remain frozen where already precommitted.
- Production remains disabled for every research lane.

## Priority 1 — P9 booking curve: historical cohort closed, prospective lane active

### Historical P9 v1 — CLOSED WITHOUT MAE EVIDENCE

The genuine full-window gate has been reached:

- T-168: **9/9 events**;
- T-168 clubs: **9**;
- `design_precommitted=true`;
- `full_window_gate_open=true`;
- `labels_export_allowed=true`;
- target-free P9a manifests registered: **2**.

Canonical precommit:

`ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`

Precommit ID:

`p9-knn-median-residual-k5-v1`

The frozen historical execution correctly failed closed before attendance labels were opened:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Frozen support diagnostic:

- T-24 comparator targets: **11**;
- T-48 comparator targets: **9**;
- T-24 support-ready targets: **0**;
- T-48 support-ready targets: **0**;
- historical learner result produced: **false**;
- attendance labels opened by learner: **false**;
- production change: **false**.

Root cause is not missing full T-168 curves. The frozen learner requires at least three selected booking-curve neighbors carrying a valid PIT incumbent forecast from the **same source family** at the analogous historical cutoff. The historical live forecast ledger does not contain enough such incumbent rows for the selected neighbors.

This historical cohort must **not** be repaired retrospectively. It provides no valid challenger-vs-incumbent MAE evidence.

Canonical result/post-mortem:

- `ml/P9_BOOKING_CURVE_HISTORICAL_COHORT_RESULT_2026-10-25.md`
- `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`

### P9 prospective v1 — ACTIVE MAE LANE

The correct continuation is prospective validation of the already frozen mechanism, not historical reconstruction and not immediate P9 v2 tuning.

Canonical precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen prospective mechanism:

- cutoffs: T-48 and T-24;
- fixed `k=5` nearest PIT-safe booking-curve neighbors;
- exact target incumbent source family for reference residuals;
- minimum residual-bearing references: 3;
- correction: median residual;
- no fitted coefficient;
- no candidate sweep;
- no target attendance available to the prediction builder;
- no late bootstrap;
- immutable prediction window: cutoff through cutoff + 90 minutes;
- primary metric: prospective event-balanced MAE vs the frozen incumbent.

Current live state at 2026-10-26:

- prediction events: **0**;
- prediction rows: **0**;
- scored events: **0**;
- evidence: `PROSPECTIVE_PREDICTIONS_ONLY`;
- `production_activation_allowed=false`;
- `live_adjustment=0`.

Zero predictions on 2026-10-26 is expected because the first precommitted windows have not opened yet.

First frozen windows include:

- Cracovia — Motor: T-48 opens **2026-10-28 17:00 UTC**, T-24 opens **2026-10-29 17:00 UTC**;
- Wisła Płock — Piast: T-48 opens **2026-10-29 11:15 UTC**;
- Lech — Wisła Kraków: T-48 opens **2026-10-29 16:30 UTC**;
- GKS Katowice — Widzew: T-48 opens **2026-10-29 19:15 UTC**.

Automation:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Schedule:

`7,37 * * * *`

It runs twice per hour so a GitHub scheduler delay is less likely to lose the frozen 90-minute prediction window. The workflow:

1. obtains a main-only OIDC token;
2. captures only already-known reference outcomes;
3. exports target-free T-48/T-24 inputs;
4. freezes P9a representation/reference identities;
5. exports PIT incumbent catalog;
6. runs the frozen prospective builder;
7. persists immutable predictions only if support is valid;
8. scores completed predictions when genuine outcomes arrive;
9. asserts `production_change=false` and `live_adjustment=0`.

### P9 v2 decision rule

Do **not** create P9 v2 merely to force a prediction.

Consider a new target-free P9 design only if prospective v1 repeatedly reaches genuine T-48/T-24 windows but remains unable to emit predictions because the frozen support contract is structurally starved **after new PIT incumbent history has had a fair chance to accumulate**.

Any P9 v2 must be precommitted before its evaluation labels are opened.

### P9 source-of-truth warning

Use:

- `public.p9_learner_gate_status_v1()` for historical learner gate;
- `public.p9_historical_cohort_status_v1()` for frozen historical result;
- `public.p9_booking_curve_prospective_summary_v1()` for prospective evidence.

Do **not** use the legacy `public.p9_booking_curve_readiness_v1()` as the canonical learner/precommit status. It contains stale learner-status semantics and can contradict the registered precommit.

## Priority 2 — make the panel report the real MAE lifecycle

The panel currently exposes generic research readiness but not the canonical P9 lifecycle.

Required P9 panel state:

- historical full-window gate: 9/9;
- historical result: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`;
- historical support: T-24 0 ready / T-48 0 ready;
- prospective prediction events/rows;
- prospective scored events;
- incumbent event-balanced MAE once scoreable;
- challenger event-balanced MAE once scoreable;
- `Δ event-balanced MAE`;
- event improvement rate / worst degradation once scoreable;
- production activation false / live adjustment 0.

The UI must distinguish **readiness**, **prediction coverage**, **scored evidence**, and **MAE result**. A readiness count must never be presented as model improvement.

## Priority 3 — P7 prospective validation: collect and score only

Historical P7 point estimate remains frozen:

- anchor MAE: 7409.79;
- challenger MAE: 6339.99;
- point improvement: 1069.80 / 14.44%;
- 95% event-block interval: `[-2566.13,+174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`.

Prospective mechanism remains frozen:

- `gbr-l1-depth2-n50-lr003`;
- model fingerprint: `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- no bootstrap backfill;
- no tuning.

Fresh live prospective state on 2026-10-26:

- prediction rows: **16**;
- independent prediction events: **3**;
- scored events: **0**;
- model fingerprint count: **1**;
- evidence: `PROSPECTIVE_PREDICTIONS_ONLY`;
- production activation false.

Next action: collection/scoring only.

## Priority 4 — continue P11 genuine PIT market-odds accumulation

Fresh readiness on 2026-10-26:

- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- genuine PIT events / clubs: **4 / 4**;
- events with >=3 bookmakers: **4**;
- T-24 coverage: **3**;
- T-72 coverage: **3**;
- T-168 coverage: **0**;
- model precommitted: false;
- target values used: false;
- production change: false.

Next action: keep append-only scheduled capture. Do not fit an attendance model before the genuine horizon coverage audit and precommit.

## Priority 5 — continue frozen Long72 prospective scoring

Last verified frozen evidence:

- genuine scored events: `[10,16,21,23]`;
- n=4 anchor event-balanced MAE: **6942.59**;
- n=4 package event-balanced MAE: **6824.16**;
- point improvement: **118.43 / 1.71%**;
- event improvement rate: **75%**;
- worst event degradation: **3633.23**.

This is not promotion evidence. Preserve the freeze and collect genuine outcomes only.

## Priority 6 — P4a accumulation

Last verified readiness:

- labeled READY events: **4/9**;
- distinct labeled previous-home-spacing values: **3**;
- variance gate: PASS;
- event-count gate: FAIL;
- research trigger: false.

Only genuine new labels move this gate.

## Priority 7 — business minimum meaningful ΔMAE

Canonical framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

The technical North Star is lower prospective event-balanced MAE, but promotion also needs a business-significant gain. Derive the minimum meaningful ΔMAE independently from real forecast-driven operational decisions.

## Priority 8 — P12 / new feature families only after active evidence lanes are protected

Canonical plan:

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

New hypotheses such as demand regimes, opponent attractiveness, form, table position, weather or attention should be prioritized by **expected incremental prospective MAE reduction**, not by feature novelty.

Do not start a broad tuning tournament while P7/P9 prospective evidence is immature.

## Immediate execution order

1. Keep P9 prospective scheduler healthy before the first T-48 window on 2026-10-28.
2. Update the panel to show the canonical P9 lifecycle and MAE evidence rather than stale/generic readiness.
3. Collect immutable P9 T-48/T-24 predictions; if frozen support is insufficient, record the failure rather than relaxing the rule.
4. Score P7 and P9 only after genuine outcomes arrive.
5. Continue Long72/P4a/P11 accumulation without retuning.
6. Set the business minimum meaningful ΔMAE.
7. Only then choose the next new challenger hypothesis using expected MAE impact.

## Next meaningful MAE milestones

1. first valid immutable P9 prospective prediction;
2. first genuine P7 prospective scored event;
3. first genuine P9 prospective scored event;
4. enough independent scored events to report stable event-balanced `ΔMAE` and event-level downside;
5. business minimum meaningful ΔMAE approved;
6. only then any production promotion decision.
