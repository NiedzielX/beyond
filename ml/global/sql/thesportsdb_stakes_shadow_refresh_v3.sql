-- TheSportsDB stakes shadow v3.
-- Do not create a new shadow observation on every 5-minute processor tick.
-- Refresh only after at least one new HTTP response was successfully processed.

create or replace function public.process_thesportsdb_round_responses_v1()
returns integer
language plpgsql
security invoker
set search_path=public,net,pg_temp
as $$
declare
  r record;
  ev jsonb;
  v_processed integer := 0;
begin
  for r in
    select q.request_id,q.round_number,h.status_code,h.content,h.timed_out,h.error_msg
    from public.sporting_round_fetch_requests q
    join net._http_response h on h.id=q.request_id
    where q.status='queued'
    order by q.requested_at
  loop
    if r.status_code<>200 or coalesce(r.timed_out,false) or r.error_msg is not null then
      update public.sporting_round_fetch_requests
      set status='error',
          processed_at=now(),
          error_text=coalesce(r.error_msg,format('HTTP %s',r.status_code))
      where request_id=r.request_id;
      continue;
    end if;

    begin
      for ev in select value from jsonb_array_elements((r.content::jsonb)->'events')
      loop
        insert into public.sporting_league_matches_shadow(
          source_event_id,league_id,season,round_number,event_date,
          home_team,away_team,home_score,away_score,match_status,completed,
          fetched_at,metadata
        ) values (
          ev->>'idEvent',
          '4422',
          '2026-2027',
          coalesce(nullif(ev->>'intRound','')::int,r.round_number),
          nullif(ev->>'dateEvent','')::date,
          ev->>'strHomeTeam',
          ev->>'strAwayTeam',
          nullif(ev->>'intHomeScore','')::int,
          nullif(ev->>'intAwayScore','')::int,
          ev->>'strStatus',
          (ev->>'strStatus'='FT'),
          now(),
          jsonb_build_object(
            'id_api_football',ev->>'idAPIfootball',
            'postponed',ev->>'strPostponed',
            'locked',ev->>'strLocked'
          )
        )
        on conflict (source_event_id) do update set
          round_number=excluded.round_number,
          event_date=excluded.event_date,
          home_team=excluded.home_team,
          away_team=excluded.away_team,
          home_score=excluded.home_score,
          away_score=excluded.away_score,
          match_status=excluded.match_status,
          completed=excluded.completed,
          fetched_at=excluded.fetched_at,
          metadata=excluded.metadata;
      end loop;

      update public.sporting_round_fetch_requests
      set status='processed',processed_at=now(),error_text=null
      where request_id=r.request_id;
      v_processed := v_processed + 1;
    exception when others then
      update public.sporting_round_fetch_requests
      set status='error',processed_at=now(),error_text=sqlerrm
      where request_id=r.request_id;
    end;
  end loop;

  if v_processed > 0 then
    perform public.refresh_thesportsdb_stakes_shadow_v1();
  end if;

  return v_processed;
end;
$$;

revoke all on function public.process_thesportsdb_round_responses_v1() from public, anon, authenticated;
grant execute on function public.process_thesportsdb_round_responses_v1() to service_role;
