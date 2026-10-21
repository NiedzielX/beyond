-- d2 Long72 Forward Prospective Evidence v1
--
-- Genuine post-freeze evidence path for the frozen Long72 P2 package.
-- Predictions are persisted before an outcome exists and are immutable.
-- Scoring only joins already-persisted predictions to later outcomes.

begin;

create table if not exists private.d2_long72_forward_predictions_v1 (
    id bigserial primary key,
    ticket_event_id bigint not null references public.ticket_events(id),
    source_prior_id bigint not null,
    source_snapshot_id bigint not null references public.snapshots(id),
    as_of_at timestamptz not null,
    run_requested_at timestamptz not null,
    kickoff_at timestamptz not null,
    hours_to_kickoff numeric not null check (hours_to_kickoff > 24 and hours_to_kickoff <= 72),
    bucket_6h integer not null,
    stadium_capacity integer not null check (stadium_capacity > 0),
    structural_t3_p50 numeric not null,
    b2_prior_home_matches integer not null check (b2_prior_home_matches >= 0),
    b2_ewma_residual_fraction numeric,
    b2_correction_seats numeric not null,
    anchor_p50 numeric not null,
    raw_inventory_delta_occupancy numeric not null,
    governed_delta_occupancy numeric not null check (abs(governed_delta_occupancy) <= 0.1000001),
    stage1_inventory_p50 numeric not null,
    stage2_observation_index integer not null check (stage2_observation_index >= 1),
    stage2_reliability numeric not null check (stage2_reliability >= 0 and stage2_reliability <= 1),
    final_p50 numeric not null,
    package_id text not null,
    stage1_expert_id text not null,
    stage2_policy_id text not null,
    package_manifest_sha256 text not null,
    feature_contract text not null,
    github_sha text,
    input_lineage jsonb not null default '{}'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique(ticket_event_id, source_snapshot_id, package_id)
);

comment on table private.d2_long72_forward_predictions_v1 is
'Immutable pre-outcome forecasts from frozen Long72 P2. Genuine prospective evidence only; production forecasts are untouched.';

create index if not exists d2_long72_forward_predictions_event_idx
    on private.d2_long72_forward_predictions_v1(ticket_event_id, as_of_at);

create table if not exists private.d2_long72_forward_event_scores_v1 (
    id bigserial primary key,
    ticket_event_id bigint not null references public.ticket_events(id),
    package_id text not null,
    actual_attendance integer not null,
    outcome_confirmed_at timestamptz,
    outcome_version_at timestamptz not null,
    representative_bucket_count integer not null check (representative_bucket_count >= 1),
    anchor_mae numeric not null,
    stage1_mae numeric not null,
    p2_mae numeric not null,
    p2_bias numeric not null,
    mae_24_48h numeric,
    anchor_mae_24_48h numeric,
    mae_48_72h numeric,
    anchor_mae_48_72h numeric,
    event_improves_anchor boolean not null,
    worst_row_degradation numeric not null,
    metadata jsonb not null default '{}'::jsonb,
    scored_at timestamptz not null default now(),
    unique(ticket_event_id, package_id, outcome_version_at)
);

comment on table private.d2_long72_forward_event_scores_v1 is
'Append-only post-outcome scores computed only from Long72 forecasts persisted before the outcome existed.';

create index if not exists d2_long72_forward_scores_event_idx
    on private.d2_long72_forward_event_scores_v1(ticket_event_id, scored_at);

create or replace function private.reject_d2_long72_evidence_mutation_v1()
returns trigger
language plpgsql
set search_path = private, public
as $function$
begin
    raise exception 'Long72 prospective evidence is append-only; % is not allowed', tg_op;
end;
$function$;

drop trigger if exists d2_long72_forward_predictions_immutable_v1
    on private.d2_long72_forward_predictions_v1;
create trigger d2_long72_forward_predictions_immutable_v1
before update or delete on private.d2_long72_forward_predictions_v1
for each row execute function private.reject_d2_long72_evidence_mutation_v1();

drop trigger if exists d2_long72_forward_scores_immutable_v1
    on private.d2_long72_forward_event_scores_v1;
