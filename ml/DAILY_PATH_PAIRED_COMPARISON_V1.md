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

## First paired target scores —November5 17:09UTC

Existing immutable Nov4 forecasts matured normally; no new retrospective issues were created. Original daily ledger now has8scored points/4events, model238.338245versus persistence226.00 across its full cohort. Keep this original primary result separate from the narrower matched comparison.

The identical-target overlap has67issued points,2scored +1points/2events/2clubs(Motor andPiast),65pending,0mature missing labels. On those exact same2targets, event-balanced MAE:fixed24h drift23.424246, frozen daily model278.069754, persistence351.50. Drift improves both events in this small descriptive snapshot; paired differences−254.645508against model/−328.075754against persistence. These are public available-place errors, not paid-sales or attendance MAE.

The8event/5club review gate is not met. No demonstrated general advantage, retuning, promotion or changed gate. Preserve the next genuine outcomes regardless of direction. Private report:`/workspace/ops-runtime/2026-11-05-first-paired-path-scores/paired-report.json`; the existing original/drift backups and independently verified62file first-window recovery preserve evidence. Original scorers, frozen rules and productionfalse/0are unchanged.
