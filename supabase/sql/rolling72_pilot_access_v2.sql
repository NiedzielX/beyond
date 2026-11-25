-- Narrow, read-only capability grants for the Rolling72 investor pilot.
-- Store only the SHA-256 hash of the owner-generated 32-byte bearer code.
create schema if not exists private;

create table if not exists private.rolling72_pilot_grants_v2 (
  token_sha256 text primary key
    check (token_sha256 ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default statement_timestamp(),
  expires_at timestamptz not null,
  fixture_ids bigint[] not null,
  lane_ids text[] not null,
  check (fixture_ids = array[27049]::bigint[]),
  check (lane_ids = array['rolling72-mvp-persistence-v1']::text[]),
  check (expires_at > created_at),
  check (expires_at <= created_at + interval '7 days'),
  check (expires_at <= timestamptz '2026-11-29 01:15:00+00')
);

alter table private.rolling72_pilot_grants_v2 enable row level security;
revoke all on table private.rolling72_pilot_grants_v2 from public, anon, authenticated, service_role;

create or replace function public.authorize_rolling72_pilot_feed_v2(p_token_sha256 text)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
set timezone = 'UTC'
as $$
declare
  v_grant private.rolling72_pilot_grants_v2%rowtype;
begin
  if p_token_sha256 is null or p_token_sha256 !~ '^[0-9a-f]{64}$' then
    return null;
  end if;

  select g.* into v_grant
  from private.rolling72_pilot_grants_v2 g
  where g.token_sha256 = p_token_sha256
    and g.created_at <= statement_timestamp()
    and g.expires_at > statement_timestamp();

  if not found then
    return null;
  end if;

  return jsonb_build_object(
    'expires_at', v_grant.expires_at,
    'fixture_ids', to_jsonb(v_grant.fixture_ids),
    'lane_ids', to_jsonb(v_grant.lane_ids)
  );
end;
$$;

revoke all on function public.authorize_rolling72_pilot_feed_v2(text) from public, anon, authenticated;
grant execute on function public.authorize_rolling72_pilot_feed_v2(text) to service_role;
