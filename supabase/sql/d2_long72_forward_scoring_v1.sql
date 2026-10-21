-- d2 Long72 forward scoring v1
--
-- Additive, research-only infrastructure for the sealed historical package:
--   d2-long72-stage2-p2-observation-maturity-2026-10-21-v1
--
-- The export is outcome-free and admits only future Ekstraklasa events plus
-- PIT-safe snapshots captured after the package seal commit. The writer
-- hard-rejects any event whose outcome already exists at forecast-generation
-- time. Production remains unchanged.

begin;

create or replace function public.export_d2_long72_forward_rows_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with constants as (
  select
    'd2-long72-stage2-p2-observation-maturity-2026-10-21-v1'::text as package_id,
    '2026-10-21 17:37:07+00'::timestamptz as package_freeze_cutoff_at
), eligible as (
  select
    e.id as ticket_event_id,
    e.club_slug,
    e.home_team,
    e.away_team,
    e.competition,
    private.normalize_structural_prior_competition_v1(e.competition) as canonical_competition,
    e.kickoff_at,
    ha.club_key as home_club_key,
    aa.club_key as away_club_key,
    replace(f.season,'-','/') as season,
    f.round_number as round_no,
    cr.stadium_capacity,
    cr.source_name as capacity_source_name,
    cr.source_url as capacity_source_url,
    cr.verification_status as capacity_verification_status,
    c.package_id,
    c.package_freeze_cutoff_at
  from public.ticket_events e
  cross join constants c
  left join public.ticket_event_outcomes o
    on o.ticket_event_id=e.id
   and o.actual_attendance is not null
  left join private.structural_prior_club_aliases_v1 ha
    on ha.alias=e.home_team
   and ha.is_active
  left join private.structural_prior_club_aliases_v1 aa
    on aa.alias=e.away_team
   and aa.is_active
  left join lateral (
    select s.season,s.round_number
    from public.sporting_league_matches_shadow s
    left join private.structural_prior_club_aliases_v1 sh
      on sh.alias=s.home_team and sh.is_active
    left join private.structural_prior_club_aliases_v1 sa
      on sa.alias=s.away_team and sa.is_active
    where s.event_date=(e.kickoff_at at time zone 'Europe/Warsaw')::date
      and sh.club_key=ha.club_key
      and sa.club_key=aa.club_key
    order by s.fetched_at desc
    limit 1
  ) f on true
  left join lateral (
    select
      r.stadium_capacity,
      r.source_name,
      r.source_url,
      r.verification_status
    from private.structural_prior_capacity_registry_v1 r
    where r.club_key=ha.club_key
      and (e.kickoff_at at time zone 'Europe/Warsaw')::date>=r.valid_from
      and (
        r.valid_to is null
        or (e.kickoff_at at time zone 'Europe/Warsaw')::date<=r.valid_to
      )
    order by r.valid_from desc,r.id desc
    limit 1
  ) cr on true
  where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
    and e.kickoff_at>now()
    and e.kickoff_at>c.package_freeze_cutoff_at
    and o.ticket_event_id is null
    and ha.club_key is not null
    and aa.club_key is not null
    and f.season is not null
    and f.round_number is not null
    and cr.stadium_capacity is not null
), candidates as (
  select
    s.id as requested_snapshot_id,
    s.ticket_event_id,
    s.captured_at as requested_as_of_at,
    e.kickoff_at,
    e.stadium_capacity,
    extract(epoch from (e.kickoff_at-s.captured_at))/3600.0 as hours_to_kickoff,
    floor(extract(epoch from (e.kickoff_at-s.captured_at))/21600.0)::integer as bucket_6h,
    row_number() over (
      partition by
        s.ticket_event_id,
        floor(extract(epoch from (e.kickoff_at-s.captured_at))/21600.0)::integer
      order by s.captured_at desc,s.id desc
    ) as rn
  from public.snapshots s
  join eligible e on e.ticket_event_id=s.ticket_event_id
  where s.captured_at>=e.package_freeze_cutoff_at
    and s.captured_at<e.kickoff_at
    and s.captured_at>=e.kickoff_at-interval '72 hours'
    and s.captured_at<e.kickoff_at-interval '24 hours'
), live_rows as (
  select
    c.ticket_event_id,
    c.requested_snapshot_id,
    c.requested_as_of_at,
    c.hours_to_kickoff,
    c.bucket_6h,
    to_jsonb(f) as features
  from candidates c
  cross join lateral public.get_live_trajectory_features_v1_1_asof(
    c.ticket_event_id,
    c.requested_as_of_at,
    c.stadium_capacity
  ) f
  where c.rn=1
    and f.point_in_time_validated
    and f.snapshot_id is not null
), event_payload as (
  select coalesce(
    jsonb_agg(to_jsonb(e) order by e.kickoff_at,e.ticket_event_id),
    '[]'::jsonb
  ) as rows
  from eligible e
  where exists (
    select 1 from live_rows l where l.ticket_event_id=e.ticket_event_id
  )
), live_payload as (
  select coalesce(
    jsonb_agg(to_jsonb(l) order by l.ticket_event_id,l.requested_as_of_at),
    '[]'::jsonb
  ) as rows
  from live_rows l
)
select jsonb_build_object(
  'version','d2-long72-forward-rows-v1',
  'packageId',(select package_id from constants),
  'packageFreezeCutoffAt',(select package_freeze_cutoff_at from constants),
  'outcomeAccessAllowed',false,
  'window',jsonb_build_object(
    'hoursToKickoffLowerExclusive',24,
    'hoursToKickoffUpperInclusive',72,
    'cadenceHours',6,
    'samplingRule','latest available snapshot in each event x 6h bucket at export time'
  ),
  'eventCount',(select count(distinct ticket_event_id) from live_rows),
  'liveRowCount',(select count(*) from live_rows),
  'events',(select rows from event_payload),
  'liveRows',(select rows from live_payload)
);
$function$;

