-- Browser-safe summary access for Ticketing Challenger v1.
-- Event-level CV rows remain service-role only.

create table if not exists public.ticketing_challenger_dashboard_summary_v1 (
  protocol text primary key,
  event_count integer not null,
  club_count integer not null,
  baseline_mae numeric,
  bias_control_mae numeric,
  challenger_mae numeric,
  uplift_vs_baseline numeric,
  incremental_ticketing_uplift numeric,
  challenger_bias numeric,
  candidate_model text,
  protocol_status text,
  refreshed_at timestamptz not null default now()
);

alter table public.ticketing_challenger_dashboard_summary_v1 enable row level security;
revoke all on public.ticketing_challenger_dashboard_summary_v1 from anon,authenticated;
grant select on public.ticketing_challenger_dashboard_summary_v1 to anon,authenticated;
grant select,insert,update,delete on public.ticketing_challenger_dashboard_summary_v1 to service_role;

drop policy if exists dashboard_ticketing_challenger_summary_read on public.ticketing_challenger_dashboard_summary_v1;
create policy dashboard_ticketing_challenger_summary_read
on public.ticketing_challenger_dashboard_summary_v1
for select to anon,authenticated using (true);

create or replace function public.refresh_ticketing_challenger_dashboard_v1()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare v_rows integer := 0;
begin
  delete from public.ticketing_challenger_dashboard_summary_v1;
  insert into public.ticketing_challenger_dashboard_summary_v1(
    protocol,event_count,club_count,baseline_mae,bias_control_mae,challenger_mae,
    uplift_vs_baseline,incremental_ticketing_uplift,challenger_bias,candidate_model,
    protocol_status,refreshed_at
  )
  select protocol,event_count,club_count,baseline_mae,bias_control_mae,challenger_mae,
    uplift_vs_baseline,incremental_ticketing_uplift,challenger_bias,candidate_model,
    protocol_status,now()
  from public.dashboard_ticketing_challenger_v1;
  get diagnostics v_rows=row_count;
  return v_rows;
end;
$$;

revoke all on function public.refresh_ticketing_challenger_dashboard_v1() from public,anon,authenticated;
grant execute on function public.refresh_ticketing_challenger_dashboard_v1() to service_role;

select public.refresh_ticketing_challenger_dashboard_v1();

drop view public.dashboard_ticketing_challenger_v1;
create view public.dashboard_ticketing_challenger_v1
with (security_invoker=true)
as
select protocol,event_count,club_count,baseline_mae,bias_control_mae,challenger_mae,
  uplift_vs_baseline,incremental_ticketing_uplift,challenger_bias,candidate_model,
  protocol_status,refreshed_at
from public.ticketing_challenger_dashboard_summary_v1;

revoke all on public.dashboard_ticketing_challenger_v1 from public;
grant select on public.dashboard_ticketing_challenger_v1 to anon,authenticated,service_role;

drop policy if exists dashboard_ticketing_challenger_model_read on public.ticketing_challenger_models_v1;
create policy dashboard_ticketing_challenger_model_read
on public.ticketing_challenger_models_v1
for select to anon,authenticated using (true);

grant select (
  model_version,trained_at,horizon,feature_key,ridge_alpha,
  training_event_count,training_club_count,status,y_mean,beta
) on public.ticketing_challenger_models_v1 to anon,authenticated;

grant select on public.dashboard_ticketing_challenger_model_v1 to anon,authenticated,service_role;
