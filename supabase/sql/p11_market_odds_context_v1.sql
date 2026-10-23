-- P11a — PIT-safe 1X2 market context v1
-- Applied live on 2026-10-23 as migration p11_market_odds_context_v1.
--
-- Scope: append-only odds capture + as-known feature derivation + target-free
-- readiness. This does NOT select an odds provider and does NOT backfill
-- closing odds into historical cutoffs.

create table if not exists private.p11_market_odds_observations_v1 (
    id bigint generated always as identity primary key,
    ticket_event_id bigint not null references public.ticket_events(id) on delete cascade,
    provider text not null,
    market_type text not null default '1x2' check (market_type = '1x2'),
    captured_at timestamptz not null,
    provider_updated_at timestamptz null,
    home_decimal numeric not null check (home_decimal > 1),
    draw_decimal numeric not null check (draw_decimal > 1),
    away_decimal numeric not null check (away_decimal > 1),
    is_in_play boolean not null default false,
    source_url text null,
    source_payload_hash text null,
    created_at timestamptz not null default now(),
    unique (ticket_event_id, provider, market_type, captured_at)
);

create index if not exists p11_market_odds_event_captured_idx
on private.p11_market_odds_observations_v1(ticket_event_id, captured_at desc)
where is_in_play = false;

alter table private.p11_market_odds_observations_v1 enable row level security;
revoke all on private.p11_market_odds_observations_v1 from anon, authenticated;
grant select, insert on private.p11_market_odds_observations_v1 to service_role;
grant usage, select on sequence private.p11_market_odds_observations_v1_id_seq to service_role;

create or replace function public.p11_market_context_as_known_v1(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz
)
returns jsonb
language sql
stable
set search_path to 'public', 'private'
as $function$
with event_row as (
    select id, kickoff_at
    from public.ticket_events
    where id = p_ticket_event_id
), latest as (
    select o.*
    from private.p11_market_odds_observations_v1 o
    join event_row e on e.id = o.ticket_event_id
    where o.ticket_event_id = p_ticket_event_id
      and o.market_type = '1x2'
      and o.is_in_play = false
      and o.captured_at <= p_as_of_at
      and o.captured_at < e.kickoff_at
    order by o.captured_at desc, o.id desc
    limit 1
), probs as (
    select l.*,
           (1 / l.home_decimal) as raw_home,
           (1 / l.draw_decimal) as raw_draw,
           (1 / l.away_decimal) as raw_away,
           ((1 / l.home_decimal) + (1 / l.draw_decimal) + (1 / l.away_decimal)) as overround_factor
    from latest l
), normalized as (
    select p.*,
           raw_home / overround_factor as home_probability,
           raw_draw / overround_factor as draw_probability,
           raw_away / overround_factor as away_probability
    from probs p
)
select case when not exists(select 1 from normalized) then
    jsonb_build_object(
        'version','p11-market-context-as-known-v1',
        'ticket_event_id',p_ticket_event_id,
        'requested_as_of_at',p_as_of_at,
        'status','MISSING',
        'point_in_time_validated',true,
        'production_change',false
    )
else (
    select jsonb_build_object(
        'version','p11-market-context-as-known-v1',
        'ticket_event_id',p_ticket_event_id,
        'requested_as_of_at',p_as_of_at,
        'status','READY',
        'point_in_time_validated',true,
        'production_change',false,
        'observation_id',id,
        'provider',provider,
        'market_type',market_type,
        'captured_at',captured_at,
        'provider_updated_at',provider_updated_at,
        'home_decimal',home_decimal,
        'draw_decimal',draw_decimal,
        'away_decimal',away_decimal,
        'overround_factor',overround_factor,
        'home_probability',home_probability,
        'draw_probability',draw_probability,
        'away_probability',away_probability,
        'favorite_probability',greatest(home_probability, draw_probability, away_probability),
        'outcome_uncertainty',
            -(home_probability * ln(home_probability)
              + draw_probability * ln(draw_probability)
              + away_probability * ln(away_probability)) / ln(3::numeric),
        'interpretation',jsonb_build_object(
            'outcome_uncertainty','normalized entropy of de-vigged 1X2 probabilities; higher means more balanced outcome probabilities',
            'favorite_probability','maximum de-vigged 1X2 probability',
            'expected_match_quality','NOT_DERIVED_FROM_1X2_V1'
        )
    )
    from normalized
) end;
$function$;

revoke all on function public.p11_market_context_as_known_v1(bigint,timestamptz) from public, anon, authenticated;
grant execute on function public.p11_market_context_as_known_v1(bigint,timestamptz) to service_role;

create or replace function public.p11_market_odds_readiness_v1()
returns jsonb
language sql
stable
set search_path to 'public', 'private'
as $function$
with valid as (
    select o.ticket_event_id,
           e.club_slug,
           e.kickoff_at,
           o.captured_at,
           extract(epoch from (e.kickoff_at - o.captured_at))/3600.0 as hours_to_kickoff
    from private.p11_market_odds_observations_v1 o
    join public.ticket_events e on e.id = o.ticket_event_id
    where o.market_type='1x2'
      and o.is_in_play=false
      and o.captured_at < e.kickoff_at
), per_event as (
    select ticket_event_id, club_slug,
           max(hours_to_kickoff) as earliest_hours_to_kickoff,
           min(hours_to_kickoff) as latest_hours_to_kickoff,
           count(*)::integer as observation_count
    from valid
    group by ticket_event_id, club_slug
)
select jsonb_build_object(
    'version','p11-market-odds-readiness-v1',
    'checked_at',now(),
    'independent_unit','ticket_event',
    'target_values_used',false,
    'production_change',false,
    'provider_selected',false,
    'model_precommitted',false,
    'events_with_any_pit_1x2',coalesce((select count(*) from per_event),0),
    'clubs_with_any_pit_1x2',coalesce((select count(distinct club_slug) from per_event),0),
    'coverage',jsonb_build_object(
        'events_reaching_168h',coalesce((select count(*) from per_event where earliest_hours_to_kickoff >= 168),0),
        'events_reaching_72h',coalesce((select count(*) from per_event where earliest_hours_to_kickoff >= 72),0),
        'events_reaching_24h',coalesce((select count(*) from per_event where earliest_hours_to_kickoff >= 24),0)
    ),
    'status',case when exists(select 1 from per_event)
        then 'DATA_ACCUMULATING'
        else 'NO_GENUINE_ODDS_CAPTURE_YET'
    end,
    'next_action','select a lawful/reliable odds source and begin append-only capture before defining any odds-model ablation'
);
$function$;

revoke all on function public.p11_market_odds_readiness_v1() from public, anon, authenticated;
grant execute on function public.p11_market_odds_readiness_v1() to service_role;
