# Beyond Ticketing — d2 Prospective Readiness v1 — Canonical Evidence

Date: **2026-10-19**

Status: **COMPLETED / READINESS OBSERVABILITY ACTIVE / NO MODEL CHANGE / NO PRODUCTION CHANGE**

## Purpose

Persist the first canonical readiness snapshot after introducing a dedicated tracked-event feed for d2 prospective evidence.

The readiness layer is intentionally separate from the frozen `v7-*` model-scoring exports.

It exists so completed tracked events waiting only for trusted attendance truth do not disappear silently from the prospective evidence pipeline.

## Canonical run

Workflow:

`d2 Prospective Score v1`

Run:

`39322049864`

Main SHA:

`1c56d81f12da2a67981fe8063461df6b5612f96c`

Artifact:

`d2-prospective-score-v1-39322049864`

Artifact ID:

`12219724931`

Artifact ZIP SHA256:

`3a5978c1c76d5012e7e8a4d124730c4aae452e9968c0fe2d2463cc48a207f964`

## Evidence hashes

- raw readiness feed: `fae7d13f00760c728c9bc49441868665f019f5ede743607faec7396e1df7327c`;
- readiness report: `5ccdb968dd455aa04cf7579a391bada4e32aa63ad18c7284b915592c0543fc74`;
- frozen split manifest: `5591880cff101ed316c4acae87fb0cb549ef9d5a987126b63245e154adb5a822`;
- development Stage-0 JSON: `bb8a7c8ef3c719bca0c54da8961aea92d8484168b6493c768fe88c53f316985a`;
- development Stage-0 CSV: `ec7aef2f458ae1db2fdaced7e0a051fe8b9035eccdb3764b0f640c6078aa6954`;
- frozen prospective scoring JSON: `9450086fb7f97d33e421cccfe07e8f5b6398721cd3358c090cb92326d2111d00`;
- prospective rows CSV: `8274ae67ebd1430a45031abcdbd771a748e56a7d15fabf1abd9e8191ba85a983`;
- prospective registry: `0d9901c749bf4e7ee18262a5f204efd69f909907a9aeac47e939547e8852827a`;
- Stage-2 package manifest: `8d04defd1400ca9aadd19abba8b4ba8a0f3ed8c2bad56d8c0b88c5aa79cf7083`.

## Export contracts

Frozen model-scoring export remains unchanged:

- `v7-events`: outcome-eligible events only;
- `v7-final24`: frozen scoring/live evidence rows;
- canonical state at this run: `10 events / 34 live rows`.

New additive readiness feed:

`d2-readiness -> public.export_d2_prospective_readiness_v1()`

Canonical state:

- feed version: `d2-prospective-readiness-v1`;
- tracked Ekstraklasa event count: **21**;
- attendance is never inferred from inventory;
- verified outcome is `LEFT JOIN`ed when available;
- audited capacity and raw final-24h snapshot count are exposed independently.

## Frozen evidence-class boundary

Canonical Stage-2 freeze cutoff:

`2026-10-19T19:11:01Z`

Every unregistered tracked event is classified before interpretation as:

### `DELAYED_LABEL_HOLDOUT`

`kickoff_at <= Stage-2 freeze cutoff`

These events were not used for Stage-1/Stage-2 selection but had already kicked off before the frozen package was canonically established.

They may be scored later for diagnostic evidence when trusted outcomes arrive, but **must not count as genuinely post-freeze prospective promotion evidence**.

### `TRUE_POST_FREEZE_PROSPECTIVE`

`kickoff_at > Stage-2 freeze cutoff`

Only this class may count toward the genuine forward sample used for eventual production-promotion decisions.

## Canonical readiness snapshot

As-of:

`2026-10-19T20:47:01.162979Z`

Status counts:

- `BLOCKED_MISSING_OUTCOME`: **5**;
- `FUTURE_NOT_DUE`: **6**;
- ready for scoring: **0**.

Evidence-class counts among surfaced unregistered events:

- `DELAYED_LABEL_HOLDOUT`: **5**;
- `TRUE_POST_FREEZE_PROSPECTIVE`: **6**.

