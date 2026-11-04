"""Capture private read-only inputs at actual persisted C1 forecast cutoffs."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request

from ml.c1_live_matched_audit_v1 import COHORT, ROOT
from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.run_daily_inventory_path_v1 import PublicInventoryReader

RPCS = {'events': 'export_c1_alpha_v7_events_v1', 'attendance': 'export_c1_alpha_v7_attendance_v1',
        'sporting': 'export_c1_alpha_v7_sporting_v1', 'aliases': 'export_c1_alpha_v7_aliases_v1',
        'final24': 'export_c1_alpha_v7_final24_rows_v1', 'readiness': 'export_d2_prospective_readiness_v1'}
TABLES = {'c1-events': 'dashboard_c1_shadow_v8_events_v1', 'c1-status': 'dashboard_c1_shadow_v8_status_v1',
          'outcomes': 'ticket_event_outcomes', 'ticket-events': 'ticket_events'}


def select_representatives(snapshots, kickoff, cutoff):
    kickoff, cutoff = parse_timestamp(kickoff), parse_timestamp(cutoff)
    if cutoff >= kickoff:
        raise ValueError('Matched cutoff must be before kickoff')
    buckets = {}
    for row in sorted(snapshots, key=lambda r: (parse_timestamp(r['captured_at']), r['id'])):
        captured = parse_timestamp(row['captured_at'])
        if not kickoff-timedelta(hours=24) < captured <= cutoff:
            continue
        bucket = math.floor((kickoff-captured).total_seconds()/21600)
        if 0 <= bucket <= 3:
            buckets[bucket] = row
    return sorted(buckets.items(), key=lambda item: parse_timestamp(item[1]['captured_at']))


class Reader(PublicInventoryReader):
    def request(self, path, payload=None):
        request = urllib.request.Request(self.base+'/rest/v1/'+path,
            headers={**self.headers, 'Content-Type': 'application/json'},
            data=None if payload is None else json.dumps(payload).encode())
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except Exception as exc:
            raise ValueError(f'Read-only audit input failed: {type(exc).__name__}') from None


def capture(output_dir):
    if output_dir.resolve().is_relative_to(ROOT):
        raise ValueError('Private source exports must remain outside the repository')
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    reader = Reader()
    values, records = {}, []
    def save(name, value):
        raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()
        with (output_dir/(name+'.json')).open('xb') as file:
            file.write(raw)
        records.append({'part': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        values[name] = value
    def rpc(item):
        name, method = item
        return name, reader.request('rpc/'+method, {})
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name, value in pool.map(rpc, RPCS.items()):
            save(name, value)
    for name, table in TABLES.items():
        # These sources currently contain fewer than 1000 rows. Stop at the
        # usual PostgREST cap so later growth cannot silently truncate a pack.
        value = reader.request(table+'?select=*&limit=1001')
        if not isinstance(value, list) or len(value) >= 1000:
            raise ValueError('Unpaginated small source expanded; revise export contract')
        save(name, value)
    c1 = [r for r in values['c1-events'] if r['outcome_available']]
    if tuple(sorted(r['ticket_event_id'] for r in c1)) != COHORT:
        raise ValueError('C1 scored cohort changed; this audit version is explicitly frozen to eleven events')
    priors, matched = [], []
    cache = {r['requested_snapshot_id']: r['features'] for r in values['final24']['liveRows']}
    def event_inputs(event):
        event_id = event['ticket_event_id']
        response = reader.request('rpc/get_structural_prior_v1',
            {'p_ticket_event_id': event_id, 'p_requested_as_of_at': event['latest_as_of_at']})
        if not isinstance(response, list) or len(response) != 1:
            raise ValueError('Expected exactly one actual T-1 anchor')
        prior = response[0]
        snapshots = reader.rows('snapshots', [
            ('select', 'id,ticket_event_id,captured_at,available_total,source'),
            ('ticket_event_id', 'eq.'+str(event_id)),
            ('captured_at', 'gt.'+(parse_timestamp(event['kickoff_at'])-timedelta(hours=24)).isoformat()),
            ('captured_at', 'lte.'+event['latest_as_of_at'])])
        selected = select_representatives(snapshots, event['kickoff_at'], event['latest_as_of_at'])
        representatives = []
        for bucket, row in selected:
            feature = cache.get(row['id'])
            if feature is None:
                result = reader.request('rpc/get_live_trajectory_features_v1_1_asof',
                    {'p_ticket_event_id': event_id, 'p_as_of': row['captured_at'], 'p_stadium_capacity': prior['stadium_capacity']})
                if not isinstance(result, list) or len(result) != 1:
                    raise ValueError('Expected one matching source-feature record')
                feature = result[0]
            if feature['snapshot_id'] != row['id']:
                raise ValueError('Source feature/snapshot identity mismatch')
            representatives.append({'ticket_event_id': event_id, 'requested_snapshot_id': row['id'],
                'requested_as_of_at': row['captured_at'], 'bucket_6h': bucket, 'features': feature})
        if not representatives or parse_timestamp(representatives[-1]['requested_as_of_at']) != parse_timestamp(event['latest_as_of_at']):
            raise ValueError('Actual C1 final timestamp could not be reconstructed')
        return {'ticket_event_id': event_id, 'requested_as_of_at': event['latest_as_of_at'], 'resolved': response}, representatives
    with ThreadPoolExecutor(max_workers=4) as pool:
        for prior, rows in pool.map(event_inputs, c1):
            priors.append(prior); matched.extend(rows)
    save('resolved-priors', priors)
    save('matched-final24', {'version': 'c1-alpha-v7-final24-rows-v1', 'eventCount': len(c1),
        'liveRowCount': len(matched), 'liveRows': matched,
        'sampling': 'latest genuine snapshot per final24h/6h bucket bounded by each persisted C1 latest_as_of_at'})
    save('export-manifest', {'version': 'c1-live-matched-audit-export-v1', 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                            'exports': records.copy(), 'read_only': True, 'production_change': False})
    print(json.dumps({'status': 'PRIVATE_INPUTS_EXPORTED', 'events': len(c1), 'matched_rows': len(matched)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    capture(parser.parse_args().output_dir)


if __name__ == '__main__':
    main()
