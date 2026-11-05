# Identical-target daily-path comparison

Implemented2026-11-05under the existing drift precommit's overlap-report provision. No new model, fit, forecast, label or source-ledger write. This report compares the frozen daily model, fixed24-hour drift and persistence on exactly shared event/issue/target/prefix/measurement/immutable-label identities. Separate earlier vintages cannot enter the comparison merely because they concern the same event/date.

Each attempt is revalidated with its original frozen ledger validator, including exact artifact reproduction and legal issue/execution times. Every persisted target must match its immutable attempt. Model hashes are fixed to the genuine frozen artifacts. Scores, target freshness and source-label links are checked and errors recomputed. Missing comparator points and delayed score copying remain explicit coverage; they never become zero errors. Average shared target errors within each event, then average events. Report signed bias, P90/worst event errors, pairwise differences and per-lead support. Both original primary evaluators and existing review gates remain unchanged.

## Actual first execution —11:01UTC

Original daily cohort:17attempts /110issued points. Drift:10attempts /53points. Exact overlap:53points, all still future; paired scores0, **all paired MAEsnull**.57older daily points have no drift counterpart and remain outside the overlap while staying in the original daily evaluation. The original daily primary has4genuine scored points/4events, model188.977408vs persistence163.25; these cannot be advertised as a drift comparison.

The53future overlapping points span4events/4clubs. Their first target cutoffs onNov5are Motor5091and Piast10500at17:00UTC, Widzew7372at19:15UTCand Jagiellonia24at20:00UTC. These are label-maturity times for forecasts genuinely issued onNov4, not instructions to reconstruct forecasts now. Labels must still qualify and be captured/scored by the existing workers. Unscored targets remain missing. The8-event/5-club drift review is unchanged.

```bash
python -m ml.daily_path_paired_comparison_v1 \
  --daily-ledger /workspace/ops-runtime/2026-11-03-daily-path/shadow-v1.sqlite \
  --drift-ledger /workspace/ops-runtime/2026-11-04-drift-comparator/drift-v1.sqlite \
  --output /workspace/ops-runtime/<new-private-report>.json
```

Both SQLite connections use read-only mode and their own snapshot transactions; read drift before daily because the former is derived from the latter. Concurrent inconsistent evidence fails closed. Seven tests cover actual frozen prediction/ledger validation on synthetic prefixes, byte-unchanged source files, event balancing, missing/pending/lagging scores, duplicate or different vintages, changed artifacts/lineage, label identity, chronology and error arithmetic. This establishes comparison correctness, not predictive accuracy. `production_change=false`, `live_adjustment=0`.
