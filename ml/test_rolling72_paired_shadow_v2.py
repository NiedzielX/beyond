"""Synthetic-only actual-time integration of the independent paired ledger."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from threadpoolctl import threadpool_limits

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_offline_challenger_v2 import fit_once
from ml.rolling72_paired_shadow_v2 import APPLICATION_ID, capture, create_freeze, report, score
from ml.test_rolling72_offline_challenger_v2 import synthetic_dataset


BASE = datetime.now(timezone.utc) + timedelta(minutes=5)
REGISTRY = json.dumps([{"id": event, "provider": "roboticket", "club_slug": f"club-{event}",
                       "external_event_id": str(event), "source_domain": "synthetic.example"}
                      for event in (999, 1000)]).encode()


def source(at=None, *, event_ids=(999,), single=False):
    at = at or BASE
    rows = ((4, 0, 1000),) if single else ((1, 48, 1480), (2, 25, 1250), (3, 12, 1120), (4, 0, 1000))
    data = {"version": "daily-inventory-public-export-v1", "exported_at": at.isoformat(),
            "retrieved_at": (at + timedelta(seconds=1)).isoformat(), "events": []}
    for event in event_ids:
        data["events"].append({"ticket_event_id": event, "club_slug": f"club-{event}", "provider": "roboticket",
                               "kickoff_at": (BASE + timedelta(days=50)).isoformat(),
                               "observations": [{"snapshot_id": event * 100 + i,
                                   "captured_at": (at - timedelta(hours=age)).isoformat(), "available_total": value,
                                   "measurement_key": "roboticket/roboticket"} for i, age, value in rows]})
    return encode(data)


def encode(data):
    data["export_sha256"] = _hash({k: v for k, v in data.items() if k != "export_sha256"})
    return json.dumps(data).encode()


def later_source(target, *, value=800, extra=None, event_ids=(999,)):
    data = json.loads(source(event_ids=event_ids))
    for event in data["events"]:
        event["observations"].append({"snapshot_id": event["ticket_event_id"] * 100 + 5,
                                     "captured_at": (target - timedelta(minutes=1)).isoformat(),
                                     "available_total": value, "measurement_key": "roboticket/roboticket"})
        if extra:
            event["observations"].extend(deepcopy(extra))
    data["exported_at"] = (target + timedelta(minutes=1)).isoformat()
    data["retrieved_at"] = (target + timedelta(minutes=2)).isoformat()
    return encode(data)


@contextmanager
def clock(at):
    with patch("ml.rolling72_paired_shadow_v2._now", return_value=at), \
         patch("ml.rolling72_offline_challenger_v2._now", return_value=at), threadpool_limits(limits=1):
        yield


class PairedShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = tempfile.TemporaryDirectory()
        cls.artifact = Path(cls.models.name) / "synthetic-model"
        with threadpool_limits(limits=1):
            fit_once(cls.artifact, synthetic_dataset(), synthetic_test=True)

    @classmethod
    def tearDownClass(cls):
        cls.models.cleanup()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.db = self.root / "paired-v2.sqlite"
        self.freeze = self.root / "freeze.json"
        with clock(BASE - timedelta(seconds=1)):
            create_freeze(self.freeze, self.artifact, REGISTRY, synthetic_test=True)
        self.issued = BASE + timedelta(seconds=2)

    def tearDown(self):
        self.folder.cleanup()

    def capture(self, payload=None, *, at=None, **kwargs):
        with clock(at or self.issued):
            return capture(self.db, payload or source(), self.artifact, self.freeze, REGISTRY,
                           synthetic_test=True, **kwargs)

    def score(self, payload, at):
        with clock(at):
            return score(self.db, payload, self.artifact, self.freeze, REGISTRY, synthetic_test=True)

    def test_exact_actual_time_pairing_and_no_mae_before_targets(self):
        result = self.capture()
        self.assertEqual(result["numeric_forecast_count"], 9)
        self.assertEqual(result["prediction_status_rows"], 12)
        self.assertEqual(result["issued_at"], self.issued.isoformat())
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("pragma application_id").fetchone()[0], APPLICATION_ID)
            self.assertEqual(db.execute("pragma foreign_key_check").fetchall(), [])
            points = db.execute("select horizon,target_at,payload_json from predictions where prediction is not null").fetchall()
            manifests = {json.loads(payload)["input_manifest_sha256"] for _, _, payload in points}
            self.assertEqual(len(manifests), 1)
            for h, target, _ in points:
                self.assertEqual(target, (self.issued + timedelta(hours=h)).isoformat())
        with clock(self.issued):
            summary = report(self.db)
        self.assertEqual(summary["pending_targets"], 3)
        self.assertEqual(summary["scores"], 0)
        self.assertEqual(summary["metrics"], {})
        self.assertIsNone(summary["paired_metrics"]["+72h/candidate-vs-persistence"]["candidate"]["event_balanced_mae"])
        self.assertEqual(summary["review_eligible_new_fixtures"], 0)
        self.assertEqual(summary["formal_review_gate"], "CLOSED")

    def test_one_real_point_issues_model_and_persistence_without_fake_drift(self):
        result = self.capture(source(single=True))
        self.assertEqual(result["numeric_forecast_count"], 6)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select count(*) from predictions where model='drift' and prediction is null").fetchone()[0], 3)

    def test_same_issue_refused_and_old_forecasts_unchanged_after_new_issue(self):
        self.capture()
        with sqlite3.connect(self.db) as db:
            original = db.execute("select * from predictions order by horizon,model").fetchall()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.capture()
        self.capture(at=self.issued + timedelta(minutes=1))
        with sqlite3.connect(self.db) as db:
            self.assertEqual(original, db.execute("select * from predictions where issued_at=? order by horizon,model", (self.issued.isoformat(),)).fetchall())

    def test_original_bytes_and_original_receipt_clock_required(self):
        with self.assertRaisesRegex(ValueError, "bytes required"):
            self.capture(source().decode())
        bad = json.loads(source()); bad["retrieved_at"] = (self.issued + timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(ValueError, "before the original receipt"):
            self.capture(encode(bad))
        self.assertFalse(self.db.exists())

    def test_synthetic_model_and_freeze_are_not_servable_by_default(self):
        with clock(self.issued), self.assertRaises(ValueError):
            capture(self.db, source(), self.artifact, self.freeze, REGISTRY)
        self.assertFalse(self.db.exists())

    def test_foreign_ledger_and_bad_freeze_never_replace_old_data(self):
        with sqlite3.connect(self.db) as db:
            db.execute("create table old_forecasts (value text)")
            db.execute("insert into old_forecasts values ('keep')")
        with self.assertRaisesRegex(ValueError, "foreign/frozen"):
            self.capture()
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select * from old_forecasts").fetchall(), [("keep",)])
        body = json.loads(self.freeze.read_text()); body["code_sha256"]["ml/rolling72_paired_shadow_v2.py"] = "0" * 64
        body["freeze_sha256"] = _hash({k: v for k, v in body.items() if k != "freeze_sha256"})
        self.freeze.write_text(json.dumps(body))
        with self.assertRaisesRegex(ValueError, "code changed"):
            self.capture()

    def test_late_freeze_and_excess_actual_write_window_are_refused(self):
        with self.assertRaisesRegex(ValueError, "precede actual execution"):
            self.capture(at=BASE - timedelta(seconds=1))
        with patch("ml.rolling72_paired_shadow_v2._now", side_effect=[self.issued, self.issued + timedelta(seconds=91)]), \
             patch("ml.rolling72_offline_challenger_v2._now", return_value=self.issued), threadpool_limits(limits=1):
            with self.assertRaisesRegex(ValueError, "write allowance"):
                capture(self.db, source(), self.artifact, self.freeze, REGISTRY, synthetic_test=True)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select count(*) from issues").fetchone()[0], 0)
            self.assertEqual(db.execute("select count(*) from sources").fetchone()[0], 0)

    def test_written_at_uses_post_insert_actual_clock(self):
        written = self.issued + timedelta(seconds=25)
        with patch("ml.rolling72_paired_shadow_v2._now", side_effect=[self.issued, written]), \
             patch("ml.rolling72_offline_challenger_v2._now", return_value=self.issued), threadpool_limits(limits=1):
            result = capture(self.db, source(), self.artifact, self.freeze, REGISTRY, synthetic_test=True)
        self.assertEqual(result["written_at"], written.isoformat())
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select written_at from issues").fetchone()[0], written.isoformat())

    def test_max_one_hour_gate_applies_to_every_model_without_fake_zero(self):
        self.capture(at=BASE + timedelta(hours=1, seconds=1))
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select count(*) from predictions where prediction is not null").fetchone()[0], 0)
            self.assertTrue(all(json.loads(row[0])["reason"] == "STALE_INPUT_FOR_V2" for row in db.execute("select payload_json from predictions")))

    def test_old_incompatible_segment_is_retained_but_not_fed_to_model(self):
        data = json.loads(source())
        data["events"][0]["observations"][0]["measurement_key"] = "roboticket/other-scope"
        self.capture(encode(data))
        with sqlite3.connect(self.db) as db:
            issue, lineage = map(json.loads, db.execute("select issue_json,lineage_json from issues").fetchone())
            self.assertEqual(len(issue["observed_prefix"]), 3)
            self.assertEqual(lineage["prior_incompatible_rows_retained"], 1)
            self.assertEqual(len(lineage["raw_received_snapshot_ids"]), 4)
            self.assertEqual(db.execute("select count(*) from source_observations").fetchone()[0], 4)

    def test_invalid_current_segment_is_not_cleaned_away(self):
        data = json.loads(source()); data["events"][0]["observations"][1]["available_total"] = None
        result = self.capture(encode(data))
        self.assertEqual(result["numeric_forecast_count"], 0)
        with sqlite3.connect(self.db) as db:
            issue = json.loads(db.execute("select issue_json from issues").fetchone()[0])
            self.assertEqual(issue["status"], "INVALID_OBSERVATION")

    def test_registry_source_identity_and_duplicate_snapshot_fail_closed(self):
        data = json.loads(source()); data["events"][0]["provider"] = "wrong"
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.capture(encode(data))
        data = json.loads(source()); data["events"][0]["observations"].append(deepcopy(data["events"][0]["observations"][-1]))
        with self.assertRaisesRegex(ValueError, "Duplicate snapshot"):
            self.capture(encode(data))
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select count(*) from sources").fetchone()[0], 0)

    def test_present_domain_and_external_id_must_match_registry_exactly(self):
        for key, value in (("source_domain", "wrong.example"), ("external_event_id", "wrong"),
                           ("source_domain", None), ("external_event_id", True),
                           ("source_url", "https://wrong.example/event")):
            data = json.loads(source()); data["events"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, "identity mismatch"):
                self.capture(encode(data))
        data = json.loads(source())
        data["events"][0].update({"source_domain": "SYNTHETIC.EXAMPLE", "external_event_id": 999})
        self.assertEqual(self.capture(encode(data))["numeric_forecast_count"], 9)

    def test_conflicting_supplied_domain_and_url_cannot_hide_wrong_identity(self):
        data = json.loads(source())
        data["events"][0].update({"source_domain": "synthetic.example", "source_url": "https://wrong.example/event"})
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.capture(encode(data))
        self.assertFalse(self.db.exists())

    def test_early_source_never_scores_future_target(self):
        self.capture()
        result = self.score(source(), self.issued + timedelta(hours=1))
        self.assertEqual(result["accepted_targets"], 0)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select count(*) from scores").fetchone()[0], 0)

    def test_genuine_first_label_scores_same_pairs_and_stays_immutable(self):
        self.capture()
        target = self.issued + timedelta(hours=24)
        result = self.score(later_source(target), target + timedelta(minutes=3))
        self.assertEqual(result["accepted_targets"], 1)
        self.assertEqual(result["added_scores"], 3)
        with sqlite3.connect(self.db) as db:
            original = db.execute("select * from scores order by model").fetchall()
            label = db.execute("select label_json from target_matches").fetchone()[0]
        newer = json.loads(later_source(target))
        newer["events"][0]["observations"].append({"snapshot_id": 99906, "captured_at": target.isoformat(),
            "available_total": 900, "measurement_key": "roboticket/roboticket"})
        self.assertEqual(self.score(encode(newer), target + timedelta(minutes=4))["accepted_targets"], 0)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(original, db.execute("select * from scores order by model").fetchall())
            self.assertEqual(label, db.execute("select label_json from target_matches").fetchone()[0])
        with clock(target + timedelta(minutes=4)):
            summary = report(self.db)
        pair = summary["paired_metrics"]["+24h/candidate-vs-persistence"]
        self.assertEqual(pair["baseline"]["event_balanced_mae"], 200)
        self.assertEqual(pair["candidate"]["scored_points"], 1)
        self.assertAlmostEqual(pair["event_balanced_mae_difference_candidate_minus_baseline"],
                               pair["candidate"]["event_balanced_mae"] - 200)

    def test_changed_old_snapshot_rejected_and_entire_score_transaction_rolls_back(self):
        self.capture(); target = self.issued + timedelta(hours=24)
        data = json.loads(later_source(target)); data["events"][0]["observations"][0]["available_total"] += 1
        with self.assertRaisesRegex(ValueError, "snapshot payload conflict"):
            self.score(encode(data), target + timedelta(minutes=3))
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select count(*) from sources").fetchone()[0], 1)
            self.assertEqual(db.execute("select count(*) from scores").fetchone()[0], 0)

    def test_intervening_scope_change_even_if_it_returns_blocks_target(self):
        self.capture(); target = self.issued + timedelta(hours=24)
        extra = [{"snapshot_id": 99906, "captured_at": (target - timedelta(hours=1)).isoformat(),
                  "available_total": 850, "measurement_key": "roboticket/other-scope"}]
        result = self.score(later_source(target, extra=extra), target + timedelta(minutes=3))
        self.assertEqual(result["accepted_targets"], 0)
        with sqlite3.connect(self.db) as db:
            self.assertIn(("MEASUREMENT_CHANGED",), db.execute("select status from scoring_attempts").fetchall())

    def test_invalid_intermediate_state_blocks_good_endpoint(self):
        self.capture(); target = self.issued + timedelta(hours=24)
        extra = [{"snapshot_id": 99906, "captured_at": (target - timedelta(hours=1)).isoformat(),
                  "available_total": None, "measurement_key": "roboticket/roboticket"}]
        self.assertEqual(self.score(later_source(target, extra=extra), target + timedelta(minutes=3))["accepted_targets"], 0)
        with sqlite3.connect(self.db) as db:
            self.assertIn(("TARGET_INTERVAL_UNUSABLE",), db.execute("select status from scoring_attempts").fetchall())

    def test_report_weights_independent_fixtures_equally_and_pairs_exact_coordinates(self):
        self.capture(source(event_ids=(999, 1000)))
        target = self.issued + timedelta(hours=24)
        payload = json.loads(later_source(target, event_ids=(999, 1000)))
        payload["events"][1]["observations"][-1]["available_total"] = 950
        self.score(encode(payload), target + timedelta(minutes=3))
        # Second issue for only fixture999, later genuine target; same original first-point data.
        issued2 = self.issued + timedelta(minutes=10)
        self.capture(source(), at=issued2)
        target2 = issued2 + timedelta(hours=24)
        data2 = json.loads(later_source(target2))
        # Preserve already received target identity; add new target value with a new ID.
        data2["events"][0]["observations"][-1] = json.loads(later_source(target))["events"][0]["observations"][-1]
        data2["events"][0]["observations"].append({"snapshot_id": 99906, "captured_at": (target2 - timedelta(minutes=1)).isoformat(),
            "available_total": 800, "measurement_key": "roboticket/roboticket"})
        self.score(encode(data2), target2 + timedelta(minutes=3))
        with clock(target2 + timedelta(minutes=4)):
            summary = report(self.db)
        persistence = summary["metrics"]["+24h/persistence"]
        self.assertEqual(persistence["scored_fixtures"], 2)
        self.assertEqual(persistence["scored_points"], 3)
        self.assertEqual(persistence["event_balanced_mae"], 125)
        self.assertEqual(summary["paired_metrics"]["+24h/candidate-vs-persistence"]["candidate"]["scored_points"], 3)


if __name__ == "__main__":
    unittest.main()
