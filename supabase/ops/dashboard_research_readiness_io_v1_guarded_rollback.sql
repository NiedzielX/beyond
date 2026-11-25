-- Guarded rollback for dashboard readiness key-only I/O optimization.
-- Only restores the two replaced readiness bodies and removes this run's helper.
-- Fails closed if any endpoint, grants, ownership, or helper differs from the tested state.
BEGIN;
DO $guard$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc p WHERE p.oid = 'public.get_live_signal_study_readiness_v1()'::regprocedure
      AND pg_catalog.pg_get_userbyid(p.proowner) = 'postgres'
      AND COALESCE(p.proacl::text, '<default>') = '{postgres=X/postgres,service_role=X/postgres}'
      AND p.prosecdef IS FALSE
      AND p.provolatile = 's'
      AND p.proconfig = ARRAY['search_path=public']::text[]
      AND encode(pg_catalog.sha256(convert_to(pg_catalog.pg_get_functiondef(p.oid), 'UTF8')), 'hex') = 'eedf3f369a64430404551852c4d6c50732ec5e53c787c0d779bda3f5bf34132a') THEN
    RAISE EXCEPTION 'guard failed: public.get_live_signal_study_readiness_v1() definition/owner/grants/security changed';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc p WHERE p.oid = 'public.get_dashboard_research_readiness_v2()'::regprocedure
      AND pg_catalog.pg_get_userbyid(p.proowner) = 'postgres'
      AND COALESCE(p.proacl::text, '<default>') = '{postgres=X/postgres,service_role=X/postgres}'
      AND p.prosecdef IS TRUE
      AND p.provolatile = 's'
      AND p.proconfig = ARRAY['search_path=public']::text[]
      AND encode(pg_catalog.sha256(convert_to(pg_catalog.pg_get_functiondef(p.oid), 'UTF8')), 'hex') = '7fcca873be5de28983e8bdc1147dee94373b81a153c03d6ba3fdc3b3699ef7b8') THEN
    RAISE EXCEPTION 'guard failed: public.get_dashboard_research_readiness_v2() definition/owner/grants/security changed';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc p WHERE p.oid = 'public.get_dashboard_ml_readiness_safe_v1()'::regprocedure
      AND pg_catalog.pg_get_userbyid(p.proowner) = 'postgres'
      AND COALESCE(p.proacl::text, '<default>') = '{postgres=X/postgres,service_role=X/postgres}'
      AND p.prosecdef IS TRUE
      AND p.provolatile = 's'
      AND p.proconfig = ARRAY['search_path=public']::text[]
      AND encode(pg_catalog.sha256(convert_to(pg_catalog.pg_get_functiondef(p.oid), 'UTF8')), 'hex') = '67621d22f95ca9a96a7fb0987106a3d04ce7b585762d1d8dea26fce6907281c9') THEN
    RAISE EXCEPTION 'guard failed: public.get_dashboard_ml_readiness_safe_v1() definition/owner/grants/security changed';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc p WHERE p.oid = 'private.dashboard_multiclub_feature_keys_v1()'::regprocedure
      AND pg_catalog.pg_get_userbyid(p.proowner) = 'postgres'
      AND COALESCE(p.proacl::text, '<default>') = '{postgres=X/postgres,service_role=X/postgres}'
      AND p.prosecdef IS TRUE
      AND p.provolatile = 's'
      AND encode(pg_catalog.sha256(convert_to(pg_catalog.pg_get_functiondef(p.oid), 'UTF8')), 'hex') = 'ca51d9cea93490235b5738bbca8977c6c5c9c3dec27984411193674650ff65d9') THEN
    RAISE EXCEPTION 'guard failed: optimized helper definition/owner/grants/security changed';
  END IF;
END $guard$;

CREATE OR REPLACE FUNCTION public.get_live_signal_study_readiness_v1()
 RETURNS TABLE(independent_outcome_events bigint, clubs_with_outcome bigint, strict_study_rows bigint, models_with_strict_rows bigint, cross_club_gate_met boolean, learned_correction_gate_met boolean, status text)
 LANGUAGE sql
 STABLE
 SET search_path TO 'public'
AS $function$
with outcomes as (
    select
      count(distinct te.id)::bigint as events,
      count(distinct te.club_slug)::bigint as clubs
    from public.ticket_events te
    join public.ticket_event_outcomes o on o.ticket_event_id=te.id
    where o.actual_attendance is not null
), rows as (
    select
      count(*)::bigint as study_rows,
      count(distinct model_version)::bigint as models
    from public.live_signal_study_rows_v1
)
select
    o.events,
    o.clubs,
    r.study_rows,
    r.models,
    (o.events>=8 and o.clubs>=3),
    (o.events>=20),
    case
      when o.events<8 then 'collect_more_independent_outcomes'
      when o.clubs<3 then 'collect_more_club_outcomes'
      when o.events<20 then 'run_exploratory_cross_club_study_no_promotion'
      else 'eligible_for_grouped_live_residual_challenger_benchmark'
    end
from outcomes o cross join rows r;
$function$


CREATE OR REPLACE FUNCTION public.get_dashboard_research_readiness_v2()
 RETURNS TABLE(crossclub_study_events bigint, crossclub_study_clubs bigint, strict_study_rows bigint, crossclub_gate_met boolean, crossclub_event_target integer, crossclub_club_target integer, independent_outcome_events_total bigint, outcome_clubs_total bigint, learned_correction_gate_met boolean, learned_correction_event_target integer, generated_at timestamp with time zone)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  with study as (
    select
      count(distinct ticket_event_id)::bigint as events,
      count(distinct club_slug)::bigint as clubs,
      count(*)::bigint as rows
    from public.crossclub_live_signal_study_rows_v2
  ), outcomes as (
    select
      count(*)::bigint as events,
      count(distinct e.club_slug)::bigint as clubs
    from public.ticket_event_outcomes o
    join public.ticket_events e on e.id = o.ticket_event_id
  )
  select
    study.events,
    study.clubs,
    study.rows,
    study.events >= 8 and study.clubs >= 3,
    8,
    3,
    outcomes.events,
    outcomes.clubs,
    outcomes.events >= 20,
    20,
    now()
  from study cross join outcomes;
$function$


DROP FUNCTION private.dashboard_multiclub_feature_keys_v1();
COMMIT;
