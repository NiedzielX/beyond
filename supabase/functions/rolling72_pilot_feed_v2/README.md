# Protected rolling72 pilot relay v2

This additive Edge function accepts only GET and authenticates its own opaque
bearer capability before invoking service-only read RPCs. Deploy with gateway
JWT verification disabled because this handler validates the non-JWT code.
Missing/malformed/expired or out-of-scope codes fail closed.

| Fixture and lane | Authorization RPC | Read RPC |
|---|---|---|
| 24377/24378 with E5 or B | `authorize_rolling72_pilot_feed_v1` | `get_rolling72_investor_feed_v1` |
| 27049 with PERS | `authorize_rolling72_pilot_feed_v2` | `get_rolling72_mvp_persistence_feed_v1` |

Existing v1 functions and grants remain unchanged. V2's private grant table
allows only fixture27049 and `rolling72-mvp-persistence-v1`, with expiry no
later than29November2026 01:15UTC. Store only SHA256 of the owner's random code.
If a code has both grants, revoke both rows to revoke both scopes.

The fixed project origin, route-specific grant allowlists, bounded request
parameters, eight-second upstream timeout, response scope checks, no-store
headers and static errors prevent arbitrary proxying and accidental leakage.
Logs contain only the failing phase and timeout/network category. No service
key or raw capability code belongs in clients, logs, URLs or repository files.

Local verification: `node --experimental-strip-types --test handler.test.ts`.
Database access tests require only the dedicated loopback PostgreSQL16 database
`rolling72_pilot_access_v2_test`; never use a hosted DSN.
