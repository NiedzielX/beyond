"""Synthetic contract tests, exclusively against a disposable local PostgreSQL DB.

These fixtures are not historical observations, model predictions or prospective evidence.
The real migration is applied; synthetic point values exercise its persistence boundary.
"""
from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import unittest
from urllib.parse import urlparse

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb


class DailyPathPostgresContract(unittest.TestCase):
    counter = 10000
    github_sha = "a"*40

    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("DAILY_PATH_TEST_DSN", "")
        target = urlparse(dsn)
        if target.hostname not in {"127.0.0.1", "localhost"} or target.path != "/daily_path_contract":
            raise RuntimeError("Only the disposable localhost daily_path_contract database is allowed")
        cls.dsn = dsn
        cls.owner = psycopg.connect(dsn, autocommit=True)
        cls.owner.execute("""
          create role anon nologin;
          create role authenticated nologin;
          create role service_role nologin;
          grant usage on schema public to anon,authenticated,service_role;
          create table public.ticket_events (
            id bigint primary key, kickoff_at timestamptz not null, provider text
          );
          create table public.snapshots (
            id bigint primary key, ticket_event_id bigint references public.ticket_events(id),
            captured_at timestamptz not null, available_total integer, source text
          );
        """)
        root = Path(__file__).resolve().parents[2]
        cls.owner.execute((root/"supabase/sql/daily_inventory_path_shadow_v1.sql").read_text())
        artifact = json.loads((root/"ml/artifacts/daily_inventory_path_v1.json").read_text())
        registered = cls.owner.execute("""select model_sha256,trained_through,fitted_at,training_event_ids
          from private.daily_inventory_path_models_v1 where model_version=%s""", (artifact["model_version"],)).fetchone()
        if registered[0] != artifact["model_sha256"]:
            raise AssertionError("Migration registry differs from actual frozen artifact")
        cls.artifact = {key: artifact[key] for key in ("model_version", "model_sha256", "trained_through", "fitted_at")}
        cls.artifact.update(production_change=False, live_adjustment=0)
        if set(registered[3]) != set(artifact["training_event_ids"]):
            raise AssertionError("Migration training event registry differs from frozen artifact")

    @classmethod
    def tearDownClass(cls):
        cls.owner.close()

    def setUp(self):
        self.db = psycopg.connect(self.dsn, autocommit=True)

    def tearDown(self):
        self.db.close()

    @contextmanager
    def role(self, role):
        self.db.execute(sql.SQL("set role {}").format(sql.Identifier(role)))
        try:
            yield
        finally:
            self.db.execute("reset role")

    def now(self):
        return self.db.execute("select clock_timestamp()").fetchone()[0]

    def fixture(self, *, age_minutes=5, n=3, event_id=None, artifact=None):
        type(self).counter += 1
        event = event_id if event_id is not None else self.counter
        issue = self.now()-timedelta(minutes=age_minutes)
        kickoff = issue+timedelta(days=n)
        self.db.execute("insert into public.ticket_events values (%s,%s,'test-provider')", (event, kickoff))
        prefix = []
        for offset, (hours, count) in enumerate(((48, 1000), (36, 900), (12, 800), (1, 700)), 1):
            snapshot_id = event*100+offset
            captured = issue-timedelta(hours=hours)
            self.db.execute("insert into public.snapshots values (%s,%s,%s,%s,'fixture')", (snapshot_id,event,captured,count))
            prefix.append({"snapshot_id": snapshot_id, "captured_at": captured.isoformat(),
                           "available_total": count, "measurement_key": "test-provider/fixture",
                           "source_active": True, "source_visible": True})
        model = deepcopy(artifact or self.artifact)
        manifest = hashlib.sha256(json.dumps(prefix, sort_keys=True).encode()).hexdigest()
        payload = {"production_change": False, "artifact": model, "issue": {
            "ticket_event_id": event, "club_slug": "synthetic-test-only", "kickoff_at": kickoff.isoformat(),
            "issued_as_of_at": issue.isoformat(), "days_to_event": n, "status": "READY",
            "observed_prefix": prefix, "measurement_key": "test-provider/fixture",
            "input_manifest_sha256": manifest, "production_change": False, "target_values_used": False},
            "points": []}
        for lead in range(1, n):
            payload["points"].append({"ticket_event_id": event, "issued_as_of_at": issue.isoformat(),
                "target_at": (issue+timedelta(days=lead)).isoformat(), "lead_days": lead,
                "model_version": model["model_version"], "model_sha256": model["model_sha256"],
                "input_manifest_sha256": manifest, "measurement_key": "test-provider/fixture",
                "predicted_available_total": 700-100*lead, "baseline_available_total": 700,
                "production_change": False})
        return payload

    def record(self, payload, github_sha=None):
        with self.role("service_role"):
            return self.db.execute("select public.record_daily_inventory_path_v1(%s,%s)",
                                   (Jsonb(payload), github_sha or self.github_sha)).fetchone()[0]

    def no_attempt(self, payload):
        count = self.db.execute("select count(*) from private.daily_inventory_path_attempts_v1 where ticket_event_id=%s",
                                (payload["issue"]["ticket_event_id"],)).fetchone()[0]
        self.assertEqual(count, 0)

    def test_capture_exact_retry_and_remote_feed(self):
        payload = self.fixture()
        first = self.record(payload)
        before = self.db.execute("select received_at from private.daily_inventory_path_attempts_v1 where id=%s", (first["attempt_id"],)).fetchone()[0]
        retry = self.record(payload)
        self.assertTrue(first["inserted"])
        self.assertFalse(retry["inserted"])
        self.assertEqual(first["attempt_id"], retry["attempt_id"])
        after = self.db.execute("select received_at from private.daily_inventory_path_attempts_v1 where id=%s", (first["attempt_id"],)).fetchone()[0]
        self.assertEqual(before, after)
        with self.role("service_role"):
            feed = self.db.execute("select public.daily_inventory_path_feed_v1()").fetchone()[0]
        vintage = next(row for row in feed["events"] if row["ticket_event_id"] == payload["issue"]["ticket_event_id"])
        self.assertEqual(len(vintage["points"]), 2)
        self.assertEqual(len(vintage["observations"]), 4)
        self.assertFalse(feed["production_change"])
        self.assertTrue(all(point["score"] is None for point in vintage["points"]))

    def test_conflicting_retry_never_overwrites(self):
        payload = self.fixture(); self.record(payload)
        payload["points"][0]["predicted_available_total"] += 1
        with self.assertRaisesRegex(psycopg.Error, "CONFLICTING_IMMUTABLE"):
            self.record(payload)

    def test_point_failures_roll_back_the_entire_attempt(self):
        for mutation in ("missing", "duplicate", "wrong_target", "negative", "cross_event"):
            payload = self.fixture()
            if mutation == "missing": payload["points"].pop()
            elif mutation == "duplicate": payload["points"][1] = deepcopy(payload["points"][0])
            elif mutation == "wrong_target": payload["points"][1]["target_at"] = payload["points"][0]["target_at"]
            elif mutation == "negative": payload["points"][1]["predicted_available_total"] = -1
            else: payload["points"][1]["ticket_event_id"] += 1
            with self.subTest(mutation=mutation), self.assertRaises(psycopg.Error):
                self.record(payload)
            self.no_attempt(payload)

    def test_prefix_must_match_actual_source_rows(self):
        for mutation in ("value", "order", "source", "hidden", "future_time"):
            payload = self.fixture(); prefix = payload["issue"]["observed_prefix"]
            if mutation == "value": prefix[1]["available_total"] += 1
            elif mutation == "order": prefix.reverse()
            elif mutation == "source": prefix[1]["measurement_key"] = "wrong/source"
            elif mutation == "hidden": prefix[1]["source_visible"] = False
            else: prefix[1]["captured_at"] = self.now().isoformat()
            with self.subTest(mutation=mutation), self.assertRaisesRegex(psycopg.Error, "PREFIX"):
                self.record(payload)
            self.no_attempt(payload)

    def test_outside_window_or_in_training_event_is_rejected(self):
        for age in (-2, 92):
            payload = self.fixture(age_minutes=age)
            with self.subTest(age=age), self.assertRaisesRegex(psycopg.Error, "WINDOW"):
                self.record(payload)
            self.no_attempt(payload)
        payload = self.fixture(event_id=1)
        with self.assertRaisesRegex(psycopg.Error, "FROZEN_MODEL_IDENTITY"):
            self.record(payload)

    def test_frozen_flags_and_hash_are_required(self):
        for mutation in ("target_used", "production", "live", "model_hash", "github_sha"):
            payload = self.fixture(); github = self.github_sha
            if mutation == "target_used": payload["issue"]["target_values_used"] = True
            elif mutation == "production": payload["production_change"] = True
            elif mutation == "live": payload["artifact"]["live_adjustment"] = 1
            elif mutation == "model_hash": payload["artifact"]["model_sha256"] = "0"*64
            else: github = "bad"
            with self.subTest(mutation=mutation), self.assertRaises(psycopg.Error):
                self.record(payload, github)
            self.no_attempt(payload)

    def test_browser_roles_and_direct_private_table_access_denied(self):
        payload = self.fixture()
        for role in ("anon", "authenticated"):
            for call, parameters in (("select public.record_daily_inventory_path_v1(%s,%s)", (Jsonb(payload),self.github_sha)),
                                     ("select public.score_daily_inventory_path_v1()", ()),
                                     ("select public.daily_inventory_path_feed_v1()", ())):
                with self.subTest(role=role, call=call), self.role(role), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    self.db.execute(call, parameters)
        for role in ("anon", "authenticated", "service_role"):
            with self.subTest(role=role), self.role(role), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                self.db.execute("select * from private.daily_inventory_path_attempts_v1")

    def seed_synthetic_scoring_fixture(self):
        """Test-only historical rows; never call this against any external database."""
        now = self.now()
        model = {"model_version": "synthetic-score-fixture", "model_sha256": "c"*64,
                 "trained_through": (now-timedelta(days=10)).isoformat(),
                 "fitted_at": (now-timedelta(days=5)).isoformat(), "production_change": False, "live_adjustment": 0}
        self.db.execute("""insert into private.daily_inventory_path_models_v1
          (model_version,model_sha256,trained_through,fitted_at,training_event_ids) values(%s,%s,%s,%s,'{}') on conflict do nothing""",
          (model["model_version"],model["model_sha256"],model["trained_through"],model["fitted_at"]))
        payload = self.fixture(age_minutes=3*24*60, n=5, artifact=model)
        issue = payload["issue"]
        attempt = self.db.execute("""insert into private.daily_inventory_path_attempts_v1
          (ticket_event_id,issued_as_of_at,kickoff_at,model_version,model_sha256,received_at,github_sha,status,input_manifest_sha256,payload)
          values(%s,%s,%s,%s,%s,%s,%s,'READY',%s,%s) returning id""",
          (issue["ticket_event_id"],issue["issued_as_of_at"],issue["kickoff_at"],model["model_version"],model["model_sha256"],
           issue["issued_as_of_at"],self.github_sha,issue["input_manifest_sha256"],Jsonb(payload))).fetchone()[0]
        point_ids = []
        for point in payload["points"]:
            point_ids.append(self.db.execute("""insert into private.daily_inventory_path_points_v1
              (attempt_id,target_at,lead_days,predicted_available_total,baseline_available_total,measurement_key)
              values(%s,%s,%s,20,50,'test-provider/fixture') returning id""", (attempt,point["target_at"],point["lead_days"])).fetchone()[0])
        target = self.db.execute("select target_at from private.daily_inventory_path_points_v1 where id=%s", (point_ids[0],)).fetchone()[0]
        event = issue["ticket_event_id"]
        # The later-than-target row must never score the first target.
        for offset, hours, available in ((50,-5,30),(51,-1,0),(52,1,999)):
            self.db.execute("insert into public.snapshots values(%s,%s,%s,%s,'fixture')",
                            (event*100+offset,event,target+timedelta(hours=hours),available))
        return payload, attempt, point_ids, event*100+51

    def test_zero_target_scoring_is_genuine_idempotent_and_immutable(self):
        _, attempt, points, target_snapshot = self.seed_synthetic_scoring_fixture()
        with self.role("service_role"):
            self.db.execute("select public.score_daily_inventory_path_v1()")
        score = self.db.execute("""select target_snapshot_id,actual_available_total,candidate_abs_error,baseline_abs_error,scored_at
          from private.daily_inventory_path_scores_v1 where point_id=%s""", (points[0],)).fetchone()
        self.assertEqual(score[:4], (target_snapshot,0,20,50))
        with self.role("service_role"):
            retry = self.db.execute("select public.score_daily_inventory_path_v1()").fetchone()[0]
        self.assertEqual(retry["inserted_scores"], 0)
        self.assertEqual(self.db.execute("select scored_at from private.daily_inventory_path_scores_v1 where point_id=%s", (points[0],)).fetchone()[0], score[4])
        for table, column, identifier in (("models", "model_version", self.artifact["model_version"]),
                                          ("attempts", "id", attempt), ("points", "id", points[0]), ("scores", "point_id", points[0])):
            for operation in ("update", "delete"):
                name = "daily_inventory_path_"+table+"_v1"
                query = (sql.SQL("update private.{} set {}={} where {}=%s").format(sql.Identifier(name),sql.Identifier(column),sql.Identifier(column),sql.Identifier(column))
                         if operation == "update" else sql.SQL("delete from private.{} where {}=%s").format(sql.Identifier(name),sql.Identifier(column)))
                with self.subTest(table=table, operation=operation), self.assertRaisesRegex(psycopg.Error, "IMMUTABLE"):
                    self.db.execute(query, (identifier,))

    def test_latest_invalid_target_does_not_fall_back_or_use_future_rows(self):
        for invalid in (None,-1):
            _, _, points, snapshot_id = self.seed_synthetic_scoring_fixture()
            self.db.execute("update public.snapshots set available_total=%s where id=%s", (invalid,snapshot_id))
            with self.role("service_role"):
                self.db.execute("select public.score_daily_inventory_path_v1()")
            self.assertEqual(self.db.execute("select count(*) from private.daily_inventory_path_scores_v1 where point_id=%s", (points[0],)).fetchone()[0], 0)
        _, _, points, snapshot_id = self.seed_synthetic_scoring_fixture()
        self.db.execute("update public.snapshots set source='changed-measurement' where id=%s", (snapshot_id,))
        with self.role("service_role"):
            self.db.execute("select public.score_daily_inventory_path_v1()")
        self.assertEqual(self.db.execute("select count(*) from private.daily_inventory_path_scores_v1 where point_id=%s", (points[0],)).fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
