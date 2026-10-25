# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-25**

Status: **CURRENT EXECUTION ORDER**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

## Priority 0 — protect data and evidence integrity

- RoboTicket ingestion safety net is live; preserve it as operational infrastructure.
- Original P7 tournament is exposed; never retune/rerun it.
- P7 prospective model fingerprint is pinned; any drift must fail closed.
- P9a target-free freeze remains closed to learner selection.
- Preserve frozen Long72 and P4a contracts.
- Never backfill closing odds or booking curves and call them prospective.
- Do not promote parking/VIP/reserve/non-football ticket products.
- Do not infer promotions from price movement.
- Do not enable production.

## Priority 1 — P7 prospective validation is now active

Historical P7 evidence:

- anchor MAE: 7409.79;
- challenger MAE: 6339.99;
- point improvement: 1069.80 / 14.44%;
- 95% event-block interval: `[-2566.13, +174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`.

Prospective lane:

- precommitted before prospective outcomes;
- selected mechanism fixed: `gbr-l1-depth2-n50-lr003`;
- exact training set fixed: events `[1,3,4,5,10,11,15,16,18,19]` / 139 rows;
- training manifest fixed: `185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`;
- deterministic model fingerprint fixed: `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- no bootstrap backfill;
- prediction persistence must occur while the event is genuinely 72–168h from kickoff.

First prospective run `40216860928` succeeded:

- immutable prediction rows: 3;
- independent events: 3;
- scored events: 0;
- evidence: `PROSPECTIVE_PREDICTIONS_ONLY`;
- production activation: false.

Schedule:

`37 */6 * * *`

Next P7 action is **collection only**. Do not tune from incoming outcomes. When a genuine outcome becomes available after `predicted_at`, the existing scorer may attach it without recomputing the prediction.

## Priority 2 — preserve ingestion coverage for future rounds

Canonical safety document:

`ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`

Operational rules:

1. hourly RoboTicket discovery;
2. candidate raw buffering every 10 minutes;
3. same-element event identity;
4. football-universe gate;
5. fail-closed non-match/non-football exclusions;
6. verified schedule promotion;
7. original PIT timestamps preserved on backfill;
8. dashboard must expose TRACKED / BUFFERING / READY / GAP states.

Fresh state:

- 11 future matches TRACKED;
- one `TRACKED_NO_SNAPSHOT`: Wisła Kraków vs Cracovia; source currently returns zero sectors;
- no genuine match is silently unbuffered.

This operational lane may expand the future research base but must not fabricate historical evidence.

## Priority 3 — preserve P11a scheduled PIT odds accumulation

Fresh readiness:

- genuine PIT events: 2;
- events with >=3 bookmakers: 2;
- current horizon coverage 24h / 72h / 168h: 1 / 1 / 0;
- model precommitted: false.

Scheduled capture:

`17 */6 * * *`

Do not fit a P11a attendance model yet.

## Priority 4 — preserve P11b/P11d context collection

### P11b price

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)` remains live and target-free.

No explicit promotion source exists; promotion stays null.

### P11c absences

Still data-bound. Continue verified collection only.

### P11d weather

Existing mechanism remains `research_only_no_uplift`; closed unless a materially new mechanism is proposed.

### P11d attention

Continue prospective-only collection. Do not force an evaluation before useful variance/coverage exists.

## Priority 5 — continue Long72 frozen prospective scoring

Current:

- scored genuine events: 2;
- anchor event-balanced MAE: 9069.52;
- package event-balanced MAE: 7641.71;
- point improvement: 1427.80 / 15.74%;
- latest score refresh inserted 0 new scores.

No retuning from n=2.

## Priority 6 — accumulate P9 full-168h coverage

Fresh readiness:

- 168h: 5/9 events / 5 clubs;
- 72h: 9 / 7;
- 48h: 12 / 7;
- 24h: 15 / 9.

Full learner remains blocked until 9/9 plus a separate learner precommit.

The ingestion safety net should improve future coverage, but the gate must not be lowered.

## Priority 7 — accumulate P4a labels

Fresh readiness:

- READY events: 5;
- labeled READY events: 2;
- distinct labeled previous-home-spacing values: 2;
- required: >=9 labeled AND >=3 distinct labeled values;
- trigger: false.

## Priority 8 — business minimum meaningful ΔMAE

Framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

Derive the threshold from real forecast-driven operational decisions, independently of challenger results.

## Priority 9 — P12 later

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

Do not start a regime-aware challenger while higher-priority prospective/data-coverage lanes remain immature.

## Completed in this execution cycle

- P7 frozen tournament executed;
- P7 prospective precommit created;
- deterministic P7 model fingerprint frozen;
- P7 service-role summary plumbing fixed without scientific changes;
- first true P7 prospective predict/persist run succeeded;
- RoboTicket discovery hardened;
- private pre-mapping raw buffer deployed;
- verified promotion/backfill deployed;
- discovery cadence tightened to hourly and buffer cadence to 10m;
- dashboard ingestion coverage added to Overview and Data Quality;
- panel CI succeeded;
- P11a first genuine capture/schedule and P11b contract remain live.

## Next meaningful milestones

1. first genuine P7 prospective scored event;
2. additional Long72 genuine outcomes;
3. P9 reaches 9/9 at 168h;
4. P4a reaches 9 labeled / 3 distinct labeled values;
5. P11a gains broader multi-event/multi-horizon coverage;
6. media attention becomes evaluation-ready;
7. business minimum meaningful ΔMAE is approved.
