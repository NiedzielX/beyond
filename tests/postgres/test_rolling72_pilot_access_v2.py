"""Isolated PostgreSQL 16 tests for the protected rolling72 pilot capability."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
import unittest
from urllib.parse import urlparse

import psycopg
from psycopg.errors import CheckViolation


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/sql/rolling72_pilot_access_v2.sql"
GRANT_TABLE = "private.rolling72_pilot_grants_v2"
AUTHORIZE = "public.authorize_rolling72_pilot_feed_v2"
AUTHORIZE_SIG = f"{AUTHORIZE}(text)"
ALLOWED_FIXTURES = [27049]
ALLOWED_LANES = ["rolling72-mvp-persistence-v1"]


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class Rolling72PilotAccessV2(unittest.TestCase):
    """Only the new grant table/RPC is installed; old rolling72 functions are sentinels."""

    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("ROLLING72_PILOT_ACCESS_V2_TEST_DSN", "")
        target = urlparse(dsn)
        if (target.scheme not in {"postgres", "postgresql"}
                or target.hostname != "127.0.0.1" or target.port != 55440
                or target.path != "/rolling72_pilot_access_v2_test"):
            raise RuntimeError("Only 127.0.0.1:55440/rolling72_pilot_access_v2_test is allowed")
        cls.db = psycopg.connect(dsn, autocommit=True)
        version = int(cls.db.execute("show server_version_num").fetchone()[0])
        dbname = cls.db.execute("select current_database()").fetchone()[0]
        if version < 160000 or version >= 170000 or dbname != "rolling72_pilot_access_v2_test":
            cls.db.close()
            raise RuntimeError("Pilot access tests require the dedicated PostgreSQL 16 database")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    def setUp(self):
        self.db.execute(f"drop function if exists {AUTHORIZE_SIG} cascade")
        self.db.execute(f"drop table if exists {GRANT_TABLE} cascade")
        self.db.execute("create schema if not exists private")
        self._ensure_role("anon")
        self._ensure_role("authenticated")
        self._ensure_role("service_role")
        self._create_old_function_sentinels()
        self.old_functions_before = self._old_function_state()
        if not MIGRATION.exists():
            raise RuntimeError(f"Missing migration under test: {MIGRATION}")
        self.db.execute(MIGRATION.read_text(encoding="utf-8"))

    def _ensure_role(self, name: str):
        exists = self.db.execute("select 1 from pg_roles where rolname=%s", (name,)).fetchone()
        if not exists:
            self.db.execute(f'create role "{name}" nologin')

    def _create_old_function_sentinels(self):
        # These ordinary, non-empty old function definitions make unchanged
        # hashes/count testable without importing or modifying frozen schemas.
        self.db.execute("""
          create or replace function public.get_rolling72_common_flow_e5_v1_status()
          returns jsonb language sql immutable as $$ select '{\"sentinel\":\"e5\"}'::jsonb $$
        """)
        self.db.execute("""
          create or replace function private.get_rolling72_forward_baselines_b_v1_status()
          returns jsonb language sql immutable as $$ select '{\"sentinel\":\"b\"}'::jsonb $$
        """)

    def _old_function_state(self):
        rows = self.db.execute("""
          select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),
                 md5(pg_get_functiondef(p.oid))
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where n.nspname in ('public','private')
            and p.proname like '%rolling72%'
            and p.proname <> 'authorize_rolling72_pilot_feed_v2'
          order by 1,2,3
        """).fetchall()
        return {(schema, name, args): digest for schema, name, args, digest in rows}

    def _insert_grant(self, raw_code: str, *, created_at=None, expires_at=None,
                      fixture_ids=None, lane_ids=None):
        created_at = created_at or datetime.now(timezone.utc)
        expires_at = expires_at or created_at + timedelta(days=1)
        return self.db.execute(f"""
          insert into {GRANT_TABLE}(token_sha256,created_at,expires_at,fixture_ids,lane_ids)
          values(%s,%s,%s,%s,%s) returning token_sha256
        """, (_sha(raw_code), created_at, expires_at,
              fixture_ids if fixture_ids is not None else ALLOWED_FIXTURES,
              lane_ids if lane_ids is not None else ALLOWED_LANES)).fetchone()[0]

    def _authorize_as_service(self, code_hash):
        self.db.execute("set role service_role")
        try:
            return self.db.execute(f"select {AUTHORIZE}(%s)", (code_hash,)).fetchone()[0]
        finally:
            self.db.execute("reset role")

    def _assert_old_function_state_unchanged(self):
        self.assertEqual(self._old_function_state(), self.old_functions_before)
        self.assertEqual(len(self.old_functions_before), 2)

    def test_grant_table_is_rls_protected_and_has_no_direct_role_grants(self):
        self.assertTrue(self.db.execute("""
          select relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace
          where n.nspname='private' and c.relname='rolling72_pilot_grants_v2'
        """).fetchone()[0])
        for role in ("anon", "authenticated", "service_role"):
            for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"):
                self.assertFalse(self.db.execute(
                    "select has_table_privilege(%s,%s,%s)", (role, GRANT_TABLE, privilege)
                ).fetchone()[0], f"{role} unexpectedly has {privilege} on grant table")
        columns = {r[0] for r in self.db.execute("""
          select column_name from information_schema.columns
          where table_schema='private' and table_name='rolling72_pilot_grants_v2'
        """).fetchall()}
        self.assertIn("token_sha256", columns)
        self.assertFalse(any("raw" in name or name in {"token", "pilot_code", "access_code"}
                             for name in columns))
        self._assert_old_function_state_unchanged()

    def test_authorize_execute_is_service_only_and_returns_narrow_grant(self):
        oid = self.db.execute("select to_regprocedure(%s)::oid", (AUTHORIZE_SIG,)).fetchone()[0]
        acl = self.db.execute("""
          select coalesce(array_agg(acl.grantee order by acl.grantee), '{}')
          from pg_proc p
          cross join lateral aclexplode(coalesce(p.proacl, acldefault('f',p.proowner))) acl
          where p.oid=%s and acl.privilege_type='EXECUTE'
        """, (oid,)).fetchone()[0]
        self.assertIn(self.db.execute("select oid from pg_roles where rolname='service_role'").fetchone()[0], acl)
        for role in ("anon", "authenticated"):
            role_oid = self.db.execute("select oid from pg_roles where rolname=%s", (role,)).fetchone()[0]
            self.assertNotIn(role_oid, acl, f"{role} unexpectedly has execute")
        self.assertNotIn(0, acl, "PUBLIC unexpectedly has execute")
        security = self.db.execute("""
          select prosecdef, provolatile, coalesce(proconfig,'{}')
          from pg_proc where oid=%s
        """, (oid,)).fetchone()
        self.assertTrue(security[0], "authorization RPC must be SECURITY DEFINER")
        self.assertEqual(security[1], "s", "authorization RPC must be STABLE")
        self.assertIn('search_path=""', security[2], "authorization RPC must have empty search_path")
        code = "synthetic-protected-pilot-code-do-not-use"
        self._insert_grant(code)
        result = self._authorize_as_service(_sha(code))
        self.assertEqual(set(result), {"expires_at", "fixture_ids", "lane_ids"})
        self.assertEqual(result["fixture_ids"], ALLOWED_FIXTURES)
        self.assertEqual(result["lane_ids"], ALLOWED_LANES)
        self.assertIn("expires_at", result)
        self._assert_old_function_state_unchanged()

    def test_revoked_grant_denies_authorization(self):
        code = "synthetic-revoked-protected-pilot-code"
        token_hash = _sha(code)
        self._insert_grant(code)
        self.assertIsNotNone(self._authorize_as_service(token_hash))
        self.db.execute(f"delete from {GRANT_TABLE} where token_sha256=%s", (token_hash,))
        self.assertIsNone(self._authorize_as_service(token_hash))
        self._assert_old_function_state_unchanged()

    def test_null_bad_format_wrong_hash_and_expired_grants_deny(self):
        code = "synthetic-expired-protected-pilot-code"
        now = datetime.now(timezone.utc)
        self._insert_grant(code, created_at=now - timedelta(days=8),
                           expires_at=now - timedelta(days=1))
        for value in (None, "bad-format", "A" * 64, _sha("wrong synthetic code"), _sha(code)):
            self.assertIsNone(self._authorize_as_service(value))

        future_code = "synthetic-future-created-pilot-grant"
        self._insert_grant(future_code, created_at=now + timedelta(hours=1),
                           expires_at=now + timedelta(hours=2))
        self.assertIsNone(self._authorize_as_service(_sha(future_code)))

    def test_grant_allowlists_and_lifetime_are_narrow(self):
        now = datetime.now(timezone.utc)
        with self.assertRaises(CheckViolation):
            self._insert_grant("synthetic-out-of-scope-fixture", fixture_ids=[24374])
        with self.assertRaises(CheckViolation):
            self._insert_grant("synthetic-out-of-scope-lane", lane_ids=["rolling72-lad-shadow-v5"])
        start = datetime(2026, 11, 20, 1, 15, tzinfo=timezone.utc)
        with self.assertRaises(CheckViolation):
            self._insert_grant("synthetic-overlong-lifetime", created_at=start,
                               expires_at=start + timedelta(days=8))
        code = "synthetic-valid-seven-day-pilot"
        start = datetime(2026, 11, 22, 1, 15, tzinfo=timezone.utc)
        expires = datetime(2026, 11, 29, 1, 15, tzinfo=timezone.utc)
        self._insert_grant(code, created_at=start, expires_at=expires)
        result = self._authorize_as_service(_sha(code))
        self.assertIsNotNone(result)
        self.assertEqual(result["fixture_ids"], ALLOWED_FIXTURES)
        self.assertEqual(result["lane_ids"], ALLOWED_LANES)
        self._assert_old_function_state_unchanged()


if __name__ == "__main__":
    unittest.main()
