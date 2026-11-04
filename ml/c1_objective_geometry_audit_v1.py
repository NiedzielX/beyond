"""Read-only loss geometry audit: no prediction, target scoring or model fit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.c1_live_matched_audit_v1 import ROOT, frozen_hashes
from ml.c1_training_expansion_v1 import EVENT_IDS, PACKAGE
from ml.demand_engine.run_c1_shadow_v8 import sha256_file


def objective_geometry(frame):
    data = frame[['ticket_event_id', 'stadium_capacity']].copy()
    if data.empty or data.isna().any().any(): raise ValueError('Missing objective identity/capacity')
    ids, capacities = data.ticket_event_id.to_numpy(dtype=float), data.stadium_capacity.to_numpy(dtype=float)
    if (not np.isfinite(ids).all() or not np.isfinite(capacities).all() or (capacities <= 0).any()
            or (ids <= 0).any() or (ids != np.floor(ids)).any()):
        raise ValueError('Invalid event/capacity')
    if data.groupby('ticket_event_id').stadium_capacity.nunique().max() != 1:
        raise ValueError('One event has conflicting capacities')
    counts = data.groupby('ticket_event_id').size()
    weights = data.ticket_event_id.map(1/counts).to_numpy(dtype=float)
    weights /= weights.mean()  # Identical normalization to the frozen Ridge fit.
    mass = pd.Series(weights).groupby(data.ticket_event_id.to_numpy()).sum()
    if not np.allclose(mass.to_numpy(), len(data)/len(counts), atol=1e-12, rtol=0):
        raise ValueError('Event contribution is not balanced')
    minimum, maximum = float(capacities.min()), float(capacities.max())
    return {'version': 'c1-objective-geometry-audit-v1', 'independent_training_events': len(counts),
        'training_rows': len(data), 'min_capacity': minimum, 'max_capacity': maximum,
        'event_weight_mass': float(mass.iloc[0]),
        'same_seat_error_small_vs_large_capacity_squared_loss_ratio': (maximum/minimum)**2,
        'same_seat_error_small_vs_large_capacity_absolute_occupancy_loss_ratio': maximum/minimum,
        'same_seat_error_small_vs_large_capacity_absolute_seat_loss_ratio': 1.0,
        'current_data_loss': 'sum(row_event_weight * seat_error**2 / capacity**2)',
        'current_penalty': 'Ridge alpha10; unchanged original preprocessing and clipping',
        'point_functional': {'squared_loss': 'conditional mean', 'absolute_loss': 'conditional median'},
        'target_values_parsed': False, 'predictions_computed': False, 'training_mae_computed': False,
        'model_fitted': False, 'mae_improvement_proven': False, 'production_change': False, 'live_adjustment': 0}


def run(training_csv, output):
    if output.exists(): raise ValueError('Refuse to overwrite an audit result')
    before = frozen_hashes()
    manifest_path = ROOT/'ml/artifacts/c1_training_expansion_v1/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    receipt = json.loads((manifest_path.parent/'freeze_receipt.json').read_text())
    if sha256_file(manifest_path) != receipt['manifest_sha256'] or manifest['package_version'] != PACKAGE:
        raise ValueError('Expansion freeze identity mismatch')
    if sha256_file(training_csv) != manifest['training']['private_frame_sha256']:
        raise ValueError('Private training frame differs from frozen input')
    # Target columns are deliberately not parsed. No in-sample error calculation.
    frame = pd.read_csv(training_csv, usecols=['ticket_event_id', 'stadium_capacity'])
    if tuple(sorted(frame.ticket_event_id.unique())) != EVENT_IDS or len(frame) != 74:
        raise ValueError('Fixed twenty-event/74-row identities changed')
    report = objective_geometry(frame)
    report['source_frame_sha256'] = sha256_file(training_csv)
    report['source_manifest_sha256'] = receipt['manifest_sha256']
    report['interpretation'] = ('Loss geometry is not observed forecast error or a causal diagnosis. Capacity is known in X; '
        'rescaling does not by itself change the unrestricted conditional functional. Finite model/regularization '
        'tradeoffs require a new precommitted future test; old structural capacity-weighting remains rejected.')
    if before != frozen_hashes(): raise ValueError('Old frozen artifacts changed')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as file: json.dump(report, file, indent=2, allow_nan=False); file.write('\n')
    print(json.dumps(report))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--training-csv', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); run(a.training_csv, a.output)


if __name__ == '__main__': main()
