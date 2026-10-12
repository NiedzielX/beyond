-- Beyond Ticketing — Match Context base refresh v2.
-- Keeps timing and competition metadata current after schedule changes.
-- Competition stage remains explicitly unknown when ticket_events does not provide it.

create or replace function public.refresh_match_context_base_v2()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare
  v_count integer := 0;
  v_rows integer := 0;
begin
  insert into public.event_context_observations(
    ticket_event_id,feature_key,observed_at,numeric_value,text_value,normalized_score,
    source_name,source_observed_at,confidence,source_record_key,metadata
  )
  select e.id,'match.timing',now(),null,
    format('%s %s Europe/Warsaw',
      case extract(isodow from e.kickoff_at at time zone 'Europe/Warsaw')::int
        when 1 then 'poniedziałek' when 2 then 'wtorek' when 3 then 'środa'
        when 4 then 'czwartek' when 5 then 'piątek' when 6 then 'sobota'
        when 7 then 'niedziela' end,
      to_char(e.kickoff_at at time zone 'Europe/Warsaw','HH24:MI')
    ),
    null,'ticket_events',e.updated_at,1.0000,
    format('ticket-events:timing:v2:%s',e.id),
    jsonb_build_object(
      'kickoff_at',e.kickoff_at,'timezone','Europe/Warsaw',
      'weekday_iso',extract(isodow from e.kickoff_at at time zone 'Europe/Warsaw')::int,
      'local_hour',extract(hour from e.kickoff_at at time zone 'Europe/Warsaw')::int,
      'local_minute',extract(minute from e.kickoff_at at time zone 'Europe/Warsaw')::int,
      'source_updated_at',e.updated_at,
      'scoring_status','raw_context_not_model_active',
      'production_impact','none_context_research_only'
    )
  from public.ticket_events e
  where e.kickoff_at>=now()-interval '3 hours'
    and e.kickoff_at<now()+interval '120 days'
  on conflict (ticket_event_id,feature_key,source_name,source_record_key)
  do update set
    observed_at=excluded.observed_at,text_value=excluded.text_value,
    source_observed_at=excluded.source_observed_at,confidence=excluded.confidence,
    metadata=excluded.metadata;

  get diagnostics v_rows=row_count;
  v_count:=v_count+v_rows;

  insert into public.event_context_observations(
    ticket_event_id,feature_key,observed_at,numeric_value,text_value,normalized_score,
    source_name,source_observed_at,confidence,source_record_key,metadata
  )
  select e.id,'match.competition_stage',now(),null,
    e.competition || ' · etap nie jest dostępny w źródle wydarzenia',
    null,'ticket_events',e.updated_at,0.9500,
    format('ticket-events:competition-stage:v2:%s',e.id),
    jsonb_build_object(
      'competition',e.competition,
      'competition_key',public.match_competition_key_v1(e.competition),
      'stage',null,'stage_status','not_provided_by_event_source',
      'source_updated_at',e.updated_at,
      'scoring_status','raw_context_not_model_active',
      'production_impact','none_context_research_only'
    )
  from public.ticket_events e
  where e.kickoff_at>=now()-interval '3 hours'
    and e.kickoff_at<now()+interval '120 days'
  on conflict (ticket_event_id,feature_key,source_name,source_record_key)
  do update set
    observed_at=excluded.observed_at,text_value=excluded.text_value,
    source_observed_at=excluded.source_observed_at,confidence=excluded.confidence,
    metadata=excluded.metadata;

  get diagnostics v_rows=row_count;
  v_count:=v_count+v_rows;
  return v_count;
end;
$$;

revoke all on function public.refresh_match_context_base_v2() from public,anon,authenticated;
grant execute on function public.refresh_match_context_base_v2() to service_role;

update public.context_feature_definitions
set collection_status='active_automated',
    refresh_cadence='every 6h + on event metadata change',
    primary_source='ticket_events',
    collection_note=case feature_key
      when 'match.timing' then 'Kickoff day/time is refreshed automatically from ticket_events in Europe/Warsaw. Reschedules overwrite the stable v2 observation rather than leaving stale timing context.'
      when 'match.competition_stage' then 'Competition is refreshed automatically from ticket_events. Stage is kept explicitly unknown when the event source does not provide it; Beyond does not infer knockout/league stage from competition name alone.'
      else collection_note end,
    updated_at=now()
where feature_key in ('match.timing','match.competition_stage');

do $$
declare v_job bigint;
begin
  select jobid into v_job from cron.job where jobname='match_context_base_6h';
  if v_job is not null then perform cron.unschedule(v_job); end if;
end $$;

select cron.schedule(
  'match_context_base_6h','47 */6 * * *',
  $$select public.refresh_match_context_base_v2();$$
);

select public.refresh_match_context_base_v2();
