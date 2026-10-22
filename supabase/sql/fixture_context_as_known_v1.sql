-- Fixture Context As-Known v1
--
-- PIT-safe forward-only feature lookup for fixture spacing/density research.
-- Uses only the latest immutable schedule batch with observed_at <= forecast as_of_at.
-- No historical schedule backfill is permitted.
-- Production forecast behavior is unchanged.

begin;

create or replace function public.fixture_context_as_known_v1(
    p_home_team text,
    p_away_team text,
    p_event_date date,
    p_as_of_at timestamptz
)
returns jsonb
language plpgsql
stable
set search_path to 'public','private'
as $function$
declare
    v_batch_id bigint;
    v_batch_observed_at timestamptz;
    v_source_max_fetched_at timestamptz;
    v_home text;
    v_away text;
    v_target private.fixture_schedule_rows_v1%rowtype;
    v_target_count integer;
    v_prev private.fixture_schedule_rows_v1%rowtype;
    v_next private.fixture_schedule_rows_v1%rowtype;
    v_team_7 integer;
    v_team_14 integer;
    v_team_30 integer;
    v_home_7 integer;
    v_home_14 integer;
    v_home_30 integer;
begin
    if p_home_team is null or p_away_team is null or p_event_date is null or p_as_of_at is null then
        raise exception 'home_team, away_team, event_date and as_of_at are required';
    end if;

    if p_as_of_at > now() + interval '5 minutes' then
        raise exception 'as_of_at cannot be in the future';
    end if;

    v_home := public.sporting_canonical_team_v1(p_home_team);
    v_away := public.sporting_canonical_team_v1(p_away_team);

    select b.id, b.observed_at, b.source_max_fetched_at
    into v_batch_id, v_batch_observed_at, v_source_max_fetched_at
    from private.fixture_schedule_batches_v1 b
    where b.observed_at <= p_as_of_at
    order by b.observed_at desc, b.id desc
    limit 1;

    if v_batch_id is null then
        return jsonb_build_object(
            'version','fixture-context-as-known-v1',
            'status','NO_SCHEDULE_STATE_AS_OF',
            'as_of_at',p_as_of_at,
            'evidence_class','forward_schedule_as_known',
            'production_change',false
        );
    end if;

    select count(*)::integer
    into v_target_count
    from private.fixture_schedule_rows_v1 r
    where r.batch_id = v_batch_id
      and r.event_date = p_event_date
      and r.home_team_canonical = v_home
      and r.away_team_canonical = v_away;

    if v_target_count = 0 then
        return jsonb_build_object(
            'version','fixture-context-as-known-v1',
            'status','TARGET_NOT_IN_SCHEDULE_STATE',
            'as_of_at',p_as_of_at,
            'schedule_batch_id',v_batch_id,
            'schedule_observed_at',v_batch_observed_at,
            'home_team_canonical',v_home,
            'away_team_canonical',v_away,
            'event_date',p_event_date,
            'evidence_class','forward_schedule_as_known',
            'production_change',false
        );
    end if;

    if v_target_count <> 1 then
        return jsonb_build_object(
            'version','fixture-context-as-known-v1',
            'status','AMBIGUOUS_TARGET',
            'target_count',v_target_count,
            'as_of_at',p_as_of_at,
            'schedule_batch_id',v_batch_id,
            'schedule_observed_at',v_batch_observed_at,
            'home_team_canonical',v_home,
            'away_team_canonical',v_away,
            'event_date',p_event_date,
            'evidence_class','forward_schedule_as_known',
            'production_change',false
        );
    end if;

    select r.*
    into v_target
    from private.fixture_schedule_rows_v1 r
    where r.batch_id = v_batch_id
      and r.event_date = p_event_date
      and r.home_team_canonical = v_home
      and r.away_team_canonical = v_away
    limit 1;

    select r.*
    into v_prev
    from private.fixture_schedule_rows_v1 r
    where r.batch_id = v_batch_id
      and r.league_id = v_target.league_id
      and r.season = v_target.season
      and r.home_team_canonical = v_target.home_team_canonical
      and r.event_date is not null
      and r.event_date < v_target.event_date
    order by r.event_date desc, r.source_event_id desc
    limit 1;

    select r.*
    into v_next
    from private.fixture_schedule_rows_v1 r
    where r.batch_id = v_batch_id
      and r.league_id = v_target.league_id
      and r.season = v_target.season
      and r.home_team_canonical = v_target.home_team_canonical
      and r.event_date is not null
      and r.event_date > v_target.event_date
    order by r.event_date asc, r.source_event_id asc
    limit 1;

    select
        count(*) filter (
            where r.event_date > v_target.event_date
              and r.event_date <= v_target.event_date + 7
              and (r.home_team_canonical = v_target.home_team_canonical or r.away_team_canonical = v_target.home_team_canonical)
        )::integer,
        count(*) filter (
            where r.event_date > v_target.event_date
              and r.event_date <= v_target.event_date + 14
              and (r.home_team_canonical = v_target.home_team_canonical or r.away_team_canonical = v_target.home_team_canonical)
        )::integer,
        count(*) filter (
            where r.event_date > v_target.event_date
              and r.event_date <= v_target.event_date + 30
              and (r.home_team_canonical = v_target.home_team_canonical or r.away_team_canonical = v_target.home_team_canonical)
        )::integer,
        count(*) filter (
            where r.event_date > v_target.event_date
              and r.event_date <= v_target.event_date + 7
              and r.home_team_canonical = v_target.home_team_canonical
        )::integer,
        count(*) filter (
            where r.event_date > v_target.event_date
              and r.event_date <= v_target.event_date + 14
              and r.home_team_canonical = v_target.home_team_canonical
        )::integer,
        count(*) filter (
            where r.event_date > v_target.event_date
              and r.event_date <= v_target.event_date + 30
              and r.home_team_canonical = v_target.home_team_canonical
        )::integer
    into v_team_7, v_team_14, v_team_30, v_home_7, v_home_14, v_home_30
    from private.fixture_schedule_rows_v1 r
    where r.batch_id = v_batch_id
      and r.league_id = v_target.league_id
      and r.season = v_target.season
      and r.event_date is not null;

    return jsonb_build_object(
        'version','fixture-context-as-known-v1',
        'status','READY',
        'as_of_at',p_as_of_at,
        'schedule_batch_id',v_batch_id,
        'schedule_observed_at',v_batch_observed_at,
        'schedule_source_max_fetched_at',v_source_max_fetched_at,
        'target_source_event_id',v_target.source_event_id,
        'league_id',v_target.league_id,
        'season',v_target.season,
        'event_date',v_target.event_date,
        'home_team_canonical',v_target.home_team_canonical,
        'away_team_canonical',v_target.away_team_canonical,
        'previous_home_match_days',case when v_prev.id is null then null else (v_target.event_date - v_prev.event_date) end,
        'previous_home_source_event_id',case when v_prev.id is null then null else v_prev.source_event_id end,
        'previous_home_opponent_canonical',case when v_prev.id is null then null else v_prev.away_team_canonical end,
        'next_home_match_days',case when v_next.id is null then null else (v_next.event_date - v_target.event_date) end,
        'next_home_source_event_id',case when v_next.id is null then null else v_next.source_event_id end,
        'next_home_opponent_canonical',case when v_next.id is null then null else v_next.away_team_canonical end,
        'team_fixture_density_next_7d',v_team_7,
        'team_fixture_density_next_14d',v_team_14,
        'team_fixture_density_next_30d',v_team_30,
        'home_fixture_density_next_7d',v_home_7,
        'home_fixture_density_next_14d',v_home_14,
        'home_fixture_density_next_30d',v_home_30,
        'evidence_class','forward_schedule_as_known',
        'historical_backfill_allowed',false,
        'production_change',false
    );
