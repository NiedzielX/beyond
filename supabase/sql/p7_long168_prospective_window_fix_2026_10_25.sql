-- Tighten P7 prospective eligibility before the first prospective prediction.
-- A historical T-168..T-72 snapshot is not enough: prediction persistence itself
-- must happen while the event is currently >72h and <=168h from kickoff.

create or replace function public.export_p7_long168_prospective_inputs_v1()
returns jsonb
language sql
stable
security invoker
set search_path to 'public', 'private'
as $function$
with eligible_base as (
  select
    e.id as ticket_event_id,
    e.club_slug,
    e.home_team,
    e.away_team,
    e.competition,
    private.normalize_structural_prior_competition_v1(e.competition) as canonical_competition,
    e.kickoff_at,
    ha.club_key as home_club_key,
    aa.club_key as away_club_key
  from public.ticket_events e
  left join private.structural_prior_club_aliases_v1 ha on ha.alias=e.home_team and ha.is_active
  left join private.structural_prior_club_aliases_v1 aa on aa.alias=e.away_team and aa.is_active
  where e.kickoff_at > now() + interval '72 hours'
    and e.kickoff_at <= now() + interval '168 hours'
    and private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
    and not exists (
      select 1 from public.ticket_event_outcomes o
      where o.ticket_event_id=e.id and o.actual_attendance is not null
    )
), enriched as (
  select
    e.*,
    f.season as sporting_season,
    replace(f.season,'-','/') as season,
    f.round_number as round_no,
    cr.stadium_capacity,
    cr.source_name as capacity_source_name,
    cr.source_url as capacity_source_url,
    cr.verification_status as capacity_verification_status
  from eligible_base e
  left join lateral (
    select s.season,s.round_number
    from public.sporting_league_matches_shadow s
    left join private.structural_prior_club_aliases_v1 sh on sh.alias=s.home_team and sh.is_active
    left join private.structural_prior_club_aliases_v1 sa on sa.alias=s.away_team and sa.is_active
    where s.event_date=(e.kickoff_at at time zone 'Europe/Warsaw')::date
      and sh.club_key=e.home_club_key and sa.club_key=e.away_club_key
    order by s.fetched_at desc limit 1
  ) f on true
  left join lateral (
    select c.stadium_capacity,c.source_name,c.source_url,c.verification_status
    from private.structural_prior_capacity_registry_v1 c
    where c.club_key=e.home_club_key
      and (e.kickoff_at at time zone 'Europe/Warsaw')::date>=c.valid_from
      and (c.valid_to is null or (e.kickoff_at at time zone 'Europe/Warsaw')::date<=c.valid_to)
    order by c.valid_from desc,c.id desc limit 1
  ) cr on true
), usable as (
  select * from enriched
  where home_club_key is not null and away_club_key is not null
    and season is not null and round_no is not null and stadium_capacity is not null
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
      partition by s.ticket_event_id,floor(extract(epoch from (e.kickoff_at-s.captured_at))/21600.0)::integer
      order by s.captured_at desc,s.id desc
    ) as rn
  from public.snapshots s
  join usable e on e.ticket_event_id=s.ticket_event_id
  where s.captured_at<=now()
    and s.captured_at<e.kickoff_at
    and s.captured_at>=e.kickoff_at-interval '168 hours'
), live_rows as (
  select c.ticket_event_id,c.requested_snapshot_id,c.requested_as_of_at,c.hours_to_kickoff,c.bucket_6h,to_jsonb(f) as features
  from candidates c
  cross join lateral public.get_live_trajectory_features_v1_1_asof(c.ticket_event_id,c.requested_as_of_at,c.stadium_capacity) f
  where c.rn=1
    and c.hours_to_kickoff>72 and c.hours_to_kickoff<=168
    and f.point_in_time_validated and f.snapshot_id is not null
), used_events as (
  select distinct ticket_event_id from live_rows
), event_payload as (
  select coalesce(jsonb_agg(jsonb_build_object(
    'ticket_event_id',u.ticket_event_id,'club_slug',u.club_slug,'home_team',u.home_team,'away_team',u.away_team,
    'competition',u.competition,'canonical_competition',u.canonical_competition,'kickoff_at',u.kickoff_at,
    'home_club_key',u.home_club_key,'away_club_key',u.away_club_key,'sporting_season',u.sporting_season,
    'season',u.season,'round_no',u.round_no,'stadium_capacity',u.stadium_capacity,
    'capacity_source_name',u.capacity_source_name,'capacity_source_url',u.capacity_source_url,
    'capacity_verification_status',u.capacity_verification_status
  ) order by u.kickoff_at,u.ticket_event_id),'[]'::jsonb) as rows
  from usable u join used_events x on x.ticket_event_id=u.ticket_event_id
), live_payload as (
  select coalesce(jsonb_agg(to_jsonb(l) order by l.ticket_event_id,l.requested_as_of_at),'[]'::jsonb) as rows
  from live_rows l
)
select jsonb_build_object(
  'version','p7-long168-prospective-inputs-v1',
  'generated_at',now(),
  'sampling',jsonb_build_object(
    'window_hours',168,
    'lower_exclusive_hours',72,
    'cadence_hours',6,
    'rule','prediction run itself and selected snapshot must both be inside >72h and <=168h before kickoff; latest snapshot in each event x 6h bucket',
    'pit_feature_function','get_live_trajectory_features_v1_1_asof'
  ),
  'eventCount',(select count(*) from used_events),
  'liveRowCount',(select count(*) from live_rows),
  'events',(select rows from event_payload),
  'liveRows',(select rows from live_payload),
  'targetValuesIncluded',false,
  'targetValuesUsed',false,
  'productionChange',false
);
$function$;

revoke all on function public.export_p7_long168_prospective_inputs_v1() from public,anon,authenticated;
grant execute on function public.export_p7_long168_prospective_inputs_v1() to service_role;
