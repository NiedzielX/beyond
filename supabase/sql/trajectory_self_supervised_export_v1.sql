-- Beyond Ticketing — Self-Supervised Trajectory Export v1
-- Applied live: 2026-10-28
-- Target-free research only. No attendance or structural-prior data are exposed.

create or replace function public.export_trajectory_self_supervised_v1()
returns jsonb
language sql
security definer
set search_path = public, private
as $$
with params as (
  select
    '2026-10-28T22:09:43.958409Z'::timestamptz as frozen_cutoff,
    array[3,1,4,9,14,15,18,11,19,5,20,10,16,23,21,22,443,446,6,444,445,447,449,450,451,452]::bigint[] as event_ids
), raw as (
  select
    e.id as ticket_event_id,
    e.club_slug,
    e.kickoff_at,
    s.id as snapshot_id,
    s.captured_at,
    s.available_total,
    floor(extract(epoch from (e.kickoff_at-s.captured_at))/3600.0)::int as hour_bucket
  from params p
  join public.ticket_events e on e.id = any(p.event_ids)
  join public.snapshots s on s.ticket_event_id=e.id
  where s.captured_at <= p.frozen_cutoff
    and s.captured_at < e.kickoff_at
    and s.available_total is not null
    and s.available_total >= 0
), dedup_ts as (
  select distinct on (ticket_event_id,captured_at)
    ticket_event_id,club_slug,kickoff_at,snapshot_id,captured_at,available_total,hour_bucket
  from raw
  order by ticket_event_id,captured_at,snapshot_id desc
), hourly as (
  select distinct on (ticket_event_id,hour_bucket)
    ticket_event_id,club_slug,kickoff_at,snapshot_id,captured_at,available_total,hour_bucket
  from dedup_ts
  order by ticket_event_id,hour_bucket,captured_at desc,snapshot_id desc
), events as (
  select
    ticket_event_id,
    max(club_slug) as club_slug,
    max(kickoff_at) as kickoff_at,
    jsonb_agg(
      jsonb_build_object(
        'snapshot_id',snapshot_id,
        'captured_at',captured_at,
        'available_total',available_total,
        'hours_to_kickoff',extract(epoch from (kickoff_at-captured_at))/3600.0
      ) order by captured_at,snapshot_id
    ) as observations
  from hourly
  group by ticket_event_id
)
select jsonb_build_object(
  'version','trajectory-self-supervised-export-v1',
  'precommit_id','trajectory-self-supervised-24h-delta-v1',
  'frozen_data_cutoff',(select frozen_cutoff from params),
  'attendance_labels_used',false,
  'structural_prior_used',false,
  'event_count',(select count(*) from events),
  'observation_count',(select count(*) from hourly),
  'events',coalesce((
    select jsonb_agg(
      jsonb_build_object(
        'ticket_event_id',ticket_event_id,
        'club_slug',club_slug,
        'kickoff_at',kickoff_at,
        'observations',observations
      ) order by kickoff_at,ticket_event_id
    ) from events
  ),'[]'::jsonb),
  'production_change',false
);
$$;

revoke all on function public.export_trajectory_self_supervised_v1()
  from public, anon, authenticated;
grant execute on function public.export_trajectory_self_supervised_v1()
  to service_role;
