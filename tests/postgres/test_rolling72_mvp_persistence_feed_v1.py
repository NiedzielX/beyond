"""Isolated PostgreSQL 16 tests for the read-only PERS investor feed."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
from datetime import datetime, timedelta
import unittest
from urllib.parse import urlparse

import psycopg

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / "supabase/sql/rolling72_mvp_persistence_feed_v1.sql"
CLOCK_GUARD_SQL = ROOT / "supabase/sql/rolling72_mvp_persistence_issue_clock_guard_v1.sql"
PERSIST_TEST_PATH = ROOT / "tests/postgres/test_rolling72_mvp_persistence_v1.py"
SPEC = importlib.util.spec_from_file_location("pers_feed_persistence_fixture_helpers", PERSIST_TEST_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load isolated PERS fixture helpers")
HELPERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPERS)
PersistenceFixture = HELPERS.Rolling72MvpPersistenceV1

FUNCTION = "public.get_rolling72_mvp_persistence_feed_v1"
SIGNATURE = FUNCTION + "(bigint,text,bigint,integer,bigint)"
LANE = "rolling72-mvp-persistence-v1"


class Rolling72MvpPersistenceFeedV1(PersistenceFixture):
    """Reuse only the synthetic P0-4b/P0-4c mechanics on a distinct test DB."""

    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("ROLLING72_MVP_PERSISTENCE_FEED_TEST_DSN", "")
        target = urlparse(dsn)
        if (target.scheme not in {"postgres", "postgresql"}
                or target.hostname not in {"127.0.0.1", "localhost"}
                or target.port != 55440
                or target.path != "/rolling72_mvp_persistence_feed_test"):
            raise RuntimeError(
                "Only 127.0.0.1:55440/rolling72_mvp_persistence_feed_test is allowed"
            )
        cls.dsn = dsn
        cls.db = psycopg.connect(dsn, autocommit=True)
        version = int(cls.db.execute("show server_version_num").fetchone()[0])
        identity = cls.db.execute("select current_database()").fetchone()[0]
        if not 160000 <= version < 170000 or identity != "rolling72_mvp_persistence_feed_test":
            cls.db.close()
            raise RuntimeError("Feed tests require the dedicated PostgreSQL 16 database")
        cls._bootstrap_parent_schema()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    def setUp(self):
        self.db.execute(f"drop function if exists {SIGNATURE} cascade")
        # Parent setUp installs synthetic admission, P0-4b and P0-4c state and
        # activates both immutable lanes. No old test methods are inherited.
        super().setUp()
        if not CLOCK_GUARD_SQL.exists():
            raise RuntimeError(f"Missing isolated PERS clock-guard patch: {CLOCK_GUARD_SQL}")
        self.db.execute(CLOCK_GUARD_SQL.read_text(encoding="utf-8"))
        before = self._function_hashes()
        self.db.execute(SQL.read_text(encoding="utf-8"))
        after = self._function_hashes()
        self.assertTrue(all(after.get(key) == value for key, value in before.items()),
                        "feed migration changed existing source/PERS function bodies")
        self._admission, seal = self._source_seal(available=0, kickoff_in_days=10)
        self.ticket_event_id = self._admission["ticket_event_id"]
        self.origin_seal_id = seal[0]
        self.issue_result = self._rpc("issue_rolling72_mvp_persistence_v1", 25)
        self.assertEqual(self.issue_result["processed_bundles"], 1)

    def _function_hashes(self):
        rows = self.db.execute("""
          select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),
           encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex')
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where (n.nspname='public' and p.proname like 'get_rolling72_mvp_%')
             or (n.nspname='private' and p.proname like 'rolling72_mvp_%')
          order by 1,2,3
        """).fetchall()
        return {(schema, name, args): digest for schema, name, args, digest in rows}

    def _feed(self, ticket_event_id=None, lane=LANE, before_bundle_id=None,
              limit=50, before_receipt_id=None):
        self.db.execute("set role service_role")
        try:
            return self.db.execute(
                f"select {FUNCTION}(%s,%s,%s,%s,%s)",
                (ticket_event_id or self.ticket_event_id, lane, before_bundle_id,
                 limit, before_receipt_id),
            ).fetchone()[0]
        finally:
            self.db.execute("reset role")

    def _ledger_snapshot(self):
        tables = (
            "private.rolling72_mvp_research_v1_attempts",
            "private.rolling72_mvp_research_v1_seals",
            "private.rolling72_mvp_research_v1_candidates",
            "private.rolling72_mvp_persistence_v1_issue_bundles",
            "private.rolling72_mvp_persistence_v1_predictions",
            "private.rolling72_mvp_persistence_v1_issue_attempts",
            "private.rolling72_mvp_persistence_v1_labels",
            "private.rolling72_mvp_persistence_v1_score_attempts",
        )
        return {table: self.db.execute(f"select count(*) from {table}").fetchone()[0]
                for table in tables}

    def _capture_current_fixture(self, available):
        snapshot = self._insert_bundle(self._admission, available=available)
        result = self._capture()
        seal = self.db.execute("""
          select id from private.rolling72_mvp_research_v1_seals where snapshot_id=%s
        """, (snapshot,)).fetchone()
        self.assertIsNotNone(seal, f"expected a second committed source seal: {result!r}")
        return seal[0]

    def test_fixed_pers_triplet_maps_real_zero_origin_and_null_free_methods(self):
        before = self._ledger_snapshot()
        payload = self._feed()
        after = self._ledger_snapshot()
        self.assertEqual(before, after, "feed reads must not write source or PERS ledgers")
        self.assertEqual(payload["schema_version"], "rolling72-investor-feed-v1")
        self.assertEqual(payload["status"], "OK")
        fixture = payload["fixtures"][0]
        self.assertEqual(fixture["ticket_event_id"], self.ticket_event_id)
        self.assertEqual(fixture["metadata_status"], "MATCH")
        lane = fixture["availability_lanes"][0]
        self.assertEqual(lane["lane_id"], LANE)
        self.assertEqual(lane["model_version"], LANE)
        self.assertEqual(len(lane["issues"]), 1)
        issue = lane["issues"][0]
        self.assertEqual(issue["issue_receipt_id"], self.origin_seal_id)
        self.assertEqual(issue["origin_observation"]["receipt_id"], self.origin_seal_id)
        self.assertEqual(issue["origin_observation"]["available_total"], 0)
        self.assertEqual(len(issue["targets"]), 3)
        for target in issue["targets"]:
            self.assertEqual(len(target["methods"]), 1)
            method = target["methods"][0]
            self.assertEqual(method["method"], "persistence")
            self.assertEqual(method["value"], 0)
            self.assertEqual(method["predicted_delta_from_origin"], 0)
            self.assertEqual(datetime.fromisoformat(target["target_at"]),
                             datetime.fromisoformat(issue["issued_at"])+timedelta(hours=target["horizon_hours"]))
        self.assertNotIn("input_prefix", issue)
        self.assertIsNone(issue["lineage"]["parent_bundle_id"])
        self.assertIsNone(issue["lineage"]["parent_prefix_sha256"])
        self.assertEqual(issue["scenario"]["price"], "UNKNOWN")
        self.assertEqual(issue["scenario"]["promotion"], "UNKNOWN")
        self.assertEqual(issue["scenario"]["advertising"], "UNKNOWN")
        self.assertEqual(issue["scenario"]["pool_policy"], "UNKNOWN")
        self.assertEqual(issue["scenario"]["pool_interpretation"], "LIMITED_PUBLIC_INVENTORY_PROXY")
        self.assertEqual(fixture["attendance_lane"]["status"], "UNAVAILABLE")

    def test_visible_prefix_is_assembled_from_observations_with_both_clock_filters(self):
        self._capture_current_fixture(9)
        self._rpc("issue_rolling72_mvp_persistence_v1", 25)
        second_issue_row = self.db.execute("""
          select b.issued_at,b.source_captured_at
          from private.rolling72_mvp_persistence_v1_issue_bundles b
          where b.ticket_event_id=%s order by b.id desc limit 1
        """, (self.ticket_event_id,)).fetchone()
        issued_at, origin_captured_at = second_issue_row

        # A receipt with an earlier capture but a later known clock is visible
        # in the current observations page, yet cannot enter this vintage's prefix.
        late_snapshot = self._insert_bundle(
            self._admission, available=77,
            captured_at=origin_captured_at - timedelta(milliseconds=100),
        )
        late_known_at = self.db.execute("select clock_timestamp()").fetchone()[0]
        late_seal_id = self._synthetic_historical_seal(
            self._admission, late_snapshot,
            captured_at=origin_captured_at - timedelta(milliseconds=100),
            known_at=late_known_at, available=77,
        )
        self.assertGreater(late_known_at, issued_at)

        payload = self._feed(limit=50)
        fixture = payload["fixtures"][0]
        issue = fixture["availability_lanes"][0]["issues"][0]
        self.assertNotIn("input_prefix", issue)
        origin = issue["origin_observation"]
        visible_prefix = [row for row in fixture["observations"]
                          if datetime.fromisoformat(row["captured_at"])
                          <= datetime.fromisoformat(origin["captured_at"])
                          and datetime.fromisoformat(row["known_at"])
                          <= datetime.fromisoformat(issue["issued_at"])]
        self.assertEqual({row["receipt_id"] for row in visible_prefix},
                         {self.origin_seal_id, origin["receipt_id"]})
        self.assertNotIn(late_seal_id, {row["receipt_id"] for row in visible_prefix})
        self.assertTrue(all(datetime.fromisoformat(row["captured_at"])
                            <= datetime.fromisoformat(origin["captured_at"])
                            and datetime.fromisoformat(row["known_at"])
                            <= datetime.fromisoformat(issue["issued_at"])
                            for row in visible_prefix))

    def test_current_binding_mismatch_is_reported_without_rewriting_issue_identity(self):
        registered_url = self.db.execute("""
          select binding->>'source_url'
          from private.rolling72_mvp_research_v1_registry where ticket_event_id=%s
        """, (self.ticket_event_id,)).fetchone()[0]
        changed_url = registered_url + "?current-metadata-change=1"
        self.db.execute("update public.ticket_events set source_url=%s where id=%s",
                        (changed_url, self.ticket_event_id))
        payload = self._feed()
        fixture = payload["fixtures"][0]
        issue = fixture["availability_lanes"][0]["issues"][0]
        self.assertEqual(payload["status"], "PARTIAL")
        self.assertEqual(fixture["metadata_status"], "MISMATCH")
        self.assertEqual(fixture["source_url"], registered_url)
        self.assertEqual(fixture["current_metadata"]["source_url"], changed_url)
        self.assertEqual(issue["issue_receipt_id"], self.origin_seal_id)

    def test_later_label_is_separate_from_prefix_and_zero_errors_are_real(self):
        scored = self._past_score_fixture(actual=0, issue_age_hours=27)
        score = self._rpc("score_rolling72_mvp_persistence_v1", 100)
        self.assertEqual(score["labels"], 1)
        payload = self._feed(scored["admission"]["ticket_event_id"])
        issue = payload["fixtures"][0]["availability_lanes"][0]["issues"][0]
        target = next(row for row in issue["targets"] if row["horizon_hours"] == 24)
        label = target["label"]
        self.assertEqual(target["status"], "SCORED")
        self.assertEqual(label["actual_available_total"], 0)
        self.assertEqual(label["method_absolute_errors"]["persistence"], 41)
        fixture = payload["fixtures"][0]
        prefix_ids = {row["receipt_id"] for row in fixture["observations"]
                      if datetime.fromisoformat(row["captured_at"])
                      <= datetime.fromisoformat(issue["origin_observation"]["captured_at"])
                      and datetime.fromisoformat(row["known_at"])
                      <= datetime.fromisoformat(issue["issued_at"])}
        self.assertNotIn(label["receipt_id"], prefix_ids)
        self.assertGreater(label["known_at"], issue["issued_at"])
        self.assertEqual(label["origin_sector_count"], issue["origin_observation"]["sector_count"])
        self.assertGreater(label["target_sector_count"], 0)
        self.assertEqual(label["continuity"], "UNKNOWN")
        self.assertIn(label["scope_status"], {"UNKNOWN", "CHANGED"})

    def test_fixture_page_does_not_narrow_global_pers_scorecards_or_denominator(self):
        second_admission, second_seal = self._source_seal(available=20, kickoff_in_days=10)
        self._rpc("issue_rolling72_mvp_persistence_v1", 25)
        payload = self._feed()
        self.assertEqual(len(payload["fixtures"]), 1)
        scope = payload["scorecard_scope"]
        self.assertEqual(scope["scope"], "FULL_LANE_COHORT")
        self.assertEqual(scope["coverage_basis"], "SOURCE_BACKED_ELIGIBLE_CANDIDATES")
        self.assertEqual(scope["candidate_denominator"]["in_scope_candidates"], 6)
        card = next(row for row in payload["scorecards"] if row["horizon_hours"] == 24)
        self.assertEqual(card["method"], "persistence")
        self.assertEqual(card["numeric_forecasts"], 2)
        self.assertEqual(card["forecast_fixtures"], 2)
        self.assertEqual(card["eligible_source_candidates"], 2)
        self.assertEqual(card["unissued_source_opportunities"], 0)
        self.assertIsNone(card["event_balanced_mae"])
        self.assertEqual(second_admission["ticket_event_id"],
                         self._feed(second_admission["ticket_event_id"])["fixtures"][0]["ticket_event_id"])
        self.assertNotEqual(second_seal[0], self.origin_seal_id)

    def test_receipt_and_bundle_cursors_page_independently(self):
        # Create a second issue and a later observation without an issue so the
        # cursors represent different ledgers and can be advanced separately.
        self._capture_current_fixture(9)
        self._rpc("issue_rolling72_mvp_persistence_v1", 25)
        self._capture_current_fixture(17)
        p1 = self._feed(limit=1)
        fixture = p1["fixtures"][0]
        self.assertTrue(p1["issues_page"]["has_more"])
        self.assertTrue(fixture["observations_page"]["has_more"])
        issue_cursor = p1["issues_page"]["next_cursor"]
        receipt_cursor = fixture["observations_page"]["next_cursor"]
        next_issue = self._feed(limit=1, before_bundle_id=issue_cursor)
        self.assertNotEqual(next_issue["fixtures"][0]["availability_lanes"][0]["issues"][0]["bundle_id"],
                            fixture["availability_lanes"][0]["issues"][0]["bundle_id"])
        next_observations = self._feed(limit=1, before_receipt_id=receipt_cursor)
        self.assertNotEqual(next_observations["fixtures"][0]["observations"][0]["receipt_id"],
                            fixture["observations"][0]["receipt_id"])

    def test_latest_failed_attempt_is_visible_without_rewriting_origin(self):
        self._synthetic_unknown_capture_attempt(
            self._admission, known_at=self.db.execute("select clock_timestamp()").fetchone()[0]
        )
        payload = self._feed()
        fixture = payload["fixtures"][0]
        self.assertEqual(fixture["latest_source_attempt"]["status"], "INTERNAL_ERROR")
        issue = fixture["availability_lanes"][0]["issues"][0]
        self.assertEqual(issue["issue_receipt_id"], self.origin_seal_id)
        self.assertEqual(issue["origin_observation"]["source_status"], "VALID")
        self.assertEqual(fixture["latest_observation"]["source_status"], "VALID_WITH_NEWER_FAILED_ATTEMPT")
        self.assertNotIn("latest_source_attempt", issue)
        self.assertEqual(payload["status"], "PARTIAL")

    def test_acl_validation_and_feed_function_are_read_only(self):
        for role in ("anon", "authenticated"):
            self.db.execute(f"set role {role}")
            try:
                with self.assertRaises(psycopg.Error):
                    self.db.execute(f"select {FUNCTION}(%s,%s,%s,%s,%s)",
                                    (self.ticket_event_id, LANE, None, 50, None))
            finally:
                self.db.execute("reset role")
        self.assertTrue(self.db.execute("select has_function_privilege('service_role',%s,'EXECUTE')",
                                        (SIGNATURE,)).fetchone()[0])
        self.assertFalse(self.db.execute("select has_function_privilege('anon',%s,'EXECUTE')",
                                         (SIGNATURE,)).fetchone()[0])
        for args in (
            (None, LANE, None, 50, None),
            (self.ticket_event_id, "rolling72-common-flow-e5-v1", None, 50, None),
            (self.ticket_event_id, LANE, 0, 50, None),
            (self.ticket_event_id, LANE, None, 201, None),
            (self.ticket_event_id, LANE, None, 50, 0),
        ):
            with self.assertRaises(psycopg.Error):
                self._rpc("get_rolling72_mvp_persistence_feed_v1", *args)


# The fixture parent supplies helper methods only. Do not discover or rerun any
# of its admission, P0-4b or P0-4c test methods in this feed suite.
for _name in tuple(vars(PersistenceFixture)):
    if _name.startswith("test_"):
        setattr(Rolling72MvpPersistenceFeedV1, _name, None)
del PersistenceFixture


if __name__ == "__main__":
    unittest.main()
