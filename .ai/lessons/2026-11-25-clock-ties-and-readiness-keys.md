# Actual clocks, paged history and readiness costs

- Consecutive real PostgreSQL clock reads can share a microsecond. Strict
  calculation-before-issue constraints need a bounded real-clock advance guard,
  not arithmetic timestamp adjustment. Keep the constraint; a persistent clock
  failure must roll back and return explicit retryable SQLSTATE40001. Record a
  separately versioned exact-body patch beside the immutable base SQL manifest.
- Check actual discovered test counts. An incorrect glob missing `persistence`
  ran zero clock tests; the correct suite ran twelve, including32 real local
  source/issue cycles. Zero tests is not verification.
- A PERS model consumes one origin, while the chart may show earlier known
  history. Use independently paged observations and both capture<=origin and
  known<=issue filters. Do not repeat unbounded full histories inside every
  issue or let later labels/current failures rewrite immutable inputs.
- Readiness aggregates can invoke full feature functions despite selecting
  only keys. Preserve exact horizon selection and join multiplicity in a
  private key selector; prove parity before replacing summary-only joins.
  The observed cache cycle changed from120s timeout to40.340s success. This
  does not measure physical Disk I/O budget consumption.
- Validate the real browser→relay→Edge→SQL chain and native polling separately
  from fixtures/CI. Keep raw capabilities in private files/process memory;
  publish only sanitized proof. A protected Vercel login is not an app read.
