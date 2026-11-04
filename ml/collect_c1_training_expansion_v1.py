"""Resolve omitted anchor metadata before invoking the unchanged frozen adapter.

The existing C1 RPC omits target_as_of_at (see resolver_fix.sql). Never invent
it from kickoff: resolve the exact persisted prior and verify identity first.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd

from ml.c1_live_matched_audit_v1 import ROOT
from ml.c1_training_expansion_capture_v1 import capture, load_frozen
from ml.c1_training_expansion_v1 import digest_json
from ml.export_c1_matched_audit_inputs_v1 import Reader


def enrich_anchor(candidate, resolved):
    if not isinstance(resolved, list) or len(resolved) != 1:
        raise ValueError('Exactly one persisted prior resolution required')
    row, prior = resolved[0], candidate['prior']
    for field in ['source_prior_id', 'horizon', 'p50', 'stadium_capacity', 'model_spec_id', 'feature_contract', 'point_in_time_validated']:
        if row[field] != prior[field]:
            raise ValueError('Collector/resolver prior identity changed')
    if row.get('status') != 'ready' or pd.Timestamp(row['generated_at']) != pd.Timestamp(prior['generated_at']):
        raise ValueError('Collector/resolver prior status/time changed')
    if 'target_as_of_at' in prior and pd.Timestamp(prior['target_as_of_at']) != pd.Timestamp(row['target_as_of_at']):
        raise ValueError('Existing anchor target time conflicts with resolver')
    enriched = deepcopy(candidate)
    enriched['prior']['target_as_of_at'] = row['target_as_of_at']
    return enriched


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--artifact-dir', type=Path, required=True)
    a = p.parse_args()
    if a.runtime.resolve().is_relative_to(ROOT): raise ValueError('Raw collector outputs must remain outside Git')
    manifest, old_manifest, runtime, old = load_frozen(a.artifact_dir)
    reader = Reader(); requested = datetime.now(timezone.utc).isoformat()
    original = reader.request('rpc/get_c1_shadow_v8_inputs_v1', {'p_requested_at': requested})
    payload = deepcopy(original); resolutions, failures, valid = [], [], []
    for c in original.get('candidates') or []:
        try:
            latest = max(r['requested_as_of_at'] for r in c['representatives'])
            resolved = reader.request('rpc/get_structural_prior_v1',
                {'p_ticket_event_id': c['ticket_event_id'], 'p_requested_as_of_at': latest})
            valid.append(enrich_anchor(c, resolved))
            resolutions.append({'ticket_event_id': c['ticket_event_id'], 'resolved': resolved})
        except (ValueError, KeyError):
            failures.append({'ticket_event_id': c['ticket_event_id'], 'status': 'FAILED_CLOSED',
                             'reason': 'EXACT_ANCHOR_RESOLUTION_FAILED'})
    payload['candidates'], payload['candidate_count'] = valid, len(valid)
    labelled = reader.request('ticket_event_outcomes?select=ticket_event_id&limit=1001')
    if len(labelled) >= 1000: raise ValueError('Unpaginated outcome source expanded')
    result = capture(payload, manifest, old_manifest, runtime, old, now=datetime.now(timezone.utc),
        labelled_ids={r['ticket_event_id'] for r in labelled}, output_dir=a.runtime/'evidence')
    result['candidate_count'] += len(failures); result['events'].extend(failures)
    result['raw_collector_candidate_count'] = original['candidate_count']
    if result['candidate_count'] != original['candidate_count']:
        raise ValueError('Anchor enrichment changed cohort accounting')
    a.runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    if original['candidate_count']:
        source = {'version': 'c1-training-expansion-source-capture-v1', 'original': original,
                  'resolved_priors': resolutions, 'enriched_payload': payload}
        path = a.runtime/'inputs'/('input-'+digest_json(source)+'.json'); path.parent.mkdir(mode=0o700, exist_ok=True)
        raw = (json.dumps(source, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
        if path.exists():
            if path.read_bytes() != raw: raise ValueError('Immutable source capture conflict')
        else:
            with path.open('xb') as file: file.write(raw)
            path.chmod(0o440)
        result['private_input_file'] = str(path.relative_to(a.runtime))
    with (a.runtime/('attempt-'+requested.replace(':', '-')+'.json')).open('x') as file:
        json.dump(result, file, indent=2, allow_nan=False); file.write('\n')
    print(json.dumps(result))


if __name__ == '__main__': main()
