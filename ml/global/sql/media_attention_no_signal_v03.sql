-- Media attention v0.3: require stronger sample coverage and distinguish
-- a genuine no-signal state from a stable non-zero signal.

create or replace function public.refresh_media_attention_context_v01()
returns integer
language plpgsql
security invoker
set search_path=public
as $$
declare
  r record;
  v_inserted integer := 0;
  v_accel numeric;
  v_direction text;
begin
  for r in
    with event_stats as (
      select
        ticket_event_id,
        sum(mentions_pl) filter (where sample_at >= now()-interval '24 hours')::numeric as mentions_24h,
        count(*) filter (where sample_at >= now()-interval '24 hours')::int as samples_24h,
        sum(mentions_pl) filter (where sample_at >= now()-interval '48 hours' and sample_at < now()-interval '24 hours')::numeric as mentions_prev24h,
        count(*) filter (where sample_at >= now()-interval '48 hours' and sample_at < now()-interval '24 hours')::int as samples_prev24h,
        max(sample_at) as latest_sample_at,
        max(source_file_timestamp) as latest_source_file_timestamp
      from public.media_attention_samples
      where sample_at >= now()-interval '48 hours'
      group by ticket_event_id
    )
    select * from event_stats
  loop
    if coalesce(r.samples_24h,0) >= 12
       and coalesce(r.samples_prev24h,0) >= 12
       and (coalesce(r.mentions_24h,0) + coalesce(r.mentions_prev24h,0)) > 0 then
      v_accel := round(
        ((coalesce(r.mentions_24h,0)/r.samples_24h)+0.25) /
        ((coalesce(r.mentions_prev24h,0)/r.samples_prev24h)+0.25),4
      );
    else
      v_accel := null;
    end if;

    v_direction := case
      when coalesce(r.samples_24h,0) >= 12
       and coalesce(r.samples_prev24h,0) >= 12
       and coalesce(r.mentions_24h,0)=0
       and coalesce(r.mentions_prev24h,0)=0
        then 'nie wykrywamy jeszcze istotnego sygnału medialnego'
      when v_accel is null then 'zbieramy bazę porównawczą'
      when v_accel >= 1.5 then 'uwaga medialna wyraźnie rośnie'
      when v_accel <= 0.67 then 'uwaga medialna wyraźnie słabnie'
      else 'uwaga medialna jest względnie stabilna'
    end;

    insert into public.event_context_observations(
      ticket_event_id,feature_key,observed_at,numeric_value,text_value,
      source_name,source_url,source_record_key,confidence,metadata
    ) values (
      r.ticket_event_id,'hype.media_attention',r.latest_sample_at,coalesce(r.mentions_24h,0),
      format('Media attention: %s polskich dopasowań w próbkach z ostatnich 24h; %s.',coalesce(r.mentions_24h,0)::int,v_direction),
      'GDELT Web News NGrams sampled signal',
      'https://data.gdeltproject.org/gdeltv5/weblegacy/ngrams/',
      format('gdelt-ngram:media-attention:v01:%s:%s',r.ticket_event_id,to_char(r.latest_sample_at at time zone 'UTC','YYYYMMDD"T"HH24MI')),
      case when coalesce(r.samples_24h,0) >= 48 then 0.80 when coalesce(r.samples_24h,0) >= 12 then 0.70 else 0.55 end,
      jsonb_build_object(
        'signal_type','sampled_media_attention',
        'mentions_24h',coalesce(r.mentions_24h,0),
        'samples_24h',coalesce(r.samples_24h,0),
        'mentions_previous_24h',coalesce(r.mentions_prev24h,0),
        'samples_previous_24h',coalesce(r.samples_prev24h,0),
        'acceleration_ratio',v_accel,
        'latest_source_file_timestamp',r.latest_source_file_timestamp,
        'coverage_note','sampled GDELT Web News NGrams; not a complete count of all media publications',
        'scoring_status','raw_media_attention_not_model_scored'
      )
    )
    on conflict (ticket_event_id,feature_key,source_name,source_record_key)
    do update set observed_at=excluded.observed_at,numeric_value=excluded.numeric_value,
      text_value=excluded.text_value,confidence=excluded.confidence,metadata=excluded.metadata;

    v_inserted := v_inserted + 1;
  end loop;
  return v_inserted;
end;
$$;

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
      when samples_24h >= 12 and samples_previous_24h >= 12
       and (mentions_24h + mentions_previous_24h) > 0 then round(
        ((mentions_24h::numeric/samples_24h)+0.25) /
        ((mentions_previous_24h::numeric/samples_previous_24h)+0.25),4)
      else null
    end as acceleration_ratio
  from stats
)
select ticket_event_id,latest_sample_at,samples_24h,mentions_24h,
  samples_previous_24h,mentions_previous_24h,acceleration_ratio,
  case
    when samples_24h < 12 then 'collecting_baseline'
    when samples_previous_24h < 12 then 'collecting_comparison'
    when mentions_24h=0 and mentions_previous_24h=0 then 'no_signal'
    when acceleration_ratio >= 1.5 then 'rising'
    when acceleration_ratio <= 0.67 then 'falling'
    else 'stable'
  end as attention_status
from scored;

revoke all on public.dashboard_attention_context_v1 from public;
grant select on public.dashboard_attention_context_v1 to anon, authenticated, service_role;
