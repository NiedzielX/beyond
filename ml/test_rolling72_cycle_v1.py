"""Bounded mocked source cycles; no network or real forecast-ledger writes."""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from datetime import timedelta
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_cycle_v1 import BoundedReader, cycle, due_status
from ml.rolling72_shadow_ledger_v1 import capture, create_freeze, report
from ml.test_rolling72_backup_v1 import MemoryStorage
from ml.test_rolling72_shadow_ledger_v1 import BASE


@contextmanager
def clocks(value):
    getter = value if callable(value) else lambda: value
    with ExitStack() as stack:
        for module in ("ml.rolling72_cycle_v1", "ml.rolling72_shadow_ledger_v1", "ml.rolling72_backup_v1"):
            stack.enter_context(patch(module + "._now", side_effect=getter))
        yield


def payload():
    events = []
    for event_id, club, provider, source, start in ((24, "club-a", "roboticket", "roboticket", 0),
                                                   (10500, "club-b", "stellis", "stellis_visible_available", 100)):
        events.append({"ticket_event_id": event_id, "club_slug": club, "provider": provider,
                       "source_domain": club + ".test", "external_event_id": "source-" + str(event_id),
                       "kickoff_at": (BASE + timedelta(days=50)).isoformat(), "competition": "league",
                       "home_team": club, "away_team": "opponent",
                       "observations": [{"snapshot_id": start + i,
                            "captured_at": (BASE - timedelta(hours=age)).isoformat(),
                            "available_total": value, "measurement_key": provider + "/" + source,
                            "source": source, "sector_count": 2}
                            for i, age, value in ((1, 48, 1480), (2, 25, 1250), (3, 12, 1120), (4, 0, 1000))]})
    data = {"version": "daily-inventory-public-export-v1", "exported_at": BASE.isoformat(),
            "retrieved_at": (BASE + timedelta(minutes=1)).isoformat(), "events": events}
    data["export_sha256"] = _hash(data)
    return json.dumps(data).encode()


class Reader:
    def __init__(self, metadata, rows=None, callback=None):
        self.metadata = deepcopy(metadata)
        self.new_rows = rows or {}
        self.callback = callback
        self.calls = []

    def rows(self, table, parameters):
        self.calls.append((table, deepcopy(parameters)))
        if self.callback:
            self.callback(table)
        if table == "ticket_events":
            return deepcopy(self.metadata)
        parameters = dict(parameters)
        identity = int(parameters["ticket_event_id"].removeprefix("eq."))
        return deepcopy(self.new_rows.get(identity, []))


