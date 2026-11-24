# Rolling72 PERS issuance and scoring

Implementation contract: [P0-4c specification](../../.ai/specs/2026-11-23-rolling72-mvp-persistence-issuance.md).
This increment consumes the independently activated source lane; it creates no
admissions and imports no historical candidate-buffer observations.

## Current release status

**Deployed and activated on 24 November at 15:05:13 UTC.**

Ten PostgreSQL16 contracts passed locally and in CI; independent review passed.
Installed RPC bodies match the tested copies; private-table RLS and service-only
RPC access were checked on the hosted database. The first scheduled Jagiellonia issue was verified at15:10UTC: three numeric
forecasts from its first source seal. Genuine scores remain future.
Passing a subset of issuance tests is insufficient to release the scorer.
The full isolated suite must cover real issue clocks, committed reads, label
selection/refusal, first accepted label immutability and event-balanced errors.

## Operator interface

The four public functions are service-only RPCs; application roles have no
direct access to the append-only private ledgers:

| RPC | Purpose |
|---|---|
| `activate_rolling72_mvp_persistence_v1(text,text)` | Validate and freeze exact manifest bytes and SHA-256. |
| `issue_rolling72_mvp_persistence_v1(integer)` | Process up to 25 source bundles; default 25. |
| `score_rolling72_mvp_persistence_v1(integer)` | Evaluate up to 100 due predictions; default 100. |
| `get_rolling72_mvp_persistence_v1_status()` | Read denominators and separate horizon scorecards. |

Activation binds the reviewed SQL hash, source SQL and source manifest, fixed
PERS method, horizons 24/48/72, one-hour source freshness and finite issue/score
cutoffs. The score cutoff preserves at least 78 hours after the issue cutoff.
No caller can supply observations, predictions, labels or issue/score clocks.

## Interpretation

Each accepted post-activation source seal can issue a shared bundle of three
horizons. The input available total is the fixed numeric forecast, including
zero and the first observation without history. The actual issue time follows
the completed input read and value calculation. Each target is independently
classified against kickoff; an outside +72 target does not suppress +24.

Earlier source seals remain explicitly outside model activation scope. Delayed,
stale, refused, outside and unattempted candidates remain visible; source-backed
candidates and numeric forecasts are separate counts. No earlier forecast is
reconstructed after deployment.

Labels require a later actual observation captured after issue and at/before
target, no more than six hours old at target. Select the newest observed capture
before validating it. A newer invalid/unsealed observation prevents fallback to
an older convenient value; unresolved source ordering prevents a label.
Accepted labels and errors are immutable. MAE is averaged within each event,
then equally across events, separately for +24/+48/+72. No labels means null
MAE. Bias uses prediction minus actual.

These are **public inventory availability** predictions and errors. They do
not measure confirmed sales or attendance, establish a causal pricing effect,
or demonstrate the separate approximately 1200-seat attendance-MAE goal.
Production `live_adjustment` remains zero.

## Local verification

Use only the disposable PostgreSQL16 database
`rolling72_mvp_persistence_test` on loopback port 55440. Put its DSN in
`ROLLING72_MVP_PERSISTENCE_TEST_DSN`; never use a hosted DSN. Run:

```sh
python -m unittest discover -s tests/postgres -p 'test_rolling72_mvp_persistence_v1.py' -v
```

The workflow `rolling72-mvp-persistence-v1.yml` provisions the same isolated
database with a disposable synthetic credential and no Supabase credentials.
