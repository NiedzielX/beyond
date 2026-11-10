from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import pandas as pd

from ml.c1_timestamp_encoding_adapter_v1 import normalize,LosslessReader


class LosslessTimestampTests(unittest.TestCase):
    def payload(self):
        return {'requested_at':'2026-11-07T12:00:00Z','candidates':[{'ticket_event_id':449,'representatives':[
            {'requested_snapshot_id':1,'requested_as_of_at':'2026-11-07T04:10:05.123456+00:00','features':{'as_of_at':'unchanged original feature'}},
            {'requested_snapshot_id':2,'requested_as_of_at':'2026-11-07T04:20:05+00:00','features':{'as_of_at':'also unchanged'}}]}]}

    def test_mixed_iso_representations_become_vector_parseable_without_changing_instants(self):
        original=self.payload();before=deepcopy(original);result,changes=normalize(original)
        values=[r['requested_as_of_at'] for r in result['candidates'][0]['representatives']]
        parsed=pd.to_datetime(values,utc=True)
        self.assertEqual(list(parsed),[pd.Timestamp(r['requested_as_of_at']) for r in original['candidates'][0]['representatives']])
        self.assertEqual(original,before);self.assertEqual(len(changes),2)
        self.assertEqual(result['requested_at'],original['requested_at'])
        self.assertEqual(result['candidates'][0]['representatives'][0]['features'],original['candidates'][0]['representatives'][0]['features'])

    def test_offset_and_nanosecond_precision_are_preserved_exactly(self):
        original=self.payload();original['candidates'][0]['representatives'][0]['requested_as_of_at']='2026-11-07T05:10:05.123456789+01:00'
        result,_=normalize(original)
        self.assertEqual(result['candidates'][0]['representatives'][0]['requested_as_of_at'],'2026-11-07T04:10:05.123456789+00:00')

    def test_unknown_or_naive_time_cannot_be_assigned_a_guessed_zone(self):
        for value in [None,'2026-11-07T04:20:05','NaT']:
            original=self.payload();original['candidates'][0]['representatives'][0]['requested_as_of_at']=value
            with self.assertRaises(ValueError):normalize(original)

    def test_only_the_input_rpc_is_normalized_and_original_bytes_are_preserved_before_return(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);reader=Mock();reader.request.return_value=self.payload();transport=LosslessReader(root,reader)
            result=transport.request('rpc/get_c1_shadow_v8_inputs_v1',{'p_requested_at':'actual'})
            files=list((root/'inputs').glob('codec-original-rpc-*.json'));self.assertEqual(len(files),1)
            raw=files[0].read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),files[0].stem.removeprefix('codec-original-rpc-'))
            self.assertEqual(json.loads(raw),self.payload());self.assertNotEqual(result,self.payload())
            receipt=json.loads(next((root/'inputs').glob('codec-receipt-*.json')).read_text())
            self.assertFalse(receipt['actual_instants_changed']);self.assertFalse(receipt['models_changed'])
            labels=[{'confirmed_at':'2026-11-07T08:22:42Z'}];reader.request.return_value=labels
            self.assertIs(transport.request('ticket_event_outcomes?select=*'),labels)


if __name__=='__main__':unittest.main()
