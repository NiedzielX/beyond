-- P11a — genuine PIT 1X2 odds capture v2
--
-- Verified live contract. Raw bookmaker-level quotes are preserved append-only;
-- consensus is derived point-in-time from the latest capture batch known at the
-- requested cutoff. No attendance target is used and production is unchanged.

create table if not exists private.p11_market_odds_observations_v2 (
    id bigint generated always as identity primary key,
    ticket_event_id bigint not null references public.ticket_events(id) on delete cascade,
    provider text not null,
    provider_event_id text not null,
    bookmaker_key text not null,
    bookmaker_title text null,
    market_type text not null default '1x2' check (market_type = '1x2'),
    capture_batch_id uuid not null,
    captured_at timestamptz not null,
    provider_commence_at timestamptz not null,
    provider_updated_at timestamptz null,
    home_decimal numeric not null check (home_decimal > 1),
    draw_decimal numeric not null check (draw_decimal > 1),
    away_decimal numeric not null check (away_decimal > 1),
    is_in_play boolean not null default false check (is_in_play = false),
    source_url text null,
    source_payload_hash text null,
    mapping_method text not null,
    home_club_key text not null,
    away_club_key text not null,
    kickoff_delta_seconds integer not null,
    created_at timestamptz not null default now(),
    unique (ticket_event_id, provider, provider_event_id, bookmaker_key, market_type, captured_at),
    check (captured_at < provider_commence_at),
    check (abs(kickoff_delta_seconds) <= 5400),
    check (source_payload_hash is null or source_payload_hash ~ '^[0-9a-f]{64}$')
);

create index if not exists p11_market_odds_v2_event_capture_idx
on private.p11_market_odds_observations_v2(ticket_event_id, captured_at desc)
where is_in_play = false;

create index if not exists p11_market_odds_v2_batch_idx
on private.p11_market_odds_observations_v2(capture_batch_id, bookmaker_key);

alter table private.p11_market_odds_observations_v2 enable row level security;
revoke all on private.p11_market_odds_observations_v2 from public, anon, authenticated;
revoke all on sequence private.p11_market_odds_observations_v2_id_seq from public, anon, authenticated;
grant usage on schema private to service_role;
grant select, insert on private.p11_market_odds_observations_v2 to service_role;
grant usage, select on sequence private.p11_market_odds_observations_v2_id_seq to service_role;
grant select on private.structural_prior_club_aliases_v1 to service_role;

create or replace function public.p11_market_capture_inputs_v2(
    p_horizon_days integer default 14
)
returns jsonb
language sql
stable
security invoker
set search_path to 'public', 'private'
as $function$
select jsonb_build_object(
    'version','p11-market-capture-inputs-v2',
    'generated_at',now(),
    'target_values_used',false,
    'production_change',false,
    'sport_key','soccer_poland_ekstraklasa',
    'events',coalesce((
        select jsonb_agg(jsonb_build_object(
            'ticket_event_id',e.id,
            'home_team',e.home_team,
            'away_team',e.away_team,
            'competition',e.competition,
            'kickoff_at',e.kickoff_at,
            'club_slug',e.club_slug
        ) order by e.kickoff_at,e.id)
        from public.ticket_events e
        where e.kickoff_at > now()
          and e.kickoff_at <= now() + make_interval(days => greatest(1,least(p_horizon_days,30)))
          and lower(coalesce(e.competition,'')) like '%ekstraklasa%'
    ),'[]'::jsonb),
    'aliases',coalesce((
        select jsonb_agg(jsonb_build_object(
            'alias',a.alias,
            'club_key',a.club_key,
            'canonical_name',a.canonical_name
        ) order by a.club_key,a.alias)
        from private.structural_prior_club_aliases_v1 a
        where a.is_active
    ),'[]'::jsonb)
);
$function$;

revoke all on function public.p11_market_capture_inputs_v2(integer) from public, anon, authenticated;
grant execute on function public.p11_market_capture_inputs_v2(integer) to service_role;

