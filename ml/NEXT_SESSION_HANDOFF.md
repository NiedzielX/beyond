# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-25 11:55 Europe/Warsaw**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Current phase: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

No research result activates production automatically.

---

## 2. Immediate execution order

Current order is:

`P11 first genuine manual capture -> P11 audit -> P7 frozen execute -> P9a main freeze audit -> continue prospective evidence`

Why P11 is first: pre-match market odds are perishable PIT evidence. P7 is now unlocked but its frozen execution is not time-critical within minutes; today’s P11 quotes are.

---

## 3. Repository reconciliation — COMPLETE

Canonical repo: `NiedzielX/beyond`.

Previous active branch: `ml/p9-p11-execution-2026-10-24`.

Completed reconciliation:

- PR #171 merged current `main` into the active branch after deliberate conflict resolution;
- P11 contract CI passed;
- P9a freeze CI passed;
- key P9a/P11a source/workflow blob SHAs were verified identical on `main` and active;
- active branch reached `behind_by=0` and zero file-content diff vs `main`;
- PR #172 merged the reconciled history back to `main` with zero changed files;
- final reconciliation merge on `main`: `c48b0045f371f0b52b98f61d24f39f3be99ec7bb`.

Therefore P9a/P11a source **already exists on main**. Do not rebuild or copy it again.

---

## 4. Genuine outcomes added on 2026-10-25

The first post-freeze completed Long72 events were event 10 and event 16.

Upstream `ticket_event_outcomes` initially had no attendance for them, although the hourly sync cron itself was healthy. `ml_home_attendance_history_v2` also had no rows for those fixtures.

Verified public post-match attendance from the same source family already used by canonical outcomes (`frekwencyjny.pl`):

- event 10 — Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 — Wisła Kraków vs Raków Częstochowa: **33,000**.

These were inserted into `public.ticket_event_outcomes` at `2026-10-25 10:54 UTC` with:

- `attendance_definition='reported_match_attendance'`;
- `source_name='frekwencyjny.pl'`;
- canonical public source URL;
- genuine post-match confirmation timestamp.

No synthetic target or estimated attendance was used.

---

## 5. First genuine Long72 prospective scores — COMPLETE

After outcomes were available, the existing frozen scorer was executed:

`public.score_d2_long72_forward_completed_events_v1(now())`

Result:

- inserted score count: **2**;
- genuine prospective scored events: **2**;
- anchor event-balanced MAE: **9069.52**;
- frozen package event-balanced MAE: **7641.71**;
- point MAE improvement: **1427.80** seats;
- relative point improvement: **15.74%**;
- event improvement rate: **1.0** on the two events;
- `production_change=false`.

Interpretation rule: **n=2 is first prospective evidence only**. Do not retune, promote, calibrate, or claim robust advance from this sample.

The hourly `d2 Long72 Forward Prospective v1` GitHub workflow already contains the score step. The zero-score state was caused by missing upstream outcomes, not a broken scorer.

---

## 6. Fresh canonical readiness — 2026-10-25 10:54 UTC

Canonical source:

`public.ml_research_readiness_v1()`

### Long72

- reproducible rows: **90**;
- genuine scored events: **2**;
- first genuine score trigger: **true**.

### P7 Long168 — NOW OPEN

- rows >72h: **139**;
- independent eligible events: **10**;
- threshold: **9**;
- `research_start_trigger=true`.

Important correction to the earlier handoff:

The frozen contract diagnosis remains correct: a Long168 event must be completed and have genuine attendance; a T-168 snapshot alone is insufficient. However, event 6 is **no longer required** to unlock P7. Genuine outcomes for events 10 and 16 raised readiness from 8/9 to 10/9.

Next P7 action is to run the existing frozen executor exactly as precommitted:

`.github/workflows/p7-long168-executor-v1.yml`

Manual dispatch:

- branch: `main`;
- input: `mode=execute`.

That workflow must:

1. verify frozen artifact hashes;
2. fetch the live Long168/support exports;
3. replay frozen T-7 anchors;
4. freeze exact event/as-of identities;
5. run the fixed candidate tournament;
6. require `independent_frozen_event_count >= 9`;
7. keep `production_change=false`;
8. keep `production_activation_allowed=false`;
9. keep `live_adjustment=0`.

