"""Fixed genuine daily-change comparator, independent of the frozen learned v1."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import math
from pathlib import Path

from ml.demand_engine.daily_inventory_path_dataset_v1 import build_issue, canonical_hash, future_targets, issue_manifest, parse_timestamp

VERSION = 'daily-inventory-genuine-24h-drift-v1'
PRECOMMIT = Path(__file__).parent/'DAILY_INVENTORY_DRIFT_COMPARATOR_PRECOMMIT_V1.md'


def implementation_hash():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def freeze_artifact(now: str) -> dict:
    frozen = parse_timestamp(now)
    if frozen > datetime.now(timezone.utc):
        raise ValueError('Future freeze timestamp is not allowed')
    artifact = {'model_version': VERSION, 'frozen_at': frozen.isoformat(),
                'implementation_sha256': implementation_hash(),
                'precommit_sha256': hashlib.sha256(PRECOMMIT.read_bytes()).hexdigest(),
                'lookback_hours': 24, 'anchor_tolerance_hours': 6,
                'fit_performed': False, 'training_event_ids': [],
                'production_change': False, 'live_adjustment': 0}
    artifact['model_sha256'] = canonical_hash(artifact)
    return artifact


def validate_artifact(artifact: dict):
    if (artifact.get('model_sha256') != canonical_hash({k:v for k,v in artifact.items() if k!='model_sha256'})
            or artifact.get('model_version') != VERSION
            or artifact.get('implementation_sha256') != implementation_hash()
            or artifact.get('precommit_sha256') != hashlib.sha256(PRECOMMIT.read_bytes()).hexdigest()
            or artifact.get('lookback_hours') != 24 or artifact.get('anchor_tolerance_hours') != 6
            or artifact.get('fit_performed') is not False or artifact.get('training_event_ids') != []
            or artifact.get('production_change') is not False or artifact.get('live_adjustment') != 0):
        raise ValueError('Drift artifact/rule/implementation mismatch')
    parse_timestamp(artifact['frozen_at'])


def predict(issue: dict, artifact: dict) -> tuple[str, list[dict]]:
    validate_artifact(artifact)
    issued = parse_timestamp(issue['issued_as_of_at'])
    if parse_timestamp(artifact['frozen_at']) > issued:
        raise ValueError('Issue precedes genuine drift freeze')
    if (canonical_hash(issue['observed_prefix']) != issue['prefix_sha256']
            or canonical_hash(issue_manifest(issue)) != issue['input_manifest_sha256']):
        raise ValueError('Drift prefix/input hash mismatch')
    if issue['status'] != 'READY':
        return issue['status'], []
    rebuilt = build_issue({'ticket_event_id': issue['ticket_event_id'], 'club_slug': issue.get('club_slug'),
                           'kickoff_at': issue['kickoff_at'], 'observations': issue['observed_prefix']}, issued)
    if (rebuilt['input_manifest_sha256'] != issue['input_manifest_sha256']
            or rebuilt['prefix_sha256'] != issue['prefix_sha256']):
        raise ValueError('Drift prefix/input hash mismatch')
    if (rebuilt['status'] != 'READY' or issue['last_available_total'] != rebuilt['last_available_total']
            or parse_timestamp(issue['latest_captured_at']) != parse_timestamp(rebuilt['latest_captured_at'])):
        raise ValueError('Drift READY/latest lineage mismatch')
    prefix = rebuilt['observed_prefix']
    latest = prefix[-1]
    last_at = parse_timestamp(latest['captured_at'])
    anchor_cutoff = last_at-timedelta(hours=24)
    candidates = [row for row in prefix if anchor_cutoff-timedelta(hours=6)
                  <= parse_timestamp(row['captured_at']) <= anchor_cutoff]
    if not candidates:
        return 'DRIFT_ANCHOR_INSUFFICIENT', []
    anchor = candidates[-1]
    anchor_at = parse_timestamp(anchor['captured_at'])
    last = float(latest['available_total'])
    velocity = (last-float(anchor['available_total'])) / ((last_at-anchor_at).total_seconds()/86400)
    points = []
    for target in future_targets(rebuilt):
        raw = last+velocity*((parse_timestamp(target['target_at'])-last_at).total_seconds()/86400)
        if not math.isfinite(raw):
            raise ValueError('Nonfinite drift forecast')
        points.append({'ticket_event_id': issue['ticket_event_id'], 'club_slug': issue.get('club_slug',''),
            'issued_as_of_at': issued.isoformat(), 'target_at': target['target_at'], 'lead_days': target['lead_days'],
            'model_version': VERSION, 'model_sha256': artifact['model_sha256'],
            'baseline_version': 'daily-inventory-persistence-v1',
            'predicted_available_total': max(0., raw), 'baseline_available_total': last,
            'measurement_key': rebuilt['measurement_key'], 'prefix_sha256': rebuilt['prefix_sha256'],
            'input_manifest_sha256': rebuilt['input_manifest_sha256'],
            'anchor_snapshot_id': anchor['snapshot_id'], 'anchor_captured_at': anchor['captured_at'],
            'latest_snapshot_id': latest['snapshot_id'], 'latest_captured_at': latest['captured_at'],
            'velocity_places_per_day': velocity, 'unclipped_available_total': raw,
            'target_kind': 'available_total', 'unit': 'places', 'target_values_used': False,
            'evidence_kind': 'local_post_freeze_prospective', 'production_change': False})
    return 'READY', points
