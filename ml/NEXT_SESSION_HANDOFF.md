# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-25**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Current phase: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

## 2. Immediate execution order

`preserve P7 prospective schedule -> preserve RoboTicket ingestion safety net -> preserve P11 collection -> score only genuine completed prospective events -> accumulate P9 to 9/9 -> accumulate P4a labels -> define business ΔMAE threshold -> P12 later`

Do not restart the P7 tournament, P9a freeze, P10 or weather loops.

## 3. RoboTicket ingestion safety net — LIVE

Canonical document:

`ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`

The 2026-10-25 incident did **not** mean the whole previous round was lost. Genuine booking curves were preserved for 5/9 round-12 fixtures; the remaining four were hosted by non-onboarded clubs while our onboarded clubs were away teams.

Root cause fixed:

`discovered RoboTicket product -> verified football match -> ticket_event -> collector`

Live controls:

- discovery `roboticket-discovery-v7`;
- same-element eventId/label parsing;
- fail-closed parking/VIP/premium/reserve/non-football exclusions;
- private raw candidate buffer before exact kickoff mapping;
- football-universe gate;
- verified promotion + PIT-preserving backfill;
- discovery hourly;
- candidate buffer every 10 minutes;
- dashboard coverage table refreshed operationally.

Fresh state:

- 11 future matches `TRACKED`;
- one `TRACKED_NO_SNAPSHOT`: Wisła Kraków vs Cracovia, event 448 / external 11718; correctly mapped but RoboTicket currently returns zero sectors;
- no genuine football match silently hangs as an unbuffered candidate;
- early false-positive raw buffer observations stayed private and never entered model-facing snapshots.

Panel repo: `NiedzielX/BeyondTicketingPanel`.

Latest panel main SHA:

`5ea5a5673317ca34cd06519add668db96e7d369b`

Dashboard CI run `40216448478`: **SUCCESS**.

Coverage is visible on Overview and Data Quality. Completed tracked matches remain visible historically.

GitHub's Deployments API did not expose a deployment record for that SHA, so do not claim Vercel production deployment from GitHub evidence alone.

## 4. P7 Long168 — historical tournament is exposed

Run `40197742930`:

- frozen events / rows: 10 / 139;
- strict forward held-out events/folds: 5 / 5;
- anchor MAE: 7409.79;
- selected candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: 6339.99;
- point improvement: 1069.80 / 14.44%;
- event/fold improvement: 80% / 80%;
- 95% event-block CI: `[-2566.13,+174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision: `ADVANCE_RESEARCH`.

Never retune/rerun this tournament.

## 5. P7 prospective validation — ACTIVE

Precommit:

`ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`

No-backfill addendum:

`ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1_ADDENDUM.md`

Pinned fingerprint evidence:

`ml/P7_LONG168_PROSPECTIVE_FINGERPRINT_V1.md`

Frozen training set:

`[1,3,4,5,10,11,15,16,18,19]`, 139 rows.

Training manifest:

`185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`

Pinned deterministic model fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Fingerprint run `40201818862`: **SUCCESS**.

First true prospective predict/persist run `40216860928`: **SUCCESS**.

Current immutable ledger:

- prediction rows: 3;
- independent events: 3;
- scored events: 0;
- evidence status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- fingerprint count: 1;
- target values used in prediction: false;
- production activation allowed: false;
- `live_adjustment=0`.

Persisted events:

- 6 Lech Poznań vs Wisła Kraków;
- 444 GKS Katowice vs Widzew Łódź;
- 446 Wisła Płock vs Piast Gliwice.

Scheduled prospective prediction cadence:

`37 */6 * * *`

Do not tune from these predictions. The scorer may only attach a genuine outcome confirmed after `predicted_at` and never recomputes the forecast.

## 6. Long72

Genuine scored events remain 2:

- event 10 Pogoń–Radomiak: 19,050;
- event 16 Wisła Kraków–Raków: 33,000.

Fresh score state:

- anchor event-balanced MAE: 9069.52;
- package event-balanced MAE: 7641.71;
- improvement: 1427.80 / 15.74%;
- new scores in latest refresh: 0.

Do not retune from n=2.

## 7. P9 / P9a — fresh state

P9a target-free freeze remains complete.

Full P9 readiness:

- 168h: 5/9 events / 5 clubs;
- 72h: 9 / 7;
- 48h: 12 / 7;
- 24h: 15 / 9;
- full 168h status: `DATA_BOUND`;
- learner precommitted: false.

The new ingestion safety net should improve future coverage but does not lower the 9/9 gate.

## 8. P4a — fresh state

- READY events: 5;
- labeled READY events: 2;
- primary previous-home-spacing distinct READY values: 4;
- distinct labeled values: 2;
- required: >=9 labeled AND >=3 distinct labeled values;
- research trigger: false.

## 9. P11 — fresh state

P11a:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- genuine PIT events: 2;
- clubs: 2;
- events with >=3 bookmakers: 2;
- latest time-relative horizon coverage 24h / 72h / 168h: 1 / 1 / 0;
- model precommitted: false;
- target values used: false.

Capture schedule remains `17 */6 * * *`.

P11b:

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)` remains live; never infer promotion from price changes.

P11c remains data-bound.

P11d weather remains closed/no-uplift; attention remains prospective collecting.

## 10. Governance / P12

Business minimum meaningful ΔMAE remains intentionally unset until independently derived from operational decisions.

P12 remains lower priority than active prospective/data-coverage lanes.

## 11. Closed loops

Do not reopen without a materially new mechanism:

- original P7 tournament;
- P10/P10b;
- P5a;
- P6 historical Long72 incremental signal;
- P8 calibration;
- existing weather mechanism;
- old estimator sweeps;
- post-hoc tuning on inspected evidence.

## 12. Cold-start command

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md`, Roadmap v4, the P7 result/precommit/fingerprint files, the RoboTicket ingestion safety-net document, P9a audit and P11 audit. Query readiness fresh. P7 prospective is live with 3 immutable predictions and 0 scored outcomes. RoboTicket discovery/buffer safety net is live and future coverage is visible in the panel. P9 remains 5/9, P4a 2/9, P11 has 2 genuine odds events, Long72 has 2 genuine scores. Keep production unchanged and never retune exposed evidence.
