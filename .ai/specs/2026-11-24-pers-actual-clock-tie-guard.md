# PERS actual-clock tie correction

24 November2026. A separate correctness repair discovered during P0-4d tests.
Root owns implementation; independent review is required before deployment.

Two isolated integration cases failed the existing strict constraint
`calculation_completed_at < issued_at`: consecutive genuine clock_timestamp()
calls returned the same microsecond. Constraint rejection rolled back the call;
no invalid bundle or label was accepted. Existing successful forecasts stay
immutable. This is not a model change or a relaxation of the time contract.

Add a guarded, separately versioned patch to the issuer function only. Preserve
the reviewed base migration bytes/hash and manifest. Guard the exact old body
hash; a mismatched installation must fail before mutation. After calculation,
stamp the actual clock as before. Only if that clock is <=calculation completion,
perform one bounded pg_sleep(0.000001), then stamp clock_timestamp() again. If
the clock still has not advanced, raise a retryable error, committing no partial
bundle. Never add arithmetic to timestamps, backdate, lower the strict table
constraint, alter forecasts/labels, or modify E5/B/source functions or cron.

The patch's distinct hash and installed before/after body hashes must be
recorded beside the base SQL identity in runtime evidence; never claim the
changed body still equals the old migration. Existing authorization and
SECURITY DEFINER/search_path/timezone settings must be preserved exactly.

Verify on isolated PG16: reproduce current failure, apply patch, all PERS/PG
feed regressions pass, rapid repeated genuine first/new-source issues preserve
strict real clock order, old tables/other bodies unchanged, exact patch retry
is idempotent and an unexpected body fails closed. Independent review, then
guarded hosted application and exact before/after verification.