create or replace function public.insert_p11_market_odds_capture_v2(
    p_capture jsonb
)
returns jsonb
language plpgsql
security invoker
set search_path to 'public', 'private'
as $function$
declare
    v_event_id bigint := (p_capture->>'ticket_event_id')::bigint;
    v_provider text := nullif(p_capture->>'provider','');
    v_provider_event_id text := nullif(p_capture->>'provider_event_id','');
    v_batch_id uuid := (p_capture->>'capture_batch_id')::uuid;
    v_captured_at timestamptz := (p_capture->>'captured_at')::timestamptz;
    v_provider_commence_at timestamptz := (p_capture->>'provider_commence_at')::timestamptz;
    v_source_url text := nullif(p_capture->>'source_url','');
    v_source_payload_hash text := nullif(p_capture->>'source_payload_hash','');
    v_mapping_method text := nullif(p_capture->>'mapping_method','');
    v_home_club_key text := nullif(p_capture->>'home_club_key','');
    v_away_club_key text := nullif(p_capture->>'away_club_key','');
    v_event public.ticket_events%rowtype;
    v_local_home_key text;
    v_local_away_key text;
    v_delta integer;
    v_quote jsonb;
    v_inserted integer := 0;
    v_attempted integer := 0;
begin
    if v_provider is null or v_provider_event_id is null or v_mapping_method is null
       or v_home_club_key is null or v_away_club_key is null then
        raise exception 'missing capture lineage fields';
    end if;
    if jsonb_typeof(p_capture->'quotes') <> 'array' or jsonb_array_length(p_capture->'quotes') < 1 then
        raise exception 'quotes array required';
    end if;
    if v_source_payload_hash is not null and v_source_payload_hash !~ '^[0-9a-f]{64}$' then
        raise exception 'invalid source payload hash';
    end if;

    select * into strict v_event
    from public.ticket_events
    where id = v_event_id;

    if lower(coalesce(v_event.competition,'')) not like '%ekstraklasa%' then
        raise exception 'ticket event is not Ekstraklasa';
    end if;
    if v_captured_at >= v_event.kickoff_at or v_provider_commence_at <= v_captured_at then
        raise exception 'capture must be genuinely pre-match';
    end if;

    v_delta := round(extract(epoch from (v_provider_commence_at - v_event.kickoff_at)))::integer;
    if abs(v_delta) > 5400 then
        raise exception 'provider/local kickoff mismatch exceeds tolerance: % seconds',v_delta;
    end if;

    select a.club_key into v_local_home_key
    from private.structural_prior_club_aliases_v1 a
    where a.is_active and (a.alias = v_event.home_team or a.canonical_name = v_event.home_team)
    order by case when a.alias = v_event.home_team then 0 else 1 end
    limit 1;

    select a.club_key into v_local_away_key
    from private.structural_prior_club_aliases_v1 a
    where a.is_active and (a.alias = v_event.away_team or a.canonical_name = v_event.away_team)
    order by case when a.alias = v_event.away_team then 0 else 1 end
    limit 1;

    if v_local_home_key is null or v_local_away_key is null then
        raise exception 'local event aliases unresolved';
    end if;
    if v_local_home_key <> v_home_club_key or v_local_away_key <> v_away_club_key then
        raise exception 'provider/local club mapping mismatch';
    end if;

    for v_quote in select value from jsonb_array_elements(p_capture->'quotes')
    loop
        v_attempted := v_attempted + 1;
        if nullif(v_quote->>'bookmaker_key','') is null then
            raise exception 'bookmaker_key required';
        end if;
        if (v_quote->>'home_decimal')::numeric <= 1
           or (v_quote->>'draw_decimal')::numeric <= 1
           or (v_quote->>'away_decimal')::numeric <= 1 then
            raise exception 'invalid decimal odds';
        end if;
        if coalesce((v_quote->>'is_in_play')::boolean,false) then
            raise exception 'in-play quote rejected';
        end if;
        if nullif(v_quote->>'provider_updated_at','') is not null
           and (v_quote->>'provider_updated_at')::timestamptz > v_captured_at + interval '10 minutes' then
            raise exception 'provider_updated_at is implausibly after capture';
        end if;

        insert into private.p11_market_odds_observations_v2(
            ticket_event_id,provider,provider_event_id,bookmaker_key,bookmaker_title,
            market_type,capture_batch_id,captured_at,provider_commence_at,provider_updated_at,
            home_decimal,draw_decimal,away_decimal,is_in_play,source_url,source_payload_hash,
            mapping_method,home_club_key,away_club_key,kickoff_delta_seconds
        ) values (
            v_event_id,v_provider,v_provider_event_id,v_quote->>'bookmaker_key',nullif(v_quote->>'bookmaker_title',''),
            '1x2',v_batch_id,v_captured_at,v_provider_commence_at,nullif(v_quote->>'provider_updated_at','')::timestamptz,
            (v_quote->>'home_decimal')::numeric,(v_quote->>'draw_decimal')::numeric,(v_quote->>'away_decimal')::numeric,
            false,v_source_url,v_source_payload_hash,v_mapping_method,v_home_club_key,v_away_club_key,v_delta
        )
        on conflict do nothing;
        if found then v_inserted := v_inserted + 1; end if;
    end loop;

    return jsonb_build_object(
        'version','insert-p11-market-odds-capture-v2',
        'ticket_event_id',v_event_id,
        'capture_batch_id',v_batch_id,
        'attempted_quotes',v_attempted,
        'inserted_quotes',v_inserted,
        'kickoff_delta_seconds',v_delta,
        'production_change',false
    );
