-- Beyond Ticketing — Match Context Challenger v1.
-- Research-only T-24h evaluation after Baseline + Ticketing.
-- Timing is reconstructable from kickoff_at; competition stage and opponent uplift are evidence-gated.
-- No match-context ablation prediction is created unless a candidate improves the incumbent chain.

create or replace view public.match_context_timing_dataset_v1 as
select
  s.id as snapshot_id,
  s.ticket_event_id,
  e.club_slug,
  e.home_team,
  e.away_team,
  e.kickoff_at,
  s.checkpoint_at,
  bt.predicted_p50 as baseline_ticketing_p50,
  o.actual_attendance,
  (o.actual_attendance-bt.predicted_p50)::numeric/nullif(bt.predicted_p50,0) as residual_ratio,
  extract(isodow from e.kickoff_at at time zone 'Europe/Warsaw')::int as weekday_iso,
  extract(hour from e.kickoff_at at time zone 'Europe/Warsaw')::int as local_hour,
  case when extract(isodow from e.kickoff_at at time zone 'Europe/Warsaw')::int in (6,7) then 1.0 else 0.0 end as weekend_flag,
  case when extract(hour from e.kickoff_at at time zone 'Europe/Warsaw')::int between 17 and 20 then 1.0 else 0.0 end as prime_window_flag
from public.event_context_snapshots_v1 s
join public.ticket_events e on e.id=s.ticket_event_id
join public.context_ablation_predictions_v1 bt
  on bt.snapshot_id=s.id and bt.variant_key='baseline_ticketing'
join public.ticket_event_outcomes o on o.ticket_event_id=s.ticket_event_id
where s.checkpoint_code='T-24h'
  and public.match_competition_key_v1(e.competition)='ekstraklasa';

revoke all on public.match_context_timing_dataset_v1 from anon,authenticated;
grant select on public.match_context_timing_dataset_v1 to service_role;

create or replace view public.match_context_timing_cv_v1 as
with feature_long as (
  select snapshot_id,ticket_event_id,club_slug,home_team,away_team,baseline_ticketing_p50,actual_attendance,residual_ratio,
         'timing_weekend_flag'::text feature_key,weekend_flag::numeric feature_value
  from public.match_context_timing_dataset_v1
  union all
  select snapshot_id,ticket_event_id,club_slug,home_team,away_team,baseline_ticketing_p50,actual_attendance,residual_ratio,
         'timing_prime_window'::text,prime_window_flag::numeric
  from public.match_context_timing_dataset_v1
  union all
  select snapshot_id,ticket_event_id,club_slug,home_team,away_team,baseline_ticketing_p50,actual_attendance,residual_ratio,
         'timing_local_hour'::text,local_hour::numeric
  from public.match_context_timing_dataset_v1
), protocols as (
  select 'leave_one_event_out'::text protocol
  union all
  select 'leave_one_club_out'::text
), scored as (
  select d.feature_key,p.protocol,d.snapshot_id,d.ticket_event_id,d.club_slug,
    d.baseline_ticketing_p50,d.actual_attendance,d.feature_value,
    st.n_train,st.club_count_train,st.x_mean,st.x_sd,st.y_mean,st.beta,
    st.y_mean as bias_only_ratio,
    st.y_mean + st.beta*((d.feature_value-st.x_mean)/nullif(st.x_sd,0)) as challenger_ratio
  from feature_long d
  cross join protocols p
  cross join lateral (
    with tr as (
      select * from feature_long t
      where t.feature_key=d.feature_key
        and case when p.protocol='leave_one_event_out' then t.ticket_event_id<>d.ticket_event_id else t.club_slug<>d.club_slug end
    ), base as (
      select count(*)::int n_train,count(distinct club_slug)::int club_count_train,
        avg(feature_value) x_mean,stddev_pop(feature_value) x_sd,avg(residual_ratio) y_mean
      from tr
    )
    select b.n_train,b.club_count_train,b.x_mean,b.x_sd,b.y_mean,
      sum(((tr.feature_value-b.x_mean)/nullif(b.x_sd,0))*(tr.residual_ratio-b.y_mean))
        /(sum(power((tr.feature_value-b.x_mean)/nullif(b.x_sd,0),2))+30.0) beta
    from tr cross join base b
    group by b.n_train,b.club_count_train,b.x_mean,b.x_sd,b.y_mean
  ) st
  where st.n_train>=5 and st.x_sd>0
)
select feature_key,protocol,snapshot_id,ticket_event_id,club_slug,baseline_ticketing_p50,actual_attendance,
  feature_value,n_train,club_count_train,x_mean,x_sd,y_mean,beta,
  round((baseline_ticketing_p50*(1+bias_only_ratio))::numeric)::int bias_only_p50,
  round((baseline_ticketing_p50*(1+greatest(-0.25::numeric,least(0.25::numeric,challenger_ratio))))::numeric)::int challenger_p50
