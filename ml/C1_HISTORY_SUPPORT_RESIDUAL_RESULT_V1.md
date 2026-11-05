# C1 history-support residual ablation — frozen pair

2026-11-05. Review:[PR220](https://github.com/NiedzielX/beyond/pull/220). Protocol:`C1_HISTORY_SUPPORT_RESIDUAL_PRECOMMIT_V1.md`. User authorized continued MAE work; source/precommit commit`5d77445183f6ac1815bdad4a4e47d5f477bab33c`was published and independently ref-verified before the two declared fits. Package:`c1-history-support-residual-v1-frozen-2026-11-05-n26`.

## Actual fixed fit

Frozen at**16:34:30.913599UTC**, exactly one6featurecontrol fit and one9featurehistory-augmented fit. Same26exposed fixtures/80rows/12clubs, same equal-event weights and QuantileRegressorq0.5/alpha0.1/HiGHS/intercept, direct-person residual target and output clipping. All old models remain untouched. No training/old-holdout MAE, search, cap adjustment or outcome-based selection.

- Control SHA:`213bbe6f88ba98529606c9a5ddc640876649c3c4c89cddcd005ec9a9ff86e437`.
- History SHA:`c11f0d9943bb33588140d8f0371db765bf2c222bbb204d59ad64260f89018e5f`.
- Source envelopeSHA:`ad1fc737f607297f20ea171e0ea99d4d3398fccccb959a6980339bceb6d67afa`.

Three new explicit history features are derived only from known completed current-season home fixtures:log count, latest-three-home mean relative to shared prior, and age.34of80rows/13fixtures/9clubs have known home history; other rows retain explicit missing level/age.16records first obtainedNov4are excluded from every old training observation. Original historical source snapshots remain independently unverified; these are exposed training reconstructions, not new validation.

Descriptive mechanism audit:`artifacts/c1_history_residual_v1/mechanism_audit.json`. The augmented head has nonzero terms for the verified-home recent-level gap and actual6hchange. Its count/age terms are zero and retained. The24hvalue coefficient is zero; its missingness indicator is active. Missingness is not learned24hvalue dynamics. Coefficient activity is not accuracy or causal importance.

## Serialization compatibility, without refit

The build CLI serialized its dataclass symbol as`__main__.ResidualRuntime`. Initial direct execution of the separate sidecar failed closed before any forecast/runtime write. The core model CLI's own check succeeded but did not catch that cross-entry-point packaging issue.

Preserved both estimator files, precommit and all frozen source bytes. A separate operational entry point`ml/launch_c1_history_residual_v1.py`imports the exact canonical inference-only class into the entry namespace. **Use this entry point**, rather than directly invoking the internal sidecar. Hosted inline loader checks likewise bind that class explicitly. No learner, model output, source contract or parameter was changed.

Across80target-free feature probes, original-build-class and canonical-class loading produce **bitwise identical predictions for both heads**; artifact hashes unchanged,0newfits. Proof:`artifacts/c1_history_residual_v1/serialization_parity.json`. Numerical equivalence is not attendance-MAE evidence. New cross-process loading regression test covers the actual frozen files.

## Operational evidence and recovery

Actual compatibility-entry cycle**16:37:52UTC**:frozen pair and all benchmarks load, genuine current source reads succeed, scorer and private verified backup complete.0newforecasts/0scores/**MAEnull**before first legal final24window. This is no-due operational health, not positive forecast evidence.

Full initial model/training/source/runtime recovery was independently uploaded/read/decompressed/restored, model identities and26/80training lineage validated without refit. Initial full recovery:28files/146043compressed bytes,SHA`0b306bed573faeae5a27a82a9eba10d79d0136bb80f17432480fb5fe882cc378`, private`c1-history-residual-v1/`namespace. Restored class binding, both models and training-source lineage validate without fit. No raw inputs/training rows are committed.

Prospective sidecar reads immutable support26candidate inputs, preserves older benchmark issue time and records its own actual post-inference issue. Each prefix requires an actual verified source archive at/before observation, at most60minutes old. Complete source blobs precede immutable forecasts. New/benchmark decisions are replayed before later genuine outcomes can score. All26training fixtures/canonical aliases are excluded; missing archive/label remains missing. Primary raw augmented-versus-control and separate all-six-benchmark governed-product gates retain30newfixtures/8clubs.

Commands(after artifact publication):

```bash
python -m ml.launch_c1_history_residual_v1 cycle \
  --runtime /workspace/ops-runtime/2026-11-05-c1-history-residual-collector \
  --support-runtime /workspace/ops-runtime/2026-11-05-c1-support26-collector \
  --archive /workspace/ops-runtime/2026-11-04-known-at-source-archive
```

Bounded watcher activation follows artifact/launcher publication and must record actualPID/deadline/post-launch cycle. Existing source archive and support26workers stopNov6 20:30UTC; this is host-dependent private research, not managed production. No MAE1200or model promotion claim. `production_change=false`, `live_adjustment=0`.

### Actual bounded activation

Afterartifact/launcherc3b37fdbpublication,watcherPID354725started16:45:09UTCwith300sintervalanddeadlineNov6 20:30UTC. ActualSslprocessand16:45:13post-launchcycleverified,0predictions/0scores/nullMAE. Newprivate6filebackup3990bytes/SHA c6279daa611e7ba3a890db44890549336a8671ae9475015e8941d7b0ae07a930read-back/decompressionverified.348registeredrootchecks pass and hosted source/artifactDemandEnginechecks succeed. First positive forecast is still future/source-dependent; no E2Eprediction or accuracy claim is inferred from this no-due cycle.

## First genuine prospective forecast —17:08UTC

Motor5091/snapshot35663 observed17:03:01.536UTC; genuine prior76 generated17:01:57UTC. Support26benchmark issued17:07:25.558UTC; this pair issued17:08:03.698UTC, its own actual issue. Source archive completed17:01:32UTC before the observation, all bytes preserved. Actual positive cycle verifies full frozen replay/private recovery:one captured event,0scores/nullMAE. Ten-file backup34902bytes/SHA342ecff8212dd69ea63da997e530c3923caa2acf34160478c93fd13eca790a7cread/decompressionverified. Later17:10watcher cycle correctly adds0duplicates.

Raw control11646.60/history11340.79; both unchanged policies select shared prior12920.27. These are forecasts, not errors or proven improvement. Motor's current-season verified-home source count is0; gap/age stay missing, never zero attendance. This proves genuine pipeline capture but does not yet test benefit on a prefix with observed home history. First30new-fixture/8-club review remains unchanged. OriginalmainC1separately persisted its same-source prediction inDB via successful run42071837843; the research pair remains private, not served or production-active. See`STRUCTURAL_PRIOR_WINDOW_GUARDIAN_RESULT_2026-11-05.md`.
