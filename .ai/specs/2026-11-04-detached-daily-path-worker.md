# Detached bounded daily-path worker

The foreground tool-session worker stopped when the prior session ended. Provide an explicit reusable launcher that starts only one detached inference subprocess, logs privately to the runtime directory and retains the existing24-hour bound. This is not an autonomous coding service and cannot survive destruction of the cloud host.

Acceptance: validate stop time/interval, refuse duplicate launch while a stored PID is alive, serialize launchers, avoid racing an active cycle, record launch metadata, and distinguish a live PID from a recent successful cycle with verified backup. Never kill an unrelated/stored PID to make room. Do not change model artifacts, missed-window rules or scoring semantics. Tests cover duplicate/process state, stale health, invalid bounds and launch locking. Current genuine issue windows must be preserved; no backfill.
