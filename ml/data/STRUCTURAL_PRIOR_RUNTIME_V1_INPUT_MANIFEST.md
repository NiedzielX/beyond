# Structural Prior Runtime v1 — canonical input manifest

Last verified: **2026-10-15**

This manifest pins the exact validated CSV bytes used to rebuild the five-season point-in-time feature store for `Structural Prior Runtime v1`.

| Input | Rows | Bytes | SHA-256 |
|---|---:|---:|---|
| `historical_multiclub_2021_25_v2_1.csv` | 1,224 | 608,360 | `ab7e460f09b9d64d2e45403affe6e405ea1e40d79c2ded3321f3101bd9851fa7` |
| `historical_multiclub_2025_26_v1.csv` | 306 | 144,601 | `42db003225ba0f5abde4a64cf33b7e5cca96a5250ef8b3f0874badd6c82ed550` |

Combined modelling population: **1,530 matches**.

The builder consumes only these columns from each input:

`season, round, date, kickoff_time_local, home_team, away_team, home_club_key, away_club_key, home_goals, away_goals, attendance, match_key`.

## Provenance

2021/22–2024/25:

- dataset version: `historical-multiclub-2021-25-v2.1`;
- observed attendance source layer: Paszport Kibica / 90minut-derived records;
- source-date validation reference: `tmorcinek/ekstraklasa-analysis`, commit `390b85cd67aae2223be1c9a0ff558259559596a5`, `data/POL.csv`;
- 53 source dates reconciled against the pinned reference;
- one verified closed-door zero-attendance match retained as historical truth and excluded from normal demand training.

2025/26:

- dataset version: `historical-multiclub-2025-26-v1`;
- source repo: `Mewhoosh/ekstraklasa-2025-26-analytics`;
- source commit: `bce5fb1ef95298a7f2c8687177bd6e9c5461c63a`;
- canonical builder: `ml/data/build_historical_multiclub.py`.

## Reproduction rule

A benchmark run must not be called a reproduction of `Structural Prior Runtime v1` unless the two input hashes above match exactly, or a new versioned dataset/benchmark is explicitly created and re-evaluated under the frozen chronological protocol.
