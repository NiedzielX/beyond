# Current persisted C1 error decomposition

Actual read: **2026-11-05 10:57 UTC**. Package `c1-shadow-v8-frozen-2026-10-16-n9`. All17forecast events are scored; no pending attendance label in this existing cohort. Read-only diagnostic of already exposed outcomes, no model replay/fit or parameter selection. All six aggregate latest/window MAEs reconcile to the current persisted status; canonical event identities, source provenance, confirmation chronology, selected outputs and stored absolute errors are checked.

| Persisted expert | Latest event MAE | Event-balanced window MAE | Signed bias | P90 AE |
|---|---:|---:|---:|---:|
| Structural prior |3131.16|3131.16|−1487.37|7364.00|
| Raw C1 live |6241.96|6195.74|−5039.81|13917.83|
| Governed C1 policy |3248.81|3913.56|−1598.49|7364.00|

Policy selects PRIOR15times and LIVE2times. Versus prior it improves1event, worsens1and ties15; aggregate DeltaMAE+117.65. Worst policy error17009.69. The same four earlier high-error events16/5/11/23 still contribute68.50%of total policy absolute error, down from83.45%on the older11-event scope solely because six other outcomes joined the cohort.

The earlier11retain policyMAE4121.45 and prior4314.72. The subsequently scored6have policy1648.96, prior961.29andraw4617.58. These are descriptive cohorts, with different fixture composition and no randomized treatment. A lower overall MAE after labeling six more events proves neither a model improvement nor an effect of the newly imported history: these are old immutable predictions.

Even an unattainable outcome-aware choice of the lower-error prior/raw output for every event would have **MAE2949.38**on all17. The maximum such diagnostic selection gain from current policy is299.42. It cannot reach the1200goal on this cohort by switching between the existing two experts alone. Do not fit a gate/threshold to this oracle or discard the four difficult events. Raw C1's pronounced underprediction and weak independent training support remain relevant hypotheses for the already frozen Ridge20/direct-person-median20 experiments; their causal benefit still needs genuine future evidence.

## Next actions

Protect actual current cutoffs and collect both frozen challengers on the same new observations, beginning with today's eligible final24window if the data qualify. Keep actual history knowledge timestamps in future inputs and continue the private immutable source archive. The prepared26-event/80-row dataset contains additional exposed training information only; no26-event model has been fitted. Do not add another learner or tune frozen parameters from this diagnostic.

Six contract tests cover label/error corruption, chronology, expert selection, canonical fixture duplication including registered aliases, complete denominators, all latest/window aggregates and pending-label coverage. Raw source receipts and detailed ranked/grouped diagnostics stay private under `/workspace/ops-runtime/2026-11-05-c1-current-error-decomposition/`. The upstream historical publication-time assumptions were not independently reverified here. `production_change=false`, `live_adjustment=0`.
