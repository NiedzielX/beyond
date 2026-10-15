-- Structural Prior v1 scope hardening.
-- Current global historical champions are validated on Ekstraklasa only.

alter table private.structural_prior_model_specs_v1
  add column if not exists validated_competitions text[] not null default array['Ekstraklasa']::text[];

update private.structural_prior_model_specs_v1
set validated_competitions=array['Ekstraklasa']::text[]
where horizon in ('T-30','T-14','T-7','T-3','T-1');

-- Keep the existing view column order stable; append the new scope column.
create or replace view private.current_structural_prior_model_specs_v1 as
select horizon,target_days_before,model_spec_id,model_family,feature_contract,
       validation_report,status,activated_at,notes,validated_competitions
from private.structural_prior_model_specs_v1
where is_current;

create or replace function public.get_structural_prior_v1(
    p_ticket_event_id bigint,
    p_requested_as_of_at timestamptz
)
returns table(
    status text,
    source_prior_id bigint,
    ticket_event_id bigint,
    horizon text,
    requested_as_of_at timestamptz,
    target_as_of_at timestamptz,
    kickoff_at timestamptz,
    model_spec_id text,
    model_family text,
    feature_contract text,
    p50 numeric,
    p10 numeric,
    p90 numeric,
    stadium_capacity integer,
    expected_occupancy numeric,
    point_in_time_validated boolean,
    generated_at timestamptz,
    metadata jsonb
)
language sql
stable
security definer
set search_path=private,public
as $function$
with event_row as (
    select id,kickoff_at,competition
    from public.ticket_events
    where id=p_ticket_event_id and kickoff_at is not null
), resolved as (
    select e.id,e.kickoff_at,e.competition,
      case
        when p_requested_as_of_at >= e.kickoff_at then 'invalid'
        when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 720 then 'not_due'
        when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 336 then 'T-30'
        when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 168 then 'T-14'
        when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 72 then 'T-7'
        when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 24 then 'T-3'
        else 'T-1'
      end as resolved_horizon
    from event_row e
), spec as (
    select r.*,s.target_days_before,s.model_spec_id,s.model_family,s.feature_contract,s.validated_competitions
    from resolved r
    left join private.structural_prior_model_specs_v1 s
      on s.horizon=r.resolved_horizon and s.is_current
), target as (
    select s.*,
      case when s.target_days_before is not null
           then s.kickoff_at-make_interval(days=>s.target_days_before)
      end as target_cutoff
    from spec s
), picked as (
    select t.*,
      p.id prior_id,p.p50,p.p10,p.p90,p.stadium_capacity,p.expected_occupancy,
      p.point_in_time_validated,p.generated_at,p.metadata,
      p.target_as_of_at stored_target_as_of_at,p.kickoff_at stored_kickoff_at,
      p.model_spec_id stored_model_spec_id,p.feature_contract stored_feature_contract
    from target t
    left join private.structural_prior_forecasts_v1 p
      on p.ticket_event_id=t.id
     and p.horizon=t.resolved_horizon
     and p.target_as_of_at=t.target_cutoff
     and p.model_spec_id=t.model_spec_id
)
select
    case
      when resolved_horizon='invalid' then 'invalid_request'
      when resolved_horizon='not_due' then 'not_due'
      when model_spec_id is null then 'missing_spec'
      when competition is null or not (competition=any(validated_competitions)) then 'out_of_domain'
      when prior_id is null then 'missing_prior'
      when point_in_time_validated is not true then 'invalid_prior'
      when stored_target_as_of_at<>target_cutoff then 'invalid_prior'
      when stored_kickoff_at<>kickoff_at then 'invalid_prior'
      when stored_model_spec_id<>model_spec_id then 'invalid_prior'
      when stored_feature_contract<>feature_contract then 'invalid_prior'
      else 'ready'
    end::text,
    prior_id,
    id,
    case when resolved_horizon in ('T-30','T-14','T-7','T-3','T-1') then resolved_horizon end,
    p_requested_as_of_at,
    target_cutoff,
    kickoff_at,
    model_spec_id,
    model_family,
    feature_contract,
    p50,p10,p90,stadium_capacity,
    coalesce(expected_occupancy,case when stadium_capacity>0 then p50/stadium_capacity end),
    point_in_time_validated,
    generated_at,
    metadata
from picked;
$function$;

comment on function public.get_structural_prior_v1(bigint,timestamptz) is
'Resolves the latest already-due current historical champion checkpoint. Returns out_of_domain outside the model validated competition scope and never falls back to a legacy model.';