Do not redesign P7 before execution.

### P9 full-window booking curve

Fresh completed reference coverage:

- 168h: **5/9 events / 5 clubs**;
- 72h: **9 events / 7 clubs**;
- 48h: **12 events / 7 clubs**;
- 24h: **15 events / 9 clubs**;
- learner precommitted: false;
- full 168h status remains `DATA_BOUND`.

Do not fit the first full-168h learner yet.

### P4a

- READY events: **5**;
- genuine labeled READY events: **2**;
- labeled non-null previous-home-spacing events: **2**;
- distinct labeled spacing values: **2**;
- gate requires `>=9 labeled + >=3 distinct labeled values`;
- research trigger: **false**.

P4a remains frozen.

---

## 7. P11a v2 — immediate time-sensitive blocker

Live Supabase already has:

- P11 v2 DB capture/consensus/readiness contract;
- Edge Function `p11_odds_capture_v2` ACTIVE v2;
- GitHub workflow `.github/workflows/p11-odds-capture-v2.yml` on `main`;
- no automatic schedule.

Current genuine evidence remains:

- raw P11 v2 rows: **0**;
- genuine PIT events: **0**;
- events with >=3 bookmakers: **0**;
- model precommitted: false.

Current capture candidates:

- event 23 — Śląsk Wrocław vs Wieczysta Kraków — `2026-10-25 11:15 UTC`;
- event 21 — Jagiellonia Białystok vs Wisła Płock — `2026-10-25 13:45 UTC`;
- event 22 — Legia Warszawa vs Lech Poznań — `2026-10-25 16:30 UTC`;
- event 6 — Lech Poznań vs Wisła Kraków — `2026-10-31 16:30 UTC`.

Required manual action because capture security intentionally requires a GitHub Actions OIDC token from `refs/heads/main`:

`Actions -> P11 Odds Capture v2 -> Run workflow -> main -> capture=true`

The workflow checks `THE_ODDS_API_KEY` first. If missing, it fails closed before provider capture. Do not work around this with a different authentication path.

After capture, audit:

- local/provider/matched events;
- every mapping status;
- bookmaker count and complete 1X2 quotes;
- kickoff delta;
- provider quota;
- capture batch and payload hash lineage;
- raw rows;
- `p11_market_context_as_known_v2(...)`;
- `p11_market_odds_readiness_v2()`.

Keep schedule off until accepted.

---

## 8. P9a target-free freeze

Live infrastructure remains ready.

Latest recorded exports before the new outcomes:

- T-24: 18 target / 19 reference events;
- T-48: 15 target / 19 reference events;
- `target_values_used=false`;
- `post_cutoff_target_snapshots_exported=false`;
- `production_change=false`.

After P11/P7:

1. run/verify main T-24/T-48 freeze audit;
2. persist/check manifest SHA values;
3. verify frozen identities;
4. confirm `target_values_opened=false`;
5. confirm `model_training_performed=false`.

Do not open labels/fit a learner merely because the freeze contract exists.

---

## 9. Governance / closed loops

Do not reopen P10/P10b, old estimator-only sweeps, P5a shrinkage, P6 historical signal, P8 simple club calibration, or post-hoc tuning on inspected evidence.

Minimum practically meaningful `ΔMAE` remains intentionally undefined and must be business-derived.

Until then, `ROBUST_RESEARCH_ADVANCE` is not available as a conclusion.

---

## 10. Cold-start command

> Read `AI_BOOTSTRAP.md`, `ml/NEXT_SESSION_HANDOFF.md`, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md` and Roadmap v4. Query readiness fresh. Branch reconciliation is complete. Long72 has 2 genuine prospective scores. P7 is now genuinely unlocked at 10/9 and must be executed only through the frozen precommitted executor. Full P9 is 5/9 and remains learner-blocked. P4a has 2/9 labels and remains blocked. Immediate time-sensitive priority is the first genuine P11 manual capture from main; keep schedule off until audited and keep production unchanged.
