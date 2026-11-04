# C1 live objective — target-free contract audit

2026-11-04. First bounded R&D step under the accepted `C1_MAE_LITERATURE_EXECUTION_SUPPLEMENT_V1.md`. No estimator fitted, inference run, training error computed, target column parsed or frozen artifact changed.

The private20event/74rowframe matches the training-expansion freeze SHA`be9aab4721e69661b8f14d3e1e8938abde569dabd6f7878e0986868fc0756549`. Read only event IDs and capacities. Equal-event row weighting reproduces total mass3.7for each event regardless of prefix count. Training capacities range15,004–43,708.

For unbounded/unclipped training predictions, current Ridge data loss is proportional to:

`sum(row_event_weight * seat_error² / capacity²)`.

Consequently the same person error has **8.4861times** the squared-occupancy loss at the smallest versus largest training capacity, after equalizing total event weight. Absolute-occupancy loss would have factor2.9131; absolute-person loss factor1. These are mathematical loss sensitivities, **not measured prediction errors or evidence that changing the objective improves MAE**. Clipping is an additional inference operation and remains frozen.

Squared loss elicits a conditional mean; absolute loss a conditional median. Because capacity is known inX, capacity rescaling alone does not change the unrestricted conditional functional; finite model class/regularization trades remain an empirical question. Existing structural weighting rejection is preserved. Do not infer an8.49xaccuracy gap or causal explanation from this calculation.

Novelty check: C1v1/v2alreadytested robust/L1tree learners and club-aware variants; structuralT1alreadyusesL1. No executed linearQuantileRegressor was found in the checkedC1source, although it appears as a proposal in older roadmapv3. A new median-linear experiment must first specify its exact loss, target scale, penalty, weights and comparisons. Replacing Ridge with L1-regularizedQuantileRegressor changes both loss and penalty; it must not be described as a loss-only ablation. No fit is authorized under an old frozen version, no exposed event becomes a new test, and no parameter grid is justified by this audit.

Next: write the exact new objective experiment's precommit and verify its difference against archived variants before fitting; keep source-history recovery and existing prospective collection running independently. A measured future improvement remains the decision criterion.

Reproduce:

```bash
python -m ml.c1_objective_geometry_audit_v1 --training-csv /private/frozen-training.csv --output /tmp/new-objective-audit.json
python -m unittest ml.test_c1_objective_geometry_audit_v1
```

Six tests cover capacity/error geometry, equal-event weighting with unequal prefixes, rescaling, invalid/conflicting capacities and target independence/no mutation. Aggregate artifact:`artifacts/c1_objective_geometry_audit_v1.json`. All prior model, collection and precommit hashes remain unchanged. `production_change=false`, `live_adjustment=0`.
