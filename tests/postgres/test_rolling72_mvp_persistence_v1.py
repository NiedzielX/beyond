"""Isolated PostgreSQL 16 contract tests for the P0-4c PERS lane.

All inputs are synthetic and the database is hard-bound to the dedicated
rolling72_mvp_persistence_test database on loopback port 55440. The existing
P0-4b fixture helpers are reused to produce genuine committed seals/candidates.
"""
from __future__ import annotations

from datetime import timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
import uuid
import unittest
from urllib.parse import urlparse

import psycopg
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/sql/rolling72_mvp_persistence_v1.sql"
PERSIST = "rolling72_mvp_persistence_v1"
_RESEARCH_PATH = ROOT / "tests/postgres/test_rolling72_mvp_research_v1.py"
_SPEC = importlib.util.spec_from_file_location("rolling72_mvp_research_test_helpers", _RESEARCH_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Could not load P0-4b synthetic fixture helpers")
_RESEARCH = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RESEARCH)
Rolling72MvpResearchV1 = _RESEARCH.Rolling72MvpResearchV1


class Rolling72MvpPersistenceV1(Rolling72MvpResearchV1):
    """P0-4c tests using the independently reviewed P0-4b source lane."""

    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("ROLLING72_MVP_PERSISTENCE_TEST_DSN", "")
        target = urlparse(dsn)
        if (target.hostname not in {"127.0.0.1", "localhost"}
                or target.port != 55440
                or target.path != "/rolling72_mvp_persistence_test"):
            raise RuntimeError(
                "Only the dedicated localhost rolling72_mvp_persistence_test database is allowed"
            )
        cls.dsn = dsn
        cls.db = psycopg.connect(dsn, autocommit=True)
        version = int(cls.db.execute("show server_version_num").fetchone()[0])
        if not 160000 <= version < 170000:
            raise RuntimeError("This suite requires PostgreSQL 16")
        cls._bootstrap_parent_schema()

    def _reset_persistence(self):
        for signature in (
            "public.activate_rolling72_mvp_persistence_v1(text,text)",
            "public.issue_rolling72_mvp_persistence_v1(integer)",
            "public.score_rolling72_mvp_persistence_v1(integer)",
            "public.get_rolling72_mvp_persistence_v1_status()",
        ):
            self.db.execute(f"drop function if exists {signature} cascade")
        for suffix in (
            "score_attempts", "labels", "issue_attempts", "predictions",
            "issue_bundles", "runs", "lane",
        ):
            self.db.execute(f"drop table if exists private.{PERSIST}_{suffix} cascade")
        for suffix in ("immutable", "hash", "committed"):
            self.db.execute(f"drop function if exists private.{PERSIST}_{suffix} cascade")

    def setUp(self):
        # Install and activate the parent lane through its own immutable API.
        super().setUp()
        self._manifest_activate()
        self._reset_persistence()
        self.frozen_before = self._frozen_function_hashes()
        self.db.execute(MIGRATION.read_text())
        after = self._frozen_function_hashes()
        self.assertTrue(all(after.get(key) == digest for key, digest in self.frozen_before.items()),
                        "additive migration changed a preexisting function")
        self._activate_persistence()

    def _activate_persistence(self):
        source = self.db.execute("""
          select manifest_sha256,sql_sha256,max_fixtures,issue_until,scoring_until
          from private.rolling72_mvp_research_v1_lane
        """).fetchone()
        issue_until = source[3].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        scoring_until = source[4].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        manifest = {
            "lane_id": "rolling72-mvp-persistence-v1",
            "version": "rolling72-mvp-persistence-v1",
            "source_lane_id": "rolling72-mvp-research-v1",
            "source_family": "roboticket/roboticket",
            "unit": "available_total_seats",
            "method": "PERS",
            "horizons_hours": [24, 48, 72],
            "max_source_age_seconds": 3600,
            "max_issue_batch": 25,
            "max_score_batch": 100,
            "max_fixtures": source[2],
            "source_manifest_sha256": source[0],
            "source_sql_sha256": source[1],
            "sql_sha256": hashlib.sha256(MIGRATION.read_bytes()).hexdigest(),
            "issue_until": issue_until,
            "scoring_until": scoring_until,
        }
        self.persistence_manifest_text = json.dumps(manifest, separators=(",", ":"), sort_keys=True)
        self.persistence_manifest_sha = hashlib.sha256(
            self.persistence_manifest_text.encode("utf-8")
        ).hexdigest()
        self.activate_result = self._rpc(
            "activate_rolling72_mvp_persistence_v1",
            self.persistence_manifest_text,
            self.persistence_manifest_sha,
        )

    def _source_seal(self, *, available=0, kickoff_in_days=10, event_id=None):
        admission = self._admit_fixture(kickoff_in_days=kickoff_in_days, event_id=event_id)
        self._register(admission)
        snapshot = self._insert_bundle(admission, available=available)
        captured = self._capture()
        seal = self.db.execute("""
          select id,known_at,captured_at,read_completed_at,ticket_event_id
          from private.rolling72_mvp_research_v1_seals
          where snapshot_id=%s
        """, (snapshot,)).fetchone()
        self.assertIsNotNone(seal, f"source helper must produce a committed immutable seal: {captured!r}")
        return admission, seal

    def _past_score_fixture(self, *, issue_age_hours=27, actual=0, latest_invalid=False,
                            label_age_hours=1, after_target_seconds=0):
        """Seed consistent, synthetic past P0-4b/P0-4c rows; never update immutable rows."""
        admission = self._admit_fixture(kickoff_in_days=20)
        self._register(admission)
        ticket_event_id = admission["ticket_event_id"]
        now = self.db.execute("select clock_timestamp()").fetchone()[0]
        issued = now - timedelta(hours=issue_age_hours)
        origin_captured, origin_known = issued - timedelta(seconds=3), issued - timedelta(seconds=1)
        origin_snapshot = self._insert_bundle(
            admission, available=41, captured_at=origin_captured
        )
        origin_seal = self._synthetic_historical_seal(
            admission, origin_snapshot, captured_at=origin_captured,
            known_at=origin_known, available=41,
        )
        candidates = {}
        for horizon in (24, 48, 72):
            candidates[horizon] = self.db.execute("""
              insert into private.rolling72_mvp_research_v1_candidates
                (seal_id,ticket_event_id,horizon_hours,observation_known_at,provisional_target_at,status)
              values(%s,%s,%s,%s,%s,'SOURCE_ELIGIBLE') returning id
            """, (origin_seal, ticket_event_id, horizon, origin_known,
                  origin_known + timedelta(hours=horizon))).fetchone()[0]
        read_done = origin_known
        calc_done = issued - timedelta(milliseconds=1)
        bundle = self.db.execute(f"""
          insert into private.{PERSIST}_issue_bundles(
            seal_id,ticket_event_id,source_known_at,source_captured_at,source_read_completed_at,
            source_age_seconds,source_content_sha256,input_available_total,scope_status,sector_count,
            prior_sector_count,sector_count_delta,membership_change_count,transition,
            calculation_completed_at,read_completed_at,issued_at,kickoff_at)
          select s.id,s.ticket_event_id,s.known_at,s.captured_at,s.read_completed_at,
            extract(epoch from %s-s.captured_at),s.source_content_sha256,s.available_total,
            'NO_PRIOR',s.sector_count,null,null,0,s.transition,%s,%s,%s,r.kickoff_at
          from private.rolling72_mvp_research_v1_seals s
          join private.rolling72_mvp_research_v1_registry r using(ticket_event_id)
          where s.id=%s returning id
        """, (issued, calc_done, read_done, issued, origin_seal)).fetchone()[0]
        prediction_ids = {}
        for horizon in (24, 48, 72):
            target = issued + timedelta(hours=horizon)
            prediction_ids[horizon] = self.db.execute(f"""
              insert into private.{PERSIST}_predictions(
                bundle_id,candidate_id,ticket_event_id,horizon_hours,issued_at,target_at,kickoff_at,
                source_candidate_status,status,prediction,origin_available_total,source_seal_id,
                source_content_sha256,source_scope_status,source_sector_count,source_prior_sector_count,
                source_sector_count_delta,source_membership_change_count,source_transition)
              select %s,c.id,c.ticket_event_id,%s,%s,%s,r.kickoff_at,c.status,'ISSUED',41,41,
                s.id,s.source_content_sha256,'NO_PRIOR',s.sector_count,null,null,0,s.transition
              from private.rolling72_mvp_research_v1_candidates c
              join private.rolling72_mvp_research_v1_seals s on s.id=c.seal_id
              join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=c.ticket_event_id
              where c.id=%s returning id
            """, (bundle, horizon, issued, target, candidates[horizon])).fetchone()[0]
            self.db.execute(f"""
              insert into private.{PERSIST}_issue_attempts(
                candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,
                attempted_at,status,bundle_id,prediction_id)
              values(%s,%s,%s,%s,'SOURCE_ELIGIBLE',%s,'ISSUED',%s,%s)
            """, (candidates[horizon], ticket_event_id, origin_seal, horizon,
                  issued, bundle, prediction_ids[horizon]))
        target = issued + timedelta(hours=24)
        label_capture = (target + timedelta(seconds=after_target_seconds)
                         if after_target_seconds else target - timedelta(hours=label_age_hours))
        label_known = label_capture + timedelta(seconds=1)
        label_snapshot = self._insert_bundle(
            admission, available=actual, captured_at=label_capture
        )
        label_seal = self._synthetic_historical_seal(
            admission, label_snapshot, captured_at=label_capture,
            known_at=label_known, available=actual,
        )
        if latest_invalid:
            bad_capture = label_capture + timedelta(minutes=10)
            bad_snapshot = self._insert_bundle(
                admission, available=actual + 1, captured_at=bad_capture
            )
            self._synthetic_historical_attempt(
                admission, bad_snapshot, captured_at=bad_capture,
                known_at=bad_capture + timedelta(seconds=1), available=actual + 1,
                status="INVALID_SOURCE", reason="SYNTHETIC_LATEST_INVALID",
            )
        return {"admission": admission, "issued": issued, "prediction_id": prediction_ids[24],
                "label_seal": label_seal, "label_capture": label_capture}

    def _extra_historical_vintage(self, admission, *, issued, origin_value=41):
        """Add a second fully triplet-shaped due bundle for event-weighting tests."""
        captured, known = issued - timedelta(seconds=12), issued - timedelta(seconds=10)
        snapshot = self._insert_bundle(admission, available=origin_value, captured_at=captured)
        seal_id = self._synthetic_historical_seal(
            admission, snapshot, captured_at=captured, known_at=known, available=origin_value
        )
        candidate_ids = {}
        for horizon in (24, 48, 72):
            candidate_ids[horizon] = self.db.execute("""
              insert into private.rolling72_mvp_research_v1_candidates
                (seal_id,ticket_event_id,horizon_hours,observation_known_at,provisional_target_at,status)
              values(%s,%s,%s,%s,%s,'SOURCE_ELIGIBLE') returning id
            """, (seal_id, admission["ticket_event_id"], horizon,
                  known, known + timedelta(hours=horizon))).fetchone()[0]
        read_done, calculation_done = known, issued - timedelta(milliseconds=1)
        bundle_id = self.db.execute(f"""
          insert into private.{PERSIST}_issue_bundles(
            seal_id,ticket_event_id,source_known_at,source_captured_at,source_read_completed_at,
            source_age_seconds,source_content_sha256,input_available_total,scope_status,sector_count,
            prior_sector_count,sector_count_delta,membership_change_count,transition,
            calculation_completed_at,read_completed_at,issued_at,kickoff_at)
          select s.id,s.ticket_event_id,s.known_at,s.captured_at, s.read_completed_at,
            extract(epoch from %s-s.captured_at),s.source_content_sha256,s.available_total,
            'NO_PRIOR',s.sector_count,null,null,0,s.transition,%s,%s,%s,r.kickoff_at
          from private.rolling72_mvp_research_v1_seals s
          join private.rolling72_mvp_research_v1_registry r using(ticket_event_id)
          where s.id=%s returning id
        """, (issued, calculation_done, read_done, issued, seal_id)).fetchone()[0]
        result = {}
        for horizon in (24, 48, 72):
            target = issued + timedelta(hours=horizon)
            result[horizon] = self.db.execute(f"""
              insert into private.{PERSIST}_predictions(
                bundle_id,candidate_id,ticket_event_id,horizon_hours,issued_at,target_at,kickoff_at,
                source_candidate_status,status,prediction,origin_available_total,source_seal_id,
                source_content_sha256,source_scope_status,source_sector_count,source_prior_sector_count,
                source_sector_count_delta,source_membership_change_count,source_transition)
              select %s,c.id,c.ticket_event_id,%s,%s,%s,r.kickoff_at,c.status,'ISSUED',%s,%s,
                s.id,s.source_content_sha256,'NO_PRIOR',s.sector_count,null,null,0,s.transition
              from private.rolling72_mvp_research_v1_candidates c
              join private.rolling72_mvp_research_v1_seals s on s.id=c.seal_id
              join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=c.ticket_event_id
              where c.id=%s returning id
            """, (bundle_id, horizon, issued, target, origin_value, origin_value,
                  candidate_ids[horizon])).fetchone()[0]
            self.db.execute(f"""
              insert into private.{PERSIST}_issue_attempts(
                candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,
                attempted_at,status,bundle_id,prediction_id)
              values(%s,%s,%s,%s,'SOURCE_ELIGIBLE',%s,'ISSUED',%s,%s)
            """, (candidate_ids[horizon], admission["ticket_event_id"], seal_id,
                  horizon, issued, bundle_id, result[horizon]))
        return result[24]

    def _synthetic_historical_attempt(self, admission, snapshot_id, *, captured_at,
                                      known_at, available, status="READY", reason=None):
        run_id = uuid.uuid4()
        actual_now = self.db.execute("select clock_timestamp()").fetchone()[0]
        self.db.execute("""
          insert into private.rolling72_mvp_research_v1_runs
          values(%s,%s,%s,'COMPLETED',1,1)
        """, (run_id, actual_now, actual_now))
        attempt_id = self.db.execute("""
          select nextval(pg_get_serial_sequence(
            'private.rolling72_mvp_research_v1_attempts','id'))
        """).fetchone()[0]
        payload = self.db.execute("""
          select jsonb_build_object('lane_id','rolling72-mvp-research-v1',
            'source_family','roboticket/roboticket','unit','available_total_seats',
            'ticket_event_id',%s,'snapshot',jsonb_build_object('id',%s,
              'captured_at',%s,'available_total',%s))
        """, (admission["ticket_event_id"], snapshot_id, captured_at, available)).fetchone()[0]
        content_hash = self.db.execute(
            "select private.rolling72_mvp_research_v1_hash(%s)", (Jsonb(payload),)
        ).fetchone()[0]
        read_started, read_completed = captured_at - timedelta(seconds=1), captured_at
        binding = self.db.execute("""
          select jsonb_build_object('attempt_id',%s,'run_id',%s,
            'lane_id','rolling72-mvp-research-v1','ticket_event_id',%s,'snapshot_id',%s,
            'source_content_sha256',%s::text,'read_started_at',%s,'read_completed_at',%s,
            'known_at',%s,'status',%s::text,'reason',%s::text)
        """, (attempt_id, run_id, admission["ticket_event_id"], snapshot_id,
              content_hash, read_started, read_completed, known_at, status, reason)).fetchone()[0]
        binding_hash = self.db.execute(
            "select private.rolling72_mvp_research_v1_hash(%s)", (Jsonb(binding),)
        ).fetchone()[0]
        header = self.db.execute("select private.rolling72_mvp_research_v1_hash(%s)",
                                 (Jsonb({"snapshot_id": snapshot_id}),)).fetchone()[0]
        self.db.execute("""
          insert into private.rolling72_mvp_research_v1_attempts(
            id,run_id,ticket_event_id,snapshot_id,read_started_at,read_completed_at,known_at,
            captured_at,status,reason,source_content_sha256,snapshot_sha256,
            attempt_binding_sha256,raw_source,binding_payload)
          overriding system value values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (attempt_id, run_id, admission["ticket_event_id"], snapshot_id,
              read_started, read_completed, known_at, captured_at, status, reason,
              content_hash, header, binding_hash, Jsonb(payload), Jsonb(binding)))
        return attempt_id, content_hash, header, payload

    def _synthetic_unknown_capture_attempt(self, admission, *, known_at):
        """Append a committed INTERNAL_ERROR whose source capture clock is unknown."""
        run_id = uuid.uuid4()
        self.db.execute("""
          insert into private.rolling72_mvp_research_v1_runs
          values(%s,%s,%s,'COMPLETED',1,1)
        """, (run_id, known_at, known_at))
        attempt_id = self.db.execute("""
          select nextval(pg_get_serial_sequence(
            'private.rolling72_mvp_research_v1_attempts','id'))
        """).fetchone()[0]
        payload = {}
        content_hash = self.db.execute(
            "select private.rolling72_mvp_research_v1_hash(%s)", (Jsonb(payload),)
        ).fetchone()[0]
        read_started, read_completed = known_at - timedelta(seconds=2), known_at - timedelta(seconds=1)
        binding = self.db.execute("""
          select jsonb_build_object('attempt_id',%s,'run_id',%s,
            'lane_id','rolling72-mvp-research-v1','ticket_event_id',%s,'snapshot_id',null,
            'source_content_sha256',%s::text,'read_started_at',%s,'read_completed_at',%s,
            'known_at',%s,'status','INTERNAL_ERROR','reason','SYNTHETIC_CAPTURE_CLOCK_UNKNOWN')
        """, (attempt_id, run_id, admission["ticket_event_id"], content_hash,
              read_started, read_completed, known_at)).fetchone()[0]
        binding_hash = self.db.execute(
            "select private.rolling72_mvp_research_v1_hash(%s)", (Jsonb(binding),)
        ).fetchone()[0]
        self.db.execute("""
          insert into private.rolling72_mvp_research_v1_attempts(
            id,run_id,ticket_event_id,snapshot_id,read_started_at,read_completed_at,known_at,
            captured_at,status,reason,source_content_sha256,snapshot_sha256,
            attempt_binding_sha256,raw_source,binding_payload)
          overriding system value values(%s,%s,%s,null,%s,%s,%s,null,
            'INTERNAL_ERROR','SYNTHETIC_CAPTURE_CLOCK_UNKNOWN',%s,null,%s,%s,%s)
        """, (attempt_id, run_id, admission["ticket_event_id"], read_started,
              read_completed, known_at, content_hash, binding_hash, Jsonb(payload), Jsonb(binding)))

    def _synthetic_historical_seal(self, admission, snapshot_id, *, captured_at,
                                   known_at, available):
        attempt_id, content_hash, header, payload = self._synthetic_historical_attempt(
            admission, snapshot_id, captured_at=captured_at, known_at=known_at,
            available=available,
        )
        return self.db.execute("""
          insert into private.rolling72_mvp_research_v1_seals(
            ticket_event_id,snapshot_id,attempt_id,captured_at,read_started_at,read_completed_at,
            known_at,available_total,sector_count,source_content_sha256,snapshot_sha256,
            source_payload,phase,prior_seal_id,prior_status,transition_status,elapsed_capture_seconds,
            total_delta,common_sector_delta,added_available,removed_available,added_sector_count,
            removed_sector_count,price_area_membership_change_count,gap_count,transition)
          values(%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s,%s,'ISSUE_WINDOW',null,'NO_PRIOR',
            'NO_PRIOR',null,null,null,null,null,null,null,0,0,
            jsonb_build_object('prior_sector_count',null,'sector_count_delta',null,
              'price_area_membership_change_count',0)) returning id
        """, (admission["ticket_event_id"], snapshot_id, attempt_id, captured_at,
              captured_at - timedelta(seconds=1), captured_at, known_at, available,
              content_hash, header, Jsonb(payload))).fetchone()[0]

    def test_due_scorer_accepts_genuine_zero_label_and_keeps_it_immutable(self):
        fixture = self._past_score_fixture(actual=0)
        result = self._rpc("score_rolling72_mvp_persistence_v1", 100)
        self.assertEqual(result["labels"], 1)
        label = self.db.execute(f"""
          select actual_available_total,prediction,signed_error,absolute_error,
                 source_captured_at,scored_at
          from private.{PERSIST}_labels where prediction_id=%s
        """, (fixture["prediction_id"],)).fetchone()
        self.assertEqual(label[:4], (0, 41, 41, 41))
        self.assertLess(label[4], label[5])
        repeat = self._rpc("score_rolling72_mvp_persistence_v1", 100)
        self.assertEqual(repeat["labels"], 0)
        with self.assertRaises(psycopg.Error):
            self.db.execute(f"update private.{PERSIST}_labels set actual_available_total=1")

    def test_latest_invalid_source_refuses_without_backtracking_to_older_ready_seal(self):
        fixture = self._past_score_fixture(actual=0, latest_invalid=True)
        result = self._rpc("score_rolling72_mvp_persistence_v1", 100)
        self.assertEqual(result["labels"], 0)
        self.assertEqual(self.db.execute(f"""
          select status from private.{PERSIST}_score_attempts
          where prediction_id=%s order by id desc limit 1
        """, (fixture["prediction_id"],)).fetchone()[0], "SOURCE_INVALID")
        self.assertEqual(self.db.execute(f"select count(*) from private.{PERSIST}_labels").fetchone()[0], 0)

    def test_strict_postissue_posttarget_and_six_hour_target_age_boundaries(self):
        at_issue = self._past_score_fixture(label_age_hours=24)
        after_target = self._past_score_fixture(after_target_seconds=1)
        stale_at_target = self._past_score_fixture(label_age_hours=7)
        result = self._rpc("score_rolling72_mvp_persistence_v1", 100)
        self.assertEqual(result["labels"], 0)
        statuses = dict(self.db.execute(f"""
          select prediction_id,status from private.{PERSIST}_score_attempts
          where prediction_id = any(%s)
        """, ([at_issue["prediction_id"], after_target["prediction_id"],
               stale_at_target["prediction_id"]],)).fetchall())
        self.assertEqual(statuses[at_issue["prediction_id"]], "WAITING")
        self.assertEqual(statuses[after_target["prediction_id"]], "WAITING")
        self.assertEqual(statuses[stale_at_target["prediction_id"]], "SOURCE_STALE")

    def test_unresolved_unknown_capture_clock_refuses_instead_of_backtracking(self):
        fixture = self._past_score_fixture(actual=0)
        unknown_known = self.db.execute("select clock_timestamp()").fetchone()[0]
        self._synthetic_unknown_capture_attempt(fixture["admission"], known_at=unknown_known)
        result = self._rpc("score_rolling72_mvp_persistence_v1", 100)
        self.assertEqual(result["labels"], 0)
        status = self.db.execute(f"""
          select status from private.{PERSIST}_score_attempts
          where prediction_id=%s order by id desc limit 1
        """, (fixture["prediction_id"],)).fetchone()[0]
        self.assertEqual(status, "SOURCE_ORDER_UNKNOWN")

    def test_event_balanced_mae_weights_two_events_equally_despite_unequal_label_counts(self):
        event_a = self._past_score_fixture(actual=0)
        extra_prediction = self._extra_historical_vintage(
            event_a["admission"], issued=event_a["issued"]
        )
        self._past_score_fixture(actual=31)
        result = self._rpc("score_rolling72_mvp_persistence_v1", 100)
        self.assertEqual(result["labels"], 3)
        horizon = next(row for row in self._rpc("get_rolling72_mvp_persistence_v1_status")["scorecards"]
                       if row["horizon_hours"] == 24)
        self.assertEqual(horizon["labels"], 3)
        self.assertEqual(horizon["fixtures"], 2)
        # Event A contributes two errors of 41 (mean 41); event B contributes 10.
        self.assertAlmostEqual(float(horizon["event_balanced_mae"]), 25.5, places=6)
        self.assertNotEqual(extra_prediction, event_a["prediction_id"])

    def test_activation_is_idempotent_and_first_zero_point_is_one_immutable_triplet(self):
        repeated = self._rpc("activate_rolling72_mvp_persistence_v1",
                             self.persistence_manifest_text, self.persistence_manifest_sha)
        self.assertTrue(repeated["idempotent"])
        conflict_manifest = json.loads(self.persistence_manifest_text)
        conflict_manifest["sql_sha256"] = "0" * 64
        conflict_text = json.dumps(conflict_manifest, separators=(",", ":"), sort_keys=True)
        conflict_sha = hashlib.sha256(conflict_text.encode("utf-8")).hexdigest()
        with self.assertRaises(psycopg.Error):
            self._rpc("activate_rolling72_mvp_persistence_v1", conflict_text, conflict_sha)
        admission, seal = self._source_seal(available=0)
        barrier = threading.Barrier(2)
        def issue_concurrently():
            with psycopg.connect(self.dsn, autocommit=True) as conn:
                barrier.wait()
                return conn.execute(
                    "select public.issue_rolling72_mvp_persistence_v1(25)"
                ).fetchone()[0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: issue_concurrently(), range(2)))
        self.assertEqual(sum(r.get("processed_bundles", 0) for r in results), 1)
        self.assertEqual(sum(r.get("numeric_forecasts", 0) for r in results), 3)
        rows = self.db.execute(f"""
          select p.horizon_hours,p.status,p.prediction,p.issued_at,p.target_at,
                 b.source_read_completed_at,b.calculation_completed_at,b.source_known_at
          from private.{PERSIST}_predictions p
          join private.{PERSIST}_issue_bundles b on b.id=p.bundle_id
          where b.ticket_event_id=%s order by p.horizon_hours
        """, (admission["ticket_event_id"],)).fetchall()
        self.assertEqual([r[0] for r in rows], [24, 48, 72])
        self.assertEqual([r[1] for r in rows], ["ISSUED"] * 3)
        self.assertEqual([r[2] for r in rows], [0, 0, 0])
        self.assertTrue(all(r[4] == r[3] + timedelta(hours=r[0]) for r in rows))
        self.assertTrue(all(r[3] >= max(r[5], r[6], r[7]) for r in rows))
        self.assertEqual(len({r[3] for r in rows}), 1, "one actual issue clock per bundle")
        self.assertEqual(self.db.execute(
            f"select count(*) from private.{PERSIST}_issue_attempts"
        ).fetchone()[0], 3)
        retry = self._rpc("issue_rolling72_mvp_persistence_v1", 25)
        self.assertNotEqual(retry.get("processed"), 3)
        self.assertEqual(self.db.execute(
            f"select count(*) from private.{PERSIST}_predictions"
        ).fetchone()[0], 3)
        with self.assertRaises(psycopg.Error):
            self.db.execute(f"delete from private.{PERSIST}_predictions")

    def test_actual_kickoff_boundary_keeps_outside_horizon_null(self):
        # Kickoff two days away makes +48/+72 actual targets cross kickoff.
        admission, _ = self._source_seal(available=37, kickoff_in_days=2)
        result = self._rpc("issue_rolling72_mvp_persistence_v1", 25)
        self.assertEqual(result["status"], "COMPLETED")
        rows = self.db.execute(f"""
          select horizon_hours,status,prediction,target_at,kickoff_at
          from private.{PERSIST}_predictions order by horizon_hours
        """).fetchall()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0][1:3], ("ISSUED", 37))
        self.assertEqual(rows[1][1:3], ("OUTSIDE_KICKOFF", None))
        self.assertEqual(rows[2][1:3], ("OUTSIDE_KICKOFF", None))
        self.assertTrue(all(r[3] >= r[4] for r in rows[1:]))

    def test_stale_at_actual_issue_refuses_all_horizons_and_keeps_attempts_in_denominator(self):
        admission = self._admit_fixture(kickoff_in_days=10)
        self._register(admission)
        known = self.db.execute("select clock_timestamp()").fetchone()[0]
        captured = known - timedelta(seconds=3601)
        snapshot = self._insert_bundle(admission, available=9, captured_at=captured)
        seal_id = self._synthetic_historical_seal(
            admission, snapshot, captured_at=captured, known_at=known, available=9
        )
        for horizon in (24, 48, 72):
            self.db.execute("""
              insert into private.rolling72_mvp_research_v1_candidates(
                seal_id,ticket_event_id,horizon_hours,observation_known_at,provisional_target_at,status)
              values(%s,%s,%s,%s,%s,'SOURCE_ELIGIBLE')
            """, (seal_id, admission["ticket_event_id"], horizon, known,
                  known + timedelta(hours=horizon)))
        result = self._rpc("issue_rolling72_mvp_persistence_v1", 25)
        self.assertEqual(result["refused_candidates"], 3, repr(result))
        self.assertEqual(self.db.execute(f"""
          select count(*) from private.{PERSIST}_issue_attempts
          where status='REFUSED' and reason='SOURCE_STALE_AT_ISSUE'
        """).fetchone()[0], 3)
        self.assertEqual(self.db.execute(f"select count(*) from private.{PERSIST}_predictions").fetchone()[0], 0)

    def test_uncommitted_source_seal_is_invisible_and_retry_issues_after_commit(self):
        admission = self._admit_fixture(kickoff_in_days=10)
        self._register(admission)
        with psycopg.connect(self.dsn, autocommit=True) as observer:
            with self.db.transaction():
                captured = self.db.execute("select clock_timestamp()-interval '10 seconds'").fetchone()[0]
                known = self.db.execute("select clock_timestamp()").fetchone()[0]
                snapshot = self._insert_bundle(admission, available=12, captured_at=captured)
                seal_id = self._synthetic_historical_seal(
                    admission, snapshot, captured_at=captured, known_at=known, available=12
                )
                for horizon in (24, 48, 72):
                    self.db.execute("""
                      insert into private.rolling72_mvp_research_v1_candidates(
                        seal_id,ticket_event_id,horizon_hours,observation_known_at,
                        provisional_target_at,status)
                      values(%s,%s,%s,%s,%s,'SOURCE_ELIGIBLE')
                    """, (seal_id, admission["ticket_event_id"], horizon, known,
                          known + timedelta(hours=horizon)))
                observer.execute("set role service_role")
                hidden = observer.execute(
                    "select public.issue_rolling72_mvp_persistence_v1(25)"
                ).fetchone()[0]
                observer.execute("reset role")
                self.assertEqual(hidden["status"], "EMPTY")
            observer.execute("set role service_role")
            visible = observer.execute(
                "select public.issue_rolling72_mvp_persistence_v1(25)"
            ).fetchone()[0]
            observer.execute("reset role")
        self.assertEqual(visible["processed_bundles"], 1)
        self.assertEqual(self.db.execute(f"select count(*) from private.{PERSIST}_predictions").fetchone()[0], 3)

    def test_service_has_rpc_only_access_and_persistence_tables_are_immutable(self):
        for role in ("anon", "authenticated", "service_role"):
            self.db.execute(f"set role {role}")
            try:
                with self.assertRaises(psycopg.Error):
                    self.db.execute(f"select * from private.{PERSIST}_predictions")
            finally:
                self.db.execute("reset role")
        self.assertTrue(self.db.execute("""
          select has_function_privilege('service_role',
            'public.issue_rolling72_mvp_persistence_v1(integer)','EXECUTE')
        """).fetchone()[0])
        self.assertFalse(self.db.execute("""
          select has_function_privilege('anon',
            'public.issue_rolling72_mvp_persistence_v1(integer)','EXECUTE')
        """).fetchone()[0])
        status = self._rpc("get_rolling72_mvp_persistence_v1_status")
        self.assertEqual(len(status["scorecards"]), 3)
        self.assertTrue(all(row["event_balanced_mae"] is None
                            and row["event_balanced_bias"] is None
                            and row["labels"] == 0 for row in status["scorecards"]))


# Inherit fixture mechanics only; the P0-4b test methods are exercised by
# their own frozen suite, not duplicated here.
for _name in tuple(vars(Rolling72MvpResearchV1)):
    if _name.startswith("test_"):
        setattr(Rolling72MvpPersistenceV1, _name, None)
del Rolling72MvpResearchV1


if __name__ == "__main__":
    unittest.main()
