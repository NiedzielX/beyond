-- Beyond Live Demand Engine — versioned contract registry v1

create table if not exists private.live_model_contract_registry_v1 (
    contract_name text not null,
    contract_version text not null,
    object_name text not null,
    object_kind text not null,
    status text not null,
    activated_at timestamptz not null default now(),
    superseded_at timestamptz,
    notes text,
    primary key(contract_name,contract_version),
    constraint live_model_contract_registry_v1_status_ck
      check(status in ('current','lineage','deprecated'))
);

comment on table private.live_model_contract_registry_v1 is
'Versioned registry of Beyond live-model contracts. Exact versioned object names are preferred over implicit aliases for reproducible training/inference lineage.';

insert into private.live_model_contract_registry_v1
(contract_name,contract_version,object_name,object_kind,status,activated_at,notes)
values
('live_trajectory_features','v1','public.get_live_trajectory_features_v1_asof','function','lineage','2026-10-15T00:00:00Z','Initial canonical PIT feature contract.'),
('live_trajectory_features','v1.1','public.get_live_trajectory_features_v1_1_asof','function','current','2026-10-15T00:00:00Z','Current calibrated release/anomaly semantics; feature_version=live-trajectory-v1.1.'),
('horizon_readiness','v1','private.ticketing_horizon_checkpoint_readiness_v1','view','deprecated','2026-10-15T00:00:00Z','Legacy nearest-snapshot semantics; do not use for new modelling because it can select post-checkpoint evidence.'),
('horizon_readiness','v2','private.ticketing_horizon_readiness_v2','view','lineage','2026-10-15T00:00:00Z','First exact-cutoff PIT readiness contract.'),
('horizon_readiness','v2.1','private.ticketing_horizon_readiness_v2_1','view','current','2026-10-15T00:00:00Z','Current exact-cutoff readiness using live-trajectory-v1.1.'),
('feature_evidence_store','v1','private.live_trajectory_feature_snapshots_v1','table','current','2026-10-15T00:00:00Z','Append-only point-in-time feature evidence.'),
('current_feature_evidence','v1','private.current_live_trajectory_feature_snapshots_v1','view','current','2026-10-15T00:00:00Z','Latest materialization per event/horizon/as-of/version while retaining prior evidence.'),
('feature_materializer','v1','private.materialize_live_trajectory_feature_snapshot_v1','function','current','2026-10-15T00:00:00Z','Idempotent single-as-of feature materializer.'),
('due_checkpoint_materializer','v1','private.materialize_due_live_trajectory_checkpoints_v1','function','current','2026-10-15T00:00:00Z','Bulk materializer for due exact business checkpoints.')
on conflict(contract_name,contract_version) do update
set object_name=excluded.object_name,
    object_kind=excluded.object_kind,
    status=excluded.status,
    notes=excluded.notes;

create or replace view private.current_live_model_contracts_v1 as
select contract_name,contract_version,object_name,object_kind,activated_at,notes
from private.live_model_contract_registry_v1
where status='current';

comment on view private.current_live_model_contracts_v1 is
'Current explicit versioned Beyond live-model contracts. This registry is descriptive lineage; consumers should still persist the exact contract version used.';
