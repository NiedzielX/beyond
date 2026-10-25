# P7 Long168 Prospective v1 — Frozen Model Fingerprint

Frozen: **2026-10-25**, before any prospective prediction was persisted.

Source fingerprint workflow run:

`40201818862` (retry after service-role summary permission plumbing fix)

Status: **SUCCESS**

## Pinned identity

Candidate:

`gbr-l1-depth2-n50-lr003`

Training event IDs:

`[1, 3, 4, 5, 10, 11, 15, 16, 18, 19]`

Training rows:

`139`

Training freeze manifest SHA256:

`185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`

Source scorecard SHA256:

`f684570856e264dae288599a8e24dde6802f84669a43e304c1d900726aa94e45`

Pinned deterministic model fingerprint SHA256:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Fingerprint contract SHA256:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Fingerprint artifact ZIP SHA256:

`a6dab7c220e065a9e2d2b5f32954303bf067387b1d24458b1fa1066d5a507184`

Artifact ID:

`12607727556`

## Fingerprint-run eligibility snapshot

At fingerprint time the target-free prospective export contained three currently eligible event identities:

`[6, 444, 446]`

Eligible prediction count: **3**.

This eligibility snapshot is informational only. Predict runs must re-evaluate eligibility at their own execution time and may persist only identities that remain prospectively eligible then.

## Guardrails

- fingerprint was produced before any prospective prediction persistence;
- `bootstrap_backfill_performed=false`;
- `target_values_used=false`;
- `production_activation_allowed=false`;
- `live_adjustment=0`;
- `production_change=false`;
- no candidate search or hyperparameter search occurred;
- any fingerprint drift must fail closed and requires a new explicit version/precommit rather than silent retraining.
