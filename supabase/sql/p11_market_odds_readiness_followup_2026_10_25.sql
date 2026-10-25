-- P11a follow-up after first genuine audited capture.
-- Keeps readiness messaging consistent with actual coverage state.
-- No target values are used and production remains unchanged.

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
    'next_action',case when exists(select 1 from per_event)
        then 'continue append-only scheduled pre-match capture; audit horizon coverage; precommit model only after genuine coverage audit'
        else 'begin append-only pre-match capture after provider configuration; precommit model only after genuine coverage audit'
    end
);
$function$;

revoke all on function public.p11_market_odds_readiness_v2() from public, anon, authenticated;
grant execute on function public.p11_market_odds_readiness_v2() to service_role;
