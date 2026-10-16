-- C1 v8 Prospective Shadow Scoring v1
--
-- Scores only decisions that were already persisted in the append-only
-- pre-outcome evidence table. It never reconstructs a missing historical
-- decision after an outcome becomes known.

begin;

create table if not exists private.c1_shadow_v8_event_scores_v1 (
    id bigserial primary key,
    ticket_event_id bigint not null references public.ticket_events(id),
    package_version text not null,
    actual_attendance integer not null,
    outcome_confirmed_at timestamptz,
    outcome_version_at timestamptz not null,
    prediction_row_count integer not null check (prediction_row_count >= 1),
    representative_bucket_count integer not null check (representative_bucket_count >= 1 and representative_bucket_count <= 4),
    latest_prediction_id bigint not null references private.c1_shadow_v8_predictions_v1(id),
    latest_as_of_at timestamptz not null,
    latest_selected_expert text not null check (latest_selected_expert in ('PRIOR','LIVE')),
    latest_reason_code text not null,
    latest_prior_error numeric not null,
    latest_live_error numeric not null,
    latest_policy_error numeric not null,
    window_prior_mae numeric not null,
    window_live_mae numeric not null,
    window_policy_mae numeric not null,
    latest_policy_improves_prior boolean not null,
    window_policy_improves_prior boolean not null,
    metadata jsonb not null default '{}'::jsonb,
    scored_at timestamptz not null default now(),
    unique(ticket_event_id, package_version, outcome_version_at)
);

comment on table private.c1_shadow_v8_event_scores_v1 is
'Post-outcome scores derived only from frozen C1 v8 decisions persisted before the outcome existed. Corrections create a new outcome-version score; historical scores are not overwritten.';

create index if not exists c1_shadow_v8_event_scores_event_idx
    on private.c1_shadow_v8_event_scores_v1(ticket_event_id, scored_at);

revoke all on private.c1_shadow_v8_event_scores_v1 from public, anon, authenticated;
grant select, insert on private.c1_shadow_v8_event_scores_v1 to service_role;
grant usage, select on sequence private.c1_shadow_v8_event_scores_v1_id_seq to service_role;

create or replace function public.score_c1_shadow_v8_completed_events_v1(
    p_requested_at timestamptz default now()
)
returns jsonb
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
    v_inserted integer := 0;
    v_event_count integer := 0;
    v_prior_mae numeric;
    v_live_mae numeric;
    v_policy_mae numeric;
    v_window_prior_mae numeric;
    v_window_live_mae numeric;
    v_window_policy_mae numeric;
