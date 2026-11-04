from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from ml.start_daily_inventory_path_watcher_v1 import ARTIFACT, launch_lock, start_worker, worker_status


class DetachedWorkerTests(unittest.TestCase):
    def test_invalid_deadline_or_interval_never_starts_process(self):
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch("ml.start_daily_inventory_path_watcher_v1.subprocess.Popen") as spawn:
            for stop, interval in ((now-timedelta(seconds=1),900), (now+timedelta(hours=25),900), (now+timedelta(hours=1),59), (now+timedelta(hours=1),60.5)):
                with self.subTest(stop=stop, interval=interval), self.assertRaises(ValueError):
                    start_worker(Path(directory), stop.isoformat(), interval=interval)
            spawn.assert_not_called()

    def test_live_pid_is_not_duplicated_or_killed(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory); (runtime/"watcher.pid").write_text("12345\n")
            with patch("ml.start_daily_inventory_path_watcher_v1.process_alive", return_value=True), \
                 patch("ml.start_daily_inventory_path_watcher_v1.subprocess.Popen") as spawn:
                result = start_worker(runtime, (datetime.now(timezone.utc)+timedelta(hours=1)).isoformat())
                self.assertEqual(result["status"], "ALREADY_RUNNING")
                self.assertFalse(result["new_worker_started"])
                spawn.assert_not_called()

    def test_new_worker_detaches_and_records_a_bounded_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory); child = Mock(pid=12345)
            with patch("ml.start_daily_inventory_path_watcher_v1.subprocess.Popen", return_value=child) as spawn:
                result = start_worker(runtime, (datetime.now(timezone.utc)+timedelta(hours=1)).isoformat())
                self.assertEqual(result["status"], "LAUNCHED_NOT_YET_CYCLE_VERIFIED")
                self.assertTrue(spawn.call_args.kwargs["start_new_session"])
                self.assertEqual((runtime/"watcher.pid").read_text().strip(), "12345")
                self.assertTrue(json.loads((runtime/"watcher-launch.json").read_text())["host_dependent"])

    def test_parallel_launcher_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            with launch_lock(runtime), patch("ml.start_daily_inventory_path_watcher_v1.subprocess.Popen") as spawn:
                with self.assertRaisesRegex(ValueError, "launcher"):
                    start_worker(runtime, (datetime.now(timezone.utc)+timedelta(hours=1)).isoformat())
                spawn.assert_not_called()

    def test_bad_pid_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory); (runtime/"watcher.pid").write_text("not-a-pid")
            with self.assertRaisesRegex(ValueError, "Malformed"):
                start_worker(runtime, (datetime.now(timezone.utc)+timedelta(hours=1)).isoformat())

    def test_liveness_is_not_recent_success_or_verified_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory); now = datetime.now(timezone.utc)
            (runtime/"watcher.pid").write_text("12345")
            launch = {"started_at": (now-timedelta(hours=2)).isoformat(),
                      "watch_until": (now+timedelta(hours=1)).isoformat(), "interval_seconds": 900}
            (runtime/"watcher-launch.json").write_text(json.dumps(launch))
            cycle = {"status": "CAPTURED_AND_SCORED", "finished_at": (now-timedelta(hours=1)).isoformat(),
                     "model_sha256": json.loads(ARTIFACT.read_text())["model_sha256"],
                     "backup": {"read_back_verified": True}, "evaluation": {"pending_prediction_count": 57}}
            with patch("ml.start_daily_inventory_path_watcher_v1.process_alive", return_value=True):
                (runtime/"latest-cycle.json").write_text(json.dumps(cycle))
                self.assertFalse(worker_status(runtime)["recent_cycle_verified"])
                cycle["finished_at"] = (now-timedelta(seconds=5)).isoformat()
                (runtime/"latest-cycle.json").write_text(json.dumps(cycle))
                self.assertEqual(worker_status(runtime)["status"], "HEALTHY")
                cycle["backup"]["read_back_verified"] = False
                (runtime/"latest-cycle.json").write_text(json.dumps(cycle))
                self.assertFalse(worker_status(runtime)["recent_cycle_verified"])
                cycle["backup"]["read_back_verified"] = True
                (runtime/"latest-cycle.json").write_text(json.dumps(cycle))
                launch["watch_until"] = (now-timedelta(seconds=1)).isoformat()
                (runtime/"watcher-launch.json").write_text(json.dumps(launch))
                self.assertFalse(worker_status(runtime)["recent_cycle_verified"])


if __name__ == "__main__":
    unittest.main()
