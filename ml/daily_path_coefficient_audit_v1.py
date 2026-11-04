"""Read-only algebraic explanation of issued frozen daily inventory paths."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

import numpy as np

from ml.daily_path_prefix_diagnostics_v1 import read_ledger
from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.demand_engine.daily_inventory_path_model_v1 import load_model, make_features, validate_model

BLOCKS = {
    'constant': (0, 1), 'days_to_event': (1, 2), 'prefix_span': (2, 3),
    'latest_staleness': (3, 4), 'observation_count': (4, 5),
    'relative_inventory_values': (5, 65), 'observed_bin_masks': (65, 125),
}


def coefficient_blocks(artifact: dict) -> dict:
    validate_model(artifact)
    return {f'{power}_{name}': {
        'coefficient_count': end-start,
        'nonzero_coefficient_count': sum(value != 0 for value in artifact['coefficients'][offset+start:offset+end]),
    } for power, offset in [('linear', 0), ('quadratic', 125)]
        for name, (start, end) in BLOCKS.items()}


def explain_point(issue: dict, point: dict, artifact: dict) -> dict:
    validate_model(artifact)
    for name in ['ticket_event_id', 'measurement_key', 'prefix_sha256', 'input_manifest_sha256']:
        if point[name] != issue[name]:
            raise ValueError('Issued point/input identity mismatch')
    if (point['model_sha256'] != artifact['model_sha256']
            or point['model_version'] != artifact['model_version']):
        raise ValueError('Issued point/model identity mismatch')
    issued = parse_timestamp(issue['issued_as_of_at'])
    if (parse_timestamp(point['issued_as_of_at']) != issued
            or parse_timestamp(point['target_at'])-issued != timedelta(days=point['lead_days'])):
        raise ValueError('Issued point/target coordinate mismatch')
    if (parse_timestamp(artifact['trained_through']) > issued
            or issue['ticket_event_id'] in artifact['training_event_ids']):
        raise ValueError('Issued event is not independent post-training inference')
    features = make_features(issue, point['lead_days'])
    latest = float(issue['last_available_total'])
    if point['baseline_available_total'] != latest:
        raise ValueError('Issued baseline differs from latest observed inventory')
    scale = max(1., max(float(row['available_total']) for row in issue['observed_prefix']))
    terms = scale * features * np.asarray(artifact['coefficients'], dtype=float)
    groups = {f'{power}_{name}': float(np.sum(terms[offset+start:offset+end]))
              for power, offset in [('linear', 0), ('quadratic', 125)]
              for name, (start, end) in BLOCKS.items()}
    unclipped = latest + math.fsum(groups.values()) + scale*artifact['intercept']
    predicted = max(0., unclipped)
    stored = point['predicted_available_total']
    if (isinstance(stored, bool) or not isinstance(stored, (int, float)) or not math.isfinite(stored)
            or not math.isclose(predicted, stored, rel_tol=1e-12, abs_tol=1e-7)):
        raise ValueError('Coefficient decomposition does not reproduce issued prediction')
    return {'ticket_event_id': issue['ticket_event_id'], 'club_slug': issue.get('club_slug', ''),
            'issued_as_of_at': point['issued_as_of_at'], 'target_at': point['target_at'],
            'lead_days': point['lead_days'], 'latest_available_total': latest, 'prefix_scale': scale,
            'additive_contributions_places': groups, 'unclipped_available_total': unclipped,
            'zero_clip_adjustment': predicted-unclipped, 'issued_predicted_available_total': stored,
            'reconstruction_absolute_difference': abs(predicted-stored)}


def build_audit(attempts: list[dict], points: list[dict], artifact: dict) -> dict:
    blocks = coefficient_blocks(artifact)
    by_id = {row['attempt_id']: row for row in attempts}
    if len(by_id) != len(attempts):
        raise ValueError('Duplicate attempt identity')
    rows = []
    for point in points:
        if point['attempt_id'] not in by_id:
            raise ValueError('Orphan issued prediction')
        attempt = by_id[point['attempt_id']]
        if attempt['artifact']['model_sha256'] != artifact['model_sha256']:
            raise ValueError('Attempt/model identity mismatch')
        rows.append(explain_point(attempt['issue'], point, artifact))
    return {'version': 'daily-path-coefficient-audit-v1', 'checked_at': datetime.now(timezone.utc).isoformat(),
            'model_sha256': artifact['model_sha256'], 'coefficient_blocks': blocks,
            'prediction_count': len(rows), 'independent_event_count': len({row['ticket_event_id'] for row in rows}),
            'points': rows, 'explanation_kind': 'exact_algebraic_terms_not_causal_importance',
            'accuracy_evaluated': False, 'target_values_used': False, 'model_refitted': False,
            'production_change': False, 'live_adjustment': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build_audit(*read_ledger(args.ledger), load_model(args.model))
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in ['version', 'prediction_count', 'coefficient_blocks', 'accuracy_evaluated']}))


if __name__ == '__main__':
    main()