begin
    if p_requested_at is null or abs(extract(epoch from (now()-p_requested_at))) > 900 then
        raise exception 'C1 v8 scorer requested_at must be within 15 minutes of now()';
    end if;

    with prediction_outcomes as (
        select
            p.*,
            o.actual_attendance,
            o.confirmed_at as outcome_confirmed_at,
            coalesce(o.updated_at,o.confirmed_at,o.created_at) as outcome_version_at,
            floor(p.hours_to_kickoff/6.0)::integer as bucket_6h,
            row_number() over (
                partition by p.ticket_event_id,p.package_version,floor(p.hours_to_kickoff/6.0)::integer
                order by p.as_of_at desc,p.id desc
            ) as bucket_rn,
            row_number() over (
                partition by p.ticket_event_id,p.package_version
                order by p.as_of_at desc,p.id desc
            ) as latest_rn
        from private.c1_shadow_v8_predictions_v1 p
        join public.ticket_event_outcomes o
          on o.ticket_event_id=p.ticket_event_id
         and o.actual_attendance is not null
        where p.package_version='c1-shadow-v8-frozen-2026-10-16-n9'
    ), aggregated as (
        select
            ticket_event_id,
            package_version,
            actual_attendance,
            max(outcome_confirmed_at) as outcome_confirmed_at,
            max(outcome_version_at) as outcome_version_at,
            count(*)::integer as prediction_row_count,
            count(*) filter (where bucket_rn=1)::integer as representative_bucket_count,
            max(id) filter (where latest_rn=1) as latest_prediction_id,
            max(as_of_at) filter (where latest_rn=1) as latest_as_of_at,
            max(selected_expert) filter (where latest_rn=1) as latest_selected_expert,
            max(reason_code) filter (where latest_rn=1) as latest_reason_code,
            max(abs(structural_prior_p50-actual_attendance)) filter (where latest_rn=1) as latest_prior_error,
            max(abs(v2_live_p50-actual_attendance)) filter (where latest_rn=1) as latest_live_error,
            max(abs(policy_prediction-actual_attendance)) filter (where latest_rn=1) as latest_policy_error,
            avg(abs(structural_prior_p50-actual_attendance)) filter (where bucket_rn=1) as window_prior_mae,
            avg(abs(v2_live_p50-actual_attendance)) filter (where bucket_rn=1) as window_live_mae,
            avg(abs(policy_prediction-actual_attendance)) filter (where bucket_rn=1) as window_policy_mae
        from prediction_outcomes
        group by ticket_event_id,package_version,actual_attendance
    ), inserted as (
        insert into private.c1_shadow_v8_event_scores_v1(
            ticket_event_id,package_version,actual_attendance,outcome_confirmed_at,outcome_version_at,
            prediction_row_count,representative_bucket_count,latest_prediction_id,latest_as_of_at,
            latest_selected_expert,latest_reason_code,
            latest_prior_error,latest_live_error,latest_policy_error,
            window_prior_mae,window_live_mae,window_policy_mae,
            latest_policy_improves_prior,window_policy_improves_prior,metadata
        )
        select
            a.ticket_event_id,a.package_version,a.actual_attendance,a.outcome_confirmed_at,a.outcome_version_at,
            a.prediction_row_count,a.representative_bucket_count,a.latest_prediction_id,a.latest_as_of_at,
            a.latest_selected_expert,a.latest_reason_code,
            a.latest_prior_error,a.latest_live_error,a.latest_policy_error,
            a.window_prior_mae,a.window_live_mae,a.window_policy_mae,
            a.latest_policy_error<a.latest_prior_error,
            a.window_policy_mae<a.window_prior_mae,
            jsonb_build_object(
                'scoring_version','c1-shadow-v8-scoring-v1',
                'scoring_requested_at',p_requested_at,
                'representative_rule','latest persisted pre-outcome decision per 6h bucket',
                'prospective_only',true
            )
        from aggregated a
        on conflict(ticket_event_id,package_version,outcome_version_at) do nothing
        returning id
    )
    select count(*)::integer into v_inserted from inserted;

    with latest_scores as (
        select distinct on (ticket_event_id,package_version)
            *
        from private.c1_shadow_v8_event_scores_v1
        where package_version='c1-shadow-v8-frozen-2026-10-16-n9'
        order by ticket_event_id,package_version,outcome_version_at desc,id desc
    )
    select
        count(*)::integer,
        avg(latest_prior_error),
        avg(latest_live_error),
        avg(latest_policy_error),
        avg(window_prior_mae),
        avg(window_live_mae),
        avg(window_policy_mae)
    into
        v_event_count,
        v_prior_mae,
        v_live_mae,
        v_policy_mae,
        v_window_prior_mae,
        v_window_live_mae,
        v_window_policy_mae
    from latest_scores;

    return jsonb_build_object(
        'version','c1-shadow-v8-scoring-v1',
        'status','EXPERIMENTAL_SHADOW',
        'package_version','c1-shadow-v8-frozen-2026-10-16-n9',
        'inserted_score_count',v_inserted,
        'prospective_scored_event_count',coalesce(v_event_count,0),
        'latest_row_metrics',jsonb_build_object(
            'prior_mae',v_prior_mae,
            'live_mae',v_live_mae,
            'policy_mae',v_policy_mae
        ),
        'representative_window_metrics',jsonb_build_object(
            'prior_mae',v_window_prior_mae,
            'live_mae',v_window_live_mae,
            'policy_mae',v_window_policy_mae
        )
    );
end;
$function$;

revoke all on function public.score_c1_shadow_v8_completed_events_v1(timestamptz) from public, anon, authenticated;
grant execute on function public.score_c1_shadow_v8_completed_events_v1(timestamptz) to service_role;

commit;
