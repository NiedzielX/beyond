"""Isolated PostgreSQL 16 contract tests for the fresh PERS/drift24 lane.

Only the dedicated loopback database ``rolling72_mvp_paired_drift24_test`` is
accepted. Source fixtures are synthetic; clocks asserted by the runtime are
database clocks, never caller supplied.
"""
from __future__ import annotations

from datetime import timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unittest
from urllib.parse import urlparse

import psycopg

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / "supabase/sql/rolling72_mvp_paired_drift24_v1.sql"
LANE = "rolling72-mvp-paired-drift24-v1"
PERS_B_SQL_SHA256 = "c9621bb692ca7de38037a204a9ca204ed3be370657b9ab89dc3aa438575effb4"
LAD_V5_SQL_SHA256 = "c2a3071d7109b74040228fb6b4ee77a6524afccc7174550acb7fa362e9f7afd2"

SOURCE_TEST = ROOT / "tests/postgres/test_rolling72_mvp_research_v1.py"
SPEC = importlib.util.spec_from_file_location("paired_drift24_source_fixture_helpers", SOURCE_TEST)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load the isolated P0-4b source fixture helpers")
SOURCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCE)
SourceFixture = SOURCE.Rolling72MvpResearchV1


class Rolling72MvpPairedDrift24V1(SourceFixture):
    """Use source fixture mechanics only; do not discover source-lane tests."""

    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("ROLLING72_MVP_PAIRED_DRIFT24_TEST_DSN", "")
        target = urlparse(dsn)
        if (target.scheme not in {"postgres", "postgresql"}
                or target.hostname not in {"127.0.0.1", "localhost"}
                or target.port != 55440
                or target.path != "/rolling72_mvp_paired_drift24_test"):
            raise RuntimeError(
                "Only 127.0.0.1:55440/rolling72_mvp_paired_drift24_test is allowed"
            )
        cls.dsn = dsn
        cls.db = psycopg.connect(dsn, autocommit=True)
        version = int(cls.db.execute("show server_version_num").fetchone()[0])
        identity = cls.db.execute("select current_database()").fetchone()[0]
        if not 160000 <= version < 170000 or identity != "rolling72_mvp_paired_drift24_test":
            cls.db.close()
            raise RuntimeError("Paired drift24 tests require the dedicated PostgreSQL 16 database")
        cls._bootstrap_parent_schema()

    def setUp(self):
        self.db = type(self).db
        self._reset_paired_lane()
        super().setUp()  # Installs/activates only the P0-4b source fixture.
        self._manifest_activate()
        if not SQL.exists():
            self.fail(f"Missing paired drift24 migration: {SQL}")
        self.preexisting_functions = self._function_hashes()
        self.db.execute(SQL.read_text(encoding="utf-8"))
        after = self._function_hashes()
        self.assertTrue(all(after.get(key) == digest
                            for key, digest in self.preexisting_functions.items()),
                        "paired migration changed a pre-existing source/admission function")
        self._activate_paired_lane()

    def _reset_paired_lane(self):
        for signature in (
            "public.activate_rolling72_mvp_paired_drift24_v1(text,text)",
            "public.issue_rolling72_mvp_paired_drift24_v1(integer)",
            "public.score_rolling72_mvp_paired_drift24_v1(integer)",
            "public.get_rolling72_mvp_paired_drift24_v1_status()",
        ):
            self.db.execute(f"drop function if exists {signature} cascade")
        for suffix in ("score_attempts", "labels", "issue_attempts", "predictions",
                       "issue_bundles", "runs", "lane"):
            self.db.execute(f"drop table if exists private.rolling72_mvp_paired_drift24_v1_{suffix} cascade")
        helpers = self.db.execute("""
          select p.oid::regprocedure::text
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where n.nspname='private' and p.proname like 'rolling72_mvp_paired_drift24_v1_%'
          order by p.proname
        """).fetchall()
        for (signature,) in helpers:
            self.db.execute(f"drop function if exists {signature} cascade")

    def _function_hashes(self):
        rows = self.db.execute("""
          select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),
           encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex')
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where n.nspname in('public','private')
          order by 1,2,3
        """).fetchall()
        return {(schema, name, args): digest for schema, name, args, digest in rows}

    def _activate_paired_lane(self):
        source = self.db.execute("""
          select manifest_sha256,sql_sha256,max_fixtures,issue_until,scoring_until
          from private.rolling72_mvp_research_v1_lane
          where lane_id='rolling72-mvp-research-v1'
        """).fetchone()
        self.assertIsNotNone(source)
        issue_until = source[3].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        scoring_until = source[4].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        manifest = {
            "lane_id": LANE,
            "version": LANE,
            "source_lane_id": "rolling72-mvp-research-v1",
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
            "max_fixtures": source[2],
            "source_manifest_sha256": source[0],
            "source_sql_sha256": source[1],
            "sql_sha256": hashlib.sha256(SQL.read_bytes()).hexdigest(),
            "issue_until": issue_until,
            "scoring_until": scoring_until,
            "b_sql_sha256": PERS_B_SQL_SHA256,
            "lad_v5_sql_sha256": LAD_V5_SQL_SHA256,
        }
        self.manifest_text = json.dumps(manifest, separators=(",", ":"), sort_keys=True)
        self.manifest_sha256 = hashlib.sha256(self.manifest_text.encode("utf-8")).hexdigest()
        self.activation = self._rpc("activate_rolling72_mvp_paired_drift24_v1",
                                    self.manifest_text, self.manifest_sha256)

    def _rpc(self, name: str, *args):
        self.db.execute("set role service_role")
        try:
            return self.db.execute(
                f"select public.{name}({','.join(['%s'] * len(args))})", args
            ).fetchone()[0]
        finally:
            self.db.execute("reset role")

    def _source_origin(self, *, available=0, kickoff_in_days=25):
        admission = self._admit_fixture(kickoff_in_days=kickoff_in_days)
        self._register(admission)
        snapshot = self._insert_bundle(admission, available=available)
        capture = self._capture()
        seal = self.db.execute("""
          select id,known_at,captured_at,read_completed_at,ticket_event_id
          from private.rolling72_mvp_research_v1_seals where snapshot_id=%s
        """, (snapshot,)).fetchone()
        self.assertIsNotNone(seal, f"source fixture failed to produce a committed seal: {capture!r}")
        return admission, seal

    def _issue(self, *, limit=25):
        return self._rpc("issue_rolling72_mvp_paired_drift24_v1", limit)

    def test_activation_contract_is_idempotent_and_read_only(self):
        again = self._rpc("activate_rolling72_mvp_paired_drift24_v1",
                          self.manifest_text, self.manifest_sha256)
        self.assertTrue(again["idempotent"])
        self.assertEqual(again["lane_id"], LANE)
        bad = dict(json.loads(self.manifest_text), b_sql_sha256="0" * 64)
        bad_text = json.dumps(bad, separators=(",", ":"), sort_keys=True)
        bad_sha = hashlib.sha256(bad_text.encode()).hexdigest()
        with self.assertRaises(psycopg.Error):
            self._rpc("activate_rolling72_mvp_paired_drift24_v1", bad_text, bad_sha)
        for signature in (
            "public.activate_rolling72_mvp_paired_drift24_v1(text,text)",
            "public.issue_rolling72_mvp_paired_drift24_v1(integer)",
            "public.score_rolling72_mvp_paired_drift24_v1(integer)",
            "public.get_rolling72_mvp_paired_drift24_v1_status()",
        ):
            self.assertTrue(self.db.execute(
                "select has_function_privilege('service_role',%s,'EXECUTE')", (signature,)
            ).fetchone()[0])
            for role in ("anon", "authenticated"):
                self.assertFalse(self.db.execute(
                    "select has_function_privilege(%s,%s,'EXECUTE')", (role, signature)
                ).fetchone()[0])
            self.assertFalse(self.db.execute("""
              select exists(
                select 1 from pg_proc p,
                  lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
                where p.oid=%s::regprocedure and a.grantee=0
                 and a.privilege_type='EXECUTE')
            """, (signature,)).fetchone()[0])

    def test_first_zero_issue_emits_common_clock_and_six_fallback_values(self):
        admission, seal = self._source_origin(available=0)
        result = self._issue()
        self.assertEqual(result["processed_bundles"], 1, result)
        self.assertEqual(result["numeric_forecasts"], 6, result)
        bundle = self.db.execute("""
          select id,projection_reference_at,calculation_completed_at,issued_at,
           issue_latency_seconds,source_age_seconds,origin_available_total,drift_status,fallback_reason
          from private.rolling72_mvp_paired_drift24_v1_issue_bundles where seal_id=%s
        """, (seal[0],)).fetchone()
        (bundle_id, projection_ref, calc_done, issued, latency, source_age,
         origin_total, drift_status, fallback_reason) = bundle
        self.assertEqual(origin_total, 0)
        self.assertGreaterEqual(projection_ref, seal[1])
        self.assertGreaterEqual(calc_done, projection_ref)
        self.assertGreater(issued, calc_done)
        self.assertGreaterEqual(latency, 0)
        self.assertLessEqual(latency, 90)
        self.assertGreaterEqual(source_age, 0)
        self.assertLessEqual(source_age, 3600)
        self.assertEqual(drift_status, "FALLBACK_PERS")
        self.assertEqual(fallback_reason, "NO_24H_ANCHOR")
        rows = self.db.execute("""
          select horizon_hours,method,target_at,issued_at,status,prediction,fallback_reason
          from private.rolling72_mvp_paired_drift24_v1_predictions
          where bundle_id=%s order by horizon_hours,method
        """, (bundle_id,)).fetchall()
        self.assertEqual(len(rows), 6)
        for horizon, method, target, row_issue, status, prediction, reason in rows:
            self.assertEqual(row_issue, issued)
            self.assertEqual(target, issued + timedelta(hours=horizon))
            self.assertIn(method, {"PERS", "DRIFT24"})
            self.assertEqual(prediction, 0)
            self.assertEqual(status, "READY" if method == "PERS" else "FALLBACK_PERS")
            self.assertEqual(reason, None if method == "PERS" else "NO_24H_ANCHOR")
        attempts = self.db.execute("""
          select count(*),count(distinct horizon_hours),bool_and(status='ISSUED')
          from private.rolling72_mvp_paired_drift24_v1_issue_attempts where seal_id=%s
        """, (seal[0],)).fetchone()
        self.assertEqual(attempts, (3, 3, True))

    def test_status_is_registered_as_service_only_before_first_label(self):
        result = self._rpc("get_rolling72_mvp_paired_drift24_v1_status")
        self.assertEqual(result["lane_id"], LANE)
        cards = result["scorecards"]
        self.assertEqual([row["horizon_hours"] for row in cards], [24, 48, 72])
        for row in cards:
            self.assertEqual(row["accepted_common_labels"], 0)
            self.assertEqual(row["numeric_pairs"], 0)
            self.assertIsNone(row["pers_event_balanced_mae"])
            self.assertIsNone(row["drift24_event_balanced_mae"])
            self.assertIsNone(row["delta_mae"])


# Import only fixture methods. Prevent unittest from discovering the inherited
# source suite as part of this paired-lane file.
for _name in dir(SourceFixture):
    if _name.startswith("test_"):
        setattr(Rolling72MvpPairedDrift24V1, _name, None)
del SourceFixture


if __name__ == "__main__":
    unittest.main()
