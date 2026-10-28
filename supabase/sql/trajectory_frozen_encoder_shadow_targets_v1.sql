-- Beyond Ticketing — Frozen Encoder Prospective Shadow Targets v1
-- Applied live: 2026-10-28
-- Research shadow only; production_change=false.

create or replace function public.get_trajectory_frozen_encoder_shadow_due_v1()
returns jsonb
language sql
security definer
set search_path = public, private
as $$
with params as (
  select
    clock_timestamp() as now_at,
    'trajectory-frozen-encoder-ridge-ratio-head-v1'::text as model_version
), horizons(days_to_event) as (
  values (7),(3),(1)
), due as (
  select
    e.id as ticket_event_id,
    e.club_slug,
    e.kickoff_at,
    h.days_to_event,
    e.kickoff_at - make_interval(days => h.days_to_event) as target_as_of_at
  from public.ticket_events e
  cross join horizons h
  cross join params p
  where e.kickoff_at is not null
    and p.now_at >= e.kickoff_at - make_interval(days => h.days_to_event)
    and p.now_at <= e.kickoff_at - make_interval(days => h.days_to_event) + interval '90 minutes'
    and p.now_at < e.kickoff_at
    and not exists (
      select 1
      from public.ticket_event_outcomes o
      where o.ticket_event_id=e.id and o.actual_attendance is not null
    )
    and not exists (
      select 1
      from private.daily_trajectory_attempts_v1 a
      where a.ticket_event_id=e.id
        and a.days_to_event=h.days_to_event
        and a.model_version=p.model_version
    )
), enriched as (
  select
    d.*,
    prior.id as structural_prior_id,
    prior.p50::double precision as structural_p50,
    prior.stadium_capacity,
    prior.model_spec_id as structural_model_spec_id,
    prior.generated_at as structural_generated_at,
    coalesce(obs.observations,'[]'::jsonb) as observations
  from due d
  left join lateral (
    select p.*
    from private.structural_prior_forecasts_v1 p
    where p.ticket_event_id=d.ticket_event_id
      and p.point_in_time_validated=true
      and p.target_as_of_at <= d.target_as_of_at
      and p.generated_at <= d.target_as_of_at
    order by p.target_as_of_at desc,p.generated_at desc,p.id desc
    limit 1
  ) prior on true
  left join lateral (
    with raw as (
      select
        s.id as snapshot_id,
        s.captured_at,
        s.available_total,
        floor(extract(epoch from (d.kickoff_at-s.captured_at))/3600.0)::int as hour_bucket
      from public.snapshots s
      where s.ticket_event_id=d.ticket_event_id
        and s.captured_at <= d.target_as_of_at
        and s.captured_at < d.kickoff_at
        and s.available_total is not null
        and s.available_total >= 0
    ), dedup_ts as (
      select distinct on (captured_at)
        snapshot_id,captured_at,available_total,hour_bucket
      from raw
      order by captured_at,snapshot_id desc
    ), hourly as (
      select distinct on (hour_bucket)
        snapshot_id,captured_at,available_total,hour_bucket
      from dedup_ts
      order by hour_bucket,captured_at desc,snapshot_id desc
    )
    select jsonb_agg(
      jsonb_build_object(
        'snapshot_id',snapshot_id,
        'captured_at',captured_at,
        'available_total',available_total,
        'hours_to_kickoff',extract(epoch from (d.kickoff_at-captured_at))/3600.0
      ) order by captured_at,snapshot_id
    ) as observations
    from hourly
  ) obs on true
)
select jsonb_build_object(
  'version','trajectory-frozen-encoder-shadow-due-v1',
  'model_version',(select model_version from params),
  'generated_at',(select now_at from params),
  'target_values_used',false,
  'production_change',false,
  'target_count',(select count(*) from enriched),
  'targets',coalesce((
    select jsonb_agg(
      jsonb_build_object(
        'ticket_event_id',ticket_event_id,
        'club_slug',club_slug,
        'kickoff_at',kickoff_at,
        'days_to_event',days_to_event,
        'target_as_of_at',target_as_of_at,
        'structural_prior_id',structural_prior_id,
        'structural_p50',structural_p50,
        'stadium_capacity',stadium_capacity,
        'structural_model_spec_id',structural_model_spec_id,
        'structural_generated_at',structural_generated_at,
        'observations',observations
      ) order by target_as_of_at,ticket_event_id
    ) from enriched
  ),'[]'::jsonb)
);
$$;

revoke all on function public.get_trajectory_frozen_encoder_shadow_due_v1()
  from public, anon, authenticated;
grant execute on function public.get_trajectory_frozen_encoder_shadow_due_v1()
  to service_role;
