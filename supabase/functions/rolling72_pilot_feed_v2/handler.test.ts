import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createHandler } from './handler.ts';

const TOKEN = 'A'.repeat(43); // Synthetic test-only capability; never use as a real pilot code.
const SERVICE_KEY = 'synthetic-service-role-key-for-handler-tests';
const BASE_URL = 'https://pilot.invalid/rolling72-feed';
const PROJECT_URL = 'https://adchzwqboeekhokapxqi.supabase.co';
const FEED_PARAMS = 'ticket_event_id=24377&lane_id=rolling72-common-flow-e5-v1&limit=25&before_bundle_id=100&before_receipt_id=200';
const FEED = {
  schema_version: 'rolling72-investor-feed-v1',
  status: 'OK',
  fixtures: [{ ticket_event_id: 24377, availability_lanes: [{ lane_id: 'rolling72-common-flow-e5-v1', issues: [] }] }],
  scorecard_scope: { lane_id: 'rolling72-common-flow-e5-v1', scope: 'FULL_LANE_COHORT' },
  scorecards: [],
};
const GRANT = {
  expires_at: '2026-11-29T01:15:00.000Z',
  fixture_ids: [24377, 24378],
  lane_ids: ['rolling72-common-flow-e5-v1', 'rolling72-forward-baselines-b-v1'],
};
const TEST_NOW = Date.parse('2026-11-23T09:00:00.000Z');

const PERS_QUERY = 'ticket_event_id=27049&lane_id=rolling72-mvp-persistence-v1&limit=3';
const PERS_GRANT = { ...GRANT, fixture_ids: [27049], lane_ids: ['rolling72-mvp-persistence-v1'] };
const PERS_FEED = { ...FEED,
  fixtures: [{ ticket_event_id: 27049, availability_lanes: [{ lane_id: 'rolling72-mvp-persistence-v1', issues: [] }] }],
  scorecard_scope: { ...FEED.scorecard_scope, lane_id: 'rolling72-mvp-persistence-v1' },
};

test('PERS authorizes through its own narrow grant and calls only its readonly feed', async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const handler = createHandler(config(async (input, init) => {
    calls.push({ url: String(input), init });
    return ok(calls.length === 1 ? PERS_GRANT : PERS_FEED);
  }));
  const response = await handler(req(PERS_QUERY));
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), PERS_FEED);
  assert.deepEqual(calls.map(c => new URL(c.url).pathname), [
    '/rest/v1/rpc/authorize_rolling72_pilot_feed_v2',
    '/rest/v1/rpc/get_rolling72_mvp_persistence_feed_v1',
  ]);
  const args = JSON.parse(String(calls[1].init?.body));
  assert.equal(args.p_ticket_event_id, 27049);
  assert.equal(args.p_lane_id, 'rolling72-mvp-persistence-v1');
  assert.equal(args.p_limit, 3);
  const hash = JSON.parse(String(calls[0].init?.body)).p_token_sha256;
  assert.match(hash, /^[0-9a-f]{64}$/);
  assert.notEqual(hash, TOKEN);
  assert.equal(response.headers.get('cache-control'), 'no-store');
});

test('fixture/lane cross-pairs fail before any RPC and grants cannot cross routes', async () => {
  let calls = 0;
  const handler = createHandler(config(async () => { calls++; return ok(GRANT); }));
  for (const query of [PERS_QUERY.replace('27049', '24377'),
    FEED_PARAMS.replace('24377', '27049')]) {
    assert.equal((await handler(req(query))).status, 403);
  }
  assert.equal(calls, 0);
  assert.equal((await handler(req(PERS_QUERY))).status, 403);
  assert.equal(calls, 1);
  const oldRoute = createHandler(config(async () => ok(PERS_GRANT)));
  assert.equal((await oldRoute(req())).status, 403);
});

function env(values: Record<string, string | undefined> = {}) {
  return (name: string) => values[name];
}

function req(query = FEED_PARAMS, options: { method?: string; authorization?: string | null } = {}) {
  const headers = new Headers();
  if (options.authorization !== null) headers.set('Authorization', options.authorization ?? `Bearer ${TOKEN}`);
  return new Request(`${BASE_URL}?${query}`, { method: options.method ?? 'GET', headers });
}

