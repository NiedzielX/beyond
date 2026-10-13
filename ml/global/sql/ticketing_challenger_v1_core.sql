-- Beyond Ticketing — Ticketing Challenger v1 core.
-- T-24h research-only challenger using hybrid 6h velocity.
-- matched sector velocity is preferred; raw velocity is the fallback.
-- Ridge alpha = 30. Validation includes leave-one-event-out and leave-one-club-out.

create or replace view public.ticketing_challenger_dataset_v1 as
select
  s.id as snapshot_id,
  s.ticket_event_id,
  e.club_slug,
  e.home_team,
  e.away_team,
  e.kickoff_at,
  s.checkpoint_at,
  b.predicted_p50 as baseline_p50,
  o.actual_attendance,
  (o.actual_attendance-b.predicted_p50)::numeric/nullif(b.predicted_p50,0) as residual_ratio,
  f.snapshot_id as feature_snapshot_id,
  f.snapshot_captured_at as feature_snapshot_captured_at,
  coalesce(f.matched_velocity_6h_pct_of_first_per_hour,f.raw_velocity_6h_pct_of_first_per_hour)::numeric as hybrid_v6,
  case when f.matched_velocity_6h_pct_of_first_per_hour is not null then 'matched_v6' else 'raw_v6' end as hybrid_v6_source,
  f.release_activity_flag,
  f.sector_coverage_change_flag,
  f.feature_quality
from public.event_context_snapshots_v1 s
join public.ticket_events e on e.id=s.ticket_event_id
join public.context_ablation_predictions_v1 b on b.snapshot_id=s.id and b.variant_key='baseline'
join public.ticket_event_outcomes o on o.ticket_event_id=s.ticket_event_id
join public.multiclub_feature_store_v4 f on f.ticket_event_id=s.ticket_event_id and f.horizon='T-24h'
where s.checkpoint_code='T-24h'
  and f.snapshot_captured_at<=s.checkpoint_at
  and coalesce(f.matched_velocity_6h_pct_of_first_per_hour,f.raw_velocity_6h_pct_of_first_per_hour) is not null;

revoke all on public.ticketing_challenger_dataset_v1 from anon,authenticated;
grant select on public.ticketing_challenger_dataset_v1 to service_role;

create or replace view public.ticketing_challenger_cv_predictions_v1 as
with protocols as (
  select 'leave_one_event_out'::text as protocol
  union all
  select 'leave_one_club_out'::text
), scored as (
  select
    p.protocol,d.snapshot_id,d.ticket_event_id,d.club_slug,d.home_team,d.away_team,
    d.baseline_p50,d.actual_attendance,d.hybrid_v6,d.hybrid_v6_source,
    st.n_train,st.club_count_train,st.x_mean,st.x_sd,st.y_mean,st.beta,
    st.y_mean as bias_only_ratio,
    st.y_mean+st.beta*((d.hybrid_v6-st.x_mean)/nullif(st.x_sd,0)) as challenger_ratio
  from public.ticketing_challenger_dataset_v1 d
  cross join protocols p
  cross join lateral (
    with tr as (
      select * from public.ticketing_challenger_dataset_v1 t
      where case when p.protocol='leave_one_event_out' then t.ticket_event_id<>d.ticket_event_id else t.club_slug<>d.club_slug end
    ), base as (
      select count(*)::int n_train,count(distinct club_slug)::int club_count_train,
        avg(hybrid_v6) x_mean,stddev_pop(hybrid_v6) x_sd,avg(residual_ratio) y_mean
      from tr
    )
    select b.n_train,b.club_count_train,b.x_mean,b.x_sd,b.y_mean,
      sum(((tr.hybrid_v6-b.x_mean)/nullif(b.x_sd,0))*(tr.residual_ratio-b.y_mean))
        /(sum(power((tr.hybrid_v6-b.x_mean)/nullif(b.x_sd,0),2))+30.0) as beta
    from tr cross join base b
    group by b.n_train,b.club_count_train,b.x_mean,b.x_sd,b.y_mean
  ) st
  where st.n_train>=5 and st.x_sd>0
)
select
  protocol,snapshot_id,ticket_event_id,club_slug,home_team,away_team,
  baseline_p50,actual_attendance,hybrid_v6,hybrid_v6_source,
  n_train,club_count_train,x_mean,x_sd,y_mean,beta,
  round((baseline_p50*(1+bias_only_ratio))::numeric)::int as bias_only_p50,
  round((baseline_p50*(1+greatest(-0.25::numeric,least(0.25::numeric,challenger_ratio))))::numeric)::int as challenger_p50,
  challenger_ratio
from scored;

revoke all on public.ticketing_challenger_cv_predictions_v1 from anon,authenticated;
grant select on public.ticketing_challenger_cv_predictions_v1 to service_role;

