"""Isolated PG16 regression suite for the exact-body PERS clock patch.

This suite composes the ten existing P0-4c regressions with two patch-specific
tests on a separate disposable DB. It never edits the base PERS SQL or tests.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import unittest
from urllib.parse import urlparse

import psycopg

ROOT = Path(__file__).resolve().parents[2]
PERSIST_TEST = ROOT / "tests/postgres/test_rolling72_mvp_persistence_v1.py"
PATCH_SQL = ROOT / "supabase/sql/rolling72_mvp_persistence_issue_clock_guard_v1.sql"
SPEC = importlib.util.spec_from_file_location("pers_clock_guard_persistence_helpers", PERSIST_TEST)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load isolated PERS regression helpers")
HELPERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPERS)
PersistenceFixture = HELPERS.Rolling72MvpPersistenceV1

ISSUER = "public.issue_rolling72_mvp_persistence_v1(integer)"
EXPECTED_BASE_BODY_SHA256 = "fa0c5cfd9449e3b1fd6af5178e7853f1ae857f8b60c422cacb28d8e05f713750"
EXPECTED_PATCH_BODY_SHA256 = "f7bc89911b5eddd3d44dd023c3e9af940ddb5ff9a6dcb65db673689fadad4874"
EXPECTED_PATCH_SQL_SHA256 = "53d4391f4486fd9f9c897a9db3d2da15bfc371ba0b4645ffb05f392d1d1e9d41"


class Rolling72MvpPersistenceIssueClockGuardV1(PersistenceFixture):
    """Run the complete persistence contract plus exact-clock guard checks."""

    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("ROLLING72_MVP_ISSUE_CLOCK_GUARD_TEST_DSN", "")
        target = urlparse(dsn)
        if (target.scheme not in {"postgres", "postgresql"}
                or target.hostname not in {"127.0.0.1", "localhost"}
                or target.port != 55440
                or target.path != "/rolling72_mvp_issue_clock_guard_test"):
            raise RuntimeError(
                "Only 127.0.0.1:55440/rolling72_mvp_issue_clock_guard_test is allowed"
            )
        cls.dsn = dsn
        cls.db = psycopg.connect(dsn, autocommit=True)
        version = int(cls.db.execute("show server_version_num").fetchone()[0])
        identity = cls.db.execute("select current_database()").fetchone()[0]
        if not 160000 <= version < 170000 or identity != "rolling72_mvp_issue_clock_guard_test":
            cls.db.close()
            raise RuntimeError("Clock-guard tests require the dedicated PostgreSQL 16 database")
        cls._bootstrap_parent_schema()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    def setUp(self):
        super().setUp()
        if not PATCH_SQL.exists():
            self.fail(f"Missing separately versioned clock patch: {PATCH_SQL}")
        self.patch_text = PATCH_SQL.read_text(encoding="utf-8")
        self.patch_sha256 = hashlib.sha256(PATCH_SQL.read_bytes()).hexdigest()
        self.assertEqual(self.patch_sha256, EXPECTED_PATCH_SQL_SHA256)
        self.function_catalog_before = self._functions()
        self.base_body_sha256 = self._body_hash(ISSUER)
        self.assertEqual(self.base_body_sha256, EXPECTED_BASE_BODY_SHA256)
        self.issuer_security_before = self._issuer_security()
        self.db.execute(self.patch_text)
        self.patched_body_sha256 = self._body_hash(ISSUER)
        self.assertEqual(self.patched_body_sha256, EXPECTED_PATCH_BODY_SHA256)
        self.issuer_security_after = self._issuer_security()
        self.assertEqual(self.issuer_security_before, self.issuer_security_after)
        after = self._functions()
        for signature, body_hash in self.function_catalog_before.items():
            if signature != ISSUER:
                self.assertEqual(after.get(signature), body_hash,
                                 f"clock patch changed unrelated function {signature}")

    def _body_hash(self, signature):
        row = self.db.execute("""
          select encode(sha256(convert_to(p.prosrc,'UTF8')),'hex')
          from pg_proc p where p.oid=%s::regprocedure
        """, (signature,)).fetchone()
        return None if row is None else row[0]

    def _functions(self):
        rows = self.db.execute("""
          select p.oid::regprocedure::text,
           encode(sha256(convert_to(p.prosrc,'UTF8')),'hex')
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where n.nspname in('public','private') and p.proname like 'rolling72_mvp_%'
          order by p.oid::regprocedure::text
        """).fetchall()
        return dict(rows)

    def _issuer_security(self):
        return self.db.execute("""
          select p.prosecdef,p.proconfig,p.proacl,
           has_function_privilege('service_role',p.oid,'EXECUTE'),
           has_function_privilege('anon',p.oid,'EXECUTE'),
           has_function_privilege('authenticated',p.oid,'EXECUTE')
          from pg_proc p where p.oid=%s::regprocedure
        """, (ISSUER,)).fetchone()

    def test_guarded_patch_is_idempotent_fail_closed_and_acl_preserving(self):
        self.db.execute(self.patch_text)
        self.assertEqual(self._body_hash(ISSUER), EXPECTED_PATCH_BODY_SHA256)
        self.assertEqual(self._issuer_security(), self.issuer_security_before)
        self.assertTrue(self.issuer_security_after[0], "issuer must remain SECURITY DEFINER")
        config = self.issuer_security_after[1] or []
        self.assertIn('search_path=""', config)
        self.assertIn("TimeZone=UTC", config)
        self.assertTrue(self.issuer_security_after[3], "service_role must retain issuer execution")
        self.assertFalse(self.issuer_security_after[4], "anon must not gain issuer execution")
        self.assertFalse(self.issuer_security_after[5], "authenticated must not gain issuer execution")
        self.assertGreater(len(self.patch_sha256), 0)

        # Tamper only inside a rollback-only transaction. A mismatched body is
        # rejected before the patch can rewrite any function state.
        definition = self.db.execute("select pg_get_functiondef(%s::regprocedure)",
                                     (ISSUER,)).fetchone()[0]
        self.assertIn("pg_sleep(0.000001)", definition)
        self.db.execute("begin")
        try:
            self.db.execute(definition.replace("pg_sleep(0.000001)", "pg_sleep(0.000002)", 1))
            with self.assertRaises(psycopg.Error) as raised:
                self.db.execute(self.patch_text)
            self.assertIn("PERS_CLOCK_GUARD_UNEXPECTED_BODY", str(raised.exception))
        finally:
            self.db.execute("rollback")
        self.assertEqual(self._body_hash(ISSUER), EXPECTED_PATCH_BODY_SHA256)

        constraint = self.db.execute("""
          select string_agg(pg_get_constraintdef(c.oid),' ')
          from pg_constraint c
          where c.conrelid='private.rolling72_mvp_persistence_v1_issue_bundles'::regclass
            and c.contype='c'
        """).fetchone()[0]
        self.assertIn("calculation_completed_at < issued_at", constraint)

    def test_rapid_32_genuine_same_event_issues_keep_strict_real_clock_order(self):
        admission = self._admit_fixture(kickoff_in_days=20)
        self._register(admission)
        expected_values = []
        for index in range(32):
            value = 0 if index == 0 else index * 3
            snapshot = self._insert_bundle(admission, available=value)
            capture = self._capture()
            seal = self.db.execute("""
              select id,known_at,captured_at,read_completed_at
              from private.rolling72_mvp_research_v1_seals where snapshot_id=%s
            """, (snapshot,)).fetchone()
            self.assertIsNotNone(seal, f"source capture did not create genuine seal: {capture!r}")
            result = self._rpc("issue_rolling72_mvp_persistence_v1", 25)
            self.assertEqual(result["processed_bundles"], 1, result)
            bundle = self.db.execute("""
              select id,source_known_at,source_captured_at,source_read_completed_at,
               calculation_completed_at,read_completed_at,issued_at,source_age_seconds,
               input_available_total
              from private.rolling72_mvp_persistence_v1_issue_bundles where seal_id=%s
            """, (seal[0],)).fetchone()
            self.assertIsNotNone(bundle)
            (bundle_id, known_at, captured_at, source_read_done, calculated_at,
             read_done, issued_at, source_age, origin_value) = bundle
            self.assertGreaterEqual(issued_at, known_at)
            self.assertGreaterEqual(issued_at, source_read_done)
            self.assertGreater(issued_at, calculated_at)
            self.assertGreater(issued_at, read_done)
            self.assertGreaterEqual(source_age, 0)
            self.assertLessEqual(source_age, 3600)
            self.assertEqual(origin_value, value)
            if index == 0:
                self.assertEqual(value, 0)
                self.assertEqual(origin_value, 0)
            forecasts = self.db.execute("""
              select horizon_hours,target_at,status,prediction
              from private.rolling72_mvp_persistence_v1_predictions
              where bundle_id=%s order by horizon_hours
            """, (bundle_id,)).fetchall()
            self.assertEqual([row[0] for row in forecasts], [24,48,72])
            for horizon, target_at, status, prediction in forecasts:
                self.assertEqual(target_at, issued_at + __import__("datetime").timedelta(hours=horizon))
                if target_at < admission["kickoff_at"]:
                    self.assertEqual((status,prediction), ("ISSUED",value))
                else:
                    self.assertEqual((status,prediction), ("OUTSIDE_KICKOFF",None))
            expected_values.append(value)

        rows = self.db.execute("""
          select count(*),count(distinct b.seal_id),count(distinct p.horizon_hours),
           min(b.issued_at),max(b.issued_at),bool_and(b.calculation_completed_at<b.issued_at)
          from private.rolling72_mvp_persistence_v1_issue_bundles b
          join private.rolling72_mvp_persistence_v1_predictions p on p.bundle_id=b.id
          join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=b.ticket_event_id
          where b.ticket_event_id=%s
        """, (admission["ticket_event_id"],)).fetchone()
        self.assertEqual(rows[0],32*3)
        self.assertEqual(rows[1],32)
        self.assertEqual(rows[2],3)
        self.assertTrue(rows[5])
        self.assertGreater(rows[4],rows[3])
        self.assertEqual(expected_values[0],0)


# Keep the inherited PERS regressions but prevent unittest from discovering the
# imported base class as an independent suite in this module.
del PersistenceFixture


if __name__ == "__main__":
    unittest.main()
