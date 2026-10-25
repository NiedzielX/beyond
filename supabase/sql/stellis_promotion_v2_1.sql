-- Stellis promotion v2.1
-- Promotion is governed by canonical candidate semantics as well as raw lineage.
-- Legacy raw rows without competition_hint can never override an explicit cup/non-league exclusion.

create or replace function public.promote_stellis_visible_observations_v1()
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v record;
  v_fixture record;
  v_raw record;
  v_fixture_count integer;
  v_ticket_event_id bigint;
  v_snapshot_id bigint;
  v_promoted_events integer := 0;
  v_promoted_snapshots integer := 0;
begin
  for v in
    select distinct on (r.club_slug,r.external_event_id)
      r.*,sc.source_domain,
      c.status as candidate_status,
      c.event_name as candidate_event_name,
      c.metadata as candidate_metadata
    from private.stellis_raw_observations_v1 r
    join public.stellis_clubs_v1 sc on sc.club_slug=r.club_slug and sc.active
    join public.stellis_event_candidates_v1 c
      on c.club_slug=r.club_slug and c.external_event_id=r.external_event_id
    where r.availability_exposed
      and r.available_total is not null
      and r.kickoff_at is not null
      and r.kickoff_at > clock_timestamp()
      and c.status not in ('non_league','invalid','hidden_availability')
      and coalesce(c.metadata->>'competition_hint','') <> 'cup'
      and coalesce(r.raw_metadata->>'competition_hint','') <> 'cup'
      and coalesce(c.event_name,'') !~* 'puchar[[:space:]]+polski'
    order by r.club_slug,r.external_event_id,r.captured_at desc
  loop
    if v.home_club_key is null or v.away_club_key is null or v.home_club_key <> v.club_slug then
      continue;
    end if;

    select count(*) into v_fixture_count
    from (
      select distinct s.source_event_id
      from public.sporting_league_matches_shadow s
      join private.structural_prior_club_aliases_v1 ha
        on ha.alias=s.home_team and ha.is_active and ha.club_key=v.home_club_key
      join private.structural_prior_club_aliases_v1 aa
        on aa.alias=s.away_team and aa.is_active and aa.club_key=v.away_club_key
      where s.event_date between
        ((v.kickoff_at at time zone 'Europe/Warsaw')::date - 4)
        and ((v.kickoff_at at time zone 'Europe/Warsaw')::date + 4)
    ) q;

    if v_fixture_count=0 then
      update public.stellis_event_candidates_v1
      set status='awaiting_fixture',last_seen_at=clock_timestamp(),
          metadata=metadata||jsonb_build_object('fixture_gate','no_unique_league_pair_in_window')
      where club_slug=v.club_slug and external_event_id=v.external_event_id;
      continue;
    elsif v_fixture_count>1 then
      update public.stellis_event_candidates_v1
      set status='invalid',last_seen_at=clock_timestamp(),
          metadata=metadata||jsonb_build_object('fixture_gate','ambiguous_league_pair_in_window')
      where club_slug=v.club_slug and external_event_id=v.external_event_id;
      continue;
    end if;

    select distinct on (s.source_event_id)
      s.home_team,s.away_team,s.event_date
    into v_fixture
    from public.sporting_league_matches_shadow s
    join private.structural_prior_club_aliases_v1 ha
      on ha.alias=s.home_team and ha.is_active and ha.club_key=v.home_club_key
    join private.structural_prior_club_aliases_v1 aa
      on aa.alias=s.away_team and aa.is_active and aa.club_key=v.away_club_key
    where s.event_date between
      ((v.kickoff_at at time zone 'Europe/Warsaw')::date - 4)
      and ((v.kickoff_at at time zone 'Europe/Warsaw')::date + 4)
    order by s.source_event_id,s.fetched_at desc;

    insert into public.ticket_events(
      provider,external_event_id,home_team,away_team,competition,match_date,kickoff_at,source_url,
      mapping_source,mapping_confidence,club_slug,source_domain,updated_at
    ) values (
      'stellis',v.external_event_id,v_fixture.home_team,v_fixture.away_team,'Ekstraklasa',
      (v.kickoff_at at time zone 'Europe/Warsaw')::date,v.kickoff_at,v.source_url,
      'stellis-visible-availability-v2.1+league-fixture-pair-window','verified',v.club_slug,v.source_domain,clock_timestamp()
    )
    on conflict(provider,source_domain,external_event_id) do update set
      home_team=excluded.home_team,away_team=excluded.away_team,competition=excluded.competition,
      match_date=excluded.match_date,kickoff_at=excluded.kickoff_at,source_url=excluded.source_url,
      mapping_source=excluded.mapping_source,mapping_confidence=excluded.mapping_confidence,updated_at=clock_timestamp()
    returning id into v_ticket_event_id;

    update public.stellis_event_candidates_v1
    set status='collecting',last_seen_at=clock_timestamp(),
        metadata=(metadata-'fixture_gate')||jsonb_build_object('promoted_ticket_event_id',v_ticket_event_id,'promotion_contract','stellis-v2.1')
    where club_slug=v.club_slug and external_event_id=v.external_event_id;
    v_promoted_events:=v_promoted_events+1;

    for v_raw in
      select r.*
      from private.stellis_raw_observations_v1 r
      where r.club_slug=v.club_slug and r.external_event_id=v.external_event_id
        and r.availability_exposed and r.available_total is not null
        and r.promoted_snapshot_id is null and r.captured_at<v.kickoff_at
        and coalesce(r.raw_metadata->>'competition_hint','') <> 'cup'
      order by r.captured_at
    loop
      insert into public.snapshots(
        event_id,source,captured_at,ticket_event_id,event_match_date_at_capture,event_kickoff_at_capture,available_total,sector_count
      ) values (
        case when v.external_event_id~'^\d+$' then v.external_event_id::bigint else null end,
        'stellis_visible_available',v_raw.captured_at,v_ticket_event_id,
        (v.kickoff_at at time zone 'Europe/Warsaw')::date,v.kickoff_at,v_raw.available_total,null
      ) returning id into v_snapshot_id;

      update private.stellis_raw_observations_v1
      set promoted_ticket_event_id=v_ticket_event_id,promoted_snapshot_id=v_snapshot_id,promoted_at=clock_timestamp()
      where id=v_raw.id;
      v_promoted_snapshots:=v_promoted_snapshots+1;
    end loop;
  end loop;

  return jsonb_build_object(
    'version','stellis-visible-promotion-v2.1',
    'promoted_event_iterations',v_promoted_events,
    'promoted_snapshots',v_promoted_snapshots,
    'target_values_used',false,
    'production_change',false
  );
end;
$function$;

-- Reassert explicit historical exclusions before the canonical collector resumes.
update public.stellis_event_candidates_v1
set status='non_league',
    metadata=metadata||jsonb_build_object('competition_hint','cup','promotion_contract','stellis-v2.1')
where event_name ~* 'puchar[[:space:]]+polski';

select private.refresh_dashboard_ticketing_ingestion_status_v1();
