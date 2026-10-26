# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-26**

Status: **CURRENT SOURCE OF TRUTH**

Canonical research strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`.

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons, with PIT-safe, reproducible evidence.**

Primary decision metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction: `ΔMAE < 0`.

Readiness counters, snapshot counts, label counts, support counts, odds rows and prediction rows are evidence-enablers only. They are not model success.

Production remains unchanged:

`live_adjustment = 0`

No research lane may activate production automatically.

## Research decision rules

1. Prefer prospective evidence over historical reconstruction whenever historical PIT cannot be proven.
2. Never relax a gate merely to obtain a model result.
3. Never tune a challenger after opening the target outcomes used to judge it.
4. `NOT_EVALUABLE` is a valid research outcome; it is neither a win nor a loss.
5. Before starting a new hypothesis, compare its expected MAE value against active frozen prospective lanes and the cost of delaying them.
6. Promotion requires a meaningful prospective MAE gain plus acceptable event-level downside; point gain alone is insufficient.
7. Preserve `live_adjustment=0` until a separate production decision is explicitly approved.

## Priority 0 — protect data and evidence integrity

- Keep multi-source ticketing acquisition, fixture watchdog, raw buffering and promotion healthy.
- Preserve original `captured_at`; never manufacture booking-curve history during promotion/backfill.
- Never backfill odds, booking curves, outcomes or forecasts and call them prospective.
- Hidden/unknown ticket availability must never become zero.
- Preserve frozen P7, P9, Long72, P4a and P11 contracts.
- Production remains disabled for every research lane.

## Priority 1 — P9 prospective v1: first real MAE lane

Historical P9 v1 is closed:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Historical frozen state:

- T-168: **9/9 events / 9 clubs**;
- learner precommitted before evaluation;
- T-24: **0/11 support-ready**;
- T-48: **0/9 support-ready**;
- attendance labels were not opened by the learner;
- no valid historical challenger-vs-incumbent MAE result exists.

Do not repair the historical cohort retrospectively.

Read:

- `ml/P9_BOOKING_CURVE_HISTORICAL_COHORT_RESULT_2026-10-25.md`
- `ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`

### Prospective contract

Canonical precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen mechanism:

- T-48 and T-24 only;
- fixed `k=5` booking-curve neighbors;
- same incumbent source family for target/reference residuals;
- minimum 3 residual-bearing references;
- correction = median residual;
- no fit/search/tuning;
- no target attendance in the prediction builder;
- no late bootstrap;
- immutable persistence window = exact cutoff through cutoff + 90 minutes;
- primary metric = prospective event-balanced MAE vs incumbent.

Current live evidence:

- prediction events: **0**;
- prediction rows: **0**;
- scored events: **0**;
- evidence: `PROSPECTIVE_PREDICTIONS_ONLY`;
- production activation false;
- `live_adjustment=0`.

Zero predictions before the first frozen window is expected.

### P9 scheduler — DEPLOYED / E2E GREEN

Workflow:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Schedule:

`7,37 * * * *`

End-to-end path has been verified on `main`:

1. main-only GitHub OIDC;
2. target-free reference-outcome export;
3. target-free T-48/T-24 inputs;
4. P9a representation/reference freeze;
5. PIT incumbent catalog;
6. frozen prospective builder;
7. immutable prediction persistence only if support is valid;
8. genuine-outcome scoring;
9. production-safety assertions.

The previously missing `p9_booking_curve_prospective_v1` Edge Function is deployed and active.

### First-window readiness — PROTECTED

First frozen windows:

- Cracovia–Motor T-48: **2026-10-28 17:00 UTC**;
- Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**.

Pre-window audit found one critical issue: Cracovia–Motor had booking snapshots but no persisted target incumbent because `sporting_league_matches_shadow.event_date` held a round-date placeholder (`2026-10-31`) while the verified ticketing kickoff is `2026-10-30 17:00 UTC`.

The resolver has been hardened:

`supabase/sql/structural_prior_fixture_date_tolerance_2026_10_26.sql`

Rule:

1. exact Warsaw date first;
2. if absent, exact aliased home/away identity may fall back only when there is exactly one matching fixture within ±3 calendar days;
3. zero or multiple nearby matches fail closed.

No ticket-event kickoff is changed and no fuzzy club matching is introduced.

The Structural Prior Materializer workflow was rerun successfully. It persisted for event 443:

- Structural Prior ID: **40**;
- horizon: **T-7**;
- P50: **10632.32**;
- verified stadium capacity: **15016**;
- `point_in_time_validated=true`;
- generated: **2026-10-26 16:25 UTC**;
- persisted before P9 T-48 cutoff: **true**.

Although the Structural Prior row is marked `backfilled_pit_forecast=true` relative to its own T-7 materialization time, the frozen feature builder reconstructs attendance/sporting features strictly at the T-7 `target_as_of_at=2026-10-23 17:00 UTC`. For P9 T-48, the forecast itself genuinely exists before the P9 decision cutoff on 2026-10-28. The P9 incumbent catalog additionally enforces `created_at <= analogous_cutoff_at`.

The live orchestrator immediately processed event 443 after persistence.

Other first-window P9 targets already have PIT-validated target incumbents:

- Wisła Płock–Piast;
- Lech–Wisła Kraków;
- GKS Katowice–Widzew.

### P9 v2 decision rule

Do **not** create P9 v2 merely to force a prediction.

Only consider a new target-free P9 design if prospective v1 repeatedly enters genuine T-48/T-24 windows but remains structurally unable to emit predictions after genuine PIT incumbent history has had a fair opportunity to accumulate.

Any P9 v2 must be precommitted before evaluation labels are opened.

## Priority 2 — maintain the P9 pre-window evidence chain

Before each near-term P9 window, audit only evidence-enabling conditions that can make an immutable window unrecoverable:

- target booking snapshots exist before cutoff;
- target incumbent exists and is PIT-valid before cutoff;
- fixture mapping is unambiguous;
- verified capacity exists where required by the incumbent;
- scheduler/gateway are green;
- no outcome is present for the future target.

Never generate a missing target incumbent after the P9 cutoff and treat it as if it existed at the cutoff.

Current known future Structural Prior gaps after protecting the first P9 window:

- event 447 Raków–Pogoń: `missing_capacity`;
- event 603 Korona–Radomiak: `missing_capacity`;
- event 452 Pogoń–Śląsk: `missing_fixture_round` because the later round is not yet present in the sporting shadow.

These are next acquisition/metadata reliability tasks, not reasons to change the P9 learner.

## Priority 3 — panel reports MAE lifecycle, not readiness as performance

Completed on 2026-10-26.

P9 browser-facing data now uses an RLS-protected safe cache and `security_invoker` views:

- `public.dashboard_p9_mae_lifecycle_cache_v1`;
- `public.dashboard_p9_mae_lifecycle_v1`;
- `public.dashboard_p9_mae_status_v1`.

The panel distinguishes:

- historical readiness;
- historical `NOT_EVALUABLE` status;
- prospective prediction coverage;
- scored events;
- incumbent MAE;
- challenger MAE;
- ΔMAE;
- event-level downside;
- production guardrails.

`P9MaeStatusPanel` is visible in Forecast Accuracy and Model Lab. Dashboard CI is green.

Reproducible DB contract:

`supabase/sql/dashboard_p9_mae_lifecycle_v1.sql`

## Priority 4 — P7 prospective: collect and score only

Frozen historical evidence:

- anchor MAE: **7409.79**;
- challenger MAE: **6339.99**;
- point improvement: **1069.80 / 14.44%**;
- 95% event-block interval: `[-2566.13,+174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`.

Prospective lane:

- model `gbr-l1-depth2-n50-lr003`;
- fingerprint `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- **16 immutable prediction rows / 3 independent events / 0 scored events**;
- no tuning.

Next action: genuine scoring only.

## Priority 5 — P11 odds: continue genuine PIT accumulation

Current state:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- events / clubs: **4 / 4**;
- events with >=3 bookmakers: **4**;
- T-24 / T-72 / T-168 coverage: **3 / 3 / 0**;
- model precommitted: false;
- production false.

Keep append-only capture. Do not fit an attendance model before genuine horizon coverage audit and precommit.

## Priority 6 — Long72 frozen scoring

Last verified n=4:

- events `[10,16,21,23]`;
- anchor event-balanced MAE: **6942.59**;
- package event-balanced MAE: **6824.16**;
- point improvement: **118.43 / 1.71%**;
- event improvement rate: **75%**;
- worst event degradation: **3633.23**.

Not promotion evidence. Do not retune.

## Priority 7 — P4a genuine label accumulation

Last verified:

- labeled READY: **4/9**;
- distinct previous-home-spacing values: **3**;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move this gate.

## Priority 8 — business minimum meaningful ΔMAE

Canonical framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

Derive the threshold from real forecast-driven operational decisions independently of current challenger results.

## Priority 9 — new feature families / P12 later

Canonical plan:

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

Rank new hypotheses such as demand regimes, opponent attractiveness, form, table position, weather or attention by expected incremental **prospective MAE reduction**, not novelty.

Do not start a broad tuning tournament while P7/P9 prospective evidence is immature.

## Immediate execution order

1. Keep the P9 prospective scheduler/gateway healthy through the first T-48 window on 2026-10-28.
2. Resolve verified-capacity gaps for future Structural Prior targets where authoritative evidence exists; keep unknowns fail-closed.
3. Keep later fixture-round coverage fresh; do not invent a round when the sporting shadow does not yet contain one.
4. Collect immutable P9 T-48/T-24 predictions; if frozen support is insufficient, record the failure rather than relaxing the rule.
5. Score P7 and P9 only after genuine outcomes arrive.
6. Continue Long72/P4a/P11 accumulation without retuning.
7. Set the business minimum meaningful ΔMAE.
8. Only then choose the next new challenger hypothesis using expected prospective MAE impact.

## Next meaningful MAE milestones

1. first valid immutable P9 prospective prediction;
2. first genuine P7 prospective scored event;
3. first genuine P9 prospective scored event;
4. enough independent scored events to report stable event-balanced ΔMAE and event-level downside;
5. business minimum meaningful ΔMAE approved;
6. only then any production promotion decision.