create trigger d2_long72_forward_scores_immutable_v1
before update or delete on private.d2_long72_forward_event_scores_v1
for each row execute function private.reject_d2_long72_evidence_mutation_v1();

revoke all on private.d2_long72_forward_predictions_v1 from public, anon, authenticated;
revoke all on private.d2_long72_forward_event_scores_v1 from public, anon, authenticated;
grant select, insert on private.d2_long72_forward_predictions_v1 to service_role;
grant select, insert on private.d2_long72_forward_event_scores_v1 to service_role;
grant usage, select on sequence private.d2_long72_forward_predictions_v1_id_seq to service_role;
grant usage, select on sequence private.d2_long72_forward_event_scores_v1_id_seq to service_role;

create or replace function public.get_d2_long72_forward_inputs_v1(
    p_requested_at timestamptz default now()
)
returns jsonb
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
    v_payload jsonb;
begin
    if p_requested_at is null
       or abs(extract(epoch from (now() - p_requested_at))) > 900 then
        raise exception 'Long72 forward input is forward-only; p_requested_at must be within 15 minutes of now()';
    end if;

    with constants as (
        select
            'd2-long72-stage2-p2-observation-maturity-2026-10-21-v1'::text as package_id,
            '2026-10-21 17:37:07+00'::timestamptz as freeze_cutoff
    ), eligible as (
        select
            e.id as ticket_event_id,
            e.club_slug,
            e.home_team,
            e.away_team,
            e.competition,
            private.normalize_structural_prior_competition_v1(e.competition) as canonical_competition,
            e.kickoff_at,
            ha.club_key as home_club_key,
            aa.club_key as away_club_key,
            replace(f.season,'-','/') as season,
            f.round_number as round_no,
            cr.stadium_capacity,
            cr.source_name as capacity_source_name,
            cr.source_url as capacity_source_url,
            cr.verification_status as capacity_verification_status,
            c.package_id,
            c.freeze_cutoff
        from public.ticket_events e
        cross join constants c
        left join public.ticket_event_outcomes o
          on o.ticket_event_id=e.id and o.actual_attendance is not null
        left join private.structural_prior_club_aliases_v1 ha
          on ha.alias=e.home_team and ha.is_active
        left join private.structural_prior_club_aliases_v1 aa
          on aa.alias=e.away_team and aa.is_active
        left join lateral (
            select s.season,s.round_number
            from public.sporting_league_matches_shadow s
            left join private.structural_prior_club_aliases_v1 sh
              on sh.alias=s.home_team and sh.is_active
            left join private.structural_prior_club_aliases_v1 sa
              on sa.alias=s.away_team and sa.is_active
            where s.event_date=(e.kickoff_at at time zone 'Europe/Warsaw')::date
              and sh.club_key=ha.club_key
              and sa.club_key=aa.club_key
            order by s.fetched_at desc
            limit 1
        ) f on true
        left join lateral (
            select r.stadium_capacity,r.source_name,r.source_url,r.verification_status
            from private.structural_prior_capacity_registry_v1 r
            where r.club_key=ha.club_key
              and (e.kickoff_at at time zone 'Europe/Warsaw')::date>=r.valid_from
              and (r.valid_to is null or (e.kickoff_at at time zone 'Europe/Warsaw')::date<=r.valid_to)
            order by r.valid_from desc,r.id desc
            limit 1
        ) cr on true
        where e.kickoff_at>p_requested_at
          and e.kickoff_at>c.freeze_cutoff
          and o.ticket_event_id is null
          and private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
          and ha.club_key is not null
          and aa.club_key is not null
          and f.season is not null
          and f.round_number is not null
          and cr.stadium_capacity is not null
    ), candidates as (
        select
            s.id as requested_snapshot_id,
            s.ticket_event_id,
            s.captured_at as requested_as_of_at,
            e.kickoff_at,
            e.stadium_capacity,
            extract(epoch from (e.kickoff_at-s.captured_at))/3600.0 as hours_to_kickoff,
            floor(extract(epoch from (e.kickoff_at-s.captured_at))/21600.0)::integer as bucket_6h,
            row_number() over (
                partition by s.ticket_event_id,
                  floor(extract(epoch from (e.kickoff_at-s.captured_at))/21600.0)::integer
                order by s.captured_at desc,s.id desc
            ) as rn
        from public.snapshots s
        join eligible e on e.ticket_event_id=s.ticket_event_id
        where s.captured_at>=e.freeze_cutoff
          and s.captured_at<=p_requested_at
          and s.captured_at<e.kickoff_at
          and s.captured_at>=e.kickoff_at-interval '72 hours'
          and s.captured_at<e.kickoff_at-interval '24 hours'
    ), live_rows as (
        select
            c.ticket_event_id,
            c.requested_snapshot_id,
            c.requested_as_of_at,
            c.hours_to_kickoff,
            c.bucket_6h,
            to_jsonb(f) as features
        from candidates c
        cross join lateral public.get_live_trajectory_features_v1_1_asof(
            c.ticket_event_id,c.requested_as_of_at,c.stadium_capacity
        ) f
        where c.rn=1
          and coalesce(f.point_in_time_validated,false)
          and f.snapshot_id is not null
    ), latest_row as (
        select distinct on (ticket_event_id)
            ticket_event_id,requested_as_of_at
        from live_rows
        order by ticket_event_id,requested_as_of_at desc
    ), anchored as (
        select
            e.*,
            p.source_prior_id,
            p.horizon as prior_horizon,
            p.target_as_of_at as prior_target_as_of_at,
            p.model_spec_id as prior_model_spec_id,
            p.model_family as prior_model_family,
            p.feature_contract as prior_feature_contract,
            p.p50 as structural_t3_p50,
            p.generated_at as prior_generated_at,
            p.point_in_time_validated as prior_point_in_time_validated
        from eligible e
        join latest_row l on l.ticket_event_id=e.ticket_event_id
        cross join lateral public.get_structural_prior_v1(
            e.ticket_event_id,l.requested_as_of_at
        ) p
        where p.status='ready'
          and p.horizon='T-3'
          and coalesce(p.point_in_time_validated,false)
          and p.target_as_of_at<=l.requested_as_of_at
    ), event_payload as (
        select coalesce(jsonb_agg(
            jsonb_build_object(
                'ticket_event_id',a.ticket_event_id,
                'club_slug',a.club_slug,
                'home_team',a.home_team,
                'away_team',a.away_team,
                'competition',a.competition,
                'canonical_competition',a.canonical_competition,
                'kickoff_at',a.kickoff_at,
                'home_club_key',a.home_club_key,
                'away_club_key',a.away_club_key,
                'season',a.season,
                'round_no',a.round_no,
                'stadium_capacity',a.stadium_capacity,
                'capacity_source_name',a.capacity_source_name,
                'capacity_source_url',a.capacity_source_url,
                'capacity_verification_status',a.capacity_verification_status,
                'prior',jsonb_build_object(
                    'source_prior_id',a.source_prior_id,
                    'horizon',a.prior_horizon,
                    'target_as_of_at',a.prior_target_as_of_at,
                    'model_spec_id',a.prior_model_spec_id,
                    'model_family',a.prior_model_family,
                    'feature_contract',a.prior_feature_contract,
                    'p50',a.structural_t3_p50,
                    'generated_at',a.prior_generated_at,
                    'point_in_time_validated',a.prior_point_in_time_validated
                )
            ) order by a.kickoff_at,a.ticket_event_id
        ),'[]'::jsonb) as rows
        from anchored a
    ), live_payload as (
        select coalesce(jsonb_agg(to_jsonb(l)
            order by l.ticket_event_id,l.requested_as_of_at),'[]'::jsonb) as rows
        from live_rows l
        where exists (
            select 1 from anchored a where a.ticket_event_id=l.ticket_event_id
        )
    )
    select jsonb_build_object(
        'version','d2-long72-forward-inputs-v1',
        'requestedAt',p_requested_at,
        'packageId',(select package_id from constants),
        'packageFreezeCutoffAt',(select freeze_cutoff from constants),
        'outcomeAccessAllowed',false,
        'eventCount',jsonb_array_length((select rows from event_payload)),
        'liveRowCount',jsonb_array_length((select rows from live_payload)),
        'events',(select rows from event_payload),
        'liveRows',(select rows from live_payload)
    ) into v_payload;

    return v_payload;
