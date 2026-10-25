-- P11 odds capture health v2.
-- Operational-only watchdog. No attendance targets and no production behavior.
-- 270 minutes is intentionally below the six-hour primary cadence so the
-- +30m fallback schedule can recover a missed primary run without duplicating
-- a successful fresh capture.

create or replace function public.p11_market_odds_capture_health_v2()
returns jsonb
language sql
stable
security definer
set search_path to 'public','private'
as $function$
with state as (
  select
    max(captured_at) as last_capture_at,
    count(*)::int as quote_rows,
    count(distinct ticket_event_id)::int as event_count,
    count(distinct capture_batch_id)::int as capture_batch_count
  from private.p11_market_odds_observations_v2
), derived as (
  select
    *,
    case when last_capture_at is null then null
         else extract(epoch from (now() - last_capture_at))/60.0 end as age_minutes,
    last_capture_at is null or last_capture_at < now() - interval '270 minutes' as capture_due
  from state
)
select jsonb_build_object(
  'version','p11-market-odds-capture-health-v2',
  'checked_at',now(),
  'last_capture_at',last_capture_at,
  'age_minutes',age_minutes,
  'stale_after_minutes',270,
  'capture_due',capture_due,
  'quote_rows',quote_rows,
  'event_count',event_count,
  'capture_batch_count',capture_batch_count,
  'target_values_used',false,
  'production_change',false
)
from derived;
$function$;

revoke all on function public.p11_market_odds_capture_health_v2() from public, anon, authenticated;
grant execute on function public.p11_market_odds_capture_health_v2() to service_role;