end;
$function$;

revoke all on function public.insert_p11_market_odds_capture_v2(jsonb) from public, anon, authenticated;
grant execute on function public.insert_p11_market_odds_capture_v2(jsonb) to service_role;

create or replace function public.p11_market_context_as_known_v2(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz
)
returns jsonb
language sql
stable
security invoker
set search_path to 'public', 'private'
as $function$
with event_row as (
    select id,kickoff_at from public.ticket_events where id=p_ticket_event_id
), latest_batch as (
    select o.capture_batch_id,o.captured_at,o.provider,o.provider_event_id
    from private.p11_market_odds_observations_v2 o
    join event_row e on e.id=o.ticket_event_id
    where o.ticket_event_id=p_ticket_event_id
      and o.market_type='1x2'
      and not o.is_in_play
      and o.captured_at <= p_as_of_at
      and o.captured_at < e.kickoff_at
    order by o.captured_at desc,o.id desc
    limit 1
), quote_probs as (
    select o.*,
           (1/o.home_decimal) / ((1/o.home_decimal)+(1/o.draw_decimal)+(1/o.away_decimal)) as p_home,
           (1/o.draw_decimal) / ((1/o.home_decimal)+(1/o.draw_decimal)+(1/o.away_decimal)) as p_draw,
           (1/o.away_decimal) / ((1/o.home_decimal)+(1/o.draw_decimal)+(1/o.away_decimal)) as p_away
    from private.p11_market_odds_observations_v2 o
    join latest_batch b on b.capture_batch_id=o.capture_batch_id
    where o.ticket_event_id=p_ticket_event_id and not o.is_in_play
), medians as (
    select count(distinct bookmaker_key)::integer as bookmaker_count,
           percentile_cont(0.5) within group(order by p_home)::numeric as med_home,
           percentile_cont(0.5) within group(order by p_draw)::numeric as med_draw,
           percentile_cont(0.5) within group(order by p_away)::numeric as med_away,
           min(captured_at) as captured_at,
           min(provider) as provider,
           min(provider_event_id) as provider_event_id,
           min(capture_batch_id::text)::uuid as capture_batch_id
    from quote_probs
), consensus as (
    select m.*,(med_home+med_draw+med_away) as med_sum
    from medians m
    where bookmaker_count > 0
), normalized as (
    select c.*,
           med_home/med_sum as home_probability,
           med_draw/med_sum as draw_probability,
           med_away/med_sum as away_probability
    from consensus c
)
select case when not exists(select 1 from normalized) then
    jsonb_build_object(
        'version','p11-market-context-as-known-v2',
        'ticket_event_id',p_ticket_event_id,
        'requested_as_of_at',p_as_of_at,
        'status','MISSING',
        'point_in_time_validated',true,
        'production_change',false
    )