end;
$function$;

revoke all on function public.get_d2_long72_forward_inputs_v1(timestamptz)
    from public, anon, authenticated;
grant execute on function public.get_d2_long72_forward_inputs_v1(timestamptz)
    to service_role;

create or replace function public.insert_d2_long72_forward_predictions_v1(
    p_rows jsonb,
    p_requested_at timestamptz default now()
)
returns jsonb
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
    v_package constant text := 'd2-long72-stage2-p2-observation-maturity-2026-10-21-v1';
    v_manifest_sha constant text := '2a523ae461a43a9d66e3870c836b56588eb582dd52513cfb9d8f638953f08872';
    v_row jsonb;
    v_event_id bigint;
    v_snapshot_id bigint;
    v_as_of timestamptz;
    v_kickoff timestamptz;
    v_hours numeric;
    v_bucket integer;
    v_capacity integer;
    v_reliability numeric;
    v_expected_reliability numeric;
    v_obs_index integer;
    v_anchor numeric;
    v_governed numeric;
    v_stage1 numeric;
    v_final numeric;
    v_db_snapshot_at timestamptz;
    v_db_kickoff timestamptz;
    v_db_capacity integer;
    v_prior record;
    v_inserted_id bigint;
    v_inserted integer := 0;
    v_duplicates integer := 0;
    v_results jsonb := '[]'::jsonb;
