# Historical blind rolling24/48/72h result

Actual run **November10,10:41:45–10:41:48UTC**, after published precommit01294a3 and tested code8a695f1. [Machine proof and full metrics](ROLLING_72H_HISTORICAL_BACKTEST_RESULT_2026-11-10.json).

The user-proposed test is complete: train the same fixed recipe only on earlier otherfixtures; issue retrospective predictions from each actual prefix; seal all predictions; then open separate target observations and score. All prefixes of the testfixture stay outside training. No random snapshot split, active-v2artifact reuse, hyperparameter search or post-result refit.

| Horizon | Model MAE | Persistence MAE, same cases | Independent fixtures | Paired points |
|---|---:|---:|---:|---:|
| +24h | 213.91 | 334.70 | 15 | 111 |
| +48h | 347.35 | 551.01 | 14 | 96 |
| +72h | 452.96 | 780.10 | 14 | 82 |

MAE is averaged within fixture and then equally across fixtures. Candidate improvements versus persistence are approximately36%/37%/42%. These are **public availability errors**, not paid-sales/attendance MAE; they do not establish the1200-seat attendance milestone or current live accuracy.

Coverage is explicit:31completed selected fixtures/300featureorigins/900horizoncoordinates. There are698matched target observations,25stale targets and177postkickoff statuses. Warm-up support5fixtures/3clubs/60rows leaves434candidateNO_FITcoordinates;289candidatepredictions are numeric, scoring111/96/82points byhorizon. Eight diagnostic fits use12distinctsupportsets. Candidate testcoverage is15fixtures at24h and14at48/72h, not31 scoredcandidatefixtures. Early missing history and literal zero remain real cases; no difficult target was removed after MAE.

The stronger drift comparison has its own exact common coverage: model125.70vsdrift178.63(+24h,95points),229.91vs333.25(+48h,80points),321.68vs503.07(+72h,66points), each15/14/14fixtures. Do not compare those reduced-cohort model numbers with the primary table. The fixed10000replicate fixturebootstrap72h candidate-minus-drift interval crosses zero (−464.09,+10.65); historical mean improvement is not proof of a reliable72h advantage. Conditionalpickup comparisons and all strata are inJSON.

Material risk retained: worst candidate errors are9450/9221/8671available places. Public availability can change through inventory release/measurement effects, not ticket buying alone. Current proxy/model does not certify a stable released pool. Historical ingestion and metadata-version clocks remain unproven; all historicalfixtures were previously exposed. This is a capture-clock retrospective diagnostic, not a fresh holdout/PIT/prospective promotion decision. It tests the fixed recipe in chronological folds, not the already-fitted live artifact on its own training data.

All900predictions/statuses were sealed at10:41:48.150304UTC before the scorer read truth. Originalactive-v2model byteSHA remained b4707d3e… unchanged; original prospective ledgers/models/gates/defaultsfalse/0 were not rewritten. New private diagnosticmodels are explicitlynonservable. Twenty-two synthetic contracts passed, including futuretraining-label/vaultpoison isolation, macro event weighting and refusing modified seals. Code/CI publication and actualsource-run proof are distinct.

Next: preserve this result without retuning the frozenlivecandidate; obtain its genuine24/48/72h outcomes and investigate the retained large inventory jumps. Resume verified fixture-admission repair to obtain genuinelynew matches; the sourceauditalreadyidentified exactH1date/participant parsing defects and a Lechdateconflict. Do not loosen leagueconfirmation or30newfixture/8clubreview gates.
