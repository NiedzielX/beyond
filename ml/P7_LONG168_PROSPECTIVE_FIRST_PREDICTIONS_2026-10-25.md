# P7 Long168 — First Immutable Prospective Predictions

Date: **2026-10-25**

Status: **PROSPECTIVE_PREDICTIONS_ONLY**

Production: **UNCHANGED** (`live_adjustment = 0`)

## Purpose

Record the first genuine P7 Long168 predictions that were generated and persisted before target attendance was known.

This is forward evidence collection only. No attendance result is interpreted in this document.

## Execution lineage

GitHub Actions run:

`40216860928`

Commit:

`83bbd6b1179a8d9c79e13747918d62430244c76d`

Workflow:

`P7 Long168 Prospective Predict v1`

Job:

`predict-persist`

Result:

`SUCCESS`

Artifact:

`p7-long168-prospective-predict-v1-40216860928`

Artifact ID:

`12608131952`

Artifact ZIP SHA256:

`0728209781edbb9eb768dd56edfe7fb1e7f3efaea59519cdcc309d1b8985f6cf`

The workflow passed all hard gates before persistence:

- frozen Structural Prior bytes verified;
- exact training freeze manifest verified;
- pinned deterministic model fingerprint verified;
- no bootstrap backfill;
- target values used: false;
- production activation allowed: false;
- `live_adjustment = 0`;
- production change: false.

## Frozen mechanism

Candidate:

`gbr-l1-depth2-n50-lr003`

Training events:

`[1, 3, 4, 5, 10, 11, 15, 16, 18, 19]`

Training rows:

`139`

Training freeze manifest SHA256:

`185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`

Model fingerprint SHA256:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Source scorecard SHA256:

`f684570856e264dae288599a8e24dde6802f84669a43e304c1d900726aa94e45`

Prospective anchor package SHA256:

`dd839dbe48a530c536c02d6d1af927800f0aa60002fb92fa46c60bbed7c4653c`

Source prospective payload SHA256:

`6d0ebf68113f50c86620ad41b5ac1dd58a506c614d455a827bfa2b0498cf6722`

## First prediction set

All three predictions were inserted in one immutable prospective run.

Persisted at:

`2026-10-25T17:31:51.07782Z`

### Event 6 — Lech Poznań vs Wisła Kraków

- kickoff: `2026-10-31T16:30:00Z`;
- snapshot: `23218`;
- snapshot as-of: `2026-10-25T17:25:54.869383Z`;
- horizon: `143.0681h`;
- 6h bucket: `23`;
- stadium capacity: `43,269`;
- Structural Prior T-7 anchor P50: `32,079.50`;
- frozen P7 challenger P50: `38,265.33`;
- prediction identity SHA256: `1254d234819a91c71fe3e614142ce07484b529cef7b950e987e3d3d9487ab15c`.

### Event 444 — GKS Katowice vs Widzew Łódź

- kickoff: `2026-10-31T19:15:00Z`;
- snapshot: `23212`;
- snapshot as-of: `2026-10-25T17:20:02.061Z`;
- horizon: `145.9161h`;
- 6h bucket: `24`;
- stadium capacity: `15,048`;
- Structural Prior T-7 anchor P50: `11,184.79`;
- frozen P7 challenger P50: `15,048.00`;
- prediction identity SHA256: `46551aba4e9995c46de1fa7a791c54e0a2cfc3dee03e2f2f526c6359caa23d45`.

The challenger is clipped at verified stadium capacity exactly as precommitted.

### Event 446 — Wisła Płock vs Piast Gliwice

- kickoff: `2026-10-31T11:15:00Z`;
- snapshot: `23215`;
- snapshot as-of: `2026-10-25T17:20:02.378Z`;
- horizon: `137.9160h`;
- 6h bucket: `22`;
- stadium capacity: `15,004`;
- Structural Prior T-7 anchor P50: `6,472.28`;
- frozen P7 challenger P50: `13,557.22`;
- prediction identity SHA256: `fdb85868142994f0b0b07c3b139cc53aa826d5f4b286973524545fde9b41b341`.

## Persistence result

Database insert response:

- inserted predictions: **3**;
- total prediction rows after insert: **3**;
- independent prospective events after insert: **3**;
- target values used: false;
- production change: false.

## Outcome state at persistence

The outcome-later scorer ran immediately after persistence and found:

- scored events: **0**;
- newly scored events: **0**.

Therefore all first P7 prospective records were created before any eligible attendance outcome was attached.

Current evidence status:

`PROSPECTIVE_PREDICTIONS_ONLY`

No MAE, bias, improvement rate or promotion conclusion is available yet.

## Decision

1. Keep the exact model/fingerprint frozen.
2. Continue the scheduled `predict -> immutable persist` lane every six hours for newly eligible identities.
3. Score only after a genuine outcome is confirmed after the prediction timestamp.
4. Never recompute historical prospective predictions after the outcome becomes known.
5. Do not retune P7 from the first three events.
6. Keep production unchanged.
