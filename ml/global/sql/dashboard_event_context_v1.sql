-- Safe browser-facing projection of latest event context.
-- Raw metadata/source details stay private in event_context_observations.

drop view if exists public.dashboard_event_context_v1;

drop policy if exists dashboard_event_context_read on public.event_context_observations;
create policy dashboard_event_context_read
on public.event_context_observations
for select
to anon, authenticated
using (feature_key in (
  'sport.form5',
  'sport.match_stakes',
  'sport.absence_impact',
  'sport.rivalry_opponent',
  'hype.media_attention',
  'hype.mention_acceleration'
));

grant select (ticket_event_id, feature_key, observed_at, numeric_value, text_value, confidence)
on public.event_context_observations
to anon, authenticated;

create view public.dashboard_event_context_v1
with (security_invoker = true)
as
select distinct on (ticket_event_id, feature_key)
  ticket_event_id,
  feature_key,
  observed_at,
  numeric_value,
  text_value,
  confidence
from public.event_context_observations
where feature_key in (
  'sport.form5',
  'sport.match_stakes',
  'sport.absence_impact',
  'sport.rivalry_opponent',
  'hype.media_attention',
  'hype.mention_acceleration'
)
order by ticket_event_id, feature_key, observed_at desc;

revoke all on public.dashboard_event_context_v1 from public;
grant select on public.dashboard_event_context_v1 to anon, authenticated, service_role;
