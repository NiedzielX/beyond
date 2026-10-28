-- Beyond Ticketing — Trajectory Development Export v1
-- Applied live: 2026-10-28
-- Research-only, service-role-only export for the frozen Lane A/Lane B cohort.

create or replace function public.export_trajectory_development_rows_v1(
  p_event_ids bigint[]
)
returns jsonb
language sql
security definer
set search_path = public, private
as $$
with base as (
  select
    fs.id as feature_row_id,
    fs.ticket_event_id,
    fs.horizon,
    fs.as_of_at,
    fs.kickoff_at,
    fs.signal_readiness,
    fs.feature_quality,
    fs.point_in_time_validated,
    fs.features,
    e.club_slug,
    o.actual_attendance,
    o.confirmed_at
  from private.live_trajectory_feature_snapshots_v1 fs
  join public.ticket_events e on e.id=fs.ticket_event_id
  join public.ticket_event_outcomes o on o.ticket_event_id=fs.ticket_event_id
  where fs.ticket_event_id = any(p_event_ids)
    and o.actual_attendance is not null
), eligible as (
  select
    b.*,
    p.id as structural_prior_id,
    p.p50::double precision as structural_p50,
    p.stadium_capacity,
    (b.features->>'clean_snapshot_count')::int as clean_snapshot_count,
    (b.features->>'observation_window_hours')::double precision as observation_window_hours
  from base b
  left join lateral (
    select p.*
    from private.structural_prior_forecasts_v1 p
    where p.ticket_event_id=b.ticket_event_id
      and p.point_in_time_validated=true
      and p.target_as_of_at <= b.as_of_at
      and p.generated_at <= b.as_of_at
    order by p.target_as_of_at desc,p.generated_at desc,p.id desc
    limit 1
  ) p on true
  where b.point_in_time_validated=true
    and b.signal_readiness='ready'
    and coalesce((b.features->>'clean_snapshot_count')::int,0) >= 4
    and coalesce((b.features->>'observation_window_hours')::double precision,0) >= 24
), model_rows as (
  select
    e.*,
    coalesce((
      select jsonb_agg(
        jsonb_build_array(
          round(extract(epoch from (e.kickoff_at-z.captured_at))/3600.0,6),
          z.available_total
        ) order by z.captured_at,z.id
      )
      from (
        select distinct on (hour_bucket)
          d.id,d.captured_at,d.available_total,d.hour_bucket
        from (
          select distinct on (s.captured_at)
            s.id,
            s.captured_at,
            s.available_total,
            floor(extract(epoch from (e.kickoff_at-s.captured_at))/3600.0)::int as hour_bucket
          from public.snapshots s
          where s.ticket_event_id=e.ticket_event_id
            and s.captured_at <= e.as_of_at
            and s.captured_at < e.kickoff_at
            and s.available_total is not null
            and s.available_total >= 0
          order by s.captured_at,s.id desc
        ) d
        order by hour_bucket,d.captured_at desc,d.id desc
      ) z
    ),'[]'::jsonb) as sequence_pairs
  from eligible e
  where e.structural_prior_id is not null
)
select jsonb_build_object(
  'version','trajectory-development-export-v1',
  'feature_contract_id','trajectory-feature-contract-v1',
  'evidence_class','historical_exposed_research',
  'event_count',(select count(distinct ticket_event_id) from model_rows),
  'row_count',(select count(*) from model_rows),
  'rows',coalesce((
    select jsonb_agg(
      jsonb_build_object(
        'feature_row_id',feature_row_id,
        'ticket_event_id',ticket_event_id,
        'club_slug',club_slug,
        'horizon',horizon,
        'as_of_at',as_of_at,
        'kickoff_at',kickoff_at,
        'actual_attendance',actual_attendance,
        'attendance_confirmed_at',confirmed_at,
        'structural_prior_id',structural_prior_id,
        'structural_p50',structural_p50,
        'stadium_capacity',stadium_capacity,
        'feature_quality',feature_quality,
        'features',features,
        'sequence_pairs',sequence_pairs,
        'target_values_used_in_features',false,
        'production_change',false
      ) order by kickoff_at,ticket_event_id,as_of_at
    ) from model_rows
  ),'[]'::jsonb),
  'production_change',false
);
$$;

revoke all on function public.export_trajectory_development_rows_v1(bigint[])
  from public, anon, authenticated;
grant execute on function public.export_trajectory_development_rows_v1(bigint[])
  to service_role;