function ok(value: unknown) {
  return new Response(JSON.stringify(value), { status: 200, headers: { 'Content-Type': 'application/json' } });
}

function config(fetch: typeof globalThis.fetch, more: Record<string, string | undefined> = {}, timeoutMs?: number,
  now: () => number = () => TEST_NOW) {
  return {
    env: env({ SUPABASE_URL: PROJECT_URL, SUPABASE_SERVICE_ROLE_KEY: SERVICE_KEY, ...more }),
    fetch,
    now,
    timeoutMs,
  };
}

async function authHash(fetchCalls: Array<{ url: string; init?: RequestInit }>): Promise<string> {
  const auth = fetchCalls[0];
  const body = JSON.parse(String(auth.init?.body));
  assert.equal(new URL(auth.url).pathname, '/rest/v1/rpc/authorize_rolling72_pilot_feed_v1');
  return body.p_token_sha256;
}

test('missing or malformed bearer is denied before any database request', async () => {
  let fetchCount = 0;
  const handler = createHandler(config(async () => { fetchCount += 1; return ok(null); }));
  for (const authorization of [null, '', 'Bearer short', `Bearer ${'x'.repeat(42)}`, `Bearer ${'x'.repeat(44)}`, `Basic ${TOKEN}`, `Bearer ${TOKEN} extra`]) {
    const response = await handler(req(FEED_PARAMS, { authorization }));
    assert.equal(response.status, 401);
    assert.equal(await response.text(), '{"error":"unauthorized"}');
  }
  assert.equal(fetchCount, 0);
});

test('hash miss, revoked grant, and expired grant stop before investor feed RPC', async () => {
  for (const { grant, status } of [
    { grant: null, status: 401 }, // Wrong hash.
    { grant: null, status: 401 }, // Revoked grant.
    { grant: { ...GRANT, expires_at: '2026-11-23T08:59:59.000Z' }, status: 403 },
  ]) {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const handler = createHandler(config(async (input, init) => {
      calls.push({ url: String(input), init });
      return ok(grant);
    }));
    const response = await handler(req());
    assert.equal(response.status, status);
    assert.equal(calls.length, 1);
    await authHash(calls);
    assert.equal(await response.text(), JSON.stringify({ error: status === 401 ? 'unauthorized' : 'forbidden' }));
  }
});

test('malformed or overbroad grant response is rejected before feed RPC', async () => {
  for (const grant of [
    { ...GRANT, fixture_ids: [24374] },
    { ...GRANT, lane_ids: ['rolling72-lad-shadow-v5'] },
    { ...GRANT, fixture_ids: [] },
    { ...GRANT, expires_at: 'not-a-time' },
    { ...GRANT, expires_at: '2026-11-29T01:16:00.000Z' }, // Past the absolute pilot cutoff.
    { ...GRANT, expires_at: '2026-12-01T00:00:00.000Z' }, // More than seven days from the test clock.
    [{ ...GRANT }],
  ]) {
    let calls = 0;
    const handler = createHandler(config(async () => { calls += 1; return ok(grant); }));
    const response = await handler(req());
    assert.equal(response.status, 403);
    assert.equal(await response.text(), '{"error":"forbidden"}');
    assert.equal(calls, 1);
  }
});

test('valid request calls only the service RPCs with exact scoped arguments', async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const handler = createHandler(config(async (input, init) => {
    calls.push({ url: String(input), init });
    return calls.length === 1 ? ok(GRANT) : ok(FEED);
  }));
  const response = await handler(req());
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), FEED);
  assert.equal(calls.length, 2);
  const auth = calls[0];
  const feed = calls[1];
  for (const call of calls) {
    assert.equal(call.init?.method, 'POST');
    assert.equal((call.init?.headers as Record<string, string>).apikey, SERVICE_KEY);
    assert.equal((call.init?.headers as Record<string, string>).Authorization, `Bearer ${SERVICE_KEY}`);
    assert.equal(new URL(call.url).origin, PROJECT_URL);
  }
  assert.equal(new URL(auth.url).pathname, '/rest/v1/rpc/authorize_rolling72_pilot_feed_v1');
  const hash = await authHash(calls);
  assert.match(hash, /^[0-9a-f]{64}$/);
  assert.notEqual(hash, TOKEN);
  const tokenDigest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(TOKEN));
  const expectedHash = Array.from(new Uint8Array(tokenDigest), (value) => value.toString(16).padStart(2, '0')).join('');
  assert.equal(hash, expectedHash);
  assert.equal(new URL(feed.url).pathname, '/rest/v1/rpc/get_rolling72_investor_feed_v1');
  assert.deepEqual(JSON.parse(String(feed.init?.body)), {
    p_ticket_event_id: 24377,
    p_lane_id: 'rolling72-common-flow-e5-v1',
    p_before_bundle_id: 100,
    p_limit: 25,
    p_before_receipt_id: 200,
  });
  assert.ok(calls.every(({ url }) => !/activate|issue|score|write|admission/i.test(new URL(url).pathname)));
  const responseText = JSON.stringify(FEED);
  assert.equal(responseText.includes(SERVICE_KEY), false);
  assert.equal(responseText.includes(TOKEN), false);
});

