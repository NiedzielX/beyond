# Beyond Ticketing — Production Activation Contract v1

Status: **control-plane active / execution intentionally disabled**  
Production P50 impact: **none**

## Purpose

Production Activation Contract v1 defines the operational safety layer that sits after:

`Research → Evidence → Promotion Gate → Frozen Package → Human Review`

An `approved_for_promotion` package does not become production automatically. It first creates a dedicated activation contract.

## v1 guardrails

The first production contract is intentionally conservative:

- activation mode: `bounded_overlay`;
- allowed horizon: **T-24h only**;
- maximum correction: **±10%** versus champion P50;
- stale-input threshold: **45 minutes**;
- missing / invalid / stale input: **fail closed to champion**;
- champion forecast must continue to be persisted in parallel;
- audit payload is mandatory;
- kill switch is mandatory;
- rollback target: **champion immediate**;
- post-activation monitoring starts after at least **5 outcomes**;
- rolling monitoring window: **5 events**;
- alert if challenger rolling MAE exceeds **105% of champion MAE**;
- alert after **3 consecutive outcomes** where challenger is worse than champion.

## Contract lifecycle

A contract is created only from a promotion package with:

`review_status = approved_for_promotion`

Lifecycle:

1. `draft`
2. `ready_for_activation`
3. `activation_approved`
4. future operational states: `paused`, `rolled_back`, `retired`

`review_model_activation_contract_v1(...)` verifies the safety rules before moving a draft to `ready_for_activation`.

`approve_model_activation_contract_v1(...)` records operational approval but **does not activate a forecast writer**.

## Execution is impossible in v1

The database enforces:

- `execution_enabled = false`
- `writer_binding_status = not_bound` for the current v1 path

This is deliberate. Contract v1 is a control-plane contract and audit layer, not a hidden production switch.

The existing forecast writer remains unchanged and the Demand Engine shadow writer still accepts shadow forecasts only.

## Health monitoring

`model_activation_health_samples_v1` stores paired post-activation evidence:

- champion P50;
- challenger P50;
- actual attendance;
- absolute errors;
- whether challenger was worse.

`evaluate_model_activation_health_v1(contract_id)` evaluates:

- rolling challenger/champion MAE ratio;
- consecutive worse outcomes;
- kill-switch alert status.

A health alert is written to the activation audit log.

## Verification

Transactional dry-runs verified that:

- an approved promotion package creates one activation contract;
- technical review moves the contract to `ready_for_activation`;
- operational approval moves it to `activation_approved`;
- `execution_enabled` remains false;
- `writer_binding_status` remains `not_bound`;
- a healthy sample does not raise a kill-switch alert;
- three consecutive worse outcomes do raise a kill-switch alert;
- all dry-run data was rolled back.

Current production state after rollback:

- real activation contracts: **0**;
- real activation health samples: **0**.

## Dashboard

Model Lab exposes **Production Activation Contract v1** with:

- approved package count;
- contract count and states;
- execution status;
- default guardrails;
- future contract queue;
- explicit fail-closed / kill-switch semantics.

The dashboard is read-only.

## Automation

Internal cron:

`model_activation_contract_refresh_6h`

Schedule:

`47 */6 * * *`

It only creates draft contracts from newly approved promotion packages. It never enables execution and never changes P50.
