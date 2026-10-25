# P7 Long168 — Prospective Validation Precommit v1

Date frozen: **2026-10-25**

Status: **PRECOMMITTED BEFORE PROSPECTIVE OUTCOME ACCESS**

Production: **UNCHANGED** (`live_adjustment = 0`)

## Research question

> Does the already-selected P7 Long168 mechanism `gbr-l1-depth2-n50-lr003`, trained once on the exact exposed P7 v1 research set, improve genuinely future 72–168h attendance forecasts versus the frozen Structural Prior T-7 anchor when predictions are persisted before attendance is known?

This is a prospective validation lane, not a new candidate tournament.

## Why this lane exists

P7 v1 produced a 14.44% point MAE improvement in strict historical forward folds, but its event-block uncertainty interval still crossed zero.

The v1 tournament is now exposed evidence and must not be retuned.

This follow-up therefore freezes the selected mechanism and evaluates only genuinely future predictions.

## Frozen training set

Source research run:

`40197742930`

Source execution artifact:

`p7-long168-execution-v1-40197742930`

Artifact ZIP SHA256:

`58a368c6281640060aed6eb7c245e4a8ce6b79c23077d3147a15834e7ccccfc2`

Frozen training event IDs:

`[1, 3, 4, 5, 10, 11, 15, 16, 18, 19]`

Frozen Long168 training rows:

`139`

Required original identity manifest SHA256:

`185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`

The prospective builder must reconstruct the historical training Long168 payload from the current canonical source, filter it to exactly these event IDs, re-run the original freeze logic, and fail closed unless the manifest SHA reproduces exactly.

No later completed event may enter training v1.

## Frozen historical source code lineage

Original P7 harness Git blob SHA:

`1eb175fc40dc5a010b22f149a8a593f53376ca6d`

Original P7 tournament Git blob SHA:

`3e1403471c7921a507768b792605a4d18a60ee7b`

The selected model definition must remain semantically identical to the original tournament.

## Frozen selected mechanism

Candidate ID:

`gbr-l1-depth2-n50-lr003`

Estimator:

`GradientBoostingRegressor`

Fixed parameters:

- `loss="absolute_error"`
- `n_estimators=50`
- `learning_rate=0.03`
- `max_depth=2`
- `min_samples_leaf=4`
- `random_state=42`

Preprocessing:

`SimpleImputer(strategy="median", keep_empty_features=True)`

Training target:

`actual_attendance - Structural Prior T-7 anchor_p50`

Training weighting:

`1 / number_of_rows_for_training_event`, normalized exactly as in P7 v1 so each event contributes equal total weight.

Hyperparameter search:

**NONE**.

Candidate search:

**NONE**.

## Frozen feature allowlist

Exactly the P7 v1 `FEATURE_ALLOWLIST`:

1. `hours_to_kickoff`
2. `available_index`
3. `available_total`
4. `available_share_of_capacity`
5. `first_available_total`
6. `net_removed_since_first`
7. `net_removed_since_previous`
8. `velocity_since_previous`
9. `velocity_7d`
10. `velocity_72h`
11. `velocity_7d_pct_of_capacity_per_hour`
12. `velocity_72h_pct_of_capacity_per_hour`
13. `acceleration_72h_vs_7d`
14. `observation_window_hours`
15. `snapshot_age_minutes`
16. `max_visible_gap_hours`
17. `raw_snapshot_count`
18. `clean_snapshot_count`
19. `data_gap_detected`
20. `release_activity_flag`
21. `unexplained_inventory_increase_flag`

No P9/P11/P12/context feature may enter P7 prospective v1.

## Structural Prior comparator

Comparator remains the frozen Structural Prior T-7 anchor.

Required frozen artifact SHA256:

`97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`

Required historical runtime SHA256:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

For each prospective event the T-7 anchor must be reconstructed from only information chronologically available by the T-7 cutoff. The target event attendance must not be present or required.

## Prospective eligibility

A prediction may be persisted only when all are true:

1. event competition canonicalizes to `Ekstraklasa`;
2. kickoff is still in the future at prediction time;
3. no genuine attendance outcome exists at prediction time;
4. a verified stadium capacity exists;
5. home/away club aliases and sporting fixture metadata required by the frozen Structural Prior are resolvable;
6. a PIT-validated ticketing snapshot exists;
7. selected row is the latest snapshot in its event × 6h bucket;
8. `72 < hours_to_kickoff <= 168`;
9. snapshot/as-of precedes kickoff;
10. prediction is persisted before kickoff and before any attendance confirmation.

## Prospective sampling

Cadence:

**every 6 hours**.

At each run, persist only previously unseen eligible event/snapshot identities.

The independent evaluation unit remains:

`ticket_event`

Repeated snapshots from one event do not increase independent event N.

## Prediction rule

For each eligible row:

`challenger_p50 = clip(anchor_p50 + fixed_GBR_residual, 0, stadium_capacity)`

Persist both:

- `anchor_p50`
- `challenger_p50`

before target attendance is known.

## Immutable persistence

Prospective prediction records are append-only.

Required lineage per prediction:

- ticket event ID;
- snapshot ID;
- `as_of_at`;
- `predicted_at`;
- kickoff / target timestamp;
- hours to kickoff / 6h bucket;
- stadium capacity;
- anchor P50;
- challenger P50;
- selected candidate ID;
- training freeze manifest SHA;
- original P7 scorecard SHA;
- fixed model fingerprint SHA;
- prospective anchor package SHA;
- source payload / prediction identity SHA where applicable.

No actual attendance field belongs in the prediction payload/table.

## Outcome attachment

Attendance may be joined only after a genuine outcome exists and `confirmed_at > predicted_at`.

Scoring must never recompute the historical prediction.

Corrections to a source outcome do not silently mutate an already scored evidence row; they require explicit audit/reconciliation.

## Primary metric

`event_balanced_mae`

Definition:

1. compute mean absolute error across all persisted eligible predictions for each completed event;
2. average those event MAEs across independent events.

## Secondary metrics

- event-balanced signed bias;
- event median AE;
- event P90 AE;
- worst event degradation vs anchor;
- event improvement rate;
- horizon-band MAE: 72–96, 96–120, 120–144, 144–168h;
- paired event-block uncertainty for challenger-minus-anchor MAE once enough completed events exist to make the interval informative.

## Interpretation

Do not invent a new N gate from this precommit.

Each completed event is genuine prospective evidence and must be reported as such.

Governance vocabulary remains:

- `NO_RESEARCH_GAIN`
- `POINT_GAIN_UNCERTAINTY_LIMITED`
- `ROBUST_RESEARCH_ADVANCE`

`ROBUST_RESEARCH_ADVANCE` additionally requires:

- approved business-derived minimum meaningful absolute ΔMAE;
- required event/fold stability where applicable;
- uncertainty/precision criterion passing;
- PIT/lineage/reproducibility gates passing.

The business threshold is intentionally not derived from P7 results.

## Prohibited changes after first prospective prediction

Without a new version/precommit, do not change:

- training event set;
- selected candidate;
- model hyperparameters;
- imputation;
- feature allowlist;
- event weighting;
- T-7 comparator;
- 72–168h window;
- 6h sampling rule;
- clipping rule;
- scoring aggregation.

Do not add P11 odds/price/weather/attention or any P9 feature to this lane.

## Production boundary

- `production_change=false`
- `production_activation_allowed=false`
- `live_adjustment=0`

Prospective success does not automatically activate production.
