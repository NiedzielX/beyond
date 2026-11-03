"""CLI and local-lifecycle integration tests, using synthetic fixtures only."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.parse

from ml import run_daily_inventory_path_v1 as runner
from ml.demand_engine.daily_inventory_path_dataset_v1 import (
    build_dataset, canonical_hash, parse_timestamp,
)
from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger
from ml.demand_engine.daily_inventory_path_model_v1 import (
    ALPHA, BASELINE_VERSION, FEATURE_COUNT, FEATURE_VERSION, MODEL_VERSION,
    PRECOMMIT_ID, QUANTILE, artifact_sha256, validate_model,
)


UTC = timezone.utc


def fixture_event(event_id=1, kickoff=None):
    kickoff = kickoff or datetime(2026, 10, 20, 18, tzinfo=UTC)
    issue = kickoff - timedelta(days=5)
    return {
        "ticket_event_id": event_id,
        "club_slug": f"club-{event_id}",
        "kickoff_at": kickoff.isoformat(),
        "observations": [
            {
                "snapshot_id": event_id * 100 + index,
                "captured_at": (issue - timedelta(hours=hours)).isoformat(),
                "available_total": value,
                "measurement_key": "provider/public-source-v1",
            }
            for index, (hours, value) in enumerate(
                ((48, 1200), (25, 1150), (12, 1100), (0, 1000)), 1,
            )
        ],
    }


def fixture_artifact(issue_at):
    """A valid zero-residual artifact for plumbing, not a model fit/result."""
    artifact = {
        "model_version": MODEL_VERSION,
        "baseline_version": BASELINE_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_count": FEATURE_COUNT,
        "precommit_id": PRECOMMIT_ID,
        "target_kind": "available_total",
        "unit": "places",
        "quantile": QUANTILE,
        "alpha": ALPHA,
        "solver": "highs",
        "fit_intercept": False,
        "trained_through": (issue_at - timedelta(days=3)).isoformat(),
        "fitted_at": (issue_at - timedelta(days=2)).isoformat(),
        "training_event_ids": [101, 102, 103, 104, 105],
        "training_club_count": 5,
        "training_row_count": 5,
        "training_manifest_sha256": "a" * 64,
        "sklearn_version": "synthetic-test-fixture",
        "coefficients": [0.0] * FEATURE_COUNT,
        "intercept": 0.0,
        "production_change": False,
        "live_adjustment": 0,
    }
    artifact["model_sha256"] = artifact_sha256(artifact)
    validate_model(artifact)
    return artifact


def fixture_export(events, as_of):
    result = {
        "version": runner.EXPORT_VERSION,
        "exported_at": as_of.isoformat(),
        "retrieved_at": as_of.isoformat(),
        "production_change": False,
        "events": events,
    }
    result["export_sha256"] = canonical_hash(result)
    return result


class DailyInventoryReaderTest(unittest.TestCase):
    def reader(self):
        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://fixture.supabase.co/",
            "SUPABASE_SERVICE_ROLE_KEY": "fixture-not-a-real-secret",
        }):
            return runner.PublicInventoryReader()

    def test_keyset_pagination_continues_after_short_nonempty_pages(self):
        pages = [
            [{"id": 1}, {"id": 3}],
            [{"id": 7}],
            [],
        ]
        responses = [io.BytesIO(json.dumps(page).encode()) for page in pages]
        with patch.object(runner.urllib.request, "urlopen", side_effect=responses) as request:
            rows = self.reader().rows("snapshots", [("select", "id")])
        self.assertEqual([row["id"] for row in rows], [1, 3, 7])
        self.assertEqual(request.call_count, 3)
        queries = [urllib.parse.parse_qs(urllib.parse.urlparse(call.args[0].full_url).query)
                   for call in request.call_args_list]
        self.assertEqual([query["id"] for query in queries], [["gt.0"], ["gt.3"], ["gt.7"]])
        self.assertTrue(all(query["limit"] == ["1000"] for query in queries))
        self.assertTrue(all(query["order"] == ["id.asc"] for query in queries))

    def test_nonadvancing_pagination_fails_instead_of_looping(self):
        responses = [io.BytesIO(b'[{"id":3}]'), io.BytesIO(b'[{"id":3}]')]
        with patch.object(runner.urllib.request, "urlopen", side_effect=responses):
            with self.assertRaisesRegex(ValueError, "did not advance"):
                self.reader().rows("snapshots", [])

    def test_rest_shape_and_http_errors_fail_closed(self):
        with patch.object(runner.urllib.request, "urlopen", return_value=io.BytesIO(b'{"bad":"shape"}')):
            with self.assertRaisesRegex(ValueError, "Unexpected REST export shape"):
                self.reader().rows("snapshots", [])
        error = urllib.error.HTTPError("https://fixture.invalid", 403, "private details", {}, None)
        with patch.object(runner.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(ValueError) as raised:
                self.reader().rows("snapshots", [])
        self.assertEqual(str(raised.exception), "Read-only snapshots export returned HTTP 403")

    def test_https_and_binding_are_required_before_any_request(self):
        with patch.dict("os.environ", {
            "SUPABASE_URL": "http://fixture.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "fixture",
        }):
            with self.assertRaises(ValueError):
                runner.PublicInventoryReader()
        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://fixture.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "",
        }):
            with self.assertRaises(ValueError):
                runner.PublicInventoryReader()


class DailyInventoryExportTest(unittest.TestCase):
    def setUp(self):
        self.as_of = datetime(2026, 10, 15, 18, tzinfo=UTC)

    def test_export_preserves_observed_zero_and_missing_source_identity(self):
        fake_reader = Mock()
        fake_reader.rows.side_effect = [
            [
                {"id": 1, "club_slug": "club", "provider": "provider", "kickoff_at": (self.as_of + timedelta(days=5)).isoformat()},
                {"id": 2, "club_slug": None, "provider": "provider", "kickoff_at": self.as_of.isoformat()},
            ],
            [
                {"id": 10, "ticket_event_id": 1, "captured_at": self.as_of.isoformat(), "available_total": 0, "source": "public", "sector_count": 3},
                {"id": 11, "ticket_event_id": 1, "captured_at": self.as_of.isoformat(), "available_total": None, "source": None},
            ],
        ]
        with patch.object(runner, "_now", return_value=self.as_of):
            exported = runner.export_public(fake_reader, self.as_of)
        self.assertEqual(len(exported["events"]), 1)
        observations = exported["events"][0]["observations"]
        self.assertEqual(observations[0]["available_total"], 0)
        self.assertEqual(observations[0]["measurement_key"], "provider/public")
        self.assertIsNone(observations[1]["available_total"])
        self.assertEqual(observations[1]["measurement_key"], "")
        self.assertFalse(exported["source_state_metadata_available"])
        self.assertEqual(exported["excluded_event_counts"], {"missing_event_identity": 1})
        self.assertEqual(exported["export_sha256"], canonical_hash({k: v for k, v in exported.items() if k != "export_sha256"}))
        self.assertEqual(fake_reader.rows.call_args_list[0].args[0], "ticket_events")
        self.assertEqual(fake_reader.rows.call_args_list[1].args[0], "snapshots")
        self.assertIn(("captured_at", "lte." + self.as_of.isoformat()), fake_reader.rows.call_args_list[1].args[1])

    def test_export_refuses_a_future_cutoff_without_reading(self):
        fake_reader = Mock()
        with patch.object(runner, "_now", return_value=self.as_of):
            with self.assertRaisesRegex(ValueError, "future cutoff"):
                runner.export_public(fake_reader, self.as_of + timedelta(seconds=1))
        fake_reader.rows.assert_not_called()

    def test_export_manifest_roundtrip_detects_tampering(self):
        exported = fixture_export([fixture_event()], self.as_of)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "export.json"
            runner._dump(path, exported, exclusive=True)
            self.assertEqual(runner.load_export(path), exported)
            exported["events"][0]["observations"][0]["available_total"] += 1
            path.write_text(json.dumps(exported))
            with self.assertRaisesRegex(ValueError, "manifest hash mismatch"):
                runner.load_export(path)

    def test_exclusive_outputs_do_not_replace_existing_export(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "export.json"
            runner._dump(path, {"first": True}, exclusive=True)
            with self.assertRaises(FileExistsError):
                runner._dump(path, {"replacement": True}, exclusive=True)
            self.assertEqual(json.loads(path.read_text()), {"first": True})


class DailyInventoryFitGuardTest(unittest.TestCase):
    def setUp(self):
        self.cutoff = datetime(2026, 10, 15, 18, tzinfo=UTC)

    def test_diagnostic_does_not_relax_minimum_support(self):
        events = [fixture_event(i) for i in range(1, 6)]
        rows = [{"issue": {"ticket_event_id": event["ticket_event_id"]}} for event in events]
        with patch.object(runner, "fit_model") as fit:
            result = runner.diagnostic_evaluation({"rows": rows}, events)
        self.assertEqual(result["status"], "INSUFFICIENT_DIAGNOSTIC_EVIDENCE")
        self.assertIn("Too few", result["reason"])
        fit.assert_not_called()

    def test_diagnostic_excludes_labels_not_known_at_first_test_issue(self):
        events, rows = [], []
        for index in range(1, 7):
            kickoff = self.cutoff + timedelta(days=index)
            event = fixture_event(index, kickoff)
            events.append(event)
            issue_at = kickoff - timedelta(days=5)
            rows.append({
                "issue": {"ticket_event_id": index, "issued_as_of_at": issue_at.isoformat()},
                "target_at": (issue_at + timedelta(days=4)).isoformat(),
                "target_captured_at": (issue_at + timedelta(days=4)).isoformat(),
            })
        with patch.object(runner, "fit_model") as fit:
            result = runner.diagnostic_evaluation({"rows": rows}, events)
        self.assertEqual(result["status"], "INSUFFICIENT_DIAGNOSTIC_EVIDENCE")
        self.assertEqual(result["test_event_ids"], [6])
        self.assertEqual(result["trained_through"], (self.cutoff + timedelta(days=1)).isoformat())
        self.assertEqual(result["train_event_ids"], [1, 2])
        self.assertEqual(result["train_row_count"], 2)
        fit.assert_not_called()

    def test_same_kickoff_events_stay_in_one_diagnostic_group(self):
        events, rows = [], []
        for index in range(1, 7):
            kickoff = self.cutoff + timedelta(days=min(index, 5))
            events.append(fixture_event(index, kickoff))
            rows.append({
                "issue": {"ticket_event_id": index, "issued_as_of_at": self.cutoff.isoformat()},
                "target_at": self.cutoff.isoformat(), "target_captured_at": self.cutoff.isoformat(),
            })
        with patch.object(runner, "fit_model") as fit:
            result = runner.diagnostic_evaluation({"rows": rows}, events)
        self.assertEqual(result["test_event_ids"], [5, 6])
        self.assertEqual(result["train_event_ids"], [1, 2, 3, 4])
        self.assertEqual(result["status"], "INSUFFICIENT_DIAGNOSTIC_EVIDENCE")
        fit.assert_not_called()

    def test_supported_diagnostic_keeps_train_and_test_events_disjoint(self):
        events = []
        for index in range(1, 9):
            kickoff = self.cutoff + timedelta(days=index * 10)
            event = fixture_event(index, kickoff)
            issue_at = kickoff - timedelta(days=5)
            for offset in (1, 2):
                event["observations"].append({
                    "snapshot_id": index * 100 + 4 + offset,
                    "captured_at": (issue_at + timedelta(days=offset)).isoformat(),
                    "available_total": 1000 - 100 * offset,
                    "measurement_key": "provider/public-source-v1",
                })
            events.append(event)
        dataset = build_dataset(events, parse_timestamp(events[-1]["kickoff_at"]))
        with patch.object(runner, "fit_model", return_value={"fixture": True}) as fit, \
                patch.object(runner, "predict_path", side_effect=lambda issue, _: [{"fixture_event": issue["ticket_event_id"]}]) as predict, \
                patch.object(runner, "evaluate_points", return_value={"fixture_metrics": True}) as evaluate:
            result = runner.diagnostic_evaluation(dataset, events)
        self.assertEqual(result["status"], "DIAGNOSTIC_ONLY")
        self.assertEqual(result["train_event_ids"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(result["test_event_ids"], [7, 8])
        train_rows, cutoff = fit.call_args.args
        self.assertEqual({row["issue"]["ticket_event_id"] for row in train_rows}, set(range(1, 7)))
        self.assertTrue(all(parse_timestamp(row["target_at"]) <= cutoff for row in train_rows))
        self.assertEqual({call.args[0]["ticket_event_id"] for call in predict.call_args_list}, {7, 8})
        self.assertEqual({row["issue"]["ticket_event_id"] for row in evaluate.call_args.args[1]}, {7, 8})
        self.assertEqual(result["metrics"], {"fixture_metrics": True})

    def test_final_fit_uses_completed_events_and_cutoff_eligible_labels_only(self):
        completed = fixture_event(1, self.cutoff - timedelta(days=1))
        ongoing = fixture_event(2, self.cutoff + timedelta(days=1))
        data = fixture_export([completed, ongoing], self.cutoff + timedelta(days=1))
        eligible = {"issue": {"ticket_event_id": 1}, "target_at": (self.cutoff - timedelta(days=2)).isoformat(), "target_captured_at": (self.cutoff - timedelta(days=2)).isoformat()}
        future_label = {"issue": {"ticket_event_id": 1}, "target_at": (self.cutoff + timedelta(hours=1)).isoformat(), "target_captured_at": self.cutoff.isoformat()}
        ongoing_row = {"issue": {"ticket_event_id": 2}, "target_at": self.cutoff.isoformat(), "target_captured_at": self.cutoff.isoformat()}
        fake_dataset = {"rows": [eligible, future_label, ongoing_row], "coverage": {"fixture": True}}
        artifact = fixture_artifact(self.cutoff + timedelta(days=4))
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(runner, "FROZEN_MODEL_REGISTRY", Path(temp) / "not-yet-frozen.json"), \
                patch.object(runner, "build_dataset", return_value=fake_dataset), \
                patch.object(runner, "fit_model", return_value=artifact) as fit, \
                patch.object(runner, "save_model") as save, \
                patch.object(runner, "diagnostic_evaluation", return_value={"status": "INSUFFICIENT_DIAGNOSTIC_EVIDENCE"}):
            destination = Path(temp) / "model.json"
            report = runner.fit_research(data, self.cutoff.isoformat(), destination)
        fit.assert_called_once_with([eligible], self.cutoff)
        save.assert_called_once_with(artifact, destination)
        self.assertEqual(report["evidence_kind"], "retrospective_diagnostic_not_prospective")
        self.assertFalse(report["production_change"])

    def test_final_fit_refuses_overwrite_before_building_or_refitting(self):
        data = fixture_export([], self.cutoff)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "frozen.json"
            path.write_text("original artifact")
            with patch.object(runner, "build_dataset") as build, patch.object(runner, "fit_model") as fit:
                with self.assertRaisesRegex(ValueError, "already exists"):
                    runner.fit_research(data, self.cutoff.isoformat(), path)
            build.assert_not_called()
            fit.assert_not_called()
            self.assertEqual(path.read_text(), "original artifact")

    def test_training_cutoff_cannot_exceed_export_cutoff(self):
        data = fixture_export([], self.cutoff)
        with self.assertRaisesRegex(ValueError, "exceeds export cutoff"):
            runner.fit_research(data, (self.cutoff + timedelta(seconds=1)).isoformat(), "/unused/model.json")

    def test_different_output_filename_cannot_refit_registered_v1(self):
        data = fixture_export([], self.cutoff)
        with tempfile.TemporaryDirectory() as temp:
            registered = Path(temp) / "registered.json"
            registered.write_text("existing frozen registration")
            with patch.object(runner, "FROZEN_MODEL_REGISTRY", registered), \
                    patch.object(runner, "fit_model") as fit:
                with self.assertRaisesRegex(ValueError, "already frozen"):
                    runner.fit_research(data, self.cutoff.isoformat(), Path(temp) / "another-name.json")
            fit.assert_not_called()


class DailyInventoryLifecycleIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.event = fixture_event()
        self.issue_at = parse_timestamp(self.event["kickoff_at"]) - timedelta(days=5)
        self.executed = self.issue_at + timedelta(minutes=20)
        self.model = fixture_artifact(self.issue_at)
        self.data = fixture_export([self.event], self.executed)

    def test_preview_emits_future_days_at_canonical_issue_without_writing_evidence(self):
        future = {
            "snapshot_id": 999,
            "captured_at": (self.issue_at + timedelta(days=1)).isoformat(),
            "available_total": 5,
            "measurement_key": "provider/public-source-v1",
        }
        self.data["events"][0]["observations"].append(future)
        result = runner.preview(self.data, self.model, self.executed)
        event = result["events"][0]
        self.assertEqual(event["issued_as_of_at"], self.issue_at.isoformat())
        self.assertEqual(event["status"], "READY")
        self.assertEqual([point["lead_days"] for point in event["points"]], [1, 2, 3, 4])
        self.assertEqual([point["predicted_available_total"] for point in event["points"]], [1000.0] * 4)
        self.assertTrue(all(parse_timestamp(observation["captured_at"]) <= self.issue_at for observation in event["observations"]))
        self.assertEqual(result["evidence_kind"], "research_preview_not_prospective")
        self.assertFalse(result["production_change"])

    def test_preview_refuses_after_export_and_suppresses_failed_input_paths(self):
        with self.assertRaisesRegex(ValueError, "exceeds the public export cutoff"):
            runner.preview(self.data, self.model, self.executed + timedelta(seconds=1))
        empty = deepcopy(self.data)
        empty["events"][0]["observations"] = []
        event = runner.preview(empty, self.model, self.executed)["events"][0]
        self.assertEqual(event["status"], "NO_OBSERVATIONS")
        self.assertEqual(event["observations"], [])
        self.assertEqual(event["points"], [])
        self.assertIsNone(event["measurement_key"])

    def test_preview_suppresses_models_trained_after_issue_or_on_target_event(self):
        after = deepcopy(self.model)
        after["trained_through"] = (self.issue_at + timedelta(minutes=1)).isoformat()
        after["fitted_at"] = (self.issue_at + timedelta(minutes=2)).isoformat()
        after["model_sha256"] = artifact_sha256(after)
        event = runner.preview(self.data, after, self.executed)["events"][0]
        self.assertEqual(event["status"], "MODEL_AFTER_ISSUE")
        self.assertEqual(event["input_status"], "READY")
        self.assertEqual(event["observations"], runner.build_issue(self.event, self.issue_at)["observed_prefix"])
        self.assertEqual(event["points"], [])
        target_event_model = deepcopy(self.model)
        target_event_model["training_event_ids"][0] = self.event["ticket_event_id"]
        target_event_model["model_sha256"] = artifact_sha256(target_event_model)
        event = runner.preview(self.data, target_event_model, self.executed)["events"][0]
        self.assertEqual(event["status"], "EVENT_IN_TRAINING")
        self.assertEqual(event["points"], [])

    def test_shadow_records_real_daily_vintages_and_later_scores_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "evidence.sqlite"
            with patch.object(runner, "_now", return_value=self.executed):
                result = runner.shadow(self.data, self.model, path)
                retry = runner.shadow(self.data, self.model, path)
            self.assertTrue(result["attempts"][0]["inserted"])
            self.assertFalse(retry["attempts"][0]["inserted"])
            self.assertEqual(result["attempts"][0]["point_count"], 4)

            tomorrow = self.issue_at + timedelta(days=1)
            later = deepcopy(self.event)
            later["observations"].append({
                "snapshot_id": 999, "captured_at": tomorrow.isoformat(),
                "available_total": 900, "measurement_key": "provider/public-source-v1",
            })
            with DailyInventoryPathLedger(path) as ledger:
                before = ledger.export_points()
                self.assertEqual(len(before), 4)
                self.assertTrue(all(point["score"] is None for point in before))
                scores = ledger.score([later], tomorrow)
                self.assertEqual(scores["scored_count"], 1)
                self.assertEqual(scores["not_due_count"], 3)
                first_score = ledger.export_points()[0]["score"]
                self.assertEqual(first_score["target_snapshot_id"], 999)
                self.assertEqual(first_score["candidate_abs_error"], 100.0)
                self.assertEqual(first_score["baseline_abs_error"], 100.0)

            tomorrow_execution = tomorrow + timedelta(minutes=20)
            tomorrow_data = fixture_export([later], tomorrow_execution)
            with patch.object(runner, "_now", return_value=tomorrow_execution):
                new = runner.shadow(tomorrow_data, self.model, path)
            self.assertTrue(new["attempts"][0]["inserted"])
            self.assertEqual(new["attempts"][0]["point_count"], 3)
            with DailyInventoryPathLedger(path) as ledger:
                after = ledger.export_points()
                self.assertEqual(len(ledger.export_attempts()), 2)
                self.assertEqual(len(after), 7)
                self.assertEqual(after[0]["score"], first_score)
                self.assertEqual(after[0]["predicted_available_total"], 1000.0)
                current = [point for point in after if point["issued_as_of_at"] == tomorrow.isoformat()]
                self.assertTrue(all(point["predicted_available_total"] == 900.0 for point in current))
                self.assertEqual(ledger.score([later], tomorrow)["already_scored_count"], 1)
            panel = runner.ledger_preview(path)
            original = panel["events"][0]
            self.assertEqual(original["points"][0]["score"], first_score)
            self.assertEqual(original["points"][0]["predicted_available_total"], 1000.0)
            self.assertEqual(len(original["observations"]), 4)
            self.assertEqual(panel["events"][1]["points"][0]["score"], None)
            metrics = runner.ledger_metrics(path, tomorrow_execution)
            self.assertEqual(metrics["challenger_event_balanced_mae"], 100.0)
            self.assertEqual(metrics["baseline_event_balanced_mae"], 100.0)
            self.assertEqual(metrics["scored_event_count"], 1)
            self.assertEqual(metrics["mature_prediction_count"], 1)
            self.assertEqual(metrics["pending_prediction_count"], 6)
            self.assertEqual(metrics["mature_label_coverage"], 1.0)
            self.assertEqual(metrics["per_lead"]["1"]["challenger_event_balanced_mae"], 100.0)

    def test_shadow_accepts_exact_window_boundary_and_skips_missed_or_early_windows(self):
        with tempfile.TemporaryDirectory() as temp:
            for suffix, when, expected in [
                ("boundary", self.issue_at + timedelta(minutes=90), 1),
                ("late", self.issue_at + timedelta(minutes=90, microseconds=1), 0),
                ("early", self.issue_at - timedelta(microseconds=1), 0),
            ]:
                data = fixture_export([self.event], min(when, self.executed))
                with self.subTest(suffix=suffix), patch.object(runner, "_now", return_value=when):
                    result = runner.shadow(data, self.model, Path(temp) / f"{suffix}.sqlite")
                    self.assertEqual(len(result["attempts"]), expected)

    def test_shadow_uses_wall_clock_and_refuses_future_export(self):
        with tempfile.TemporaryDirectory() as temp:
            data = fixture_export([self.event], self.executed + timedelta(seconds=1))
            with patch.object(runner, "_now", return_value=self.executed):
                with self.assertRaisesRegex(ValueError, "Export cutoff is in the future"):
                    runner.shadow(data, self.model, Path(temp) / "evidence.sqlite")
            self.assertFalse((Path(temp) / "evidence.sqlite").exists())

    def test_shadow_does_not_accept_a_model_fitted_after_issue(self):
        artifact = deepcopy(self.model)
        artifact["fitted_at"] = (self.issue_at + timedelta(minutes=1)).isoformat()
        artifact["model_sha256"] = artifact_sha256(artifact)
        with tempfile.TemporaryDirectory() as temp, patch.object(runner, "_now", return_value=self.executed):
            path = Path(temp) / "evidence.sqlite"
            result = runner.shadow(self.data, artifact, path)
            self.assertEqual(result["attempts"][0]["status"], "MODEL_NOT_FROZEN_AT_ISSUE")
            with DailyInventoryPathLedger(path) as ledger:
                self.assertEqual(ledger.export_attempts(), [])

    def test_audit_cli_writes_coverage_only_and_exits_successfully(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.json"
            destination = Path(temp) / "audit.json"
            runner._dump(source, self.data)
            self.assertEqual(runner.main(["audit", "--input", str(source), "--output", str(destination)]), 0)
            output = json.loads(destination.read_text())
            self.assertEqual(output["ready_issue_count"], 1)
            self.assertEqual(output["matched_target_count"], 0)
            self.assertEqual(output["pending_target_count"], 4)
            self.assertNotIn("rows", output)


class PanelLedgerExportTest(unittest.TestCase):
    def test_original_vintage_is_exported_without_regenerating_inputs(self):
        event = fixture_event(9)
        issued = parse_timestamp(event["kickoff_at"]) - timedelta(days=5)
        issue = runner.build_issue(event, issued)
        model = fixture_artifact(issued)
        points = runner.predict_path(issue, model)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ledger.sqlite"
            with DailyInventoryPathLedger(path) as ledger:
                ledger.record(issue, points, model, issued + timedelta(minutes=5))
            feed = runner.ledger_preview(path)
            vintage = feed["events"][0]
            self.assertEqual(vintage["observations"], issue["observed_prefix"])
            self.assertEqual(vintage["points"][0]["predicted_available_total"], points[0]["predicted_available_total"])
            self.assertEqual(vintage["origin_evidence_kind"], "local_post_freeze_prospective")
            self.assertEqual(vintage["points"][0]["evidence_kind"], "research_preview_not_prospective")
            output = Path(temp) / "panel.json"
            self.assertEqual(runner.main(["export-ledger", "--ledger", str(path), "--output", str(output)]), 0)
            self.assertEqual(json.loads(output.read_text())["events"][0]["issued_as_of_at"], issue["issued_as_of_at"])

    def test_prediction_gate_does_not_change_hashed_input_status_or_hide_observations(self):
        event = fixture_event(9)
        issued = parse_timestamp(event["kickoff_at"]) - timedelta(days=5)
        issue = runner.build_issue(event, issued)
        model = fixture_artifact(issued)
        model["trained_through"] = (issued + timedelta(hours=1)).isoformat()
        model["fitted_at"] = (issued + timedelta(hours=2)).isoformat()
        model["model_sha256"] = artifact_sha256(model)
        feed = runner.preview(fixture_export([event], issued + timedelta(hours=3)), model, issued + timedelta(hours=3))
        vintage = feed["events"][0]
        self.assertEqual(vintage["status"], "MODEL_AFTER_ISSUE")
        self.assertEqual(vintage["input_status"], "READY")
        self.assertEqual(vintage["input_manifest_sha256"], issue["input_manifest_sha256"])
        self.assertEqual(vintage["observations"], issue["observed_prefix"])
        self.assertEqual(vintage["points"], [])


if __name__ == "__main__":
    unittest.main()
