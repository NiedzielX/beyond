# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Read `ml/NEXT_SESSION_HANDOFF.md`.
3. Read `ml/EXECUTION_PLAN_CURRENT.md`.
4. Read `ml/PROGRESS_TRACKING.md` for the latest canonical state.
5. Read `ml/MAE_RESEARCH_ROADMAP_V4.md` for strategy.
6. Query `public.ml_research_readiness_v1()` fresh before acting on any data gate.
7. Never rebuild frozen history merely to recover context.
8. Never store secrets/tokens/service-role keys in repo files.

## Core principle

> **The objective is lower true out-of-sample MAE, not model complexity.**

Current phase: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Repository / live-state

Canonical repository branch is `main`.

The former active branch `ml/p9-p11-execution-2026-10-24` has already been reconciled with `main`; do not repeat branch reconciliation unless a fresh compare shows a new divergence.

Live Supabase project:

`adchzwqboeekhokapxqi`

P9a and P11a v2 source are present on canonical `main` and live Supabase.

Do not redeploy from memory or create parallel implementations.

## Ticketing ingestion safety net — live 2026-10-25

A permanent pre-mapping protection layer is now active to prevent losing booking-curve history when a new RoboTicket match appears before exact kickoff mapping is ready.

Live controls:

- RoboTicket discovery hardened to same-element/direct-event identity instead of nearby-text heuristics;
- explicit parking / VIP / Premium / reserve / non-match exclusion;
- football eligibility fail-closed before raw buffering;
- discovery cadence tightened from 6h to hourly;
- candidate raw inventory buffer runs every 10 minutes;
- raw candidate observations are isolated in `private.roboticket_candidate_snapshots_v1` and are not model-facing;
- exact original `captured_at` is preserved;
- verified schedule mapping promotes the event and safely backfills eligible raw observations into normal `snapshots`;
- normal RoboTicket collector remains active every 15 minutes;
- dashboard ingestion cache refreshes every 10 minutes;
- Beyond Ticketing Panel Data Quality page exposes tracking / buffer / gap state.

Important safety rule:

> A candidate raw buffer is evidence preservation only. It must not become model-facing until a verified event identity and kickoff exist.

Known non-football / ambiguous products remain fail-closed even if they share the same RoboTicket storefront.

## Validation / evidence

Historical/global:

- strict expanding temporal folds;
- complete `match_key` blocking across all horizons;
- no future-season leakage;
- persist exact identities/manifest SHA.

Live/context:

- `ticket_event` is the independent unit;
- strict forward-event validation by kickoff;
- tied kickoffs cannot train one another;
- no random snapshot split as headline evidence;
- freeze target-free identities/features before labels/model-result selection whenever prospective evidence is possible.

## Governance v2

Use `ml/research_advance_governance_v2.py`.

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

A positive point estimate alone is not a robust advance. Robust advancement requires a predeclared business-derived minimum meaningful MAE improvement plus precision, stability and evidence-integrity gates.

Do not infer the meaningful threshold from the experiment being judged.

## Fresh readiness checkpoint recorded 2026-10-25 16:58 UTC

Always query fresh before acting, but current recorded state is:

- Long72: `90` reproducible rows / `2` genuine scored events; first-score trigger open;
- P7 Long168: **10/9** independent events / `139` rows >72h — gate OPEN;
- P4a: `5` READY / `2` labeled / `2` distinct labeled spacing values — gate CLOSED (`>=9` labeled and `>=3` distinct required);
- P9 full 168h: **5** ready events / 5 clubs — still `DATA_BOUND`;
- P9 T-72: `9` ready events / 7 clubs;
- P9 T-48: `12` ready events / 7 clubs;
- P9 T-24: `15` ready events / 9 clubs;
- production change remains `false`.

### P7 Long168 — execute now

P7 research-start gate is open.

Required action:

1. freeze exact event/as-of identities before any Long168 model selection;
2. replay the frozen T-7 structural anchors;
3. run only the precommitted fixed P7 tournament;
4. evaluate with existing governance;
5. keep `production_change=false`, `production_activation_allowed=false`, `live_adjustment=0`.

Do not redesign candidates after seeing the result.

## P10 / P10b — frozen closeout

