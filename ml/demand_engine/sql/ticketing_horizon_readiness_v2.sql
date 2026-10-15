-- Canonical Beyond live-horizon readiness contract v2.
--
-- v1 selected the nearest snapshot by absolute time distance and could therefore
-- select information captured after the intended checkpoint. v2 is strictly
-- point-in-time: every feature row is computed at the exact T-30/T-14/T-7/T-3/T-1
-- cutoff via get_live_trajectory_features_v1_asof.

create or replace view private.ticketing_horizon_readiness_v2 as
with horizons(horizon,target_days_before,target_interval) as (
    values
      ('T-30'::text,30::integer,interval '30 days'),
      ('T-14'::text,14::integer,interval '14 days'),
      ('T-7'::text,7::integer,interval '7 days'),
      ('T-3'::text,3::integer,interval '3 days'),
      ('T-1'::text,1::integer,interval '1 day')
),
base as (
    select
      e.id as ticket_event_id,
      e.club_slug,
      e.home_team,
      e.away_team,
      e.competition,
      e.external_event_id,
      e.kickoff_at,
      h.horizon,
      h.target_days_before,
      e.kickoff_at-h.target_interval as target_as_of_at,
      (e.kickoff_at-h.target_interval <= now()) as checkpoint_due
    from public.ticket_events e
    cross join horizons h
    where e.kickoff_at is not null
)
select
    b.ticket_event_id,
    b.club_slug,
    b.home_team,
    b.away_team,
    b.competition,
    b.external_event_id,
    b.kickoff_at,
    b.horizon,
    b.target_days_before,
    b.target_as_of_at,
    b.checkpoint_due,
    f.snapshot_id,
    f.snapshot_captured_at,
    f.snapshot_age_minutes,
    f.feature_version,
    f.feature_quality,
    f.signal_readiness,
    f.point_in_time_validated,
    f.available_total,
    f.first_available_total,
    f.available_index,
    f.raw_snapshot_count,
    f.clean_snapshot_count,
    f.excluded_anomaly_count,
    f.max_visible_gap_hours,
    f.data_gap_detected,
    case
      when not b.checkpoint_due then false
      when f.snapshot_id is null then false
      when f.signal_readiness <> 'ready' then false
      else true
    end as checkpoint_ready,
    case
      when not b.checkpoint_due then 'not_due'
      when f.snapshot_id is null then 'missing_snapshot'
      when f.signal_readiness <> 'ready' then 'insufficient_signal'
      else 'ready'
    end as readiness_status
from base b
left join lateral public.get_live_trajectory_features_v1_asof(
    b.ticket_event_id,
    b.target_as_of_at,
    null
) f on b.checkpoint_due;

comment on view private.ticketing_horizon_readiness_v2 is
'Canonical leakage-safe horizon readiness for Live Demand Engine. Statuses: not_due, missing_snapshot, insufficient_signal, ready. Supersedes ticketing_horizon_checkpoint_readiness_v1 for new modelling work; v1 remains unchanged for reproducibility.';
