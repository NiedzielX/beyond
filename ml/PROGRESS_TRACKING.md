# Beyond Ticketing — ML Progress Tracking

## Rolling72 — November 8: coverage audited, input/label code prepared

[Stage A result and remaining gates](ROLLING_72H_STAGE_A_RESULT_2026-11-08.md), [reproducible aggregates](ROLLING_72H_COVERAGE_AUDIT_2026-11-08.json). Cached November7source:38fixtures/16clubs/29,063snapshotrows. First-observation+72h has19fixtures/13clubs; earlyP-50support has only1fixture/1club. These are **historical capture-time matches**, not PIT-proven validation, issued forecasts or new MAE. Missing ingestion clocks, stable-pool proof and per-sector histories remain unresolved in this export.

Separate `rolling72_features_v1` and `rolling72_labels_v1` implement arbitrary actual issue times, one-point prefixes, declared knowledge clocks, real6/24/72h history features and later genuine24/48/72h label matching. Frozen versions/ledgers remain unchanged. Prepared and tested code is not live ingestion, a fitted challenger, a deployed panel feed or proven prospective improvement. The old panel parser also rejects this new contract; an explicit new feed/version is required.

**Local source/store follow-up:** `rolling72_receipt_store_v1` now uses the real retrieval receipt as a conservative knowledge bound and appends immutable inputs/features to a separateSQLite. Actual cached-source capture at14:09UTC created38failed issues/114status rows, zero forecasts:33past-kickoff,2stale,3measurement-changed.256local tests passed. Receipt/store code395ef0ealso passed actual hostedDemandEngineSmoke42488648388/42488642850. At14:14:57UTC a subsequent3-GET/two-event bounded source refresh proved **2READYinputs→6READYfeature rows→local immutable store**, with all38old failedinputs preserved and idempotent retry. Source history gaps remain missing. This is not a forecast, panel or MAE proof; [source/store evidence](ROLLING_72H_FEATURE_STORE_PROOF_2026-11-08.json).

**Next:** exact benchmark/candidate precommit and model/dataset implementation; source/measurement compatibility for the1mixed-key fixture beyond72h remains a separate coverage blocker. Receipt-bound adapter/store have positive actual source proof for2stable-key fixtures, but no fitted challenger, persisted prediction or live panel feed has been proven. Preserve the diagnostic cohort as exposed and the30new-fixture/8-club review rule. Never invent old known_at clocks to turn cached historical rows into PIT evidence. No DBwrite, worker renewal, production activation or1200MAE achievement is claimed; defaultsfalse/0.

## Latest product priority — November 8: 48–72 hours to act

**Literature checkpoint before implementation:** [targeted review](ROLLING_72H_LITERATURE_REVIEW_2026-11-08.md) and [source-access registry](ROLLING_72H_LITERATURE_SOURCES_2026-11-08.json). Keep MAE/P50 aligned, add a separately precommitted conditional booking-curve baseline, audit sector coverage, evaluate advance warning quality, and separate forecast accuracy from causal price/ad revenue effects. No algorithm or1200MAE is guaranteed. Direct publisher access was403blocked; classic booking papersR12/R13remain metadata-only, explicitly not full-text verified. The completed capture-time coverage audit and new input/label contract are recorded above; no new fit, activation, worker renewal or DBwrite occurred.

**Whole sales lifecycle:** rolling +24/+48/+72 h forecasts start with the first genuine observed datum after sales open, including the one-observation case, and are re-issued throughout tracking. At P-50 the targets are P-49/P-48/P-47; at P-15 they are P-14/P-13/P-12. These are future horizons, not a final72h eligibility window or a requirement for24h of prior history. Preserve late-start/missing-history gaps and immutable issue times; existing frozen cold-start gates stay unchanged.

**Accuracy remains a core objective:** minimise genuine prospective event-balanced MAE and continue targeting **about 1200 seats attendance MAE** as a research milestone, with lower better. The rolling24/48/72h product adds forward commercial value; it does not replace the existing accuracy goal. Report each horizon/target/cohort separately and never substitute a low inventory-path score for attendance accuracy. No frozen gates, estimators or parameters change.

Full thesis, staged delivery and evaluation: [rolling72 commercial forecast plan](ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md). Coverage audit A is recorded above; the next step is fresh source capture and exact benchmark/candidate precommit before model fitting; the local receipt-bound feature store is recorded above. The next72hours are the MVP decision horizon from the first genuine observation, not a restriction to the final72hours before kickoff.

The user clarified the MVP again: **from the first genuine observation of a tracked match, forecast the next24/48/72hours and update from the full history actually known now**. This applies from early tracking, includingP-50, through kickoff. P-15is an example, not an eligibility cutoff; final24C1alone does not implement this product. Clubs need48–72hours to act on expected demand/sector changes if price/promotion/pool conditions remain as assumed.

Contract and DONE: [.ai rolling72spec](../.ai/specs/2026-11-08-rolling-72h-commercial-forecast-mvp.md). The path of the same measured variable starts from the last real observation; preserve each actual issue, predict future changes, then score against genuine later observations at+24/+48/+72. A first-observation/short-history route needs a separately versioned contract; never weaken old daily/drift/C1gates. Unknown interventions stayUNKNOWN; public availability does not prove paid sales or a causal price effect. Sector claims require actual comparable sector data. Attendance and inventory targets remain separately evaluated.

**Immediate product work:** audit existing dataset/model/serving against that contract, specify one new version before fitting, verify actual use of trajectory information, and prove real observation→persisted future path→panel→later observation→score. The historical final-attendance chart readsforecast_observations.final_p50and is not that path or median26. Existing dailyv1had zero relative-value-history coefficients; neither passing full prefixes nor a decorative plot proves learned dynamics. Keep existing frozen artifacts, exposed cohorts, missed observations and review gates unchanged.

The live-refresh guardian was a supporting operational WIP. It is **untested, unpublished, inactive and deferred**; source preserved privately, SDDremains open. No collectors were renewed or old source slots re-run during this scope clarification. This rolling72product acceptance is the current MVP priority; the existing terminal-attendance objective continues within its own lane. No new model/fit/deployment or measured72hour advantage is claimed. Defaultsfalse/0.

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

## Genuine postmatch results and recovered collection — November 7

Updated **13:10 UTC / 14:10 Europe/Warsaw**. Motor5091 actual attendance is **8,410**; Wisła448 is **31,849**. Source run42355072143 verified completed fixtures, appended history72/73 and created two genuine outcomes at08:22:42UTC. It then failed on the original history score-path defect. Preserve that failed state and all missed observations.

**Actual scoring recovered.** Published adaptere3bb70c before the12:08:57UTC relocation. The original partial score exactly matched one of96frozen genuine replays, was independently backed up and relocated byte-identically under exclusive locks. The12:09cycle persisted96prefix scores for two independent fixtures; complete private recovery was remotely restored. No model, prediction, issue clock or frozen assumption changed. See [recovery evidence](POSTMATCH_SCORE_RECOVERY_RESULT_2026-11-07.md).

Keep the cohorts separate:

| Evaluation | Independent scored fixtures | Latest-per-event MAE |
|---|---:|---:|
| Existing served C1 governed policy | 19 | 3331.314855 |
| Served C1 prior / raw | 19 | 3226.049075 / 6135.688243 |
| Paired support26 median26 governed | 2 new | 1878.052008 |
| Paired support26 Ridge20 governed | Same 2 | 1880.260933 |
| Paired support26 median20 governed | Same 2 | 2016.952489 |
| Paired original9 governed / stored prior | Same 2 | 4032.624269 |
| History augmentation raw / paired control raw | Same 2 | 3293.380472 / 3204.714092 |
| Fresh structural / own-lane matched prior | 2 new | 3536.609250 / 4032.624269 |

