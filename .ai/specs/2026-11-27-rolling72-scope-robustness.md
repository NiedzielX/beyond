# Rolling72 diagnostic for changing ticket pools

Status: research proposal. No change to the running comparator. A later
challenger needs its own frozen protocol and a new prospective cohort.

Jagiellonia’s first 99 paired bundles contained 4 supported drift issues and
95 scope fallbacks. Endpoint signatures differed in 77 sector cases and 4
price-area cases. A further 14 had identical endpoints and an intervening
membership change. Count-only and endpoints-only tests would hide some of
these breaks. The 95 fallbacks limit what damping alone can improve.

## First research step

For the same strictly selected 24–30 h anchor, report the footprint of the
pairs with a continuous identity between anchor and origin. Use seal time and
immutable source membership only. Pending, missing and invalid source
observations create gaps; do not assume continuity. For each tested origin
record stable common pairs, coverage by count and available places, member
adds and removals, and the contribution of the stable common pairs to the
observed change. Preserve zero, no usable pair and no anchor as distinct states.
Keep inventory movements separate from confirmed sales.

Use the attached recent-bundle diagnostic for the first screening. It
compares endpoint signatures and retains the existing fallback classification.
It does not measure continuous-pair coverage or create a model result.

## Criterion for implementation

If this screen shows meaningful stable support on multiple verified fixtures,
specify one new candidate that projects change only within that stable group
and holds the rest of the origin inventory at the current level. Define
support and missingness before outcomes, using structural checks and a
separate development set if calibration is needed. Do not relax eligibility
of the active strict drift or use E5 scores to select this candidate.

Compare the full candidate policy to PERS and fixed drift24 on actual shared
+24/+48/+72 issue times and labels. Preserve refusals and fallbacks in
coverage. Include valid target scope changes in the primary MAE and show
stable-scope separately. The main independent-event gate remains
30 matches / 8 clubs, +72 MAE improvement of at least 10% versus PERS,
paired event-bootstrap CI below zero, and non-inferior +24/+48 point MAEs.
Report incremental error against fixed drift24 separately.
