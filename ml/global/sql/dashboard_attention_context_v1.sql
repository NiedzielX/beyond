-- Safe browser-facing sampled media-attention projection.
-- Raw sample metadata stays private; dashboard sees only aggregate counts/status.

drop policy if exists dashboard_media_attention_samples_read on public.media_attention_samples;
create policy dashboard_media_attention_samples_read
on public.media_attention_samples
for select
to anon, authenticated
using (true);

grant select (ticket_event_id, sample_at, mentions_pl)
on public.media_attention_samples
to anon, authenticated;

drop view if exists public.dashboard_attention_context_v1;
create view public.dashboard_attention_context_v1
with (security_invoker = true)
as
with stats as (
  select
    ticket_event_id,
    max(sample_at) as latest_sample_at,
    count(*) filter (where sample_at >= now()-interval '24 hours')::int as samples_24h,
    coalesce(sum(mentions_pl) filter (where sample_at >= now()-interval '24 hours'),0)::int as mentions_24h,
    count(*) filter (where sample_at >= now()-interval '48 hours' and sample_at < now()-interval '24 hours')::int as samples_previous_24h,
    coalesce(sum(mentions_pl) filter (where sample_at >= now()-interval '48 hours' and sample_at < now()-interval '24 hours'),0)::int as mentions_previous_24h
  from public.media_attention_samples
  where sample_at >= now()-interval '48 hours'
  group by ticket_event_id
), scored as (
  select *,
    case
      when samples_24h >= 12 and samples_previous_24h >= 12 then round(
        ((mentions_24h::numeric/samples_24h)+0.25) /
        ((mentions_previous_24h::numeric/samples_previous_24h)+0.25),4
      )
      else null
    end as acceleration_ratio
  from stats
)
select
  ticket_event_id,
  latest_sample_at,
  samples_24h,
  mentions_24h,
  samples_previous_24h,
  mentions_previous_24h,
  acceleration_ratio,
  case
    when samples_24h < 12 then 'collecting_baseline'
    when samples_previous_24h < 12 then 'collecting_comparison'
    when acceleration_ratio >= 1.5 then 'rising'
    when acceleration_ratio <= 0.67 then 'falling'
    else 'stable'
  end as attention_status
from scored;

revoke all on public.dashboard_attention_context_v1 from public;
grant select on public.dashboard_attention_context_v1 to anon, authenticated, service_role;
