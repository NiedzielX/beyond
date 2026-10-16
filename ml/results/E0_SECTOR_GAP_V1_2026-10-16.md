# E0 Sector Gap v1 — Release/Coverage-Aware Diagnostic

Date: **2026-10-16**  
Status: **implemented / live service-role contract / Step 2 complete**

## Contract

Function:

`public.get_sector_gap_v1_asof(ticket_event_id, as_of_at)`

Feature version:

`sector-gap-v1`

Depends on:

`sector-trajectory-v1`

No sector status is assigned by this contract. It only decides whether the continuous gap is sufficiently reliable to be used by the next status layer.

## Coverage policy

Version:

`COVERAGE_STABILITY_V1_PRESENCE80_6H_24H`

For every currently visible sector the contract measures:

- number of event snapshots in the latest 6h;
- number of those snapshots where the sector was visible;
- 6h sector-presence ratio;
- same metrics over 24h.

Coverage is provisionally stable when presence is at least **80%** over both windows.

Observed across the selected current active-event sample before freezing the policy:

- 6h presence median: **100%**;
- 24h presence median: **100%**;
- only about 4% of current sector rows had presence below 80% in either diagnostic window.

This confirms that most currently visible sectors are stable even though the total number of visible sectors can fluctuate between snapshots.

## Availability increase / release heuristic

Version:

`PROVISIONAL_RELEASE_HEURISTIC_V1_MIN5_AND_10PCT`

A sector is flagged as potential material release activity only when the largest positive availability jump in the latest 24h is both:

- at least **5 seats**; and
- at least **10% of the sector reference availability**.

The rule intentionally ignores small positive moves as release evidence because public inventory commonly rises due to holds expiring and other public-inventory mechanics.

Observed positive-jump-ratio distribution across 339 READY current sector rows before freezing this heuristic:

- p50: **0.9%**;
- p75: **3.2%**;
- p90: **12.5%**;
- p95: **20.0%**;
- maximum: **81.8%**.

This makes 10% + 5 seats a deliberately material provisional threshold rather than treating every positive move as a release.

## Current release-aware live sample

Across 9 selected active events:

- current sector rows: **341**;
- usable for status: **311**;
- potential material release: **16**;
- coverage unstable: **15**;
- HIGH gap reliability: **104**;
- MEDIUM: **207**;
- LOW: **28**;
- INSUFFICIENT: **2**.

The quality gate therefore preserves the majority of current sector evidence while removing the clearest release/coverage contamination.

## Gap distribution after quality gate

For the 311 rows currently usable for sector status:

- p10: **-0.355263**;
- p25: **-0.151039**;
- p50: **+0.003529**;
- p75: **+0.069436**;
- p90: **+0.216777**.

The median being close to zero is expected from the relative-event baseline and supports using the continuous normalized gap as the core sector-position signal.

Positive gap means more public inventory remains than expected relative to the event's current visible-sector progress — candidate underperformance.

Negative gap means less inventory remains than expected — candidate outperformance.

## Reliability semantics

`gap_reliability`:

- `INSUFFICIENT` — underlying trajectory contract is not READY;
- `LOW` — coverage unstable or material release heuristic is active;
- `MEDIUM` — smaller availability increases / recently appearing sector but no material release;
- `HIGH` — stable coverage and no current increase anomaly.

`gap_usable_for_status = true` only when:

- trajectory readiness is READY;
- 6h and 24h coverage are stable;
- material release heuristic is false.

## Decision

**Step 2 is complete.**

The next layer may now freeze a small versioned status policy using:

- normalized sector gap;
- time to kickoff;
- current/recent velocity and acceleration as trend context;
- the release/coverage quality gate above.

After status, implement bounded no-action public-availability projection.
