# Historical C1 recipe replay v1 — exposed diagnostic

Completed **2026-11-05 15:36:57UTC**. Review:[PR219](https://github.com/NiedzielX/beyond/pull/219). Protocol:`C1_HISTORICAL_REPLAY_PRECOMMIT_V1.md`; implementation/publication`f7706419e33b461f3d39559e47a9fcf697c7b77b`verified remotely before fitting. This tests separately refitted fixed recipes, **not the actual frozen26artifact**. All17target fixtures/50source-time prefixes were previously exposed. No tuning, training-MAE claim, production write or prospective backfill.

## Same17fixtures, latest-row attendance MAE in persons

| Forecast | Chronological recipe replay | Leave-one-fixture-out, non-temporal diagnostic |
|---|---:|---:|
| Stored structural prior |3131.16|3131.16|
| Actually persisted C1v8policy |3248.81|3248.81|
| Median expanded recipe, raw |4558.29|3318.41|
| Median expanded recipe, unchangedv8policy |3107.62|3491.58|
| Median base20-restricted recipe, raw |4558.29|2887.33|
| Median base20-restricted recipe, unchangedv8policy |3107.62|3495.21|
| Ridge10expanded recipe, raw |4051.41|2962.37|
| Ridge10expanded recipe, unchangedv8policy |3199.89|3306.75|

Chronological training contains9–20earlier independent fixtures. Every fold excludes all target-fixture rows and fits its own imputer/indicators/scaler. Label availability is max(confirmed_at,created_at,updated_at), enforced before the earliest evaluated target prefix. All17foldsmeet the predeclared9fixtureminimum; no target dropped. The six additional outcomes first became knownNov4, after all evaluated predictions; **none can enter any chronological training fold**. Therefore expanded/base20chronological results are identical and do not test a causal benefit from those six added labels.

The non-temporal diagnostic fits25other fixtures per expanded fold; base20restrictedfits19or20. It may use later fixtures and is explicitly not a historical live simulation. Its expanded rawmedian is worse than restricted rawmedian by **431.08**(paired event bootstrap95%interval **−416.74to1431.68**). No demonstrated support-expansion benefit.

## Why3107.62does not establish a live improvement

Chronological median-policy minus actual C1policy:−141.19, paired95%event-bootstrapinterval **−728.12to304.54**; minus prior:−23.54, interval **−70.62to0.00**. Neither is a decisive gain;1200is not demonstrated. Rawmedian is worse than prior by1427.14(interval23.34to3196.04)on this exposed conditional replay; do not select a rescue parameter from these outcomes.

The first11fixtureshave44matched prefixes; their chronological median-policy MAEis**4278.34**, worse than actual C1policy**4121.45**and slightly better than prior4314.72. The later6fixtureshave only one latest reconstructed input each; their counterfactual median-policy always falls back to prior, MAE**961.29**, versus stored C1policy1648.96. Their original multi-observation policy context is not reproduced. Thus the overall−141.19cannot be sold as a like-for-like improvement of live26or proof of a better policy. Preserve that sparse-context caveat and full17denominator.

Original C1rawlatest forecasts match all17stored outputs to7.28e-12. Training data are the immutable26/80/12snapshot and exact30features. However historical feature/publication times and reconstructed structural inputs retain inherited, independently unverified availability assumptions. This is a chronological **training-label** audit and an exposed recipe diagnostic, not fully independently verified PIT or new prospective validation. No claim is made that old point-in-time flags alone prove full source availability.

## Reproducibility and checks

Aggregate JSON:`artifacts/c1_historical_replay_v1_summary.json`. Private result includes exact fold IDs/cutoffs/training sizes, all50predictions per design, paired errors, event-balanced latest/window MAE, bias, improvement rates, P90/worst degradation, horizon/club and first11/later6groups. Stored C1policy has no fabricated window baseline. Bootstrap10000paired-eventresamples/seed42is descriptive only. Source hashes are predeclared in`artifacts/c1_historical_replay_v1_source_hashes.json`.

18newfold/chronology/metric/immutability tests pass;311registered root checks and189DemandEnginechecks pass. Broad root discovery ran637checks but had7import errors solely because unrelated olderCatBoostmodules lack their optional dependency; do not claim that broader suite passed or change the pinned live environment to repair it. Hosted source/result DemandEngine42058255308and other non-skipped checks succeed; skipped live-anchor/main-audit jobs are not claimed as executed. Frozen26loader/identitycheck passes and the complete frozen artifact/source map is identical before/after both designs.

Private evidence16files/185950compressed bytes,SHA**5171496708f387152274f44298662ec02f8472ebb3117173af090090cf4240ce**, namespace`c1-historical-replay-v1/`. Independent remote read/decompression/file hashes and complete input reload/numerical parity verified after restoration,0refits. Runtime:`/workspace/ops-runtime/2026-11-05-c1-historical-replay-v1/`. Raw rows remain outsideGit.

## Decision

**DIAGNOSTIC_COMPLETE_NO_DEMONSTRATED_GAIN_NO_PROMOTION.** Do not retune the frozen median26or reopen closed old searches. Its future collector continues unchanged; genuine future data are still required to measure that exact artifact's MAE. The present historical result provides no evidence that adding6fixtures achieves1200or improves rawmedian; it also identifies sparse policy context as a limit on historical product comparisons. Model/data research must continue under a separate justified precommit, not by optimizing this exposed result.

`production_change=false`, `live_adjustment=0`. No source schedule, missed window, frozen artifact or live score was changed.
