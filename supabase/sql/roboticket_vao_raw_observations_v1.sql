-- Beyond Ticketing — Roboticket VAO raw observations v1
--
-- Append-only audit ledger for complete VAO seat-state checks.
-- A raw observation may legitimately contain selectable_seats=0.
-- Public ticket snapshots are still promoted only when selectable_seats > 0.
-- This preserves source evidence without converting "no public selectable seats"
-- into an attendance-model inventory observation.

create table if not exists private.roboticket_vao_observations_v1 (
  id bigint generated always as identity primary key,
  ticket_event_id bigint not null references public.ticket_events(id),
  club_slug text not null,
  external_event_id text not null,
  captured_at timestamptz not null,
  geometry_seats integer not null check (geometry_seats > 0),
  vao_key_count integer not null check (vao_key_count > 0),
  response_unique_ids integer not null check (response_unique_ids >= geometry_seats),
  geometry_matched_rows integer not null check (geometry_matched_rows = geometry_seats),
  extra_response_ids integer not null check (extra_response_ids >= 0),
  selectable_seats integer not null check (selectable_seats >= 0),
  rights_true integer not null check (rights_true >= 0),
  occ_counts jsonb not null,
  status text not null check (status in ('NO_PUBLIC_SELECTABLE_SEATS','PUBLIC_SELECTABLE_SEATS')),
  source_version text not null default 'roboticket-vao-collect-v1',
  promoted_snapshot_id bigint references public.snapshots(id),
  production_change boolean not null default false check (production_change=false),
  created_at timestamptz not null default now()
);

create index if not exists roboticket_vao_observations_event_time_idx
  on private.roboticket_vao_observations_v1(ticket_event_id,captured_at desc);

create index if not exists roboticket_vao_observations_status_time_idx
  on private.roboticket_vao_observations_v1(status,captured_at desc);

revoke all on table private.roboticket_vao_observations_v1
  from public,anon,authenticated;
grant select,insert,update on table private.roboticket_vao_observations_v1
  to service_role;
grant usage,select on sequence private.roboticket_vao_observations_v1_id_seq
  to service_role;
