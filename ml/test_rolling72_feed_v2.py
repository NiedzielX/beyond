"""Synthetic-only paired-feed semantics and readonly snapshot evidence."""
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import unittest

from ml.demand_engine.rolling72_features_v1 import _hash
from ml.rolling72_feed_v2 import build_feed, MODELS
from ml.test_rolling72_paired_shadow_v2 import (
    BASE, clock, encode, later_source, source,
)


import ml.test_rolling72_paired_shadow_v2 as paired_fixture


class PairedFeedTests(unittest.TestCase):
    setUpClass = classmethod(paired_fixture.PairedShadowTests.setUpClass.__func__)
    tearDownClass = classmethod(paired_fixture.PairedShadowTests.tearDownClass.__func__)
    setUp = paired_fixture.PairedShadowTests.setUp
    tearDown = paired_fixture.PairedShadowTests.tearDown
    capture = paired_fixture.PairedShadowTests.capture
    score = paired_fixture.PairedShadowTests.score

    def feed(self, at=None, **kwargs):
        return build_feed(self.db, generated_at=at or self.issued + timedelta(minutes=1),
                          allow_synthetic_test=True, **kwargs)

    def change_prediction(self, mutate, model='candidate', horizon=24):
        with sqlite3.connect(self.db) as db:
            row = db.execute('select payload_json from predictions where model=? and horizon=?', (model,horizon)).fetchone()
            payload = json.loads(row[0]); mutate(payload)
            db.execute('update predictions set payload_json=? where model=? and horizon=?', (json.dumps(payload),model,horizon))

    def scored(self):
        self.capture()
        target = self.issued + timedelta(hours=24)
        self.score(later_source(target), target + timedelta(minutes=3))
        return target + timedelta(minutes=4)

    def test_real_model_and_baselines_are_four_distinct_models_not_v1(self):
        self.capture()
        feed = self.feed()
        self.assertEqual(feed['version'], 'rolling72-shadow-feed-v2')
        self.assertEqual(feed['evidence_kind'], 'immutable_actual_time_paired_shadow')
        self.assertTrue(feed['historical_training_knowledge_unproven'])
        self.assertTrue(feed['synthetic_test'])
        vintage = feed['vintages'][0]
        self.assertEqual(vintage['issued_at'], self.issued.isoformat())
        for point in vintage['points']:
            self.assertEqual(set(point['models']), set(MODELS))
            self.assertEqual(point['target_at'], (self.issued+timedelta(hours=point['horizon_hours'])).isoformat())
            self.assertEqual(point['models']['candidate']['model_id'], MODELS['candidate'])
            self.assertTrue(point['models']['candidate']['outside_training_maturity_range'])
            self.assertIsNone(point['models']['candidate']['score'])

    def test_no_synthetic_default_or_inferred_model_freeze(self):
        self.capture()
        with self.assertRaisesRegex(ValueError,'Synthetic'):
            build_feed(self.db,generated_at=self.issued+timedelta(minutes=1))
        self.assertIsNone(self.feed()['model_frozen_at'])
        manifest=json.loads((self.artifact/'manifest.json').read_text())
        self.assertEqual(self.feed(model_manifest=manifest)['model_frozen_at'],manifest['frozen_at'])
        forged=deepcopy(manifest);forged['frozen_at']=BASE.isoformat()
        with self.assertRaisesRegex(ValueError,'manifest'):
            self.feed(model_manifest=forged)
        forged['manifest_sha256']=_hash({k:v for k,v in forged.items() if k!='manifest_sha256'})
        with self.assertRaisesRegex(ValueError,'manifest'):
            self.feed(model_manifest=forged)

    def test_first_point_preserves_real_anchor_and_genuine_zero_not_null(self):
        raw=json.loads(source(single=True));raw['events'][0]['observations'][0]['available_total']=0
        self.capture(encode(raw))
        vintage=self.feed()['vintages'][0]
        self.assertEqual(len(vintage['observations']),1)
        self.assertNotEqual(vintage['observations'][0]['captured_at'],vintage['issued_at'])
        for point in vintage['points']:
            self.assertEqual(point['models']['persistence']['predicted_available_total'],0)
            self.assertIsNone(point['models']['pickup']['predicted_available_total'])
            self.assertEqual(point['models']['pickup']['status'],'UNAVAILABLE')

    def test_readonly_bytes_and_old_vintages_preserved(self):
        self.capture(); first=self.feed()['vintages'][0]
        self.capture(at=self.issued+timedelta(minutes=2))
        before=hashlib.sha256(self.db.read_bytes()).hexdigest()
        feed=self.feed(self.issued+timedelta(minutes=3))
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(),before)
        self.assertEqual(feed['vintages'][0],first)
        self.assertEqual(len(feed['vintages']),2)

    def test_source_private_fields_are_never_exported(self):
        data=json.loads(source());data['secret']='private-token-never-export'
        data['private_url']='https://private.invalid/token'
        self.capture(encode(data))
        encoded=json.dumps(self.feed())
        self.assertNotIn('private-token',encoded)
        self.assertNotIn('private.invalid',encoded)
        self.assertNotIn('fixture_group',encoded)

    def test_stale_source_symmetrically_unavailable_and_failed_coordinates_retained(self):
        self.capture(at=self.issued+timedelta(hours=2))
        vintage=self.feed(self.issued+timedelta(hours=2,minutes=1))['vintages'][0]
        self.assertTrue(all(m['predicted_available_total'] is None and m['status_reason']=='STALE_INPUT_FOR_V2'
                            for p in vintage['points'] for m in p['models'].values()))

    def test_failed_input_retains_real_prefix_and_null_targets(self):
        self.capture(at=self.issued+timedelta(hours=7))
        vintage=self.feed(self.issued+timedelta(hours=7,minutes=1))['vintages'][0]
        self.assertEqual(vintage['status'],'STALE_INPUT')
        self.assertTrue(vintage['observations'])
        self.assertTrue(all(p['target_at'] is None for p in vintage['points']))

    def test_shared_later_labels_score_existing_forecasts_only(self):
        at=self.scored();vintage=self.feed(at)['vintages'][0]
        scores=[m['score'] for m in vintage['points'][0]['models'].values() if m['predicted_available_total'] is not None]
        self.assertEqual(len(scores),3)
        self.assertTrue(all(s['target_available_total']==800 for s in scores))
        self.assertEqual(len({s['target_snapshot_id'] for s in scores}),1)
        self.assertEqual(len(vintage['observations']),4)
        for model in vintage['points'][0]['models'].values():
            if model['score'] is not None:
                self.assertAlmostEqual(model['score']['absolute_error'],abs(model['predicted_available_total']-800))

    def test_foreign_v1_ledger_and_missing_fourth_model_rejected(self):
        self.capture()
        with sqlite3.connect(self.db) as db: db.execute('pragma application_id=0x52374C31')
        with self.assertRaisesRegex(ValueError,'paired'):
            self.feed()

    def test_incomplete_coordinates_rejected(self):
        self.capture()
        with sqlite3.connect(self.db) as db:db.execute("delete from predictions where model='candidate' and horizon=48")
        with self.assertRaisesRegex(ValueError,'coordinates'):
            self.feed()

    def test_candidate_target_model_lineage_and_training_flag_tampering_rejected(self):
        self.capture()
        with sqlite3.connect(self.db) as db:
            original=db.execute("select payload_json from predictions where model='candidate' and horizon=24").fetchone()[0]
        changes=[{'model_manifest_sha256':'0'*64},{'version':'rolling72-persistence-v1'},
                 {'historical_training_knowledge_unproven':False},{'outside_training_maturity_range':None},
                 {'effective_lead_hours':24},{'target_at':(self.issued+timedelta(hours=25)).isoformat()},
                 {'computed_at':(self.issued-timedelta(seconds=1)).isoformat()}]
        for change in changes:
            with self.subTest(change=change):
                with sqlite3.connect(self.db) as db:
                    x=json.loads(original);x.update(change)
                    db.execute("update predictions set payload_json=? where model='candidate' and horizon=24",(json.dumps(x),))
                with self.assertRaises(ValueError):self.feed()

    def test_numeric_delta_mismatch_rejected(self):
        self.capture();self.change_prediction(lambda x:x.update(predicted_delta=42))
        with self.assertRaisesRegex(ValueError,'Numeric'):self.feed()

    def test_unavailable_model_cannot_carry_numeric_delta(self):
        self.capture();self.change_prediction(lambda x:x.update(predicted_delta=0),model='pickup')
        with self.assertRaisesRegex(ValueError,'not null'):self.feed()

    def test_ready_forecast_cannot_carry_failure_reason(self):
        self.capture();self.change_prediction(lambda x:x.update(reason='failure'))
        with self.assertRaisesRegex(ValueError,'Numeric'):self.feed()

    def test_mutated_observation_without_new_input_hash_is_rejected(self):
        self.capture()
        with sqlite3.connect(self.db) as db:
            data=json.loads(db.execute('select issue_json from issues').fetchone()[0])
            data['observed_prefix'][-1]['available_total']=0
            db.execute('update issues set issue_json=?',(json.dumps(data),))
        with self.assertRaisesRegex(ValueError,'issue lineage'):self.feed()

    def test_missing_or_wrong_score_rejected(self):
        at=self.scored()
        with sqlite3.connect(self.db) as db:db.execute("update scores set absolute_error=0 where model='candidate'")
        with self.assertRaisesRegex(ValueError,'arithmetic'):self.feed(at)

    def test_accepted_label_requires_candidate_score(self):
        at=self.scored()
        with sqlite3.connect(self.db) as db:db.execute("delete from scores where model='candidate'")
        with self.assertRaisesRegex(ValueError,'lacks'):self.feed(at)

    def test_actual_write_clock_corruption_rejected(self):
        self.capture()
        with sqlite3.connect(self.db) as db:db.execute('update issues set written_at=?',((self.issued+timedelta(seconds=91)).isoformat(),))
        with self.assertRaisesRegex(ValueError,'clocks'):self.feed(self.issued+timedelta(minutes=2))

    def test_export_before_score_acceptance_fails_closed(self):
        self.scored()
        with self.assertRaisesRegex(ValueError,'clocks'):self.feed(self.issued+timedelta(minutes=1))


if __name__=='__main__':unittest.main()
