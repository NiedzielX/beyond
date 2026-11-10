"""Synthetic-only historical packet isolation and source reconstruction checks."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_offline_dataset_v2 import build_dataset
from ml.test_rolling72_offline_dataset_v2 import originals, event, observation, iso
from ml.rolling72_historical_replay_packets_v1 import (
    PRECOMMIT_PATH, build_packets, prepare_packets, load_precommit,
)


def make_sources(events=None):
    originals_raw, v2_protocol = originals(events)
    dataset = build_dataset(*originals_raw, synthetic_test=True, precommit=v2_protocol)
    return bind(dataset, originals_raw[0], v2_protocol["source_bindings"])


def bind(dataset, source_raw, source_bindings):
    dataset_raw = json.dumps(dataset, sort_keys=True).encode()
    protocol = json.loads(PRECOMMIT_PATH.read_text())
    coverage = dataset["coverage"]
    statuses = coverage["coordinate_status_counts"]
    count = coverage["input_status_counts"].get("ELIGIBLE_OFFLINE_CAPTURE_ORIGIN", 0)
    protocol["dataset"].update(dataset_file_sha256=hashlib.sha256(dataset_raw).hexdigest(),
        dataset_sha256=dataset["dataset_sha256"], source_bindings=source_bindings,
        completed_selected_fixture_catalogue=len({s["fixture_group"] for s in dataset["segment_catalogue"]}),
        all_feature_origins_before_label_filter=count, all_horizon_coordinates=3 * count,
        known_matched_labels=len(dataset["rows"]),
        known_stale_target_coordinates=statuses.get("STALE_TARGET_OBSERVATION", 0),
        known_postkickoff_coordinates=statuses.get("TARGET_NOT_BEFORE_KICKOFF", 0))
    protocol["precommit_sha256"] = _hash({k: v for k, v in protocol.items() if k != "precommit_sha256"})
    return dataset_raw, source_raw, protocol


def build(args):
    dataset_raw, source_raw, protocol = args
    return build_packets(dataset_raw, source_raw, synthetic_test=True, precommit=protocol)


class ReplayPacketTests(unittest.TestCase):
    def test_all_coordinates_retained_before_future_label_filter(self):
        packets = build(make_sources())
        self.assertEqual(len(packets["test_inputs"]), 12)
        self.assertEqual(packets["coverage"]["feature_origins"], 4)
        self.assertEqual(packets["coverage"]["truth_status_counts"],
                         {"MATCHED": 6, "STALE_TARGET_OBSERVATION": 3, "NO_STRICT_FUTURE_OBSERVATION": 3})
        self.assertEqual(len(packets["training_rows"]), 6)
        self.assertTrue(packets["coverage"]["all_inputs_selected_before_label_matching"])

    def test_test_inputs_have_features_but_no_future_values_or_truth_status(self):
        packets = build(make_sources())
        required = {"coordinate_id", "fixture_group", "ticket_event_id", "club_slug", "kickoff_at",
                    "origin_capture_at", "horizon_hours", "target_at", "status", "features",
                    "source_family", "prefix_sha256", "history_quality", "raw_prefix_snapshot_ids"}
        for row in packets["test_inputs"]:
            self.assertEqual(set(row), required)
            self.assertEqual(row["status"], "READY")
            self.assertNotIn("available_total", row)
            self.assertNotIn("matched_available_total", row)
            self.assertNotIn("target_delta", row)
            expected = _hash({k: row[k] for k in ("fixture_group", "origin_capture_at", "horizon_hours")})
            self.assertEqual(row["coordinate_id"], expected)
        self.assertNotIn('"known_at"', json.dumps(packets))

    def test_poisoning_future_values_cannot_change_earlier_inputs(self):
        original = build(make_sources())
        modified = build(make_sources([event([observation(1, 0, 1000), observation(2, 24, 999999),
                                              observation(3, 48, 800), observation(4, 72, 700)])]))
        before = [r for r in original["test_inputs"] if r["origin_capture_at"] == iso(0)]
        after = [r for r in modified["test_inputs"] if r["origin_capture_at"] == iso(0)]
        self.assertEqual(before, after)
        coordinate = before[0]["coordinate_id"]
        self.assertNotEqual(original["truth"][coordinate]["available_total"], modified["truth"][coordinate]["available_total"])

    def test_missing_or_hidden_future_does_not_erase_earlier_coordinates(self):
        original = build(make_sources())
        modified = build(make_sources([event([observation(1, 0, 1000), observation(2, 24, 950, source_visible=False),
                                              observation(3, 48, 800), observation(4, 72, 700)])]))
        before = [r for r in original["test_inputs"] if r["origin_capture_at"] == iso(0)]
        after = [r for r in modified["test_inputs"] if r["origin_capture_at"] == iso(0)]
        self.assertEqual(before, after)
        self.assertTrue(all(modified["truth"][r["coordinate_id"]]["status"] != "MATCHED" for r in after))
        self.assertTrue(all(modified["truth"][r["coordinate_id"]]["available_total"] is None for r in after))

    def test_scope_transition_and_return_remain_unmatched_not_same_key_labels(self):
        data = build(make_sources([event([observation(1, 0),
            observation(2, 12, 900, "roboticket/roboticket_candidate_backfill"),
            observation(3, 24, 800), observation(4, 48, 700), observation(5, 72, 600)])]))
        first = [r for r in data["test_inputs"] if r["origin_capture_at"] == iso(0)]
        self.assertEqual(len(first), 3)
        self.assertTrue(all(data["truth"][r["coordinate_id"]]["status"] == "SOURCE_SCOPE_TRANSITION_BEFORE_TARGET" for r in first))
        later = next(r for r in data["test_inputs"] if r["origin_capture_at"] == iso(24))
        self.assertEqual(later["features"]["prefix_span_hours"], 0)
        self.assertEqual(later["raw_prefix_snapshot_ids"], [3])

    def test_postkickoff_horizons_are_retained_as_declared_status(self):
        data = build(make_sources([event([observation(1, 0), observation(2, 24, 900)], kickoff_hours=48)]))
        first = next(r for r in data["test_inputs"] if r["origin_capture_at"] == iso(0) and r["horizon_hours"] == 48)
        self.assertEqual(first["status"], "TARGET_NOT_BEFORE_KICKOFF")
        self.assertEqual(data["truth"][first["coordinate_id"]]["status"], "TARGET_NOT_BEFORE_KICKOFF")
        self.assertIsNone(data["truth"][first["coordinate_id"]]["available_total"])

    def test_zero_target_is_numeric_and_one_point_windows_stay_missing(self):
        data = build(make_sources([event([observation(1, 0), observation(2, 24, 0)])]))
        point = next(r for r in data["test_inputs"] if r["origin_capture_at"] == iso(0) and r["horizon_hours"] == 24)
        self.assertEqual(data["truth"][point["coordinate_id"]]["available_total"], 0)
        self.assertIsNone(point["features"]["slope_24h"])
        self.assertFalse(point["history_quality"]["delta24_anchor_valid"])

    def test_hourly_drift_quality_uses_genuine_elapsed_capture_time(self):
        rows = [observation(1, -37, 1250), observation(2, -36, 1240), observation(3, -24, 1120),
                observation(4, -18, 1060), observation(5, -12, 1000), observation(6, 12, 760)]
        data = build(make_sources([event(rows)]))
        point = next(r for r in data["test_inputs"] if r["origin_capture_at"] == iso(-12))
        self.assertEqual(point["history_quality"]["hourly_latest_bins"], 5)
        self.assertEqual(point["history_quality"]["hourly_span_hours"], 25)
        self.assertTrue(point["history_quality"]["delta24_anchor_valid"])

    def test_same_capture_tie_uses_latest_real_id_without_duplicate_origin(self):
        data = build(make_sources([event([observation(1, 0, 1000), observation(2, 0, 990), observation(3, 24, 900)])]))
        points = [r for r in data["test_inputs"] if r["origin_capture_at"] == iso(0)]
        self.assertEqual(len(points), 3)
        self.assertTrue(all(r["features"]["last_available_total"] == 990 for r in points))
        self.assertEqual(points[0]["raw_prefix_snapshot_ids"], [1, 2])
        self.assertEqual(points[0]["history_quality"]["hourly_latest_bins"], 1)

    def test_private_exclusive_files_bind_truth_without_putting_it_in_inputs(self):
        dataset_raw, source_raw, protocol = make_sources()
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "packets"
            manifest = prepare_packets(out, dataset_raw, source_raw, synthetic_test=True, precommit=protocol)
            self.assertEqual({p.name for p in out.iterdir()}, {"manifest.json", "training_rows.json", "test_inputs.json", "truth.json"})
            self.assertFalse(manifest["servable"])
            self.assertTrue(manifest["historical_knowledge_unproven"])
            for name, digest in manifest["file_sha256"].items():
                self.assertEqual(hashlib.sha256((out / name).read_bytes()).hexdigest(), digest)
                self.assertEqual((out / name).stat().st_mode & 0o777, 0o600)
            with self.assertRaises(ValueError):
                prepare_packets(out, dataset_raw, source_raw, synthetic_test=True, precommit=protocol)

    def test_real_mode_rejects_synthetic_custom_bindings_and_boolean_coercion(self):
        args = make_sources()
        with self.assertRaises(ValueError):
            build_packets(args[0], args[1], precommit=args[2])
        with self.assertRaises(ValueError):
            build_packets(args[0], args[1])
        with self.assertRaises(ValueError):
            load_precommit(synthetic_test=1)

    def test_original_byte_and_manifest_corruption_fail_closed(self):
        dataset_raw, source_raw, protocol = make_sources()
        with self.assertRaisesRegex(ValueError, "dataset bytes"):
            build_packets(dataset_raw + b" ", source_raw, synthetic_test=True, precommit=protocol)
        with self.assertRaisesRegex(ValueError, "inventory byte"):
            build_packets(dataset_raw, source_raw + b" ", synthetic_test=True, precommit=protocol)
        changed = deepcopy(protocol); changed["dataset"]["all_horizon_coordinates"] += 1
        with self.assertRaisesRegex(ValueError, "precommit"):
            build_packets(dataset_raw, source_raw, synthetic_test=True, precommit=changed)

    def test_rehashed_catalogue_or_training_feature_tamper_is_still_rejected(self):
        raw, source, protocol = make_sources()
        for change in ("catalogue", "feature"):
            data = json.loads(raw)
            if change == "catalogue":
                data["segment_catalogue"][0]["raw_snapshot_ids"][0] = 999999
            else:
                data["rows"][0]["features"]["last_available_total"] = 100
                data["rows"][0]["row_sha256"] = _hash({k: v for k, v in data["rows"][0].items() if k != "row_sha256"})
            data["dataset_sha256"] = _hash({k: v for k, v in data.items() if k != "dataset_sha256"})
            args = bind(data, source, protocol["dataset"]["source_bindings"])
            with self.subTest(change=change), self.assertRaises(ValueError):
                build(args)

    def test_precommitted_coordinate_counts_cannot_be_silently_reduced(self):
        raw, source, protocol = make_sources()
        protocol["dataset"]["known_stale_target_coordinates"] -= 1
        protocol["precommit_sha256"] = _hash({k: v for k, v in protocol.items() if k != "precommit_sha256"})
        with self.assertRaisesRegex(ValueError, "coverage"):
            build((raw, source, protocol))

    def test_composed_synthetic_packets_prediction_seal_then_truth_scoring(self):
        from threadpoolctl import threadpool_limits
        from ml.rolling72_historical_replay_v1 import run_predictions, score_predictions
        past = []
        for identifier in range(1, 6):
            rows = [observation(identifier * 1000 + i, hours, 2000 - i * 20)
                    for i, hours in enumerate(range(-216, 0, 24), 1)]
            past.append(event(rows, identifier=identifier, kickoff_hours=0, club=f"club-{identifier % 3}"))
        rows = [observation(99000 + i, hours, 2500 - i * 50)
                for i, hours in enumerate(range(0, 193, 24), 1)]
        dataset, source, protocol = make_sources(past + [event(rows, identifier=99, kickoff_hours=240, club="test-club")])
        with tempfile.TemporaryDirectory() as folder, threadpool_limits(limits=1):
            root = Path(folder)
            manifest = prepare_packets(root / "packets", dataset, source, synthetic_test=True, precommit=protocol)
            original_open = Path.open

            def no_truth(path, *args, **kwargs):
                if path.name == "truth.json":
                    raise AssertionError("Prediction phase must never open future-truth vault")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", no_truth):
                seal = run_predictions(root / "packets", root / "prediction", synthetic_test=True, precommit=protocol)
            self.assertFalse(seal["truth_vault_opened"])
            self.assertEqual(seal["diagnostic_model_fits"], 1)
            self.assertEqual(seal["coordinates"], 162)
            self.assertEqual(manifest["coverage"]["test_coordinates"], 162)
            sealed_raw = (root / "prediction/predictions.json").read_bytes()
            report = score_predictions(root / "packets", root / "prediction", synthetic_test=True, precommit=protocol)
            self.assertEqual((root / "prediction/predictions.json").read_bytes(), sealed_raw)
            self.assertEqual(report["seal_sha256"], seal["seal_sha256"])
            self.assertFalse(report["servable"])
            self.assertFalse(report["active_v2_artifact_used"])
            self.assertEqual(report["metrics"]["+24h/candidate"]["scored_fixtures"], 1)
            self.assertEqual(report["coverage"]["truth_status_counts"]["MATCHED"], 126)


if __name__ == "__main__":
    unittest.main()
