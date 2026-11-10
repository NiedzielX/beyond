"""Synthetic-only isolation and seal contracts for historical replay."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_historical_replay_packets_v1 import PRECOMMIT_PATH
from ml.rolling72_historical_replay_v1 import (
    _gate, _past, _weights, run_predictions, score_predictions,
)


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
FEATURES = ("last_available_total", "observed_delta_since_first", "prefix_span_hours",
            "latest_staleness_hours", "hours_to_kickoff", "horizon_hours", "delta_6h",
            "slope_6h", "delta_24h", "slope_24h", "delta_72h", "slope_72h")


def iso(hours):
    return (BASE + timedelta(hours=hours)).isoformat()


def build_packet(root):
    protocol = json.loads(PRECOMMIT_PATH.read_text())
    protocol["dataset"].update(completed_selected_fixture_catalogue=7,
        all_feature_origins_before_label_filter=67, all_horizon_coordinates=201,
        known_matched_labels=201, known_stale_target_coordinates=0,
        known_postkickoff_coordinates=0)
    protocol["precommit_sha256"] = _hash({k:v for k,v in protocol.items() if k != "precommit_sha256"})
    training, inputs, truth = [], [], {}
    # Six earlier completed fixtures, ten labeled examples per horizon each.
    for group_i in range(6):
        group, event = f"train-{group_i}", 1000 + group_i
        kickoff = iso(100 + group_i)
        for h in (24, 48, 72):
            for sample in range(11):
                origin_h = sample * 0.01
                target_h = origin_h + h
                feature = {k: 0.0 for k in FEATURES}
                feature.update(last_available_total=1000 + group_i * 100 + sample,
                    prefix_span_hours=0.0, latest_staleness_hours=0.0,
                    hours_to_kickoff=(100 + group_i) - origin_h, horizon_hours=h)
                row = {"fixture_group":group,"ticket_event_id":event,"club_slug":f"club-{group_i % 3}",
                    "kickoff_at":kickoff,"origin_capture_at":iso(origin_h),"target_at":iso(target_h),
                    "label_captured_at":iso(target_h-1),"nominal_horizon_hours":h,
                    "historical_input_known_at":None,"historical_knowledge_unproven":True,
                    "source_family":"roboticket/roboticket",
                    "features":feature,"last_available_total":feature["last_available_total"],
                    "matched_available_total":feature["last_available_total"]-10,
                    "target_delta":-10.0}
                row["row_sha256"] = _hash(row)
                training.append(row)
                ident={"fixture_group":group,"origin_capture_at":row["origin_capture_at"],"horizon_hours":h}
                coordinate=_hash(ident)
                inputs.append({**ident,"coordinate_id":coordinate,"ticket_event_id":event,"club_slug":row["club_slug"],
                    "kickoff_at":kickoff,"target_at":row["target_at"],"status":"READY","features":feature,
                    "source_family":"roboticket/roboticket","history_quality":{"hourly_latest_bins":1,
                    "hourly_span_hours":0.0,"delta24_anchor_valid":False},"raw_prefix_snapshot_ids":[10000+group_i*100+sample]})
                truth[coordinate]={"fixture_group":group,"origin_capture_at":row["origin_capture_at"],"horizon_hours":h,
                    "target_at":row["target_at"],"status":"MATCHED","available_total":row["matched_available_total"],
                    "label_captured_at":row["label_captured_at"],"label_snapshot_id":20000+group_i*100+sample*3+h}
    test_group, event = "test-current", 9999
    for h in (24, 48, 72):
        feature = {k: 0.0 for k in FEATURES}
        feature.update(last_available_total=800.0,prefix_span_hours=0.0,latest_staleness_hours=0.0,
                       hours_to_kickoff=300.0,horizon_hours=h)
        ident = {"fixture_group":test_group,"origin_capture_at":iso(200),"horizon_hours":h}
        coordinate = _hash(ident)
        row = {**ident,"coordinate_id":coordinate,"ticket_event_id":event,"club_slug":"club-test",
            "kickoff_at":iso(500),"target_at":iso(200+h),"status":"READY","features":feature,
            "source_family":"roboticket/roboticket","history_quality":{"hourly_latest_bins":1,
            "hourly_span_hours":0.0,"delta24_anchor_valid":False},"raw_prefix_snapshot_ids":[99999]}
        inputs.append(row)
        training_row={"fixture_group":test_group,"ticket_event_id":event,"club_slug":"club-test",
            "kickoff_at":iso(500),"origin_capture_at":iso(200),"target_at":iso(200+h),
            "label_captured_at":iso(200+h-1),"nominal_horizon_hours":h,
            "historical_input_known_at":None,"historical_knowledge_unproven":True,
            "source_family":"roboticket/roboticket","features":feature,
            "last_available_total":800.0,"matched_available_total":700.0-h,"target_delta":-100.0-h}
        training_row["row_sha256"]=_hash(training_row)
        training.append(training_row)
        truth[coordinate] = {"fixture_group":test_group,"origin_capture_at":iso(200),"horizon_hours":h,
            "target_at":iso(200+h),"status":"MATCHED","available_total":700.0-h,
            "label_captured_at":iso(200+h-1),"label_snapshot_id":30000+h}
    packet = Path(root)
    packet.mkdir()
    write = lambda name, obj: (packet/name).write_bytes(json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode())
    write("training_rows.json",training); write("test_inputs.json",inputs); write("truth.json",truth)
    hashes = {name:hashlib.sha256((packet/name).read_bytes()).hexdigest()
              for name in ("training_rows.json","test_inputs.json","truth.json")}
    manifest = {"version":"rolling72-historical-replay-packets-v1","precommit_sha256":protocol["precommit_sha256"],
        "synthetic_test":True,"servable":False,"historical_knowledge_unproven":True,
        "production_change":False,"live_adjustment":0,"dataset_sha256":protocol["dataset"]["dataset_sha256"],
        "file_sha256":hashes}
    manifest["manifest_sha256"] = _hash(manifest)
    write("manifest.json",manifest)
    return packet, protocol


class HistoricalReplayTests(unittest.TestCase):
    def test_temporal_training_excludes_current_fixture_and_targets_at_or_after_origin(self):
        training=[]
        for group,kickoff,targets in (("old",iso(-1),[iso(-3),iso(-2),iso(-1)]),
                                      ("future",iso(10),[iso(-3),iso(-2),iso(-1)]),
                                      ("current",iso(-1),[iso(-3),iso(-2),iso(-1)])):
            for h,target in zip((24,48,72),targets):
                training.append({"fixture_group":group,"kickoff_at":kickoff,"target_at":target,
                                 "nominal_horizon_hours":h,"row_sha256":group+str(h)})
        selected=_past(training,BASE,"current")
        self.assertEqual([r["target_at"] for r in selected],[iso(-3),iso(-2),iso(-1)])
        self.assertEqual({r["fixture_group"] for r in selected},{"old"})

    def test_common_cohort_gate_and_exact_fixture_horizon_weights(self):
        rows=[]
        for group in range(5):
            for h in (24,48,72):
                for _ in range(4): rows.append({"fixture_group":str(group),"club_slug":f"c{group%3}","nominal_horizon_hours":h})
        self.assertEqual(_gate(rows)["status"],"READY_TO_FIT")
        weights=_weights(rows)
        self.assertTrue(all(w==1.0 for w in weights))
        self.assertAlmostEqual(sum(weights),60.0)

    def test_synthetic_predictions_seal_without_reading_truth_then_score(self):
        with tempfile.TemporaryDirectory() as temp:
            packet,protocol=build_packet(Path(temp)/"packet")
            out=Path(temp)/"run"
            real_read=Path.read_bytes
            truth_reads=[]
            def observed_read(path):
                if path.name=="truth.json": truth_reads.append(path)
                return real_read(path)
            with patch.object(Path,"read_bytes",observed_read):
                seal=run_predictions(packet,out,synthetic_test=True,precommit=protocol)
                self.assertEqual(truth_reads,[])
                self.assertFalse(seal["truth_vault_opened"])
                self.assertGreaterEqual(seal["diagnostic_model_fits"],1)
                with self.assertRaises(ValueError):
                    run_predictions(packet,out,synthetic_test=True,precommit=protocol)
                result=score_predictions(packet,out,synthetic_test=True,precommit=protocol)
            self.assertEqual(len(truth_reads),1)
            self.assertEqual(result["coverage"]["input_coordinates"],201)
            self.assertFalse(result["servable"])
            self.assertFalse(result["attendance_mae_computed"])
            self.assertIn("+24h/candidate-vs-persistence",result["paired_metrics"])
            pair=result["paired_metrics"]["+24h/candidate-vs-persistence"]
            self.assertIsNotNone(pair["event_balanced_mae_difference_candidate_minus_baseline"])

    def test_poisoning_truth_vault_cannot_change_sealed_predictions(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            packet_a,protocol=build_packet(root/"packet-a")
            packet_b,_=build_packet(root/"packet-b")
            truth_path=packet_b/"truth.json"
            truth=json.loads(truth_path.read_text())
            for label in truth.values():
                if label["available_total"] is not None:
                    label["available_total"] += 123456
            truth_path.write_text(json.dumps(truth,sort_keys=True,separators=(",",":")))
            manifest_path=packet_b/"manifest.json"
            manifest=json.loads(manifest_path.read_text())
            manifest["file_sha256"]["truth.json"]=hashlib.sha256(truth_path.read_bytes()).hexdigest()
            manifest.pop("manifest_sha256")
            manifest["manifest_sha256"]=_hash(manifest)
            manifest_path.write_text(json.dumps(manifest,sort_keys=True,separators=(",",":")))
            out_a,out_b=root/"run-a",root/"run-b"
            run_predictions(packet_a,out_a,synthetic_test=True,precommit=protocol)
            run_predictions(packet_b,out_b,synthetic_test=True,precommit=protocol)
            predictions_a=json.loads((out_a/"predictions.json").read_text())["predictions"]
            predictions_b=json.loads((out_b/"predictions.json").read_text())["predictions"]
            self.assertEqual(predictions_a,predictions_b)


    def test_excluded_future_fixture_training_targets_cannot_change_predictions(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            a,protocol=build_packet(root/'a'); b,_=build_packet(root/'b')
            path=b/'training_rows.json';rows=json.loads(path.read_text())
            for row in rows:
                if row['fixture_group']=='test-current':
                    row['matched_available_total']+=1000000
                    row['target_delta']+=1000000
                    row['row_sha256']=_hash({k:v for k,v in row.items() if k!='row_sha256'})
            path.write_text(json.dumps(rows,sort_keys=True,separators=(',',':')))
            mp=b/'manifest.json';m=json.loads(mp.read_text())
            m['file_sha256']['training_rows.json']=hashlib.sha256(path.read_bytes()).hexdigest()
            m['manifest_sha256']=_hash({k:v for k,v in m.items() if k!='manifest_sha256'})
            mp.write_text(json.dumps(m,sort_keys=True,separators=(',',':')))
            run_predictions(a,root/'pa',synthetic_test=True,precommit=protocol)
            run_predictions(b,root/'pb',synthetic_test=True,precommit=protocol)
            self.assertEqual(json.loads((root/'pa/predictions.json').read_text())['predictions'],
                             json.loads((root/'pb/predictions.json').read_text())['predictions'])

    def test_paired_metrics_macro_weight_fixtures_instead_of_dependent_rows(self):
        from ml.rolling72_historical_replay_v1 import _paired
        candidate=[];baseline=[]
        for i,(group,error,control) in enumerate([('a',10,20),('a',10,20),('a',10,20),('b',100,50)]):
            base={'coordinate_id':str(i),'fixture_group':group,'club_slug':group}
            candidate.append({**base,'error':error});baseline.append({**base,'error':control})
        result=_paired(candidate,baseline)
        self.assertEqual(result['candidate']['event_balanced_mae'],55)
        self.assertEqual(result['baseline']['event_balanced_mae'],35)
        self.assertEqual(result['event_balanced_mae_difference_candidate_minus_baseline'],20)

    def test_tampered_sealed_predictions_fail_before_truth_is_opened(self):
        with tempfile.TemporaryDirectory() as temp:
            packet,protocol=build_packet(Path(temp)/'packets');out=Path(temp)/'out'
            run_predictions(packet,out,synthetic_test=True,precommit=protocol)
            pred=out/'predictions.json';pred.write_bytes(pred.read_bytes()+b' ')
            original=Path.read_bytes
            def guard(path):
                if path.name=='truth.json':raise AssertionError('truth read before seal verification')
                return original(path)
            with patch.object(Path,'read_bytes',guard),self.assertRaisesRegex(ValueError,'Sealed prediction'):
                score_predictions(packet,out,synthetic_test=True,precommit=protocol)


if __name__ == "__main__":
    unittest.main()