revoke all on function public.export_d2_long72_forward_rows_v1()
  from public,anon,authenticated;
grant execute on function public.export_d2_long72_forward_rows_v1()
  to service_role;

create or replace function public.insert_d2_long72_forward_forecast_v1(
  p_observation jsonb
)
returns bigint
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
  v_package_id constant text := 'd2-long72-stage2-p2-observation-maturity-2026-10-21-v1';
  v_freeze_cutoff constant timestamptz := '2026-10-21 17:37:07+00'::timestamptz;
  v_event_id bigint;
  v_snapshot_id bigint;
  v_generated_at timestamptz;
  v_snapshot_at timestamptz;
  v_kickoff_at timestamptz;
  v_model_version text;
  v_package_payload_id text;
  v_hours double precision;
  v_bucket integer;
  v_capacity integer;
  v_anchor_p50 numeric;
  v_final_p50 numeric;
  v_reliability numeric;
  v_registered_capacity integer;
  v_db_snapshot_at timestamptz;
  v_id bigint;
begin
  if p_observation is null then
    raise exception 'p_observation is required';
  end if;

  v_event_id := nullif(p_observation->>'ticket_event_id','')::bigint;
  v_snapshot_id := nullif(p_observation->>'source_snapshot_id','')::bigint;
  v_generated_at := nullif(p_observation->>'forecast_generated_at','')::timestamptz;
  v_snapshot_at := nullif(p_observation->>'source_snapshot_captured_at','')::timestamptz;
  v_kickoff_at := nullif(p_observation->'payload'->>'kickoff_at','')::timestamptz;
  v_model_version := nullif(p_observation->>'model_version','');
  v_package_payload_id := nullif(p_observation->'payload'->>'package_id','');
  v_hours := nullif(p_observation->>'hours_to_kickoff','')::double precision;
  v_bucket := nullif(p_observation->'payload'->>'bucket_6h','')::integer;
  v_capacity := nullif(p_observation->'payload'->>'stadium_capacity','')::integer;
  v_anchor_p50 := nullif(p_observation->'payload'->>'anchor_p50','')::numeric;
  v_final_p50 := nullif(p_observation->'payload'->>'final_p50','')::numeric;
  v_reliability := nullif(p_observation->'payload'->>'reliability','')::numeric;

  if v_event_id is null or v_snapshot_id is null or v_generated_at is null
     or v_snapshot_at is null or v_kickoff_at is null or v_hours is null
     or v_bucket is null or v_capacity is null or v_anchor_p50 is null
     or v_final_p50 is null or v_reliability is null then
    raise exception 'incomplete long72 forward observation';
  end if;
  if v_model_version<>v_package_id or v_package_payload_id<>v_package_id then
    raise exception 'package id mismatch';
  end if;
  if coalesce(p_observation->>'forecast_status','')<>'shadow' then
    raise exception 'long72 writer accepts shadow forecasts only';
  end if;
  if coalesce(p_observation->>'correction_status','')<>'frozen_long72_p2_research' then
    raise exception 'invalid correction_status';
  end if;
  if v_snapshot_at<v_freeze_cutoff then
    raise exception 'source snapshot predates package freeze cutoff';
  end if;
  if v_generated_at<v_snapshot_at or v_generated_at>=v_kickoff_at then
    raise exception 'forecast must be generated after snapshot and before kickoff';
  end if;
  if not (v_hours>24.0 and v_hours<=72.0) then
    raise exception 'hours_to_kickoff outside frozen long72 scope';
  end if;
  if v_bucket<>floor(v_hours/6.0)::integer then
    raise exception 'bucket_6h mismatch';
  end if;
  if v_reliability<0 or v_reliability>1 then
    raise exception 'reliability outside [0,1]';
  end if;
  if v_anchor_p50<0 or v_anchor_p50>v_capacity
     or v_final_p50<0 or v_final_p50>v_capacity then
    raise exception 'forecast outside physical capacity bounds';
  end if;

  if not exists (
    select 1
    from public.ticket_events e
    where e.id=v_event_id
      and e.kickoff_at=v_kickoff_at
      and e.kickoff_at>v_freeze_cutoff
      and private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
  ) then
    raise exception 'event is not eligible for frozen long72 forward scoring';
  end if;

  if exists (
    select 1
    from public.ticket_event_outcomes o
    where o.ticket_event_id=v_event_id
      and o.actual_attendance is not null
  ) then
    raise exception 'outcome already exists; prospective write rejected';
  end if;

  select s.captured_at
  into v_db_snapshot_at
  from public.snapshots s
  where s.id=v_snapshot_id
    and s.ticket_event_id=v_event_id;
  if not found or v_db_snapshot_at<>v_snapshot_at then
    raise exception 'source snapshot lineage mismatch';
  end if;

  if abs(
    v_hours
    - extract(epoch from (v_kickoff_at-v_snapshot_at))/3600.0
  )>0.001 then
    raise exception 'hours_to_kickoff lineage mismatch';
  end if;

  select r.stadium_capacity
  into v_registered_capacity
  from public.ticket_events e
  join private.structural_prior_club_aliases_v1 a
    on a.alias=e.home_team and a.is_active
  join private.structural_prior_capacity_registry_v1 r
    on r.club_key=a.club_key
  where e.id=v_event_id
    and (e.kickoff_at at time zone 'Europe/Warsaw')::date>=r.valid_from
    and (
      r.valid_to is null
      or (e.kickoff_at at time zone 'Europe/Warsaw')::date<=r.valid_to
    )
  order by r.valid_from desc,r.id desc
  limit 1;
  if v_registered_capacity is null or v_registered_capacity<>v_capacity then
    raise exception 'verified capacity mismatch';
  end if;

  -- Idempotent per immutable source snapshot + package. Multiple source
  -- snapshots may coexist in the same 6h bucket; downstream scoring selects
  -- the latest persisted pre-outcome forecast per event x bucket.
  select fo.id
  into v_id
  from public.forecast_observations fo
  where fo.ticket_event_id=v_event_id
    and fo.source_snapshot_id=v_snapshot_id
    and fo.model_version=v_package_id
    and fo.forecast_status='shadow'
  order by fo.id desc
  limit 1;
  if found then
    return v_id;
  end if;

  v_id := nextval('public.forecast_observations_id_seq');

  insert into public.forecast_observations (
    id,
    ticket_event_id,
    source_snapshot_id,
    forecast_generated_at,
    source_snapshot_captured_at,
    hours_to_kickoff,
    days_to_match,
    horizon,
    model_version,
    historical_model,
    historical_p10,
    historical_p50,
    historical_p90,
    live_adjustment,
    final_p10,
    final_p50,
    final_p90,
    forecast_status,
    correction_status,
    signal_readiness,
    live_available_total,
    live_first_available_total,
    live_available_index,
    live_net_removed_since_first,
    live_net_removed_since_previous,
    live_velocity_since_previous,
    live_net_removed_6h,
    live_velocity_6h,
    live_net_removed_24h,
    live_velocity_24h,
    live_acceleration_6h_vs_24h,
    live_raw_snapshot_count,
    live_clean_snapshot_count,
    live_excluded_anomaly_count,
    payload
  ) values (
    v_id,
    v_event_id,
    v_snapshot_id,
    v_generated_at,
    v_snapshot_at,
    v_hours,
    v_hours/24.0,
    'T-3-live-24-72',
    v_package_id,
    'pre-live-v2-v3-equivalent-t3-plus-b2',
    null,
    round(v_anchor_p50)::integer,
    null,
    round(v_final_p50-v_anchor_p50)::integer,
    null,
    round(v_final_p50)::integer,
    null,
    'shadow',
    'frozen_long72_p2_research',
    nullif(p_observation->>'signal_readiness',''),
    nullif(p_observation->>'live_available_total','')::integer,
    nullif(p_observation->>'live_first_available_total','')::integer,
    nullif(p_observation->>'live_available_index','')::double precision,
    nullif(p_observation->>'live_net_removed_since_first','')::integer,
    nullif(p_observation->>'live_net_removed_since_previous','')::integer,
    nullif(p_observation->>'live_velocity_since_previous','')::double precision,
    nullif(p_observation->>'live_net_removed_6h','')::integer,
    nullif(p_observation->>'live_velocity_6h','')::double precision,
    nullif(p_observation->>'live_net_removed_24h','')::integer,
    nullif(p_observation->>'live_velocity_24h','')::double precision,
    nullif(p_observation->>'live_acceleration_6h_vs_24h','')::double precision,
    nullif(p_observation->>'live_raw_snapshot_count','')::integer,
    nullif(p_observation->>'live_clean_snapshot_count','')::integer,
    nullif(p_observation->>'live_excluded_anomaly_count','')::integer,
    coalesce(p_observation->'payload','{}'::jsonb)
  );

  return v_id;
end;
$function$;

revoke all on function public.insert_d2_long72_forward_forecast_v1(jsonb)
  from public,anon,authenticated;
grant execute on function public.insert_d2_long72_forward_forecast_v1(jsonb)
  to service_role;

commit;
