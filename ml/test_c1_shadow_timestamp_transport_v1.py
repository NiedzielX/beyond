from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from ml.c1_shadow_timestamp_transport_v1 import normalize,convert


class ShadowTimestampTransportTests(unittest.TestCase):
    def payload(self):
        return {'version':'c1-shadow-v8-inputs-v1','requested_at':'2026-11-07T12:00:00Z',
                'candidates':[{'ticket_event_id':449,'representatives':[
                    {'requested_snapshot_id':1,'requested_as_of_at':'2026-11-07T03:00:00.123456+00:00','features':{'untouched':True}},
                    {'requested_snapshot_id':2,'requested_as_of_at':'2026-11-07T04:20:05+00:00','features':{'untouched':True}}]}]}

    def test_mixed_valid_iso_formats_become_parseable_with_identical_instants(self):
        before=self.payload();copy=deepcopy(before)
        with self.assertRaises(ValueError):pd.to_datetime([r['requested_as_of_at'] for r in before['candidates'][0]['representatives']],utc=True)
        result,changes=normalize(before)
        parsed=pd.to_datetime([r['requested_as_of_at'] for r in result['candidates'][0]['representatives']],utc=True)
        self.assertEqual(list(parsed),[pd.Timestamp(r['requested_as_of_at']) for r in before['candidates'][0]['representatives']])
        self.assertEqual(before,copy);self.assertEqual(len(changes),2)
        for a,b in zip(result['candidates'][0]['representatives'],before['candidates'][0]['representatives']):self.assertEqual(a['features'],b['features'])

    def test_already_parseable_payload_stays_byte_identical(self):
        before=self.payload();before['candidates'][0]['representatives'][1]['requested_as_of_at']='2026-11-07T04:20:05.000001+00:00'
        self.assertEqual(normalize(before),(before,[]))
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=json.dumps(before,indent=4).encode();(root/'raw.json').write_bytes(raw)
            result=convert(root/'raw.json',root/'normalized.json',root/'receipt.json')
            self.assertEqual((root/'normalized.json').read_bytes(),raw);self.assertEqual(result['original_sha256'],result['normalized_sha256'])

    def test_timezone_and_nanosecond_precision_are_not_rounded(self):
        before=self.payload();before['candidates'][0]['representatives'][0]['requested_as_of_at']='2026-11-07T04:00:00.123456789+01:00'
        result,_=normalize(before)
        self.assertEqual(result['candidates'][0]['representatives'][0]['requested_as_of_at'],'2026-11-07T03:00:00.123456789+00:00')

    def test_naive_unknown_times_and_wrong_contract_fail_closed(self):
        for value in [None,'NaT','2026-11-07T03:00:00']:
            before=self.payload();before['candidates'][0]['representatives'][0]['requested_as_of_at']=value
            with self.assertRaises(ValueError):normalize(before)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'raw.json').write_text('{"version":"wrong"}')
            with self.assertRaises(ValueError):convert(root/'raw.json',root/'normalized.json',root/'receipt.json')
            self.assertFalse((root/'normalized.json').exists())

    def test_original_and_existing_outputs_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=json.dumps(self.payload()).encode();(root/'raw.json').write_bytes(raw)
            with self.assertRaises(ValueError):convert(root/'raw.json',root/'raw.json',root/'receipt.json')
            result=convert(root/'raw.json',root/'normalized.json',root/'receipt.json')
            self.assertEqual((root/'raw.json').read_bytes(),raw);self.assertEqual(result['original_sha256'],hashlib.sha256(raw).hexdigest())
            with self.assertRaises(FileExistsError):convert(root/'raw.json',root/'normalized.json',root/'receipt.json')

    def test_empty_candidates_stay_empty(self):
        payload={'version':'c1-shadow-v8-inputs-v1','candidates':[]}
        self.assertEqual(normalize(payload),(payload,[]))


if __name__=='__main__':unittest.main()
