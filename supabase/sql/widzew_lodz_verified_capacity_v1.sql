-- Verified football capacity for Widzew Łódź / Stadion Miejski Widzewa Łódź.
--
-- Source: official City of Łódź portal (ŁÓDŹ.PL), which states that the current
-- stadium at al. Piłsudskiego 138 can accommodate 18,018 spectators.
--
-- This is a source-data addition only. It does not alter model artifacts,
-- coefficients, forecasts, labels, frozen prospective evidence, or production
-- activation rules. Existing missed windows remain missed and are not backfilled.

insert into private.structural_prior_capacity_registry_v1(
  club_key,
  valid_from,
  valid_to,
  stadium_capacity,
  verification_status,
  source_name,
  source_url,
  verified_at,
  notes
)
select
  'widzewlodz',
  date '2026-07-01',
  null,
  18018,
  'verified',
  'Miasto Łódź — ŁÓDŹ.PL, Stadion Widzewa Łódź',
  'https://lodz.pl/galeria/pilkarskie-miejsca-w-lodzi-to-nie-tylko-stadiony-widzewa-i-lks-przewodnik-55053/?imgNum=2',
  now(),
  'Official City of Łódź portal states that the current Stadion Widzewa Łódź can accommodate 18,018 spectators. Added for prospective 2026/27 Structural Prior inference.'
where not exists (
  select 1
  from private.structural_prior_capacity_registry_v1
  where club_key='widzewlodz'
    and valid_from=date '2026-07-01'
    and stadium_capacity=18018
);
