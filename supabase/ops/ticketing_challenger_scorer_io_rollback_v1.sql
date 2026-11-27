-- Run this rollback in a transaction after verifying the helper was installed.
set local search_path=pg_catalog,public;
do $guard$
begin
  if (select md5(prosrc) from pg_proc where oid='public.score_ticketing_challenger_v1()'::regprocedure)
       is distinct from 'b1a5b2220afa01b3292087f8bd66965f'
    or to_regprocedure('private.ticketing_challenger_t24_features_io_v1(bigint[])') is null then
    raise exception 'TICKETING_SCORER_IO_ROLLBACK_VERSION_CHANGED';
  end if;
end
$guard$;
CREATE OR REPLACE FUNCTION public.score_ticketing_challenger_v1()
 RETURNS integer
 LANGUAGE plpgsql
 SET search_path TO 'public', 'pg_temp'
AS $function$
declare
  v_rows integer := 0;
begin
  insert into public.context_ablation_predictions_v1(
    snapshot_id,variant_key,predicted_p50,prediction_method,model_version,metadata
  )
  select
    s.id,
    'baseline_ticketing',
    round((
      b.predicted_p50 * (
        1 + greatest(
          m.score_floor_ratio,
          least(
            m.score_ceiling_ratio,
            m.y_mean + m.beta * (
              (coalesce(f.matched_velocity_6h_pct_of_first_per_hour,f.raw_velocity_6h_pct_of_first_per_hour)-m.x_mean)
              / nullif(m.x_sd,0)
            )
          )
        )
      )
    )::numeric)::int,
    'ticketing_challenger_v1_prospective_shadow',
    m.model_version,
    jsonb_build_object(
      'feature','hybrid_v6',
      'feature_value',coalesce(f.matched_velocity_6h_pct_of_first_per_hour,f.raw_velocity_6h_pct_of_first_per_hour),
      'feature_source',case when f.matched_velocity_6h_pct_of_first_per_hour is not null then 'matched_v6' else 'raw_v6' end,
      'feature_snapshot_id',f.snapshot_id,
      'feature_snapshot_captured_at',f.snapshot_captured_at,
      'model_trained_at',m.trained_at,
      'shadow_only',true
    )
  from public.event_context_snapshots_v1 s
  join public.context_ablation_predictions_v1 b
    on b.snapshot_id=s.id and b.variant_key='baseline'
  join public.multiclub_feature_store_v4 f
    on f.ticket_event_id=s.ticket_event_id and f.horizon='T-24h'
  join public.ticketing_challenger_models_v1 m
    on m.status='shadow_active' and m.horizon='T-24h'
  left join public.context_ablation_predictions_v1 existing
    on existing.snapshot_id=s.id and existing.variant_key='baseline_ticketing'
  where s.checkpoint_code='T-24h'
    and s.capture_mode='prospective'
    and m.trained_at<=s.checkpoint_at
    and f.snapshot_captured_at<=s.checkpoint_at
    and coalesce(f.matched_velocity_6h_pct_of_first_per_hour,f.raw_velocity_6h_pct_of_first_per_hour) is not null
    and existing.id is null;

  get diagnostics v_rows=row_count;
  return v_rows;
end;
$function$;
drop function private.ticketing_challenger_t24_features_io_v1(bigint[]);
