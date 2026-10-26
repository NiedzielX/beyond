-- Verified current-event stadium capacities required by Structural Prior Runtime v1.
-- Sources are current official club / municipal / stadium-operator pages.

begin;

insert into private.structural_prior_capacity_registry_v1(
  club_key,valid_from,valid_to,stadium_capacity,verification_status,
  source_name,source_url,verified_at,notes
) values
(
  'wisla_plock','2026-07-01',null,15004,'verified',
  'Wisła Płock official stadium page','https://wisla-plock.pl/klub/stadion/',now(),
  'ORLEN Stadion official capacity. Added for current-event Structural Prior inference.'
),
(
  'gkskatowice','2026-07-01',null,15048,'verified',
  'Miasto Katowice — Arena Katowice','https://katowice.eu/dla-mieszkanca/aktualnosci?ItemID=7461&ListID=75169dcb-89ef-46cd-a876-165c1e838909',now(),
  'Arena Katowice current capacity. Added for current-event Structural Prior inference.'
),
(
  'cracovia','2026-07-01',null,15016,'verified',
  'Zarząd Infrastruktury Sportowej w Krakowie — Stadion Cracovii','https://zis.krakow.pl/stadion-cracovii-im-jozefa-pilsudskiego?parent=baza-obiektow-sportowych',now(),
  'Stadion Cracovii current capacity. Added for current-event Structural Prior inference.'
),
(
  'gornikzabrze','2026-07-01',null,28236,'verified',
  'Górnik Zabrze — Arena Zabrze','https://www.gornikzabrze.pl/klub/stadion',now(),
  'Arena Zabrze current capacity. Added for current-event Structural Prior inference.'
),
(
  'zaglebie_lubin','2026-07-01',null,16086,'verified',
  'Zagłębie Lubin — KGHM Zagłębie Arena','https://www.zaglebie.com/Klub',now(),
  'KGHM Zagłębie Arena current capacity. Added for current-event Structural Prior inference.'
),
(
  'rakow','2026-07-01',null,5500,'verified',
  'Raków Częstochowa — official club stadium page','https://rakow.com/informacje-i-kontakt-100',now(),
  'zondacrypto Arena current capacity: 5,500 seated places. Verified 2026-10-26 for 2026/27 current-event Structural Prior inference.'
),
(
  'koronakielce','2026-07-01',null,15550,'verified',
  'MOSiR Kielce — Stadion Miejski','https://www.mosir.kielce.pl/obiekty.php?oPath=3&obiekt_id=4',now(),
  'Stadion Miejski / Exbud Arena current capacity: 15,550 seated places. Verified 2026-10-26 for 2026/27 current-event Structural Prior inference.'
)
on conflict (club_key,valid_from,stadium_capacity) do update set
  verification_status=excluded.verification_status,
  source_name=excluded.source_name,
  source_url=excluded.source_url,
  verified_at=excluded.verified_at,
  notes=excluded.notes;

commit;