from scored;

revoke all on public.match_context_timing_cv_v1 from anon,authenticated;
grant select on public.match_context_timing_cv_v1 to service_role;

create table if not exists public.match_context_challenger_dashboard_v1 (
  feature_key text not null,
  protocol text not null,
  event_count integer not null,
  club_count integer not null,
  baseline_ticketing_mae numeric,
  bias_control_mae numeric,
  challenger_mae numeric,
  uplift_vs_ticketing numeric,
  incremental_match_context_uplift numeric,
  candidate_status text not null,
  refreshed_at timestamptz not null default now(),
  primary key(feature_key,protocol)
);

alter table public.match_context_challenger_dashboard_v1 enable row level security;
revoke all on public.match_context_challenger_dashboard_v1 from anon,authenticated;
grant select on public.match_context_challenger_dashboard_v1 to anon,authenticated;
grant select,insert,update,delete on public.match_context_challenger_dashboard_v1 to service_role;

drop policy if exists dashboard_match_context_challenger_read on public.match_context_challenger_dashboard_v1;
create policy dashboard_match_context_challenger_read on public.match_context_challenger_dashboard_v1
for select to anon,authenticated using (true);

create table if not exists public.match_context_feature_readiness_v1 (
  feature_key text primary key,
  readiness_status text not null,
  reason text not null,
  evidence jsonb not null default '{}'::jsonb,
  refreshed_at timestamptz not null default now()
);

alter table public.match_context_feature_readiness_v1 enable row level security;
revoke all on public.match_context_feature_readiness_v1 from anon,authenticated;
grant select on public.match_context_feature_readiness_v1 to anon,authenticated;
grant select,insert,update,delete on public.match_context_feature_readiness_v1 to service_role;

drop policy if exists dashboard_match_context_readiness_read on public.match_context_feature_readiness_v1;
create policy dashboard_match_context_readiness_read on public.match_context_feature_readiness_v1
for select to anon,authenticated using (true);