create or replace view public.dashboard_ticketing_challenger_v1
with (security_invoker=true)
as
select
  protocol,count(*)::int event_count,count(distinct club_slug)::int club_count,
  round(avg(abs(baseline_p50-actual_attendance)),1) baseline_mae,
  round(avg(abs(bias_only_p50-actual_attendance)),1) bias_control_mae,
  round(avg(abs(challenger_p50-actual_attendance)),1) challenger_mae,
  round(avg(abs(baseline_p50-actual_attendance))-avg(abs(challenger_p50-actual_attendance)),1) uplift_vs_baseline,
  round(avg(abs(bias_only_p50-actual_attendance))-avg(abs(challenger_p50-actual_attendance)),1) incremental_ticketing_uplift,
  round(avg(challenger_p50-actual_attendance),1) challenger_bias,
  'hybrid_v6_ridge_alpha30'::text candidate_model,
  case
    when count(*)<8 or count(distinct club_slug)<5 then 'insufficient_sample'
    when avg(abs(challenger_p50-actual_attendance))<avg(abs(bias_only_p50-actual_attendance))
     and avg(abs(challenger_p50-actual_attendance))<avg(abs(baseline_p50-actual_attendance)) then 'positive_research_signal'
    when avg(abs(challenger_p50-actual_attendance))>=avg(abs(baseline_p50-actual_attendance)) then 'no_uplift'
    else 'mixed_signal'
  end protocol_status
from public.ticketing_challenger_cv_predictions_v1
group by protocol;

revoke all on public.dashboard_ticketing_challenger_v1 from public;

create table if not exists public.ticketing_challenger_models_v1 (
  model_version text primary key,
  trained_at timestamptz not null default now(),
  horizon text not null default 'T-24h',
  feature_key text not null default 'hybrid_v6',
  ridge_alpha numeric not null,
  training_event_count integer not null,
  training_club_count integer not null,
  training_outcome_max_confirmed_at timestamptz,
  x_mean numeric not null,
  x_sd numeric not null,
  y_mean numeric not null,
  beta numeric not null,
  score_floor_ratio numeric not null default -0.25,
  score_ceiling_ratio numeric not null default 0.25,
  status text not null check (status in ('shadow_active','frozen','retired')),
  metadata jsonb not null default '{}'::jsonb
);

alter table public.ticketing_challenger_models_v1 enable row level security;
revoke all on public.ticketing_challenger_models_v1 from anon,authenticated;
grant select,insert,update,delete on public.ticketing_challenger_models_v1 to service_role;

insert into public.ticketing_challenger_models_v1(
  model_version,ridge_alpha,training_event_count,training_club_count,
  training_outcome_max_confirmed_at,x_mean,x_sd,y_mean,beta,status,metadata
)
with d as (select * from public.ticketing_challenger_dataset_v1),
b as (
  select count(*)::int n,count(distinct club_slug)::int clubs,avg(hybrid_v6) x_mean,
    stddev_pop(hybrid_v6) x_sd,avg(residual_ratio) y_mean,max(o.confirmed_at) max_confirmed
  from d join public.ticket_event_outcomes o on o.ticket_event_id=d.ticket_event_id
), fit as (
  select b.*,
    sum(((d.hybrid_v6-b.x_mean)/nullif(b.x_sd,0))*(d.residual_ratio-b.y_mean))
      /(sum(power((d.hybrid_v6-b.x_mean)/nullif(b.x_sd,0),2))+30.0) beta
  from d cross join b
  group by b.n,b.clubs,b.x_mean,b.x_sd,b.y_mean,b.max_confirmed
)
select 'ticketing-challenger-v1-t24-ridge-a30-20261013',30.0,n,clubs,max_confirmed,
  x_mean,x_sd,y_mean,beta,'shadow_active',
  jsonb_build_object(
    'feature_definition','matched velocity 6h pct-of-first per hour, raw velocity 6h fallback',
    'target','attendance residual ratio vs checkpoint baseline',
    'validation','leave-one-event-out and leave-one-club-out',
    'promotion','none; research shadow only','bias_control_required',true
  )
from fit
on conflict (model_version) do nothing;

insert into public.context_ablation_predictions_v1(
  snapshot_id,variant_key,predicted_p50,prediction_method,model_version,metadata
)
select p.snapshot_id,'baseline_ticketing',p.challenger_p50,
  'ticketing_challenger_v1_leave_one_club_out_cv','ticketing-challenger-v1-t24-ridge-a30-cv',
  jsonb_build_object(
    'protocol',p.protocol,'feature','hybrid_v6','feature_value',p.hybrid_v6,
    'feature_source',p.hybrid_v6_source,'training_events',p.n_train,
    'training_clubs',p.club_count_train,'bias_control_p50',p.bias_only_p50,'research_only',true
  )
from public.ticketing_challenger_cv_predictions_v1 p
where p.protocol='leave_one_club_out'
on conflict (snapshot_id,variant_key) do nothing;

create or replace view public.dashboard_ticketing_challenger_model_v1
with (security_invoker=true)
as
select model_version,trained_at,horizon,feature_key,ridge_alpha,training_event_count,
  training_club_count,status,round(y_mean*100.0,2) calibration_pct,round(beta,6) feature_beta
from public.ticketing_challenger_models_v1;

revoke all on public.dashboard_ticketing_challenger_model_v1 from public;
