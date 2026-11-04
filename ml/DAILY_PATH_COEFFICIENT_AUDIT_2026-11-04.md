# Frozen daily-path mechanism audit

Recorded 2026-11-04 before first genuine target scores. This explains issued predictions, not forecast accuracy. No fit or model change was performed.

Artifact: `artifacts/daily_inventory_path_v1.json`, canonical model SHA `1137e257494583374f768622feca343f2dd7d634ef2446198703f8c27fbd9525`.

## Finding

**All 120 relative-inventory-value coefficients are exactly 0**: 60 linear and 60 quadratic. The 250-feature representation receives genuine full prefixes, but this fitted artifact has no direct contribution from their relative value history. Nine coefficients are nonzero:linear constant, linear observation count, six linear observation-bin masks and quadratic constant. All nine are negative.

Latest observed inventory supplies the persistence anchor; maximum prefix inventory supplies scale. Those still depend on observed quantities. Observation count/masks encode collection pattern, not a demonstrated demand mechanism. The result is not independent of all history, but it must not be described as having learned the sequence of sales changes. Public availability remains a proxy, not paid sales.

For a fixed issued prefix, the raw model is therefore:

`latest_inventory + prefix_scale * (A(prefix_count,observed_masks)*lead/7 + B*(lead/7)^2)`

followed by the original zero clipping. Here A and B are negative. This artifact forces a declining raw path for every positive lead; an all-zero path can be produced by clipping a small negative raw forecast. The feature representation could encode rises; the fitted coefficients do not use that capability. This is an algebraic limitation, not evidence that future inventory must rise or that this model's future MAE is known.

## Exact issued-point reconciliation

The read-only audit reconstructs all 57 issued points across 4 events. Maximum difference from stored predictions: 9.10e-13 places. No target values enter the decomposition. Full private report: `/workspace/ops-runtime/2026-11-04-review/coefficient-audit-first.json`.

| Issued case | Latest | Linear constant | Observation count | Observed masks | Quadratic constant | Raw forecast | Issued after clip |
|---|---:|---:|---:|---:|---:|---:|---:|
| Motor 5091, +1 day |7278|−89.72|−89.37|−28.66|−3.47|7066.78|7066.78|
| Piast 10500, +16 days |4356|−647.92|−689.68|−207.00|−401.17|2410.23|2410.23|
| Jagiellonia 24, +36 days |8441|−2809.18|−3420.36|−2230.69|−3913.53|−3932.77|0|
| Widzew 7372, +1 day |0|−0.0092|−0.0088|−0.0029|−0.0004|−0.0213|0|

Rounded terms in this table do not replace exact report values. These are algebraic contributions under correlated features, not causal feature importance. Long-lead training support remains a separate warning:maximum observed training lead 28 days; Jagiellonia +36 is extrapolation.

## Consequence for the plan

Preserve v1 and its issued persistence control; score genuine future points with the unchanged primary evaluator. The separate prefix-regime diagnostics must show zero-only/constant/varying conditional errors without excluding difficult cases or redefining the headline denominator.

The next separately precommitted daily-path research question is now concrete:can a restrained prefix-change mechanism retain usable trajectory information and beat persistence on new future targets, without treating observation density as demand? A standard fixed drift comparator is a candidate baseline, not a proven winner. Define its anchor/staleness rules, version, validation and immutable prospective persistence before using it; do not patch v1 coefficients, reduce alpha or select a curve to resemble the current plots. Source-state v2 is an independent information family whose SQL→feature contract is validated but whose project deployment remains blocked. Its flags must never be joined retroactively onto old snapshots.

For any next learned candidate, audit feature-block sensitivity before freezing and report a degenerate fit explicitly. This capability check does not select hyperparameters or establish MAE improvement. A model whose value-history coefficients vanish may remain a valid recorded experiment, but does not establish the user's intended learned temporal behaviour.

## Reproduce

```bash
python -m ml.daily_path_coefficient_audit_v1 --ledger /workspace/ops-runtime/2026-11-03-daily-path/shadow-v1.sqlite --model ml/artifacts/daily_inventory_path_v1.json --output /tmp/daily-path-coefficient-audit.json
```

Existing output paths are never overwritten. The ledger is opened read-only; frozen model source is never written. Six focused tests cover block indexing, prefix scale, zero clipping, exact reconstruction, identity/corruption rejection and ignoring score fields.