begin
    if p_rows is null or jsonb_typeof(p_rows)<>'array' then
        raise exception 'p_rows must be a JSON array';
    end if;
    if p_requested_at is null
       or abs(extract(epoch from (now()-p_requested_at)))>900 then
        raise exception 'Long72 forward write is forward-only; requested_at must be within 15 minutes of now()';
    end if;

    for v_row in select value from jsonb_array_elements(p_rows)
    loop
        if v_row->>'package_id'<>v_package
           or v_row->>'package_manifest_sha256'<>v_manifest_sha
           or v_row->>'stage1_expert_id'<>'inventory-linear-extrapolation'
           or v_row->>'stage2_policy_id'<>'P2-observation-maturity' then
            raise exception 'frozen package lineage mismatch';
        end if;

        v_event_id := (v_row->>'ticket_event_id')::bigint;
        v_snapshot_id := (v_row->>'source_snapshot_id')::bigint;
        v_as_of := (v_row->>'as_of_at')::timestamptz;
        v_kickoff := (v_row->>'kickoff_at')::timestamptz;
        v_hours := (v_row->>'hours_to_kickoff')::numeric;
        v_bucket := (v_row->>'bucket_6h')::integer;
        v_capacity := (v_row->>'stadium_capacity')::integer;
        v_obs_index := (v_row->>'stage2_observation_index')::integer;
        v_reliability := (v_row->>'stage2_reliability')::numeric;
        v_anchor := (v_row->>'anchor_p50')::numeric;
        v_governed := (v_row->>'governed_delta_occupancy')::numeric;
        v_stage1 := (v_row->>'stage1_inventory_p50')::numeric;
        v_final := (v_row->>'final_p50')::numeric;

        if not (v_hours>24 and v_hours<=72) then
            raise exception 'hours_to_kickoff outside frozen Long72 scope';
        end if;
        if v_bucket<>floor(v_hours/6.0)::integer then
            raise exception 'bucket_6h mismatch event %',v_event_id;
        end if;
        if abs(v_governed)>0.1000001 then
            raise exception 'governed correction exceeds frozen 10pp cap event %',v_event_id;
        end if;

        v_expected_reliability :=
            least(
                case when v_obs_index<=1 then 0.25 when v_obs_index=2 then 0.60 else 1.0 end,
                case when v_hours>60 then 0.75 when v_hours>48 then 0.90 else 1.0 end
            );
        if abs(v_reliability-v_expected_reliability)>0.000001 then
            raise exception 'P2 reliability mismatch event % actual % expected %',
                v_event_id,v_reliability,v_expected_reliability;
        end if;
        if abs(v_stage1-(v_anchor+v_governed*v_capacity))>0.02 then
            raise exception 'Stage1 forecast formula mismatch event %',v_event_id;
        end if;
        if abs(v_final-(v_anchor+v_reliability*v_governed*v_capacity))>0.02 then
            raise exception 'P2 forecast formula mismatch event %',v_event_id;
        end if;
        if v_anchor<0 or v_anchor>v_capacity
           or v_stage1<0 or v_stage1>v_capacity
           or v_final<0 or v_final>v_capacity then
            raise exception 'forecast outside physical capacity event %',v_event_id;
        end if;

        select e.kickoff_at into v_db_kickoff
        from public.ticket_events e
        where e.id=v_event_id
          and private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa';
        if v_db_kickoff is null or v_db_kickoff<>v_kickoff or v_kickoff<=p_requested_at then
            raise exception 'event/kickoff is not forward eligible event %',v_event_id;
        end if;

        if exists (
            select 1 from public.ticket_event_outcomes o
            where o.ticket_event_id=v_event_id and o.actual_attendance is not null
        ) then
            raise exception 'outcome already exists; prospective write rejected event %',v_event_id;
        end if;

        select s.captured_at into v_db_snapshot_at
        from public.snapshots s
        where s.id=v_snapshot_id and s.ticket_event_id=v_event_id;
        if v_db_snapshot_at is null or v_db_snapshot_at<>v_as_of then
            raise exception 'snapshot/as_of lineage mismatch event %',v_event_id;
        end if;
        if v_as_of<'2026-10-21 17:37:07+00'::timestamptz
           or v_as_of>p_requested_at
           or v_as_of>=v_kickoff then
            raise exception 'non-forward snapshot event %',v_event_id;
        end if;
        if abs(v_hours-extract(epoch from (v_kickoff-v_as_of))/3600.0)>0.001 then
            raise exception 'hours_to_kickoff lineage mismatch event %',v_event_id;
        end if;

        select r.stadium_capacity into v_db_capacity
        from public.ticket_events e
        join private.structural_prior_club_aliases_v1 a
          on a.alias=e.home_team and a.is_active
        join private.structural_prior_capacity_registry_v1 r
          on r.club_key=a.club_key
        where e.id=v_event_id
          and (e.kickoff_at at time zone 'Europe/Warsaw')::date>=r.valid_from
          and (r.valid_to is null or (e.kickoff_at at time zone 'Europe/Warsaw')::date<=r.valid_to)
        order by r.valid_from desc,r.id desc
        limit 1;
        if v_db_capacity is null or v_db_capacity<>v_capacity then
            raise exception 'verified capacity mismatch event %',v_event_id;
        end if;

        select * into v_prior
        from public.get_structural_prior_v1(v_event_id,v_as_of)
        limit 1;
        if v_prior.status is distinct from 'ready'
           or v_prior.horizon is distinct from 'T-3'
           or not coalesce(v_prior.point_in_time_validated,false)
           or v_prior.source_prior_id is distinct from (v_row->>'source_prior_id')::bigint
           or abs(v_prior.p50-(v_row->>'structural_t3_p50')::numeric)>0.02
           or v_prior.target_as_of_at>v_as_of then
            raise exception 'T-3 Structural Prior verification failed event %',v_event_id;
        end if;

        v_inserted_id := null;
        insert into private.d2_long72_forward_predictions_v1(
            ticket_event_id,source_prior_id,source_snapshot_id,as_of_at,run_requested_at,
            kickoff_at,hours_to_kickoff,bucket_6h,stadium_capacity,
            structural_t3_p50,b2_prior_home_matches,b2_ewma_residual_fraction,b2_correction_seats,
            anchor_p50,raw_inventory_delta_occupancy,governed_delta_occupancy,
            stage1_inventory_p50,stage2_observation_index,stage2_reliability,final_p50,
            package_id,stage1_expert_id,stage2_policy_id,package_manifest_sha256,
            feature_contract,github_sha,input_lineage,metadata
        ) values (
            v_event_id,(v_row->>'source_prior_id')::bigint,v_snapshot_id,v_as_of,p_requested_at,
            v_kickoff,v_hours,v_bucket,v_capacity,
            (v_row->>'structural_t3_p50')::numeric,
            (v_row->>'b2_prior_home_matches')::integer,
            nullif(v_row->>'b2_ewma_residual_fraction','')::numeric,
            (v_row->>'b2_correction_seats')::numeric,
            v_anchor,(v_row->>'raw_inventory_delta_occupancy')::numeric,v_governed,
            v_stage1,v_obs_index,v_reliability,v_final,
            v_package,v_row->>'stage1_expert_id',v_row->>'stage2_policy_id',v_manifest_sha,
            v_row->>'feature_contract',nullif(v_row->>'github_sha',''),
            coalesce(v_row->'input_lineage','{}'::jsonb),
            coalesce(v_row->'metadata','{}'::jsonb)
        )
        on conflict(ticket_event_id,source_snapshot_id,package_id) do nothing
        returning id into v_inserted_id;

        if v_inserted_id is null then
            v_duplicates := v_duplicates+1;
            select id into v_inserted_id
            from private.d2_long72_forward_predictions_v1
            where ticket_event_id=v_event_id
              and source_snapshot_id=v_snapshot_id
              and package_id=v_package;
            v_results := v_results || jsonb_build_array(jsonb_build_object(
                'ticket_event_id',v_event_id,'source_snapshot_id',v_snapshot_id,
                'status','duplicate','prediction_id',v_inserted_id
            ));
        else
            v_inserted := v_inserted+1;
            v_results := v_results || jsonb_build_array(jsonb_build_object(
                'ticket_event_id',v_event_id,'source_snapshot_id',v_snapshot_id,
                'status','inserted','prediction_id',v_inserted_id
            ));
        end if;
    end loop;

    return jsonb_build_object(
        'version','d2-long72-forward-write-v1',
        'package_id',v_package,
        'requested_at',p_requested_at,
        'inserted_count',v_inserted,
        'duplicate_count',v_duplicates,
        'results',v_results,
        'production_change',false
    );
