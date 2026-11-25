-- Guarded apply for dashboard readiness key-only I/O optimization.
-- Project: adchzwqboeekhokapxqi. Captured originals 2026-11-25.
-- Apply only as one transaction; fails closed on any definition/ownership/grant drift.
BEGIN;
DO $guard$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc p WHERE p.oid = 'public.get_live_signal_study_readiness_v1()'::regprocedure
      AND pg_catalog.pg_get_userbyid(p.proowner) = 'postgres'
      AND COALESCE(p.proacl::text, '<default>') = '{postgres=X/postgres,service_role=X/postgres}'
      AND p.prosecdef IS FALSE
      AND p.provolatile = 's'
      AND p.proconfig = ARRAY['search_path=public']::text[]
      AND encode(pg_catalog.sha256(convert_to(pg_catalog.pg_get_functiondef(p.oid), 'UTF8')), 'hex') = 'edcb98f7caee46b16701bbd6ef3928f8cf58419ddedea810a7f855435751a333') THEN
    RAISE EXCEPTION 'guard failed: public.get_live_signal_study_readiness_v1() definition/owner/grants/security changed';
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
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc p WHERE p.oid = 'public.get_dashboard_research_readiness_v2()'::regprocedure
      AND pg_catalog.pg_get_userbyid(p.proowner) = 'postgres'
      AND COALESCE(p.proacl::text, '<default>') = '{postgres=X/postgres,service_role=X/postgres}'
      AND p.prosecdef IS TRUE
      AND p.provolatile = 's'
      AND p.proconfig = ARRAY['search_path=public']::text[]
      AND encode(pg_catalog.sha256(convert_to(pg_catalog.pg_get_functiondef(p.oid), 'UTF8')), 'hex') = '0b77c59d3136702f36a25b61076e605032f287a9ca3f07d99b68e0d9dd11fe15') THEN
    RAISE EXCEPTION 'guard failed: public.get_dashboard_research_readiness_v2() definition/owner/grants/security changed';
  END IF;
  IF pg_catalog.to_regprocedure('private.dashboard_multiclub_feature_keys_v1()') IS NOT NULL THEN
    RAISE EXCEPTION 'guard failed: private helper already exists';
  END IF;
END $guard$;

-- Review draft: aggregate-only dashboard readiness queries must not call the
-- full live feature store. Apply only after isolated parity tests and review.

create or replace function private.dashboard_multiclub_feature_keys_v1()
returns table(ticket_event_id bigint, club_slug text, horizon text, snapshot_id bigint)
language sql
stable
security definer
set search_path = ''
as $function$
with horizons(label,target_hours,tolerance_hours,ord) as (
 values
  ('T-30'::text,720.0::numeric,240.0::numeric,1),
  ('T-14',336.0,96.0,2),
  ('T-7',168.0,48.0,3),
  ('T-3',72.0,24.0,4),
  ('T-24h',24.0,12.0,5)
), candidates as (
 select te.id as ticket_event_id,te.club_slug,h.label as horizon,s.id as snapshot_id,
  row_number() over (
   partition by te.id,h.label
   order by (extract(epoch from (te.kickoff_at-s.captured_at))/3600.0-h.target_hours) asc,
    s.captured_at desc,s.id desc
  ) as rn
 from public.ticket_events te
 join public.snapshots s on s.ticket_event_id=te.id
 cross join horizons h
 where te.kickoff_at is not null
  and s.available_total is not null
  and s.captured_at<=te.kickoff_at
  and extract(epoch from (te.kickoff_at-s.captured_at))/3600.0>=h.target_hours
  and extract(epoch from (te.kickoff_at-s.captured_at))/3600.0<=h.target_hours+h.tolerance_hours
)
select c.ticket_event_id,c.club_slug,c.horizon,c.snapshot_id
from candidates c where c.rn=1
$function$;

revoke all on function private.dashboard_multiclub_feature_keys_v1()
 from public,anon,authenticated,service_role;
grant execute on function private.dashboard_multiclub_feature_keys_v1() to service_role;

create or replace function public.get_live_signal_study_readiness_v1()
returns table(
 independent_outcome_events bigint,
 clubs_with_outcome bigint,
 strict_study_rows bigint,
 models_with_strict_rows bigint,
 cross_club_gate_met boolean,
 learned_correction_gate_met boolean,
 status text
)
language sql
stable
set search_path to 'public'
as $function$
with outcomes as (
 select count(distinct te.id)::bigint as events,
  count(distinct te.club_slug)::bigint as clubs
 from public.ticket_events te
 join public.ticket_event_outcomes o on o.ticket_event_id=te.id
 where o.actual_attendance is not null
), study as (
 select count(*)::bigint as study_rows,
  count(distinct ml.model_version)::bigint as models
 from public.get_model_lab_rows_v1() ml
 join private.dashboard_multiclub_feature_keys_v1() fk
  on fk.ticket_event_id=ml.ticket_event_id and fk.horizon=ml.horizon
 where ml.historical_p50 is not null
)
select o.events,o.clubs,s.study_rows,s.models,
 (o.events>=8 and o.clubs>=3),
 (o.events>=20),
 case
  when o.events<8 then 'collect_more_independent_outcomes'
  when o.clubs<3 then 'collect_more_club_outcomes'
  when o.events<20 then 'run_exploratory_cross_club_study_no_promotion'
  else 'eligible_for_grouped_live_residual_challenger_benchmark'
 end
from outcomes o cross join study s
$function$;

create or replace function public.get_dashboard_research_readiness_v2()
returns table (
 crossclub_study_events bigint,
 crossclub_study_clubs bigint,
 strict_study_rows bigint,
 crossclub_gate_met boolean,
 crossclub_event_target integer,
 crossclub_club_target integer,
 independent_outcome_events_total bigint,
 outcome_clubs_total bigint,
 learned_correction_gate_met boolean,
 learned_correction_event_target integer,
 generated_at timestamptz
)
language sql
stable
security definer
set search_path to 'public'
as $function$
with study as (
 select count(distinct b.ticket_event_id)::bigint as events,
  count(distinct b.club_slug)::bigint as clubs,
  count(*)::bigint as rows
 from public.crossclub_baseline_rows_v2 b
 join private.dashboard_multiclub_feature_keys_v1() fk
  on fk.ticket_event_id=b.ticket_event_id
), outcomes as (
 select count(*)::bigint as events,
  count(distinct e.club_slug)::bigint as clubs
 from public.ticket_event_outcomes o
 join public.ticket_events e on e.id=o.ticket_event_id
)
select study.events,study.clubs,study.rows,
 study.events>=8 and study.clubs>=3,
 8,3,outcomes.events,outcomes.clubs,outcomes.events>=20,20,now()
from study cross join outcomes
$function$;

COMMIT;
