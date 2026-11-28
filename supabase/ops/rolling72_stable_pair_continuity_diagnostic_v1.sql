-- Read-only research screen for continuous sector / price-area pairs.
-- The six latest anchored SCOPE_MISMATCH bundles are selected before reading
-- their same-event seals. An interval over 130 seals fails closed; do not infer
-- continuity across missing, late-known, gapped, or malformed observations.
with recent_bundles as materialized (
 select b.id bundle_id,b.ticket_event_id,b.issued_at,b.projection_reference_at,
        b.anchor_seal_id,b.anchor_captured_at,b.anchor_known_at,
        a.snapshot_id anchor_snapshot_id,
        b.seal_id origin_seal_id,b.source_captured_at origin_captured_at,
        o.snapshot_id origin_snapshot_id,
        b.source_known_at origin_known_at,b.origin_available_total,
        b.anchor_available_total,
        b.anchor_membership,b.origin_membership,b.fallback_reason
 from private.rolling72_mvp_paired_drift24_v1_issue_bundles b
 left join private.rolling72_mvp_research_v1_seals a
   on (a.id,a.ticket_event_id)=(b.anchor_seal_id,b.ticket_event_id)
 left join private.rolling72_mvp_research_v1_seals o
   on (o.id,o.ticket_event_id)=(b.seal_id,b.ticket_event_id)
 where b.fallback_reason='SCOPE_MISMATCH' and b.anchor_seal_id is not null
 order by b.id desc
 limit 6
), bounded_seals as materialized (
 -- Fetch at most 131 rows per bundle: 131 is a sentinel proving the cap failed.
 select b.bundle_id,s.id seal_id,s.snapshot_id,s.captured_at,s.known_at,
        s.phase,s.transition_status,s.gap_count,s.source_payload,
        s.available_total,s.prior_seal_id
 from recent_bundles b
 cross join lateral (
  select z.id,z.snapshot_id,z.captured_at,z.known_at,z.phase,z.transition_status,
         z.gap_count,z.source_payload,z.available_total,z.prior_seal_id
  from private.rolling72_mvp_research_v1_seals z
  where z.ticket_event_id=b.ticket_event_id
    and (z.captured_at,z.snapshot_id)>=(b.anchor_captured_at,b.anchor_snapshot_id)
    and (z.captured_at,z.snapshot_id)<=(b.origin_captured_at,b.origin_snapshot_id)
    and z.known_at<=b.projection_reference_at
  order by z.captured_at,z.snapshot_id
  limit 131
 ) s
), visible_chain as (
 select s.*,lag(seal_id) over (
   partition by bundle_id order by captured_at,snapshot_id
 ) previous_visible_seal_id
 from bounded_seals s
), seal_summary as (
 select b.bundle_id,count(s.seal_id)::integer seal_count,
        bool_and(case when s.seal_id=b.anchor_seal_id then s.previous_visible_seal_id is null
                 else s.transition_status='COMPLETE' and s.gap_count=0
                  and s.previous_visible_seal_id is not null
                  and s.prior_seal_id is not distinct from s.previous_visible_seal_id
                 end) intervals_complete,
        bool_and(case when jsonb_typeof(s.source_payload->'sector_price_area_rows')='array'
                      then jsonb_array_length(s.source_payload->'sector_price_area_rows')>0
                      else false end) payloads_well_formed,
        bool_or(s.seal_id=b.anchor_seal_id) has_anchor,
        bool_or(s.seal_id=b.origin_seal_id) has_origin,
        min(s.captured_at) first_seal_at,max(s.captured_at) last_seal_at
 from recent_bundles b left join visible_chain s using(bundle_id)
 group by b.bundle_id
), interval_status as (
 select b.*,ss.seal_count,ss.intervals_complete,ss.payloads_well_formed,
        ss.has_anchor,ss.has_origin,ss.first_seal_at,ss.last_seal_at,
        case
         when b.anchor_captured_at is null or b.origin_captured_at is null then 'MISSING_ENDPOINT_CLOCK'
         when b.anchor_known_at>b.projection_reference_at or b.origin_known_at>b.projection_reference_at then 'ENDPOINT_NOT_KNOWN_BY_PROJECTION'
         when ss.seal_count>=131 then 'OVER_130_SEALS_FAIL_CLOSED'
         when ss.seal_count<2 or not coalesce(ss.has_anchor,false) or not coalesce(ss.has_origin,false) then 'MISSING_ENDPOINT_SEAL'
         when ss.seal_count<3 then 'NO_INTERIOR_SEAL'
         when exists (
           select 1 from private.rolling72_mvp_research_v1_attempts a
           where a.ticket_event_id=b.ticket_event_id
             and a.known_at>b.anchor_known_at and a.known_at<=b.projection_reference_at
             and a.status in ('MISSING_SOURCE','SKIPPED_STALE','INVALID_SOURCE','INTERNAL_ERROR')
             and (a.captured_at is null or a.captured_at between b.anchor_captured_at and b.origin_captured_at)
         ) then 'KNOWN_FAILED_SOURCE_ATTEMPT'
         when not coalesce(ss.intervals_complete,false) then 'GAPPED_OR_INCOMPLETE_TRANSITION'
         when not coalesce(ss.payloads_well_formed,false) then 'MALFORMED_OR_EMPTY_MEMBERSHIP'
         else 'MEASURED'
        end continuity_status
 from recent_bundles b join seal_summary ss using(bundle_id)
), pair_per_seal as (
 -- Collapse any repeated row for a key within a source seal before testing
 -- continuity; availability remains the summed inventory for that key.
 select s.bundle_id,s.seal_id,s.snapshot_id,
        jsonb_build_array(x->'sector_source_id',x->'price_area_id') pair_key,
        sum((x->>'available')::bigint)::bigint pair_available
 from bounded_seals s
 join interval_status st using(bundle_id)
 cross join lateral jsonb_array_elements(s.source_payload->'sector_price_area_rows') x
 where st.continuity_status='MEASURED'
 group by s.bundle_id,s.seal_id,s.snapshot_id,
          jsonb_build_array(x->'sector_source_id',x->'price_area_id')
), pair_presence as (
 select p.bundle_id,p.pair_key,count(*)::integer observed_seals,
        max(p.pair_available) filter(where p.seal_id=st.anchor_seal_id) anchor_available,
        max(p.pair_available) filter(where p.seal_id=st.origin_seal_id) origin_pair_available
 from pair_per_seal p join interval_status st using(bundle_id)
 group by p.bundle_id,p.pair_key,st.seal_count,st.anchor_seal_id,st.origin_seal_id
), stable_metrics as (
 select st.bundle_id,
        count(*) filter(where pp.observed_seals=st.seal_count)::integer continuous_pair_count,
        coalesce(sum(pp.origin_pair_available) filter(where pp.observed_seals=st.seal_count),0)::bigint continuous_origin_available,
        coalesce(sum(pp.origin_pair_available-pp.anchor_available)
          filter(where pp.observed_seals=st.seal_count),0)::bigint continuous_pair_observed_delta,
        count(*) filter(where pp.observed_seals<st.seal_count)::integer noncontinuous_pair_keys
 from interval_status st left join pair_presence pp using(bundle_id)
 group by st.bundle_id
)
select statement_timestamp() read_at,
       st.bundle_id,st.ticket_event_id,st.issued_at,st.anchor_seal_id,st.origin_seal_id,
       st.anchor_captured_at,st.origin_captured_at,st.projection_reference_at,
       st.seal_count,st.first_seal_at,st.last_seal_at,st.continuity_status,
       st.anchor_available_total,st.origin_available_total,
       st.origin_available_total-st.anchor_available_total observed_total_delta,
       case when st.continuity_status='MEASURED' then sm.continuous_pair_count end continuous_pair_count,
       case when st.continuity_status='MEASURED' then sm.noncontinuous_pair_keys end noncontinuous_pair_keys,
       case when st.continuity_status='MEASURED' then sm.continuous_origin_available end continuous_origin_available,
       case when st.continuity_status='MEASURED' and st.origin_available_total>0
            then round(100.0*sm.continuous_origin_available/st.origin_available_total,2) end continuous_origin_available_pct,
       case when st.continuity_status='MEASURED' then sm.continuous_pair_observed_delta end continuous_pair_observed_delta,
       case when st.continuity_status='MEASURED'
            then st.origin_available_total-st.anchor_available_total-sm.continuous_pair_observed_delta end
            as observed_delta_outside_continuous_pairs
from interval_status st
join stable_metrics sm using(bundle_id)
order by st.bundle_id desc;
