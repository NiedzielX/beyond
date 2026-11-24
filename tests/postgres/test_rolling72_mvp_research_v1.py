"""Isolated PostgreSQL 16 tests for the Rolling72 MVP runtime source lane.

All source fixtures are synthetic. The only accepted target is the disposable
loopback database ``rolling72_mvp_research_test`` on port 55440. This suite
does not call a hosted database or a source API.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import timedelta
import hashlib
import importlib.util
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


ROOT = Path(__file__).resolve().parents[2]
LANE = "rolling72-mvp-research-v1"
ADMISSION_SQL = ROOT / "supabase/sql/roboticket_forward_only_admission_v2.sql"
MIGRATION = ROOT / "supabase/sql/rolling72_mvp_research_v1.sql"
ADMISSION_HELPERS = ROOT / "tests/postgres/test_roboticket_forward_only_admission_v2.py"


def _load_admission_helpers():
    spec = importlib.util.spec_from_file_location("admission_v2_fixture_helpers", ADMISSION_HELPERS)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the frozen admission-v2 synthetic fixture helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AdmissionFixtureModule = _load_admission_helpers()


def _admission_helper_class():
    helper_class = AdmissionFixtureModule.RoboticketForwardOnlyAdmissionV2
    helper_class.counter = time.time_ns() // 1000
    return helper_class


def _instant(value):
    if isinstance(value, str):
        return __import__("datetime").datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


class Rolling72MvpResearchV1(unittest.TestCase):
    """Contract tests for committed admission, source reads, and seals."""

    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("ROLLING72_MVP_RESEARCH_TEST_DSN", "")
        target = urlparse(dsn)
        if (target.hostname not in {"127.0.0.1", "localhost"} or target.port != 55440
                or target.path != "/rolling72_mvp_research_test"):
            raise RuntimeError(
                "Only the disposable localhost rolling72_mvp_research_test database is allowed"
            )
        cls.dsn = dsn
        cls.db = psycopg.connect(dsn, autocommit=True)
        version = int(cls.db.execute("show server_version_num").fetchone()[0])
        if version < 160000 or version >= 170000:
            raise RuntimeError("This suite requires PostgreSQL 16")
        cls._bootstrap_parent_schema()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    @classmethod
    def _bootstrap_parent_schema(cls):
        """Install only the frozen v2 admission contract and minimal source tables."""
        if not ADMISSION_SQL.exists():
            raise RuntimeError(f"Missing frozen admission contract: {ADMISSION_SQL}")
        cls.db.execute("""
          do $$ begin
            if not exists(select 1 from pg_roles where rolname='anon') then create role anon nologin; end if;
            if not exists(select 1 from pg_roles where rolname='authenticated') then create role authenticated nologin; end if;
            if not exists(select 1 from pg_roles where rolname='service_role') then create role service_role nologin; end if;
          end $$;
          create schema if not exists private;
          create schema if not exists extensions;
          grant usage on schema public to anon,authenticated,service_role;
          grant usage on schema private to anon,authenticated,service_role;
          create table if not exists public.roboticket_clubs (
            club_slug text primary key, club_name text not null, base_url text not null unique,
            source_domain text not null unique, active boolean not null default true,
            created_at timestamptz not null default now(), updated_at timestamptz not null default now()
          );
          create table if not exists public.roboticket_event_candidates (
            club_slug text not null references public.roboticket_clubs(club_slug) on update cascade on delete cascade,
            external_event_id text not null, label text, source_url text,
            status text not null default 'discovered', first_seen_at timestamptz not null default now(),
            last_seen_at timestamptz not null default now(), metadata jsonb not null default '{}'::jsonb,
            primary key(club_slug,external_event_id),
            check(status in ('discovered','mapped','collecting','ignored','expired'))
          );
          create table if not exists public.ticket_events (
            id bigserial primary key, provider text not null, external_event_id text not null,
            home_team text not null, away_team text not null, competition text,
            match_date date not null, kickoff_at timestamptz not null, source_url text,
            mapping_source text, mapping_confidence text, created_at timestamptz not null default now(),
            updated_at timestamptz not null default now(), club_slug text not null, source_domain text not null,
            unique(provider,source_domain,external_event_id)
          );
          create table if not exists public.snapshots (
            id bigserial primary key, ticket_event_id bigint references public.ticket_events(id),
            event_id bigint, source text, captured_at timestamptz not null,
            event_match_date_at_capture date, event_kickoff_at_capture timestamptz,
            available_total integer, sector_count integer
          );
          create table if not exists private.roboticket_verified_schedule_v1 (
            club_slug text not null, external_event_id text not null,
            home_team text not null, away_team text not null, competition text not null default 'Ekstraklasa',
            kickoff_at timestamptz not null, source_url text not null, source_type text not null,
            verification_confidence text not null default 'verified', verified_at timestamptz not null default now(),
            promoted_ticket_event_id bigint references public.ticket_events(id), promoted_at timestamptz,
            primary key(club_slug,external_event_id),
            check(length(trim(home_team))>0 and length(trim(away_team))>0),
            check(verification_confidence in ('verified','high'))
          );
          create table if not exists private.roboticket_candidate_snapshots_v1 (
            id bigint generated always as identity primary key,
            club_slug text not null, external_event_id text not null, captured_at timestamptz not null,
            available_total integer, sector_count integer, state jsonb not null,
            source_url text, source_timestamp text, collector_version text not null,
            promoted_ticket_event_id bigint references public.ticket_events(id),
            promoted_snapshot_id bigint references public.snapshots(id), promoted_at timestamptz,
            created_at timestamptz not null default now()
          );
          create table if not exists private.structural_prior_club_aliases_v1 (
            alias text primary key, club_key text not null, canonical_name text not null,
            is_active boolean not null default true, source text not null default 'verified_mapping',
            created_at timestamptz not null default now()
          );
          create table if not exists private.structural_prior_competition_aliases_v1 (
            alias text primary key, canonical_competition text not null,
            is_active boolean not null default true, source text not null default 'manual_verified',
            created_at timestamptz not null default now()
          );
          create table if not exists public.sector_price_area_observations_v1 (
            id bigint generated always as identity primary key,
            ticket_event_id bigint not null references public.ticket_events(id),
            snapshot_id bigint references public.snapshots(id), captured_at timestamptz not null,
            sector text not null, sector_source_id bigint, price_area_id integer not null,
            price_area_name text, available integer not null,
            source text not null default 'roboticket', created_at timestamptz not null default now()
          );
          create table if not exists public.sector_inventory (
            id bigint generated always as identity primary key,
            snapshot_id bigint not null references public.snapshots(id), event_id bigint,
            sector text not null, available integer not null
          );
        """)
        # The container is a new, dedicated test database. pgcrypto is needed
        # by the frozen admission contract's SHA-256 compatibility helpers.
        cls.db.execute("create extension if not exists pgcrypto with schema extensions")
        cls.db.execute(cls.admission_sql().read_text())
        cls.db.execute("""
          insert into public.roboticket_clubs(club_slug,club_name,base_url,source_domain) values
            ('testclub','Test Club','https://tickets.test','tickets.test')
            on conflict(club_slug) do nothing;
          insert into private.structural_prior_club_aliases_v1(alias,club_key,canonical_name) values
            ('Test Home','home_key','Test Home'),('Test Away','away_key','Test Away'),
            ('Test Club','home_key','Test Club') on conflict(alias) do nothing;
          insert into private.structural_prior_competition_aliases_v1(alias,canonical_competition)
            values('Ekstraklasa','Ekstraklasa') on conflict(alias) do nothing;
        """)

    @staticmethod
    def admission_sql():
        return ADMISSION_SQL

    def setUp(self):
        self.db = type(self).db
        self._reset_new_lane()
        if not MIGRATION.exists():
            self.fail(f"Missing new migration under test: {MIGRATION}")
        frozen_before = self._frozen_function_hashes()
        self.assertGreaterEqual(len(frozen_before), 4, "expected frozen Roboticket v2 functions")
        self.db.execute(MIGRATION.read_text())
        self.assertEqual(frozen_before, self._frozen_function_hashes(),
                         "new migration changed a preexisting public/private function")
        self.manifest, self.manifest_text, self.manifest_sha = self._activate()
        helper_class = _admission_helper_class()
        self.helper = helper_class.__new__(helper_class)
        self.helper.db = self.db

    def tearDown(self):
        if self.db.info.transaction_status != psycopg.pq.TransactionStatus.IDLE:
            self.db.execute("rollback")

    def _reset_new_lane(self):
        """Reset only the named lane objects in the dedicated disposable DB."""
        for signature in (
            "public.activate_rolling72_mvp_research_v1(text,text)",
            "public.register_rolling72_mvp_research_v1(bigint[])",
            "public.capture_rolling72_mvp_research_v1(integer)",
            "public.get_rolling72_mvp_research_v1_status()",
        ):
            self.db.execute(f"drop function if exists {signature} cascade")
        for table in (
            "rolling72_mvp_research_v1_candidates", "rolling72_mvp_research_v1_seals",
            "rolling72_mvp_research_v1_attempts", "rolling72_mvp_research_v1_runs",
            "rolling72_mvp_research_v1_registration_attempts",
            "rolling72_mvp_research_v1_registry", "rolling72_mvp_research_v1_lane",
        ):
            self.db.execute(f"drop table if exists private.{table} cascade")
        helper_functions = self.db.execute("""
          select p.oid::regprocedure::text
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where n.nspname='private' and p.proname like 'rolling72_mvp_research_v1_%'
          order by p.proname
        """).fetchall()
        for (signature,) in helper_functions:
            self.db.execute(f"drop function if exists {signature} cascade")

    def _frozen_function_hashes(self):
        rows = self.db.execute("""
          select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),pg_get_functiondef(p.oid)
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where n.nspname in ('public','private')
            and p.proname not like '%rolling72_mvp_research_v1%'
          order by n.nspname,p.proname,pg_get_function_identity_arguments(p.oid)
        """).fetchall()
        return {(schema, name, args): hashlib.sha256(definition.encode("utf-8")).hexdigest()
                for schema, name, args, definition in rows}

    def _activate(self):
        now = self.db.execute("select clock_timestamp()").fetchone()[0]
        # Default fixtures use a 25-day issue window; the dedicated early-cycle
        # case extends it to 60 days and registers a P-55 fixture.
        issue_until = now + timedelta(days=25)
        scoring_until = issue_until + timedelta(hours=78)
        manifest = {
            "lane_id": LANE, "version": LANE,
            "source_family": "roboticket/roboticket", "unit": "available_total_seats",
            "max_source_age_seconds": 3600, "max_batch": 25, "max_fixtures": 100,
            "issue_until": issue_until.isoformat(), "scoring_until": scoring_until.isoformat(),
            "sql_sha256": hashlib.sha256(MIGRATION.read_bytes()).hexdigest(),
        }
        encoded = json.dumps(manifest, separators=(",", ":"), sort_keys=True)
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return manifest, encoded, digest

    def _rpc(self, name: str, *args):
        self.db.execute("set role service_role")
        try:
            return self.db.execute(
                f"select public.{name}({','.join(['%s'] * len(args))})", args
            ).fetchone()[0]
        finally:
            self.db.execute("reset role")

    def _plan_fixture(self, *, kickoff_in_days: int = 10, event_id: str | None = None):
        nonce = self.helper.unique_id() if event_id is None else int(event_id)
        event_id = str(nonce) if event_id is None else str(event_id)
        home, away = f"Synthetic Home {nonce}", f"Synthetic Away {nonce}"
        home_key, away_key = "home_key", f"synthetic_away_{nonce}"
        self.db.execute("""
          insert into private.structural_prior_club_aliases_v1(alias,club_key,canonical_name)
          values(%s,%s,%s),(%s,%s,%s) on conflict(alias) do nothing
        """, (home, home_key, home, away, away_key, away))
        kickoff = self.db.execute(
            "select clock_timestamp() + make_interval(days => %s)", (kickoff_in_days,)
        ).fetchone()[0]
        fixture = self.helper.plan(event_id=event_id, home=home, away=away,
                                   home_key=home_key, away_key=away_key, kickoff=kickoff)
        self.helper.seed_candidate(fixture)
        return fixture

    def _admit_fixture(self, *, kickoff_in_days: int = 10, event_id: str | None = None):
        fixture = self._plan_fixture(kickoff_in_days=kickoff_in_days, event_id=event_id)
        result = self.helper.admit(fixture)
        if result["fixtures"][0]["admitted"] is not True:
            raise AssertionError(f"Synthetic v2 admission failed: {result!r}")
        identity = (fixture["club_slug"], fixture["roboticket_event_id"])
        admission_id, ticket_event_id, known_at = self.db.execute("""
          select id,ticket_event_id,known_at from private.roboticket_admission_receipts_v2
          where club_slug=%s and external_event_id=%s
        """, identity).fetchone()
        event_id_db = self.db.execute(
            "select external_event_id from public.ticket_events where id=%s", (ticket_event_id,)
        ).fetchone()[0]
        kickoff_at = _instant(fixture["plan_evidence"]["kickoff_at"])
        return {
            "fixture": fixture, "admission_id": admission_id,
            "ticket_event_id": ticket_event_id, "known_at": known_at,
            "external_event_id": int(event_id_db), "kickoff_at": kickoff_at,
        }

    def _register(self, *admissions):
        return self._rpc("register_rolling72_mvp_research_v1",
                         [a["admission_id"] for a in admissions])

    def _insert_bundle(self, admission, *, available: int, captured_at=None,
                       sectors: list[tuple[int, str, int]] | None = None,
                       area_ticket_event_id=None, inventory_event_id=None,
                       snapshot_source="roboticket", snapshot_event_id=None,
                       snapshot_ticket_event_id=None, snapshot_kickoff=None,
                       snapshot_date=None, source_children="roboticket",
                       insert_children=True, sector_count_override=None):
        """Write a synthetic source bundle; commit before calling capture."""
        if sectors is None:
            sectors = [(51001, "North", available)]
        captured_at = captured_at or self.db.execute("select clock_timestamp()").fetchone()[0]
        snapshot_event_id = admission["external_event_id"] if snapshot_event_id is None else snapshot_event_id
        snapshot_ticket_event_id = admission["ticket_event_id"] if snapshot_ticket_event_id is None else snapshot_ticket_event_id
        snapshot_kickoff = admission["kickoff_at"] if snapshot_kickoff is None else snapshot_kickoff
        snapshot_date = admission["kickoff_at"].astimezone(ZoneInfo("Europe/Warsaw")).date() if snapshot_date is None else snapshot_date
        sector_count = len(sectors) if sector_count_override is None else sector_count_override
        snapshot_id = self.db.execute("""
          insert into public.snapshots(ticket_event_id,event_id,source,captured_at,
            event_match_date_at_capture,event_kickoff_at_capture,available_total,sector_count)
          values(%s,%s,%s,%s,%s,%s,%s,%s) returning id
        """, (snapshot_ticket_event_id, snapshot_event_id, snapshot_source, captured_at,
              snapshot_date, snapshot_kickoff, available, sector_count)).fetchone()[0]
        for idx, (sector_id, sector_name, sector_available) in enumerate(sectors, 1) if insert_children else ():
            self.db.execute("""
              insert into public.sector_price_area_observations_v1
                (ticket_event_id,snapshot_id,captured_at,sector,sector_source_id,
                 price_area_id,price_area_name,available,source)
              values(%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (area_ticket_event_id or admission["ticket_event_id"], snapshot_id,
                  captured_at, sector_name, sector_id, idx, f"{sector_name} Main",
                  sector_available, source_children))
            self.db.execute("""
              insert into public.sector_inventory(snapshot_id,event_id,sector,available)
              values(%s,%s,%s,%s)
            """, (snapshot_id,
                  admission["external_event_id"] if inventory_event_id is None else inventory_event_id,
                  sector_name, sector_available))
        return snapshot_id

    def _insert_children(self, admission, snapshot_id, *, captured_at, sectors,
                         area_ticket_event_id=None, inventory_event_id=None,
                         source_children="roboticket"):
        for idx, (sector_id, sector_name, sector_available) in enumerate(sectors, 1):
            self.db.execute("""
              insert into public.sector_price_area_observations_v1
                (ticket_event_id,snapshot_id,captured_at,sector,sector_source_id,
                 price_area_id,price_area_name,available,source)
              values(%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (area_ticket_event_id or admission["ticket_event_id"], snapshot_id,
                  captured_at, sector_name, sector_id, idx, f"{sector_name} Main",
                  sector_available, source_children))
            self.db.execute("""
              insert into public.sector_inventory(snapshot_id,event_id,sector,available)
              values(%s,%s,%s,%s)
            """, (snapshot_id,
                  admission["external_event_id"] if inventory_event_id is None else inventory_event_id,
                  sector_name, sector_available))

    def _capture(self, limit: int = 25):
        return self._rpc("capture_rolling72_mvp_research_v1", limit)

    def _table_rows(self, table: str, ticket_event_id: int):
        rows = self.db.execute(
            f"select to_jsonb(x) from private.{table} x where ticket_event_id=%s order by id",
            (ticket_event_id,),
        ).fetchall()
        return [row[0] for row in rows]

    def _manifest_activate(self):
        return self._rpc("activate_rolling72_mvp_research_v1", self.manifest_text, self.manifest_sha)

    def test_activation_and_only_service_rpc_write_access(self):
        activation = self._manifest_activate()
        self.assertTrue(activation)
        function_rows = self.db.execute("""
          select p.proname,p.prosecdef,coalesce(p.proconfig,'{}')
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where n.nspname='public' and p.proname in (
            'activate_rolling72_mvp_research_v1',
            'register_rolling72_mvp_research_v1',
            'capture_rolling72_mvp_research_v1',
            'get_rolling72_mvp_research_v1_status')
        """).fetchall()
        self.assertEqual({row[0] for row in function_rows}, {
            "activate_rolling72_mvp_research_v1", "register_rolling72_mvp_research_v1",
            "capture_rolling72_mvp_research_v1", "get_rolling72_mvp_research_v1_status"})
        for _, security_definer, settings in function_rows:
            self.assertTrue(security_definer)
            self.assertIn("search_path=", " ".join(settings))
        private_tables = self.db.execute("""
          select tablename from pg_tables where schemaname='private'
          and tablename like 'rolling72_mvp_research_v1_%'
        """).fetchall()
        self.assertGreaterEqual(len(private_tables), 6)
        for (table,) in private_tables:
            for role in ("anon", "authenticated", "service_role"):
                self.assertFalse(self.db.execute(
                    "select has_table_privilege(%s,%s,'select,insert,update,delete')",
                    (role, f"private.{table}"),
                ).fetchone()[0], f"unexpected direct table privilege {role}.{table}")
            self.assertTrue(self.db.execute(
                "select relrowsecurity from pg_class where oid=%s::regclass",
                (f"private.{table}",),
            ).fetchone()[0])
        for role in ("anon", "authenticated"):
            self.db.execute(f"set role {role}")
            try:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    self.db.execute("select public.capture_rolling72_mvp_research_v1(1)")
            finally:
                self.db.execute("reset role")

    def test_committed_admission_source_zero_no_prior_and_real_candidate_clocks(self):
        issue_until = self.db.execute(
            "select clock_timestamp()+interval '60 days'"
        ).fetchone()[0]
        self.manifest["issue_until"] = issue_until.isoformat()
        self.manifest["scoring_until"] = (issue_until + timedelta(hours=78)).isoformat()
        self.manifest_text = json.dumps(self.manifest, separators=(",", ":"), sort_keys=True)
        self.manifest_sha = hashlib.sha256(self.manifest_text.encode()).hexdigest()
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=55)
        registered = self._register(admission)
        self.assertEqual(registered["results"][0]["status"], "REGISTERED")
        snapshot_id = self._insert_bundle(admission, available=0)
        self.db.commit()  # Source writer and capture are separate transactions.
        captured = self._capture()
        result = next(row for row in captured["results"] if row.get("snapshot_id") == snapshot_id)
        self.assertEqual(result["status"], "READY")
        self.assertNotEqual(admission["ticket_event_id"], admission["external_event_id"])
        seal_rows = self._table_rows("rolling72_mvp_research_v1_seals", admission["ticket_event_id"])
        self.assertEqual(len(seal_rows), 1)
        seal = seal_rows[0]
        self.assertEqual(seal["snapshot_id"], snapshot_id)
        self.assertEqual(seal["ticket_event_id"], admission["ticket_event_id"])
        self.assertEqual(seal["available_total"], 0)
        self.assertEqual(seal["prior_status"], "NO_PRIOR")
        self.assertIsNone(seal["total_delta"])
        self.assertIsNone(seal["prior_seal_id"])
        self.assertEqual(seal["gap_count"], 0)
        self.assertLessEqual(_instant(seal["read_started_at"]), _instant(seal["read_completed_at"]))
        self.assertLessEqual(_instant(seal["read_completed_at"]), _instant(seal["known_at"]))
        self.assertLessEqual(admission["known_at"], _instant(seal["read_started_at"]))
        self.assertLessEqual(_instant(seal["captured_at"]), _instant(seal["known_at"]))
        candidates = self._table_rows("rolling72_mvp_research_v1_candidates", admission["ticket_event_id"])
        self.assertEqual(sorted(row["horizon_hours"] for row in candidates), [24, 48, 72])
        for candidate in candidates:
            self.assertEqual(_instant(candidate["observation_known_at"]), _instant(seal["known_at"]))
            self.assertEqual(_instant(candidate["provisional_target_at"]),
                             _instant(seal["known_at"]) + timedelta(hours=candidate["horizon_hours"]))
            self.assertIn(candidate["status"], {"SOURCE_ELIGIBLE", "OUTSIDE_KICKOFF"})

    def test_same_snapshot_retry_changes_attempt_binding_not_seal_or_candidates(self):
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=15)
        self._register(admission)
        snapshot_id = self._insert_bundle(admission, available=17)
        self.db.commit()
        first = self._capture()
        first_seal = self._table_rows("rolling72_mvp_research_v1_seals", admission["ticket_event_id"])[0]
        first_candidates = self._table_rows("rolling72_mvp_research_v1_candidates", admission["ticket_event_id"])
        first_attempt = next(row for row in self._table_rows(
            "rolling72_mvp_research_v1_attempts", admission["ticket_event_id"]
        ) if row["id"] == first_seal["attempt_id"])
        second = self._capture()
        attempts = self._table_rows("rolling72_mvp_research_v1_attempts", admission["ticket_event_id"])
        self.assertGreaterEqual(len(attempts), 2)
        self.assertEqual(attempts[-1]["status"], "NO_NEW_SOURCE")
        self.assertEqual(attempts[-1]["source_content_sha256"], first_seal["source_content_sha256"])
        self.assertNotEqual(attempts[-1]["attempt_binding_sha256"], first_attempt["attempt_binding_sha256"])
        self.assertEqual(self._table_rows("rolling72_mvp_research_v1_seals", admission["ticket_event_id"]), [first_seal])
        self.assertEqual(self._table_rows("rolling72_mvp_research_v1_candidates", admission["ticket_event_id"]), first_candidates)
        self.assertEqual(first_seal["snapshot_id"], snapshot_id)

    def test_registration_refuses_current_transaction_and_savepoint_admissions(self):
        self._manifest_activate()
        for savepoint in (False, True):
            fixture = self._plan_fixture(kickoff_in_days=12)
            self.db.execute("begin")
            if savepoint:
                self.db.execute("savepoint admission_child")
            admitted = self.helper.admit(fixture)
            if savepoint:
                self.db.execute("release savepoint admission_child")
            receipt_id = admitted["fixtures"][0]["receipt_id"]
            rejected = self._rpc("register_rolling72_mvp_research_v1", [receipt_id])
            self.assertEqual(rejected["results"][0]["status"], "REJECTED")
            self.assertEqual(rejected["results"][0]["reason"], "UNCOMMITTED_ADMISSION")
            self.db.execute("rollback")
            committed = self.helper.admit(fixture)
            self.assertTrue(committed["fixtures"][0]["admitted"])
            committed_id = committed["fixtures"][0]["receipt_id"]
            registration = self._register({"admission_id": committed_id})
            self.assertEqual(registration["results"][0]["status"], "REGISTERED")

    def test_capture_refuses_source_rows_written_in_its_transaction_then_accepts_after_commit(self):
        self._manifest_activate()
        for savepoint in (False, True):
            admission = self._admit_fixture(kickoff_in_days=14)
            self._register(admission)
            self.db.execute("begin")
            if savepoint:
                self.db.execute("savepoint source_child")
            snapshot_id = self._insert_bundle(admission, available=4)
            if savepoint:
                self.db.execute("release savepoint source_child")
            same_transaction = self._capture()
            self.db.execute("commit")
            rejected = next(row for row in same_transaction["results"]
                            if row.get("snapshot_id") == snapshot_id)
            self.assertNotEqual(rejected["status"], "READY")
            self.assertTrue(rejected["reason"])
            after_commit = self._capture()
            accepted = next(row for row in after_commit["results"]
                            if row.get("snapshot_id") == snapshot_id)
            self.assertEqual(accepted["status"], "READY")
            seals = self._table_rows("rolling72_mvp_research_v1_seals", admission["ticket_event_id"])
            self.assertEqual(len(seals), 1)
            attempts = self._table_rows("rolling72_mvp_research_v1_attempts", admission["ticket_event_id"])
            self.assertGreaterEqual(len(attempts), 2)

    def test_wrong_external_inventory_id_is_rejected_without_contaminating_valid_fixture(self):
        self._manifest_activate()
        valid = self._admit_fixture(kickoff_in_days=12)
        invalid = self._admit_fixture(kickoff_in_days=13)
        self._register(valid, invalid)
        good_snapshot = self._insert_bundle(valid, available=8)
        bad_snapshot = self._insert_bundle(
            invalid, available=9, inventory_event_id=invalid["ticket_event_id"]
        )
        self.db.commit()
        captured = self._capture()
        results = {row.get("snapshot_id"): row for row in captured["results"]}
        self.assertEqual(results[good_snapshot]["status"], "READY")
        self.assertNotEqual(results[bad_snapshot]["status"], "READY")
        self.assertTrue(results[bad_snapshot]["reason"])
        self.assertEqual(len(self._table_rows(
            "rolling72_mvp_research_v1_seals", valid["ticket_event_id"])), 1)
        self.assertEqual(self._table_rows(
            "rolling72_mvp_research_v1_seals", invalid["ticket_event_id"]), [])
        self.assertEqual(self._table_rows(
            "rolling72_mvp_research_v1_candidates", invalid["ticket_event_id"]), [])

    def test_partial_children_retry_same_header_then_ready_mutation_is_blocked(self):
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=18)
        self._register(admission)
        snapshot_id = self._insert_bundle(
            admission, available=10, sectors=[(71001, "North", 10)],
            insert_children=False, sector_count_override=1,
        )
        first = self._capture()
        first_result = next(row for row in first["results"] if row.get("snapshot_id") == snapshot_id)
        self.assertEqual(first_result["status"], "INVALID_SOURCE")
        self.assertEqual(first_result["reason"], "MISSING_CHILD_ROWS")
        captured_at = self.db.execute(
            "select captured_at from public.snapshots where id=%s", (snapshot_id,)
        ).fetchone()[0]
        self._insert_children(admission, snapshot_id, captured_at=captured_at,
                              sectors=[(71001, "North", 10)])
        self.db.commit()
        recovered = self._capture()
        recovered_result = next(row for row in recovered["results"]
                                if row.get("snapshot_id") == snapshot_id)
        self.assertEqual(recovered_result["status"], "READY")
        original = self._table_rows("rolling72_mvp_research_v1_seals", admission["ticket_event_id"])[0]
        recomputed_header = self.db.execute("""
          select encode(sha256(convert_to(to_jsonb(s)::text,'UTF8')),'hex')
          from public.snapshots s where s.id=%s
        """, (snapshot_id,)).fetchone()[0]
        self.assertEqual(original["snapshot_sha256"], recomputed_header)
        self.db.execute("""
          update public.sector_price_area_observations_v1 set available=9 where snapshot_id=%s
        """, (snapshot_id,))
        mutation = self._capture()
        mutation_result = next(row for row in mutation["results"]
                               if row.get("snapshot_id") == snapshot_id)
        self.assertEqual(mutation_result["status"], "INVALID_SOURCE")
        self.assertEqual(mutation_result["reason"], "SOURCE_ROW_MUTATED")
        self.assertEqual(self._table_rows("rolling72_mvp_research_v1_seals",
                                          admission["ticket_event_id"]), [original])
        self.assertEqual(len(self._table_rows("rolling72_mvp_research_v1_candidates",
                                             admission["ticket_event_id"])), 3)

    def test_membership_swap_decomposition_and_unsealed_intervening_gap(self):
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=20)
        self._register(admission)
        first_time = self.db.execute("select clock_timestamp()").fetchone()[0]
        first_id = self._insert_bundle(
            admission, available=12, captured_at=first_time,
            sectors=[(72001, "North", 6), (72002, "South", 6)],
        )
        first = self._capture()
        self.assertEqual(next(row for row in first["results"]
                             if row.get("snapshot_id") == first_id)["status"], "READY")
        gap_time = self.db.execute("select clock_timestamp()").fetchone()[0]
        self.assertGreater(gap_time, first_time)
        gap_id = self._insert_bundle(
            admission, available=8, captured_at=gap_time,
            sectors=[(72002, "South", 8)], insert_children=False, sector_count_override=1,
        )
        gap = self._capture()
        self.assertEqual(next(row for row in gap["results"]
                             if row.get("snapshot_id") == gap_id)["status"], "INVALID_SOURCE")
        final_id = self._insert_bundle(
            admission, available=13,
            sectors=[(72001, "North", 6), (72003, "East", 7)],
        )
        final = self._capture()
        final_result = next(row for row in final["results"]
                            if row.get("snapshot_id") == final_id)
        self.assertEqual(final_result["status"], "READY")
        seal = self._table_rows("rolling72_mvp_research_v1_seals", admission["ticket_event_id"])[-1]
        self.assertEqual(seal["prior_status"], "READY_PRIOR")
        self.assertEqual(seal["transition_status"], "GAPPED")
        self.assertEqual(seal["gap_count"], 1)
        self.assertEqual(seal["total_delta"], 1)
        self.assertEqual(seal["total_delta"],
                         seal["common_sector_delta"] + seal["added_available"] - seal["removed_available"])
        self.assertEqual(seal["added_available"], 7)
        self.assertEqual(seal["removed_available"], 6)
        self.assertEqual(seal["added_sector_count"], 1)
        self.assertEqual(seal["removed_sector_count"], 1)
        self.assertEqual(seal["price_area_membership_change_count"], 2)

    def test_equal_capture_timestamp_uses_snapshot_id_without_inventing_rate(self):
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=20)
        self._register(admission)
        captured_at = self.db.execute("select clock_timestamp()").fetchone()[0]
        sectors = [(73001, "North", 5), (73002, "South", 5)]
        first_id = self._insert_bundle(admission, available=10, captured_at=captured_at,
                                       sectors=sectors)
        second_id = self._insert_bundle(admission, available=12, captured_at=captured_at,
                                        sectors=[(73001, "North", 6), (73002, "South", 6)])
        self.assertLess(first_id, second_id)
        first_result = self._capture(1)["results"][0]
        self.assertEqual(first_result["snapshot_id"], first_id)
        self.assertEqual(first_result["status"], "READY")
        second_result = self._capture(1)["results"][0]
        self.assertEqual(second_result["snapshot_id"], second_id)
        self.assertEqual(second_result["status"], "READY")
        seals = self._table_rows("rolling72_mvp_research_v1_seals", admission["ticket_event_id"])
        self.assertEqual(len(seals), 2)
        first, second = seals
        self.assertEqual(second["prior_seal_id"], first["id"])
        self.assertEqual(second["elapsed_capture_seconds"], 0)
        self.assertEqual(second["total_delta"], 2)
        self.assertEqual(second["transition"]["measurement_order_status"], "TIED_CAPTURE_TIME")
        self.assertEqual(second["transition"]["rate_status"], "UNAVAILABLE_ZERO_ELAPSED")
        self.assertGreater(_instant(second["transition"]["transition_known_at"]),
                           _instant(second["known_at"]))

    def test_captured_clock_may_fall_inside_read_but_not_after_completion(self):
        self._manifest_activate()
        first_admission = self._admit_fixture(kickoff_in_days=16)
        self._register(first_admission)
        real_name = "rolling72_mvp_research_v1_committed_real_for_test"
        self.db.execute(f"""
          alter function private.rolling72_mvp_research_v1_committed(xid,pg_snapshot)
          rename to {real_name}
        """)
        try:
            self.db.execute(f"""
              create function private.rolling72_mvp_research_v1_committed(x xid,snap pg_snapshot)
              returns boolean language plpgsql volatile security definer set search_path='' as $$
              begin
                perform pg_catalog.pg_sleep(0.05);
                return private.{real_name}(x,snap);
              end $$
            """)
            self.db.execute("""
              revoke all on function private.rolling72_mvp_research_v1_committed(xid,pg_snapshot)
              from public,anon,authenticated,service_role
            """)
            between_clock = self.db.execute(
                "select clock_timestamp()+interval '50 milliseconds'"
            ).fetchone()[0]
            between_id = self._insert_bundle(first_admission, available=4, captured_at=between_clock)
            inside = self._capture(1)["results"][0]
            self.assertEqual(inside["snapshot_id"], between_id)
            self.assertEqual(inside["status"], "READY")
            first_seal = self._table_rows(
                "rolling72_mvp_research_v1_seals", first_admission["ticket_event_id"]
            )[0]
            self.assertLess(_instant(first_seal["read_started_at"]), between_clock)
            self.assertLessEqual(between_clock, _instant(first_seal["read_completed_at"]))
            self.assertLessEqual(_instant(first_seal["read_completed_at"]), _instant(first_seal["known_at"]))
            self.assertLessEqual(between_clock, _instant(first_seal["known_at"]))

            second_admission = self._admit_fixture(kickoff_in_days=17)
            self._register(second_admission)
            beyond_clock = self.db.execute(
                "select clock_timestamp()+interval '5 seconds'"
            ).fetchone()[0]
            beyond_id = self._insert_bundle(second_admission, available=5, captured_at=beyond_clock)
            beyond = self._capture(1)["results"][0]
            self.assertEqual(beyond["snapshot_id"], beyond_id)
            self.assertEqual(beyond["status"], "INVALID_SOURCE")
            self.assertEqual(beyond["reason"], "SOURCE_CLOCK")
            self.assertEqual(self._table_rows(
                "rolling72_mvp_research_v1_seals", second_admission["ticket_event_id"]), [])
        finally:
            self.db.execute("""
              drop function if exists private.rolling72_mvp_research_v1_committed(xid,pg_snapshot) cascade
            """)
            self.db.execute(f"""
              alter function private.{real_name}(xid,pg_snapshot)
              rename to rolling72_mvp_research_v1_committed
            """)

    def test_external_uncommitted_source_is_invisible_until_writer_commit(self):
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=17)
        self._register(admission)
        writer = psycopg.connect(self.dsn, autocommit=True)
        original_db = self.db
        try:
            writer.execute("begin")
            self.db = writer
            snapshot_id = self._insert_bundle(admission, available=3)
            self.db = original_db
            before_commit = self._capture()
            missing = next(row for row in before_commit["results"]
                           if row.get("ticket_event_id") == admission["ticket_event_id"])
            self.assertEqual(missing["status"], "MISSING_SOURCE")
            self.assertIsNone(missing["snapshot_id"])
            writer.execute("commit")
            after_commit = self._capture()
            ready = next(row for row in after_commit["results"]
                         if row.get("snapshot_id") == snapshot_id)
            self.assertEqual(ready["status"], "READY")
        finally:
            self.db = original_db
            if writer.info.transaction_status != psycopg.pq.TransactionStatus.IDLE:
                writer.execute("rollback")
            writer.close()

    def test_fifo_limit_stale_missing_and_no_new_are_separate_outcomes(self):
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=17)
        self._register(admission)
        no_source = self._capture(1)
        missing = no_source["results"][0]
        self.assertEqual(missing["status"], "MISSING_SOURCE")
        self.assertIsNone(missing["snapshot_id"])
        self.db.execute("alter table private.rolling72_mvp_research_v1_lane disable trigger all")
        try:
            self.db.execute("""
              update private.rolling72_mvp_research_v1_lane
              set activated_at=clock_timestamp()-interval '2 hours'
            """)
        finally:
            self.db.execute("alter table private.rolling72_mvp_research_v1_lane enable trigger all")
        stale_time = self.db.execute("select clock_timestamp()-interval '70 minutes'").fetchone()[0]
        stale_id = self._insert_bundle(admission, available=7, captured_at=stale_time)
        fresh_id = self._insert_bundle(admission, available=8)
        stale = self._capture(1)["results"][0]
        self.assertEqual(stale["snapshot_id"], stale_id)
        self.assertEqual(stale["status"], "SKIPPED_STALE")
        fresh = self._capture(1)["results"][0]
        self.assertEqual(fresh["snapshot_id"], fresh_id)
        self.assertEqual(fresh["status"], "READY")
        no_new = self._capture(1)["results"][0]
        self.assertEqual(no_new["status"], "NO_NEW_SOURCE")
        self.assertEqual(no_new["seal_id"], fresh["seal_id"])

    def test_populated_ledgers_reject_update_delete_and_truncate(self):
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=17)
        self._register(admission)
        self._insert_bundle(admission, available=5)
        self._capture()
        cases = (
            ("lane", "lane_id", "rolling72-mvp-research-v1", "manifest_text=manifest_text"),
            ("registry", "ticket_event_id", admission["ticket_event_id"], "binding=binding"),
            ("registration_attempts", "id", None, "reason=reason"),
            ("runs", "id", None, "status=status"),
            ("attempts", "id", None, "reason=reason"),
            ("seals", "id", None, "source_payload=source_payload"),
            ("candidates", "id", None, "status=status"),
        )
        for suffix, key, value, assignment in cases:
            table = f"rolling72_mvp_research_v1_{suffix}"
            if value is None:
                value = self.db.execute(
                    f"select {key} from private.{table} order by {key} limit 1"
                ).fetchone()[0]
            before = self.db.execute(
                f"select to_jsonb(x) from private.{table} x where {key}=%s", (value,)
            ).fetchone()[0]
            with self.assertRaises(psycopg.Error):
                self.db.execute(f"update private.{table} set {assignment} where {key}=%s", (value,))
            with self.assertRaises(psycopg.Error):
                self.db.execute(f"delete from private.{table} where {key}=%s", (value,))
            with self.assertRaises(psycopg.Error):
                self.db.execute(f"truncate private.{table}")
            after = self.db.execute(
                f"select to_jsonb(x) from private.{table} x where {key}=%s", (value,)
            ).fetchone()[0]
            self.assertEqual(after, before, table)

    def test_concurrent_exact_registration_retry_is_idempotent(self):
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=16)
        gate = threading.Barrier(2)

        def register_once():
            with psycopg.connect(self.dsn, autocommit=True) as connection:
                connection.execute("set role service_role")
                gate.wait(timeout=5)
                return connection.execute(
                    "select public.register_rolling72_mvp_research_v1(%s)",
                    ([admission["admission_id"]],),
                ).fetchone()[0]

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: register_once(), range(2)))
        statuses = [result["results"][0]["status"] for result in results]
        self.assertCountEqual(statuses, ["REGISTERED", "IDEMPOTENT"])
        registry = self.db.execute("""
          select count(*) from private.rolling72_mvp_research_v1_registry where ticket_event_id=%s
        """, (admission["ticket_event_id"],)).fetchone()[0]
        attempts = self.db.execute("""
          select count(*) from private.rolling72_mvp_research_v1_registration_attempts
          where admission_receipt_id=%s
        """, (admission["admission_id"],)).fetchone()[0]
        self.assertEqual(registry, 1)
        self.assertEqual(attempts, 2)

    def test_registration_and_capture_boundaries_reject_bad_inputs(self):
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=11)
        with self.assertRaises(psycopg.Error):
            self._rpc("register_rolling72_mvp_research_v1",
                      [admission["admission_id"], admission["admission_id"]])
        with self.assertRaises(psycopg.Error):
            self._rpc("register_rolling72_mvp_research_v1", [])
        with self.assertRaises(psycopg.Error):
            self._capture(26)
        self.assertEqual(self._register(admission)["results"][0]["status"], "REGISTERED")

    def test_manifest_deadline_and_frozen_identity(self):
        invalid = deepcopy(self.manifest)
        invalid["scoring_until"] = (
            self.db.execute("select (%s::timestamptz + interval '77 hours')", (invalid["issue_until"],))
            .fetchone()[0].isoformat()
        )
        encoded = json.dumps(invalid, separators=(",", ":"), sort_keys=True)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        with self.assertRaises(psycopg.Error):
            self._rpc("activate_rolling72_mvp_research_v1", encoded, digest)
        self._manifest_activate()
        conflicting = deepcopy(self.manifest)
        conflicting["max_fixtures"] = 99
        encoded = json.dumps(conflicting, separators=(",", ":"), sort_keys=True)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        with self.assertRaises(psycopg.Error):
            self._rpc("activate_rolling72_mvp_research_v1", encoded, digest)

    def test_registry_cap_and_admission_identity_tamper_fail_closed(self):
        self.manifest["max_fixtures"] = 1
        self.manifest_text = json.dumps(self.manifest, separators=(",", ":"), sort_keys=True)
        self.manifest_sha = hashlib.sha256(self.manifest_text.encode()).hexdigest()
        self._manifest_activate()
        admitted = self._admit_fixture(kickoff_in_days=12)
        accepted = self._register(admitted)
        self.assertEqual(accepted["results"][0]["status"], "REGISTERED")
        overflow = self._admit_fixture(kickoff_in_days=13)
        rejected = self._register(overflow)
        self.assertEqual(rejected["results"][0]["status"], "REJECTED")
        self.assertEqual(rejected["results"][0]["reason"], "REGISTRY_CAP")

        # Use a fresh lane reset with an admitted receipt whose immutable
        # evidence is deliberately altered by the disposable database owner.
        self._reset_new_lane()
        self.db.execute(MIGRATION.read_text())
        self.manifest, self.manifest_text, self.manifest_sha = self._activate()
        self._manifest_activate()
        tampered = self._admit_fixture(kickoff_in_days=14)
        self.db.execute("alter table private.roboticket_admission_receipts_v2 disable trigger all")
        try:
            self.db.execute("""
              update private.roboticket_admission_receipts_v2
              set evidence_payload=jsonb_set(evidence_payload,'{plan_evidence,canonical_home_club_key}',to_jsonb('changed'::text))
              where id=%s
            """, (tampered["admission_id"],))
        finally:
            self.db.execute("alter table private.roboticket_admission_receipts_v2 enable trigger all")
        invalid = self._register(tampered)
        self.assertEqual(invalid["results"][0]["status"], "REJECTED")
        self.assertEqual(invalid["results"][0]["reason"], "ADMISSION_EVIDENCE_MISMATCH")

    def test_issue_cutoff_creates_label_only_seal_and_no_candidates(self):
        issue_until = self.db.execute(
            "select clock_timestamp()+interval '10 seconds'"
        ).fetchone()[0]
        scoring_until = issue_until + timedelta(hours=78)
        self.manifest["issue_until"] = issue_until.isoformat()
        self.manifest["scoring_until"] = scoring_until.isoformat()
        self.manifest_text = json.dumps(self.manifest, separators=(",", ":"), sort_keys=True)
        self.manifest_sha = hashlib.sha256(self.manifest_text.encode()).hexdigest()
        self._manifest_activate()
        admission = self._admit_fixture(kickoff_in_days=12)
        self._register(admission)
        snapshot_id = self._insert_bundle(admission, available=6)
        remaining = self.db.execute(
            "select greatest(0,extract(epoch from %s::timestamptz-clock_timestamp()))",
            (issue_until,),
        ).fetchone()[0]
        time.sleep(float(remaining) + 0.1)
        captured = self._capture()
        result = next(row for row in captured["results"] if row.get("snapshot_id") == snapshot_id)
        self.assertEqual(result["status"], "READY")
        seal = self._table_rows("rolling72_mvp_research_v1_seals", admission["ticket_event_id"])[0]
        self.assertEqual(seal["phase"], "LABEL_ONLY")
        self.assertEqual(self._table_rows(
            "rolling72_mvp_research_v1_candidates", admission["ticket_event_id"]), [])

