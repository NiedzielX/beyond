-- Keep Context Matrix cadence labels aligned with deployed collectors/registries.

update public.context_feature_definitions
set refresh_cadence = case feature_key
  when 'sport.match_stakes' then 'source every 6h; process every 5m'
  when 'sport.rivalry_opponent' then 'daily propagation + on registry change'
  when 'sport.absence_impact' then 'daily propagation + on registry change'
  when 'hype.media_attention' then 'every 15m sampled'
  when 'hype.mention_acceleration' then 'derived from sampled windows'
  else refresh_cadence
end,
updated_at=now()
where feature_key in (
  'sport.match_stakes','sport.rivalry_opponent','sport.absence_impact',
  'hype.media_attention','hype.mention_acceleration'
);
