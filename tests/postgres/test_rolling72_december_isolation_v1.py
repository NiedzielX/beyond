"""Same-database old/new lane isolation checks for generated December SQL.

Uses only the disposable loopback PostgreSQL 16 database named below. No hosted
calls, source API reads, or old test-class discovery are performed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from urllib.parse import urlparse

import psycopg

from ml.rolling72_december_bundle_v1 import generate_manifests, generate_sql

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LANE = "rolling72-december-source-v1"
PAIR_LANE = "rolling72-december-pair-v1"
SOURCE_PREFIX = "rolling72_december_source_v1"
PAIR_PREFIX = "rolling72_december_pair_v1"
OLD_SOURCE_SQL = ROOT / "supabase/sql/rolling72_mvp_research_v1.sql"
OLD_PAIR_SQL = ROOT / "supabase/sql/rolling72_mvp_paired_drift24_v1.sql"
SOURCE_FIXTURES = ROOT / "tests/postgres/test_rolling72_mvp_research_v1.py"
B_SQL_SHA256 = "c9621bb692ca7de38037a204a9ca204ed3be370657b9ab89dc3aa438575effb4"
LAD_V5_SQL_SHA256 = "c2a3071d7109b74040228fb6b4ee77a6524afccc7174550acb7fa362e9f7afd2"


def _load_source_fixtures():
    spec = importlib.util.spec_from_file_location("december_source_fixture_helpers", SOURCE_FIXTURES)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load source test bootstrap helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SourceFixtures = _load_source_fixtures()


def _future_deadlines(db, days: int = 10):
    now = db.execute("select clock_timestamp() at time zone 'UTC'").fetchone()[0]
    issue = now.replace(tzinfo=timezone.utc) + timedelta(days=days)
    score = issue + timedelta(hours=78)
    fmt = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return fmt(issue), fmt(score)


def _manifest_text(values):
    encoded = json.dumps(values, separators=(",", ":"), sort_keys=True)
    return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _activate(db, function_name, values):
    encoded, digest = _manifest_text(values)
    db.execute("set role service_role")
    try:
        result = db.execute(f"select public.{function_name}(%s,%s)", (encoded, digest)).fetchone()[0]
    finally:
        db.execute("reset role")
    return result, digest


def _all_function_hashes(db):
    rows = db.execute("""
      select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),
        encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex')
      from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname in ('public','private')
      order by 1,2,3
    """).fetchall()
    return {(schema, name, args): digest for schema, name, args, digest in rows}


def _manifest_old_source(db, sql_text, issue, score):
    values = {
        "lane_id": "rolling72-mvp-research-v1",
        "version": "rolling72-mvp-research-v1",
        "source_family": "roboticket/roboticket",
        "unit": "available_total_seats",
        "max_source_age_seconds": 3600,
        "max_batch": 25,
        "max_fixtures": 100,
        "issue_until": issue,
        "scoring_until": score,
        "sql_sha256": hashlib.sha256(sql_text.encode("utf-8")).hexdigest(),
    }
    return values


def _manifest_pair(db, lane_id, source_lane_id, source_row, pair_sql, issue, score):
    values = {
        "lane_id": lane_id,
        "version": lane_id,
        "source_lane_id": source_lane_id,
        "source_family": "roboticket/roboticket",
        "unit": "available_total_seats",
        "methods": ["PERS", "DRIFT24"],
        "horizons_hours": [24, 48, 72],
        "anchor_min_hours": 24,
        "anchor_max_hours": 30,
        "max_issue_latency_seconds": 90,
        "max_source_age_seconds": 3600,
        "max_target_age_seconds": 21600,
        "max_issue_batch": 25,
        "max_score_batch": 100,
        "max_fixtures": source_row[2],
        "source_manifest_sha256": source_row[0],
        "source_sql_sha256": source_row[1],
        "sql_sha256": hashlib.sha256(pair_sql.encode("utf-8")).hexdigest(),
        "issue_until": issue,
        "scoring_until": score,
        "b_sql_sha256": B_SQL_SHA256,
        "lad_v5_sql_sha256": LAD_V5_SQL_SHA256,
    }
    return values


class Rolling72DecemberIsolationV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("ROLLING72_DECEMBER_ISOLATION_TEST_DSN", "")
        target = urlparse(dsn)
        if (target.scheme not in {"postgres", "postgresql"}
                or target.hostname not in {"127.0.0.1", "localhost"}
                or target.port != 55440
                or target.path != "/rolling72_december_isolation_test"):
            raise RuntimeError(
                "Only 127.0.0.1:55440/rolling72_december_isolation_test is allowed"
            )
        cls.db = psycopg.connect(dsn, autocommit=True)
        identity = cls.db.execute("select current_database(),current_setting('server_version_num')").fetchone()
        if identity[0] != "rolling72_december_isolation_test" or not 160000 <= int(identity[1]) < 170000:
            cls.db.close()
            raise RuntimeError("Requires the dedicated PostgreSQL 16 December isolation database")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    def test_manifest_generation_rejects_a_short_scoring_window(self):
        with self.assertRaisesRegex(ValueError, "78 hours"):
            generate_manifests(ROOT, issue_until="2026-12-31T00:00:00Z",
                               scoring_until="2027-01-03T05:59:59Z", max_fixtures=100)

    def test_generated_lanes_install_activate_and_preserve_old_lane(self):
        self.db = type(self).db
        generated = generate_sql(ROOT)
        self.assertEqual(set(generated), {"source", "paired"})
        source_sql, pair_sql = generated["source"], generated["paired"]
        self.assertTrue(source_sql.strip())
        self.assertTrue(pair_sql.strip())

        # Reuse only the fixture helper's isolated parent-schema bootstrap; do not
        # run or discover any old lane test methods.
        SourceFixtures.Rolling72MvpResearchV1.db = self.db
        SourceFixtures.Rolling72MvpResearchV1._bootstrap_parent_schema()

        old_source_sql = OLD_SOURCE_SQL.read_text(encoding="utf-8")
        old_pair_sql = OLD_PAIR_SQL.read_text(encoding="utf-8")
        self.db.execute(old_source_sql)
        self.db.execute(old_pair_sql)
        issue_old, score_old = _future_deadlines(self.db, 5)
        old_source_manifest = _manifest_old_source(self.db, old_source_sql, issue_old, score_old)
        old_source_result, old_source_hash = _activate(
            self.db, "activate_rolling72_mvp_research_v1", old_source_manifest
        )
        self.assertTrue(old_source_result["activated"])
        old_source_row = self.db.execute("""
          select manifest_sha256,sql_sha256,max_fixtures,issue_until,scoring_until
          from private.rolling72_mvp_research_v1_lane
          where lane_id='rolling72-mvp-research-v1'
        """).fetchone()
        self.assertEqual(old_source_row[0], old_source_hash)
        old_pair_manifest = _manifest_pair(
            self.db, "rolling72-mvp-paired-drift24-v1", "rolling72-mvp-research-v1",
            old_source_row, old_pair_sql, issue_old, score_old,
        )
        old_pair_result, _ = _activate(
            self.db, "activate_rolling72_mvp_paired_drift24_v1", old_pair_manifest
        )
        self.assertTrue(old_pair_result["activated"])

        function_hashes_before_new = _all_function_hashes(self.db)
        self.db.execute(source_sql)
        self.db.execute(pair_sql)
        function_hashes_after_new = _all_function_hashes(self.db)
        for signature, digest in function_hashes_before_new.items():
            self.assertEqual(function_hashes_after_new.get(signature), digest,
                             f"generated SQL changed old/public function {signature}")

        issue_new, score_new = _future_deadlines(self.db, 10)
        manifests = generate_manifests(ROOT, issue_until=issue_new, scoring_until=score_new,
                                       max_fixtures=100)
        source_values = json.loads(manifests["source"])
        source_result, source_manifest_hash = _activate(
            self.db, "activate_rolling72_december_source_v1", source_values
        )
        self.assertTrue(source_result["activated"])
        source_row = self.db.execute(f"""
          select manifest_sha256,sql_sha256,max_fixtures,issue_until,scoring_until
          from private.{SOURCE_PREFIX}_lane where lane_id=%s
        """, (SOURCE_LANE,)).fetchone()
        self.assertEqual(source_row[0], source_manifest_hash)
        pair_values = json.loads(manifests["paired"])
        self.assertEqual(pair_values["source_manifest_sha256"], source_manifest_hash)
        pair_result, _ = _activate(self.db, "activate_rolling72_december_pair_v1", pair_values)
        self.assertTrue(pair_result["activated"])

        for lane_row in (source_row, self.db.execute(f"""
          select manifest_sha256,sql_sha256,max_fixtures,issue_until,scoring_until
          from private.{PAIR_PREFIX}_lane where lane_id=%s
        """, (PAIR_LANE,)).fetchone()):
            self.assertGreaterEqual(lane_row[4] - lane_row[3], timedelta(hours=78))
        self.assertNotEqual(source_row[0], old_source_row[0])
        self.assertEqual(self.db.execute("""
          select manifest_sha256,issue_until,scoring_until
          from private.rolling72_mvp_research_v1_lane
          where lane_id='rolling72-mvp-research-v1'
        """).fetchone(), (old_source_row[0], old_source_row[3], old_source_row[4]))

        for prefix in (SOURCE_PREFIX, PAIR_PREFIX):
            table_rows = self.db.execute("""
              select c.relname,c.relrowsecurity,c.oid::regclass::text
              from pg_class c join pg_namespace n on n.oid=c.relnamespace
              where n.nspname='private' and c.relkind in ('r','p') and c.relname like %s
              order by c.relname
            """, (prefix + "_%",)).fetchall()
            self.assertTrue(table_rows, f"No private tables found for {prefix}")
            role_oids = {name: oid for name, oid in self.db.execute(
                "select rolname,oid from pg_roles where rolname in ('anon','authenticated','service_role')"
            ).fetchall()}
            for name, rls, regclass_name in table_rows:
                self.assertTrue(rls, f"RLS is not enabled on private.{name}")
                self.assertFalse(self.db.execute("""
                  select exists(
                    select 1 from pg_class c,
                      lateral aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) x
                    where c.oid=%s::regclass
                      and (x.grantee=0 or x.grantee=any(%s::oid[]))
                  )
                """, (regclass_name, list(role_oids.values()))).fetchone()[0],
                    f"Direct table grant found on private.{name}")
                for role in role_oids:
                    self.assertFalse(self.db.execute(
                        "select has_table_privilege(%s,%s,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')",
                        (role, f"private.{name}"),
                    ).fetchone()[0], f"{role} has direct table privileges on private.{name}")

        fixtures = SourceFixtures.Rolling72MvpResearchV1()
        fixtures.db = self.db
        helper_class = SourceFixtures._admission_helper_class()
        fixtures.helper = helper_class.__new__(helper_class)
        fixtures.helper.db = self.db
        receipt = fixtures._admit_fixture()
        fixtures._rpc("register_rolling72_december_source_v1", [receipt["admission_id"]])
        fixtures._insert_bundle(receipt, available=0)
        fixtures._rpc("capture_rolling72_december_source_v1", 25)
        fixtures._rpc("issue_rolling72_december_pair_v1", 25)
        self.assertEqual(self.db.execute("""
          select horizon_hours,count(*),min(prediction),max(prediction)
          from private.rolling72_december_pair_v1_predictions
          group by horizon_hours order by horizon_hours
        """).fetchall(), [(24,2,0,0),(48,2,0,0),(72,2,0,0)])
        self.assertEqual(self.db.execute("select count(*) from private.rolling72_mvp_research_v1_registry").fetchone()[0],0)
        self.assertEqual(self.db.execute("select count(*) from private.rolling72_mvp_paired_drift24_v1_predictions").fetchone()[0],0)


if __name__ == "__main__":
    unittest.main()
