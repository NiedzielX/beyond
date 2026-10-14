-- Beyond Ticketing — dashboard security hardening v1
-- Replaces public SECURITY DEFINER dashboard access with service-role-refreshed cache tables.

create table if not exists public.dashboard_event_live_state_cache_v1
as select * from public.get_dashboard_event_live_state_safe_v1() with no data;
create unique index if not exists idx_dashboard_event_live_state_cache_event
  on public.dashboard_event_live_state_cache_v1(ticket_event_id);
alter table public.dashboard_event_live_state_cache_v1 enable row level security;
revoke all on public.dashboard_event_live_state_cache_v1 from anon,authenticated;
grant select on public.dashboard_event_live_state_cache_v1 to anon,authenticated;
grant select,insert,update,delete on public.dashboard_event_live_state_cache_v1 to service_role;
create policy dashboard_event_live_state_cache_read on public.dashboard_event_live_state_cache_v1
for select to anon,authenticated using (true);

create table if not exists public.dashboard_ml_readiness_cache_v1
as select * from public.get_dashboard_ml_readiness_safe_v1() with no data;
alter table public.dashboard_ml_readiness_cache_v1 add column if not exists cache_id boolean not null default true;
alter table public.dashboard_ml_readiness_cache_v1 add constraint dashboard_ml_readiness_cache_v1_pkey primary key (cache_id);
alter table public.dashboard_ml_readiness_cache_v1 enable row level security;
revoke all on public.dashboard_ml_readiness_cache_v1 from anon,authenticated;
grant select on public.dashboard_ml_readiness_cache_v1 to anon,authenticated;
grant select,insert,update,delete on public.dashboard_ml_readiness_cache_v1 to service_role;
create policy dashboard_ml_readiness_cache_read on public.dashboard_ml_readiness_cache_v1
for select to anon,authenticated using (true);

create table if not exists public.dashboard_research_readiness_cache_v2
as select * from public.get_dashboard_research_readiness_v2() with no data;
alter table public.dashboard_research_readiness_cache_v2 add column if not exists cache_id boolean not null default true;
alter table public.dashboard_research_readiness_cache_v2 add constraint dashboard_research_readiness_cache_v2_pkey primary key (cache_id);
alter table public.dashboard_research_readiness_cache_v2 enable row level security;
revoke all on public.dashboard_research_readiness_cache_v2 from anon,authenticated;
grant select on public.dashboard_research_readiness_cache_v2 to anon,authenticated;
grant select,insert,update,delete on public.dashboard_research_readiness_cache_v2 to service_role;
create policy dashboard_research_readiness_cache_read on public.dashboard_research_readiness_cache_v2
for select to anon,authenticated using (true);

create table if not exists public.dashboard_weather_latest_cache_v1
as select * from public.get_dashboard_weather_latest_safe_v1() with no data;
create unique index if not exists idx_dashboard_weather_latest_cache_event
  on public.dashboard_weather_latest_cache_v1(ticket_event_id);
alter table public.dashboard_weather_latest_cache_v1 enable row level security;
revoke all on public.dashboard_weather_latest_cache_v1 from anon,authenticated;
grant select on public.dashboard_weather_latest_cache_v1 to anon,authenticated;
grant select,insert,update,delete on public.dashboard_weather_latest_cache_v1 to service_role;
create policy dashboard_weather_latest_cache_read on public.dashboard_weather_latest_cache_v1
for select to anon,authenticated using (true);

create table if not exists public.dashboard_weather_research_cache_v1
as select * from public.get_dashboard_weather_research_v1() with no data;
alter table public.dashboard_weather_research_cache_v1 add column if not exists cache_id boolean not null default true;
alter table public.dashboard_weather_research_cache_v1 add constraint dashboard_weather_research_cache_v1_pkey primary key (cache_id);
alter table public.dashboard_weather_research_cache_v1 enable row level security;
revoke all on public.dashboard_weather_research_cache_v1 from anon,authenticated;
grant select on public.dashboard_weather_research_cache_v1 to anon,authenticated;
grant select,insert,update,delete on public.dashboard_weather_research_cache_v1 to service_role;
create policy dashboard_weather_research_cache_read on public.dashboard_weather_research_cache_v1
for select to anon,authenticated using (true);