end;
$function$;

revoke all on function public.insert_d2_long72_forward_predictions_v1(jsonb,timestamptz)
    from public, anon, authenticated;
grant execute on function public.insert_d2_long72_forward_predictions_v1(jsonb,timestamptz)
    to service_role;

create or replace function public.score_d2_long72_forward_completed_events_v1(
    p_requested_at timestamptz default now()
)
returns jsonb
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
    v_package constant text := 'd2-long72-stage2-p2-observation-maturity-2026-10-21-v1';
    v_inserted integer := 0;
    v_event_count integer := 0;
    v_anchor_mae numeric;
    v_p2_mae numeric;
    v_p2_bias numeric;
    v_improvement_rate numeric;
    v_worst_degradation numeric;
    v_anchor_24_48 numeric;
    v_p2_24_48 numeric;
    v_anchor_48_72 numeric;
    v_p2_48_72 numeric;
begin
    if p_requested_at is null
       or abs(extract(epoch from (now()-p_requested_at)))>900 then
        raise exception 'Long72 scorer requested_at must be within 15 minutes of now()';
    end if;

    with joined as (
        select
            p.*,
            o.actual_attendance,
            o.confirmed_at as outcome_confirmed_at,
            coalesce(o.updated_at,o.confirmed_at,o.created_at) as outcome_version_at,
            row_number() over (
                partition by p.ticket_event_id,p.package_id,p.bucket_6h
                order by p.as_of_at desc,p.id desc
            ) as bucket_rn
        from private.d2_long72_forward_predictions_v1 p
        join public.ticket_event_outcomes o
          on o.ticket_event_id=p.ticket_event_id
         and o.actual_attendance is not null
        where p.package_id=v_package
    ), representative as (
        select *
        from joined
        where bucket_rn=1
    ), event_agg as (
        select
            ticket_event_id,
            package_id,
            actual_attendance,
            max(outcome_confirmed_at) as outcome_confirmed_at,
            max(outcome_version_at) as outcome_version_at,
            count(*)::integer as representative_bucket_count,
            avg(abs(anchor_p50-actual_attendance)) as anchor_mae,
            avg(abs(stage1_inventory_p50-actual_attendance)) as stage1_mae,
            avg(abs(final_p50-actual_attendance)) as p2_mae,
            avg(final_p50-actual_attendance) as p2_bias,
            avg(abs(final_p50-actual_attendance))
              filter (where hours_to_kickoff>24 and hours_to_kickoff<=48) as mae_24_48h,
            avg(abs(anchor_p50-actual_attendance))
              filter (where hours_to_kickoff>24 and hours_to_kickoff<=48) as anchor_mae_24_48h,
            avg(abs(final_p50-actual_attendance))
              filter (where hours_to_kickoff>48 and hours_to_kickoff<=72) as mae_48_72h,
            avg(abs(anchor_p50-actual_attendance))
              filter (where hours_to_kickoff>48 and hours_to_kickoff<=72) as anchor_mae_48_72h,
            max(greatest(
                0,
                abs(final_p50-actual_attendance)-abs(anchor_p50-actual_attendance)
            )) as worst_row_degradation
        from representative
        group by ticket_event_id,package_id,actual_attendance
    ), inserted as (
        insert into private.d2_long72_forward_event_scores_v1(
            ticket_event_id,package_id,actual_attendance,outcome_confirmed_at,outcome_version_at,
            representative_bucket_count,anchor_mae,stage1_mae,p2_mae,p2_bias,
            mae_24_48h,anchor_mae_24_48h,mae_48_72h,anchor_mae_48_72h,
            event_improves_anchor,worst_row_degradation,metadata
        )
        select
            a.ticket_event_id,a.package_id,a.actual_attendance,a.outcome_confirmed_at,a.outcome_version_at,
            a.representative_bucket_count,a.anchor_mae,a.stage1_mae,a.p2_mae,a.p2_bias,
            a.mae_24_48h,a.anchor_mae_24_48h,a.mae_48_72h,a.anchor_mae_48_72h,
            a.p2_mae<a.anchor_mae,a.worst_row_degradation,
            jsonb_build_object(
                'scoring_version','d2-long72-forward-scoring-v1',
                'scoring_requested_at',p_requested_at,
                'representative_rule','latest persisted pre-outcome forecast per event x 6h bucket',
                'prospective_only',true
            )
        from event_agg a
        on conflict(ticket_event_id,package_id,outcome_version_at) do nothing
        returning id
    )
    select count(*)::integer into v_inserted from inserted;

    with latest_scores as (
        select distinct on (ticket_event_id,package_id)
            *
        from private.d2_long72_forward_event_scores_v1
        where package_id=v_package
        order by ticket_event_id,package_id,outcome_version_at desc,id desc
    )
    select
        count(*)::integer,
        avg(anchor_mae),
        avg(p2_mae),
        avg(p2_bias),
        avg(case when event_improves_anchor then 1.0 else 0.0 end),
        max(greatest(0,p2_mae-anchor_mae)),
        avg(anchor_mae_24_48h) filter (where anchor_mae_24_48h is not null),
        avg(mae_24_48h) filter (where mae_24_48h is not null),
        avg(anchor_mae_48_72h) filter (where anchor_mae_48_72h is not null),
        avg(mae_48_72h) filter (where mae_48_72h is not null)
    into
        v_event_count,v_anchor_mae,v_p2_mae,v_p2_bias,v_improvement_rate,v_worst_degradation,
        v_anchor_24_48,v_p2_24_48,v_anchor_48_72,v_p2_48_72
    from latest_scores;

    return jsonb_build_object(
        'version','d2-long72-forward-scoring-v1',
        'package_id',v_package,
        'inserted_score_count',v_inserted,
        'prospective_scored_event_count',coalesce(v_event_count,0),
        'overall_24_72h',jsonb_build_object(
            'anchor_event_balanced_mae',v_anchor_mae,
            'package_event_balanced_mae',v_p2_mae,
            'mae_improvement',case when v_anchor_mae is null or v_p2_mae is null then null else v_anchor_mae-v_p2_mae end,
            'relative_mae_improvement',case when coalesce(v_anchor_mae,0)>0 then (v_anchor_mae-v_p2_mae)/v_anchor_mae else null end,
            'event_balanced_bias',v_p2_bias,
            'event_improvement_rate',v_improvement_rate,
            'worst_event_degradation',v_worst_degradation
        ),
        'band_24_48h',jsonb_build_object(
            'anchor_mae',v_anchor_24_48,
            'package_mae',v_p2_24_48,
            'mae_improvement',case when v_anchor_24_48 is null or v_p2_24_48 is null then null else v_anchor_24_48-v_p2_24_48 end
        ),
        'band_48_72h',jsonb_build_object(
            'anchor_mae',v_anchor_48_72,
            'package_mae',v_p2_48_72,
            'mae_improvement',case when v_anchor_48_72 is null or v_p2_48_72 is null then null else v_anchor_48_72-v_p2_48_72 end
        ),
        'production_change',false
    );
