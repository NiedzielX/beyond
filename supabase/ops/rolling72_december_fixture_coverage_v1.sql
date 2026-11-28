-- Read-only December pilot audit. One row per registered fixture and horizon,
-- including fixtures with no observation and horizons with no shared label.
with watermark as materialized (
  select statement_timestamp() as read_at
), fixtures as materialized (
  select r.ticket_event_id,r.club_slug,r.external_event_id,r.registered_at,r.kickoff_at
  from private.rolling72_december_source_v1_registry r
  where r.lane_id='rolling72-december-source-v1'
), source_coverage as (
  select c.ticket_event_id,c.horizon_hours,
         count(*) filter(where c.status='SOURCE_ELIGIBLE') as source_eligible,
         count(*) filter(where c.status='OUTSIDE_KICKOFF') as source_outside_kickoff,
         max(s.captured_at) as latest_capture_at
  from fixtures f
  join private.rolling72_december_source_v1_candidates c using(ticket_event_id)
  join private.rolling72_december_source_v1_seals s on s.id=c.seal_id
  group by c.ticket_event_id,c.horizon_hours
), paired as (
  select p.ticket_event_id,p.horizon_hours,p.issued_at,p.target_at,p.status,
         d.status as drift_status,d.fallback_reason,
         p.prediction is not null and d.prediction is not null as numeric_pair,
         l.id as label_id,l.pers_absolute_error,l.drift24_absolute_error
  from fixtures f
  join private.rolling72_december_pair_v1_predictions p using(ticket_event_id)
  join private.rolling72_december_pair_v1_predictions d
    on (d.bundle_id,d.horizon_hours,d.ticket_event_id)=(p.bundle_id,p.horizon_hours,p.ticket_event_id)
   and d.method='DRIFT24'
  left join private.rolling72_december_pair_v1_labels l
    on (l.bundle_id,l.horizon_hours,l.ticket_event_id)=(p.bundle_id,p.horizon_hours,p.ticket_event_id)
  where p.method='PERS'
), forecasts as (
  select p.ticket_event_id,p.horizon_hours,
         count(*) filter(where p.status='OUTSIDE_KICKOFF') as issue_outside_kickoff,
         count(*) filter(where p.numeric_pair) as numeric_pairs,
         count(*) filter(where p.numeric_pair and p.target_at>w.read_at) as future_targets,
         count(*) filter(where p.numeric_pair and p.target_at<=w.read_at and p.label_id is null) as due_without_label,
         count(*) filter(where p.numeric_pair and p.drift_status='READY') as drift_ready,
         count(*) filter(where p.numeric_pair and p.fallback_reason='NO_24H_ANCHOR') as fallback_no_anchor,
         count(*) filter(where p.numeric_pair and p.fallback_reason='SCOPE_MISMATCH') as fallback_scope,
         count(*) filter(where p.numeric_pair and p.fallback_reason='SOURCE_BREAK') as fallback_source,
         count(p.label_id) filter(where p.numeric_pair) as shared_labels,
         round((avg(p.pers_absolute_error) filter(where p.numeric_pair))::numeric,2) as pers_mae,
         round((avg(p.drift24_absolute_error) filter(where p.numeric_pair))::numeric,2) as drift24_mae,
         max(p.issued_at) filter(where p.numeric_pair) as latest_issue_at,
         min(p.target_at) filter(where p.numeric_pair and p.target_at>w.read_at) as next_target_at
  from paired p cross join watermark w
  group by p.ticket_event_id,p.horizon_hours
)
select w.read_at,f.ticket_event_id,f.club_slug,f.external_event_id,f.registered_at,f.kickoff_at,h.horizon_hours,
       'available_total_seats' as unit,
       coalesce(s.source_eligible,0) as source_eligible,
       coalesce(s.source_outside_kickoff,0) as source_outside_kickoff,
       coalesce(p.issue_outside_kickoff,0) as issue_outside_kickoff,
       coalesce(p.numeric_pairs,0) as numeric_pairs,
       coalesce(p.future_targets,0) as future_targets,
       coalesce(p.due_without_label,0) as due_without_label,
       coalesce(p.drift_ready,0) as drift_ready,
       coalesce(p.fallback_no_anchor,0) as fallback_no_anchor,
       coalesce(p.fallback_scope,0) as fallback_scope,
       coalesce(p.fallback_source,0) as fallback_source,
       coalesce(p.shared_labels,0) as shared_labels,
       p.pers_mae,p.drift24_mae,s.latest_capture_at,p.latest_issue_at,p.next_target_at
from fixtures f
cross join (values (24),(48),(72)) h(horizon_hours)
cross join watermark w
left join source_coverage s using(ticket_event_id,horizon_hours)
left join forecasts p using(ticket_event_id,horizon_hours)
order by f.ticket_event_id,h.horizon_hours;