create or replace function public.refresh_match_context_challenger_v1()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare v_rows integer := 0; v_ready_opponent integer := 0;
begin
  delete from public.match_context_challenger_dashboard_v1;

  insert into public.match_context_challenger_dashboard_v1(
    feature_key,protocol,event_count,club_count,baseline_ticketing_mae,bias_control_mae,
    challenger_mae,uplift_vs_ticketing,incremental_match_context_uplift,candidate_status,refreshed_at
  )
  select feature_key,protocol,count(*)::int,count(distinct club_slug)::int,
    round(avg(abs(baseline_ticketing_p50-actual_attendance)),1),
    round(avg(abs(bias_only_p50-actual_attendance)),1),
    round(avg(abs(challenger_p50-actual_attendance)),1),
    round(avg(abs(baseline_ticketing_p50-actual_attendance))-avg(abs(challenger_p50-actual_attendance)),1),
    round(avg(abs(bias_only_p50-actual_attendance))-avg(abs(challenger_p50-actual_attendance)),1),
    case
      when count(*)<8 or count(distinct club_slug)<5 then 'insufficient_sample'
      when avg(abs(challenger_p50-actual_attendance))<avg(abs(baseline_ticketing_p50-actual_attendance))
       and avg(abs(challenger_p50-actual_attendance))<avg(abs(bias_only_p50-actual_attendance)) then 'positive_research_signal'
      else 'rejected_no_uplift'
    end,
    now()
  from public.match_context_timing_cv_v1
  group by feature_key,protocol;

  get diagnostics v_rows=row_count;

  select count(*)::int into v_ready_opponent
  from (
    select distinct on (ticket_event_id) ticket_event_id,readiness_status
    from public.opponent_uplift_shadow_samples
    order by ticket_event_id,observed_at desc
  ) x
  where readiness_status='ready';

  insert into public.match_context_feature_readiness_v1(feature_key,readiness_status,reason,evidence,refreshed_at)
  values
    ('match.timing','tested_rejected_current_candidates',
      'Timing is fully reconstructable from kickoff_at, but weekend, prime-window and local-hour Ridge candidates do not improve MAE over Baseline + Ticketing on the current T-24h sample.',
      jsonb_build_object('checkpoint','T-24h','features_tested',jsonb_build_array('weekend_flag','prime_window_flag','local_hour'),'ridge_alpha',30,'production_impact','none'),now()),
    ('match.competition_stage','not_testable_current_sample',
      'All current evaluation rows are Ekstraklasa and the event source does not provide an explicit stage, so there is no trustworthy stage variation to test.',
      jsonb_build_object('source_stage_status','not_provided_by_event_source','production_impact','none'),now()),
    ('match.opponent_historical_uplift',
      case when v_ready_opponent>0 then 'shadow_ready_for_some_future_events' else 'insufficient_history' end,
      case when v_ready_opponent>0
        then 'Some future events pass the 8-club/3-opponent history gate, but the current completed T-24h evaluation sample does not have point-in-time opponent uplift coverage.'
        else 'No current event passes the 8 prior club outcomes and 3 prior same-opponent home meetings gate; no zero fallback is used.' end,
      jsonb_build_object('club_history_gate',8,'opponent_history_gate',3,'ready_future_events',v_ready_opponent,'production_impact','none_shadow_only'),now())
  on conflict (feature_key) do update set
    readiness_status=excluded.readiness_status,reason=excluded.reason,evidence=excluded.evidence,refreshed_at=excluded.refreshed_at;

  return v_rows;
end;
$$;

revoke all on function public.refresh_match_context_challenger_v1() from public,anon,authenticated;
grant execute on function public.refresh_match_context_challenger_v1() to service_role;

select public.refresh_match_context_challenger_v1();

create or replace view public.dashboard_match_context_challenger_v1
with (security_invoker=true)
as
select feature_key,protocol,event_count,club_count,baseline_ticketing_mae,bias_control_mae,
  challenger_mae,uplift_vs_ticketing,incremental_match_context_uplift,candidate_status,refreshed_at
from public.match_context_challenger_dashboard_v1;

revoke all on public.dashboard_match_context_challenger_v1 from public;
grant select on public.dashboard_match_context_challenger_v1 to anon,authenticated,service_role;

create or replace view public.dashboard_match_context_readiness_v1
with (security_invoker=true)
as
select feature_key,readiness_status,reason,evidence,refreshed_at
from public.match_context_feature_readiness_v1;

revoke all on public.dashboard_match_context_readiness_v1 from public;
grant select on public.dashboard_match_context_readiness_v1 to anon,authenticated,service_role;

do $$
declare v_job bigint;
begin
  select jobid into v_job from cron.job where jobname='match_context_challenger_summary_6h';
  if v_job is not null then perform cron.unschedule(v_job); end if;
end $$;

select cron.schedule('match_context_challenger_summary_6h','17 */6 * * *',
  $$select public.refresh_match_context_challenger_v1();$$);

update public.context_feature_definitions
set collection_note=coalesce(collection_note,'') || ' Research result 2026-10-13: T-24h timing candidates (weekend flag, prime window, local hour; Ridge alpha 30) did not improve MAE over Baseline + Ticketing. Timing collection remains active raw context; no Match Context P50 is produced from these candidates.',
    updated_at=now()
where feature_key='match.timing';
