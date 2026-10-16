# E0 Sector Trajectory v1 — Live Verification

Date: **2026-10-16**  
Status: **implemented / live service-role contract / Step 1 complete**

## Contract

Function:

`public.get_sector_trajectory_v1_asof(ticket_event_id, as_of_at)`

Feature version:

`sector-trajectory-v1`

Provisional baseline:

`PROVISIONAL_RELATIVE_EVENT_BASELINE_V1_CURRENT_VISIBLE_SET`

The contract intentionally resolves event ownership through:

`sector_inventory.snapshot_id -> snapshots.id -> snapshots.ticket_event_id`

`sector_inventory.event_id` is ignored because it is nullable and is not the canonical relationship.

## Semantics

- public availability is a demand proxy, not confirmed paid sales;
- positive velocity means observed public availability decreased;
- availability increases are preserved as explicit signals and are not interpreted as negative sales;
- the relative-event sector gap compares the currently visible sector with the current visible-sector set;
- the baseline is provisional and is not a learned sector-specific demand curve.

## Implemented features

Per current visible sector the function exposes:

- current / previous / first / maximum / minimum observed availability;
- versioned reference availability;
- observation count and source timestamps;
- 6h / 24h / 72h / 7d historical availability anchors;
- effective hours behind each anchor;
- 6h / 24h / 72h / 7d availability velocity;
- 6h-vs-24h acceleration;
- public absorption proxy and public sell-through proxy;
- current and previous visible-sector counts;
- event current/reference public availability;
- provisional event remaining ratio;
- expected sector availability under proportional event progress;
- continuous sector gap in seats and normalized ratio;
- current and 24h availability-increase signals;
- maximum positive 24h availability jump;
- sector appeared-within-24h signal;
- sector-level coverage gap;
- event-level sector coverage-change flag;
- data-gap flag;
- deterministic trajectory readiness;
- PIT validation flag.

## Live reconciliation — Lech event 5

At the implementation checkpoint:

- returned sector rows: **28**;
- source snapshot sector count: **28**;
- sum of current sector availability: **233**;
- source snapshot `available_total`: **233**;
- READY rows: **27**;
- COVERAGE_UNSTABLE rows: **1**;
- DATA_GAP rows: **0**;
- INSUFFICIENT_HISTORY rows: **0**.

Therefore both sector count and availability reconcile exactly with the source snapshot.

Observed continuous gap range for current visible sectors:

- minimum normalized gap: **-0.155520**;
- maximum normalized gap: **+0.558737**.

## Availability-increase finding

On the same current Lech snapshot:

- **21 / 28** visible sectors had at least one positive availability change during the prior 24h.

This confirms that any positive availability movement cannot be treated as a direct reversal of paid sales. It may reflect released inventory, expired holds, coverage changes or other public-inventory mechanics.

Therefore E0 must use the magnitude/pattern of increases as a quality/release signal rather than simply subtracting them from demand.

## Cross-event live verification

Selected current events:

| Event ID | Current visible sectors | READY | Not ready | Average absolute gap | Gap min | Gap max |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 28 | 27 | 1 | 0.1747 | -0.155520 | +0.558737 |
| 10 | 38 | 38 | 0 | 0.3024 | -0.493572 | +0.437620 |
| 15 | 19 | 19 | 0 | 0.2131 | -0.268427 | +0.450371 |
| 19 | 13 | 13 | 0 | 0.2377 | -0.556069 | +0.272302 |
| 20 | 17 | 17 | 0 | 0.0949 | -0.364555 | +0.080021 |

This proves the continuous relative-event gap has enough variation to support Step 2 diagnostics. Thresholds are deliberately not frozen yet.

## Historical PIT verification

The same function was evaluated for Lech event 5 with `as_of = now() - 12 hours`.

Result:

- returned rows: **46**;
- selected source snapshot timestamp was earlier than the requested as-of time;
- returned sector count reconciled exactly to the historical source snapshot;
- returned sector availability sum reconciled exactly to historical `available_total`;
- all rows returned `point_in_time_validated = true`.

No future snapshot was used.

## Security

Function characteristics:

- `SECURITY INVOKER`;
- direct `EXECUTE` only for `service_role` and database owner;
- no `anon` or `authenticated` execution grant;
- no new security-advisor warning introduced.

The public dashboard surface will be added separately after E0 projection semantics are ready.

## Performance

Current on-demand execution for the largest tested Lech event:

- approximately **924 ms** for one event at the current checkpoint;
- 28 current rows returned;
- historical sector history is scanned to calculate all four velocity windows and reference metrics.

This is acceptable for R&D / service-role evaluation. Before high-frequency dashboard polling across many events, either optimize the SQL or materialize current E0 features.

## Decision

**Step 1 is complete.**

Do not add status labels yet.

Next:

1. inspect normalized gap and positive-availability-jump distributions across active events;
2. separate ordinary inventory noise/hold expiry from material release/coverage changes;
3. derive release-aware continuous E0 features;
4. only then freeze a small versioned status policy;
5. proceed to bounded no-action sector projection.
