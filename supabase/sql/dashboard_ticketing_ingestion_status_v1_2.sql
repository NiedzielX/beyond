-- Dashboard ticketing ingestion monitor v1.2
-- Extends the existing operational monitor from RoboTicket to both canonical providers:
-- RoboTicket and Stellis. No model behavior changes.

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
  with snapshot_stats as (
    select ticket_event_id,count(*)::int as snapshot_count,min(captured_at) as first_snapshot_at,max(captured_at) as last_snapshot_at
    from public.snapshots
    where ticket_event_id is not null
    group by ticket_event_id
  ),
  robot_raw as (
    select club_slug,external_event_id,count(*)::int as raw_snapshot_count,min(captured_at) as first_raw_snapshot_at,max(captured_at) as last_raw_snapshot_at
    from private.roboticket_candidate_snapshots_v1
    group by club_slug,external_event_id
  ),
  stellis_raw as (
    select club_slug,external_event_id,count(*)::int as raw_snapshot_count,min(captured_at) as first_raw_snapshot_at,max(captured_at) as last_raw_snapshot_at
    from private.stellis_raw_observations_v1
    group by club_slug,external_event_id
  ),
  tracked as (
    select
      'event:'||e.id as record_key,
      'tracked'::text as record_type,
      e.club_slug,
      coalesce(rc.club_name,sc.club_name,e.home_team) as club_name,
      e.external_event_id,
      (e.home_team||' – '||e.away_team)::text as label,
      'match'::text as candidate_kind,
      case
        when e.kickoff_at < now() then 'COMPLETED_TRACKED'
        when coalesce(ss.snapshot_count,0)=0 then 'TRACKED_NO_SNAPSHOT'
        else 'TRACKED'
      end::text as ingestion_status,
      e.kickoff_at,
      e.id as ticket_event_id,
      coalesce(ss.snapshot_count,0) as snapshot_count,
      ss.first_snapshot_at,
      ss.last_snapshot_at,
      0::int as raw_snapshot_count,
      null::timestamptz as first_raw_snapshot_at,
      null::timestamptz as last_raw_snapshot_at,
      e.source_url,
      e.mapping_source,
      case
        when e.kickoff_at>=now() and coalesce(ss.snapshot_count,0)=0
          then 'ticket event exists but no inventory snapshot has been collected yet'
        else null
      end::text as issue_reason,
      e.created_at as first_seen_at,
      e.updated_at as last_seen_at
    from public.ticket_events e
    left join public.roboticket_clubs rc on e.provider='roboticket' and rc.club_slug=e.club_slug
    left join public.stellis_clubs_v1 sc on e.provider='stellis' and sc.club_slug=e.club_slug
    left join snapshot_stats ss on ss.ticket_event_id=e.id
    where e.provider in ('roboticket','stellis')
  ),
  robot_base as (
    select
      rcand.*,
      rc.club_name,
      te.id as ticket_event_id,
      te.kickoff_at as tracked_kickoff,
      te.mapping_source,
      vs.kickoff_at as verified_kickoff,
      coalesce(rr.raw_snapshot_count,0) as raw_snapshot_count,
      rr.first_raw_snapshot_at,
      rr.last_raw_snapshot_at,
      concat_ws(' ',rcand.label,rcand.metadata->>'anchor_aria_label',rcand.metadata->>'direct_page_h1') as candidate_text
    from public.roboticket_event_candidates rcand
    left join public.roboticket_clubs rc on rc.club_slug=rcand.club_slug
    left join public.ticket_events te
      on te.provider='roboticket' and te.club_slug=rcand.club_slug and te.external_event_id=rcand.external_event_id
    left join private.roboticket_verified_schedule_v1 vs
      on vs.club_slug=rcand.club_slug and vs.external_event_id=rcand.external_event_id
    left join robot_raw rr
      on rr.club_slug=rcand.club_slug and rr.external_event_id=rcand.external_event_id
  ),
  robot_candidates as (
    select
      'candidate:'||club_slug||':'||external_event_id as record_key,
      'candidate'::text as record_type,
      club_slug,club_name,external_event_id,label,
      coalesce(metadata->>'candidate_kind','unknown') as candidate_kind,
      case
        when ticket_event_id is not null then 'TRACKED'
        when coalesce(metadata->>'candidate_kind','')='non_match' then 'NON_MATCH_EXCLUDED'
        when coalesce(metadata->>'candidate_kind','')<>'match' then 'UNKNOWN_EXCLUDED'
        when not private.roboticket_candidate_is_known_football_match_v1(club_slug,external_event_id,candidate_text) then 'NON_FOOTBALL_EXCLUDED'
        when verified_kickoff is not null then 'READY_TO_PROMOTE'
        when raw_snapshot_count>0 then 'BUFFERING_AWAITING_KICKOFF'
        else 'MATCH_DISCOVERED_NO_BUFFER'
      end::text as ingestion_status,
      coalesce(tracked_kickoff,verified_kickoff) as kickoff_at,
      ticket_event_id,
      0::int as snapshot_count,null::timestamptz as first_snapshot_at,null::timestamptz as last_snapshot_at,
      raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,
      coalesce((select v.source_url from private.roboticket_verified_schedule_v1 v where v.club_slug=robot_base.club_slug and v.external_event_id=robot_base.external_event_id),source_url) as source_url,
      mapping_source,
      case
        when ticket_event_id is not null then null
        when coalesce(metadata->>'candidate_kind','')='non_match' then 'non-match product intentionally excluded'
        when coalesce(metadata->>'candidate_kind','')<>'match' then 'candidate identity insufficient'
        when not private.roboticket_candidate_is_known_football_match_v1(club_slug,external_event_id,candidate_text) then 'not a pair of known football clubs in the model universe'
        when verified_kickoff is null and raw_snapshot_count>0 then 'exact kickoff pending; raw curve protected'
        when verified_kickoff is null then 'exact kickoff pending and candidate buffer has no snapshot yet'
        else 'verified schedule exists; promotion pending'
      end::text as issue_reason,
      first_seen_at,last_seen_at
    from robot_base
  ),
  stellis_candidates as (
    select
      'stellis-candidate:'||c.club_slug||':'||c.external_event_id as record_key,
      'candidate'::text as record_type,
      c.club_slug,
      sc.club_name,
      c.external_event_id,
      c.event_name as label,
      'match'::text as candidate_kind,
      case
        when te.id is not null then 'TRACKED'
        when c.status='non_league' then 'NON_LEAGUE_EXCLUDED'
        when c.status='invalid' then 'UNKNOWN_EXCLUDED'
        when c.status='hidden_availability' then 'HIDDEN_AVAILABILITY'
        when c.status='awaiting_fixture' then 'BUFFERING_AWAITING_FIXTURE'
        when c.status='collecting' then 'READY_TO_PROMOTE'
        when c.status='discovered' and coalesce(sr.raw_snapshot_count,0)>0 then 'BUFFERING_AWAITING_FIXTURE'
        when c.status='discovered' then 'MATCH_DISCOVERED_NO_BUFFER'
        else 'UNKNOWN_EXCLUDED'
      end::text as ingestion_status,
      c.kickoff_at,
      te.id as ticket_event_id,
      coalesce(ss.snapshot_count,0) as snapshot_count,
      ss.first_snapshot_at,
      ss.last_snapshot_at,
      coalesce(sr.raw_snapshot_count,0) as raw_snapshot_count,
      sr.first_raw_snapshot_at,
      sr.last_raw_snapshot_at,
      c.source_url,
      coalesce(te.mapping_source,'stellis-candidate-v3') as mapping_source,
      case
        when te.id is not null then null
        when c.status='non_league' then 'explicit non-league product intentionally excluded'
        when c.status='invalid' then 'invalid or non-match Stellis product intentionally excluded'
        when c.status='hidden_availability' then 'source publishes the event but hides visible availability; sold-only evidence stays private'
        when c.status='awaiting_fixture' then 'visible raw curve protected; waiting for unique league fixture mapping before model-facing promotion'
        when c.status='collecting' then 'candidate marked collecting but canonical ticket-event promotion is still pending'
        when c.status='discovered' and coalesce(sr.raw_snapshot_count,0)>0 then 'visible raw curve protected; fixture verification/promotion pending'
        else 'event discovered but no protected raw observation exists yet'
      end::text as issue_reason,
      c.first_seen_at,
      c.last_seen_at
    from public.stellis_event_candidates_v1 c
    left join public.stellis_clubs_v1 sc on sc.club_slug=c.club_slug
    left join public.ticket_events te
      on te.provider='stellis' and te.club_slug=c.club_slug and te.external_event_id=c.external_event_id
    left join snapshot_stats ss on ss.ticket_event_id=te.id
    left join stellis_raw sr on sr.club_slug=c.club_slug and sr.external_event_id=c.external_event_id
  )
  select tracked.*,clock_timestamp() from tracked
  union all
  select robot_candidates.*,clock_timestamp() from robot_candidates where ticket_event_id is null
  union all
  select stellis_candidates.*,clock_timestamp() from stellis_candidates where ticket_event_id is null;

  get diagnostics v_count=row_count;
  return jsonb_build_object(
    'version','dashboard-ticketing-ingestion-status-v1.2',
    'row_count',v_count,
    'refreshed_at',clock_timestamp()
  );
end;
$function$;

select private.refresh_dashboard_ticketing_ingestion_status_v1();
