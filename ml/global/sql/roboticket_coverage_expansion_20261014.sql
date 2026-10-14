-- Beyond Ticketing — RoboTicket coverage expansion 2026-10-14
-- Adds verified future fixtures and removes a bad Górnik bundle mapping from model-linked snapshots.

select setval('public.ticket_events_id_seq',(select max(id) from public.ticket_events),true);

insert into public.ticket_events(
  id,provider,external_event_id,home_team,away_team,competition,match_date,kickoff_at,
  source_url,mapping_source,mapping_confidence,club_slug,source_domain
)
values
  (nextval('public.ticket_events_id_seq'),'roboticket','5422','Jagiellonia Białystok','Wisła Płock','Ekstraklasa',date '2026-10-25',timestamptz '2026-10-25 13:45:00+00','https://bilety.jagiellonia.pl/Stadium/Index?eventId=5422','roboticket_discovery+official_club_schedule','confirmed','jagiellonia','bilety.jagiellonia.pl'),
  (nextval('public.ticket_events_id_seq'),'roboticket','8438','Legia Warszawa','Lech Poznań','Ekstraklasa',date '2026-10-25',timestamptz '2026-10-25 16:30:00+00','https://bilety.legia.com/Stadium/Index?eventId=8438','roboticket_discovery+official_club_schedule','confirmed','legia','bilety.legia.com'),
  (nextval('public.ticket_events_id_seq'),'roboticket','8550','Śląsk Wrocław','Wieczysta Kraków','Ekstraklasa',date '2026-10-25',timestamptz '2026-10-25 11:15:00+00','https://bilety.slaskwroclaw.pl/Stadium/Index?eventId=8550','roboticket_discovery+official_league_schedule','confirmed','slaskwroclaw','bilety.slaskwroclaw.pl')
on conflict (provider,source_domain,external_event_id) do update set
  home_team=excluded.home_team,away_team=excluded.away_team,competition=excluded.competition,
  match_date=excluded.match_date,kickoff_at=excluded.kickoff_at,source_url=excluded.source_url,
  mapping_source=excluded.mapping_source,mapping_confidence=excluded.mapping_confidence,
  club_slug=excluded.club_slug,updated_at=now();

update public.roboticket_event_candidates c
set status='collecting',
    metadata=coalesce(c.metadata,'{}'::jsonb)||jsonb_build_object(
      'mapped_ticket_event',true,
      'ticket_event_id',(select te.id from public.ticket_events te where te.provider='roboticket' and te.source_domain=(select rc.source_domain from public.roboticket_clubs rc where rc.club_slug=c.club_slug) and te.external_event_id=c.external_event_id limit 1)
    )
where (c.club_slug='jagiellonia' and c.external_event_id='5422')
   or (c.club_slug='legia' and c.external_event_id='8438')
   or (c.club_slug='slaskwroclaw' and c.external_event_id='8550');

-- Jagiellonia stale/parking candidates are explicitly excluded.
update public.roboticket_event_candidates
set status='ignored',metadata=coalesce(metadata,'{}'::jsonb)||jsonb_build_object('ignore_reason',case
  when external_event_id='5322' then 'historical_stale_mapping'
  else 'parking_event' end)
where club_slug='jagiellonia' and external_event_id in ('5157','5322','5421');

-- Correct Górnik–Piast: 5213 is a DWUPAK bundle, 5741 is the single match.
update public.snapshots
set ticket_event_id=null
where ticket_event_id=(select id from public.ticket_events where club_slug='gornikzabrze' and home_team='Górnik Zabrze' and away_team='Piast Gliwice' order by id desc limit 1)
  and event_id=5213;

update public.ticket_events
set external_event_id='5741',source_url='https://bilety.gornikzabrze.pl/Stadium/Index?eventId=5741',
    mapping_source='roboticket_discovery_exact_match_label',mapping_confidence='confirmed',updated_at=now()
where club_slug='gornikzabrze' and home_team='Górnik Zabrze' and away_team='Piast Gliwice';

update public.roboticket_event_candidates
set status=case when external_event_id='5741' then 'collecting' else 'ignored' end,
    metadata=coalesce(metadata,'{}'::jsonb)||case when external_event_id='5741'
      then jsonb_build_object('mapped_ticket_event',true)
      else jsonb_build_object('ignore_reason','bundle_dwupak_not_single_match') end
where club_slug='gornikzabrze' and external_event_id in ('5213','5741');

-- Jagiellonia is now covered by the generic collector; remove the stale one-event cron.
do $$ declare v_job bigint; begin
  select jobid into v_job from cron.job where jobname='jaga_roboticket_15m';
  if v_job is not null then perform cron.unschedule(v_job); end if;
end $$;
