-- Beyond Ticketing — Sporting Challenger v1.
-- First candidate: Match Stakes added after Baseline + Ticketing at T-24h.
-- Historical evidence is reconstructed only from league matches played before target date.
-- Prospective evaluation prefers the immutable snapshot value when available.
-- Current candidate is research-only and rejected because it did not improve MAE.

create or replace view public.sporting_stakes_reconstruction_v1 as
with targets as (
  select
    s.id as snapshot_id,
    s.ticket_event_id,
    e.club_slug,
    e.home_team,
    e.away_team,
    e.kickoff_at,
    s.checkpoint_at,
    s.capture_mode,
    bt.predicted_p50 as baseline_ticketing_p50,
    o.actual_attendance,
    (o.actual_attendance-bt.predicted_p50)::numeric/nullif(bt.predicted_p50,0) as residual_ratio,
    nullif(s.context_features->'sport.match_stakes'->>'numeric_value','')::numeric as snapshot_stakes_score,
    s.context_features->'sport.match_stakes'->>'status' as snapshot_stakes_status
  from public.event_context_snapshots_v1 s
  join public.ticket_events e on e.id=s.ticket_event_id
  join public.context_ablation_predictions_v1 bt
    on bt.snapshot_id=s.id and bt.variant_key='baseline_ticketing'
  join public.ticket_event_outcomes o on o.ticket_event_id=s.ticket_event_id
  where s.checkpoint_code='T-24h'
    and public.match_competition_key_v1(e.competition)='ekstraklasa'
), match_rows as (
  select
    t.snapshot_id,
    public.sporting_canonical_team_v1(m.home_team) as team_key,
    case when m.home_score>m.away_score then 3 when m.home_score=m.away_score then 1 else 0 end as points,
    m.home_score as goals_for,
    m.away_score as goals_against,
    1 as played
  from targets t
  join public.sporting_league_matches_shadow m
    on m.league_id='4422'
   and m.season='2026-2027'
   and m.completed=true
   and m.event_date < (t.kickoff_at at time zone 'Europe/Warsaw')::date
  union all
  select
    t.snapshot_id,
    public.sporting_canonical_team_v1(m.away_team),
    case when m.away_score>m.home_score then 3 when m.away_score=m.home_score then 1 else 0 end,
    m.away_score,
    m.home_score,
    1
  from targets t
  join public.sporting_league_matches_shadow m
    on m.league_id='4422'
   and m.season='2026-2027'
   and m.completed=true
   and m.event_date < (t.kickoff_at at time zone 'Europe/Warsaw')::date
), team_stats as (
  select
    snapshot_id,
    team_key,
    sum(points)::int as points,
    sum(played)::int as played,
    sum(goals_for)::int as goals_for,
    sum(goals_against)::int as goals_against,
    (sum(goals_for)-sum(goals_against))::int as goal_difference
  from match_rows
  group by snapshot_id,team_key
), ranked as (
  select
    *,
    row_number() over(
      partition by snapshot_id
      order by points desc,goal_difference desc,goals_for desc,team_key
    )::int as rank
  from team_stats
), joined as (
  select
    t.*,
    h.rank as home_rank,
    a.rank as away_rank,
    h.points as home_points,
    a.points as away_points,
    h.played as home_played,
    a.played as away_played
  from targets t
  left join ranked h
    on h.snapshot_id=t.snapshot_id
   and h.team_key=public.sporting_canonical_team_v1(t.home_team)
  left join ranked a
    on a.snapshot_id=t.snapshot_id
   and a.team_key=public.sporting_canonical_team_v1(t.away_team)
), components as (
  select
    j.*,
    ((home_played+away_played)/2.0)/34.0 as progress,
    case
      when home_rank<=2 then 15.0
      when home_rank<=4 then 12.0
      when home_rank>=16 then 15.0
      when home_rank<=6 or home_rank>=14 then 6.0
      else 3.0
    end as home_zone_component
  from joined j
), reconstructed as (
  select
    c.*,
    case
      when home_rank is null or away_rank is null then null
      else round(least(100.0,greatest(0.0,
        20.0
        + 25.0*least(greatest(progress,0.0),1.0)
        + home_zone_component
        + case
            when abs(home_points-away_points)<=3 and abs(home_rank-away_rank)<=3 then 10.0
            when abs(home_points-away_points)<=6 and abs(home_rank-away_rank)<=5 then 5.0
            else 0.0
          end
        + case
            when progress>=0.75 and home_zone_component>=12.0
              then 15.0*((progress-0.75)/0.25)
            else 0.0
          end
      )),1)::numeric
    end as reconstructed_stakes_score
  from components c
)
select
  snapshot_id,
  ticket_event_id,
  club_slug,
  home_team,
  away_team,
  kickoff_at,
  checkpoint_at,
  capture_mode,
  baseline_ticketing_p50,
  actual_attendance,
  residual_ratio,
  case
    when capture_mode='prospective' and snapshot_stakes_status='observed' and snapshot_stakes_score is not null
      then snapshot_stakes_score
    else reconstructed_stakes_score
  end as stakes_score,
  case
    when capture_mode='prospective' and snapshot_stakes_status='observed' and snapshot_stakes_score is not null
      then 'prospective_snapshot_observation'
    else 'retrospective_historical_fact_reconstruction'
  end as stakes_evidence_mode,
  home_rank,
  away_rank,
  home_points,
  away_points,
  home_played,
  away_played
