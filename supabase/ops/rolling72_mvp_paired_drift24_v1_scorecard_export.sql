-- Read-only, full-cohort export for the fixed offline decision evaluator.
-- Run as an authorized service/database operator and save the single JSON value
-- to a private file. No source payloads, grants, tokens or credentials are read.
-- Coverage comes from the runtime status RPC; these are accepted shared labels.
with facts as (
 select l.bundle_id,l.ticket_event_id,r.club_slug as club_id,l.horizon_hours,
  l.actual_available_total as actual,l.pers_prediction,l.drift24_prediction
 from private.rolling72_mvp_paired_drift24_v1_labels l
 join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=l.ticket_event_id
)
select jsonb_build_object(
 'schema_version','rolling72-paired-drift24-accepted-label-export-v1',
 'lane_id','rolling72-mvp-paired-drift24-v1',
 'exported_at',statement_timestamp(),
 'accepted_shared_labels',count(*),
 'coverage_source','get_rolling72_mvp_paired_drift24_v1_status',
 'rows',coalesce(jsonb_agg(to_jsonb(facts) order by horizon_hours,ticket_event_id,bundle_id),'[]'::jsonb)
) as scorecard_input
from facts;
