# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-25**

Status: **CURRENT EXECUTION ORDER**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

## Priority 0 — protect data and evidence integrity

- Multi-source ticketing ingestion is live: RoboTicket + Stellis.
- Alias-resolved current-league source coverage is **18/18 home clubs / 0 uncovered**.
- Fixture schedule watchdog is live; preserve it so known fixtures cannot silently disappear before a ticketing event opens.
- Original P7 tournament is exposed; never retune/rerun it.
- P7 prospective model fingerprint is pinned; any drift must fail closed.
- P9a target-free freeze remains closed to learner selection.
- Preserve frozen Long72 and P4a contracts.
- P11 odds capture has primary + health-guarded fallback schedules; preserve both.
- Never backfill closing odds or booking curves and call them prospective.
- Do not promote parking/VIP/reserve/non-football/cup ticket products.
- Do not convert hidden/unknown availability into zero.
- Do not infer promotions from price movement.
- Do not enable production.

## Priority 1 — P7 prospective validation is active

Historical P7 evidence:

- anchor MAE: 7409.79;
- challenger MAE: 6339.99;
- point improvement: 1069.80 / 14.44%;
- 95% event-block interval: `[-2566.13,+174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`.

Prospective lane:

- precommitted before outcomes;
- fixed mechanism: `gbr-l1-depth2-n50-lr003`;
- fixed training set: `[1,3,4,5,10,11,15,16,18,19]` / 139 rows;
- training manifest: `185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`;
- model fingerprint: `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- no bootstrap backfill;
- prediction persistence only while genuinely 72–168h before kickoff.

Current prospective ledger:

- prediction rows: **6**;
- independent events: **3**;
- scored events: **0**;
- evidence: `PROSPECTIVE_PREDICTIONS_ONLY`;
- production activation false.

The second three rows are later genuine timepoints for the same three events; independent event N remains 3.

Schedule:

`37 */6 * * *`

End-to-end schedule-path validation run `40223004586` succeeded. Next P7 action is collection/scoring only. Do not tune.

## Priority 2 — preserve full multi-source ticketing coverage

Read:

- `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`
- `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`
- `ml/TICKETING_SCHEDULE_WATCHDOG_2026-10-25.md`

Alias-resolved league coverage:

- current Ekstraklasa home clubs: **18**;
- covered by an active source: **18**;
- uncovered: **0**.

### Layer A — fixture watchdog

Reverse coverage check:

`known upcoming league fixture -> onboarded source -> canonical event or safe candidate`

Live view:

`public.dashboard_ticketing_fixture_coverage_v1`

Dashboard refresh:

`private.refresh_dashboard_ticketing_ingestion_status_v2()`

Cadence:

`9,19,29,39,49,59 * * * *`

Fresh genuine schedule gaps after source rechecks: **5**:

- Górnik Zabrze – Legia Warszawa;
- Jagiellonia Białystok – GKS Katowice;
- Motor Lublin – Wisła Płock;
- Śląsk Wrocław – Piast Gliwice;
- Widzew Łódź – Pogoń Szczecin.

These are operational alerts, not training rows. They remain until the source exposes a safe event/candidate.

### Layer B — RoboTicket

- discovery v8 hourly;
- private candidate buffer every 10m;
- same-element product identity;
- football-universe gate;
- non-match/non-football fail closed;
- verified schedule promotion + original PIT backfill.

Wieczysta–Jagiellonia is already protected and therefore correctly absent from SCHEDULE_GAP.

### Layer C — Stellis

Canonical collector:

`stellis_collect_v3`

Cadence:

`3,13,23,33,43,53 * * * *`

Monitored home sources:

- Widzew;
- Radomiak;
- Piast;
- Motor;
- Korona.

Rules:

- latest raw classification wins;
- explicit cup/non-league/friendly fails closed;
- source kickoff is canonical exact time;
- unique league pair required within +/-4 days;
- hidden inventory remains hidden, never fake zero;
- raw curve may accumulate before promotion.

Fresh canonical future source state:

- RoboTicket: 12 future canonical events / 11 with snapshots;
- Stellis: 1 / 1;
- total: 13 / 12;
- one TRACKED_NO_SNAPSHOT: Wisła Kraków vs Cracovia.

Panel displays TRACKED / BUFFERING / SCHEDULE_GAP and other actionable states. Schedule-gap UI CI run `40222368344` succeeded.

This lane expands future research data only. Never fabricate historical evidence.

## Priority 3 — preserve P11a PIT odds accumulation with resilience

Fresh genuine state after recovery run `40223646599`:

- raw append-only odds rows: **81**;
- genuine PIT events / clubs: **4 / 4**;
- capture batches: **5**;
- events with >=3 bookmakers: **4**;
- current horizon coverage 24h / 72h / 168h: **3 / 3 / 0**;
- latest capture: `2026-10-25T18:56:51.448Z`;
- health after capture: `capture_due=false`;
- model precommitted: false;
- target values used: false;
- production change: false.

Capture schedules:

- primary: `17 */6 * * *`;
- fallback: `47 0,6,12,18 * * *`.

Health contract:

`public.p11_market_odds_capture_health_v2()`

Stale threshold:

`270 minutes`

The fallback calls the provider only when the latest genuine capture is stale. A healthy primary run makes the fallback skip provider work. Recovery artifact digest: `6c326149cea6d1043eaa3c5a200b5430853a3fb46454aad910cbf0faf188beba`.

Do not fit a P11a attendance model yet and never backfill closing odds.

## Priority 4 — preserve P11b/P11d context collection

### P11b price

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)` remains live and target-free.

