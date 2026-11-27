# Rolling72 stable-pair candidate

This offline arithmetic prototype addresses `SCOPE_MISMATCH` in the
existing strict drift24 comparator. A scope change can leave a useful
subset of inventory comparable across the full anchor interval.

## Fixed test rule

- Reuse the parent's 24–30 h anchor and origin. Retain every independently
  verified seal from anchor through origin, sorted by capture time and
  snapshot ID. Each seal must be committed and known by the parent's
  projection reference. Check the complete chain before intersection,
  including exact endpoints, an interior seal and no missing edges.
- Intersect `(sector_source_id, price_area_id)` across the interval.
  Resolve ambiguous identities and unreconciled inventory as unsupported.
  Stop at the 131st seal and refuse an oversized interval.
- Require at least three sectors and 80% of origin availability in
  persistent pairs. Keep uncovered origin inventory constant. Apply the
  stable pairs' observed hourly change to their origin total at each
  +24/+48/+72 horizon, including the age of the source observation.
  Floor the projected stable component at zero.
- Keep PERS for other rejected `SCOPE_MISMATCH` cases. Treat a valid zero
  observation as zero. Leave other parent cases to the existing policy.

The synthetic suite covers scope breaks, ties, missing and late-known
observations, invalid source records, incomplete chains, bounded reads,
support boundaries, increasing and decreasing slopes, and true zero.

## Evidence needed before a live comparison

The helper consumes caller assertions. A live integration must verify
ledger bindings, commit visibility, interval completeness and issue
reference inside the source reader. Use the parent's exact selected
anchor ID. Review adverse source attempts over the entire interval
even if parent evaluation stopped at its first scope change. Retain
the parent clock, kickoff eligibility, label selection and score units.

Check coverage across multiple verified matches before selecting this
candidate for deployment. Freeze the complete policy and admission
window before seeing candidate outcomes. Compare it with PERS and
fixed drift24 on the same prospective issue and label IDs. Report
full-policy MAE by horizon, fallback coverage and club-level support.
The pilot target is available seats. Paid tickets and attendance
require their own observed targets.