end;
$function$;

create or replace function public.fixture_context_for_ticket_event_as_known_v1(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz
)
returns jsonb
language plpgsql
stable
set search_path to 'public','private'
as $function$
declare
    v_event public.ticket_events%rowtype;
    v_context jsonb;
begin
    select * into v_event
    from public.ticket_events
    where id = p_ticket_event_id;

    if v_event.id is null then
        return jsonb_build_object(
            'version','fixture-context-ticket-event-adapter-v1',
            'status','TICKET_EVENT_NOT_FOUND',
            'ticket_event_id',p_ticket_event_id,
            'as_of_at',p_as_of_at,
            'production_change',false
        );
    end if;

    v_context := public.fixture_context_as_known_v1(
        v_event.home_team,
        v_event.away_team,
        v_event.match_date,
        p_as_of_at
    );

    return v_context || jsonb_build_object(
        'ticket_event_id',p_ticket_event_id,
        'ticket_event_home_team',v_event.home_team,
        'ticket_event_away_team',v_event.away_team,
        'ticket_event_match_date',v_event.match_date,
        'ticket_event_kickoff_at',v_event.kickoff_at
    );
end;
$function$;

revoke all on function public.fixture_context_as_known_v1(text,text,date,timestamptz) from public, anon, authenticated;
revoke all on function public.fixture_context_for_ticket_event_as_known_v1(bigint,timestamptz) from public, anon, authenticated;
grant execute on function public.fixture_context_as_known_v1(text,text,date,timestamptz) to service_role;
grant execute on function public.fixture_context_for_ticket_event_as_known_v1(bigint,timestamptz) to service_role;

commit;
