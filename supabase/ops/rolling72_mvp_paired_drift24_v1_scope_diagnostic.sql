-- Recent endpoint diagnostics. The production fallback reason stays authoritative.
-- Bound the sample before unpacking membership arrays. No score/model changes.
with recent as materialized (
 select id, ticket_event_id, issued_at, fallback_reason,
        origin_membership, anchor_membership
 from private.rolling72_mvp_paired_drift24_v1_issue_bundles
 order by id desc limit 120
), classified as (
 select r.id, r.ticket_event_id, r.issued_at,
  coalesce(r.fallback_reason,'DRIFT_READY') forecast_policy,
  case
   when r.anchor_membership is null then 'NO_SELECTED_ANCHOR'
   when r.origin_membership->'sector_ids' is distinct from r.anchor_membership->'sector_ids'
     then 'ENDPOINT_SECTOR_IDS_DIFFER'
   when r.origin_membership->'pairs' is distinct from r.anchor_membership->'pairs'
     then 'ENDPOINT_PRICE_AREAS_DIFFER'
   when r.fallback_reason='SCOPE_MISMATCH' then 'ENDPOINTS_AGREE_INTERVENING_SCOPE_CHANGE'
   else 'ENDPOINTS_AGREE'
  end diagnostic,
  case when r.anchor_membership is not null then (
    select count(*) from (
     (select value from jsonb_array_elements(r.origin_membership->'pairs')
      except select value from jsonb_array_elements(r.anchor_membership->'pairs'))
     union all
     (select value from jsonb_array_elements(r.anchor_membership->'pairs')
      except select value from jsonb_array_elements(r.origin_membership->'pairs'))
    ) differences
  ) end pair_symmetric_difference
 from recent r
)
select statement_timestamp() read_at,
 (select count(*) from recent) sampled_bundles,
 120 sample_limit, ticket_event_id, forecast_policy, diagnostic,
 count(*) bundles, min(issued_at) first_issued_at,max(issued_at) last_issued_at,
 min(pair_symmetric_difference) min_pairs_changed,
 max(pair_symmetric_difference) max_pairs_changed
from classified
group by ticket_event_id,forecast_policy,diagnostic
order by ticket_event_id,forecast_policy,diagnostic;
