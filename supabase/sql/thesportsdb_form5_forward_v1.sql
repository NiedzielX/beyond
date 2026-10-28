-- TheSportsDB form5 forward-only context v1.
--
-- Purpose:
-- - replace sparse manual `sport.form5` observations with an automated forward-only
--   research signal for future Ekstraklasa events;
-- - preserve PIT lineage through the provider row `fetched_at` timestamp;
-- - never mutate/backfill immutable historical event_context_snapshots_v1 rows;
-- - keep production P50 and live_adjustment unchanged.

create or replace function public.refresh_thesportsdb_form5_context_v1()
returns integer
language plpgsql
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_inserted integer := 0;
begin
  with targets as (
    select
      e.id as ticket_event_id,
      e.home_team,
      e.away_team,
      e.kickoff_at
    from public.ticket_events e
    where e.kickoff_at >= now()
      and e.kickoff_at < now() + interval '30 days'
      and public.match_competition_key_v1(e.competition) = 'ekstraklasa'
  ), ranked_matches as (
    select
      t.ticket_event_id,
      t.home_team as target_home_team,
      t.away_team as target_away_team,
      m.source_event_id,
      m.round_number,
      m.event_date,
      m.home_team,
      m.away_team,
      m.home_score,
      m.away_score,
      m.fetched_at,
      case
        when public.sporting_canonical_team_v1(m.home_team) = public.sporting_canonical_team_v1(t.home_team)
          then case when m.home_score > m.away_score then 3 when m.home_score = m.away_score then 1 else 0 end
        else case when m.away_score > m.home_score then 3 when m.away_score = m.home_score then 1 else 0 end
      end as points,
      case
        when public.sporting_canonical_team_v1(m.home_team) = public.sporting_canonical_team_v1(t.home_team)
          then m.home_score - m.away_score
        else m.away_score - m.home_score
      end as goal_difference,
      row_number() over (
        partition by t.ticket_event_id
        order by m.event_date desc, m.round_number desc, m.source_event_id desc
      ) as rn
    from targets t
    join public.sporting_league_matches_shadow m
      on m.league_id = '4422'
     and m.season = '2026-2027'
     and m.completed = true
     and m.event_date < (t.kickoff_at at time zone 'Europe/Warsaw')::date
     and m.fetched_at <= now()
     and public.sporting_canonical_team_v1(t.home_team) in (
       public.sporting_canonical_team_v1(m.home_team),
       public.sporting_canonical_team_v1(m.away_team)
     )
  ), last_five as (
    select *
    from ranked_matches
    where rn <= 5
  ), aggregated as (
    select
      ticket_event_id,
      max(target_home_team) as target_home_team,
      max(target_away_team) as target_away_team,
      count(*)::integer as match_count,
      sum(points)::integer as form5_points,
      sum(goal_difference)::integer as form5_goal_difference,
      max(fetched_at) as latest_source_fetch,
      max(event_date) as latest_match_date,
      jsonb_agg(
        jsonb_build_object(
          'source_event_id', source_event_id,
          'round_number', round_number,
          'event_date', event_date,
          'home_team', home_team,
          'away_team', away_team,
          'home_score', home_score,
          'away_score', away_score,
          'points_for_target_home_team', points,
          'goal_difference_for_target_home_team', goal_difference,
          'fetched_at', fetched_at
        ) order by rn
      ) as source_matches
    from last_five
    group by ticket_event_id
    having count(*) = 5
  )
  insert into public.event_context_observations(
    ticket_event_id,
    feature_key,
    observed_at,
    numeric_value,
    text_value,
    normalized_score,
    source_name,
    source_url,
    source_observed_at,
    confidence,
    source_record_key,
    metadata
  )
  select
    a.ticket_event_id,
    'sport.form5',
    a.latest_source_fetch,
    a.form5_points,
    format(
      'Recent league form: %s points from the last 5 completed matches; goal difference %+s.',
      a.form5_points,
      a.form5_goal_difference
    ),
    round(a.form5_points::numeric / 15.0, 4),
    'TheSportsDB v1 shadow',
    null,
    a.latest_source_fetch,
    0.7500,
    format(
      'thesportsdb:form5:v01:event:%s:%s',
      a.ticket_event_id,
      to_char(a.latest_source_fetch at time zone 'UTC','YYYYMMDD"T"HH24MISS')
    ),
    jsonb_build_object(
      'signal_version','v1',
      'signal_type','home_team_recent_league_form_last5',
      'target_home_team',a.target_home_team,
      'target_away_team',a.target_away_team,
      'match_count',a.match_count,
      'points_last5',a.form5_points,
      'goal_difference_last5',a.form5_goal_difference,
      'latest_match_date',a.latest_match_date,
      'latest_source_fetch',a.latest_source_fetch,
      'source_matches',a.source_matches,
      'source_tier','free_v1_shadow_not_canonical',
      'leakage_rule','only completed league matches with event_date before target local date and provider fetched_at at/before observation time',
      'historical_snapshot_backfill',false,
      'scoring_status','prospective_raw_form_not_model_active',
      'production_impact','none_context_research_only'
    )
  from aggregated a
  on conflict (ticket_event_id,feature_key,source_name,source_record_key) do nothing;

  get diagnostics v_inserted = row_count;
  return v_inserted;
