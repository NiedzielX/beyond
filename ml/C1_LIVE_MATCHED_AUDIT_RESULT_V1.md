# C1 v8: audit at the actual persisted forecast times

2026-11-04. Executed the user-authorized [MAE1200 plan](C1_LIVE_MAE_1200_PLAN_V1.md). This is an **exposed retrospective diagnostic**, not new prospective evidence. No old model, threshold, forecast, score or production setting changed.

## Same opportunity comparison

All 11 scored C1 events remain included: 5,10,11,15,16,18,19,20,21,22,23. Reconstructed 44 genuine final24/6-hour representatives, bounded separately by each event's actually persisted C1 latest timestamp. No later snapshot was used. D2 uses the original frozen 9-event/30-row development set, reconstructed in memory, never these 11 outcomes for training.

| Forecast | Latest-per-event attendance MAE |
|---|---:|
| Actually persisted structural prior |4,314.72|
| Actually persisted raw C1 live |7,127.99|
| Actually persisted governed C1 v8 |**4,121.45**|
| Frozen Pre-Live v2/b2 anchor at matching times |4,754.01|
| Frozen D2 P2 at matching times |5,157.52|

D2 event-balanced representative-window MAE is4,921.87. Do not compare this with C1's official4,971.62window score as if the windows were identical: that stored C1 aggregate contains its own persisted inference vintages. The matched latest comparison above is the primary result.

The earlier Lech5 D2 diagnostic remains valid at its original later15:18:50forecast time: P2AE6,652.81. At C1's actual13:49:09time, P2AE10,416.44 versus C1AE7,669.07. Comparing these different opportunities would overstate the D2 advantage. All original event5 golden metrics reproduce; no old report is relabelled as a same-time result.

## What the dominant errors establish

| Match / event | Actual | Prior | C1 policy absolute error | D2 P2 error |
|---|---:|---:|---:|---:|
| Wisła Kraków–Raków /16 |33,000|15,990.31|17,009.69|17,801.56|
| Lech–Korona /5 |37,407|29,737.93|7,669.07|10,416.44|
| Górnik–Piast /11 |27,659|20,498.38|7,160.62|9,984.22|
| Śląsk–Wieczysta /23 |12,391|18,384.33|5,993.33|3,848.28|

These four contribute83.45%of C1 total absolute error. They remain in the denominator. Policy chooses PRIOR10times/LIVE1time. An inadmissible outcome-aware choice between the two existing experts still gives4,103.05MAE: selection thresholds alone cannot repair this cohort.

**Confirmed input gap:** the actual materialized priors for Wisła16 and Górnik11 have `season_home_n=0`. The current attendance export also lacks earlier current-season home results for these clubs. Sporting fixtures identify five earlier completed Wisła home matches and four Górnik matches. Both clubs are outside the original C1 training cohort. This proves missing information, not the causal size of a potential MAE improvement. The complete follow-up queue has18history checks and6missing completed-event outcomes; some history checks refer to the same source fixture for different target events.

**Capacity is not a demonstrated explanation:** used capacities33,130 /43,269 /28,236 /43,708 all accommodate the four recorded outcomes. No simple label-over-capacity repair was found. Public map size is available on6events, only2original training events, and absent from C1's30features. Unavailable map seats cannot be equated with paid sales or attendance.

**No numerical train/serve discrepancy found:** all900original training feature cells match; loaded C1 reproduces its stored raw/policy/prior outputs within3.64e-12seats and all expert selections exactly. Original D2 development metrics reproduce within1e-9. Frozen artifact hashes remain unchanged.

**Freshness is separate:** actual final C1 forecasts occur0.42–5.42hours before kickoff;10of11events have later genuine source observations. Those observations were excluded from this comparison. This supports checking future collection coverage, not rewriting old forecasts or claiming that later always improves accuracy.

## Proven, blocked, next

The reusable exporter and audit CLI both executed successfully against fresh read-only DB inputs retrieved12:17UTC. Twelve focused tests cover pairing, exact cohorts, label/anchor drift, PIT timing, source sampling and missing-history accounting. Source tables are sequential exports rather than an atomic DB snapshot; historical publication times are not independently established.

External source sites fail from this cloud host with `URLError`. Existing canonical outcomes agree across the DB exports but have **not** been independently reverified at their original sites. The six Oct30–Nov2outcomes remain missing. The queue contains nulls, never guessed attendance; historical missed prospective observations remain missing.

Next bounded hypothesis: test genuinely new confirmed training information,9→20independent matches, while holding the C1 features/Ridge/policy fixed, under a separate precommit and version. All20become exposed training data; only genuinely future paired forecasts can establish improvement. Missing prior history remains a separate unresolved data task. No MAE1200claim follows from this audit.

Reproduction:

```bash
python -m ml.export_c1_matched_audit_inputs_v1 --output-dir /private/new-input-directory
python -m ml.c1_live_matched_audit_v1 --input-dir /private/new-input-directory --output-dir /private/new-result-directory
```

Private outputs must be outside Git. Aggregates, input/frozen hashes and the null-label queue are in `artifacts/c1_live_matched_audit_v1/`. Full private evidence is under `/workspace/ops-runtime/2026-11-04-c1-audit-cli-results/`; a separately verified private backup of the original input/evidence pack exists under the content-addressed `c1-audit-v1/`namespace. A source export can now fail closed if the scored cohort changes; do not force the old11-event identity onto new scores.

`production_change=false`, `live_adjustment=0`.
