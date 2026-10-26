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

### P9 scheduler/gateway — DEPLOYED

Workflow:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

Schedule:

`7,37 * * * *`

Gateway:

`supabase/functions/p9_booking_curve_prospective_v1`

The workflow is responsible for:

1. main-only GitHub OIDC;
2. target-free P9 preflight;
3. target-free reference-outcome export;
4. target-free T-48/T-24 inputs;
5. P9a representation/reference freeze;
6. PIT incumbent catalog;
7. frozen prospective builder;
8. immutable prediction persistence only if support is valid;
9. genuine-outcome scoring;
10. production-safety assertions.

### First-window readiness — PROTECTED

First frozen windows:

- Cracovia–Motor T-48: **2026-10-28 17:00 UTC**;
- Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**.

A pre-window audit found Cracovia–Motor had booking snapshots but no target incumbent because `sporting_league_matches_shadow.event_date` used a round-date placeholder (`2026-10-31`) while the verified ticketing kickoff is `2026-10-30 17:00 UTC`.

The resolver was hardened in:

`supabase/sql/structural_prior_fixture_date_tolerance_2026_10_26.sql`

Rule:

1. exact Warsaw date first;
2. if absent, exact aliased home/away identity may fall back only when there is exactly one matching fixture within ±3 calendar days;
3. zero or multiple nearby matches fail closed.

No ticket-event kickoff is changed and no fuzzy club matching is introduced.

The Structural Prior Materializer persisted event 443:

- Structural Prior ID: **40**;
- horizon: **T-7**;
- P50: **10632.32**;
- verified capacity: **15016**;
- `point_in_time_validated=true`;
- persisted **2026-10-26 16:25 UTC**;
- persisted before P9 T-48 cutoff: **true**.

The P9 incumbent catalog additionally enforces `as_of_at <= analogous_cutoff_at` and `created_at <= analogous_cutoff_at`.

### P9 v2 decision rule

Do **not** create P9 v2 merely to force a prediction.

Only consider a new target-free P9 design if prospective v1 repeatedly enters genuine T-48/T-24 windows but remains structurally unable to emit predictions after genuine PIT incumbent history has had a fair opportunity to accumulate.

Any P9 v2 must be precommitted before evaluation labels are opened.

## Priority 2 — automated P9 preflight protects immutable windows

Canonical function:

`public.p9_prospective_preflight_v1(10)`

Repo source:

`supabase/sql/p9_prospective_preflight_v1.sql`

The function is service-role-only, target-free and production-safe. It audits future targets before immutable T-48/T-24 windows and classifies each cutoff as:

- `READY`;
- `WATCH_NO_SNAPSHOT` / `WATCH_NO_INCUMBENT`;
- `CRITICAL_NO_SNAPSHOT` / `CRITICAL_NO_INCUMBENT` within 48h of cutoff;
- `WINDOW_OPEN`;
- `CAPTURED`;
- `MISSED_WINDOW`.

The P9 workflow calls the preflight on every run. WATCH/CRITICAL conditions create visible warnings but do not abort the whole job, so one future target cannot block an already-open valid target.

Fresh 10-day audit on 2026-10-26:

- critical: **0**;
- watch: **0**;
- all six near-term P9 targets are `READY` at T-48 and T-24;
- Cracovia–Motor, Wisła Płock–Piast, Lech–Wisła Kraków, GKS–Widzew, Zagłębie–Korona and Raków–Pogoń all have cutoff-eligible snapshots and incumbents.

### Capacity gaps resolved

Officially verified capacities were added for current Structural Prior inference:

- Raków Częstochowa: **5500**;
- Korona Kielce: **15550**.

Repo source:

`supabase/sql/structural_prior_current_capacities_2026_v1.sql`

Materializer/orchestrator then produced and processed:

- event 447 Raków–Pogoń — Structural Prior ID **45**, P50 **5049.53**, capacity **5500**;
- event 603 Korona–Radomiak — Structural Prior ID **46**, P50 **12016.93**, capacity **15550**.

Both are PIT-validated. The previous `missing_capacity` state for 447/603 is closed.

### Remaining evidence watches

- event 452 Pogoń–Śląsk remains `missing_fixture_round`; sporting shadow is current but upstream currently exposes only rounds 13–14. Do not invent the later round.
- event 448 Wisła Kraków–Cracovia is `TRACKED_NO_SNAPSHOT`; the event exists but no inventory snapshot has been observed yet. Do not convert absence of visible inventory to zero.

These are data-acquisition/metadata watches, not learner-design failures.

## Priority 3 — panel reports MAE lifecycle, not readiness as performance

Completed on 2026-10-26.

P9 browser-facing data uses an RLS-protected safe cache and `security_invoker` views:

- `public.dashboard_p9_mae_lifecycle_cache_v1`;
- `public.dashboard_p9_mae_lifecycle_v1`;
- `public.dashboard_p9_mae_status_v1`.

The panel distinguishes historical readiness/NOT_EVALUABLE status, prospective prediction coverage, scored events, incumbent MAE, challenger MAE, ΔMAE, event-level downside and production guardrails.

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

1. Keep automated P9 preflight + scheduler/gateway healthy through the first T-48 window on **2026-10-28 17:00 UTC**.
2. Watch event 448 for first genuine ticketing snapshot and event 452 for upstream round coverage; do not fabricate either.
3. Collect immutable P9 T-48/T-24 predictions; if frozen support is insufficient, record the failure rather than relaxing the rule.
4. Score P7 and P9 only after genuine outcomes arrive.
5. Continue Long72/P4a/P11 accumulation without retuning.
6. Set the business minimum meaningful ΔMAE.
7. Only then choose the next new challenger hypothesis using expected prospective MAE impact.

## Next meaningful MAE milestones

1. first valid immutable P9 prospective prediction;
2. first genuine P7 prospective scored event;
3. first genuine P9 prospective scored event;
4. enough independent scored events to report stable event-balanced ΔMAE and event-level downside;
5. business minimum meaningful ΔMAE approved;
6. only then any production promotion decision.
