const ALLOWED_FIXTURES = new Set([24377, 24378, 27049]);
const PERS_LANE = 'rolling72-mvp-persistence-v1';
const ALLOWED_LANES = new Set([
  'rolling72-common-flow-e5-v1',
  'rolling72-forward-baselines-b-v1',
  PERS_LANE,
]);
const TOKEN_RE = /^[A-Za-z0-9_-]{43}$/;
const HASH_RE = /^[0-9a-f]{64}$/;
const ALLOWED_QUERY = new Set([
  'ticket_event_id', 'lane_id', 'limit', 'before_bundle_id', 'before_receipt_id',
]);
const DEFAULT_LIMIT = 50;
const REQUEST_TIMEOUT_MS = 8_000;
const PROJECT_ORIGIN = 'https://adchzwqboeekhokapxqi.supabase.co';

type Env = (name: string) => string | undefined;
export interface PilotFeedHandlerConfig {
  env: Env;
  fetch?: typeof fetch;
  now?: () => number;
  timeoutMs?: number;
}
type PilotGrant = { expires_at: string; fixture_ids: number[]; lane_ids: string[] };
type FeedParams = {
  p_ticket_event_id: number;
  p_lane_id: string;
  p_before_bundle_id: number | null;
  p_limit: number;
  p_before_receipt_id: number | null;
};

const json = (status: number, error: string) => new Response(JSON.stringify({ error }), {
  status,
  headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
});

function safePositiveInt(value: string | null, field: string, optional = false): number | null {
  if (value === null && optional) return null;
  if (value === null || !/^[1-9]\d*$/.test(value)) throw new Error(`invalid ${field}`);
  const n = Number(value);
  if (!Number.isSafeInteger(n) || n < 1) throw new Error(`invalid ${field}`);
  return n;
}

function queryParams(request: Request): FeedParams {
  const url = new URL(request.url);
  for (const key of url.searchParams.keys()) {
    if (!ALLOWED_QUERY.has(key)) throw new Error('unknown query parameter');
  }
  for (const key of ALLOWED_QUERY) {
    if (url.searchParams.getAll(key).length > 1) throw new Error('duplicate query parameter');
  }
  const fixture = safePositiveInt(url.searchParams.get('ticket_event_id'), 'ticket_event_id')!;
  const lane = url.searchParams.get('lane_id');
  if (lane === null || !ALLOWED_LANES.has(lane) || !ALLOWED_FIXTURES.has(fixture)
      || (lane === PERS_LANE) !== (fixture === 27049)) {
    throw new Error('unsupported pilot scope');
  }
  const limitRaw = url.searchParams.get('limit');
  const limit = limitRaw === null ? DEFAULT_LIMIT : safePositiveInt(limitRaw, 'limit')!;
  if (limit < 1 || limit > 200) throw new Error('invalid limit');
  return {
    p_ticket_event_id: fixture,
    p_lane_id: lane,
    p_before_bundle_id: safePositiveInt(url.searchParams.get('before_bundle_id'), 'before_bundle_id', true),
    p_limit: limit,
    p_before_receipt_id: safePositiveInt(url.searchParams.get('before_receipt_id'), 'before_receipt_id', true),
  };
}

async function sha256Hex(token: string): Promise<string> {
  const bytes = new TextEncoder().encode(token);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, '0')).join('');
}

function parseGrant(value: unknown, pers: boolean): PilotGrant | null {
  if (value === null) return null;
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('invalid grant');
  const grant = value as Record<string, unknown>;
  const expires = grant.expires_at;
  if (typeof expires !== 'string' || !Number.isFinite(Date.parse(expires))) throw new Error('invalid grant expiry');
  const fixtures = grant.fixture_ids;
  const lanes = grant.lane_ids;
  const fixturesForRoute = pers ? new Set([27049]) : new Set([24377, 24378]);
  const lanesForRoute = pers ? new Set([PERS_LANE]) : new Set([
    'rolling72-common-flow-e5-v1', 'rolling72-forward-baselines-b-v1',
  ]);
  if (!Array.isArray(fixtures) || !fixtures.every((id) => Number.isSafeInteger(id) && fixturesForRoute.has(id))
    || new Set(fixtures).size !== fixtures.length || fixtures.length === 0
    || !Array.isArray(lanes) || !lanes.every((id) => typeof id === 'string' && lanesForRoute.has(id))
    || new Set(lanes).size !== lanes.length || lanes.length === 0) throw new Error('invalid grant scope');
  return { expires_at: expires, fixture_ids: fixtures as number[], lane_ids: lanes as string[] };
}

function restBase(raw: string | undefined): string | null {
  if (!raw) return null;
  try {
    const url = new URL(raw);
    if (url.origin !== PROJECT_ORIGIN || url.pathname !== '/' || url.username || url.password
      || url.search || url.hash) return null;
    return PROJECT_ORIGIN;
  } catch {
    return null;
  }
}

