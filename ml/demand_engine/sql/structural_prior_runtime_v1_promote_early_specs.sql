-- Promote the reproducible Structural Prior Runtime v1 candidates for T-30/T-14.
-- The old specs remain as lineage but are no longer current.

update private.structural_prior_model_specs_v1
set is_current=false
where horizon in ('T-30','T-14')
  and is_current;

insert into private.structural_prior_model_specs_v1(
    horizon,target_days_before,model_spec_id,model_family,feature_contract,
    validation_report,status,is_current,activated_at,notes,validated_competitions
) values
('T-30',30,'structural-prior-runtime-v1-t30-extra-full','ExtraTreesRegressor','structural-prior-pit-v1+verified-capacity-v1','ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md','historical_champion_candidate',true,'2026-10-15T00:00:00Z','Reproducible early-horizon runtime candidate: 2024/25 MAE 1889.4; 2025/26 MAE 1846.3.',array['Ekstraklasa']::text[]),
('T-14',14,'structural-prior-runtime-v1-t14-hist-base','HistGradientBoostingRegressor','structural-prior-pit-v1+verified-capacity-v1','ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md','historical_champion_candidate',true,'2026-10-15T00:00:00Z','Reproducible early-horizon runtime candidate: 2024/25 MAE 1748.5; 2025/26 MAE 1870.4.',array['Ekstraklasa']::text[])
on conflict(horizon,model_spec_id) do update
set target_days_before=excluded.target_days_before,
    model_family=excluded.model_family,
    feature_contract=excluded.feature_contract,
    validation_report=excluded.validation_report,
    status=excluded.status,
    is_current=excluded.is_current,
    notes=excluded.notes,
    validated_competitions=excluded.validated_competitions;
