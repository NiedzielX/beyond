from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ml.test_structural_known_at_inputs_v1 import fixture
from ml.archive_structural_known_at_inputs_v1 import bounds, cycle, restore, source_lock, SourceArchiveStorage


class MemoryStorage:
    def __init__(self):self.data={}
    def ensure_private_bucket(self):pass
    def put_verified(self,key,data,content_type):
        self.data[key]=data
        return {'key':key,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'read_back_verified':True}
    def read(self,key):return self.data[key]


class ArchiveTests(unittest.TestCase):
    def test_explicit_bounds_cannot_be_perpetual_or_poll_too_fast(self):
        now=datetime(2026,11,4,tzinfo=timezone.utc)
        self.assertEqual(bounds((now+timedelta(hours=2)).isoformat(),900,now),now+timedelta(hours=2))
        for delta,interval in [(0,900),(73,900),(2,60),(2,3601)]:
            with self.assertRaises(ValueError):bounds((now+timedelta(hours=delta)).isoformat(),interval,now)

    def test_storage_namespace_cannot_change_other_experiment_manifests(self):
        self.assertTrue(SourceArchiveStorage._key('structural-known-at-inputs-v1/'+'a'*64+'.json'))
        for prefix in ['manifests','c1-seat-median-v1','drift-v1','../structural-known-at-inputs-v1']:
            with self.assertRaises(ValueError):SourceArchiveStorage._key(prefix+'/'+'a'*64+'.json')

    def test_source_contract_refuses_a_changed_exporter(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'test.py').write_text('original')
            with patch('ml.archive_structural_known_at_inputs_v1.ROOT',root),patch('ml.archive_structural_known_at_inputs_v1.SOURCES',['test.py']):
                runtime=root/'archive';runtime.mkdir()
                source_lock(runtime);(root/'test.py').write_text('changed')
                with self.assertRaisesRegex(ValueError,'changed after'):source_lock(runtime)

    def test_existing_other_experiment_runtime_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'experiment.json').write_text('{"other_experiment":true}')
            with self.assertRaisesRegex(ValueError,'own empty runtime'):source_lock(root)

    def test_actual_cycle_preserves_and_restores_all_raw_metadata_without_prediction(self):
        payload=fixture();storage=MemoryStorage()
        with tempfile.TemporaryDirectory() as d,patch('ml.archive_structural_known_at_inputs_v1.capture',return_value=payload):
            result=cycle(Path(d)/'archive',storage=storage)
            self.assertEqual(result['status'],'SOURCE_ARCHIVED_AND_RESTORED')
            self.assertTrue(result['restore_verified']);self.assertFalse(result['forecast_created'])
            self.assertFalse(result['official_database_write'])
            self.assertEqual(restore(storage.read(result['private_backup']['key'])),payload)
            self.assertEqual(json.loads(Path(result['private_input_path']).read_text()),payload)
            self.assertEqual(hashlib.sha256(storage.read(result['private_backup']['key'])).hexdigest(),result['private_backup']['key'].split('/')[-1][:-5])
            with self.assertRaises(FileExistsError):cycle(Path(d)/'archive',storage=storage)

    def test_corrupt_recovery_cannot_produce_a_success_receipt(self):
        storage=MemoryStorage()
        storage.read=lambda key:b'not-a-valid-backup'
        with tempfile.TemporaryDirectory() as d,patch('ml.archive_structural_known_at_inputs_v1.capture',return_value=fixture()):
            root=Path(d)/'archive'
            with self.assertRaises(ValueError):cycle(root,storage=storage)
            self.assertFalse(list(root.glob('capture-*/receipt.json')))

    def test_recovery_namespace_or_hash_tampering_is_rejected(self):
        storage=MemoryStorage()
        with tempfile.TemporaryDirectory() as d,patch('ml.archive_structural_known_at_inputs_v1.capture',return_value=fixture()):
            result=cycle(Path(d)/'archive',storage=storage)
            blob=json.loads(storage.read(result['private_backup']['key']))
            blob['payload_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'hash mismatch'):restore(json.dumps(blob).encode())
            blob['version']='other-experiment'
            with self.assertRaisesRegex(ValueError,'identity'):restore(json.dumps(blob).encode())


if __name__=='__main__':unittest.main()
