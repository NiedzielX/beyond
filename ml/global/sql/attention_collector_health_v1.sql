-- Beyond Ticketing — media attention collector health v1.
--
-- The collector is expected every 15 minutes. If the newest persisted sample is
-- older than 45 minutes (or there are no samples), mark media-attention features
-- as degraded instead of pretending automation is healthy.

alter table public.context_feature_definitions
  drop constraint if exists context_feature_definitions_collection_status_check;

alter table public.context_feature_definitions
  add constraint context_feature_definitions_collection_status_check
  check (collection_status is null or collection_status in (
    'active_automated','active_manual','verified_registry','shadow_automated',
    'degraded_automation','planned','blocked_external_access'
  ));

create or replace view public.dashboard_attention_collector_health_v1
with (security_invoker=true)
as
with latest as (
  select max(sample_at) as latest_sample_at
  from public.media_attention_samples
), state as (
  select
    latest_sample_at,
    case when latest_sample_at is null then null
         else round(extract(epoch from (now()-latest_sample_at))/60.0,1) end as age_minutes
  from latest
)
select
  latest_sample_at,
  age_minutes,
  15::int as expected_interval_minutes,
  45::int as degraded_after_minutes,
  case
    when latest_sample_at is null then 'no_samples'
    when age_minutes>45 then 'degraded'
    else 'healthy'
  end as health_status
from state;

revoke all on public.dashboard_attention_collector_health_v1 from public;
grant select on public.dashboard_attention_collector_health_v1 to anon,authenticated,service_role;

create or replace function public.refresh_attention_collector_health_v1()
returns text
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare
  v_status text;
begin
  select health_status into v_status
  from public.dashboard_attention_collector_health_v1;

  update public.context_feature_definitions
  set collection_status=case
        when v_status='healthy' then 'active_automated'
        else 'degraded_automation'
      end,
      updated_at=now()
  where feature_key in ('hype.media_attention','hype.mention_acceleration');

  return v_status;
end;
$$;

revoke all on function public.refresh_attention_collector_health_v1() from public,anon,authenticated;
grant execute on function public.refresh_attention_collector_health_v1() to service_role;

do $$
declare v_job bigint;
begin
  select jobid into v_job from cron.job where jobname='attention_collector_health_15m';
  if v_job is not null then perform cron.unschedule(v_job); end if;
end $$;

select cron.schedule(
  'attention_collector_health_15m','*/15 * * * *',
  $$select public.refresh_attention_collector_health_v1();$$
);

select public.refresh_attention_collector_health_v1();
