-- Verified rivalry context seed: Cracovia <-> Wisła Kraków.
--
-- Evidence is factual event context, not a learned attendance coefficient.
-- It remains shadow/research-only and does not change P50 or live_adjustment.
--
-- Primary official source:
-- https://www.cracovia.pl/posts/poznalismy-date-meczu-z-wisla-krakow/6443
-- Current official Wisła communication independently refers to the fixture as
-- "derby Krakowa z Cracovią".

insert into public.sporting_rivalry_relations(
  id,
  team_a,
  team_b,
  team_a_key,
  team_b_key,
  rivalry_type,
  source_name,
  source_url,
  confidence,
  verified_at,
  is_active,
  notes,
  created_at,
  updated_at
) values (
  2,
  'Cracovia',
  'Wisła Kraków',
  'cracovia',
  'wisla krakow',
  'Derby Krakowa',
  'official_club_research',
  'https://www.cracovia.pl/posts/poznalismy-date-meczu-z-wisla-krakow/6443',
  0.9900,
  now(),
  true,
  'Verified from current official Cracovia wording ("derby Krakowa") and independently corroborated by current official Wisła Kraków communication. Map presence means verified rivalry; map absence does not mean no rivalry.',
  now(),
  now()
)
on conflict (team_a_key, team_b_key) do update set
  rivalry_type = excluded.rivalry_type,
  source_name = excluded.source_name,
  source_url = excluded.source_url,
  confidence = excluded.confidence,
  verified_at = excluded.verified_at,
  is_active = true,
  notes = excluded.notes,
  updated_at = now();

select public.refresh_verified_rivalry_context_v1();
