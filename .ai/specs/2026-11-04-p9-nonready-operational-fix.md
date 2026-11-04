# P9 v2 non-ready input operational fix

Incident17:00UTC: heartbeat→P9workflow41873320229recordedMotor5091v1PIT_SUPPORT_INSUFFICIENT, then crashed at v2len(neighbors)==5for a legitimate non-readyP9afreeze withzero neighbors. Existing schema accepts non-ready v2support failure; no eligibility relaxation or new prediction allowed.

Fix in isolated main-based worktree: known freeze_ready=false/reference_ready=falseand<5neighbors yields an existing FALLBACK_SUPPORT_INSUFFICIENT diagnostic with zero predictions. Unknown/contradictory readiness or oversized neighbor sets stay rejected; all valid five-neighbor results remain exact. Before-edit goldens recorded four original synthetic cases; compare full output afterfix. Test0–4neighbor failures, malformedmetadata rejection and originaltargetleakguard.

No threshold/model/reference reranking, newSQL ormainmerge. Publish focusedreviewablehotfix. An in-window local execution may record the actual still-open failedcoverage attempt viaexistingservice-roleRPC; never backfill after18:30UTC. Mainworkflow success/DBchain cannot be claimed before actual corrected hostedexecution. Preserveoriginalworkflowfailure. Sharedrunlog tracks bothresultandremainingdeploymentgap.

Executed:main-baseddraftPR212commit794f74a,hostedcontractSUCCESS;actualfreshlocal17:17in-windowDBnegativeattemptrecorded,target5091,no forecast. Mainworkflowrelease/fullchainstillpending. Evidence:`ml/P9_NONREADY_OPERATIONAL_FIX_2026-11-04.md`.
