-- Beyond Ticketing — Roboticket Price Observations v1
--
-- Append-only event pricing evidence for E0/E1.
-- Public tables are not browser-exposed: RLS is enabled and only service_role
-- may read/write them directly. Sanitized current pricing will be materialized
-- separately for the dashboard.

create table if not exists public.sector_price_area_observations_v1 (
    id bigserial primary key,
    ticket_event_id bigint not null references public.ticket_events(id),
    snapshot_id bigint references public.snapshots(id),
    captured_at timestamptz not null,
    sector text not null,
    sector_source_id bigint,
    price_area_id integer not null,
    price_area_name text,
    available integer not null check (available >= 0),
    source text not null default 'roboticket',
    created_at timestamptz not null default now(),
    unique(ticket_event_id,captured_at,sector,price_area_id)
);

create index if not exists sector_price_area_obs_event_time_idx
    on public.sector_price_area_observations_v1(ticket_event_id,captured_at desc);
create index if not exists sector_price_area_obs_snapshot_idx
    on public.sector_price_area_observations_v1(snapshot_id);
create index if not exists sector_price_area_obs_area_idx
    on public.sector_price_area_observations_v1(ticket_event_id,price_area_id,captured_at desc);

alter table public.sector_price_area_observations_v1 enable row level security;
revoke all on public.sector_price_area_observations_v1 from public,anon,authenticated;
grant select,insert on public.sector_price_area_observations_v1 to service_role;
grant usage,select on sequence public.sector_price_area_observations_v1_id_seq to service_role;

comment on table public.sector_price_area_observations_v1 is
'Append-only Roboticket public inventory split by sector and priceAreaId. Availability is a public-inventory proxy, not confirmed paid sales.';

create table if not exists public.ticket_price_observations_v1 (
    id bigserial primary key,
    ticket_event_id bigint not null references public.ticket_events(id),
    snapshot_id bigint references public.snapshots(id),
    captured_at timestamptz not null,
    price_area_id integer not null,
    price_area_name text,
    price_type_id integer not null,
    price_type_name text,
    price numeric(12,2) not null check (price >= 0),
    currency text,
    source text not null default 'roboticket',
    created_at timestamptz not null default now(),
    unique(ticket_event_id,captured_at,price_area_id,price_type_id)
);

create index if not exists ticket_price_obs_event_time_idx
    on public.ticket_price_observations_v1(ticket_event_id,captured_at desc);
create index if not exists ticket_price_obs_snapshot_idx
    on public.ticket_price_observations_v1(snapshot_id);
create index if not exists ticket_price_obs_area_type_idx
    on public.ticket_price_observations_v1(ticket_event_id,price_area_id,price_type_id,captured_at desc);

alter table public.ticket_price_observations_v1 enable row level security;
revoke all on public.ticket_price_observations_v1 from public,anon,authenticated;
grant select,insert on public.ticket_price_observations_v1 to service_role;
grant usage,select on sequence public.ticket_price_observations_v1_id_seq to service_role;

comment on table public.ticket_price_observations_v1 is
'Append-only Roboticket event price matrix: priceAreaId x priceTypeId x price, captured from event-specific stadium HTML. Zero-price ticket types are preserved.';