end;
$function$;

revoke all on function public.score_d2_long72_forward_completed_events_v1(timestamptz)
    from public, anon, authenticated;
grant execute on function public.score_d2_long72_forward_completed_events_v1(timestamptz)
    to service_role;

-- Preserve the two already-materialized genuine post-freeze checkpoints from
-- public.forecast_observations (created before their outcomes existed).
insert into private.d2_long72_forward_predictions_v1(
    ticket_event_id,source_prior_id,source_snapshot_id,as_of_at,run_requested_at,
    kickoff_at,hours_to_kickoff,bucket_6h,stadium_capacity,
    structural_t3_p50,b2_prior_home_matches,b2_ewma_residual_fraction,b2_correction_seats,
    anchor_p50,raw_inventory_delta_occupancy,governed_delta_occupancy,
    stage1_inventory_p50,stage2_observation_index,stage2_reliability,final_p50,
    package_id,stage1_expert_id,stage2_policy_id,package_manifest_sha256,
    feature_contract,github_sha,input_lineage,metadata
)
select
    fo.ticket_event_id,
    (fo.payload->>'source_prior_id')::bigint,
    fo.source_snapshot_id,
    fo.source_snapshot_captured_at,
    fo.forecast_generated_at,
    (fo.payload->>'kickoff_at')::timestamptz,
    fo.hours_to_kickoff,
    (fo.payload->>'bucket_6h')::integer,
    (fo.payload->>'stadium_capacity')::integer,
    (fo.payload->>'anchor_base_p50')::numeric,
    (fo.payload->>'b2_prior_home_matches')::integer,
    null,
    (fo.payload->>'b2_correction_seats')::numeric,
    (fo.payload->>'anchor_p50')::numeric,
    (fo.payload->>'raw_inventory_delta_occupancy')::numeric,
    (fo.payload->>'governed_delta_occupancy')::numeric,
    (fo.payload->>'stage1_inventory_p50')::numeric,
    (fo.payload->>'stage2_observation_index')::integer,
    (fo.payload->>'reliability')::numeric,
    (fo.payload->>'final_p50')::numeric,
    fo.model_version,
    fo.payload->>'stage1_expert_id',
    fo.payload->>'stage2_policy_id',
    '2a523ae461a43a9d66e3870c836b56588eb582dd52513cfb9d8f638953f08872',
    'live-trajectory-v1.1',
    null,
    jsonb_build_object(
        'migrated_from_forecast_observation_id',fo.id,
        'evidence_class','true_post_freeze_prospective',
        'source_snapshot_captured_at',fo.source_snapshot_captured_at
    ),
    coalesce(fo.payload,'{}'::jsonb) || jsonb_build_object(
        'migration','d2-long72-forward-prospective-v1',
        'manual_first_checkpoint',true
    )
from public.forecast_observations fo
where fo.model_version='d2-long72-stage2-p2-observation-maturity-2026-10-21-v1'
  and fo.forecast_status='shadow'
  and fo.correction_status='frozen_long72_p2_research'
  and fo.payload->>'evidence_class'='true_post_freeze_prospective'
on conflict(ticket_event_id,source_snapshot_id,package_id) do nothing;

commit;
