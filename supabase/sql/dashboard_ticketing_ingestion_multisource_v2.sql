-- Multi-source ticketing ingestion dashboard v2.
-- Keeps the existing panel-facing schema/status vocabulary and unions
-- Roboticket + Stellis coverage. This avoids a frontend contract change.

create or replace function private.refresh_dashboard_ticketing_ingestion_status_v1()
returns jsonb
language plpgsql
security definer
set search_path to 'public','private'
as $function$
declare
  v_count integer;
begin
  truncate public.dashboard_ticketing_ingestion_status_v1;

  insert into public.dashboard_ticketing_ingestion_status_v1(
    record_key,record_type,club_slug,club_name,external_event_id,label,candidate_kind,
    ingestion_status,kickoff_at,ticket_event_id,snapshot_count,first_snapshot_at,last_snapshot_at,
    raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,source_url,mapping_source,
    issue_reason,first_seen_at,last_seen_at,refreshed_at
  )
  with
  ss as (
    select ticket_event_id,count(*)::int snapshot_count,min(captured_at) first_snapshot_at,max(captured_at) last_snapshot_at
    from public.snapshots where ticket_event_id is not null group by ticket_event_id
  ),
  robot_raw as (
    select club_slug,external_event_id,count(*)::int raw_snapshot_count,min(captured_at) first_raw_snapshot_at,max(captured_at) last_raw_snapshot_at
    from private.roboticket_candidate_snapshots_v1 group by club_slug,external_event_id
  ),
  stellis_raw as (
    select club_slug,external_event_id,
           count(*) filter (where availability_exposed and available_total is not null)::int raw_snapshot_count,
           min(captured_at) filter (where availability_exposed and available_total is not null) first_raw_snapshot_at,
           max(captured_at) filter (where availability_exposed and available_total is not null) last_raw_snapshot_at
    from private.stellis_raw_observations_v1
    group by club_slug,external_event_id
  ),
  tracked as (
    select
      'event:'||e.id as record_key,'tracked'::text as record_type,e.club_slug,
      coalesce(rc.club_name,sc.club_name,e.club_slug) as club_name,e.external_event_id,
      e.home_team||' – '||e.away_team as label,'match'::text as candidate_kind,
      case when e.kickoff_at<now() then 'COMPLETED_TRACKED'
           when coalesce(ss.snapshot_count,0)=0 then 'TRACKED_NO_SNAPSHOT'
           else 'TRACKED' end::text as ingestion_status,
      e.kickoff_at,e.id as ticket_event_id,coalesce(ss.snapshot_count,0) as snapshot_count,
      ss.first_snapshot_at,ss.last_snapshot_at,0::int as raw_snapshot_count,
      null::timestamptz as first_raw_snapshot_at,null::timestamptz as last_raw_snapshot_at,
      e.source_url,e.mapping_source,
      case when e.kickoff_at>=now() and coalesce(ss.snapshot_count,0)=0
           then 'ticket event exists but no inventory snapshot has been collected yet' else null end as issue_reason,
      e.created_at as first_seen_at,e.updated_at as last_seen_at
    from public.ticket_events e
    left join public.roboticket_clubs rc on rc.club_slug=e.club_slug
    left join public.stellis_clubs_v1 sc on sc.club_slug=e.club_slug
    left join ss on ss.ticket_event_id=e.id
    where e.provider in ('roboticket','stellis')
  ),
  robot_cb as (
    select rc.*,c.club_name,te.id ticket_event_id,te.kickoff_at tracked_kickoff,te.mapping_source,
           vs.kickoff_at verified_kickoff,coalesce(rr.raw_snapshot_count,0) raw_snapshot_count,
           rr.first_raw_snapshot_at,rr.last_raw_snapshot_at,
           concat_ws(' ',rc.label,rc.metadata->>'anchor_aria_label',rc.metadata->>'direct_page_h1') candidate_text
    from public.roboticket_event_candidates rc
    left join public.roboticket_clubs c on c.club_slug=rc.club_slug
    left join public.ticket_events te on te.provider='roboticket' and te.club_slug=rc.club_slug and te.external_event_id=rc.external_event_id
    left join private.roboticket_verified_schedule_v1 vs on vs.club_slug=rc.club_slug and vs.external_event_id=rc.external_event_id
    left join robot_raw rr on rr.club_slug=rc.club_slug and rr.external_event_id=rc.external_event_id
  ),
  robot_candidates as (
    select
      'candidate:roboticket:'||club_slug||':'||external_event_id as record_key,
      'candidate'::text as record_type,club_slug,club_name,external_event_id,label,
      coalesce(metadata->>'candidate_kind','unknown') as candidate_kind,
      case when ticket_event_id is not null then 'TRACKED'
           when coalesce(metadata->>'candidate_kind','')='non_match' then 'NON_MATCH_EXCLUDED'
           when coalesce(metadata->>'candidate_kind','')<>'match' then 'UNKNOWN_EXCLUDED'
           when not private.roboticket_candidate_is_known_football_match_v1(club_slug,external_event_id,candidate_text) then 'NON_FOOTBALL_EXCLUDED'
           when verified_kickoff is not null then 'READY_TO_PROMOTE'
           when raw_snapshot_count>0 then 'BUFFERING_AWAITING_KICKOFF'
           else 'MATCH_DISCOVERED_NO_BUFFER' end::text as ingestion_status,
      coalesce(tracked_kickoff,verified_kickoff) as kickoff_at,ticket_event_id,
      0::int as snapshot_count,null::timestamptz as first_snapshot_at,null::timestamptz as last_snapshot_at,
      raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,
      coalesce((select source_url from private.roboticket_verified_schedule_v1 v where v.club_slug=robot_cb.club_slug and v.external_event_id=robot_cb.external_event_id),source_url) as source_url,
      mapping_source,
      case when ticket_event_id is not null then null
           when coalesce(metadata->>'candidate_kind','')='non_match' then 'non-match product intentionally excluded'
           when coalesce(metadata->>'candidate_kind','')<>'match' then 'candidate identity insufficient'
           when not private.roboticket_candidate_is_known_football_match_v1(club_slug,external_event_id,candidate_text) then 'not a pair of known football clubs in the model universe'
           when verified_kickoff is null and raw_snapshot_count>0 then 'exact kickoff pending; raw curve protected'
           when verified_kickoff is null then 'exact kickoff pending and candidate buffer has no snapshot yet'
           else 'verified schedule exists; promotion pending' end as issue_reason,
      first_seen_at,last_seen_at
    from robot_cb
  ),
  stellis_cb as (
    select c.*,sc.club_name,te.id ticket_event_id,te.mapping_source,
           coalesce(sr.raw_snapshot_count,0) raw_snapshot_count,sr.first_raw_snapshot_at,sr.last_raw_snapshot_at
    from public.stellis_event_candidates_v1 c
    left join public.stellis_clubs_v1 sc on sc.club_slug=c.club_slug
    left join public.ticket_events te on te.provider='stellis' and te.club_slug=c.club_slug and te.external_event_id=c.external_event_id
    left join stellis_raw sr on sr.club_slug=c.club_slug and sr.external_event_id=c.external_event_id
  ),
  stellis_candidates as (
    select
      'candidate:stellis:'||club_slug||':'||external_event_id as record_key,
      'candidate'::text as record_type,club_slug,club_name,external_event_id,event_name as label,
      case when home_club_key is not null and away_club_key is not null and home_club_key=club_slug then 'match' else 'unknown' end::text as candidate_kind,
      case when ticket_event_id is not null then 'TRACKED'
           when status='non_league' then 'NON_MATCH_EXCLUDED'
           when status='invalid' then 'UNKNOWN_EXCLUDED'
           when home_club_key is null or away_club_key is null or home_club_key<>club_slug then 'UNKNOWN_EXCLUDED'
           when status='collecting' then 'READY_TO_PROMOTE'
           when availability_exposed and raw_snapshot_count>0 then 'BUFFERING_AWAITING_KICKOFF'
           else 'MATCH_DISCOVERED_NO_BUFFER' end::text as ingestion_status,
      kickoff_at,ticket_event_id,0::int as snapshot_count,
      null::timestamptz as first_snapshot_at,null::timestamptz as last_snapshot_at,
      raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,source_url,mapping_source,
      case when ticket_event_id is not null then null
           when status='non_league' then 'non-league/cup event intentionally excluded'
           when status='invalid' then 'Stellis event identity is not eligible for football-match ingestion'
           when home_club_key is null or away_club_key is null or home_club_key<>club_slug then 'home/away football identity not safely resolved'
           when status='hidden_availability' then 'match discovered but source does not expose aggregate availability'
           when status='awaiting_fixture' and raw_snapshot_count>0 then 'league fixture confirmation pending; raw curve protected'
           when availability_exposed and raw_snapshot_count>0 then 'league fixture confirmation pending; raw curve protected'
           else 'match discovered but no model-safe inventory snapshot is available yet' end as issue_reason,
      first_seen_at,last_seen_at
    from stellis_cb
  )
  select tracked.*,clock_timestamp() from tracked
  union all select robot_candidates.*,clock_timestamp() from robot_candidates where ticket_event_id is null
  union all select stellis_candidates.*,clock_timestamp() from stellis_candidates where ticket_event_id is null;

  get diagnostics v_count=row_count;
  return jsonb_build_object('version','dashboard-ticketing-ingestion-status-v2','row_count',v_count,'refreshed_at',clock_timestamp());
end;
$function$;

select private.refresh_dashboard_ticketing_ingestion_status_v1();
