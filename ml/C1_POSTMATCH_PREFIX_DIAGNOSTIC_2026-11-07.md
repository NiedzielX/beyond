# Genuine C1 errors over the pre-match prefix — November 7

This is an exposed diagnostic of already-issued immutable forecasts, not a new experiment or model-selection result. Independent unit is the fixture; ninety Motor prefixes and six Wisła prefixes still represent **two events**. No fitting, policy changes, reconstructed issues or forecast writes.

## Current served model reconciles to the actual scoreboard

Existing read-only `c1_current_error_decomposition_v1` completed13:02:04UTC:21forecast events,19scored, Górnik449/Widzew7372 still pending. Latest policy MAE **3331.314855**, prior **3226.049075**, raw **6135.688243**. Event-balanced window policy MAE **3921.115012** is a different summary. All17previous public scored rows remained exactly identical after appending the two genuine new scores.

Policy selects prior on17/19latest rows and live on2/19. The four largest errors account for59.772049%of total policy error. Even an outcome-aware choice between the existing prior and raw outputs would give3052.636555MAE on these19events. That unavailable oracle is diagnostic only: switching the existing gate alone cannot demonstrate a1200MAE model on this cohort. Old events remain exposed; their errors do not authorise retuning a frozen version.

## Do updates actually change error?

Same support26ledger, absolute attendance error in seats. “First” and “latest” are the earliest/latest genuinely captured observations in this lane, not equal clock cutoffs across clubs.

| Fixture / frozen output | First error | Latest error | Captured prefixes |
|---|---:|---:|---:|
| Motor / median26 governed | 827.93 | 201.12 | 90 |
| Motor / median20 governed | 555.98 | 478.93 | 90 |
| Motor / Ridge20 governed | 3469.86 | 3061.27 | 90 |
| Motor / original9 governed | 4334.06 | 4510.27 | 90 |
| Motor / stored prior | 4510.27 | 4510.27 | 90 |
| Wisła / median26 governed | 3554.98 | 3554.98 | 6 |
| Wisła / median20 governed | 3554.98 | 3554.98 | 6 |
| Wisła / Ridge20 governed | 3554.98 | 699.25 | 6 |
| Wisła / original9 governed | 3554.98 | 3554.98 | 6 |

Motor source observations spanNovember5 17:03:01–November6 16:43:03UTC; Wisła November6 02:05:02–18:20:02UTC. Every corresponding actual issue precedes kickoff and confirmed outcome. This does not imply uninterrupted capture between those endpoints or a daily forecast contract.

The unchanged policy explains part of the flat output. At Wisła's latest observation median26raw=28947.993150, stored prior=28294.020760, actual=31849. The stored reason is `insufficient_disagreement`, so governed output stays prior even though raw changed. Ridge20 selects live at32548.252138. At Motor's latest observation median26selects live8611.124775 against actual8410; original9selects prior with `live_slope_not_positive`. These stored reasons describe the frozen rule; they do not prove that choosing a different rule from the two outcomes would generalise.

## Horizon coverage matters

Existing predeclared support26horizon summaries, averaging within each fixture before averaging fixtures:

| Observation horizon | Independent fixtures | Median26 governed MAE | Original9 governed MAE |
|---|---:|---:|---:|
| 6–24hours | 2 | 2641.74 | 3826.92 |
| 1–6hours | 2 | 1830.22 | 4032.62 |
| 0–1hour | **1** | 184.24 | 4510.27 |

The final-hour184.24result has Motor only; it cannot be compared as a two-event improvement over earlier bins. Wisła's latest observation was about70minutes before kickoff. Do not interpolate or fabricate the missing final-hour evidence. More frequent snapshots do not create independent fixtures.

History augmentation raw worsened on these two events versus its control:3293.380472against3204.714092. Fresh structural output stayed constant across its actual14Motor/3Wisła prefixes; refreshed source knowledge changed Motor's level but did not make that structural model a trajectory estimator. Its own-laneMAE3536.609250 remains distinct from the paired support26median26MAE1878.052008 and the official19-event3331.314855.

## Evidence and next decision

Offline integrity audit verified209immutable score files (96support26,96history,17fresh), exact capture hashes, real issue/confirmation clocks, numeric errors, matching source snapshots and shared benchmark values across lanes. Some early fresh score files omit a copied forecast dictionary; the audit uses the exact hash-bound original capture without rewriting those files. Source hashes remained unchanged. Seven-file private diagnostic recovery49bdf479c493a0e80602d820ebf24db61745d7a4bcb19021dc82b835a5490fbewas independently read, decompressed and hashed. Script, detailed ledger and actual read-only C1export are private under `/workspace/ops-runtime/2026-11-07-postmatch-score-recovery/`; `prefix-diagnostic.py` reproduces the descriptive calculation without model imports or network calls.

Continue already-frozen paired capture and genuine outcome acquisition for Górnik/Widzew under the separate [forward-source acceptance](FORWARD_OUTCOME_CLOSURE_RESULT_2026-11-07.md). Preserve declared horizon/club/tail diagnostics and the fixed30new-fixture/8club review. Motor's update improvement, Wisła's unchanged gate output and source-refresh limits are research questions to track across future fixtures, not reasons to select a model or threshold now. No claim that1200MAE has been reached.
