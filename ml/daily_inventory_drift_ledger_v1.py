"""Separate append-only drift ledger; existing v1 ledger is never opened for writes."""
from __future__ import annotations

from datetime import timedelta
import json
import math
from pathlib import Path
import sqlite3

from ml.daily_inventory_drift_comparator_v1 import VERSION, predict, validate_artifact
from ml.demand_engine.daily_inventory_path_dataset_v1 import canonical_hash, parse_timestamp
from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger

MARKER = 'daily-inventory-drift-private-ledger-v1'
REFERENCE_SHA = '1137e257494583374f768622feca343f2dd7d634ef2446198703f8c27fbd9525'


class DriftLedger(DailyInventoryPathLedger):
    def __init__(self, path):
        path = Path(path)
        # Reject another existing ledger before the shared lifecycle can write any schema.
        if path.exists():
            with sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True) as existing:
                try:
                    marker = existing.execute('select version from drift_ledger_meta where singleton=1').fetchone()
                except sqlite3.Error:
                    raise ValueError('Refusing an existing non-drift ledger') from None
                if not marker or marker[0] != MARKER:
                    raise ValueError('Unexpected drift ledger identity')
        super().__init__(path)
        self._conn.execute('create table if not exists drift_ledger_meta(singleton integer primary key check(singleton=1), version text not null)')
        self._conn.execute('insert or ignore into drift_ledger_meta values(1,?)', (MARKER,))
        self._conn.commit()

    @staticmethod
    def _validate(issue, points, artifact, executed_at):
        validate_artifact(artifact)
        execution = parse_timestamp(executed_at)
        issued = parse_timestamp(issue['issued_as_of_at'])
        event, days = issue.get('ticket_event_id'), issue.get('days_to_event')
        if (not isinstance(event,int) or isinstance(event,bool) or event<=0
                or not isinstance(days,int) or isinstance(days,bool) or not 1<=days<=60
                or parse_timestamp(issue['kickoff_at'])-issued != timedelta(days=days)
                or issue.get('production_change',False) is not False):
            raise ValueError('Invalid drift issue identity/coordinate/flags')
        if not issued <= execution <= issued+timedelta(minutes=90):
            raise ValueError('Drift prospective window is issue through +90minutes only')
        # Also validates prefix hashes, original eligibility and freeze-before-issue.
        status, expected = predict(issue, artifact)
        if canonical_hash(points) != canonical_hash(expected):
            raise ValueError('Drift points differ from exact frozen rule output')
        payload = {'issue': issue, 'artifact': artifact, 'points': points, 'drift_status': status,
                   'evidence_kind': 'local_post_freeze_prospective', 'production_change': False}
        canonical_hash(payload)
        return payload, points, execution.isoformat()

    def score(self, *args, **kwargs):
        raise ValueError('Drift scoring requires the exact immutable reference target')

    def score_from_reference(self, reference_points: list[dict], as_of_at: str) -> dict:
        """Attach the exact same immutable genuine target, never a different matched label."""
        now = parse_timestamp(as_of_at)
        references = {}
        for point in reference_points:
            identity = (point['ticket_event_id'], parse_timestamp(point['issued_as_of_at']), parse_timestamp(point['target_at']))
            if identity in references:
                raise ValueError('Duplicate reference target identity')
            references[identity] = point
        counts = {'new_scores': 0, 'already_scored': 0, 'waiting_for_reference_score': 0, 'production_change': False}
        with self._transaction():
            for point in self.export_points():
                if point['score'] is not None:
                    counts['already_scored'] += 1
                    continue
                issued, target = parse_timestamp(point['issued_as_of_at']), parse_timestamp(point['target_at'])
                reference = references.get((point['ticket_event_id'], issued, target))
                score = reference.get('score') if reference else None
                if score is None or parse_timestamp(score['scored_at']) > now:
                    counts['waiting_for_reference_score'] += 1
                    continue
                if (reference.get('model_version') != 'daily-inventory-direct-median-v1'
                        or reference.get('model_sha256') != REFERENCE_SHA
                        or reference.get('evidence_kind') != 'local_post_freeze_prospective'
                        or reference.get('production_change') is not False):
                    raise ValueError('Unexpected frozen reference evidence')
                for key in ['measurement_key', 'prefix_sha256', 'input_manifest_sha256', 'baseline_available_total', 'lead_days']:
                    if reference[key] != point[key]:
                        raise ValueError('Reference/drift point lineage mismatch')
                captured = parse_timestamp(score['target_captured_at'])
                actual = score['target_available_total']
                snapshot = score['target_snapshot_id']
                if (not issued < captured <= target <= parse_timestamp(score['scored_at']) <= now
                        or captured < target-timedelta(hours=6)
                        or not isinstance(snapshot,int) or isinstance(snapshot,bool) or snapshot<=0
                        or isinstance(actual,bool) or not isinstance(actual,(int,float)) or not math.isfinite(actual) or actual<0
                        or score.get('measurement_key') != point['measurement_key']):
                    raise ValueError('Reference score violates genuine target contract')
                delta, baseline = point['predicted_available_total']-actual, point['baseline_available_total']-actual
                attached = {'target_snapshot_id': snapshot, 'target_captured_at': captured.isoformat(),
                    'target_available_total': actual, 'measurement_key': point['measurement_key'],
                    'candidate_error': delta, 'candidate_abs_error': abs(delta),
                    'baseline_error': baseline, 'baseline_abs_error': abs(baseline),
                    'scored_at': now.isoformat(), 'reference_source_point_id': reference.get('point_id'),
                    'reference_source_scored_at': score['scored_at'], 'production_change': False}
                self._conn.execute('insert into daily_path_scores(point_id,scored_at,payload_json) values(?,?,?)',
                                   (point['point_id'], now.isoformat(), json.dumps(attached, sort_keys=True, allow_nan=False)))
                counts['new_scores'] += 1
        return counts
