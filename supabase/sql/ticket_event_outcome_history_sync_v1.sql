-- Ticket Event Outcome Sync v1
--
-- Purpose:
-- Automatically copy verified Ekstraklasa attendance outcomes from
-- public.ml_home_attendance_history_v2 into public.ticket_event_outcomes
-- once the tracked ticket event is safely post-match.
--
-- Matching is intentionally strict:
-- - same club_slug;
-- - exact kickoff_at;
-- - source history competition_key = 'ekstraklasa';
-- - tracked competition normalizes to Ekstraklasa;
-- - kickoff is at least 3 hours in the past;
-- - existing outcomes are never overwritten.

create or replace function public.sync_ticket_event_outcomes_from_home_history_v1()
returns integer
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
  v_inserted integer := 0;
begin
  with inserted as (
    insert into public.ticket_event_outcomes(
      ticket_event_id,
      actual_attendance,
      attendance_definition,
      source_name,
      source_url,
      confirmed_at,
      notes
    )
    select
      te.id,
      h.actual_attendance,
      'reported_match_attendance',
      h.source_name,
      h.source_url,
      now(),
      'Automatically synced from ml_home_attendance_history_v2 by exact club_slug and kickoff_at match.'
    from public.ticket_events te
    join public.ml_home_attendance_history_v2 h
      on h.club_slug = te.club_slug
     and h.kickoff_at = te.kickoff_at
     and h.competition_key = 'ekstraklasa'
    where te.kickoff_at < now() - interval '3 hours'
      and private.normalize_structural_prior_competition_v1(te.competition) = 'Ekstraklasa'
      and not exists (
        select 1
        from public.ticket_event_outcomes o
        where o.ticket_event_id = te.id
      )
    on conflict (ticket_event_id) do nothing
    returning ticket_event_id
  )
  select count(*)::integer into v_inserted from inserted;

  return v_inserted;
end;
$function$;

revoke all on function public.sync_ticket_event_outcomes_from_home_history_v1() from public, anon, authenticated;
grant execute on function public.sync_ticket_event_outcomes_from_home_history_v1() to service_role;

select cron.schedule(
  'ticket-event-outcome-history-sync-v1',
  '17 * * * *',
  $$select public.sync_ticket_event_outcomes_from_home_history_v1();$$
)
where not exists (
  select 1
  from cron.job
  where jobname = 'ticket-event-outcome-history-sync-v1'
);
