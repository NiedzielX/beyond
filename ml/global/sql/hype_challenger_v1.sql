-- Beyond Ticketing — Attention & Hype Challenger v1.
-- Prospective-only evaluation after Baseline + Ticketing.
-- Historical Hype backfill is explicitly prohibited.

create or replace view public.hype_challenger_dataset_v1 as
select
  s.id as snapshot_id,s.ticket_event_id,e.club_slug,e.home_team,e.away_team,e.kickoff_at,s.checkpoint_at,
  bt.predicted_p50 as baseline_ticketing_p50,o.actual_attendance,
  (o.actual_attendance-bt.predicted_p50)::numeric/nullif(bt.predicted_p50,0) as residual_ratio,
  nullif(s.context_features->'hype.media_attention'->>'numeric_value','')::numeric as media_attention,
  nullif(s.context_features->'hype.mention_acceleration'->>'numeric_value','')::numeric as mention_acceleration,
  s.context_features->'hype.media_attention'->>'source_name' as media_source_name,
  s.context_features->'hype.mention_acceleration'->>'source_name' as acceleration_source_name,
  nullif(s.context_features->'hype.media_attention'->>'source_observed_at','')::timestamptz as media_source_observed_at,
  nullif(s.context_features->'hype.mention_acceleration'->>'source_observed_at','')::timestamptz as acceleration_source_observed_at
from public.event_context_snapshots_v1 s
join public.ticket_events e on e.id=s.ticket_event_id
join public.context_ablation_predictions_v1 bt on bt.snapshot_id=s.id and bt.variant_key='baseline_ticketing'
join public.ticket_event_outcomes o on o.ticket_event_id=s.ticket_event_id
where s.checkpoint_code='T-24h'
  and s.capture_mode='prospective'
  and s.context_features->'hype.media_attention'->>'source_name'='GDELT Web News NGrams v2 broad event-team attention'
  and nullif(s.context_features->'hype.media_attention'->>'numeric_value','') is not null
  and nullif(s.context_features->'hype.media_attention'->>'source_observed_at','')::timestamptz<=s.checkpoint_at;

revoke all on public.hype_challenger_dataset_v1 from anon,authenticated;
grant select on public.hype_challenger_dataset_v1 to service_role;

create or replace view public.hype_challenger_cv_predictions_v1 as
with feature_long as (
  select snapshot_id,ticket_event_id,club_slug,baseline_ticketing_p50,actual_attendance,residual_ratio,
         'hype.media_attention'::text feature_key,media_attention feature_value
  from public.hype_challenger_dataset_v1 where media_attention is not null
  union all
  select snapshot_id,ticket_event_id,club_slug,baseline_ticketing_p50,actual_attendance,residual_ratio,
         'hype.mention_acceleration'::text,mention_acceleration
  from public.hype_challenger_dataset_v1
  where mention_acceleration is not null
    and acceleration_source_name='GDELT Web News NGrams v2 broad event-team attention'
), protocols as (
  select 'leave_one_event_out'::text protocol union all select 'leave_one_club_out'::text
), scored as (
  select d.feature_key,p.protocol,d.snapshot_id,d.ticket_event_id,d.club_slug,
    d.baseline_ticketing_p50,d.actual_attendance,d.feature_value,
    st.n_train,st.club_count_train,st.y_mean,st.beta,
    st.y_mean as bias_only_ratio,
    st.y_mean+st.beta*((d.feature_value-st.x_mean)/nullif(st.x_sd,0)) as challenger_ratio
  from feature_long d
  cross join protocols p
  cross join lateral (
    with tr as (
      select * from feature_long t
      where t.feature_key=d.feature_key
        and case when p.protocol='leave_one_event_out' then t.ticket_event_id<>d.ticket_event_id else t.club_slug<>d.club_slug end
    ), base as (
      select count(*)::int n_train,count(distinct club_slug)::int club_count_train,
        avg(feature_value) x_mean,stddev_pop(feature_value) x_sd,avg(residual_ratio) y_mean from tr
    )
    select b.n_train,b.club_count_train,b.x_mean,b.x_sd,b.y_mean,
      sum(((tr.feature_value-b.x_mean)/nullif(b.x_sd,0))*(tr.residual_ratio-b.y_mean))
        /(sum(power((tr.feature_value-b.x_mean)/nullif(b.x_sd,0),2))+30.0) beta
    from tr cross join base b
    group by b.n_train,b.club_count_train,b.x_mean,b.x_sd,b.y_mean
  ) st
  where st.n_train>=5 and st.club_count_train>=4 and st.x_sd>0
)
select feature_key,protocol,snapshot_id,ticket_event_id,club_slug,baseline_ticketing_p50,actual_attendance,
  feature_value,n_train,club_count_train,
  round((baseline_ticketing_p50*(1+bias_only_ratio))::numeric)::int bias_only_p50,
  round((baseline_ticketing_p50*(1+greatest(-0.25::numeric,least(0.25::numeric,challenger_ratio))))::numeric)::int challenger_p50,
  beta