test('non-GET requests never invoke database RPCs', async () => {
  let calls = 0;
  const handler = createHandler(config(async () => { calls += 1; return ok(null); }));
  const response = await handler(req(FEED_PARAMS, { method: 'POST' }));
  assert.equal(response.status, 405);
  assert.equal(await response.text(), '{"error":"method_not_allowed"}');
  assert.equal(calls, 0);
});

test('query allowlist, duplicate keys, scope, limits, and cursors fail closed', async () => {
  const invalid = [
    `${FEED_PARAMS}&unexpected=1`,
    `${FEED_PARAMS}&lane_id=rolling72-common-flow-e5-v1`,
    'ticket_event_id=24374&lane_id=rolling72-common-flow-e5-v1',
    'ticket_event_id=24377&lane_id=unknown-lane',
    'ticket_event_id=24377&lane_id=rolling72-common-flow-e5-v1&limit=0',
    'ticket_event_id=24377&lane_id=rolling72-common-flow-e5-v1&limit=201',
    'ticket_event_id=24377&lane_id=rolling72-common-flow-e5-v1&limit=1.5',
    'ticket_event_id=24377&lane_id=rolling72-common-flow-e5-v1&before_bundle_id=-1',
    'ticket_event_id=24377&lane_id=rolling72-common-flow-e5-v1&before_receipt_id=9007199254740992',
  ];
  let calls = 0;
  const handler = createHandler(config(async () => { calls += 1; return ok(GRANT); }));
  for (const query of invalid) {
    const response = await handler(req(query));
    assert.ok([400, 403].includes(response.status), `${query}: ${response.status}`);
    assert.equal(await response.text(), JSON.stringify({ error: response.status === 403 ? 'forbidden' : 'invalid_request' }));
  }
  assert.equal(calls, 0, 'bad query must be rejected before service RPC');
});

test('untrusted project URL, missing service key, and upstream errors do not leak details', async () => {
  let calls = 0;
  const missing = createHandler({
    env: env({ SUPABASE_URL: 'https://example.supabase.co' }),
    fetch: async () => { calls += 1; return ok(null); },
  });
  assert.equal((await missing(req())).status, 503);
  assert.equal(calls, 0);

  const badUrl = createHandler(config(async () => { calls += 1; return ok(GRANT); }, {
    SUPABASE_URL: 'https://attacker.example',
  }));
  assert.equal((await badUrl(req())).status, 503);
  assert.equal(calls, 0);

  const badUrlPath = createHandler(config(async () => { calls += 1; return ok(GRANT); }, {
    SUPABASE_URL: `${PROJECT_URL}/untrusted-path`,
  }));
  assert.equal((await badUrlPath(req())).status, 503);
  assert.equal(calls, 0);

  const errorBody = 'upstream secret, token, and SQL details must not escape';
  const handler = createHandler(config(async (_input, init) => {
    if (String(init?.body).includes('p_token_sha256')) return ok(GRANT);
    return new Response(errorBody, { status: 500 });
  }));
  const response = await handler(req());
  assert.equal(response.status, 502);
  const body = await response.text();
  assert.equal(body, '{"error":"upstream_unavailable"}');
  assert.equal(body.includes(errorBody), false);
});

