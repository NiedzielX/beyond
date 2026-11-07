"""Lossless ISO encoding for the unchanged frozen C1 input boundary; no inference or fitting."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pandas as pd

VERSION='c1-shadow-lossless-timestamp-transport-v1'


def normalize(payload):
    result=deepcopy(payload);changes=[]
    for candidate in result.get('candidates') or []:
        representatives=candidate.get('representatives') or []
        values=[rep['requested_as_of_at'] for rep in representatives]
        instants=[pd.Timestamp(value) for value in values]
        if any(not isinstance(value,str) or pd.isna(instant) or instant.tzinfo is None for value,instant in zip(values,instants)):
            raise ValueError('Explicit original aware timestamps required; no guessed source time')
        try:
            parsed=pd.to_datetime(values,utc=True)
            if list(parsed)==instants:continue
        except ValueError:pass
        for rep,instant in zip(representatives,instants):
            original=rep['requested_as_of_at'];normalized=instant.tz_convert('UTC').isoformat(timespec='nanoseconds')
            if pd.Timestamp(normalized)!=instant:raise ValueError('Transport changed actual source instant')
            rep['requested_as_of_at']=normalized
            if original!=normalized:
                changes.append({'ticket_event_id':candidate['ticket_event_id'],'source_snapshot_id':rep['requested_snapshot_id'],
                                'original':original,'normalized':normalized})
    return result,changes


def convert(source,destination,receipt):
    paths=[p.resolve() for p in (source,destination,receipt)]
    if len(set(paths))!=3:raise ValueError('Original, normalized input and receipt must be separate files')
    raw=source.read_bytes();payload=json.loads(raw)
    if payload.get('version')!='c1-shadow-v8-inputs-v1':raise ValueError('Expected actual C1 v8 input contract')
    normalized,changes=normalize(payload)
    body=(json.dumps(normalized,sort_keys=True,allow_nan=False)+'\n').encode() if changes else raw
    evidence={'version':VERSION,'original_sha256':hashlib.sha256(raw).hexdigest(),
              'normalized_sha256':hashlib.sha256(body).hexdigest(),'changed_representations':changes,
              'actual_instants_changed':False,'models_changed':False,'production_change':False,'live_adjustment':0}
    with destination.open('xb') as file:file.write(body)
    with receipt.open('x') as file:json.dump(evidence,file,indent=2,sort_keys=True);file.write('\n')
    if source.read_bytes()!=raw:raise ValueError('Original source bytes changed')
    return evidence


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    result=convert(a.input,a.output,a.receipt)
    print(json.dumps({'version':VERSION,'normalized_representatives':len(result['changed_representations']),
                      'actual_instants_changed':False,'models_changed':False,'production_change':False,'live_adjustment':0}))


if __name__=='__main__':main()
