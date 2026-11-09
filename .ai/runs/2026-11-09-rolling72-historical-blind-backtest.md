# Historical blind24/48/72h backtest

ActualstartNovember9 20:00UTC. Status: PRECOMMITTED_BEFORE_REAL_FIT.

User explicitly asks why not train on pastmatches and predict future24/48/72h without exposing held-out outcomes, then reveal and score them. We agree and implement this now. The existing v2one-fit artifact cannot fairly test its own23trainingfixtures; preserve it and create a separatelyversioned chronological event-heldout replay with the identical fixed HGB recipe, no search/retune/production change.

Exactprecommit4acdfd98…created20:02:06UTC. Feasibility only:31selectedcompletedgroups,29withmatched labels,23commontraininggroups,300eligibleorigins/900horizons,698matched/25stale/177postkickoff.259matched-origin clocks yield12distinctpast-supportsets;102ofthoseoriginclocks satisfy5/3/60. These are support counts, not errors. Select testfeatures before targetavailability; separatetruthvault andpredictionchecksumseal before scoring. Historicalknowledge/metadata clocksunproven, alloldfixturesexposed, event-balancedavailabilityMAE/horizon separately fromattendance1200goal.

Parallel agents own privatepacketbuilder and prediction/scoringengine, with syntheticcontractchecks. No realfit/MAE before allcode published and sourcebindings verified. Existingv1PID931348 andv2PID936149 continue theiractualfuture windows unchanged. Source-discoveryaudit has finished: actualcandidateH1dateparser/teamnamebug, existingleaguepairs andLechdateconflict recorded; parserrepair deferredundernewuserpriority. No gate orsource/model rewrite.
