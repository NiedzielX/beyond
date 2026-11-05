# Bounded guardian for existing P9 heartbeat

ObservedNov5:scheduled main executions are sparse; actual Korona603T48heartbeat42017429991SUCCESS→child42017444883FAILURE. Preserve that failure and the separate legitimate local zero-prediction attempt. PR212 remains unmerged; this guardian is not a deployment or a substitute for the full chain's successful-child/expected-DB acceptance gate.

Add a bounded operational guardian that reads the existing fresh P9preflight and dispatches only the existing main heartbeat during exact genuine T48/T24…+90minute windows with no v1attempt/prediction. It never builds/records forecasts or outcomes, changes model/support rules, backfills a window, mergesmain or writes production. Include missing-snapshot windows as operational dispatch coverage; an accepted dispatch with no eligible export is not a DBattempt. Preserve that distinction.

Reject stale/wrong-version/governance/coordinate/duplicate contracts. Check active mainP9runs before dispatching, global10minutecooldown, at most3dispatches for one legal event/cutoff, fresh actual wall clock after network reads and immediately before dispatch. Source/state/runtime lock, lifetime process lock, explicit at-most24hourdeadline, actual post-launch cycle and durable dispatch audit. Keep failure/status-only receipts free of credentials. Tests cover exact boundary, expiry, captured/missed history, invalid flags/source times, duplicates, active runs, cooldown, bounded retry and successful dispatch versus unproven DBchain.

Publish/test before launching the worker. Verify a no-due cycle now and actual later dispatches/child/DB separately. `production_change=false`, `live_adjustment=0`.