from scored;

revoke all on public.hype_challenger_cv_predictions_v1 from anon,authenticated;
grant select on public.hype_challenger_cv_predictions_v1 to service_role;

create table if not exists public.hype_challenger_readiness_v1 (
  feature_key text primary key,
  readiness_status text not null,
  reason text not null,
  prospective_t24_count integer not null default 0,
  completed_eligible_count integer not null default 0,
  completed_club_count integer not null default 0,
  distinct_value_count integer not null default 0,
  evidence jsonb not null default '{}'::jsonb,
  refreshed_at timestamptz not null default now()
);

create table if not exists public.hype_challenger_summary_v1 (
  id boolean primary key default true check (id),
  collector_version text not null,
  collector_latest_sample_at timestamptz,
  collector_sample_rows integer not null default 0,
  collector_event_count integer not null default 0,
  collector_nonzero_event_count integer not null default 0,
  prospective_t24_count integer not null default 0,
  prospective_t24_club_count integer not null default 0,
  completed_media_eligible_count integer not null default 0,
  completed_media_club_count integer not null default 0,
  promotion_gate_event_target integer not null default 8,
  promotion_gate_club_target integer not null default 5,
  overall_status text not null,
  historical_backfill_allowed boolean not null default false,
  refreshed_at timestamptz not null default now()
);

create table if not exists public.hype_challenger_cv_summary_v1 (
  feature_key text not null,protocol text not null,event_count integer not null,club_count integer not null,
  baseline_ticketing_mae numeric,bias_control_mae numeric,challenger_mae numeric,
  uplift_vs_ticketing numeric,incremental_hype_uplift numeric,candidate_status text not null,
  refreshed_at timestamptz not null default now(),primary key(feature_key,protocol)
);

alter table public.hype_challenger_readiness_v1 enable row level security;
alter table public.hype_challenger_summary_v1 enable row level security;
alter table public.hype_challenger_cv_summary_v1 enable row level security;

grant select on public.hype_challenger_readiness_v1,public.hype_challenger_summary_v1,public.hype_challenger_cv_summary_v1 to anon,authenticated;
grant select,insert,update,delete on public.hype_challenger_readiness_v1,public.hype_challenger_summary_v1,public.hype_challenger_cv_summary_v1 to service_role;

create policy dashboard_hype_challenger_readiness_read on public.hype_challenger_readiness_v1 for select to anon,authenticated using (true);
create policy dashboard_hype_challenger_summary_read on public.hype_challenger_summary_v1 for select to anon,authenticated using (true);
create policy dashboard_hype_challenger_cv_read on public.hype_challenger_cv_summary_v1 for select to anon,authenticated using (true);

-- Runtime refresh function in production computes collector health, the 8-event / 5-club gate,
-- feature readiness for all six Hype features and prospective CV summaries. It intentionally
-- creates no ablation P50 rows; a positive research signal still requires explicit review.

create or replace view public.dashboard_hype_challenger_summary_v1 with (security_invoker=true)
as select * from public.hype_challenger_summary_v1;
create or replace view public.dashboard_hype_challenger_readiness_v1 with (security_invoker=true)
as select * from public.hype_challenger_readiness_v1;
create or replace view public.dashboard_hype_challenger_cv_v1 with (security_invoker=true)
as select * from public.hype_challenger_cv_summary_v1;

grant select on public.dashboard_hype_challenger_summary_v1,public.dashboard_hype_challenger_readiness_v1,public.dashboard_hype_challenger_cv_v1 to anon,authenticated,service_role;

-- Internal refresh cadence used in production:
-- cron.schedule('hype_challenger_summary_6h','23 */6 * * *',
--   $$select public.refresh_hype_challenger_v1();$$)