from reconstructed
where (
  capture_mode='prospective' and snapshot_stakes_status='observed' and snapshot_stakes_score is not null
) or reconstructed_stakes_score is not null;

revoke all on public.sporting_stakes_reconstruction_v1 from anon,authenticated;
grant select on public.sporting_stakes_reconstruction_v1 to service_role;

create or replace view public.sporting_challenger_cv_predictions_v1 as
with protocols as (
  select 'leave_one_event_out'::text as protocol
  union all
  select 'leave_one_club_out'::text
), scored as (
  select
    p.protocol,
    d.snapshot_id,
    d.ticket_event_id,
    d.club_slug,
    d.home_team,
    d.away_team,
    d.baseline_ticketing_p50,
    d.actual_attendance,
    d.stakes_score,
    d.stakes_evidence_mode,
    st.n_train,
    st.club_count_train,
    st.x_mean,
    st.x_sd,
    st.y_mean,
    st.beta,
    st.y_mean as bias_only_ratio,
    st.y_mean + st.beta*((d.stakes_score-st.x_mean)/nullif(st.x_sd,0)) as challenger_ratio
  from public.sporting_stakes_reconstruction_v1 d
  cross join protocols p
  cross join lateral (
    with tr as (
      select *
      from public.sporting_stakes_reconstruction_v1 t
      where case
        when p.protocol='leave_one_event_out' then t.ticket_event_id<>d.ticket_event_id
        else t.club_slug<>d.club_slug
      end
    ), base as (
      select
        count(*)::int as n_train,
        count(distinct club_slug)::int as club_count_train,
        avg(stakes_score) as x_mean,
        stddev_pop(stakes_score) as x_sd,
        avg(residual_ratio) as y_mean
      from tr
    )
    select
      b.n_train,
      b.club_count_train,
      b.x_mean,
      b.x_sd,
      b.y_mean,
      sum(((tr.stakes_score-b.x_mean)/nullif(b.x_sd,0))*(tr.residual_ratio-b.y_mean))
        /(sum(power((tr.stakes_score-b.x_mean)/nullif(b.x_sd,0),2))+30.0) as beta
    from tr cross join base b
    group by b.n_train,b.club_count_train,b.x_mean,b.x_sd,b.y_mean
  ) st
  where st.n_train>=5 and st.x_sd>0
)
select
  protocol,
  snapshot_id,
  ticket_event_id,
  club_slug,
  home_team,
  away_team,
  baseline_ticketing_p50,
  actual_attendance,
  stakes_score,
  stakes_evidence_mode,
  n_train,
  club_count_train,
  x_mean,
  x_sd,
  y_mean,
  beta,
  round((baseline_ticketing_p50*(1+bias_only_ratio))::numeric)::int as bias_only_p50,
  round((baseline_ticketing_p50*(1+greatest(-0.25::numeric,least(0.25::numeric,challenger_ratio))))::numeric)::int as challenger_p50,
  challenger_ratio
from scored;

revoke all on public.sporting_challenger_cv_predictions_v1 from anon,authenticated;
grant select on public.sporting_challenger_cv_predictions_v1 to service_role;

create table if not exists public.sporting_challenger_candidates_v1 (
  candidate_version text primary key,
  created_at timestamptz not null default now(),
  checkpoint_code text not null,
  feature_key text not null,
  model_family text not null,
  ridge_alpha numeric not null,
  status text not null check (status in ('research_active','rejected_current_candidate','promoted','retired')),
  reason text not null,
  metadata jsonb not null default '{}'::jsonb
);

alter table public.sporting_challenger_candidates_v1 enable row level security;
revoke all on public.sporting_challenger_candidates_v1 from anon,authenticated;
grant select,insert,update,delete on public.sporting_challenger_candidates_v1 to service_role;

