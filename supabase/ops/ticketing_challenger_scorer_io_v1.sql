-- Additive selector derived from the reviewed deployed feature-store chain.
-- Deploy with the version guard, not as a standalone hosted migration.
create function private.ticketing_challenger_t24_features_io_v1(p_ticket_event_ids bigint[])
returns table (
  ticket_event_id bigint,
  snapshot_id bigint,
  snapshot_captured_at timestamptz,
  matched_velocity_6h_pct_of_first_per_hour numeric,
  raw_velocity_6h_pct_of_first_per_hour numeric
)
language sql stable security invoker set search_path=''
as $$
  with selected as materialized (
    select event.id as ticket_event_id, sn.id as snapshot_id,
           sn.captured_at, sn.available_total
    from (select distinct unnest(p_ticket_event_ids) as id) pending
    join public.ticket_events event on event.id=pending.id
    cross join lateral (
      select s.id,s.captured_at,s.available_total
      from public.snapshots s
      where s.ticket_event_id=event.id and s.available_total is not null
        and s.captured_at<=event.kickoff_at
        and extract(epoch from (event.kickoff_at-s.captured_at))/3600.0 between 24.0 and 36.0
      order by (extract(epoch from (event.kickoff_at-s.captured_at))/3600.0-24.0),
               s.captured_at desc,s.id desc
      limit 1
    ) sn
    where event.kickoff_at is not null
  )
  select sel.ticket_event_id,sel.snapshot_id,sel.captured_at,
    round(lf.velocity_6h/nullif(first_s.available_total,0)*100.0,8),
    case when anchor6.available_total is not null and sel.captured_at>anchor6.captured_at
      then round((
        ((anchor6.available_total-sel.available_total)::numeric /
          nullif(extract(epoch from (sel.captured_at-anchor6.captured_at))/3600.0,0))
        / nullif(first_s.available_total,0) * 100.0
      )::numeric,8)
    end
  from selected sel
  left join lateral (
    select s.available_total
    from public.snapshots s
    where s.ticket_event_id=sel.ticket_event_id and s.available_total is not null
      and s.captured_at<=sel.captured_at
    order by s.captured_at asc,s.id asc
    limit 1
  ) first_s on true
  left join lateral (
    select s.captured_at,s.available_total
    from public.snapshots s
    where s.ticket_event_id=sel.ticket_event_id and s.available_total is not null
      and s.captured_at<=sel.captured_at-interval '6 hours'
    order by s.captured_at desc,s.id desc
    limit 1
  ) anchor6 on true
  left join lateral public.get_live_features_v1_asof(sel.ticket_event_id,sel.captured_at) lf on true
  left join public.ticket_event_outcomes o on o.ticket_event_id=sel.ticket_event_id
  left join public.ticket_event_inventory_reference r
    on r.ticket_event_id=sel.ticket_event_id and r.reference_type='public_seat_map_size';
$$;

revoke all on function private.ticketing_challenger_t24_features_io_v1(bigint[])
  from public,anon,authenticated;
grant execute on function private.ticketing_challenger_t24_features_io_v1(bigint[]) to service_role;

create or replace function public.score_ticketing_challenger_v1()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare
  v_rows integer := 0;
begin
  with due as materialized (
    select s.id,s.ticket_event_id,s.checkpoint_at,b.predicted_p50,
           m.model_version,m.trained_at,m.score_floor_ratio,m.score_ceiling_ratio,
           m.y_mean,m.beta,m.x_mean,m.x_sd
    from public.event_context_snapshots_v1 s
    join public.context_ablation_predictions_v1 b
      on b.snapshot_id=s.id and b.variant_key='baseline'
    join public.ticketing_challenger_models_v1 m
      on m.status='shadow_active' and m.horizon='T-24h'
     and m.trained_at<=s.checkpoint_at
    where s.checkpoint_code='T-24h' and s.capture_mode='prospective'
      and not exists (
        select 1 from public.context_ablation_predictions_v1 existing
        where existing.snapshot_id=s.id and existing.variant_key='baseline_ticketing'
          and existing.id is not null
      )
  ), features as materialized (
    select f.*
    from (select array_agg(distinct ticket_event_id) keys from due
          having count(*)>0) requested
    cross join lateral private.ticketing_challenger_t24_features_io_v1(requested.keys) f
  )
  insert into public.context_ablation_predictions_v1(
    snapshot_id,variant_key,predicted_p50,prediction_method,model_version,metadata
  )
  select
    d.id,
    'baseline_ticketing',
    round((
      d.predicted_p50 * (
        1 + greatest(
          d.score_floor_ratio,
          least(
            d.score_ceiling_ratio,
            d.y_mean + d.beta * (
              (coalesce(f.matched_velocity_6h_pct_of_first_per_hour,f.raw_velocity_6h_pct_of_first_per_hour)-d.x_mean)
              / nullif(d.x_sd,0)
            )
          )
        )
      )
    )::numeric)::int,
    'ticketing_challenger_v1_prospective_shadow',
    d.model_version,
    jsonb_build_object(
      'feature','hybrid_v6',
      'feature_value',coalesce(f.matched_velocity_6h_pct_of_first_per_hour,f.raw_velocity_6h_pct_of_first_per_hour),
      'feature_source',case when f.matched_velocity_6h_pct_of_first_per_hour is not null then 'matched_v6' else 'raw_v6' end,
      'feature_snapshot_id',f.snapshot_id,
      'feature_snapshot_captured_at',f.snapshot_captured_at,
      'model_trained_at',d.trained_at,
      'shadow_only',true
    )
  from due d
  join features f on f.ticket_event_id=d.ticket_event_id
  where f.snapshot_captured_at<=d.checkpoint_at
    and coalesce(f.matched_velocity_6h_pct_of_first_per_hour,f.raw_velocity_6h_pct_of_first_per_hour) is not null;

  get diagnostics v_rows=row_count;
  return v_rows;
end;
$$;