test('authorization service failure is static and prevents investor feed call', async () => {
  let calls = 0;
  const handler = createHandler(config(async () => {
    calls += 1;
    return new Response('secret upstream failure', { status: 500 });
  }));
  const response = await handler(req());
  assert.equal(response.status, 503);
  assert.equal(await response.text(), '{"error":"service_unavailable"}');
  assert.equal(calls, 1);
});

test('abort timeout returns static upstream failure', async () => {
  let calls = 0;
  const handler = createHandler(config(async (_input, init) => {
    calls += 1;
    if (calls === 1) return ok(GRANT);
    return await new Promise<Response>((_resolve, reject) => {
      const signal = init?.signal;
      if (signal?.aborted) reject(new DOMException('aborted', 'AbortError'));
      else signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')), { once: true });
    });
  }, {}, 5));
  const response = await handler(req());
  assert.equal(response.status, 502);
  assert.equal(await response.text(), '{"error":"upstream_unavailable"}');
  assert.equal(calls, 2);
});

test('grant that expires while feed RPC is in flight is denied on response', async () => {
  let calls = 0;
  let feedReturned = false;
  const expiredTime = Date.parse(GRANT.expires_at) + 1;
  const handler = createHandler(config(async (input) => {
    calls += 1;
    if (String(input).includes('authorize_rolling72_pilot_feed_v1')) return ok(GRANT);
    feedReturned = true;
    return ok(FEED);
  }, {}, undefined, () => feedReturned ? expiredTime : TEST_NOW));
  const response = await handler(req());
  assert.equal(calls, 2);
  assert.equal(response.status, 403);
  assert.equal(await response.text(), '{"error":"forbidden"}');
});

test('HTTP 200 feed response must match the requested schema, fixture, and lane', async () => {
  const invalidFeeds = [
    { ...FEED, schema_version: 'wrong-version' },
    { ...FEED, fixtures: [{ ...FEED.fixtures[0], ticket_event_id: 24378 }] },
    { ...FEED, scorecard_scope: { ...FEED.scorecard_scope, lane_id: 'rolling72-forward-baselines-b-v1' } },
    { ...FEED, fixtures: [{ ticket_event_id: 24377, availability_lanes: [{ lane_id: 'rolling72-forward-baselines-b-v1' }] }] },
    { ...FEED, scorecard_scope: undefined },
    { ...FEED, scorecards: [{ lane_id: 'rolling72-forward-baselines-b-v1' }] },
  ];
  for (const invalidFeed of invalidFeeds) {
    let calls = 0;
    const handler = createHandler(config(async (input) => {
      calls += 1;
      return String(input).includes('authorize_rolling72_pilot_feed_v1') ? ok(GRANT) : ok(invalidFeed);
    }));
    const response = await handler(req());
    assert.equal(response.status, 502);
    assert.equal(await response.text(), '{"error":"upstream_unavailable"}');
    assert.equal(calls, 2);
  }
});

test('RPC network and timeout warnings contain only fixed phase and category', async () => {
  const warnings: unknown[] = [];
  const originalWarn = console.warn;
  console.warn = (...args: unknown[]) => { warnings.push(args.length === 1 ? args[0] : args); };
  try {
    const authFailure = createHandler(config(async () => {
      throw new Error(`secret ${TOKEN} ${SERVICE_KEY} upstream detail`);
    }));
    const authResponse = await authFailure(req());
    assert.equal(authResponse.status, 502);
    assert.equal(await authResponse.text(), '{"error":"upstream_unavailable"}');

    const feedTimeout = createHandler(config(async (input) => {
      if (String(input).includes('authorize_rolling72_pilot_feed_v1')) return ok(GRANT);
      throw new DOMException(`secret ${TOKEN} ${SERVICE_KEY} upstream detail`, 'TimeoutError');
    }));
    const feedResponse = await feedTimeout(req());
    assert.equal(feedResponse.status, 502);
    assert.equal(await feedResponse.text(), '{"error":"upstream_unavailable"}');
  } finally {
    console.warn = originalWarn;
  }

  assert.deepEqual(warnings, [
    { phase: 'authorize', category: 'network' },
    { phase: 'feed', category: 'timeout' },
  ]);
  const warningText = JSON.stringify(warnings);
  assert.equal(warningText.includes(TOKEN), false);
  assert.equal(warningText.includes(SERVICE_KEY), false);
  assert.equal(warningText.includes('secret'), false);
});
