# Historical Multi-Club Dataset v1

## Purpose

Provide a reproducible, match-level historical attendance dataset for Beyond's global forecasting model.

## Scope

- competition: Ekstraklasa;
- seasons: 2021/22 through 2025/26;
- expected full-season matches: 306 per season;
- primary source: FBref Scores & Fixtures;
- target: match attendance;
- this dataset is historical ground truth, not live ticketing telemetry.

## Required columns

- season;
- round;
- date;
- kickoff_time_local;
- home_team / away_team;
- home_club_key / away_club_key;
- home_goals / away_goals;
- attendance;
- venue;
- referee;
- match_key;
- source_name / source_url;
- completed;
- attendance_observed;
- attendance_positive.

## Quality gate

For each completed full season:

- exactly 306 completed league matches;
- >=95% attendance coverage;
- unique match keys;
- no negative attendance values.

A failed gate blocks use as a training dataset.

## Modelling rule

This dataset may be used to create point-in-time historical features only. Any feature derived from league position, form, opponent performance or attendance history must be reconstructed strictly from information available before the forecast checkpoint.

The raw final attendance target must never enter the feature state for the same match.

## Next layer

After this raw dataset passes quality gates, build `Feature Store v1` snapshots at multiple horizons and benchmark a global multi-club model against club-specific historical baselines.
