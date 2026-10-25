-- Stellis public ticketing ingestion v1.
-- Adds source registry + immutable-ish raw public event observations.
-- Model-facing snapshots are created by the Edge collector only when the
-- source explicitly exposes aggregate availableTicketsCount and a league
-- fixture cross-check succeeds. No target/outcome data is referenced.

create table if not exists public.stellis_clubs_v1 (
  club_slug text primary key,
  club_name text not null,
  base_url text not null,
  source_domain text not null unique,
  platform_variant text not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint stellis_clubs_variant_check check (platform_variant in ('frontend_json','legacy_event_list'))
);

insert into public.stellis_clubs_v1(club_slug,club_name,base_url,source_domain,platform_variant,active)
values
  ('widzewlodz','Widzew Łódź','https://bilety.widzew.com','bilety.widzew.com','legacy_event_list',true),
  ('radomiak_radom','Radomiak Radom','https://bilety.rksradomiak.pl','bilety.rksradomiak.pl','frontend_json',true),
  ('piastgliwice','Piast Gliwice','https://bilety.piast-gliwice.eu','bilety.piast-gliwice.eu','frontend_json',true),
  ('motorlublin','Motor Lublin','https://bilety.motorlublin.eu','bilety.motorlublin.eu','legacy_event_list',true),
  ('koronakielce','Korona Kielce','https://bilety.korona-kielce.pl','bilety.korona-kielce.pl','legacy_event_list',true)
on conflict(club_slug) do update set
  club_name=excluded.club_name,
  base_url=excluded.base_url,
  source_domain=excluded.source_domain,
  platform_variant=excluded.platform_variant,
  active=excluded.active,
  updated_at=now();

create table if not exists private.stellis_event_observations_v1 (
  id bigint generated always as identity primary key,
  club_slug text not null references public.stellis_clubs_v1(club_slug),
  external_event_id text not null,
  captured_at timestamptz not null,
  event_name text,
  event_type integer,
  source_kickoff_at timestamptz,
  home_team text,
  away_team text,
  available_tickets_count integer,
  sold_tickets_count integer,
  has_active_stage boolean,
  source_url text,
  platform_variant text not null,
  parser_version text not null,
  league_crosscheck_status text not null,
  promoted_ticket_event_id bigint references public.ticket_events(id),
  promoted_snapshot_id bigint references public.snapshots(id),
  raw_payload jsonb not null,
  created_at timestamptz not null default now(),
  constraint stellis_event_available_check check (available_tickets_count is null or available_tickets_count >= 0),
  constraint stellis_event_sold_check check (sold_tickets_count is null or sold_tickets_count >= 0),
  constraint stellis_event_variant_check check (platform_variant in ('frontend_json','legacy_event_list')),
  constraint stellis_event_crosscheck_check check (league_crosscheck_status in ('MATCHED','NO_MATCH','AMBIGUOUS','NON_MATCH_PRODUCT','MISSING_IDENTITY')),
  constraint stellis_event_raw_object check (jsonb_typeof(raw_payload)='object')
);

create unique index if not exists stellis_event_observations_identity_uq
  on private.stellis_event_observations_v1(club_slug,external_event_id,captured_at);
create index if not exists stellis_event_observations_lookup_idx
  on private.stellis_event_observations_v1(club_slug,external_event_id,captured_at desc);

revoke all on private.stellis_event_observations_v1 from public,anon,authenticated;
grant select on public.stellis_clubs_v1 to anon,authenticated,service_role;