/** Capability-authenticated, read-only relay to the existing investor RPC. */
export function createHandler(config: PilotFeedHandlerConfig) {
  const doFetch = config.fetch ?? fetch;
  const now = config.now ?? Date.now;
  const timeoutMs = config.timeoutMs ?? REQUEST_TIMEOUT_MS;
  return async (request: Request): Promise<Response> => {
    if (request.method !== 'GET') return json(405, 'method_not_allowed');

    const authorization = request.headers.get('authorization') ?? '';
    const match = /^Bearer ([A-Za-z0-9_-]{43})$/.exec(authorization);
    if (!match || !TOKEN_RE.test(match[1])) return json(401, 'unauthorized');
    const tokenHash = await sha256Hex(match[1]);
    if (!HASH_RE.test(tokenHash)) return json(401, 'unauthorized');

    let params: FeedParams;
    try {
      params = queryParams(request);
    } catch (error) {
      return json(error instanceof Error && error.message === 'unsupported pilot scope' ? 403 : 400,
        error instanceof Error && error.message === 'unsupported pilot scope' ? 'forbidden' : 'invalid_request');
    }

    const base = restBase(config.env('SUPABASE_URL'));
    const serviceKey = config.env('SUPABASE_SERVICE_ROLE_KEY');
    if (!base || !serviceKey) return json(503, 'service_unavailable');

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const headers = {
      apikey: serviceKey,
      Authorization: `Bearer ${serviceKey}`,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
    const rpc = async (name: string, body: Record<string, unknown>): Promise<Response> =>
      await doFetch(`${base}/rest/v1/rpc/${name}`, {
        method: 'POST', headers, body: JSON.stringify(body), signal: controller.signal, redirect: 'error',
      });

    let phase: 'authorize' | 'feed' = 'authorize';
    try {
      const pers = params.p_lane_id === PERS_LANE;
      const authResponse = await rpc(pers ? 'authorize_rolling72_pilot_feed_v2' : 'authorize_rolling72_pilot_feed_v1', { p_token_sha256: tokenHash });
      if (!authResponse.ok) return json(503, 'service_unavailable');
      let rawGrant: unknown;
      try { rawGrant = await authResponse.json(); } catch { return json(503, 'service_unavailable'); }
      let grant: PilotGrant | null;
      try { grant = parseGrant(rawGrant, pers); } catch { return json(403, 'forbidden'); }
      if (!grant) return json(401, 'unauthorized');
      const currentTime = now();
      const expiresAt = Date.parse(grant.expires_at);
      if (expiresAt <= currentTime || expiresAt > currentTime + 7 * 24 * 60 * 60 * 1000
        || expiresAt > Date.parse('2026-11-29T01:15:00Z')) return json(403, 'forbidden');
      if (!grant.fixture_ids.includes(params.p_ticket_event_id) || !grant.lane_ids.includes(params.p_lane_id)) {
        return json(403, 'forbidden');
      }
      if (now() >= expiresAt) return json(403, 'forbidden');

      phase = 'feed';
      const feedResponse = await rpc(pers ? 'get_rolling72_mvp_persistence_feed_v1' : 'get_rolling72_investor_feed_v1', params);
      if (!feedResponse.ok) return json(502, 'upstream_unavailable');
      let feed: unknown;
      try { feed = await feedResponse.json(); } catch { return json(502, 'upstream_unavailable'); }
      if (!feed || typeof feed !== 'object' || Array.isArray(feed)) return json(502, 'upstream_unavailable');
      const result = feed as Record<string, unknown>;
      const fixtures = result.fixtures;
      const scorecardScope = result.scorecard_scope;
      const scorecards = result.scorecards;
      if (result.schema_version !== 'rolling72-investor-feed-v1'
        || !['OK', 'PARTIAL', 'EMPTY'].includes(String(result.status))
        || !Array.isArray(fixtures) || fixtures.length > 1
        || !Array.isArray(scorecards)
        || scorecards.some((scorecard) => !scorecard || typeof scorecard !== 'object'
          || (scorecard as Record<string, unknown>).lane_id !== params.p_lane_id)
        || fixtures.some((fixture) => !fixture || typeof fixture !== 'object'
          || (fixture as Record<string, unknown>).ticket_event_id !== params.p_ticket_event_id
          || !Array.isArray((fixture as Record<string, unknown>).availability_lanes)
          || ((fixture as Record<string, unknown>).availability_lanes as unknown[]).length !== 1
          || (((fixture as Record<string, unknown>).availability_lanes as unknown[])[0] as Record<string, unknown>)?.lane_id !== params.p_lane_id)
        || !scorecardScope || typeof scorecardScope !== 'object'
        || (scorecardScope as Record<string, unknown>).lane_id !== params.p_lane_id) {
        return json(502, 'upstream_unavailable');
      }
      if (now() >= expiresAt) return json(403, 'forbidden');
      return new Response(JSON.stringify(feed), {
        status: 200,
        headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
      });
    } catch (error) {
      const errorName = error && typeof error === 'object' && 'name' in error
        && typeof (error as { name?: unknown }).name === 'string'
        ? (error as { name: string }).name : '';
      const category = controller.signal.aborted || errorName === 'AbortError' || errorName === 'TimeoutError'
        ? 'timeout' : 'network';
      try { console.warn({ phase, category }); } catch { /* logging must not affect the protected response */ }
      return json(502, 'upstream_unavailable');
    } finally {
      clearTimeout(timer);
    }
  };
}
