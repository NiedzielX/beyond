-- Read-only diagnostic for the active finite comparator. No forecast or label writes.
-- Count a pair once, at its DRIFT24 row. Existing status RPC owns the full
-- source opportunity denominator, including refused and unattempted origins.
with horizon as (
 select unnest(array[24,48,72]) as hours
), facts as materialized (
 select p.horizon_hours, p.ticket_event_id, p.status, p.fallback_reason,
  p.target_at, l.id as label_id, l.pers_absolute_error, l.drift24_absolute_error,
  case when l.id is null then null
       when l.origin_membership_changed or l.origin_sector_count_delta <> 0
       then 'CHANGED_SCOPE'
       else 'SAME_SCOPE' end as target_scope
 from private.rolling72_mvp_paired_drift24_v1_predictions p
 left join private.rolling72_mvp_paired_drift24_v1_labels l
  on l.bundle_id=p.bundle_id and l.horizon_hours=p.horizon_hours
 where p.method='DRIFT24'
), totals as (
 select f.horizon_hours,
  count(*) filter(where f.status in ('READY','FALLBACK_PERS')) numeric_pairs,
  count(*) filter(where f.status='READY') drift_ready,
  count(*) filter(where f.status='FALLBACK_PERS') fallback,
  count(*) filter(where f.status='OUTSIDE_KICKOFF') outside_kickoff,
  count(*) filter(where f.status in ('READY','FALLBACK_PERS')
    and f.target_at<=statement_timestamp()) mature_pairs,
  count(f.label_id) shared_labels,
  count(*) filter(where f.fallback_reason='SCOPE_MISMATCH') scope_mismatch,
  count(*) filter(where f.fallback_reason='SOURCE_BREAK') source_break,
  count(*) filter(where f.fallback_reason='NO_24H_ANCHOR') no_24h_anchor
 from facts f group by f.horizon_hours
), event_scores as (
 select horizon_hours,ticket_event_id,target_scope,count(*) labels,
  avg(pers_absolute_error) pers_mae,avg(drift24_absolute_error) drift24_mae
 from facts where label_id is not null
 group by horizon_hours,ticket_event_id,target_scope
), score_slices as (
 select horizon_hours,target_scope,count(*) fixtures,sum(labels) labels,
  avg(pers_mae) pers_mae,avg(drift24_mae) drift24_mae
 from event_scores group by horizon_hours,target_scope
)
select statement_timestamp() as read_at,h.hours horizon_hours,
 coalesce(t.numeric_pairs,0) numeric_pairs,coalesce(t.drift_ready,0) drift_ready,
 coalesce(t.fallback,0) fallback,
 coalesce(t.fallback,0)::numeric/nullif(t.numeric_pairs,0) fallback_share,
 coalesce(t.scope_mismatch,0) scope_mismatch,coalesce(t.source_break,0) source_break,
 coalesce(t.no_24h_anchor,0) no_24h_anchor,
 coalesce(t.outside_kickoff,0) outside_kickoff,
 coalesce(t.mature_pairs,0) mature_pairs,coalesce(t.shared_labels,0) shared_labels,
 coalesce(t.shared_labels,0)::numeric/nullif(t.mature_pairs,0) scoring_coverage,
 (select jsonb_object_agg(s.target_scope,jsonb_build_object(
   'fixtures',s.fixtures,'labels',s.labels,'pers_mae',s.pers_mae,
   'drift24_mae',s.drift24_mae))
  from score_slices s where s.horizon_hours=h.hours) target_scope_scores
from horizon h left join totals t on t.horizon_hours=h.hours order by h.hours;
