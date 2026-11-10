# Actual MAE review — November 8, 2026

## Verified results — November 8, 12:28 UTC / 13:28 Warsaw

The forward postmatch chain is now **proven end-to-end**: hosted source run42462549531SUCCESS → exact completed fixture/source verification → history74/75 and two genuine DB outcomes at08:23UTC → unchanged scorers → actual21-event public scores. Górnik attendance **27,867**, Widzew **16,010**. Earlier19:45/22:30source attempts correctly imported zero while sources/completion were pending. Original source contract/ref4dd7130 is unchanged; no missed observations reconstructed.

| Metric / frozen output | Independent fixtures | Latest-per-event attendance MAE |
|---|---:|---:|
| Current served live C1 governed | 21 | **3653.473506** |
| Current served prior | Same21 | 3096.747834 |
| Prospective support26 median26 governed | 4 new / 4 clubs | **1873.219024** |
| Support26 Ridge20 governed | Same4, same observations | 1874.323487 |
| Support26 median20 governed | Same4, same observations | 1942.669265 |
| Support26 original9 governed / prior | Same4, same observations | 2950.505155 |

**1873is the experimental four-event MAE, not current served-model MAE or a guarantee for each match.** Median26has not replaced live C1. Its primary raw support comparison is currently worse than median20raw:2213.593109versus1904.349966 (+309.243144). All30-new-fixture/8-club review gates remain closed; no winner selection, retuning, rejection or promotion. On the latest Górnik/Widzew support observations, all four governed heads selected the shared prior; the existing four-event median26advantage over prior comes from Motor. Do not treat the near-tie with Ridge20as a demonstrated gain.

**Next operational priority is actual live forecast freshness.** Górnik's served latest source was13:20UTC, more than3hours before16:30kickoff: policy15090.546739, actual27867, error12776.453261; same-row prior error3085.263969. The private unchanged original9later selected prior on actual16:20observation (error3085.263969). These are different issue times, not evidence of a model change or permission to repair the old served record. Actual main Actions ran13:30then18:17UTC despite configured quarter-hour cron. Guard future useful live refreshes with bounded, source-safe orchestration and prove the hosted→new-current-DB-record chain before calling it restored; do not backfill Górnik.

History augmentation raw2635.187585is worse than paired control2516.888131 on its own four-event clock support. Fresh structural2702.497646versus its own matched prior2950.505155; later Legia450capture fails closed on unverified anchor capacity. History's latest Górnik/Widzew observations are fromNovember6, while support26has laterNovember7observations because archive gaps remain missing. Same snapshot benchmarks match; do not compare different latest clocks as a paired model effect.

Daily inventory-path comparison now has16matched targets /4fixtures /4clubs: drift13.290929, daily model259.341810, persistence175.291667. These are available-inventory errors, not attendance errors;8-event/5-club review remains closed. Overnight daily legal windows did execute and persist genuine new issues/targets.

All six bounded workers **expired at November8 10:30UTC / 11:30Warsaw**; process state isZ, not running. No renewal or expired source-slot catchup was performed during this read-only review. Preserve forecasts/state/private backups before a new bounded activation. Current production defaults remainfalse/0. Detailed evidence: [November8review](MAE_REVIEW_2026-11-08.md); private read-only actual DB exports and Actions receipts under `/workspace/ops-runtime/2026-11-08-mae-review/`.

## Verified outcome evidence

Actual source run42462549531on immutable4dd7130completed successfully. Original9-file source/import proof was independently backed up before scoring, SHA c4d8fa7c5dfb58afb7f6208b29c61b5a847705c63915af1b5a6bc7731f83c553; final10-file proof SHA c760870445aca8feaef38935a43bae3835f9f6060a78285610c02df5e6fe79cc includes scorers. Exact scoped source inputs, append receipt, outcome sync and final result remain in the original private v4source-run directory. The earlier zero-import attempts remain unchanged. Actual read-only public decomposition12:27:42UTC independently reconciles21events/3653.473506to confirmed DB outcomes; no scorer, model, prediction or schema was changed in this review.

The immediate technical next action is to restore timely genuine future hosted inference before attributing all served errors to the estimator. Keep controlled MAE research running with frozen candidates and future labels. Do not alter the1873experimental result into a live performance claim, select a gate from these four exposed outcomes or count snapshots as independent fixtures.
