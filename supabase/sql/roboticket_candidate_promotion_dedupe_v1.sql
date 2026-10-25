-- Candidate promotion v1.1: aggregate source sub-sectors sharing a display name.

create or replace function public.promote_roboticket_verified_candidates_v1()
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $f$
declare
  v record;
  r record;
  v_ticket_event_id bigint;
  v_snapshot_id bigint;
  v_promoted_events integer:=0;
  v_backfilled integer:=0;
  v_unique_sector_count integer;
begin
  for v in
    select s.*,c.base_url,c.source_domain
    from private.roboticket_verified_schedule_v1 s
    join public.roboticket_clubs c on c.club_slug=s.club_slug and c.active
    where s.kickoff_at>clock_timestamp()
  loop
    insert into public.ticket_events(
      provider,external_event_id,home_team,away_team,competition,match_date,kickoff_at,source_url,
      mapping_source,mapping_confidence,club_slug,source_domain,updated_at
    ) values (
      'roboticket',v.external_event_id,v.home_team,v.away_team,v.competition,
      (v.kickoff_at at time zone 'Europe/Warsaw')::date,v.kickoff_at,v.source_url,
      'roboticket_discovery_v7+verified_schedule','verified',v.club_slug,v.source_domain,clock_timestamp()
    )
    on conflict(provider,source_domain,external_event_id) do update set
      home_team=excluded.home_team,away_team=excluded.away_team,competition=excluded.competition,
      match_date=excluded.match_date,kickoff_at=excluded.kickoff_at,source_url=excluded.source_url,
      mapping_source=excluded.mapping_source,mapping_confidence=excluded.mapping_confidence,updated_at=clock_timestamp()
    returning id into v_ticket_event_id;

    update private.roboticket_verified_schedule_v1
      set promoted_ticket_event_id=v_ticket_event_id,promoted_at=coalesce(promoted_at,clock_timestamp())
      where club_slug=v.club_slug and external_event_id=v.external_event_id;
    update public.roboticket_event_candidates
      set status='collecting',metadata=metadata||jsonb_build_object('promoted_ticket_event_id',v_ticket_event_id,'promotion_version','roboticket-candidate-promotion-v1.1')
      where club_slug=v.club_slug and external_event_id=v.external_event_id;
    v_promoted_events:=v_promoted_events+1;

    for r in
      select * from private.roboticket_candidate_snapshots_v1
      where club_slug=v.club_slug and external_event_id=v.external_event_id
        and promoted_snapshot_id is null and captured_at<v.kickoff_at
      order by captured_at
    loop
      select count(distinct x->>'sector')::integer into v_unique_sector_count
      from jsonb_array_elements(coalesce(r.state->'sectors','[]'::jsonb)) x
      where nullif(x->>'sector','') is not null;

      insert into public.snapshots(
        event_id,source,captured_at,ticket_event_id,event_match_date_at_capture,event_kickoff_at_capture,available_total,sector_count
      ) values (
        case when v.external_event_id~'^\d+$' then v.external_event_id::bigint else null end,
        'roboticket_candidate_backfill',r.captured_at,v_ticket_event_id,
        (v.kickoff_at at time zone 'Europe/Warsaw')::date,v.kickoff_at,r.available_total,coalesce(v_unique_sector_count,0)
      ) returning id into v_snapshot_id;

      insert into public.sector_inventory(snapshot_id,event_id,sector,available)
      select v_snapshot_id,
             case when v.external_event_id~'^\d+$' then v.external_event_id::bigint else null end,
             x->>'sector',sum(coalesce((x->>'available')::integer,0))::integer
      from jsonb_array_elements(coalesce(r.state->'sectors','[]'::jsonb)) x
      where nullif(x->>'sector','') is not null
      group by x->>'sector';

      insert into public.sector_price_area_observations_v1(
        ticket_event_id,snapshot_id,captured_at,sector,sector_source_id,price_area_id,price_area_name,available,source
      )
      select v_ticket_event_id,v_snapshot_id,r.captured_at,
             x->>'sector',
             case when count(distinct nullif(x->>'sectorSourceId',''))=1 then max(nullif(x->>'sectorSourceId',''))::bigint else null end,
             (x->>'priceAreaId')::integer,max(x->>'priceAreaName'),sum(coalesce((x->>'available')::integer,0))::integer,
             'roboticket_candidate_backfill'
      from jsonb_array_elements(coalesce(r.state->'sectorPriceAreas','[]'::jsonb)) x
      where nullif(x->>'sector','') is not null and nullif(x->>'priceAreaId','') is not null
      group by x->>'sector',(x->>'priceAreaId')::integer;

      insert into public.ticket_price_observations_v1(
        ticket_event_id,snapshot_id,captured_at,price_area_id,price_area_name,price_type_id,price_type_name,price,currency,source
      )
      select v_ticket_event_id,v_snapshot_id,r.captured_at,(x->>'priceAreaId')::integer,max(x->>'priceAreaName'),
             (x->>'priceTypeId')::integer,max(x->>'priceTypeName'),max((x->>'price')::numeric),max(x->>'currency'),
             'roboticket_candidate_backfill'
      from jsonb_array_elements(coalesce(r.state->'prices','[]'::jsonb)) x
      where nullif(x->>'priceAreaId','') is not null and nullif(x->>'priceTypeId','') is not null and nullif(x->>'price','') is not null
      group by (x->>'priceAreaId')::integer,(x->>'priceTypeId')::integer;

      update private.roboticket_candidate_snapshots_v1
        set promoted_ticket_event_id=v_ticket_event_id,promoted_snapshot_id=v_snapshot_id,promoted_at=clock_timestamp()
        where id=r.id;
      v_backfilled:=v_backfilled+1;
    end loop;
  end loop;

  perform private.refresh_dashboard_ticketing_ingestion_status_v1();
  return jsonb_build_object(
    'version','roboticket-candidate-promotion-v1.1',
    'promoted_event_iterations',v_promoted_events,
    'backfilled_candidate_snapshots',v_backfilled,
    'production_change',false
  );
end;
$f$;

revoke all on function public.promote_roboticket_verified_candidates_v1() from public,anon,authenticated;
grant execute on function public.promote_roboticket_verified_candidates_v1() to service_role;
