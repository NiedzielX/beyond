import unittest
import base64
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import zlib

from ml.watch_c1_training_expansion_v1 import ExpansionStorage, validate_bounds, backup, lock_source_contract
from ml.demand_engine.daily_inventory_path_storage_v1 import digest


class ExpansionWorkerBoundsTests(unittest.TestCase):
    def test_deadline_and_polling_are_explicit_and_bounded(self):
        validate_bounds('2026-11-06T20:30:00Z', 900, '2026-11-04T13:00:00Z')
        for until, interval in [('2026-11-08T13:00:00Z', 900), ('2026-11-04T12:00:00Z', 900),
                                ('2026-11-05T13:00:00Z', 1), ('2026-11-05T13:00:00Z', 3600)]:
            with self.subTest(until=until, interval=interval), self.assertRaises(ValueError):
                validate_bounds(until, interval, '2026-11-04T13:00:00Z')

    def test_backup_cannot_write_original_lane_or_latest_manifest(self):
        self.assertEqual(ExpansionStorage._key('c1-expansion-v1/'+'a'*64+'.json'), 'c1-expansion-v1/'+'a'*64+'.json')
        for path in ['manifests/'+'a'*64+'.json', 'drift-v1/'+'a'*64+'.json', 'c1-expansion-v1/../../latest.json']:
            with self.subTest(path=path), self.assertRaises(ValueError): ExpansionStorage._key(path)

    def test_compressed_private_backup_preserves_original_evidence_bytes(self):
        class Store:
            def ensure_private_bucket(self): pass
            def put_verified(self, key, raw, content_type):
                self.key, self.raw = key, raw
                return {'read_back_verified': True}
        with tempfile.TemporaryDirectory() as d, patch('ml.watch_c1_training_expansion_v1.load_frozen'):
            root = Path(d); artifact = root/'artifact'; artifact.mkdir()
            (artifact/'manifest.json').write_text('{"test":true}')
            runtime = root/'runtime'; (runtime/'evidence').mkdir(parents=True)
            original = b'{ "keep whitespace": true }\n'
            (runtime/'evidence/event-501-snapshot-2.json').write_bytes(original)
            store = Store(); backup(runtime, artifact, store)
            ExpansionStorage._key(store.key)
            wrapper = json.loads(store.raw); raw = zlib.decompress(base64.b64decode(wrapper['payload']))
            self.assertEqual(digest(raw), wrapper['payload_sha256'])
            bundle = json.loads(raw); restored = base64.b64decode(bundle['files'][0]['base64'])
            self.assertEqual(restored, original); self.assertEqual(digest(restored), bundle['files'][0]['sha256'])

    def test_first_collection_contract_cannot_be_replaced_after_code_changes(self):
        with tempfile.TemporaryDirectory() as d:
            runtime = Path(d); hashes = {'collector': 'original'}
            lock_source_contract(runtime, hashes)
            raw = (runtime/'collection-contract.json').read_bytes()
            lock_source_contract(runtime, hashes)
            with self.assertRaisesRegex(ValueError, 'implementation changed'):
                lock_source_contract(runtime, {'collector': 'new'})
            self.assertEqual((runtime/'collection-contract.json').read_bytes(), raw)


if __name__ == '__main__': unittest.main()
