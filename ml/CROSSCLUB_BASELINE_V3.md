# Beyond Ticketing — Cross-club Baseline v3

Status: **research fallback active**  
Production impact: **none**

## Purpose

Provide a leakage-safe baseline P50 for clubs that do not yet have an incumbent historical forecast, so Context Snapshot / Ablation can evaluate multiple clubs rather than only Lech.

## Baseline definition

For home Ekstraklasa events:

`P50 = median verified home attendance from prior home Ekstraklasa matches`

Minimum history gate: **3 prior home outcomes**.

No league-wide median is used as a fallback. If a club has fewer than 3 prior home outcomes, baseline remains null.

## Selection rule

The Context Ablation `baseline` variant uses:
1. incumbent engine historical baseline when one already exists;
2. otherwise `club_trailing_home_median_v3` when the cross-club gate is met;
3. otherwise no baseline prediction.

The cross-club baseline never overwrites the incumbent engine baseline.

## Evidence modes

### Retrospective historical-fact reconstruction

Used for bootstrap snapshots created after the historical checkpoints had already passed.

A historical attendance may enter the baseline only when its match kickoff was strictly before the target checkpoint. The row is explicitly labelled `retrospective_historical_fact_reconstruction` because the Beyond database itself was populated later during migration/research.

### Prospective system point-in-time

Used for snapshots captured prospectively.

A historical attendance may enter the baseline only when:
- its match kickoff is before the target checkpoint; and
- the attendance record was already available in Beyond before the checkpoint.

This mode is labelled `prospective_system_point_in_time`.

## Current coverage — 2026-10-13

Eligible club history currently exists for:
- Lech Poznań;
- Pogoń Szczecin;
- Cracovia;
- Jagiellonia Białystok;
- Legia Warszawa;
- GKS Katowice;
- Śląsk Wrocław.

Current insufficient-history examples include Górnik Zabrze, Zagłębie Lubin and Wisła Płock. Lech–Bayer is excluded from this fallback because v3 is currently Ekstraklasa-home-only.

Context snapshot baseline coverage after backfill:
- T-7d: 12 baseline-ready snapshots;
- T-3d: 9;
- T-24h: 9;
- T-6h: 9.

Completed-event baseline evaluation currently spans **9 events / 7 clubs** at T-3d, T-24h and T-6h.

## Same-event challenger check

For incumbent Lech events where both the incumbent baseline and trailing-median challenger can be computed, the challenger currently has lower MAE on the same tiny sample:

| Checkpoint | N | Incumbent MAE | Trailing median MAE | MAE improvement |
|---|---:|---:|---:|---:|
| T-7d | 2 | 9,698.5 | 4,707.0 | +4,991.5 |
| T-3d | 3 | 12,629.0 | 7,082.0 | +5,547.0 |
| T-24h | 3 | 12,532.0 | 8,078.7 | +4,453.3 |
| T-6h | 3 | 12,532.0 | 8,078.7 | +4,453.3 |

This is **not a promotion result**. The sample is only 2–3 independent matches and remains research-only. It does, however, justify keeping the simple trailing median as an explicit challenger to the current runtime historical baseline.

## Automation

`event_context_snapshot_15m` captures due snapshots every 15 minutes.

`crossclub_checkpoint_baseline_15m` runs at minutes `02,17,32,47`, after the snapshot collector, and creates missing baseline fallback predictions.

## Dashboard

Model Lab exposes:
- baseline coverage by club/checkpoint;
- incumbent vs fallback source;
- insufficient-history and unsupported-competition states;
- same-event incumbent vs challenger MAE comparison;
- explicit research-only warning.
