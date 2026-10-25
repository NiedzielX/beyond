-- Make tracked-but-empty future events visible as an ingestion warning.

create or replace function private.refresh_dashboard_ticketing_ingestion_status_v1()
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $f$
declare v_count integer;
begin
 truncate public.dashboard_ticketing_ingestion_status_v1;
 insert into public.dashboard_ticketing_ingestion_status_v1(
   record_key,record_type,club_slug,club_name,external_event_id,label,candidate_kind,ingestion_status,kickoff_at,
   ticket_event_id,snapshot_count,first_snapshot_at,last_snapshot_at,raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,
   source_url,mapping_source,issue_reason,first_seen_at,last_seen_at,refreshed_at
 )
 with ss as (
   select ticket_event_id,count(*)::int snapshot_count,min(captured_at) first_snapshot_at,max(captured_at) last_snapshot_at
   from public.snapshots where ticket_event_id is not null group by ticket_event_id
 ), rs as (
   select club_slug,external_event_id,count(*)::int raw_snapshot_count,min(captured_at) first_raw_snapshot_at,max(captured_at) last_raw_snapshot_at
   from private.roboticket_candidate_snapshots_v1 group by club_slug,external_event_id
 ), tracked as (
   select
     'event:'||e.id,'tracked',e.club_slug,c.club_name,e.external_event_id,e.home_team||' – '||e.away_team,'match',
     case
       when e.kickoff_at<now() then 'COMPLETED_TRACKED'
       when coalesce(ss.snapshot_count,0)=0 then 'TRACKED_NO_SNAPSHOT'
       else 'TRACKED'
     end,
     e.kickoff_at,e.id,coalesce(ss.snapshot_count,0),ss.first_snapshot_at,ss.last_snapshot_at,
     0,null::timestamptz,null::timestamptz,e.source_url,e.mapping_source,
     case when e.kickoff_at>=now() and coalesce(ss.snapshot_count,0)=0
       then 'ticket event exists but no inventory snapshot has been collected yet'
       else null end,
     e.created_at,e.updated_at
   from public.ticket_events e
   left join public.roboticket_clubs c on c.club_slug=e.club_slug
   left join ss on ss.ticket_event_id=e.id
   where e.provider='roboticket'
 ), cb as (
   select rc.*,c.club_name,te.id ticket_event_id,te.kickoff_at tracked_kickoff,te.mapping_source,
     vs.kickoff_at verified_kickoff,coalesce(rs.raw_snapshot_count,0) raw_snapshot_count,rs.first_raw_snapshot_at,rs.last_raw_snapshot_at,
     concat_ws(' ',rc.label,rc.metadata->>'anchor_aria_label',rc.metadata->>'direct_page_h1') candidate_text
   from public.roboticket_event_candidates rc
   left join public.roboticket_clubs c on c.club_slug=rc.club_slug
   left join public.ticket_events te on te.provider='roboticket' and te.club_slug=rc.club_slug and te.external_event_id=rc.external_event_id
   left join private.roboticket_verified_schedule_v1 vs on vs.club_slug=rc.club_slug and vs.external_event_id=rc.external_event_id
   left join rs on rs.club_slug=rc.club_slug and rs.external_event_id=rc.external_event_id
 ), cand as (
   select
     'candidate:'||club_slug||':'||external_event_id,'candidate',club_slug,club_name,external_event_id,label,
     coalesce(metadata->>'candidate_kind','unknown'),
     case
       when ticket_event_id is not null then 'TRACKED'
       when coalesce(metadata->>'candidate_kind','')='non_match' then 'NON_MATCH_EXCLUDED'
       when coalesce(metadata->>'candidate_kind','')<>'match' then 'UNKNOWN_EXCLUDED'
       when not private.roboticket_candidate_is_known_football_match_v1(club_slug,external_event_id,candidate_text) then 'NON_FOOTBALL_EXCLUDED'
       when verified_kickoff is not null then 'READY_TO_PROMOTE'
       when raw_snapshot_count>0 then 'BUFFERING_AWAITING_KICKOFF'
       else 'MATCH_DISCOVERED_NO_BUFFER'
     end,
     coalesce(tracked_kickoff,verified_kickoff),ticket_event_id,0,null::timestamptz,null::timestamptz,
     raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,
     coalesce((select source_url from private.roboticket_verified_schedule_v1 v where v.club_slug=cb.club_slug and v.external_event_id=cb.external_event_id),source_url),
     mapping_source,
     case
       when ticket_event_id is not null then null
       when coalesce(metadata->>'candidate_kind','')='non_match' then 'non-match product intentionally excluded'
       when coalesce(metadata->>'candidate_kind','')<>'match' then 'candidate identity insufficient'
       when not private.roboticket_candidate_is_known_football_match_v1(club_slug,external_event_id,candidate_text) then 'not a pair of known football clubs in the model universe'
       when verified_kickoff is null and raw_snapshot_count>0 then 'exact kickoff pending; raw curve protected'
       when verified_kickoff is null then 'exact kickoff pending and candidate buffer has no snapshot yet'
       else 'verified schedule exists; promotion pending'
     end,
     first_seen_at,last_seen_at
   from cb
 )
 select tracked.*,clock_timestamp() from tracked
 union all
 select cand.*,clock_timestamp() from cand where ticket_event_id is null;
 get diagnostics v_count=row_count;
 return jsonb_build_object('version','dashboard-ticketing-ingestion-status-v1.1','row_count',v_count,'refreshed_at',clock_timestamp());
end;
$f$;

select private.refresh_dashboard_ticketing_ingestion_status_v1();