No explicit promotion source exists; promotion stays null.

### P11c absences

Still data-bound. Continue verified collection only.

### P11d weather

Existing mechanism remains `research_only_no_uplift`; closed unless a materially new mechanism is proposed.

### P11d attention

Continue prospective-only collection. Do not force evaluation before useful variance/coverage exists.

## Priority 5 — continue Long72 frozen prospective scoring

Current:

- genuine scored events: 2;
- anchor event-balanced MAE: 9069.52;
- package event-balanced MAE: 7641.71;
- point improvement: 1427.80 / 15.74%.

No retuning from n=2.

## Priority 6 — accumulate P9 full-168h coverage

Fresh readiness:

- 168h: 5/9 events / 5 clubs;
- 72h: 9 /7;
- 48h: 12 /7;
- 24h: 15 /9.

Full learner remains blocked until 9/9 plus a separate learner precommit.

Multi-source ingestion should improve future coverage, but the gate must not be lowered and current-day inventory must not be backfilled into missing old T-168 windows.

## Priority 7 — accumulate P4a labels

Fresh readiness:

- READY events: 5;
- labeled READY events: 2;
- distinct labeled previous-home-spacing values: 2;
- required: >=9 labeled AND >=3 distinct labeled values;
- trigger false.

## Priority 8 — business minimum meaningful ΔMAE

Framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

Derive the threshold independently from real forecast-driven operational decisions.

## Priority 9 — P12 later

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

Do not start a regime-aware challenger while higher-priority prospective/data-coverage lanes remain immature.

## Completed in this execution cycle

- P7 historical tournament executed and frozen;
- P7 prospective precommit + deterministic fingerprint completed;
- P7 immutable prospective ledger advanced to 6 rows across 3 independent events;
- P7 real six-hour predict/persist/score workflow validated end to end;
- RoboTicket discovery/promotion/buffer safety net deployed;
- source coverage expanded to Stellis family and verified at 18/18 current league home clubs;
- canonical Stellis v3 collector scheduled every 10 minutes;
- Stellis state-transition and cup fail-closed hardening deployed;
- shared multi-source ingestion dashboard deployed;
- reverse future-fixture schedule watchdog deployed;
- five genuine schedule gaps surfaced;
- panel updated to render SCHEDULE_GAP and source family correctly;
- panel CI `40222368344` succeeded;
- P11 stale-health contract deployed;
- P11 primary + fallback schedules implemented;
- P11 recovery run `40223646599` succeeded and expanded genuine odds coverage to 4 events / 81 rows;
- temporary P7/P11 one-shot workflows removed after successful validation;
- README, handoff, progress tracking, bootstrap and execution plan synchronized.

## Next meaningful milestones

1. each current `SCHEDULE_GAP` transitions to a safe candidate/track state before meaningful early-window loss;
2. first genuine P7 prospective scored event;
3. additional Long72 genuine outcomes;
4. P9 reaches 9/9 at 168h;
5. P4a reaches 9 labeled / 3 distinct labeled values;
6. P11a reaches genuine 168h coverage and broader multi-event accumulation;
7. media attention becomes evaluation-ready;
8. business minimum meaningful ΔMAE is approved.