The existing served score-only RPC appended two scores; all17old public scored rows remained identical. Official window policy MAE3921.115012 is a different summary. Raw median20=1279.888537 and raw median26=1551.065813 are secondary outputs, not newly selected policies. Do not compare the two-event challenger mean with the19-event aggregate as a model gain. No tuning, winner selection, early rejection or promotion; **30new fixtures / 8clubs** review gates remain closed.

**Main C1 delivery is proven.** Isolated three-file [PR228](https://github.com/NiedzielX/beyond/pull/228) normally merged to main **bcec6b027e33a6ed6260d3ee469006c05f6f1010**. Lossless input transport repairs valid mixed ISO encodings while retaining original input and identical actual instants; frozen model/artifact/policy bytes are unchanged. Thirteen focused checks passed. Actual main run **42373112500 SUCCESS → DB predictions110→112**, new Górnik/Widzew forecasts before kickoff. Original failed run42347554854 and missed observations remain recorded. Research [PR227](https://github.com/NiedzielX/beyond/pull/227) stays a separate draft stack.

**Bounded attendance collection continues until November8 10:30UTC / 11:30Warsaw.** Source archivePID624595, support26 lossless readerPID625458, fresh structuralPID624625 and history score adapterPID624626 run every900seconds. Published4544421 preceded actual support replacement; Górnik captures succeeded. Old Widzew same-snapshot encoding conflict was retained; later snapshots qualify normally. Overnight source archive gaps stay missing: the history ablation may fail closed for later prefixes even when fresh structural qualifies. Standalone Ridge20/median20 capture stays paused.

**Forward outcome acquisition is running; postmatch completion is pending.** Immutable runtime ref `codex/forward-outcome-runtime-v4-2026-11-07` is fixed at **4dd7130dd93cc4fa4a801583f79387020afbd545**; never advance it with docs. Actual hosted pregame run **42374625183 SUCCESS** produced bothHTTP200 source pages, verified original raw recovery, two `NOT_POSTMATCH_3H` results, zero imports and independently restored private proof. Worker **PID630513** started13:01:28UTC with an actual successful local no-window cycle. Future source slots: **November7 19:45/22:30UTC and November8 08:20UTC** (Warsaw20:45/23:30/09:20); deadlineNovember8 10:30UTC. Full actual verification inputs/source backup precede append/scoring. Require future **source → DB outcome → successful unchanged scorer → expected score** before calling that chain DONE. [Contract, proof and operator paths](FORWARD_OUTCOME_CLOSURE_RESULT_2026-11-07.md). Never reuse expired V2/V3slots.

**Temporal diagnosis is complete, with no selection.** Existing read-only decomposition reconciled the19-event public metrics at13:02UTC;209immutable score/capture/clock/error/shared-benchmark checks passed. Motor median26 governed error827.93→201.12 over90prefixes; Wisła3554.98→3554.98 over6prefixes, with latest `insufficient_disagreement` retaining the prior. Final-hourMAE184.24contains **Motor only**. History raw is worse than its control on these two events; fresh structural changes the level but stays constant within its own captured prefixes. Even the diagnostic outcome-aware served prior/raw oracle is3052.636555MAE, so merely switching that existing gate cannot establish1200on this cohort. [Diagnostic and explicit denominators](C1_POSTMATCH_PREFIX_DIAGNOSTIC_2026-11-07.md).

**Separate daily inventory-path collection is renewed.** Original window runner475182 expiredNovember6 20:30UTC. Original published0f9a43fb source/artifact hashes match its locked contract. Consistent original daily/drift SQLite checkpoints and old state/launch were independently backed up/restored. New **PID631277** started13:07:24UTC on the same state, untilNovember8 10:30UTC. Actual no-window cycles executed zero full exports. Next genuine issue is event450 cutoff **16:30UTC**, eligible from16:40UTC. Future persistence remains scheduled, not yet proven. Local minute checks only; full exports run at legal windows. No old misses restored or redundant15minute full-history polling. Inventory-path MAE remains separate from attendance.

Source revision4dd7130 has478registered local checks and successful hosted Demand Engine/contract/public-source checks; main transport has separate13focused checks and actual hosted→DB proof. Workers depend on this cloud host and have explicit deadlines. Defaults remain **`production_change=false`, `live_adjustment=0`**.

## Active MAE work — 2026-11-06 13:51 UTC

Latest real background cycle **13:51:37 UTC SUCCESS** captured another genuine Motor prefix (snapshot36364, observation2026-11-06T13:43:02.861000+00:00, own issue2026-11-06T13:51:34.727782+00:00) and exercised the exact one-time unchanged later-clock retry. Both original issue hashes preserved; **2 prefixes /1 independent event /0 scored /null MAE**. New6-file82723-byte backup **bcad4af3a40387f8d48f5a4fcc64ca71623ed62844e82b93b56d9b6d5440ac43** remotely read/decompressed/hashed. This proves the operational retry in the actual background worker, beyond YAML or unit tests. No frozen code/model/clock changes.

**New information now has a genuine prospective test.** The unchanged frozen structural model has a separate history-refresh shadow: [protocol](STRUCTURAL_HISTORY_REFRESH_PRECOMMIT_V1.md), [evidence](STRUCTURAL_HISTORY_REFRESH_RESULT_2026-11-06.md), [PR225](https://github.com/NiedzielX/beyond/pull/225). Motor5091 observation13:23:02.260 / own issue13:32:22.997610 UTC / snapshot36354: fresh P50 **11,928.239260475439** versus actual stored prior **12,920.269297843897**, using7 genuinely later-known Motor home facts (86 guarded source records). This is a forecast change, not an MAE improvement. New lane: **1 captured event / 0 scored / null MAE**. Existing history-residual lane: **2 captured / 0 scored / null MAE**. Wisła's stale source remains missing in the new lane; do not backfill or relax freshness.

No fit or frozen-core repair. Source dd6083e published before activation13:16:42.673503; manifest7f2bad9 published before capture. Frozen collector's immediate validation used its earlier cycle-start clock; an unchanged actual-later repeat fully replayed and backed up the original issue. A separate tested operational watcher permits only that exact one-time validation retry, retaining all original forecast hashes. Active **PID486539**, runtime `/workspace/ops-runtime/2026-11-06-structural-history-refresh-collector`,900seconds, until **November7 10:30UTC**. Existing frozen model/source/protocol bytes remain unchanged. First fixed review remains30 new independent fixtures/8clubs; earlier scores descriptive only.

**Close the actual-label flow next.** [PR226](https://github.com/NiedzielX/beyond/pull/226) / [postmatch evidence](POSTMATCH_OUTCOME_CLOSURE_RESULT_2026-11-06.md). Public-source v2 hosted run **42227206213 SUCCESS**, both pagesHTTP200, original raw bytes recovered with exact run/attempt/head identity; private5-file133655-byte source backup independently restored. Pregame validation correctly produced2NOT_POSTMATCH_3H / **0 imports**. This proves retrieval/recovery/pregame guards, not postmatch DB import or scored MAE.

Active closure **PID487100**, runtime `/workspace/ops-runtime/2026-11-06-postmatch-outcome-closure-v2`, local60second checks; remote opportunities only **November6 20:20UTC,23:20UTC; November7 08:20UTC**, deadline **November7 10:30UTC**. Immutable execution branch `codex/postmatch-outcome-runtime-v2b-2026-11-06` at **b39ab8637f22da74bd0f5646ea55f67388b79120**: DO NOT advance it with review/docs commits. Source code keeps historical `*_v1.py` filenames but acquisition/storage contract isv2. The v1 worker was stopped before all scheduled dispatches/imports; failed hosted-lineage preflights remain recorded.

Only exact canonical fixture/time/competition, positive in-capacity attendance, actual postmatch receipt and independent completed sporting result permit append-only history creation/readback. Existing outcomes/history cannot be overwritten. Then invoke existing outcome-sync RPC and unchanged frozen scorers. Missing/conflicting sources stay unknown. Existing outcome-sync SQL alone is not proof of deployed cron or actual label ingestion. Next agent must inspect `latest-cycle.json`, `state.json`, each `source-run-*/apply-result.json`/`final-result.json` and actual DB rows before claiming the postmatch chain. No full-prefix feature RPC is added. Support26 lock is respected; old standalone Ridge20/median20 capture remains paused.

All **451 registered root tests pass**; original frozen residual and new frozen inference identities verified unchanged. Demand Engine/readiness checks passed on published source revisions; record final-head hosted status separately. Existing P9/encoder legal phases and IO mitigation remain in force, most old collectors endNovember6 20:30UTC. New workers are bounded and host dependent. Defaults stay `production_change=false`, `live_adjustment=0`; no automatic promotion, retrospective observations or promised MAE1200.

## Pure history staging finished — November6

CompletedthepreviouslyuncommittedadapterwithoutnetworkorDBwork:`ml/current_home_history_staging_v1.py`,15integritytests;all402registeredrootcheckspass. Actualrecoveredsourcepagesreproduceeveryfieldofall27originalappendpayloadrows,includingactualNov5verificationtimeandcorrectsource-runID. No data/model/forecast/source-contractchangeorfit. Sourceappend/real7-recordfutureconsumption/stagingSDDisnowimplemented;newattendanceMAEstillunproven. This supersedes the earlier IOhandoff'sWIP-adapter note. IOmitigation/readonly-admin-metricslimitandboundedworkerdeadlinesunderPR223remainunchanged.


## IO mitigation active — November6 12:05UTC

[PR223](https://github.com/NiedzielX/beyond/pull/223),source0f9a43fbpublishedbeforeactivation. OldRidge20/median20capturePIDs169529/200395paused;72/67forecastsbyte-verified,pairedbenchmarkscontinueinsupport26. History474192/priorguardian473151now900secondswithrealpostlaunchsuccess. Outcome-onlylocalbridge475181healthy(0truth→0remotechecks). Dailycutoffrunner475182completedactual11:15Koronaslotat11:57UTCincludingunchangeddaily/drift/privatebackup;laterminutechecksperformnofullexports. Allfrozenmodels/parameters/sources/gatesfalse/0unchanged,387root+hostedsmokesSUCCESS.

Measured1359P9+222encoderchecks/dated24h,1211P9no-window. Originalguardiansnowscheduledonlyknownphasesviahostdependentparents475523/475524:currentthrough12:45UTC,16:35–18:00and19:20–20:45,900secondpolling. Futurephasesnotyetexecuted. Currentencoderworkflow42214205780SUCCESS→fresh603/P1MODEL_INPUT_INSUFFICIENTDBattempt11:59:44UTC;no falseforecast/backfill,oldP7misskept. Mostcollectors/bridgesexpire20:30UTC,lastguardianphase20:45;do notpromisepermanentmanagedexecution.

DiskIOphysicalrecovery/rootqueryattributionunproven:admin/Managementbindingabsent,readonlydiagnosticSQLpreparednotrun. No mainworkflow/source-ingestion shutdown,DDL,paidupgradeorcleanup. Private56file582103bytebackupccd64824f4c0952c2cad74c7e944adf3741463b09a7d7e47e07b3dcf42e6533cindependentlyrestored. Report:`SUPABASE_DISK_IO_MITIGATION_RESULT_2026-11-06.md`. Rawhistoryfullprefixexportnowonlyatrealdailywindows(currently~6clocktimes/day),not96polls/day;thisisrequestworkloadreduction,notmeasuredserverIOpercentage.

New27recordconsumptionprovedMotor35680/Nov5 17:33→17:40forecast,home_n7;old17:03n0bytesunchanged. Newattendancepair2events/0labels/nullMAE. Dailyidentical-target4eventdescriptivedrift11.945442/model198.484646/persistence176.00stillbelow8event/5clubreview;notattendanceMAE. Reusablestagingadapterfrompriorworkremainsuncommitted/outsideIOrelease;append/coreconsumptionitselfdone.


## Supabase disk IO incident — November6 11:54UTC

User supplied actual provider warning. Paused redundant standaloneRidge20PID169529/median20PID200395;all72/67oldforecastsbyte-preserved. Support26continuesbothbenchmarks;do notclaimthepausedindependentstreamscontinued. HistorysidecarPID474192andpriorguardianPID473151actuallyrestartedtousing900seconds(not300),source/modelbytesunchanged,actualpostlaunchcyclesverified. DeadlinesremainNov6 20:30UTC. LocalfeatureRPCschedule12→4/hour;notameasurementofserverIO. Sourcearchive/support26stay900seconds.

Olddailyfullhistoryexportwas28019rows/7.57MBpercycle;workerexpired10:30UTC. DriftpreviouslyfailedStorageHTTP544at06:12. Newtestedlocalcutoffschedulerandoutcomescoringbridgeareimplemented,notyetpublished/launched.387registeredrootchecks pass. ActualscheduledGitHubhistoryhas36runs/24h,notquarter-hourYAMLcounts. Admin/Managementmetricsbindingabsent;read-onlydiagnosticSQLpreparedbutnotexecuted. Report:`SUPABASE_DISK_IO_MITIGATION_RESULT_2026-11-06.md`. No paidupgrade/indexDDL/cleanup/modelchange.

Newhistoryconsumptionfinallyprovenfromexistingimmutableevidence:Motor35680atNov5 17:33,ownissue17:40:44,home_n7,archivepre-observation. Old17:03zero-historybytesunchanged.27rowappenddataacceptancecomplete;purestagingadapterremainsuncommittedWIPandoutsideIOrelease. Newpair2capturedevents/0scored/nullMAE,no gainclaim. Defaultsfalse/0.


## New information actually appended — November5 17:26UTC

Targeted public audit/source recovery complete:27previously absent current-season home fixtures, Motor7/Korona6/Widzew7/Piast7; all match unique completed sporting home/away/date/result identities. Exact independent kickoff-hour proof remains unavailable; public reported clocks and historical publication limits preserved. Hosted source runs42073004397/42073601199and latestDemandEnginechecksSUCCESS,rawhashes/extractionindependentlyreproduced.

Appendverified at17:24:52UTC:history44→71,allold44rows/27outcomes/38same-timepriorresolutions/existingC1predictionsunchanged. Original900featurecellsreproduceoncurrent/planned/actualpostexports;allnewrecordsareexcludedat80oldtrainingobservations. No fits/oldpriorregeneration/outcomesync/backfill. Actual source archive71rowscompleted17:25:47UTCandprivatelyrestored. Remaining acceptance:later genuine prefix→newarchive→nonmissing residual homehistory, preserving the17:03forecast/sourcebytes and zero-historymanifest. MAEstillnullfornewpair;productionfalse/0unchanged. Report:`CURRENT_HOME_HISTORY_SOURCE_COVERAGE_RESULT_V1.md`. Separate appendSDDremainsactiveuntilactualconsumptionproof.


## Positive C1 capture and first paired path scores — November5 17:11UTC

Main materializer42070393174SUCCESS→DBMotor5091prior76actualgenerated17:01:57→real snapshot35663at17:03:01→support26immutable17:07:25→new history residual pair17:08:03. Newpair1captured/0scored/nullMAE, genuine pre-observation source archive and private recoveryverified. Motor verified-home count0; no fake history. MainC1workflow42071837843alsoSUCCESS→new Motor predictionindependentlyconfirmed inDB. ExistingC1scoreboard102predictionrows/18events/17scored, latestpolicyMAE3248.807865unchanged. Newpairisprivate, notDBserving. Report:`STRUCTURAL_PRIOR_WINDOW_GUARDIAN_RESULT_2026-11-05.md`.

New bounded dependency guardianPID358963publishedbeforelaunch(d906be4), actual17:07:06successfulno-duecycle,300sintervaluntilNov6 20:30UTC,hostdependent.12focused/360registeredrootchecks pass. Frozenmodels/defaultsunchanged; exact17:00cutoff availability is not claimed, no missed encoder/P9repair.

First matched daily inventory +1scores now2targets/2events/2clubs:driftMAE23.424246,dailymodel278.069754,persistence351.50. Descriptive only;8event/5clubreview remainsclosed. Originaldailycohortseparately8scores/4events,model238.338245versus226.00persistence;do not replace itwithmatchedmetrics. Report:`DAILY_PATH_PAIRED_COMPARISON_V1.md`. Actualcurrenthistorycoveragehas0acceptedcurrent-seasonhomefixturesforMotor/Korona/Widzew/Piast, versus5–7forother6futureclubs; new public-source coverage is the next targeted data question, not an excuse to backdate features.


## Genuine T1 dependency restored — November5 17:05UTC

The actual structural-prior workflow history had no visible run after11:35UTC despite configured15minute cron. At the genuine17:00opening a bounded/no-active/no-expired-ready preflight dispatched existing main materializer. Run42070393174SUCCESS; independent DB read confirms Motor5091/T-1 prior76, actualgenerated17:01:57UTC, canonicalcutoff17:00. Preserve its actual late generation and existing backfilled_pit_forecast metadata; never claim availability at17:00 or repair exact-cutoff misses. This enables later eligible C1 observations only. Frozen new residual models remain unchanged, future MAEstillnull. Separate structural-prior dispatch guardian implemented/tested(12focused,360registeredroot checks), publication/launch stillpending. Report:`STRUCTURAL_PRIOR_WINDOW_GUARDIAN_RESULT_2026-11-05.md`.


## Current execution — November5 16:45UTC

New history-support residual ablation is actually frozen and collecting privately. Artifact/launcher commitc3b37fdb22bb9df80b4f386a42dcaffea4e5fd40was published before watcherPID354725launched16:45:09UTC,300sinterval, untilNov6 20:30UTC. ActualprocessSsl and16:45:13post-launchcycleverified:0newforecasts/0scores/nullMAE,6fileprivatebackup3990bytes/SHA c6279daa611e7ba3a890db44890549336a8671ae9475015e8941d7b0ae07a930, read-back/decompressionverified. Use`python -m ml.launch_c1_history_residual_v1`, preserving the compatibility binding; frozen estimator/core/precommit bytes unchanged.348registeredrootchecks and hosted source/artifactDemandEnginechecks succeeded. Report:`C1_HISTORY_SUPPORT_RESIDUAL_RESULT_V1.md`. First new legal final24inputs begin17:00UTC, subject to original source/prior and genuine archive readiness. No new MAE claim;30newfixtures/8clubs review unchanged.

StrictP9freshchainisnow**PROVEN**:guardian16:31:03→heartbeat42065252556SUCCESS→child42065268900SUCCESS→Górnik449/T48newv1attempt16:31:47andfirstprediction16:31:48insidebuild/persiststep. DBv1now9attempts/1prediction/0scores;v2now8attempts/3predictions/3score rows(2events),newV1_COVEREDattempt. No localwriter/backfill. This satisfies full-chain operational acceptance, not accuracy or a new negative fallback-path test. Old603retry/failures/misses retain their scopes. Report:`P9_FRESH_HEARTBEAT_CHAIN_RESULT_2026-11-05.md`, private11file32243bytebackupindependentlyverified.

Existing median26/Ridge20/median20, sourcearchive, daily/drift, pairedmonitor and encoder/P9guardians remain unchanged. Next actual checkpoints:Motor5091/T24+encoderP1+firstC1final24at17:00UTC;Widzew7372/T48andLech451/encoderP3at19:15;Wisła448/T24+encoderP1at19:30(currentlynoinventory). Inspect live state before acting. Newworker/support26/sourcearchiveallstopNov6 20:30; other worker deadlines remain in their launchfiles. No production model changes, defaultsfalse/0.

## New history residual pair frozen — November5 16:37UTC

User-authorized fixed ablation is fitted exactly twice after source/precommit5d774451publication:one6featurecontrol/one9featurehistoryhead, same26/80/12exposed training. Freeze16:34:30UTC, control213bbe6f88ba98529606c9a5ddc640876649c3c4c89cddcd005ec9a9ff86e437/historyc11f0d9943bb33588140d8f0371db765bf2c222bbb204d59ad64260f89018e5f. No new-head training/old-holdoutMAE; futureMAEstillnull. Explicit recent-home level gap and actual6hchange have nonzero coefficients;24hvalue iszero(its missingness indicator isactive). This is mechanism metadata, not accuracy.

BuildCLIserialized__main__.ResidualRuntime; initial directinternal-sidecarinvocationfailedbeforeforecast. Use compatibilityentry`python -m ml.launch_c1_history_residual_v1 ...`or inlinebind`ResidualRuntime`beforeload_models. It preservesallfrozen source/artifactbytes, and80target-freeprobesprovebitwiseidenticaloutputs/0refits. Actual16:37:52compatibilitycycleverifiesmodels/currentreads/scorer/privatebackup,0forecasts/0scores/nullMAE. Initialfullprivatebackup28files/146043bytes/SHA0b306bed573faeae5a27a82a9eba10d79d0136bb80f17432480fb5fe882cc378independentlyrestored. Publishartifact/launcherbeforeboundedwatcheractivation; actualPID/launchproofwillfollow. Report:`C1_HISTORY_SUPPORT_RESIDUAL_RESULT_V1.md`.

## Authorized next MAE experiment — history-support residual ablation, before fit

User requested immediate continuation after the MAE plan. Source-consumption audit and target-free preparation are implemented. Exact separate protocol:`C1_HISTORY_SUPPORT_RESIDUAL_PRECOMMIT_V1.md`. Fixed6featurecontrol versus9featurehistory-augmented direct-person residual median, same26/80exposed training and fixed settings. Three new explicit history features use actual known-at/revision/season/canonical rules; new16imports are excluded from all old training observations. This tests a representation difference, not a new algorithm or historical improvement. No candidate fitted yet. Publish tested implementation/protocol before the two declared fits; genuine future source archives and unchanged30new-event/8-club review are required. Frozen models/gates/defaults remain unchanged.

## Panel monitoring correction deployed — November5 15:52UTC verification

Narrow frontendPR9normallymerged to panelmaincfb3d675d7fbb2cd4c6fc008f73c019ab33beb40; VercelProduction7578292659SUCCESS15:50:46UTC. Final-head and main TypeScript/build/Chromium checks succeeded. This release contains only ingestionmonitoring/test changes, not PR8daily-feed/C1cardwork. Exact reviewed tree/integrity verified. Current browser-role133rows classified by shipped code as24current/2elapsedunresolved, preserving all source data. Direct productionDOMwas not inspected fromthishost(networkblocked); successful productionartifactdeployment and actual component tests are independently recorded.

Root cause:DBprojectionfreshbutcandidatebranchesretainoldstatuses; UIpreviouslyfilteredonlyCOMPLETED_TRACKEDandfetchedonce. Newcurrent/historypartition, minute/focus/manualrefresh, lastgooddata/errorwarning and separateprojection/observationtimescorrect presentationwithoutsourcepromotion/backfill. Evidence:`PANEL_INGESTION_FRESHNESS_RESULT_2026-11-05.md`;31fileprivatebackup135051bytes/SHAad77322aa3e78d3b9d9b975cb41a2e75c64332baa5e3842460d843654eb0eb48independentlyrestored.

HistoricalrecipebacktestiscompleteinPR219withno demonstratedgain; exact frozen26futureMAEstillnull. ActualC1v8read15:52retains17/3248.807865/adjustment0; support26collector, pairedmonitor andP9guardianlivewithsuccessfulrecentcycles. NextfreshP9proof449/T48opens16:30UTC(17:30Warsaw); firstnewC1final24/sharedinventorytargets17:00UTC(18:00Warsaw). Preserve gates, no historicalmissbackfill. Manageddailyfeed/known-atservingstillundeployed/admin-bound; its blocker did not apply to this independentread-onlyUIrelease.

## Historical replay executed — November5 15:36UTC

User-requested fixed experiment complete:`C1_HISTORICAL_REPLAY_RESULT_V1.md`. All17actual scored fixtures/50prefixes, whole-fixture exclusion and fresh fold preprocessing. Chronological training9–20earlier label-known fixtures:rawmedian4558.29, median-policy3107.62, prior3131.16, persistedC1policy3248.81. PolicyDelta−141.19CI[−728.12,304.54]; first11policy4278.34worse than4121.45, later6single-prefixcontextfalls back toprior961.29. No full-history live-gain claim. New6labels were not known before any old cutoff, so expanded/base20chronological fits are identical.

Explicit non-temporal leave-one-fixture-out rawmedian-expanded3318.41versusbase20restricted2887.33,Delta+431.08CI[−416.74,1431.68]. All outcomes exposed; inherited historical publication-time limits remain. No demonstrated gain,1200unproven,no tuning/promotion. Actual frozen26was neither refitted nor scored on training fixtures; future collector unchanged.311registeredroot+189DemandEnginechecks pass; full discovery's7unrelatedCatBoostimporterrorsremain documented. Verified private independent recovery16files/185950bytes. Earlier before-fit section is dated history.

## Authorized historical recipe replay — November5, before execution

The user requested historical testing of the new median method. Separate precommit:`C1_HISTORICAL_REPLAY_PRECOMMIT_V1.md`. Evaluate17already-exposed scored C1fixtures/50actual-time reconstructed prefixes, with fresh fold-local preprocessing and whole-fixture exclusion. Fixed chronological training uses actual label knowledge and earlier fixtures; separate leave-one-fixture-out allows later data only as an explicitly non-temporal diagnostic. All26frozen training events remain exposed; no frozen26in-sample score or live model/source/gate change. No parameter search, retrospective prospective write, or production activation. SDD/run:`.ai/specs/implemented/2026-11-05-c1-historical-replay.md` /`.ai/runs/2026-11-05-c1-historical-replay.md`. At that before-run checkpoint, results were pending. The completed execution section above supersedes that status.

Last updated: **2026-11-05**

Status: **CANONICAL TRACKING SNAPSHOT**

Canonical MAE strategy: `ml/MAE_RESEARCH_ROADMAP_V6.md`

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`

Important: operational counters below are dated snapshots unless explicitly refreshed from live DB.

## P9 correction released — November5 12:22UTC

PR212merged normally; remote maine04033fcontains only its reviewed correction/contract files. Main-push P9workflowSUCCESS, independent heartbeat42026225277→child42026240780bothSUCCESS. Expected existing DBstate and original11:16attempt time unchanged, no duplicates. **Fresh heartbeat-created DBrow remains pending**; next eligible449T48at16:30UTCis protected by the guardian. No frozen model/parameter/eligibility change or C1promotion. Report:`P9_NONREADY_RELEASE_RESULT_2026-11-05.md`.

## Support26 median frozen — November5 11:58UTC

User-authorized data-only20→26support comparison implemented and fitted once after source/precommit publication1bdfc8f. Same frozen median20 preprocessor,30features, learner parameters, weights and policy. Estimator29839c647277d91b333d5a23d7f337250dae4c11d36cc3692b78af668ece57d3; existing artifacts/source hashes unchanged. Actual11:59current no-due cycle and independent private model+training restore verified;0futureforecasts/0scores/nullMAE.293root checks,23new tests and two hosted pre-fit jobs pass. Artifact publication/bounded launch next; first possible source window today17:00UTC.30new-event/8-club review unchanged. Report:`C1_SUPPORT26_RESULT_V1.md`. Dataset26is now training for this separate package, never validation.

Collector activation verified12:06UTC:artifact08dc634published, PID320703alive, successful actual cycle/private recovery, every900suntilNov6 20:30UTC. All non-skipped artifact checks pass. New score remainsnull; no predictive improvement or promotion established.

## November5 continuation —11:04UTC

Later11:20update: actual603T48heartbeat42017429991SUCCESS→P9child42017444883FAILURE; genuine v1attempt and separate local zero-prediction v2attempt confirmed11:16UTC. DBcounts8/0/0and7/3/3respectively; v2still2independent scored events. No hosted-chainDONEor new accuracy. Corrected helper remainsPR212/unmerged. New bounded main-heartbeat guardian has7unit tests and awaits publication/launch; it changes no model/DBevidence contract. `P9_HEARTBEAT_GUARDIAN_2026-11-05.md`.

11:23execution:guardian source328f533publishedPR216, actualPID315508live, initial fresh no-due cycle verified; deadlineNov6 11:20UTC.270root checks pass. Private15fileP9recovery verified; no claimed hosted-success chain, target forecast or model improvement.

- Current persisted C1diagnostic complete:17/17scored, policy3248.81vsprior3131.16andraw6241.96; four largest failures68.50%, outcome-aware oracle2949.38DIAGNOSTIC_ONLY. Six new tests, nofit/thresholdchange. `C1_CURRENT_ERROR_DECOMPOSITION_RESULT_V1.md`.
- Published dataset26is prepared training only:26fixtures/12clubs/80rows, original74rowsbyte-preserved, no successor fitted. Existing Ridge20/median20remain0newforecasts/0scores; future review30events/8clubsunchanged. `C1_TRAINING_DATA26_SNAPSHOT_V1.md`.
- Daily/drift/encoder guardians renewed after genuine09:30expiry; actual10:52post-launch cycles verified, untilNov6 10:30UTC. Existing C1/raw-source workers survived, with recent verified private backups. No missing issue fabricated.
- Widzew7372encoderP3captured Nov4 19:16:53UTCfail-closed; Wisła448P9T48remainsMISSED_WINDOW. P9corrected hosted chain and managed source/feed release still pending.
- Identical-target daily-model/drift/persistencecomparison implemented:53paired future points,0scores/nullMAE; original daily188.98vs163.25on4eventsis a different scope. Seven new tests, byte-unchanged ledgers. `DAILY_PATH_PAIRED_COMPARISON_V1.md`.263registered root tests pass; existing frozen models/source hashes verified unchanged.

---

## User-requested daily-path MVP — 2026-11-03 update

The latest user instruction requires **genuine observed prefix → predictions for every remaining day**, updated daily. Terminal attendance alone is insufficient for this product deliverable. The parallel error-driven attendance research programme below remains canonical; the new inventory-path lane has its own observable target, baseline and metrics and does not replace attendance evidence or its 550-seat contract. Partner transactions are unavailable for MVP and are not a prerequisite.

Implementation: [`DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md`](DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md). Deployment/recovery: [`DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md`](DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md). Formal lane precommit: [`DAILY_INVENTORY_PATH_PRECOMMIT_V1.md`](DAILY_INVENTORY_PATH_PRECOMMIT_V1.md).

Current operational counters, watcher health and deadlines belong in `NEXT_SESSION_HANDOFF.md` and the live runtime status command. Verified milestones:one frozen daily-path model; genuine post-freeze local captures and private backup/restore; hosted panel TypeScript/build; isolated PostgreSQL16persistence and typed panel-feed contract tests(run41810511980). These test milestones do not prove the undeployed SQL/Edge/scheduled workflow in live Supabase. No private partner transactions, production activation or old-model retuning is required.

The attendance history read on2026-11-03 ended at2026-10-25. The six tracked fixtures onOctober30–November2 had no confirmed outcomes in `ticket_event_outcomes`; zero attendance scores are therefore not evidence of zero error. Keep this source-ingestion blocker separate from daily inventory-target scoring.

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

---

# 2. MAE research programme status

| Work package | Status | Current decision |
|---|---|---|
| MAE-01 — Incumbent error decomposition | ✅ HISTORICAL DIAGNOSTIC COMPLETE |603events; all10frozen MAEs reproduced; see `MAE01_INCUMBENT_ERROR_AUDIT_RESULT_V1.md`; hosted checks passed in run41711896063 |
| MAE-02 — Structural baseline benchmark | ✅ BOUNDED AUDIT COMPLETE | weighting-only variant rejected; simple anchors worse; frozen Pre-Live v3 research anchor reconciled; see `MAE02_SEAT_WEIGHTED_MEDIAN_RESULT_V1.md` |
| MAE-03 — Context residual model | 🟡 AUDITED / DATA_BOUND | form/standings/opponent/fixture/odds; squad only with trustworthy PIT-safe source |
| C1liveMAE1200 — separate training expansion | 🟡 FROZEN / CLOUD COLLECTING | matched audit complete;20eventnewtrainingpackage; realpost-launchno-duecycle;0futureforecasts/0scores, MAEnull;30new-event/8clubreviewpending |
| MAE-04 — Engineered trajectory benchmark | ⚪ QUEUED | velocity/acceleration/deltas/plateau/surge/density/similarity |
| MAE-05 — Horizon-specific correction | ⚪ QUEUED | test whether early vs late horizons need distinct residual logic |
| MAE-06 — Demand-regime / club heterogeneity | ⚪ QUEUED | investigate low/normal/near-sellout and club bias without brittle per-club models |
| MAE-07 — Controlled ablations | ⚪ QUEUED | structural vs context vs trajectory vs combined on same events |
| MAE-08 — Ensemble / calibrated blend | ⚪ QUEUED | only after independently useful signals show complementary error |
| Sequence-model expansion | ⏸ CONDITIONAL | proceed only if simpler trajectory evidence justifies representation complexity |

Research method:

`measure error -> classify residual failure -> state hypothesis -> add one information family/mechanism -> event-grouped PIT-safe test -> update scoreboard -> freeze/reject -> repeat`

---

# 3. Existing frozen / collecting evidence

Latest detailed machine-state values in the prior snapshot were from **2026-10-30**. Query live DB before using them as current counts.

| Item | Recorded status | Current decision |
|---|---|---|
| P7 prospective | 🟢 COLLECTING | collect/score only |
| P9 prospective v1 | 🟢 COLLECTING | correct fail-closed; protect genuine windows |
| P9 Family Fallback v2 | 🟢 COLLECTING | separate evidence only |
| Form5 prospective | 🟢 COLLECTING | genuine outcomes only |
| Long72 | 🟡 FROZEN | keep frozen evidence separate |
| P11 odds | 🟡 COLLECTING | useful future context family when PIT-safe coverage supports testing |
| P4a | 🟡 COLLECTING | gate remains evidence-driven |
| Daily trajectory infrastructure | ✅ DONE | PIT dataset + immutable evidence backend |
| Lane A v1 | ❌ REJECTED | MAE 4153.34 vs 2594.54 incumbent |
| Lane B v1 | ❌ DO NOT ADVANCE | MAE 2595.40; near-zero correction |
| Lane B v2 | ❌ MECHANISM NOT SUPPORTED | MAE 4792.42; harmful over-correction |
| Supervised tuning on exposed cohort | 🛑 STOPPED | no post-hoc repair |
| SSP trajectory v1 | ✅ REPRESENTATION_SUPPORTED | target-free representation result only |
| SSP encoder | ✅ FROZEN | immutable v1 artifact |
| Frozen attendance head v1 | ✅ FIT ONCE / FROZEN | Ridge alpha 10, cap +/-10% |
| Frozen encoder prospective shadow | 🟢 COLLECTING | P-7/P-3/P-1; production off |
| Business meaningful Delta MAE threshold | ✅ FROZEN FOR ACTIVE COMPARISON | `Delta MAE <= -550 seats` plus risk guards |

---

# 4. Closed supervised trajectory evidence

## Lane A v1

- incumbent MAE: 2594.54;
- Lane A MAE: 4153.34;
- Delta: +1558.80;
- decision: `REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`.

## Lane B v1

- Lane B MAE: 2595.40;
- Delta: +0.87;
- near-zero corrections;
- decision: `DO_NOT_ADVANCE`.

## Lane B v2

- Lane B v2 MAE: 4792.42;
- Delta: +2197.88;
- harmful over-corrections;
- decision: `MECHANISM_NOT_SUPPORTED`.

Conclusion:

> **Do not keep tuning supervised correction mechanics on the same exposed 10-event cohort.**

This conclusion does not prohibit new separately versioned research questions under Roadmap v6.

---

# 5. SSP v1 result

Precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Result:

`ml/results/trajectory_self_supervised_24h_delta_v1_result.json`

Frozen target-free sample:

- 26 usable events / 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / 3397 pairs;
- 5 validation events / 168 pairs.

Result:

- zero-change event-balanced MAE: **0.0917223592**;
- model event-balanced MAE: **0.0628961688**;
- Delta: **-0.0288261905**;
- improved validation events: **5/5**;
- attendance labels used: false;
- structural prior used: false.

Decision:

`REPRESENTATION_SUPPORTED`

Encoder artifact:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Do not interpret this as attendance accuracy evidence.

---

# 6. Frozen encoder attendance head v1

Candidate ID:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Frozen head artifact:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

Protocol:

- frozen 8-d SSP encoder embedding;
- Ridge alpha 10;
- residual-ratio target;
- +/-10% correction cap;
- exact 10-event / 19-row exposed fit cohort;
- no historical candidate selection;
- no historical MAE-based tuning;
- P-7 / P-3 / P-1 prospective only.

The candidate remains frozen. New Roadmap v6 experiments must use new versions/lanes rather than modifying this artifact.

---

# 7. Current data/source semantics to preserve

Public inventory is a demand/inventory proxy, not confirmed sales or attendance.

P-60 is a collection horizon, not a requirement for fabricated full history.

Never forward-fill or interpolate merely to create model input.

Hidden/unknown inventory is never zero.

Known source findings remain fail-closed:

- Motor historical inactive-stage zeroes remain historical and are not rewritten;
- Korona hidden availability remains unknown, not zero;
- Widzew structural prior is resolved; source inventory semantics remain separate;
- Wisła Kraków VAO diagnostic observed **6,870 `occ=0` seats but 0 public-selectable seats under rights semantics**; do not promote those seats without confirmed rights.

---

# 8. Mandatory MAE experiment scoreboard

Every serious Roadmap v6 experiment must register:

| Field | Required |
|---|---|
| Experiment/version ID | yes |
| Hypothesis | yes |
| Incumbent/version | yes |
| Independent events | yes |
| Distinct clubs | yes |
| Coverage | yes |
| Incumbent event-balanced MAE | yes |
| Challenger event-balanced MAE | yes |
| Delta MAE | yes |
| Event improvement rate | yes |
| Median event Delta AE | yes |
| P90 AE / worst-event degradation | yes |
| Signed bias | yes |
| Per-horizon MAE when relevant | yes |
| PIT audit status | yes |
| Decision | yes |

Human-readable registry:

`ml/MAE_EXPERIMENT_SCOREBOARD.md`

---

# 9. Immediate order

1. Read `ml/MAE_RESEARCH_ROADMAP_V6.md`.
2. Query `public.prospective_decision_summary_v1(10)` for fresh live state.
3. Protect an immutable legal cutoff only if one is currently at risk.
4. Never backfill a missed prospective row.
5. Keep frozen prospective candidates unchanged while evidence accumulates.
6. MAE-01 historical diagnostic is reproduced; MAE-02 weighting audit rejected the variant; MAE-03 context audit is complete and data-bound; collect genuine variable context and validate prepared daily-path SQL in an isolated DB, preserving existing C2 rejection and Pre-Live v3 anchor.
7. Use the decomposition to choose the next falsifiable PIT-safe hypothesis instead of guessing a feature.
8. Follow MAE-02 through MAE-08 in evidence-driven order, skipping/reordering only when the preceding evidence clearly justifies it.
9. Update `ml/MAE_EXPERIMENT_SCOREBOARD.md` after every serious challenger.
10. Keep production review-gated and OFF.

## Daily-path diagnostic findings before first outcomes —2026-11-04

Exact coefficient audit:`DAILY_PATH_COEFFICIENT_AUDIT_2026-11-04.md`. All120relative-value-history coefficients are0;57issued points reconcile exactly to latest level/scale plus negative global/observation-pattern terms and clipping. No future accuracy claim, v1retuning or new learner. Separately versioned research should test a restrained genuine-prefix-change mechanism against persistence after its own precommit.

Prefix-regime diagnostics passed8hosted tests(run41816697000), preserve the full-cohort primary denominator and do not drop all-zero cases. Prepared source-statev2passed actualSQL→features integration(run41816696989),20SQL+13adaptercases; project deployment remains blocked.

The separately precommitted fixed24-hour drift comparator was implemented/frozen at11:06:27UTC(SHA332f6fd37bc2a09ce665668ef3c9c23d8d34ec3613f18435ec729d95d3bb43cf). Thirteen tests passed in hosted309-check run41818376777. Actual no-due cycle:0new attempts/points, nullMAE, verified private backup and byte-identical originalv1inputs. Bounded sidecar collecting only new legal post-freeze issues; no old-prediction backfill or fitted-model replacement. That first snapshot preceded a legal issue. First fail-closed drift capture is now proven in `FROZEN_WINDOW_GUARDIAN_EVIDENCE_2026-11-04.md`; READYforecasts and genuine drift labels remain pending.

At11:20UTCthe full guardian→encoderworkflow→success→expected DBattempt chain was proven for Korona603/P-3(run41819915267,DBattempt11:19:48UTC,MODEL_INPUT_INSUFFICIENT). Encoder9/5/0; P9v1 6/0/0,P9v2 5/3/0. Source contracts and historical misses unchanged. Separate localv1captured its8thattempt; drift watcher captured its1stlegal fail-closed attempt with verified backup. No READYdrift forecast/score yet. Evidence:`FROZEN_WINDOW_GUARDIAN_EVIDENCE_2026-11-04.md`.

## C1 same-time audit completed —2026-11-04 12:20UTC

`C1_LIVE_MATCHED_AUDIT_RESULT_V1.md`: all11events /44exact C1-time representatives retained. C1policyMAE4121.45, D2P2MAE5157.52; do not promote D2from the old later-time event5comparison. C1numerical replay matches,900old training cells verified; frozen D2development and original event5goldens reproduce. Wisła/Górnikactual prior metadata have zero season home history; source queue18history checks+6missing outcomes, no guessed labels. External source revalidation blocked. Separate one-factor9→20training-support experiment is precommitted in `C1_TRAINING_EXPANSION_PRECOMMIT_V1.md` before fitting; oldv8and all prospective gates unchanged. All20become training, never fresh holdout. New future evidence required.

### C1 training-support challenger actually frozen —12:27UTC

See `C1_TRAINING_EXPANSION_RESULT_V1.md`. New separate20event/74rowpackage frozen once12:26:39UTC, estimatorSHA04dbdf1e5b8846782194f2ca1e833078a10238d1c9ca151b8391a869449027ba; original30features/Ridge10/policy unchanged. No training-MAEclaim. Current DBinference12:27returns0eligiblecandidates/0predictions/0scores; MAEnull. Privatefreeze/input/lineagebackupbyteverified. Separate bounded collector ACTIVE PID169529untilNov6 20:30UTC; actual12:37:41UTCpost-launchno-duecapture→scorer→verifiedprivatebackupcycle.0forecasts/0scores, MAEnull. Lockedcollector/scorerimplementation; futurepositivecapturepending. FirsteligiblewindowNov5 17:00, later than oldworkersdeadline. Candidate needs genuinefuturepairedforecasts and30newscored events/8clubs. No oldmodel/score/gateway/productionwrites.

## Accepted literature execution supplement —2026-11-04

User authorized `C1_MAE_LITERATURE_EXECUTION_SUPPLEMENT_V1.md`: baseline-history completeness, bounded live-objective novelty/contract audit, separately precommitted dynamics mechanism and future paired evaluation. This expands the research programme beyond the20eventtraining expansion; it changes no frozen candidate or review gate. StructuralT1alreadyusesL1; C1v1/v2alreadytestedL1trees; weighting-only experiment rejected. Next objective experiment must identify its exact difference before fit. Public source revalidation remains blocked. Panelwork proceeds separately: existing public browser-readable C1scoreboard added to preview; daily-pathlivefeed stillundeployed. Productionoff.

## Current execution snapshot — 2026-11-04 17:36 UTC

This supersedes earlier dated operational counters. Existing frozen models, review gates, historical misses and production flags remain unchanged.

| Lane / target | Latest genuine evidence | Current interpretation |
|---|---|---|
| Original C1 v8 attendance | 101 prediction rows / 17 events / 16 scored; policy MAE 3428.29, prior 3303.29, raw 6540.76 | Five delayed genuine outcomes expanded the cohort; the old 4121.45 on 11 events is not a model-improvement comparison |
| Expanded Ridge20 attendance | Frozen once at 12:26 UTC; 0 future predictions / 0 scores / null MAE | Collect only new final24 observations |
| Direct-person median attendance | Frozen once at 13:44 UTC; separate verified worker cycle; 0 predictions / 0 scores / null MAE | Same 20-event / 74-row training information; no training-MAE claim |
| Frozen encoder attendance | 10 attempts / 6 predictions / 3 scores; MAE 1529.71 vs 923.27 | Early worse results; no promotion or retuning |
| P9 v1 / v2 attendance | v1: 7 / 0 / 0; v2: 6 attempts / 3 predictions / 3 score rows across 2 events | v2 event MAE 1984.72 vs 1248.35; keep lanes separate |
| Daily v1 inventory | 2 mature points / 2 events; MAE 258.94 vs persistence 326.50; 71 points pending at 17:14 | Availability is a separate target; 1 of 2 events improves; too early for a decision |
| Fixed drift inventory | 5 attempts / 16 future points / 0 scores at 17:27; 2 READY issues | Actual post-freeze forecasts now exist; no drift-MAE claim |

### Completed data work and remaining source boundary

Inserted 15 verified absent history records at actual knowledge time 17:18:36 UTC and synced five exact outcomes: 6, 443, 444, 446, 447. Old outcomes and forecast counts remain unchanged; 900 original training cells reproduce before and after import. Event445 remains missing because source and canonical kickoff differ by 10 minutes. See `VERIFIED_ATTENDANCE_IMPORT_RESULT_2026-11-04.md`.

The existing history view / C1 export / structural Edge feed omit source knowledge timestamps. A separate guard now preserves actual availability and connects to the unchanged frozen feature builder. Actual Górnik449 / T-3 input audit: unfiltered season_home_n=6 versus correctly known=1 at the 16:30 cutoff. All 15 new records are excluded before ingestion and available at the later actual read. The registered PKO competition alias is handled explicitly. This is tested input integration, **not deployed serving enforcement**. Never regenerate old priors using newly obtained history. See `ATTENDANCE_KNOWLEDGE_TIME_AUDIT_V1.md`.

### Automation and immediate next actions

1. Finish the separately versioned raw-source export → per-cutoff guard → unchanged predictor integration and its release verification. Do not change frozen collectors to repair old evidence.
2. Protect Widzew7372 / P-3 at **19:15 UTC (20:15 Warsaw)** and Wisła448 / P9 T-48 at **19:30 UTC (20:30 Warsaw)**. Invalid or absent inventory remains a coverage failure.
3. P9 heartbeat run41873299368 succeeded but child41873320229 failed on a non-ready zero-neighbor freeze. Main-based draft PR212 fixes only that negative path; hosted contract tests pass. An actual in-window local DB attempt was recorded at17:17 UTC. **P9 redundancy remains NOT DONE** until corrected hosted execution succeeds and produces the expected DB record. No main merge occurred. See `P9_NONREADY_OPERATIONAL_FIX_2026-11-04.md`.
4. The distinct positive encoder chain is proven: guardian → mainrun41867901421 SUCCESS → Górnik449/P-3 immutable prediction_id6 at16:31:16 UTC. This does not prove the P9 chain.
5. Original daily/drift/guardian workers stop **Nov5 09:30 UTC**; both C1 research collectors stop **Nov6 20:30 UTC** and depend on this host. Median PID200395 has an actual post-launch capture → scorer → verified private backup cycle and a separate byte-verified restore. Inspect process state and current cycles before renewal. First possible new C1 final24 window: **Nov5 17:00 UTC (18:00 Warsaw)**. First review remains 30 new scored events / 8 clubs.

Panel PR8 has a successful Preview and an independent C1 accuracy card. Its public browser-role endpoint now returns the actual16-event / 3428.29 result. Production main and the new daily-path livefeed deployment remain unchanged / pending. No production activation: `production_change=false`, `live_adjustment=0`.

## Input-contract continuation — 2026-11-04 18:10 UTC

The separate raw-source export → per-event knowledge/revision guard → unchanged frozen predictor implementation is complete in draft [PR213](https://github.com/NiedzielX/beyond/pull/213), initially published asdf4fc02. Actual source counts:43history /26outcomes /38ticket events /135sporting fixtures /20aliases; one due target is not ready, so actual inspection produced0forecasts. Synthetic integration matches the original predictor's complete output for already known data; no fit. Managed serving is still unchanged: this output is explicitly non-persistable and activates no new prospective lane.

Private source snapshots are now actually collecting: PID209974, runtime `/workspace/ops-runtime/2026-11-04-known-at-source-archive/`, every900seconds until **Nov6 20:30UTC**. Published source/dependency hashes and exclusive lifetime/runtime locks are enforced. Post-launch18:08:50UTCcycle captured, privately uploaded, read-back and restored;12,105bytes, SHA9a47abe50d656453128815da5e22e58a86be3c37d03af09b2a451a22acbd713e. This collector never predicts or writes official forecast/outcome rows. It depends on this cloud host.

A separate read-only as-of reader now selects the latest verified snapshot at/before an elapsed cutoff, within60minutes, and verifies source/recovery identity. Actual18:10lookup selects the18:08:49capture;16:30lookup honestly returns no pre-cutoff archive. Five tests include later source revisions and corruption; no backfilled history or forecast. The archive/predictor sources are unchanged after their collection hash lock.

Actual old managed process created Górnik449/T-3prior74at17:55:18UTC, with canonical16:30cutoff andseason_home_n=6, confirming the consumer gap. Newly verified source history was not known at16:30. Preserve the record and actual generated_at; do not use it as evidence available at the earlier cutoff. This lane did not write that prior. Release of guarded managed serving remains a separate task; no old priors/forecasts are overwritten.

Fresh18:10C1read remains101rows /17events /16scored, policyMAE3428.29vsprior3303.29. All five earlier workers remain live; their deadlines and frozen gates are unchanged. PR211headc058e93nowhas all non-skipped hosted checksSUCCESS; new PR213 validation is separate. Evidence and commands: `STRUCTURAL_KNOWN_AT_INPUT_INTEGRATION_V1.md`.

## Last tracked outcome resolved — 2026-11-04 18:32 UTC

All six tracked Oct30–Nov2 outcomes are now present. Event445 is supported by an exact independent official fixture schedule/date/result and the matching primary provider attendance3396. The primary18:10display is retained as a discrepancy; its cause and independent official attendance corroboration remain unverified. No canonical time was changed or generalized tolerance introduced. Actual append-only history/outcome write18:29UTC; old outcomes, forecasts and frozen hashes unchanged. Across the two source tasks:16new history records and6genuine outcomes. Evidence: `OUTCOME445_COMPOSITE_VERIFICATION_RESULT_V1.md`.

Fresh C1v8 status: **101rows /17forecast events /17scored, latest policyMAE3248.807865, prior3131.157876, raw6241.964642; window policy3913.558409**. Older4121.45/11 and3428.29/16 remain dated scopes; no model improvement is inferred from cohort growth. Encoder now4scores/4clubs, MAE1623.917287vs1051.043479; P9v2 unchanged1984.717101vs1248.354372on2events. Keep all frozen review gates and no promotion. Both newer C1challengers still0future scores/nullMAE.

The source archive, as-of reader and frozen-predictor boundary in PR213 are implemented/tested; the bounded archive is collecting. Managed serving still needs its guarded release, and P9PR212stillneeds the actual corrected hosted chain. Protect genuine19:15/19:30UTCcheckpoints; never backfill missed observations. `production_change=false`, `live_adjustment=0`.
