-- Verified football capacity for Motor Lublin / Arena Lublin.
--
-- Source: official MOSiR Lublin Arena material.
-- The venue lists 15,243 seated places and 19,000 maximum event capacity.
-- Structural Prior uses football seated stadium capacity, therefore 15,243.
--
-- This is a source-data addition only. It does not alter model artifacts,
-- coefficients, forecasts, labels, or production activation rules.

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
  'motorlublin',
  date '2026-07-01',
  null,
  15243,
  'verified',
  'MOSiR Lublin — Arena Lublin official venue material',
  'https://mosir.lublin.pl/wp-content/uploads/2021/04/arena_folder_2021_on_line_1.pdf',
  now(),
  'Official venue material lists 15,243 seated places; 19,000 is the maximum event capacity including floor use. Football Structural Prior uses seated capacity.'
where not exists (
  select 1
  from private.structural_prior_capacity_registry_v1
  where club_key='motorlublin'
    and valid_from=date '2026-07-01'
    and stadium_capacity=15243
);
