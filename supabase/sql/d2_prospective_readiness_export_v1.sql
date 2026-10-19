-- d2 Prospective Readiness Export v1
--
-- Purpose:
-- Expose all tracked Ekstraklasa ticket events for prospective evidence
-- readiness, including events that do not yet have a verified attendance
-- outcome. This is intentionally separate from the frozen C1 v7 training
-- export, which must continue to require ticket_event_outcomes.
--
-- Read-only evidence contract:
-- - LEFT JOIN verified outcome;
-- - audited home capacity when available;
-- - raw final-24h snapshot count from public.snapshots;
-- - no attendance estimation from inventory;
-- - no mutation of frozen model/training state.

create or replace function public.export_d2_prospective_readiness_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with tracked as (
  select
    e.id as ticket_event_id,
    e.club_slug,
    e.home_team,
    e.away_team,
    e.competition,
    private.normalize_structural_prior_competition_v1(e.competition) as canonical_competition,
    e.kickoff_at,
    o.actual_attendance,
    o.source_name as outcome_source_name,
    o.source_url as outcome_source_url,
    o.confirmed_at as outcome_confirmed_at,
    ha.club_key as home_club_key
  from public.ticket_events e
  left join public.ticket_event_outcomes o
    on o.ticket_event_id = e.id
  left join private.structural_prior_club_aliases_v1 ha
    on ha.alias = e.home_team
   and ha.is_active
  where private.normalize_structural_prior_competition_v1(e.competition) = 'Ekstraklasa'
), enriched as (
  select
    t.*,
    cr.stadium_capacity,
    cr.source_name as capacity_source_name,
    cr.source_url as capacity_source_url,
    cr.verification_status as capacity_verification_status,
    coalesce(sc.final24_snapshot_count, 0)::integer as final24_snapshot_count
  from tracked t
  left join lateral (
    select
      c.stadium_capacity,
      c.source_name,
      c.source_url,
      c.verification_status
    from private.structural_prior_capacity_registry_v1 c
    where c.club_key = t.home_club_key
      and (t.kickoff_at at time zone 'Europe/Warsaw')::date >= c.valid_from
      and (c.valid_to is null or (t.kickoff_at at time zone 'Europe/Warsaw')::date <= c.valid_to)
    order by c.valid_from desc, c.id desc
    limit 1
  ) cr on true
  left join lateral (
    select count(*)::integer as final24_snapshot_count
    from public.snapshots s
    where s.ticket_event_id = t.ticket_event_id
      and s.captured_at >= t.kickoff_at - interval '24 hours'
      and s.captured_at <= t.kickoff_at
  ) sc on true
), payload as (
  select coalesce(
    jsonb_agg(to_jsonb(e) order by e.kickoff_at, e.ticket_event_id),
    '[]'::jsonb
  ) as rows
  from enriched e
)
select jsonb_build_object(
  'version', 'd2-prospective-readiness-v1',
  'eventCount', (select count(*) from enriched),
  'events', (select rows from payload)
);
$function$;

revoke all on function public.export_d2_prospective_readiness_v1() from public, anon, authenticated;
grant execute on function public.export_d2_prospective_readiness_v1() to service_role;