create or replace function public.refresh_dashboard_safe_caches_v1()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare v_rows integer:=0; v_n integer;
begin
  delete from public.dashboard_event_live_state_cache_v1;
  insert into public.dashboard_event_live_state_cache_v1 select * from public.get_dashboard_event_live_state_safe_v1();
  get diagnostics v_n=row_count; v_rows:=v_rows+v_n;
  delete from public.dashboard_ml_readiness_cache_v1;
  insert into public.dashboard_ml_readiness_cache_v1(independent_outcome_events,clubs_with_outcome,strict_study_rows,models_with_strict_rows,cross_club_gate_met,learned_correction_gate_met,status,cross_club_event_target,cross_club_club_target,learned_correction_event_target,generated_at)
    select * from public.get_dashboard_ml_readiness_safe_v1();
  get diagnostics v_n=row_count; v_rows:=v_rows+v_n;
  delete from public.dashboard_research_readiness_cache_v2;
  insert into public.dashboard_research_readiness_cache_v2(crossclub_study_events,crossclub_study_clubs,strict_study_rows,crossclub_gate_met,crossclub_event_target,crossclub_club_target,independent_outcome_events_total,outcome_clubs_total,learned_correction_gate_met,learned_correction_event_target,generated_at)
    select * from public.get_dashboard_research_readiness_v2();
  get diagnostics v_n=row_count; v_rows:=v_rows+v_n;
  delete from public.dashboard_weather_latest_cache_v1;
  insert into public.dashboard_weather_latest_cache_v1 select * from public.get_dashboard_weather_latest_safe_v1();
  get diagnostics v_n=row_count; v_rows:=v_rows+v_n;
  delete from public.dashboard_weather_research_cache_v1;
  insert into public.dashboard_weather_research_cache_v1(historical_study_version,historical_sample_size,historical_seasons,baseline_mae,loocv_weather_mae,loocv_uplift,loso_weather_mae,loso_uplift,historical_signal_status,prospective_weather_events,prospective_weather_rows,prospective_t24_outcome_pairs,generated_at)
    select * from public.get_dashboard_weather_research_v1();
  get diagnostics v_n=row_count; v_rows:=v_rows+v_n;
  return v_rows;
end;
$$;
revoke all on function public.refresh_dashboard_safe_caches_v1() from public,anon,authenticated;
grant execute on function public.refresh_dashboard_safe_caches_v1() to service_role;

create or replace view public.dashboard_event_live_state_v1 with (security_invoker=true) as
select * from public.dashboard_event_live_state_cache_v1;
create or replace view public.dashboard_ml_readiness_v1 with (security_invoker=true) as
select independent_outcome_events,clubs_with_outcome,strict_study_rows,models_with_strict_rows,cross_club_gate_met,learned_correction_gate_met,status,cross_club_event_target,cross_club_club_target,learned_correction_event_target,generated_at from public.dashboard_ml_readiness_cache_v1;
create or replace view public.dashboard_research_readiness_v2 with (security_invoker=true) as
select crossclub_study_events,crossclub_study_clubs,strict_study_rows,crossclub_gate_met,crossclub_event_target,crossclub_club_target,independent_outcome_events_total,outcome_clubs_total,learned_correction_gate_met,learned_correction_event_target,generated_at from public.dashboard_research_readiness_cache_v2;
create or replace view public.dashboard_weather_latest_v1 with (security_invoker=true) as
select * from public.dashboard_weather_latest_cache_v1;
create or replace view public.dashboard_weather_research_v1 with (security_invoker=true) as
select historical_study_version,historical_sample_size,historical_seasons,baseline_mae,loocv_weather_mae,loocv_uplift,loso_weather_mae,loso_uplift,historical_signal_status,prospective_weather_events,prospective_weather_rows,prospective_t24_outcome_pairs,generated_at from public.dashboard_weather_research_cache_v1;

grant select on public.dashboard_event_live_state_v1,public.dashboard_ml_readiness_v1,public.dashboard_research_readiness_v2,public.dashboard_weather_latest_v1,public.dashboard_weather_research_v1 to anon,authenticated,service_role;

revoke all on function public.get_dashboard_event_live_state_safe_v1() from public,anon,authenticated;
revoke all on function public.get_dashboard_ml_readiness_safe_v1() from public,anon,authenticated;
revoke all on function public.get_dashboard_research_readiness_v2() from public,anon,authenticated;
revoke all on function public.get_dashboard_weather_latest_safe_v1() from public,anon,authenticated;
revoke all on function public.get_dashboard_weather_research_v1() from public,anon,authenticated;
grant execute on function public.get_dashboard_event_live_state_safe_v1() to service_role;
grant execute on function public.get_dashboard_ml_readiness_safe_v1() to service_role;
grant execute on function public.get_dashboard_research_readiness_v2() to service_role;
grant execute on function public.get_dashboard_weather_latest_safe_v1() to service_role;
grant execute on function public.get_dashboard_weather_research_v1() to service_role;

alter function public.sporting_canonical_team_v1(text) set search_path=public,pg_temp;
alter function public.match_competition_key_v1(text) set search_path=public,pg_temp;

create index if not exists idx_weather_backfill_request_map_ticket_event on public.weather_backfill_request_map(ticket_event_id);
create index if not exists idx_model_activation_health_ticket_event on public.model_activation_health_samples_v1(ticket_event_id);

-- Internal schedule used in production:
-- cron.schedule('dashboard_safe_cache_refresh_15m','8,23,38,53 * * * *',
--   $$select public.refresh_dashboard_safe_caches_v1();$$)
