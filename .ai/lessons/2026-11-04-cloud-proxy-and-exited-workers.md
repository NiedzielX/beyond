# Cloud process launch and actual health

A filtered environment omitted required cloud proxy variables. The manual drift cycle had succeeded, but the first detached worker then failed DNS and exited. Relaunching with the inherited working cloud environment produced a new post-launch successful cycle and verified private backup. Do not print proxy credentials or environment bindings.

A zombie child still answers `os.kill(pid,0)`. A PID alone is not proof a worker runs; inspect process state and require a successful cycle after that exact launch, correct model/artifact, private read-back, freshness and a valid deadline. The shared launcher now rejects zombie/exited states and fails closed when process inspection is unavailable. Real live/unreaped-child tests cover this distinction. Never kill an unrelated PID or suppress a failed launch in the log.

Evidence: initial driftPID154243failed; replacementPID154636completed11:09:54UTCcycle after11:09:54launch. Historical PID values are snapshots; always read current runtime metadata. Model rule/freeze and prospective semantics were unchanged.
