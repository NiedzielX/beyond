"""Isolated PostgreSQL tests for Roboticket explicit forward-only admission v2.

Only synthetic fixtures run here. The target database is strictly constrained
on localhost and this test never connects to a Supabase project.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import unittest
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import psycopg
from psycopg.types.json import Jsonb


class RoboticketForwardOnlyAdmissionV2(unittest.TestCase):
    counter = 900_000
    migration = Path(__file__).resolve().parents[2] / "supabase/sql/roboticket_forward_only_admission_v2.sql"

    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("ROBOTICKET_ADMISSION_TEST_DSN", "")
        target = urlparse(dsn)
        if target.hostname not in {"127.0.0.1", "localhost"} or target.path != "/roboticket_admission_test":
            raise RuntimeError("Only the disposable localhost roboticket_admission_test database is allowed")
        cls.dsn = dsn
        cls.owner = psycopg.connect(dsn, autocommit=True)
        cls.owner.execute("""
          create role anon nologin;
          create role authenticated nologin;
          create role service_role nologin;
          create schema private;
          grant usage on schema public to anon,authenticated,service_role;
          create table public.roboticket_clubs (
            club_slug text primary key, club_name text not null, base_url text not null unique,
            source_domain text not null unique, active boolean not null default true,
            created_at timestamptz not null default now(), updated_at timestamptz not null default now()
          );
          create table public.roboticket_event_candidates (
            club_slug text not null references public.roboticket_clubs(club_slug) on update cascade on delete cascade,
            external_event_id text not null, label text, source_url text,
            status text not null default 'discovered', first_seen_at timestamptz not null default now(),
            last_seen_at timestamptz not null default now(), metadata jsonb not null default '{}'::jsonb,
            primary key(club_slug,external_event_id),
            check(status in ('discovered','mapped','collecting','ignored','expired'))
          );
          create table public.ticket_events (
            id bigserial primary key, provider text not null, external_event_id text not null,
            home_team text not null, away_team text not null, competition text,
            match_date date not null, kickoff_at timestamptz not null, source_url text,
            mapping_source text, mapping_confidence text, created_at timestamptz not null default now(),
            updated_at timestamptz not null default now(), club_slug text not null, source_domain text not null,
            unique(provider,source_domain,external_event_id)
          );
          create table public.snapshots (
            id bigserial primary key, ticket_event_id bigint references public.ticket_events(id),
            event_id bigint, source text, captured_at timestamptz not null,
            event_match_date_at_capture date, event_kickoff_at_capture timestamptz,
            available_total integer, sector_count integer
          );
          create table private.roboticket_verified_schedule_v1 (
            club_slug text not null, external_event_id text not null,
            home_team text not null, away_team text not null, competition text not null default 'Ekstraklasa',
            kickoff_at timestamptz not null, source_url text not null, source_type text not null,
            verification_confidence text not null default 'verified', verified_at timestamptz not null default now(),
            promoted_ticket_event_id bigint references public.ticket_events(id), promoted_at timestamptz,
            primary key(club_slug,external_event_id),
            check(length(trim(home_team))>0 and length(trim(away_team))>0),
            check(verification_confidence in ('verified','high'))
          );
          create table private.roboticket_candidate_snapshots_v1 (
            id bigint generated always as identity primary key,
            club_slug text not null, external_event_id text not null, captured_at timestamptz not null,
            available_total integer, sector_count integer, state jsonb not null,
            source_url text, source_timestamp text, collector_version text not null,
            promoted_ticket_event_id bigint references public.ticket_events(id),
            promoted_snapshot_id bigint references public.snapshots(id), promoted_at timestamptz,
            created_at timestamptz not null default now()
          );
          create table private.structural_prior_club_aliases_v1 (
            alias text primary key, club_key text not null, canonical_name text not null,
            is_active boolean not null default true, source text not null default 'verified_mapping',
            created_at timestamptz not null default now()
          );
          create table private.structural_prior_competition_aliases_v1 (
            alias text primary key, canonical_competition text not null,
            is_active boolean not null default true, source text not null default 'manual_verified',
            created_at timestamptz not null default now()
          );
        """)
        cls.owner.execute(cls.migration.read_text())
        cls.owner.execute("""
          insert into public.roboticket_clubs(club_slug,club_name,base_url,source_domain) values
            ('testclub','Test Club','https://tickets.test','tickets.test');
          insert into public.roboticket_clubs(club_slug,club_name,base_url,source_domain) values
            ('otherclub','Other Club','https://other.test','other.test');
          insert into private.structural_prior_club_aliases_v1(alias,club_key,canonical_name) values
            ('Test Home','home_key','Test Home'),('Test Away','away_key','Test Away'),
            ('Test Club','home_key','Test Club'),
            ('Other Home','other_home','Other Home'),('Other Away','other_away','Other Away'),
            ('Other Club','other_home','Other Club');
          insert into private.structural_prior_competition_aliases_v1(alias,canonical_competition)
            values('Ekstraklasa','Ekstraklasa');
          grant usage on schema private to anon,authenticated,service_role;
        """)

    @classmethod
    def tearDownClass(cls):
        cls.owner.close()

    def setUp(self):
        self.db = psycopg.connect(self.dsn, autocommit=True)

    def tearDown(self):
        self.db.close()

    @classmethod
    def unique_id(cls):
        cls.counter += 1
        return str(cls.counter)

    def now(self):
        return self.db.execute("select clock_timestamp()").fetchone()[0]

    def plan(self, *, club="testclub", event_id=None, domain="tickets.test", home="Test Home", away="Test Away",
             home_key="home_key", away_key="away_key", kickoff=None, civil_date=None):
        event_id = event_id or self.unique_id()
        now = self.now()
        kickoff = kickoff or now + timedelta(days=5 + (int(event_id) % 20))
        civil_date = civil_date or kickoff.astimezone(ZoneInfo("Europe/Warsaw")).date()
        source_domain = domain
        page_url = f"https://{domain}/Stadium/Index?eventId={event_id}"
        runtime_at = now - timedelta(seconds=2)
        civil_time = kickoff.astimezone(ZoneInfo("Europe/Warsaw")).strftime("%H:%M")
        plan_evidence = {
            "status": "PREPARATION_REQUIRES_RUNTIME_RECHECK",
            "admitted": False,
            "historical_backfill": False,
            "writes_performed": False,
            "network_requests_performed": False,
            "collection_readiness": "NOT_ASSESSED",
            "club_slug": club,
            "roboticket_event_id": event_id,
            "canonical_home_club_key": home_key,
            "canonical_away_club_key": away_key,
            "competition": "Ekstraklasa",
            "source_event_id": "2490001",
            "ticket_event_id": None,
            "kickoff_at": kickoff.isoformat(),
            "civil_date": civil_date.isoformat(),
            "civil_time": civil_time,
            "time_zone": "Europe/Warsaw",
            "h1_home_team_text": home,
            "h1_away_team_text": away,
            "ticket_source_domain": domain,
            "ticket_source_url": page_url,
            "original_html_sha256": "a" * 64,
            "provider_body_sha256": "b" * 64,
            "acquisition_index_sha256": "c" * 64,
            "source_retrieved_at_bound": (now - timedelta(hours=1)).isoformat(),
        }
        runtime = {
            "ticket_source_domain": source_domain,
            "ticket_page_url": page_url,
            "home_team": home,
            "away_team": away,
            "ticket_html_sha256": "a" * 64,
            "provider_body_sha256": "b" * 64,
            "retrieved_at": runtime_at.isoformat(),
            "provider_home_club_key": home_key,
            "provider_away_club_key": away_key,
            "civil_time": civil_time,
            "provider_source_domain": "www.thesportsdb.com",
            "provider_source_type": "thesportsdb_league_schedule",
            "provider_competition": "Ekstraklasa",
            "provider_event_id": "2490001",
            "provider_match_date": civil_date.isoformat(),
        }
        plan_json = json.dumps(plan_evidence, ensure_ascii=False, separators=(",", ":"))
        return {"club_slug": club, "roboticket_event_id": event_id,
                "plan_sha256": hashlib.sha256(plan_json.encode("utf-8")).hexdigest(),
                "plan_evidence": plan_evidence, "plan_evidence_json": plan_json,
                "runtime_recheck": runtime}

    def request(self, *fixtures):
        return {"version": "roboticket-explicit-admission-request-v2", "fixtures": list(fixtures)}

    def resign_plan(self, fixture):
        encoded=json.dumps(fixture["plan_evidence"],ensure_ascii=False,separators=(",",":"))
        fixture["plan_evidence_json"]=encoded
        fixture["plan_sha256"]=hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def admit(self, *fixtures, role="service_role", connection=None):
        db = connection or self.db
        db.execute("set role " + role)
        try:
            return db.execute("select public.admit_roboticket_explicit_fixtures_v2(%s)",
                              (Jsonb(self.request(*fixtures)),)).fetchone()[0]
        finally:
            db.execute("reset role")

    def seed_candidate(self, fixture):
        pe = fixture["plan_evidence"]
        self.db.execute("insert into public.roboticket_event_candidates(club_slug,external_event_id,label,source_url,status,metadata) values(%s,%s,%s,%s,'discovered',%s)",
                        (fixture["club_slug"],fixture["roboticket_event_id"],
                         fixture["runtime_recheck"]["home_team"]+" - "+fixture["runtime_recheck"]["away_team"],
                         fixture["runtime_recheck"]["ticket_page_url"],Jsonb({"candidate_kind":"match"})))
        self.db.execute("insert into private.roboticket_candidate_snapshots_v1(club_slug,external_event_id,captured_at,available_total,sector_count,state,collector_version) values(%s,%s,%s,123,1,'{}','legacy-v1')",
                        (fixture["club_slug"],fixture["roboticket_event_id"],pe["source_retrieved_at_bound"]))

    def counts(self, fixture):
        club,event=fixture["club_slug"],fixture["roboticket_event_id"]
        return self.db.execute("""select
          (select count(*) from private.roboticket_candidate_snapshots_v1 where club_slug=%s and external_event_id=%s),
          (select count(*) from public.snapshots),
          (select count(*) from public.ticket_events where provider='roboticket' and club_slug=%s and external_event_id=%s),
          (select count(*) from private.roboticket_admission_receipts_v2 where club_slug=%s and external_event_id=%s)
        """,(club,event,club,event,club,event)).fetchone()

    def test_service_role_admission_records_actual_clock_and_never_backfills(self):
        fixture=self.plan();self.seed_candidate(fixture);before=self.counts(fixture);wall_before=self.now()
        result=self.admit(fixture)
        after=self.counts(fixture);wall_after=self.now()
        row=self.db.execute("select known_at,ticket_event_id from private.roboticket_admission_receipts_v2 where club_slug=%s and external_event_id=%s",
                            (fixture["club_slug"],fixture["roboticket_event_id"])).fetchone()
        self.assertEqual(before[0],after[0]);self.assertEqual(before[1],after[1])
        self.assertEqual(after[2:],(1,1));self.assertTrue(wall_before<=row[0]<=wall_after)
        self.assertEqual(result["version"],"roboticket-explicit-admission-v2")
        self.assertEqual(result["backfilled_snapshots"],0)
        self.assertFalse(result["model_activation"]);self.assertEqual(result["live_adjustment"],0)

    def test_exact_retry_is_idempotent_and_conflicting_hash_rejects(self):
        fixture=self.plan();self.seed_candidate(fixture);self.admit(fixture)
        first=self.db.execute("select known_at,ticket_event_id from private.roboticket_admission_receipts_v2 where club_slug=%s and external_event_id=%s",
                              (fixture["club_slug"],fixture["roboticket_event_id"])).fetchone()
        result=self.admit(fixture)
        second=self.db.execute("select known_at,ticket_event_id from private.roboticket_admission_receipts_v2 where club_slug=%s and external_event_id=%s",
                               (fixture["club_slug"],fixture["roboticket_event_id"])).fetchone()
        self.assertEqual(first,second);self.assertEqual(self.counts(fixture)[2:],(1,1))
        changed=deepcopy(fixture);changed["plan_evidence"]["original_html_sha256"]="9"*64
        changed["runtime_recheck"]["ticket_html_sha256"]="9"*64;self.resign_plan(changed)
        with self.assertRaises(psycopg.Error):self.admit(changed)
        self.assertEqual(self.counts(fixture)[2:],(1,1))
        self.assertEqual(result["tracking_created_count"],0)

    def test_invalid_club_domain_alias_and_kickoff_reject_without_mutation(self):
        cases=[]
        f=self.plan();cases.append(("missing candidate",f,False))
        f=self.plan();self.seed_candidate(f);bad=deepcopy(f);bad["runtime_recheck"]["ticket_source_domain"]="wrong.test";cases.append(("wrong domain",bad,True))
        f=self.plan();self.seed_candidate(f);bad=deepcopy(f);bad["plan_evidence"]["canonical_away_club_key"]="wrong";cases.append(("wrong alias",bad,True))
        f=self.plan();self.seed_candidate(f);cases.append(("inactive club",f,True))
        f=self.plan(kickoff=self.now()-timedelta(minutes=1));self.seed_candidate(f);cases.append(("past kickoff",f,True))
        for name,fixture,seeded in cases:
            with self.subTest(name=name):
                if name == "inactive club":
                    self.db.execute("update public.roboticket_clubs set active=false where club_slug='testclub'")
                before=self.counts(fixture)
                with self.assertRaises(psycopg.Error):self.admit(fixture)
                self.assertEqual(self.counts(fixture),before)
                if name == "inactive club":
                    self.db.execute("update public.roboticket_clubs set active=true where club_slug='testclub'")

    def test_v1_schedule_presence_blocks_admission_and_v2_receipt_blocks_v1_write(self):
        fixture=self.plan();self.seed_candidate(fixture);r=fixture["runtime_recheck"];p=fixture["plan_evidence"]
        self.db.execute("insert into private.roboticket_verified_schedule_v1(club_slug,external_event_id,home_team,away_team,kickoff_at,source_url,source_type) values(%s,%s,%s,%s,%s,%s,'legacy')",
                        (fixture["club_slug"],fixture["roboticket_event_id"],r["home_team"],r["away_team"],p["kickoff_at"],r["ticket_page_url"]))
        with self.assertRaises(psycopg.Error):self.admit(fixture)
        self.db.execute("delete from private.roboticket_verified_schedule_v1 where club_slug=%s and external_event_id=%s",
                        (fixture["club_slug"],fixture["roboticket_event_id"]))
        self.admit(fixture)
        with self.assertRaises(psycopg.Error):
            self.db.execute("insert into private.roboticket_verified_schedule_v1(club_slug,external_event_id,home_team,away_team,kickoff_at,source_url,source_type) values(%s,%s,%s,%s,%s,%s,'legacy')",
                            (fixture["club_slug"],fixture["roboticket_event_id"],r["home_team"],r["away_team"],p["kickoff_at"],r["ticket_page_url"]))
        unrelated=self.plan(club="otherclub",domain="other.test",home="Other Home",away="Other Away",home_key="other_home",away_key="other_away")
        self.seed_candidate(unrelated)
        self.db.execute("insert into private.roboticket_verified_schedule_v1(club_slug,external_event_id,home_team,away_team,kickoff_at,source_url,source_type) values(%s,%s,%s,%s,%s,%s,'legacy')",
                        (unrelated["club_slug"],unrelated["roboticket_event_id"],"Other Home","Other Away",unrelated["plan_evidence"]["kickoff_at"],unrelated["runtime_recheck"]["ticket_page_url"]))
        update_sql="update private.roboticket_verified_schedule_v1 set club_slug=%s,external_event_id=%s where club_slug=%s and external_event_id=%s"
        with self.assertRaises(psycopg.Error):
            self.db.execute(update_sql,(fixture["club_slug"],fixture["roboticket_event_id"],unrelated["club_slug"],unrelated["roboticket_event_id"]))

    def test_non_read_committed_and_browser_roles_are_denied(self):
        fixture=self.plan();self.seed_candidate(fixture)
        self.db.execute("begin isolation level repeatable read")
        try:
            with self.assertRaises(psycopg.Error):
                self.db.execute("select public.admit_roboticket_explicit_fixtures_v2(%s)",(Jsonb(self.request(fixture)),))
        finally:self.db.execute("rollback")
        for role in ("anon","authenticated"):
            with self.subTest(role=role):
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.admit(fixture,role=role)
                self.db.execute("set role "+role)
                try:
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        self.db.execute("select * from private.roboticket_admission_receipts_v2")
                finally:self.db.execute("reset role")
        self.db.execute("set role service_role")
        try:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                self.db.execute("select * from private.roboticket_admission_receipts_v2")
        finally:self.db.execute("reset role")
        other=self.plan(club="otherclub",domain="other.test",home="Other Home",away="Other Away",home_key="other_home",away_key="other_away")
        self.seed_candidate(other)
        r=other["runtime_recheck"];p=other["plan_evidence"]
        self.db.execute("begin isolation level repeatable read")
        try:
            with self.assertRaises(psycopg.Error):
                self.db.execute("insert into private.roboticket_verified_schedule_v1(club_slug,external_event_id,home_team,away_team,kickoff_at,source_url,source_type) values(%s,%s,%s,%s,%s,%s,'legacy')",
                                (other["club_slug"],other["roboticket_event_id"],r["home_team"],r["away_team"],p["kickoff_at"],r["ticket_page_url"]))
        finally:self.db.execute("rollback")

    def test_v1_wins_race_v2_then_observes_existing_schedule(self):
        fixture=self.plan();self.seed_candidate(fixture);r=fixture["runtime_recheck"];p=fixture["plan_evidence"]
        dsn=self.dsn
        sql=f"begin; insert into private.roboticket_verified_schedule_v1(club_slug,external_event_id,home_team,away_team,kickoff_at,source_url,source_type) values('{fixture['club_slug']}','{fixture['roboticket_event_id']}','{r['home_team']}','{r['away_team']}','{p['kickoff_at']}','{r['ticket_page_url']}','legacy'); select pg_sleep(1); commit;"
        with ThreadPoolExecutor(max_workers=2) as pool:
            v1=pool.submit(self._psql,sql,False)
            time.sleep(0.2)
            v2=pool.submit(self._admit_new_connection,fixture)
            out1=v1.result(timeout=15);out2=v2.result(timeout=15)
        self.assertEqual(out1.returncode,0,out1.stderr);self.assertNotEqual(out2[0],0)
        self.assertIn("ROBOTICKET_ADMISSION_V1_SCHEDULE_ALREADY_OWNS_IDENTITY",out2[2])
        self.assertEqual(self.counts(fixture)[3],0)

    def test_prefix_slug_lock_order_matches_legacy_trigger(self):
        # Tuple ordering would acquire testclub:A before testclub1:B, while the
        # legacy UPDATE trigger compares the concatenated lock keys and takes
        # testclub1:B first. Hold B, then race a v2 batch against a v1 insert A:
        # v2 must wait on B without holding A so v1 can commit A and v2 can
        # reject the now-v1-owned identity without a deadlock.
        self.db.execute("insert into public.roboticket_clubs(club_slug,club_name,base_url,source_domain) values('testclub1','Test Club','https://tickets-prefix.test','tickets-prefix.test')")
        fixture_a=self.plan(event_id=self.unique_id())
        fixture_b=self.plan(club="testclub1",domain="tickets-prefix.test",event_id=self.unique_id())
        self.seed_candidate(fixture_a);self.seed_candidate(fixture_b)

        holder=psycopg.connect(self.dsn,autocommit=False)
        holder_pid=holder.execute("select pg_backend_pid()").fetchone()[0]
        holder.execute("select private.lock_roboticket_admission_identity_v2('testclub1',%s)",
                       (fixture_b["roboticket_event_id"],))
        ready=threading.Event()
        state={}

        def admit_batch():
            with psycopg.connect(self.dsn,autocommit=True) as db:
                state["pid"]=db.execute("select pg_backend_pid()").fetchone()[0]
                ready.set()
                try:
                    self.admit(fixture_a,fixture_b,connection=db)
                    return None
                except psycopg.Error as error:
                    return str(error)

        pool=ThreadPoolExecutor(max_workers=1)
        future=pool.submit(admit_batch)
        try:
            self.assertTrue(ready.wait(timeout=5),"admission worker did not connect")
            deadline=time.monotonic()+2
            blocked=False
            while time.monotonic()<deadline and not future.done():
                blockers,wait_type=self.db.execute(
                    "select pg_blocking_pids(%s),wait_event_type from pg_stat_activity where pid=%s",
                    (state["pid"],state["pid"]),
                ).fetchone()
                if holder_pid in blockers and wait_type=="Lock":
                    blocked=True
                    break
                time.sleep(0.02)
            self.assertTrue(blocked,"v2 batch did not wait on the held testclub1:B lock")

            holder.execute("set local lock_timeout='2s'")
            r=fixture_a["runtime_recheck"];p=fixture_a["plan_evidence"]
            holder.execute(
                "insert into private.roboticket_verified_schedule_v1(club_slug,external_event_id,home_team,away_team,kickoff_at,source_url,source_type) values(%s,%s,%s,%s,%s,%s,'legacy')",
                (fixture_a["club_slug"],fixture_a["roboticket_event_id"],r["home_team"],r["away_team"],p["kickoff_at"],r["ticket_page_url"]),
            )
            holder.commit()
            error=future.result(timeout=10)
            self.assertIsNotNone(error,"v2 should reject the v1-owned A identity")
            self.assertIn("ROBOTICKET_ADMISSION_V1_SCHEDULE_ALREADY_OWNS_IDENTITY",error)
            self.assertEqual(self.db.execute(
                "select count(*) from private.roboticket_verified_schedule_v1 where club_slug='testclub' and external_event_id=%s",
                (fixture_a["roboticket_event_id"],),
            ).fetchone()[0],1)
            self.assertEqual(self.counts(fixture_a)[3],0)
            self.assertEqual(self.counts(fixture_b)[3],0)
        finally:
            if not holder.closed:
                holder.rollback()
                holder.close()
            pool.shutdown(wait=True)

    def test_v2_wins_race_legacy_write_then_v1_trigger_rejects(self):
        fixture=self.plan();self.seed_candidate(fixture)
        db=psycopg.connect(self.dsn,autocommit=False)
        try:
            result=self.admit(fixture,connection=db)
            self.assertEqual(result["tracking_created_count"],1)
            r=fixture["runtime_recheck"];p=fixture["plan_evidence"]
            sql=f"insert into private.roboticket_verified_schedule_v1(club_slug,external_event_id,home_team,away_team,kickoff_at,source_url,source_type) values('{fixture['club_slug']}','{fixture['roboticket_event_id']}','{r['home_team']}','{r['away_team']}','{p['kickoff_at']}','{r['ticket_page_url']}','legacy');"
            with ThreadPoolExecutor(max_workers=1) as pool:
                v1=pool.submit(self._psql,sql,False);time.sleep(0.2);db.commit();out=v1.result(timeout=15)
            self.assertNotEqual(out.returncode,0);self.assertIn("ROBOTICKET_V1_SCHEDULE_BLOCKED_BY_V2_ADMISSION",out.stderr)
            self.assertEqual(self.counts(fixture)[3],1)
        finally:
            if not db.closed:db.close()

    def test_v2_transaction_rollback_leaves_no_receipt_or_tracking(self):
        fixture=self.plan();self.seed_candidate(fixture)
        db=psycopg.connect(self.dsn,autocommit=False)
        try:
            result=self.admit(fixture,connection=db);self.assertEqual(result["tracking_created_count"],1)
            db.rollback()
        finally:db.close()
        self.assertEqual(self.counts(fixture)[2:],(0,0))
        r=fixture["runtime_recheck"];p=fixture["plan_evidence"]
        self.db.execute("insert into private.roboticket_verified_schedule_v1(club_slug,external_event_id,home_team,away_team,kickoff_at,source_url,source_type) values(%s,%s,%s,%s,%s,%s,'legacy')",
                        (fixture["club_slug"],fixture["roboticket_event_id"],r["home_team"],r["away_team"],p["kickoff_at"],r["ticket_page_url"]))

    def test_invalid_later_fixture_rolls_back_entire_batch(self):
        first=self.plan();second=self.plan(club="otherclub",domain="other.test",home="Other Home",away="Other Away",home_key="other_home",away_key="other_away")
        self.seed_candidate(first);self.seed_candidate(second)
        second["runtime_recheck"]["ticket_source_domain"]="wrong.test"
        before_first=self.counts(first);before_second=self.counts(second)
        with self.assertRaises(psycopg.Error):self.admit(first,second)
        self.assertEqual(self.counts(first),before_first)
        self.assertEqual(self.counts(second),before_second)

    def test_concurrent_identical_v2_requests_commit_exactly_once(self):
        fixture=self.plan();self.seed_candidate(fixture)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(self._admit_new_connection,fixture) for _ in range(2)]
            results=[f.result(timeout=15) for f in futures]
        self.assertTrue(all(code==0 for code,_,_ in results),results)
        self.assertEqual(self.counts(fixture)[2:],(1,1))

    def _admit_new_connection(self, fixture):
        try:
            with psycopg.connect(self.dsn,autocommit=True) as conn:
                out=self.admit(fixture,connection=conn)
                return 0,out,""
        except Exception as e:
            return 1,None,str(e)

    def _psql(self, query, expect_success):
        # psql runs inside the already isolated disposable container.
        import subprocess
        proc=subprocess.run(["docker","exec","-i","beyond-roboticket-admission-v2-test","psql","-v","ON_ERROR_STOP=1","-U","postgres","-d","roboticket_admission_test","-c",query],
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=20)
        if expect_success and proc.returncode:
            raise AssertionError(proc.stderr)
        return proc


if __name__ == "__main__":
    unittest.main()