else (
    select jsonb_build_object(
        'version','p11-market-context-as-known-v2',
        'ticket_event_id',p_ticket_event_id,
        'requested_as_of_at',p_as_of_at,
        'status','READY',
        'point_in_time_validated',true,
        'production_change',false,
        'provider',provider,
        'provider_event_id',provider_event_id,
        'capture_batch_id',capture_batch_id,
        'captured_at',captured_at,
        'bookmaker_count',bookmaker_count,
        'home_probability',home_probability,
        'draw_probability',draw_probability,
        'away_probability',away_probability,
        'favorite_probability',greatest(home_probability,draw_probability,away_probability),
        'outcome_uncertainty',
            -(home_probability*ln(home_probability)
              + draw_probability*ln(draw_probability)
              + away_probability*ln(away_probability))/ln(3::numeric),
        'interpretation',jsonb_build_object(
            'consensus','median of bookmaker-level de-vigged probabilities, renormalized to sum to 1',
            'outcome_uncertainty','normalized entropy of consensus 1X2 probabilities; higher means more balanced outcomes',
            'expected_match_quality','NOT_DERIVED_FROM_1X2_V2'
        )
    ) from normalized
) end;
$function$;

revoke all on function public.p11_market_context_as_known_v2(bigint,timestamptz) from public, anon, authenticated;
grant execute on function public.p11_market_context_as_known_v2(bigint,timestamptz) to service_role;

create or replace function public.p11_market_odds_readiness_v2()
returns jsonb
language sql
stable
security invoker
set search_path to 'public', 'private'
as $function$
with valid as (
    select o.ticket_event_id,e.club_slug,e.kickoff_at,o.captured_at,o.bookmaker_key,o.capture_batch_id,
           extract(epoch from (e.kickoff_at-o.captured_at))/3600.0 as hours_to_kickoff
    from private.p11_market_odds_observations_v2 o
    join public.ticket_events e on e.id=o.ticket_event_id
    where o.market_type='1x2' and not o.is_in_play and o.captured_at<e.kickoff_at
), per_event as (
    select ticket_event_id,club_slug,
           max(hours_to_kickoff) as earliest_hours_to_kickoff,
           count(distinct bookmaker_key)::integer as bookmaker_count,
           count(distinct capture_batch_id)::integer as capture_batches
    from valid
    group by ticket_event_id,club_slug
)
select jsonb_build_object(
    'version','p11-market-odds-readiness-v2',
    'checked_at',now(),
    'independent_unit','ticket_event',
    'target_values_used',false,
    'production_change',false,
    'provider_selected',true,
    'provider','the-odds-api-v4',
    'model_precommitted',false,
    'events_with_any_pit_1x2',coalesce((select count(*) from per_event),0),
    'clubs_with_any_pit_1x2',coalesce((select count(distinct club_slug) from per_event),0),
    'events_with_at_least_3_bookmakers',coalesce((select count(*) from per_event where bookmaker_count>=3),0),
    'coverage',jsonb_build_object(
        'events_reaching_168h',coalesce((select count(*) from per_event where earliest_hours_to_kickoff>=168),0),
        'events_reaching_72h',coalesce((select count(*) from per_event where earliest_hours_to_kickoff>=72),0),
        'events_reaching_24h',coalesce((select count(*) from per_event where earliest_hours_to_kickoff>=24),0)
    ),
    'status',case when exists(select 1 from per_event)
        then 'GENUINE_PIT_DATA_ACCUMULATING'
        else 'CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET'
    end,
    'next_action','configure provider secret and begin append-only pre-match capture; precommit model only after genuine coverage audit'
);
$function$;

revoke all on function public.p11_market_odds_readiness_v2() from public, anon, authenticated;
grant execute on function public.p11_market_odds_readiness_v2() to service_role;
