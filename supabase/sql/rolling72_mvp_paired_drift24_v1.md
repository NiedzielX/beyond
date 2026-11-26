# Fresh paired PERS–drift24 runtime

This additive research lane issues both methods together for each eligible new
source seal. Its target is public available inventory (`available_total_seats`),
not sales or attendance. The exact prospective contract is in
[the precommit](../../.ai/specs/2026-11-24-rolling72-fresh-paired-drift24.md) and
[runtime specification](../../.ai/specs/2026-11-25-rolling72-paired-drift24-runtime.md).

The source lane, existing PERS product lane and exposed E5/B experiments are
dependencies. Their forecasts and labels do not enter this paired cohort.
`live_adjustment=0` remains unchanged.

## Interface

Only the service role can call these public RPCs:

- `activate_rolling72_mvp_paired_drift24_v1(manifest_text, manifest_sha256)`
- `issue_rolling72_mvp_paired_drift24_v1(25)`
- `score_rolling72_mvp_paired_drift24_v1(100)`
- `get_rolling72_mvp_paired_drift24_v1_status()`

Activation pins exact manifest bytes and implementation/source hashes. It does
not import old origins. Older source seals may supply anchor history only.
Every issued bundle contains six rows: two methods at +24/+48/+72 hours,
with one actual issue coordinate and one shared accepted outcome per horizon.
An outside-kickoff target retains its row with a null prediction.

PERS works from the first point, including true zero. Drift uses the fixed
24–30-hour anchor recipe. Missing or broken drift support produces an explicit
numeric PERS fallback. An invalid current source makes both methods unavailable.
Deferred transaction visibility can be retried; terminal refusals remain counted.

## Release boundary

Apply the additive SQL only after the isolated PostgreSQL contract suite and an
independent review pass for those exact bytes. Generate the final manifest from
the reviewed file, validate it against the actual hosted source configuration,
then activate and install the separately guarded finite cron job. A normal
scheduled new-source cycle, rather than a synthetic test, proves live issuance.
Do not treat an unexecuted tool call, a configured job or a green CI run as that
runtime proof. If hosted access is unavailable, keep activation unverified.

## Evaluation

Report all three horizons separately, with equal weight per event. The drift
policy includes every PERS fallback. The primary +72 comparison requires at
least 30 new independent events across eight clubs, at least 10% MAE reduction,
and an entirely negative paired event-bootstrap 95% interval for MAE delta
(10,000 draws, seed 42). +24/+48 point MAEs must not worsen. The pure report
module implements this fixed decision rule; accepted-label exports alone cannot
measure forecast or scoring coverage. Use the runtime denominator counters too.

The [read-only export](../ops/rolling72_mvp_paired_drift24_v1_scorecard_export.sql)
produces the full accepted-label input, with no source payloads or credentials.
Save its single JSON value privately, then run:

```sh
python ml/rolling72_paired_drift24_scorecard_v1.py --help
```

The report accepts the `rows` array in that export. Do not truncate or select
events by their errors. The report cannot attest the source, prospective clocks,
or completeness of an arbitrary caller-supplied file; retain the immutable
runtime receipts and status alongside it.

These requirements assess availability forecasting. They cannot establish the
separate attendance goal of approximately 1,200 seats MAE.
