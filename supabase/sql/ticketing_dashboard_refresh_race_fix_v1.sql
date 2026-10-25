-- Dashboard refresh race fix v1.
-- A legacy caller of refresh_dashboard_ticketing_ingestion_status_v1() could
-- truncate the shared table and temporarily remove SCHEDULE_GAP rows until the
-- next v2 watchdog refresh. Preserve the original multisource refresh as a base
-- function and make v1 itself append schedule gaps, so every caller is safe.

do $$
begin
  if not exists (
    select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='private' and p.proname='refresh_dashboard_ticketing_ingestion_base_v1' and p.prokind='f'
  ) then
    alter function private.refresh_dashboard_ticketing_ingestion_status_v1()
      rename to refresh_dashboard_ticketing_ingestion_base_v1;
  end if;
end $$;

create or replace function private.refresh_dashboard_ticketing_ingestion_status_v1()
returns jsonb
language plpgsql
security definer
set search_path to 'public','private'
as $function$
declare
  v_base jsonb;
  v_inserted integer := 0;
  v_total integer := 0;
begin
  v_base := private.refresh_dashboard_ticketing_ingestion_base_v1();

  insert into public.dashboard_ticketing_ingestion_status_v1(
    record_key,record_type,club_slug,club_name,external_event_id,label,candidate_kind,
    ingestion_status,kickoff_at,ticket_event_id,snapshot_count,first_snapshot_at,last_snapshot_at,
    raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,source_url,mapping_source,
    issue_reason,first_seen_at,last_seen_at,refreshed_at
  )
  select
    'schedule:'||f.source_event_id,
    'schedule_gap',
    coalesce(f.source_club_slug,f.home_club_key),
    coalesce(f.source_club_name,f.home_team),
    f.source_event_id,
    f.home_team||' – '||f.away_team,
    'match',
    'SCHEDULE_GAP',
    null,
    null,
    0,null,null,0,null,null,
    f.source_url,
    'schedule-watchdog:'||coalesce(f.source_family,'unmapped'),
    case
      when f.source_family is null then 'upcoming league home fixture has no onboarded ticketing source; fixture date '||f.event_date::text
      else 'upcoming league home fixture has no canonical ticket event or protected candidate yet; fixture date '||f.event_date::text||'; source='||f.source_family
    end,
    f.fetched_at,f.fetched_at,clock_timestamp()
  from public.dashboard_ticketing_fixture_coverage_v1 f
  where f.coverage_status in ('SCHEDULE_GAP','SOURCE_NOT_ONBOARDED')
  on conflict(record_key) do nothing;

  get diagnostics v_inserted=row_count;
  select count(*)::int into v_total from public.dashboard_ticketing_ingestion_status_v1;

  return jsonb_build_object(
    'version','dashboard-ticketing-ingestion-status-v2.2',
    'base_refresh',v_base,
    'schedule_gap_rows',v_inserted,
    'row_count',v_total,
    'refreshed_at',clock_timestamp()
  );
end;
$function$;

-- Keep v2 as a compatibility alias; it no longer needs to append gaps itself.
create or replace function private.refresh_dashboard_ticketing_ingestion_status_v2()
returns jsonb
language sql
security definer
set search_path to 'public','private'
as $function$
  select private.refresh_dashboard_ticketing_ingestion_status_v1();
$function$;

select private.refresh_dashboard_ticketing_ingestion_status_v1();