insert into public.sporting_challenger_candidates_v1(
  candidate_version,checkpoint_code,feature_key,model_family,ridge_alpha,status,reason,metadata
)
values (
  'sporting-challenger-v1-t24-stakes-ridge-a30-20261013',
  'T-24h',
  'sport.match_stakes',
  'one_feature_ridge_on_ticketing_residual',
  30.0,
  'rejected_current_candidate',
  'Match Stakes did not improve MAE over Baseline + Ticketing or bias-only control in leave-one-club-out validation.',
  jsonb_build_object(
    'historical_evidence','retrospective standings reconstruction using completed league matches strictly before target local match date',
    'prospective_evidence','snapshot sport.match_stakes observation when available',
    'production_impact','none',
    'ablation_prediction_created',false
  )
)
on conflict (candidate_version) do nothing;

create table if not exists public.sporting_challenger_dashboard_summary_v1 (
  protocol text primary key,
  event_count integer not null,
  club_count integer not null,
  baseline_ticketing_mae numeric,
  bias_control_mae numeric,
  challenger_mae numeric,
  uplift_vs_ticketing numeric,
  incremental_sporting_uplift numeric,
  challenger_bias numeric,
  candidate_model text,
  protocol_status text,
  refreshed_at timestamptz not null default now()
);

alter table public.sporting_challenger_dashboard_summary_v1 enable row level security;
revoke all on public.sporting_challenger_dashboard_summary_v1 from anon,authenticated;
grant select on public.sporting_challenger_dashboard_summary_v1 to anon,authenticated;
grant select,insert,update,delete on public.sporting_challenger_dashboard_summary_v1 to service_role;

drop policy if exists dashboard_sporting_challenger_summary_read on public.sporting_challenger_dashboard_summary_v1;
create policy dashboard_sporting_challenger_summary_read
on public.sporting_challenger_dashboard_summary_v1
for select to anon,authenticated
using (true);

create or replace function public.refresh_sporting_challenger_dashboard_v1()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare
  v_rows integer := 0;
begin
  delete from public.sporting_challenger_dashboard_summary_v1;

  insert into public.sporting_challenger_dashboard_summary_v1(
    protocol,event_count,club_count,baseline_ticketing_mae,bias_control_mae,challenger_mae,
    uplift_vs_ticketing,incremental_sporting_uplift,challenger_bias,candidate_model,
    protocol_status,refreshed_at
  )
  select
    protocol,
    count(*)::int,
    count(distinct club_slug)::int,
    round(avg(abs(baseline_ticketing_p50-actual_attendance)),1),
    round(avg(abs(bias_only_p50-actual_attendance)),1),
    round(avg(abs(challenger_p50-actual_attendance)),1),
    round(avg(abs(baseline_ticketing_p50-actual_attendance))-avg(abs(challenger_p50-actual_attendance)),1),
    round(avg(abs(bias_only_p50-actual_attendance))-avg(abs(challenger_p50-actual_attendance)),1),
    round(avg(challenger_p50-actual_attendance),1),
    'match_stakes_ridge_alpha30',
    case
      when count(*)<8 or count(distinct club_slug)<5 then 'insufficient_sample'
      when avg(abs(challenger_p50-actual_attendance)) < avg(abs(bias_only_p50-actual_attendance))
       and avg(abs(challenger_p50-actual_attendance)) < avg(abs(baseline_ticketing_p50-actual_attendance))
        then 'positive_research_signal'
      when avg(abs(challenger_p50-actual_attendance)) >= avg(abs(baseline_ticketing_p50-actual_attendance))
        then 'rejected_no_uplift'
      else 'mixed_signal'
    end,
    now()
  from public.sporting_challenger_cv_predictions_v1
  group by protocol;

  get diagnostics v_rows=row_count;
  return v_rows;
end;
$$;

revoke all on function public.refresh_sporting_challenger_dashboard_v1() from public,anon,authenticated;
grant execute on function public.refresh_sporting_challenger_dashboard_v1() to service_role;

select public.refresh_sporting_challenger_dashboard_v1();

create or replace view public.dashboard_sporting_challenger_v1
with (security_invoker=true)
as
select
  protocol,event_count,club_count,baseline_ticketing_mae,bias_control_mae,challenger_mae,
  uplift_vs_ticketing,incremental_sporting_uplift,challenger_bias,candidate_model,
  protocol_status,refreshed_at
from public.sporting_challenger_dashboard_summary_v1;

revoke all on public.dashboard_sporting_challenger_v1 from public;
grant select on public.dashboard_sporting_challenger_v1 to anon,authenticated,service_role;

do $$
declare v_job bigint;
begin
  select jobid into v_job from cron.job where jobname='sporting_challenger_summary_6h';
  if v_job is not null then perform cron.unschedule(v_job); end if;
end $$;

select cron.schedule(
  'sporting_challenger_summary_6h','11 */6 * * *',
  $$select public.refresh_sporting_challenger_dashboard_v1();$$
);