P10 v1:

- local HGB `2120.93`;
- pooled HGB `2057.46`;
- `ΔMAE=-63.47`;
- status `POINT_GAIN_UNCERTAINTY_LIMITED`.

P10b against actual frozen Pre-Live v3:

- incumbent `1919.92`;
- pooled `2067.43`;
- challenger-incumbent `ΔMAE=+147.51`;
- 95% CI `[+82.97,+210.67]`;
- 0/4 folds and 0/5 horizons improved;
- status `NO_RESEARCH_GAIN`.

Do **not** retune P10/P10b after these results. A future pooling experiment requires a materially new mechanism and a new precommit.

## P9 full-window booking curves

Use existing trajectory infrastructure; do not duplicate it.

Hard rules:

- no target snapshot after `as_of_at`;
- no future target canonical point;
- no self-event historical reference;
- reference event completed before target cutoff;
- public inventory is a demand proxy, not confirmed sales.

Current full-168h coverage: **5** genuine completed reference events.

Do not fit the first full-window P9 residual challenger before the 9-event gate. At 9/9, freeze the learner contract before opening model-result comparisons.

## P9a T-24/T-48 target-free freeze

P9a is **freeze/audit infrastructure**, not a trained model.

The harness freezes exact target/reference/snapshot/incumbent identities and a deterministic SHA. It rejects attendance target fields, post-cutoff target snapshots and self references.

Run/verify the main P9a freeze audit after P7. Require:

- `target_values_opened=false`;
- `model_training_performed=false`;
- future target snapshots not used;
- labels remain separate.

Do **not** call `export_p9a_booking_curve_labels_v1` merely because it exists. Label opening/model fitting requires a separate explicit learner/comparator precommit.

## P11a market odds v2

Provider target:

`the-odds-api-v4` / `soccer_poland_ekstraklasa` / pre-match `h2h`.

Architecture:

- append-only raw bookmaker-level 1X2 quotes;
- provider event + capture batch lineage;
- verified alias mapping;
- kickoff tolerance 5,400 seconds;
- ambiguous mappings fail closed;
- actual capture timestamp is authoritative;
- source payload SHA-256;
- de-vig each bookmaker first;
- median bookmaker consensus, then renormalize;
- as-known lookup uses only batches captured by requested cutoff and pre-kickoff.

Semantic guard:

`outcome_uncertainty != expected_match_quality`

Current architecture is live, but genuine odds capture must still be verified before enabling any schedule.

Required secret:

`THE_ODDS_API_KEY`

Configure/verify it in Supabase Edge Function secrets; never commit it.

First genuine capture must be manual and audited before any schedule is enabled.

Never backfill closing odds into earlier PIT cutoffs.

## P4a / Long72

P4a remains frozen/data-bound:

- 5 READY events;
- 2 labeled events;
- 2 distinct labeled previous-home-spacing values;
- gate `>=9` labeled + `>=3` distinct labeled spacing values;
- fixed previous-home-spacing challenger.

Long72 remains immutable forecast-before-label evidence. Two genuine events are now scored; inspect as prospective evidence only and do not retune the frozen package from them.

## Closed loops

Do not reopen without materially new evidence/mechanism:

- estimator-only tuning;
- estimator uncertainty re-analysis on same sample;
- simple structural/live shrinkage;
- historical Long72 incremental-value loop;
- simple club/opponent post-hoc calibration;
- fixed P10/P10b pooled-HGB direct replacement;
- blind model or weight sweeps.

## Immediate development order

1. **execute frozen P7 Long168 now**;
2. run/verify P9a target-free T-24/T-48 main freeze audit; do not open labels/train;
3. configure/verify `THE_ODDS_API_KEY` if not already set;
4. run one manual P11a v2 genuine capture and audit it; keep schedule off until audited;
5. keep full-168h P9 genuine curve capture running toward 9 events;
6. derive the business minimum meaningful MAE threshold;
7. keep P4a/Long72 evidence collection unchanged;
8. keep ingestion safety-net monitoring active and fail closed on ambiguous/non-football candidates.

The old ChatGPT Beyond readiness automations are intentionally disabled. Do not enable them implicitly.

No research result activates production automatically.
