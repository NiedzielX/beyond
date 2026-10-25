# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)
2. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md)
3. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
4. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)
5. [`ml/MAE_RESEARCH_ROADMAP_V4.md`](ml/MAE_RESEARCH_ROADMAP_V4.md)
6. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md)
7. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md)

Do **not** restart from Roadmap v3. Roadmap v4 is canonical.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

## Current execution priority — 2026-10-25 11:55 Europe/Warsaw

Immediate order:

`first genuine P11 capture -> audit P11 -> execute already-unlocked frozen P7 -> P9a main freeze audit -> continue genuine evidence collection`

### Repository reconciliation — DONE

The previous `main` vs `ml/p9-p11-execution-2026-10-24` divergence has been reconciled.

- PR #171 merged `main` into the active branch after deliberate conflict resolution.
- P11 and P9a contract CI passed.
- Key P11/P9a implementation blobs were verified identical on both branches.
- PR #172 merged the reconciled history back into `main` with zero file-content differences.
- Final `main` reconciliation merge commit: `c48b0045f371f0b52b98f61d24f39f3be99ec7bb`.

Do **not** recreate P9a/P11a from scratch. Their source/workflows are already on `main`.

## Fresh live readiness after genuine 24.10 outcomes

At `2026-10-25 10:54 UTC`, two verified post-match attendance outcomes were added from `frekwencyjny.pl`:

- event 10 — Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 — Wisła Kraków vs Raków Częstochowa: **33,000**.

These are genuine post-match outcomes, not estimates or synthetic labels.

The frozen Long72 scorer was then run without changing model parameters or production.

### Long72

- reproducible rows: **90**;
- genuine scored events: **2**;
- first genuine score gate: **OPEN**;
- frozen package MAE on the first two scored events: **7,641.71**;
- anchor MAE: **9,069.52**;
- point `ΔMAE`: **-1,427.80** (~15.7% improvement);
- evidence is **far too small for promotion or retuning**;
- `production_change=false`.

Treat n=2 as first prospective evidence only.

### P7 Long168 — GATE NOW OPEN

Canonical readiness changed from 8/9 to:

- independent eligible events: **10**;
- threshold: **9**;
- rows >72h: **139**;
- `research_start_trigger=true`.

The earlier event-6 diagnosis was correct about the contract — completed event + genuine attendance is required — but event 6 is no longer needed to unlock P7 because events 10 and 16 now supply valid completed outcomes.

Next P7 step is the **already-frozen executor**, not redesign:

1. freeze exact Long168 event/as-of identities;
2. replay the frozen T-7 anchor;
3. execute the fixed precommitted tournament;
4. keep `production_activation_allowed=false` and `live_adjustment=0`.

The canonical workflow is `.github/workflows/p7-long168-executor-v1.yml` with manual `mode=execute`.

### P9 full-window booking curve

Fresh genuine completed-reference coverage:

- 168h: **5/9** events / 5 clubs;
- 72h: **9** events / 7 clubs;
- 48h: **12** events / 7 clubs;
- 24h: **15** events / 9 clubs.

`P9_BOOKING_CURVE_168_START=false` remains correct. Do not fit the first learnable full-168h P9 model yet.

### P4a fixture context

- READY independent events: **5**;
- genuine labeled READY events: **2**;
- distinct labeled `previous_home_match_days`: **2**;
- research gate: `>=9 labeled + >=3 distinct labeled values` — **still CLOSED**.

Do not retune from the first two labels.

## P11a v2 — immediate time-sensitive priority

P11 v2 is already deployed in live Supabase:

- DB capture/consensus/readiness contract live;
- Edge Function `p11_odds_capture_v2` ACTIVE v2;
- workflow/source already on `main`;
- automatic schedule off;
- genuine raw odds rows remain **0** until first capture.

Current capture candidates include:

- event 23 — Śląsk Wrocław vs Wieczysta Kraków — `2026-10-25 11:15 UTC`;
- event 21 — Jagiellonia Białystok vs Wisła Płock — `2026-10-25 13:45 UTC`;
- event 22 — Legia Warszawa vs Lech Poznań — `2026-10-25 16:30 UTC`;
- event 6 — Lech Poznań vs Wisła Kraków — `2026-10-31 16:30 UTC`.

First capture must be manual through GitHub Actions because the Edge Function validates a `main`-branch GitHub OIDC token.

Run:

`Actions -> P11 Odds Capture v2 -> Run workflow -> main -> capture=true`

The workflow first verifies whether `THE_ODDS_API_KEY` is configured. Keep schedule off until the first capture is audited.

## P9a target-free freeze

P9a remains freeze/audit tooling, not a trained model.

Latest known target-free exports:

- T-24: 18 target / 19 reference events;
- T-48: 15 target / 19 reference events;
- `target_values_used=false`;
- `post_cutoff_target_snapshots_exported=false`;
- `production_change=false`.

After the P11/P7 time-sensitive steps, run/verify the main freeze audit and keep:

- `target_values_opened=false`;
- `model_training_performed=false`.

## Closed loops / governance

Do not reopen P10/P10b, old estimator-only sweeps, P5a shrinkage, P6 historical Long72 signal, P8 simple calibration, or post-hoc tuning on inspected evidence.

`ROBUST_RESEARCH_ADVANCE` still requires a predeclared business-derived minimum meaningful MAE improvement. Do not invent the threshold from observed model results.

## Never do these

- do not backfill closing odds as historical PIT observations;
- do not insert synthetic odds;
- do not fuzzy-match ambiguous provider fixtures;
- do not enable P11 schedule before first audited capture;
- do not use future target trajectory points in P9/P9a;
- do not open P9a labels merely because freeze tooling exists;
- do not lower P9/P4 gates;
- do not retune frozen Long72 from the first two genuine scores;
- do not change `live_adjustment` from zero without reviewed promotion.

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> forward/event-safe evaluation -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause model development.**
