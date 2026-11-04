# Exited children are not live inference workers

Status:complete. Nine lifecycle tests(three new real-process/error cases) passed in hosted Demand Engine41819264406,total312Pythonchecks. Original v1worker remained healthy; replacement drift worker completed its own post-launch backup-verified cycle.

Observed while starting the independent drift sidecar: os.kill(pid,0) succeeds for an unreaped zombie even though its network cycle failed. A completed manual cycle must not make a dead detached process look healthy. Its proxy environment omission was corrected separately; inherit the environment needed by this cloud host and verify a successful cycle after launch.

Improve the shared bounded v1launcher PID probe to reject exited/zombie states while retaining recent-cycle/model/backup/deadline checks. Fail closed when process inspection is unavailable; never kill or silently replace an unrelated live PID. Verify real exited/live child processes and inspection failure. No model, prediction, scoring, gate or deadline change.
