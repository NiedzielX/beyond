# Beyond multi-club execution status — 2026-10-10

## Working reporting rule

After each material execution step, summarize:

1. **Where we are now**
2. **What comes next**

This is the default project reporting format.

## 1. Club acquisition scope — FROZEN FOR NOW

The current collection footprint is sufficient for the POC. Do not spend the next iteration adding more clubs unless a data-quality gap requires it.

Current database coverage includes future events across 11 clubs, with the strongest active collection on Lech plus the newer Roboticket-based clubs.

The priority has shifted from adding sources to converting trajectories into comparable event-level evidence.

## 2. Multi-Club Feature Store — ACTIVE

Backend contracts:

- `get_multiclub_feature_store_v1()` — first strict event x canonical-horizon feature store;
- `get_multiclub_feature_store_v2()` — adds historical raw-total velocity fallback, observation-window metadata and explicit feature quality;
- `multiclub_feature_store_v3` — training view adding optional event-level public seat-map normalization;
- `get_multiclub_readiness_v1()` — per-club readiness monitor.

Canonical horizons remain:

- T-30
- T-14
- T-7
- T-3
- T-24h

Selection protocol:

- at most one snapshot per event/horizon;
- snapshot must be available before the target checkpoint;
- choose the closest eligible pre-checkpoint snapshot;
- no post-checkpoint fallback.

## 3. Feature semantics

Inventory is always labelled:

`demand_proxy_not_confirmed_sales`

### Raw-total features

Available even for older historical snapshots without sector-level history:

- available total;
- first observed available total;
- available index;
- observation window length;
- snapshot count visible at checkpoint;
- net removed since first;
- previous-step velocity;
- raw 6h velocity;
- raw 24h velocity;
- raw 6h-vs-24h acceleration;
- percentage-normalized versions.

### Sector-matched features

Available where sector inventory was captured:

- matched net removed 6h/24h;
- matched velocity 6h/24h;
- acceleration;
- sector coverage entry/exit;
- coverage inventory effect;
- release activity.

Feature quality is explicit:

- `sector_matched_plus_raw`
- `raw_total_only`
- `single_snapshot_only`

## 4. Normalization

Two normalization families are retained deliberately.

### First-observed normalization

Works for all tracked events and preserves trajectory relative to when Beyond started observing the public inventory.

Important caveat: it depends on observation start time, so `observation_window_hours` and `first_snapshot_hours_to_kickoff` must stay in the dataset.

### Public seat-map normalization

`ticket_event_inventory_reference` stores verified event-level references of type:

`public_seat_map_size`

This is the number of seats exposed by the public ticketing seat map for that event. It is **not** asserted to equal certified stadium capacity or confirmed inventory for sale.

The v3 training view exposes:

- available % of public seat map;
- raw velocity % of public seat map per hour;
- matched velocity % of public seat map per hour;
- normalized acceleration.

Only verified probe values are stored; missing references remain null rather than being guessed.

## 5. Outcome pipeline — ACTIVE

Backend queue:

`get_missing_outcomes_v1()`

Returns events that:

- are at least three hours past kickoff;
- have no verified `ticket_event_outcomes` row.

A recurring `Beyond Outcome Sweep` task runs daily in the morning. It must:

- prefer official club/league/competition attendance sources;
- use trustworthy secondary sources only when necessary;
- never infer attendance from inventory or stadium size;
- write source name, source URL, attendance definition and confirmation timestamp;
- avoid overwriting an existing verified outcome unless a real conflict is established.

## 6. Current readiness

At status time:

- verified outcome events: 4, all Lech;
- Lech historical snapshot volume: ~2,000 rows;
- Lech canonical rows with outcomes: 12;
- newly added clubs are collecting prospective trajectories but have not yet produced independent verified outcomes;
- the next several matches will materially increase the independent-event count.

This means the bottleneck is now **independent completed matches**, not snapshot volume.

## 7. Modelling gate

Do not train or promote a learned cross-club live correction yet.

A snapshot is not an independent ML sample. Splits must be grouped by `ticket_event_id`.

Planned proof:

`historical / club baseline error -> baseline + live features error -> live signal uplift`

The existing live residual challenger promotion gate remains at minimum 20 independent completed matches.

Before that threshold, use the multi-club dataset for:

- data-quality analysis;
- feature stability;
- trajectory visualisation;
- descriptive signal studies;
- prospective benchmark accumulation.

## 8. Where we are now

1. Club acquisition: sufficient and frozen.
2. Multi-club collection: active.
3. Strict multi-club feature store: active, versioned through v3.
4. Outcome acquisition: automated.
5. Exact Lech v1.7 T-7 prospective validation: running separately.
6. Learned multi-club live correction: intentionally not trained yet.

## 9. What comes next

1. Let the current multi-club events complete and populate verified outcomes.
2. Monitor `get_multiclub_readiness_v1()` rather than raw snapshot counts.
3. Run the first cross-club Live Signal Study once multiple clubs have independent outcomes.
4. Test whether inventory index, 6h/24h velocity, acceleration and release/coverage flags add predictive information beyond club/event baseline.
5. Only after stable uplift appears, train a grouped live residual challenger.
6. Keep T-30 forensic reconstruction as a parallel lower-priority task; do not let it block prospective multi-club evidence collection.
