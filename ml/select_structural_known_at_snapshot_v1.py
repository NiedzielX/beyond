"""Read-only selection of genuinely pre-cutoff source captures; no model calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from ml.archive_structural_known_at_inputs_v1 import VERSION as ARCHIVE_VERSION, SourceArchiveStorage
from ml.attendance_knowledge_time_guard_v1 import timestamp
from ml.export_structural_known_at_inputs_v1 import validate_envelope

VERSION = 'structural-known-at-archive-asof-reader-v1'
MAX_AGE = timedelta(minutes=60)


def select_snapshot(runtime, cutoff, now=None):
    as_of=timestamp(cutoff);actual=now or datetime.now(timezone.utc)
    if as_of>actual:raise ValueError('As-of archive lookup cannot claim future availability')
    eligible=[]
    for directory in sorted(Path(runtime).glob('capture-*')):
        receipt_path=directory/'receipt.json'
        if not receipt_path.exists():continue  # Partial/failed captures never qualify.
        receipt=json.loads(receipt_path.read_text())
        if receipt.get('version')!=ARCHIVE_VERSION or receipt.get('status')!='SOURCE_ARCHIVED_AND_RESTORED' or receipt.get('restore_verified') is not True:
            raise ValueError('Archive receipt identity or verified restore missing')
        completed=timestamp(receipt['capture_completed_at'])
        if completed>as_of or as_of-completed>MAX_AGE:continue
        payload=validate_envelope(json.loads((directory/'inputs.json').read_text()))
        if (payload['export_sha256']!=receipt['source_export_sha256']
                or payload['export_sha256']!=directory.name.removeprefix('capture-')
                or timestamp(payload['completed_at'])!=completed):
            raise ValueError('Immutable archive source identity mismatch')
        if receipt.get('forecast_created') is not False or receipt.get('official_database_write') is not False:
            raise ValueError('Archive receipt is not the read-only source contract')
        backup=receipt['private_backup'];SourceArchiveStorage._key(backup['key'])
        if backup.get('read_back_verified') is not True or backup.get('sha256')!=backup['key'].split('/')[-1][:-5]:
            raise ValueError('Archive recovery receipt is not verified')
        eligible.append((completed,payload['export_sha256'],payload,receipt))
    if not eligible:
        return {'version':VERSION,'status':'NO_GENUINE_PRE_CUTOFF_SNAPSHOT','cutoff_at':as_of.isoformat(),
                'source':None,'forecast_created':False,'production_change':False}
    # Equal capture times must not choose arbitrary conflicting versions.
    latest=max(r[0] for r in eligible);chosen=[r for r in eligible if r[0]==latest]
    if len({r[1] for r in chosen})!=1:raise ValueError('Conflicting source captures at the same actual time')
    completed,sha,payload,receipt=chosen[0]
    return {'version':VERSION,'status':'GENUINE_PRE_CUTOFF_SNAPSHOT_SELECTED','cutoff_at':as_of.isoformat(),
            'capture_completed_at':completed.isoformat(),'age_seconds':(as_of-completed).total_seconds(),
            'source_export_sha256':sha,'private_backup':receipt['private_backup'], 'source':payload,
            'forecast_created':False,'production_change':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--cutoff',required=True);args=p.parse_args();result=select_snapshot(args.runtime,args.cutoff)
    print(json.dumps({k:v for k,v in result.items() if k not in ['source','private_backup']}))


if __name__=='__main__':main()
