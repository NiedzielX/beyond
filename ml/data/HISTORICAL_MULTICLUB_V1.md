# Historical Multi-Club Dataset v1

## Purpose

Provide a reproducible, match-level historical attendance dataset for Beyond's global forecasting model.

## Current source layer

The first production-quality historical layer is the **completed 2025/26 Ekstraklasa season**.

Source:

- public repository: `Mewhoosh/ekstraklasa-2025-26-analytics`;
- source data: processed FBref club match logs;
- source is pinned to immutable commit `bce5fb1ef95298a7f2c8687177bd6e9c5461c63a`;
- we do not bypass FBref's direct CI access restrictions;
- only `Comp = Ekstraklasa` and `Venue = Home` rows are retained, so each league match occurs once.

Current expected scope:

- season: 2025/26;
- 18 home clubs;
- 17 home league matches per club;
- 306 completed matches total;
- match-level attendance target.

## Expansion plan

2025/26 is **layer 1, not the final historical dataset**.

Older seasons will be added only from sources that are reproducible and can be pinned/versioned. The target remains multiple seasons and >1,000 match-level observations, but the model should start using the validated 2025/26 layer immediately instead of waiting for the full archive.

## Required columns

- season;
- round;
- date;
- kickoff_time_local;
- home_team / away_team;
- home_club_key / away_club_key;
- home_goals / away_goals;
- attendance;
- referee;
- match_key;
- source_name;
- source_repo / source_commit / source_path / source_url;
- completed;
- attendance_observed;
- attendance_positive.

## Quality gate

For the current completed season:

- exactly 306 completed league matches;
- exactly 18 home clubs;
- exactly 17 home league matches per club;
- >=98% attendance coverage;
- unique match keys;
- every observed attendance must be positive.

A failed gate blocks use as a training dataset.

## Modelling rule

This dataset is historical ground truth. It may be used to create point-in-time historical features only.

Any feature derived from league position, form, opponent performance or attendance history must be reconstructed strictly from information available before the forecast checkpoint.

The final attendance target for a match must never enter the feature state for that same match.

## Next layer

After the raw dataset passes quality gates:

1. persist it in Beyond's historical data layer;
2. create point-in-time feature snapshots;
3. build a global multi-club benchmark;
4. compare global models against club-specific baselines;
5. add older seasons without changing the feature/benchmark contract.
