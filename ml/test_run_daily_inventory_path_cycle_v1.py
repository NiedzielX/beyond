import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from ml import run_daily_inventory_path_cycle_v1 as cycle
from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger


class DailyCycleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = Path(__file__).resolve().parent / "artifacts/daily_inventory_path_v1.json"
        self.feed = self.root / "feed.json"
        self.backup = {"bucket": "private-fixture", "manifest_object": {"key": "manifests/fixture.json"}}
        self.data = {"events": [], "exported_at": "2026-11-03T17:00:00Z", "export_sha256": "a" * 64}

    def test_complete_cycle_retains_export_score_backup_and_valid_empty_feed(self):
        with patch.object(cycle, "PublicInventoryReader"), \
             patch.object(cycle, "export_public", return_value=self.data), \
             patch.object(cycle, "shadow", return_value={"attempts": []}) as shadow, \
             patch.object(cycle, "backup_ledger", return_value=self.backup) as backup:
            result = cycle.run_cycle(self.root, self.model, self.feed)
        self.assertEqual(result["status"], "CAPTURED_AND_SCORED")
        self.assertTrue(result["backup"]["read_back_verified"])
        shadow.assert_called_once()
        backup.assert_called_once()
        self.assertEqual(json.loads(self.feed.read_text())["events"], [])
        self.assertEqual(json.loads((self.root / "latest-cycle.json").read_text())["status"], result["status"])
        self.assertEqual(len(list(self.root.glob("public-export-*.json"))), 1)

    def test_export_failure_still_backs_up_original_ledger_and_reports_failed_cycle(self):
        with patch.object(cycle, "PublicInventoryReader"), \
             patch.object(cycle, "export_public", side_effect=ValueError("offline")), \
             patch.object(cycle, "shadow") as shadow, \
             patch.object(cycle, "backup_ledger", return_value=self.backup) as backup:
            with self.assertRaisesRegex(ValueError, "failed closed"):
                cycle.run_cycle(self.root, self.model, self.feed)
        shadow.assert_not_called()
        backup.assert_called_once()
        result = json.loads((self.root / "latest-cycle.json").read_text())
        self.assertEqual(result["status"], "FAILED_CLOSED")
        self.assertTrue(result["backup"]["read_back_verified"])

    def test_backup_failure_is_not_reported_as_success(self):
        with patch.object(cycle, "PublicInventoryReader"), \
             patch.object(cycle, "export_public", return_value=self.data), \
             patch.object(cycle, "shadow", return_value={"attempts": []}), \
             patch.object(cycle, "backup_ledger", side_effect=ValueError("write denied")):
            with self.assertRaises(ValueError):
                cycle.run_cycle(self.root, self.model, self.feed)
        result = json.loads((self.root / "latest-cycle.json").read_text())
        self.assertEqual(result["status"], "FAILED_CLOSED")
        self.assertIn("backup_error_type", result)

    def test_concurrent_cycle_cannot_write_a_second_partial_run(self):
        with cycle.exclusive_cycle(self.root):
            with self.assertRaisesRegex(ValueError, "already running"):
                with cycle.exclusive_cycle(self.root):
                    self.fail("Second cycle unexpectedly entered the lock")

    def test_expired_watcher_does_not_start_more_work(self):
        with patch.object(cycle, "run_cycle") as runner:
            result = cycle.main(["--runtime", str(self.root), "--watch-until", "2020-01-01T00:00:00Z"])
        self.assertEqual(result, 0)
        runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
