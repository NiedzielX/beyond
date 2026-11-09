"""Offline source/clock/scope boundaries; synthetic rows cannot serve a model."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

from ml.demand_engine.rolling72_features_v1 import _hash, build_issue, features
from ml.rolling72_offline_dataset_v2 import PRECOMMIT_PATH, build_dataset, capture_features


BASE = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
FAMILY = "roboticket/roboticket"


def iso(hours):
    return (BASE + timedelta(hours=hours)).isoformat()


def observation(identifier, hours, value=1000, family=FAMILY, **extra):
    return {"snapshot_id": identifier, "captured_at": iso(hours), "available_total": value,
            "measurement_key": family, "source": family.split('/')[-1], "sector_count": 1, **extra}


def event(rows=None, identifier=1, kickoff_hours=240, club="club"):
    return {"ticket_event_id": identifier, "club_slug": club, "provider": "roboticket",
            "kickoff_at": iso(kickoff_hours),
            "observations": [observation(i, t, v) for i, t, v in
                             ((1, 0, 1000), (2, 24, 950), (3, 48, 800), (4, 72, 700))]
                            if rows is None else rows}


def originals(events=None, identities=None, confirmations=None):
    events = [event()] if events is None else events
    source = {"version": "daily-inventory-public-export-v1", "exported_at": iso(200),
              "retrieved_at": iso(200.01), "events": events}
    source["export_sha256"] = _hash(source)
    identities = [{"id": e["ticket_event_id"], "provider": e["provider"], "source_domain": "bilety.test",
                   "club_slug": e["club_slug"], "external_event_id": str(e["ticket_event_id"])}
                  for e in events] if identities is None else identities
    confirmations = [{"ticket_event_id": e["ticket_event_id"], "confirmed_at": iso(243),
                       "created_at": iso(243), "actual_attendance": 99999}
                      for e in events] if confirmations is None else confirmations
    archive = {"completed_at": iso(301), "parts": {"outcomes": confirmations}}
    raw = [json.dumps(value, sort_keys=True).encode() for value in (source, identities, confirmations, archive)]
    protocol = json.loads(PRECOMMIT_PATH.read_text())
    protocol["training_data_cutoff_at"] = iso(360)
    for name, value in zip(("inventory", "identity_registry", "outcomes", "outcome_archive"), raw):
        import hashlib
        protocol["source_bindings"][name]["file_sha256"] = hashlib.sha256(value).hexdigest()
    protocol["source_bindings"]["inventory"].update(manifest_sha256=source["export_sha256"], received_at=source["retrieved_at"])
    protocol["source_bindings"]["outcomes"]["knowledge_bound_at"] = iso(300)
    protocol["source_bindings"]["outcome_archive"]["knowledge_bound_at"] = iso(301)
    protocol["precommit_sha256"] = _hash({k: v for k, v in protocol.items() if k != "precommit_sha256"})
    return raw, protocol


class OfflineDatasetTests(unittest.TestCase):
    def build(self, events=None, identities=None, confirmations=None):
        raw, protocol = originals(events, identities, confirmations)
        return build_dataset(*raw, synthetic_test=True, precommit=protocol)

    def first(self, data, horizon=24):
        return next(row for row in data["rows"] if row["origin_capture_at"] == iso(0)
                    and row["nominal_horizon_hours"] == horizon)

    def test_explicit_offline_fields_and_hashes_never_invent_knowledge_time(self):
        data = self.build()
        self.assertTrue(data["synthetic_test"])
        self.assertFalse(data["servable_training_input"])
        self.assertTrue(data["historical_knowledge_unproven"])
        self.assertIsNone(data["historical_input_known_at"])
        self.assertEqual(data["dataset_sha256"], _hash({k: v for k, v in data.items() if k != "dataset_sha256"}))
        row = self.first(data)
        self.assertEqual(row["row_sha256"], _hash({k: v for k, v in row.items() if k != "row_sha256"}))
        self.assertIsNone(row["historical_input_known_at"])
        self.assertNotIn('"known_at":', json.dumps(data))
        self.assertFalse(data["historical_accuracy_computed"])
        self.assertFalse(data["model_fit_performed"])
        self.assertFalse(data["attendance_values_used"])

    def test_custom_sources_cannot_escape_explicit_nonservable_test_mode(self):
        raw, protocol = originals()
        with self.assertRaisesRegex(ValueError, "only for nonservable"):
            build_dataset(*raw, precommit=protocol)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            build_dataset(*raw)
        with self.assertRaisesRegex(ValueError, "explicit boolean"):
            build_dataset(*raw, synthetic_test=1, precommit=protocol)

    def test_original_bytes_binding_rejects_even_rehashed_content(self):
        raw, protocol = originals()
        changed = json.loads(raw[0]); changed["events"][0]["observations"][0]["available_total"] = 900
        changed["export_sha256"] = _hash({k: v for k, v in changed.items() if k != "export_sha256"})
        raw[0] = json.dumps(changed).encode()
        with self.assertRaisesRegex(ValueError, "inventory source byte hash"):
            build_dataset(*raw, synthetic_test=True, precommit=protocol)

    def test_feature_values_equal_live_physics_without_reusing_live_knowledge_claims(self):
        prefix = [observation(1, -30, 1300), observation(2, -24, 1240), observation(3, -6, 1060), observation(4, 0, 1000)]
        offline, _ = capture_features(prefix, BASE, BASE + timedelta(days=50), 72)
        live_event = {"ticket_event_id": 1, "club_slug": "test", "kickoff_at": iso(1200), "known_at": iso(0),
                      "observations": [{k: v for k, v in row.items() if k not in ('source', 'sector_count')} | {"known_at": iso(0)} for row in prefix]}
        live = features(build_issue(live_event, BASE), 72)
        self.assertEqual(offline, live["features"])
        self.assertEqual(list(offline), json.loads(PRECOMMIT_PATH.read_text())["features"])

    def test_actual_window_elapsed_and_missing_are_not_zero(self):
        values, _ = capture_features([observation(1, -30, 1300), observation(2, 0, 1000)], BASE, BASE + timedelta(days=10), 24)
        self.assertEqual(values["delta_24h"], -300)
        self.assertEqual(values["slope_24h"], -10)
        self.assertIsNone(values["delta_6h"])
        values, _ = capture_features([observation(1, -30.001), observation(2, 0)], BASE, BASE + timedelta(days=10), 24)
        self.assertIsNone(values["delta_24h"])
        single = self.first(self.build())["features"]
        self.assertEqual(single["prefix_span_hours"], 0)
        self.assertEqual(single["observed_delta_since_first"], 0)
        self.assertIsNone(single["slope_24h"])

    def test_same_last_level_different_history_changes_value_features(self):
        falling, _ = capture_features([observation(1, -24, 1200), observation(2, 0, 1000)], BASE, BASE + timedelta(days=10), 72)
        rising, _ = capture_features([observation(1, -24, 800), observation(2, 0, 1000)], BASE, BASE + timedelta(days=10), 72)
        self.assertEqual(falling["last_available_total"], rising["last_available_total"])
        self.assertEqual(falling["delta_24h"], -200)
        self.assertEqual(rising["delta_24h"], 200)
        self.assertNotIn("observation_count", rising)

    def test_scope_change_starts_fresh_segment_without_aliasing_old_data(self):
        observations = [observation(10, -24, 9000, "roboticket/roboticket_candidate_backfill"),
                        observation(1, 0, 1000), observation(2, 24, 900), observation(3, 48, 800), observation(4, 72, 700)]
        data = self.build([event(observations)])
        row = self.first(data)
        self.assertEqual(row["features"]["observed_delta_since_first"], 0)
        self.assertEqual(row["segment_lineage"]["prior_incompatible_rows_retained"], 1)
        self.assertEqual(row["segment_lineage"]["raw_prefix_snapshot_ids"], [1])
        self.assertEqual(len(data["segment_catalogue"]), 2)
        self.assertFalse(data["segment_catalogue"][0]["supported_family"])
        self.assertEqual(data["coverage"]["raw_source_counts"]["snapshot_rows"], 5)

    def test_scope_switch_and_return_cannot_become_same_key_endpoint_label(self):
        data = self.build([event([observation(1, 0), observation(2, 12, 990, "roboticket/roboticket_vao_selectable_v1"),
                                 observation(3, 24, 900), observation(4, 48, 800), observation(5, 72, 700)])])
        self.assertFalse(any(row["origin_capture_at"] == iso(0) for row in data["rows"]))
        self.assertGreater(data["coverage"]["coordinate_status_counts"]["SOURCE_SCOPE_TRANSITION_BEFORE_TARGET"], 0)
        self.assertEqual(len(data["segment_catalogue"]), 3)

    def test_invalid_intermediate_reading_or_hidden_source_never_falls_through(self):
        for extra in ({"available_total": None}, {"source_visible": False}, {"source_active": False}):
            bad = observation(2, 12, 990) | extra
            data = self.build([event([observation(1, 0), bad, observation(3, 24, 900), observation(4, 48, 800)])])
            self.assertFalse(any(row["origin_capture_at"] == iso(0) for row in data["rows"]))
            self.assertGreater(data["coverage"]["coordinate_status_counts"].get("INVALID_OR_HIDDEN_FUTURE_INTERVAL", 0), 0)

    def test_literal_zero_preserved_and_complete_source_flags_counted(self):
        rows = [observation(1, 0, 0, source_active=True, source_visible=True),
                observation(2, 24, 0, source_active=True, source_visible=True)]
        data = self.build([event(rows)])
        row = self.first(data)
        self.assertEqual(row["matched_available_total"], 0)
        self.assertEqual(row["target_delta"], 0)
        self.assertEqual(data["coverage"]["matched_targets_with_complete_source_flags"], len(data["rows"]))
        self.assertEqual(data["coverage"]["raw_source_counts"]["literal_zero_rows"], 2)

    def test_six_hour_target_boundary_no_interpolation_or_post_kickoff(self):
        accepted = self.build([event([observation(1, 0), observation(2, 18, 900)])])
        self.assertEqual(self.first(accepted)["label_captured_at"], iso(18))
        rejected = self.build([event([observation(1, 0), observation(2, 17.999, 900)])])
        self.assertFalse(any(row["origin_capture_at"] == iso(0) for row in rejected["rows"]))
        kickoff = self.build([event([observation(1, 0), observation(2, 24, 900)], kickoff_hours=24)])
        self.assertEqual(kickoff["rows"], [])
        self.assertGreater(kickoff["coverage"]["coordinate_status_counts"]["TARGET_NOT_BEFORE_KICKOFF"], 0)

    def test_future_values_do_not_change_earlier_feature_or_prefix_hash(self):
        original = event()
        before = self.first(self.build([original]))
        original["observations"].append(observation(5, 6, 999999))
        after = self.first(self.build([original]))
        self.assertEqual(before["features"], after["features"])
        self.assertEqual(before["prefix_sha256"], after["prefix_sha256"])
        self.assertEqual(before["target_delta"], after["target_delta"])

    def test_attendance_values_do_not_enter_features_or_inventory_target(self):
        first = [{"ticket_event_id": 1, "confirmed_at": iso(243), "actual_attendance": 10}]
        second = [{"ticket_event_id": 1, "confirmed_at": iso(243), "actual_attendance": 100000000}]
        self.assertEqual(self.build(confirmations=first)["rows"], self.build(confirmations=second)["rows"])
        unknown = self.build(confirmations=[])
        self.assertEqual(unknown["rows"], [])
        self.assertEqual(unknown["coverage"]["event_status_counts"]["UNCONFIRMED_COMPLETED_FIXTURE"], 1)

    def test_after_cutoff_confirmation_or_ongoing_fixture_is_not_training(self):
        late = self.build(confirmations=[{"ticket_event_id": 1, "confirmed_at": iso(400)}])
        self.assertEqual(late["rows"], [])
        ongoing = self.build([event(kickoff_hours=400)])
        self.assertEqual(ongoing["rows"], [])
        self.assertEqual(ongoing["coverage"]["event_status_counts"]["ONGOING_FIXTURE"], 1)

    def test_global_snapshot_owner_or_payload_conflict_excludes_whole_groups(self):
        one, two = event(), event(identifier=2)
        data = self.build([one, two])
        self.assertEqual(data["rows"], [])
        self.assertEqual(len(data["coverage"]["snapshot_conflict_groups"]), 2)
        one["observations"].append(observation(1, 1, 9999))
        data = self.build([one])
        self.assertEqual(data["rows"], [])
        self.assertEqual(len(data["coverage"]["snapshot_conflict_groups"]), 1)

    def test_duplicate_source_identity_cannot_multiply_prefix_rows(self):
        duplicate = event()
        duplicate["observations"].append(deepcopy(duplicate["observations"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate snapshot identity"):
            self.build([duplicate])

    def test_confirmation_cannot_exist_before_its_created_clock(self):
        rows = [{"ticket_event_id": 1, "confirmed_at": iso(243), "created_at": iso(350)}]
        self.assertEqual(self.build(confirmations=rows)["rows"], [])

    def test_real_alias_group_is_one_fixture_and_selected_before_targets(self):
        events = [event(), event([observation(11, 0), observation(12, 24, 900), observation(13, 48, 800)], identifier=2)]
        identities = [{"id": identifier, "provider": "roboticket", "club_slug": "club",
                       "source_domain": "bilety.test", "external_event_id": "same-fixture"} for identifier in (1, 2)]
        data = self.build(events, identities)
        self.assertEqual(data["coverage"]["common_fixture_count"], 1)
        self.assertTrue(all(row["ticket_event_id"] == 1 for row in data["rows"]))
        self.assertEqual(data["coverage"]["event_status_counts"]["ALIAS_EVENT_EXCLUDED"], 1)
        events[1]["kickoff_at"] = iso(241)
        self.assertEqual(self.build(events, identities)["rows"], [])

    def test_received_or_captured_after_training_source_cutoff_is_rejected(self):
        rows = [observation(1, 201)]
        with self.assertRaisesRegex(ValueError, "export cutoff"):
            self.build([event(rows)])
        raw, protocol = originals()
        protocol["training_data_cutoff_at"] = iso(199)
        protocol["precommit_sha256"] = _hash({k: v for k, v in protocol.items() if k != "precommit_sha256"})
        with self.assertRaisesRegex(ValueError, "training cutoff"):
            build_dataset(*raw, synthetic_test=True, precommit=protocol)

    def test_same_time_latest_id_parity_and_no_input_mutation(self):
        prefix = [observation(1, -24, 1200), observation(2, 0, 1100), observation(3, 0, 1000)]
        before = deepcopy(prefix)
        values, clean = capture_features(prefix, BASE, BASE + timedelta(days=10), 24)
        self.assertEqual(values["last_available_total"], 1000)
        self.assertEqual(clean[-1]["snapshot_id"], 3)
        self.assertEqual(prefix, before)
        with self.assertRaisesRegex(ValueError, "Future"):
            capture_features(prefix + [observation(4, 1)], BASE, BASE + timedelta(days=10), 24)


if __name__ == "__main__":
    unittest.main()