class Rolling72CycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.database = self.root / "shadow.sqlite"
        self.source = self.root / "seed-source.json"
        self.source.write_bytes(payload())
        self.registry = self.root / "identity-registry.json"
        self.metadata = [{"id": e["ticket_event_id"], **{k: v for k, v in e.items()
                         if k not in ("ticket_event_id", "observations")}}
                         for e in json.loads(payload())["events"]]
        self.registry.write_text(json.dumps(self.metadata))
        self.freeze = self.root / "freeze.json"
        with clocks(BASE + timedelta(minutes=2)):
            create_freeze(self.freeze)
        self.issued = BASE + timedelta(minutes=3)
        with clocks(self.issued):
            capture(self.database, payload(), self.freeze)
        self.runtime = self.root / "runtime"
        self.until = BASE + timedelta(hours=72)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cycle(self, now, reader=None, storage=None, **kwargs):
        with clocks(now):
            return cycle(self.database, self.source, self.registry, self.freeze, self.runtime,
                         kwargs.pop("until", self.until), reader=reader,
                         storage=storage or MemoryStorage(), **kwargs)

    def increments(self, now):
        target = self.issued + timedelta(hours=24)
        rows = {}
        for event_id, start, source in ((24, 0, "roboticket"), (10500, 100, "stellis_visible_available")):
            rows[event_id] = [{"id": start + identifier, "ticket_event_id": event_id,
                              "captured_at": captured.isoformat(), "available_total": value,
                              "source": source, "sector_count": 2}
                             for identifier, captured, value in ((5, target - timedelta(minutes=1), 800),
                                                                 (6, now - timedelta(minutes=1), 790))]
        return rows

    def test_not_due_does_not_construct_reader_or_touch_network(self):
        with patch("ml.rolling72_cycle_v1.BoundedReader", side_effect=AssertionError("network forbidden")):
            result = self.run_cycle(BASE + timedelta(hours=1))
        self.assertEqual(result["status"], "NOT_DUE")
        self.assertEqual(result["network_reads"], 0)
        self.assertEqual(json.loads((self.runtime / "audit.jsonl").read_text())["status"], "NOT_DUE")
        with clocks(BASE + timedelta(hours=1)):
            self.assertEqual(report(self.database)["numeric_forecasts"], 12)

    def test_ten_minute_grace_is_exact_for_capture_and_target(self):
        before = due_status(self.database, self.issued + timedelta(hours=24, minutes=9, seconds=59))
        at = due_status(self.database, self.issued + timedelta(hours=24, minutes=10))
        self.assertFalse(before["due"])
        self.assertEqual(at["capture_event_ids"], [24, 10500])
        self.assertEqual(len(at["mature_unmatched_targets"]), 2)

    def test_due_cycle_scores_then_issues_actual_new_vintage_and_backs_up(self):
        now = self.issued + timedelta(hours=24, minutes=11)
        reader = Reader(self.metadata, self.increments(now))
        storage = MemoryStorage()
        result = self.run_cycle(now, reader, storage)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["network_reads"], 3)
        self.assertEqual(result["incremental_snapshot_count"], 4)
        self.assertEqual(result["scoring"]["accepted_targets"], 2)
        self.assertEqual(result["scoring"]["added_scores"], 4)
        self.assertEqual(result["capture"]["issued_at"], now.isoformat())
        self.assertEqual(result["capture"]["numeric_forecast_count"], 12)
        self.assertTrue(result["backup"]["independent_restore_verified"])
        with clocks(now):
            self.assertEqual(report(self.database)["numeric_forecasts"], 24)
        self.assertTrue((self.runtime / "current-feed.json").exists())
        state = json.loads((self.runtime / "state.json").read_text())
        self.assertEqual(state["checkpoint"]["scores"], 4)
        self.assertEqual(len(state["source_paths"]), 2)
        for table, params in reader.calls[1:]:
            self.assertEqual(table, "snapshots")
            query = dict(params)
            self.assertEqual(query["limit"], "500")
            self.assertIn(query["id"], ("gt.4", "gt.104"))
            self.assertTrue(query["captured_at"].startswith("lte."))

    def test_explicit_capture_works_before_daily_due_and_keeps_old_rows(self):
        now = BASE + timedelta(hours=1)
        result = self.run_cycle(now, Reader(self.metadata), capture_now=True)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["capture"]["input_issue_count"], 2)
        self.assertEqual(result["capture"]["issued_at"], now.isoformat())
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute("select count(*) from issues where issued_at=?", (self.issued.isoformat(),)).fetchone()[0], 2)

    def test_source_identity_mismatch_fails_before_snapshot_queries(self):
        metadata = deepcopy(self.metadata)
        metadata[0]["external_event_id"] = "different-fixture"
        reader = Reader(metadata)
        result = self.run_cycle(BASE + timedelta(hours=1), reader, capture_now=True)
        self.assertEqual(result["status"], "FAILED_CLOSED")
        self.assertEqual(result["failure_stage"], "source_read")
        self.assertEqual(result["network_reads"], 1)
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute("select count(*) from sources").fetchone()[0], 1)

    def test_snapshot_cap_and_future_capture_abort_without_ledger_writes(self):
        cap_reader = Reader(self.metadata, {24: [{}] * 500})
        result = self.run_cycle(BASE + timedelta(hours=1), cap_reader, capture_now=True)
        self.assertEqual(result["status"], "FAILED_CLOSED")
        self.assertEqual(result["network_reads"], 2)
        future = {24: [{"id": 5, "ticket_event_id": 24,
                        "captured_at": (BASE + timedelta(hours=2)).isoformat(),
                        "available_total": 900, "source": "roboticket", "sector_count": 2}]}
        result = self.run_cycle(BASE + timedelta(hours=1, minutes=1), Reader(self.metadata, future), capture_now=True)
        self.assertEqual(result["status"], "FAILED_CLOSED")
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute("select count(*) from issues").fetchone()[0], 2)

    def test_failed_due_read_is_throttled_locally_without_minute_polling(self):
        now = self.issued + timedelta(hours=24, minutes=11)
        metadata = deepcopy(self.metadata)
        metadata[0]["source_domain"] = "wrong.test"
        reader = Reader(metadata)
        self.assertEqual(self.run_cycle(now, reader)["status"], "FAILED_CLOSED")
        result = self.run_cycle(now + timedelta(minutes=1), reader)
        self.assertEqual(result["status"], "RETRY_INTERVAL_NOT_DUE")
        self.assertEqual(result["network_reads"], 0)
        self.assertEqual(len(reader.calls), 1)

    def test_committed_ledger_recovers_backup_without_duplicate_forecasts(self):
        now = BASE + timedelta(hours=1)
        failed = self.run_cycle(now, Reader(self.metadata), MemoryStorage(corrupt_second_read=True), capture_now=True)
        self.assertEqual(failed["status"], "FAILED_CLOSED")
        self.assertEqual(failed["failure_stage"], "feed_and_private_backup")
        with patch("ml.rolling72_cycle_v1.BoundedReader", side_effect=AssertionError("no source repoll")):
            result = self.run_cycle(now + timedelta(minutes=1))
        self.assertEqual(result["status"], "RECOVERED_COMMITTED_LEDGER")
        self.assertEqual(result["network_reads"], 0)
        with clocks(now + timedelta(minutes=1)):
            self.assertEqual(report(self.database)["numeric_forecasts"], 24)
        self.assertTrue(result["backup"]["independent_restore_verified"])
        state = json.loads((self.runtime / "state.json").read_text())
        self.assertNotIn("failure_stage", state)

    def test_failed_recovery_never_repolls_source_or_reissues_forecast(self):
        now = BASE + timedelta(hours=1)
        self.run_cycle(now, Reader(self.metadata), MemoryStorage(corrupt_second_read=True), capture_now=True)
        with patch("ml.rolling72_cycle_v1.BoundedReader", side_effect=AssertionError("no source repoll")):
            failed = self.run_cycle(now + timedelta(minutes=1), storage=MemoryStorage(corrupt_second_read=True))
        self.assertEqual(failed["status"], "FAILED_CLOSED")
        self.assertEqual(failed["failure_stage"], "recover_committed_ledger")
        self.assertEqual(failed["network_reads"], 0)
        with clocks(now + timedelta(minutes=1)):
            self.assertEqual(report(self.database)["numeric_forecasts"], 24)

    def test_explicit_falsey_reader_never_falls_back_to_real_network(self):
        class FalseyReader(Reader):
            def __bool__(self):
                return False
        reader = FalseyReader(self.metadata)
        with patch("ml.rolling72_cycle_v1.BoundedReader", side_effect=AssertionError("fake reader must be used")):
            result = self.run_cycle(BASE + timedelta(hours=1), reader, capture_now=True)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(len(reader.calls), 3)

    def test_only_due_fixture_gets_a_new_capture(self):
        subset = json.loads(payload())
        subset["events"] = [subset["events"][1]]
        subset["export_sha256"] = _hash({k: v for k, v in subset.items() if k != "export_sha256"})
        subset_path = self.root / "subset-original.json"
        subset_path.write_text(json.dumps(subset))
        later = self.issued + timedelta(hours=1)
        with clocks(later):
            capture(self.database, subset_path.read_bytes(), self.freeze)
        now = self.issued + timedelta(hours=24, minutes=11)
        result = self.run_cycle(now, Reader(self.metadata, self.increments(now)))
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["capture"]["input_issue_count"], 1)
        with sqlite3.connect(self.database) as db:
            latest = dict(db.execute("select event_id,max(issued_at) from issues group by event_id"))
        self.assertEqual(latest[24], now.isoformat())
        self.assertEqual(latest[10500], later.isoformat())

    def test_contract_and_deadline_cannot_silently_change(self):
        now = BASE + timedelta(hours=1)
        self.run_cycle(now)
        with self.assertRaisesRegex(ValueError, "contract changed"):
            self.run_cycle(now + timedelta(minutes=1), until=self.until - timedelta(hours=1))
        with self.assertRaisesRegex(ValueError, "within72hours"):
            self.run_cycle(now, until=now + timedelta(hours=73))
        expired = self.run_cycle(self.until)
        self.assertEqual(expired["status"], "DEADLINE_EXPIRED")
        self.assertEqual(expired["network_reads"], 0)
        self.assertEqual(json.loads((self.runtime / "audit.jsonl").read_text().splitlines()[-1])["status"], "DEADLINE_EXPIRED")

    def test_deadline_expiring_during_reads_prevents_score_or_capture(self):
        clock = {"now": BASE + timedelta(hours=1)}
        until = clock["now"] + timedelta(minutes=1)
        reader = Reader(self.metadata, callback=lambda table: clock.update(now=until + timedelta(seconds=1)))
        result = self.run_cycle(lambda: clock["now"], reader, capture_now=True, until=until)
        self.assertEqual(result["status"], "FAILED_CLOSED")
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute("select count(*) from sources").fetchone()[0], 1)

    def test_frozen_code_mismatch_is_checked_before_source_access(self):
        data = json.loads(self.freeze.read_text())
        data["code_sha256"]["ml/demand_engine/rolling72_features_v1.py"] = "0" * 64
        data["freeze_sha256"] = _hash({k: v for k, v in data.items() if k != "freeze_sha256"})
        self.freeze.write_text(json.dumps(data))
        reader = Reader(self.metadata)
        with self.assertRaisesRegex(ValueError, "code changed"):
            self.run_cycle(BASE + timedelta(hours=1), reader, capture_now=True)
        self.assertEqual(reader.calls, [])

    def test_duplicate_incremental_snapshot_owner_fails_transactionally(self):
        now = self.issued + timedelta(hours=24, minutes=11)
        rows = self.increments(now)
        rows[10500][0]["id"] = rows[24][0]["id"]
        # The second fixture's ID5 is below its declared cursor104 and must fail before scoring.
        result = self.run_cycle(now, Reader(self.metadata, rows))
        self.assertEqual(result["status"], "FAILED_CLOSED")
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute("select count(*) from scores").fetchone()[0], 0)

    def test_default_reader_demands_an_exact_untruncated_count(self):
        class Response(io.BytesIO):
            def __init__(self, rows, total):
                super().__init__(json.dumps(rows).encode())
                self.headers = {"Content-Range": "0-0/" + str(total)}
        reader = BoundedReader.__new__(BoundedReader)
        reader.base, reader.headers = "https://synthetic.test", {}
        with patch("ml.rolling72_cycle_v1.urllib.request.urlopen", return_value=Response([{"id": 1}], 1)):
            self.assertEqual(reader.rows("snapshots", [("id", "gt.0"), ("limit", "500")]), [{"id": 1}])
        with patch("ml.rolling72_cycle_v1.urllib.request.urlopen", return_value=Response([{"id": 1}], 2)):
            with self.assertRaisesRegex(ValueError, "truncated"):
                reader.rows("snapshots", [("limit", "500")])


if __name__ == "__main__":
    unittest.main()