## Completed events blocked only on trusted outcome

| Event | Match | Kickoff UTC | Final-24h snapshots | Capacity state | Evidence class | Readiness |
|---|---|---|---:|---|---|---|
| 15 | GKS Katowice vs Pogoń Szczecin | 2026-10-17 15:30 | 96 | verified | delayed-label | missing outcome |
| 18 | Cracovia vs Legia Warszawa | 2026-10-17 18:15 | 51 | verified | delayed-label | missing outcome |
| 11 | Górnik Zabrze vs Piast Gliwice | 2026-10-18 10:15 | 96 | verified | delayed-label | missing outcome |
| 19 | KGHM Zagłębie Lubin vs Jagiellonia Białystok | 2026-10-18 12:45 | 96 | verified | delayed-label | missing outcome |
| 20 | Wisła Płock vs Radomiak Radom | 2026-10-19 17:00 | 96 | verified, `15,004` | delayed-label | missing outcome |

Important:

> Do not estimate these attendance outcomes from ticket inventory to accelerate scoring.

They become eligible only after a trusted verified outcome enters the outcome pipeline.

## Future true post-freeze prospective candidates

The readiness feed currently tracks these future events as `TRUE_POST_FREEZE_PROSPECTIVE`:

- event 10 — Pogoń Szczecin vs Radomiak Radom — `2026-10-24T15:30Z`;
- event 16 — Wisła Kraków vs Raków Częstochowa — `2026-10-24T18:15Z`;
- event 23 — Śląsk Wrocław vs Wieczysta Kraków — `2026-10-25T11:15Z`;
- event 21 — Jagiellonia Białystok vs Wisła Płock — `2026-10-25T13:45Z`;
- event 22 — Legia Warszawa vs Lech Poznań — `2026-10-25T16:30Z`;
- event 6 — Lech Poznań vs Wisła Kraków — `2026-10-31T16:30Z`.

At the canonical snapshot they are correctly `FUTURE_NOT_DUE` and have no final-24h rows yet.

## Trusted outcome pipeline

Existing sync:

`supabase/sql/ticket_event_outcome_history_sync_v1.sql`

Contract:

- source: `ml_home_attendance_history_v2`;
- exact `club_slug + kickoff_at` match;
- Ekstraklasa only;
- only after kickoff + 3 hours;
- never overwrite an existing outcome;
- hourly cron at minute `17`.

At the time of this canonical run, the five blocked events do not yet have verified outcomes in the trusted source path.

## Frozen model-scoring result in the same run

Frozen scorer status:

`NO_NEW_ELIGIBLE_EVENTS`

This is correct and does not conflict with the readiness blockers.

Reason:

- the frozen `v7-*` scorer intentionally sees only outcome-eligible events;
- the additive readiness feed independently surfaces tracked events waiting for truth labels.

No new model score was produced in this run.

## Safety / governance assertions

The run verifies:

- Frozen Ridge remains `ridge-a10`;
- Stage-2 package remains `d2-stage2-p2-observation-maturity-2026-10-19-v1`;
- frozen 9-event / 30-row development lineage remains exact;
- event 5 remains registered as exposed;
- no prospective outcome enters training;
- no P2 retuning occurs;
- no attendance estimation occurs;
- no production change occurs;
- `live_adjustment = 0` remains unchanged.

## Decision

Readiness observability is now sufficient to distinguish:

1. a completed tracked event that is blocked on truth data;
2. a delayed-label holdout;
3. a genuinely post-freeze prospective event;
4. a future event not yet due for scoring.

Current next work is **not model tuning**.

Next operational priorities:

1. maintain freshness/coverage of trusted attendance outcomes;
2. ensure snapshot collection is active for the six post-freeze future events before their final-24h window;
3. score and persist new events under the frozen package when they become eligible;
4. report delayed-label and true-prospective evidence separately;
5. count only `TRUE_POST_FREEZE_PROSPECTIVE` events toward eventual production-promotion evidence.

## Production boundary

No production change.

No retraining.

No Stage-2 policy change.

`live_adjustment = 0`
