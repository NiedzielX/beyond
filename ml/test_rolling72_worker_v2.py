"""Bounded cloud lifecycle without actual waiting, source calls or forecast writes."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import threading
import unittest

from ml.rolling72_worker_v2 import run_worker


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.paths = [self.root / name for name in ("ledger", "source", "model", "registry", "freeze")]
        for path in [self.paths[i] for i in (0,1,3,4)]:
            path.write_text('{}')
        self.paths[2].mkdir()
        for name in ('manifest.json','fit-marker.json','model.joblib'):
            (self.paths[2]/name).write_text('{}')
        self.at = datetime(2026, 11, 8, 23, tzinfo=timezone.utc)

    def tearDown(self):
        self.tmp.cleanup()

    def run_with(self, **overrides):
        options = {"clock": lambda: self.at, "wait": lambda seconds: setattr(self, "at", self.at + timedelta(seconds=seconds)),
                   "cycle_fn": lambda *args: {"status": "NOT_DUE", "network_reads": 0}}
        options.update(overrides)
        return run_worker(*self.paths, self.root / "worker", self.at + timedelta(seconds=120), **options)

    def test_actual_checks_are_bounded_and_do_not_poll_network(self):
        state = self.run_with()
        self.assertEqual(state["status"], "DEADLINE_EXPIRED")
        self.assertEqual(state["cycle_count"], 2)
        self.assertEqual(state["network_reads"], 0)
        stored = json.loads((self.root / "worker/worker-state.json").read_text())
        self.assertEqual(stored, state)

    def test_stop_event_ends_without_waiting_until_deadline(self):
        stop = threading.Event()
        def check(*args):
            stop.set()
            return {"status": "NOT_DUE", "network_reads": 0}
        state = self.run_with(stop_event=stop, cycle_fn=check)
        self.assertEqual(state["status"], "STOPPED")
        self.assertEqual(state["cycle_count"], 1)

    def test_failed_cycle_stays_fail_closed_and_does_not_echo_error_text(self):
        def fail(*args):
            raise ValueError('secret-bearing request detail')
        state = self.run_with(cycle_fn=fail)
        self.assertEqual(state["error_count"], 2)
        self.assertEqual(state["cycle_count"], 0)
        files = [self.root / 'worker/worker-state.json', self.root / 'worker/worker-audit.jsonl']
        self.assertTrue(all('secret-bearing' not in path.read_text() for path in files))

    def test_fail_closed_cycle_result_counts_as_error_even_without_exception(self):
        state = self.run_with(cycle_fn=lambda *args: {"status": "FAILED_CLOSED", "network_reads": 1})
        self.assertEqual(state["error_count"], 2)
        self.assertEqual(state["cycle_count"], 2)
        self.assertEqual(state["network_reads"], 2)

    def test_different_activation_cannot_overwrite_original_contract(self):
        self.run_with()
        with self.assertRaisesRegex(ValueError, "contract changed"):
            self.run_with()

    def test_oversized_or_expired_deadline_refused(self):
        for until in (self.at, self.at - timedelta(seconds=1), self.at + timedelta(hours=96, seconds=1)):
            with self.assertRaisesRegex(ValueError, "deadline"):
                run_worker(*self.paths, self.root / "bad", until, clock=lambda: self.at)

    def test_invalid_interval_and_missing_inputs_refused(self):
        for interval in (True, 0, 14, 61, 900):
            with self.assertRaisesRegex(ValueError, "interval"):
                self.run_with(interval_seconds=interval)
        self.paths[1].unlink()
        with self.assertRaisesRegex(ValueError, "Existing original"):
            self.run_with()

    def test_network_reads_and_actual_successful_cycles_are_recorded(self):
        state = self.run_with(cycle_fn=lambda *args: {"status": "SUCCESS", "network_reads": 3})
        self.assertEqual(state["network_reads"], 6)
        self.assertEqual(state["cycle_count"], 2)

    def test_initial_runtime_must_be_separate_from_unrelated_evidence(self):
        folder = self.root / "worker"
        folder.mkdir()
        (folder / "original-proof.json").write_text('{}')
        with self.assertRaisesRegex(ValueError, "empty worker runtime"):
            self.run_with()
        self.assertTrue((folder / "original-proof.json").exists())


if __name__ == "__main__":
    unittest.main()