end;
$function$;

revoke all on function public.refresh_thesportsdb_form5_context_v1() from public;
revoke all on function public.refresh_thesportsdb_form5_context_v1() from anon;
revoke all on function public.refresh_thesportsdb_form5_context_v1() from authenticated;
grant execute on function public.refresh_thesportsdb_form5_context_v1() to service_role;

-- Keep form5 generation coupled to the same successful provider-ingest transaction
-- that already refreshes TheSportsDB match-stakes research state.
create or replace function public.process_thesportsdb_round_responses_v1()
returns integer
language plpgsql
set search_path to 'public', 'net', 'pg_temp'
as $function$
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
      set status='error',processed_at=now(),error_text=coalesce(r.error_msg,format('HTTP %s',r.status_code))
      where request_id=r.request_id;
      continue;
    end if;

    begin
      for ev in select value from jsonb_array_elements((r.content::jsonb)->'events')
      loop
        insert into public.sporting_league_matches_shadow(
          source_event_id,league_id,season,round_number,event_date,home_team,away_team,
          home_score,away_score,match_status,completed,fetched_at,metadata
        ) values (
          ev->>'idEvent','4422','2026-2027',coalesce(nullif(ev->>'intRound','')::int,r.round_number),
          nullif(ev->>'dateEvent','')::date,ev->>'strHomeTeam',ev->>'strAwayTeam',
          nullif(ev->>'intHomeScore','')::int,nullif(ev->>'intAwayScore','')::int,ev->>'strStatus',
          (ev->>'strStatus'='FT'),now(),
          jsonb_build_object('id_api_football',ev->>'idAPIfootball','postponed',ev->>'strPostponed','locked',ev->>'strLocked')
        )
        on conflict (source_event_id) do update set
          round_number=excluded.round_number,event_date=excluded.event_date,home_team=excluded.home_team,away_team=excluded.away_team,
          home_score=excluded.home_score,away_score=excluded.away_score,match_status=excluded.match_status,
          completed=excluded.completed,fetched_at=excluded.fetched_at,metadata=excluded.metadata;
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
    perform public.refresh_thesportsdb_form5_context_v1();
  end if;

  return v_processed;
end;
$function$;

update public.context_feature_definitions
set primary_source='TheSportsDB v1 shadow (forward-only research)',
    collection_status='active_automated',
    collection_note='Forward-only automated last-5 league points are materialized from TheSportsDB shadow rows using fetched_at as known-at lineage. Existing immutable historical T-24 snapshots are never backfilled. This remains research-only until prospective MAE evidence exists.',
    updated_at=now()
where feature_key='sport.form5';

-- Seed only current/future observations. The function itself only targets future events.
select public.refresh_thesportsdb_form5_context_v1();
