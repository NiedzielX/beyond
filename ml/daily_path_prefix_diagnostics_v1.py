"""Read-only prefix-stratified diagnostics; original full-cohort evaluator retained."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3

from ml.demand_engine.daily_inventory_path_dataset_v1 import parse_timestamp
from ml.demand_engine.daily_inventory_path_model_v1 import evaluate_points

REGIMES = ("ZERO_ONLY_PREFIX", "CONSTANT_POSITIVE_PREFIX", "VARYING_PREFIX")


def prefix_regime(issue: dict) -> str:
    if issue.get("status") != "READY":
        return "INPUT_NOT_READY"
    observations = issue.get("observed_prefix")
    if not isinstance(observations,list) or not observations:
        raise ValueError("READY prefix must contain genuine observations")
    values=[]
    for observation in observations:
        value=observation.get("available_total")
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            raise ValueError("Invalid observed inventory value")
        values.append(float(value))
    if all(value==0 for value in values):return "ZERO_ONLY_PREFIX"
    return "CONSTANT_POSITIVE_PREFIX" if len(set(values))==1 else "VARYING_PREFIX"


def build_report(attempts: list[dict], points: list[dict], as_of_at: str) -> dict:
    as_of=parse_timestamp(as_of_at)
    attempts_by_id={row['attempt_id']:row for row in attempts}
    if len(attempts_by_id)!=len(attempts):raise ValueError("Duplicate attempt identity")
    visible_attempts={key:value for key,value in attempts_by_id.items()
                      if parse_timestamp(value['issue']['issued_as_of_at'])<=as_of
                      and parse_timestamp(value['executed_at'])<=as_of}
    regimes={key:prefix_regime(value['issue']) for key,value in visible_attempts.items()}
    visible,labels,scored=[],[],[]
    for point in points:
        identifier=point['attempt_id']
        if identifier not in attempts_by_id:raise ValueError("Orphan prediction")
        if identifier not in visible_attempts:continue
        if regimes[identifier]=='INPUT_NOT_READY':raise ValueError("Failed-input attempt cannot have predictions")
        if parse_timestamp(point['issued_as_of_at'])!=parse_timestamp(visible_attempts[identifier]['issue']['issued_as_of_at']):
            raise ValueError("Prediction/attempt cutoff mismatch")
        if point['ticket_event_id']!=visible_attempts[identifier]['issue']['ticket_event_id']:
            raise ValueError("Prediction/attempt event mismatch")
        visible.append(point)
        score=point.get('score')
        if score is None or parse_timestamp(score['scored_at'])>as_of:continue
        if parse_timestamp(point['target_at'])>as_of:raise ValueError("Premature target score")
        issue=visible_attempts[identifier]['issue']
        label={'issue':issue,'lead_days':point['lead_days'],'target_at':point['target_at'],
               'target_snapshot_id':score['target_snapshot_id'],'target_captured_at':score['target_captured_at'],
               'target_available_total':score['target_available_total'],'measurement_key':point['measurement_key']}
        labels.append(label)
        scored.append((point,score))
    primary=evaluate_points(visible,labels)
    event_points=Counter(point['ticket_event_id'] for point,_ in scored)
    events=len(event_points)
    groups={}
    for regime in REGIMES:
        subset=[point for point in visible if regimes[point['attempt_id']]==regime]
        subset_ids={point['attempt_id'] for point in subset}
        subset_labels=[label for label in labels if any(
            label['issue']['ticket_event_id']==visible_attempts[key]['issue']['ticket_event_id']
            and parse_timestamp(label['issue']['issued_as_of_at'])==parse_timestamp(visible_attempts[key]['issue']['issued_as_of_at'])
            for key in subset_ids)]
        metrics=evaluate_points(subset,subset_labels)
        contribution=sum(abs(point['predicted_available_total']-score['target_available_total'])/
                         (events*event_points[point['ticket_event_id']]) for point,score in scored
                         if regimes[point['attempt_id']]==regime) if events else None
        mature=sum(parse_timestamp(point['target_at'])<=as_of for point in subset)
        groups[regime]={**metrics,'mature_prediction_count':mature,'pending_prediction_count':len(subset)-mature,
                       'mature_unscored_count':mature-len(subset_labels),
                       'contribution_to_primary_challenger_mae':contribution}
    if events and not math.isclose(sum(group['contribution_to_primary_challenger_mae'] for group in groups.values()),
                                   primary['challenger_event_balanced_mae'],rel_tol=1e-10,abs_tol=1e-8):
        raise ValueError("Descriptive contributions do not reconcile to primary MAE")
    return {'version':'daily-path-prefix-diagnostics-v1','checked_at':as_of.isoformat(),'primary':primary,
            'prefix_groups':groups,'input_not_ready_attempt_count':sum(value=='INPUT_NOT_READY' for value in regimes.values()),
            'group_event_counts_may_overlap_across_vintages':True,'diagnostic_only':True,
            'primary_evaluator_changed':False,'promotion_gate_changed':False,
            'source':'read_only_local_post_freeze_ledger','production_change':False,'live_adjustment':0}


def read_ledger(path: Path):
    if not path.is_file():raise ValueError("Existing ledger file required")
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as database:
        database.row_factory=sqlite3.Row
        database.execute('BEGIN')
        version=database.execute('SELECT version FROM daily_path_meta WHERE singleton=1').fetchone()
        if version is None or version['version']!='daily-inventory-path-local-ledger-v1':
            raise ValueError("Unsupported ledger schema")
        attempts=[{'attempt_id':row['id'],'executed_at':row['executed_at'],**json.loads(row['payload_json'])} for row in
                  database.execute('SELECT id,executed_at,payload_json FROM daily_path_attempts ORDER BY id')]
        points=[]
        for row in database.execute('''SELECT p.attempt_id,p.payload_json,s.payload_json score_json
          FROM daily_path_points p LEFT JOIN daily_path_scores s ON s.point_id=p.id ORDER BY p.id'''):
            points.append({**json.loads(row['payload_json']),'attempt_id':row['attempt_id'],
                           'score':json.loads(row['score_json']) if row['score_json'] else None})
    return attempts,points


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--as-of')
    args=parser.parse_args()
    now=datetime.now(timezone.utc)
    as_of=parse_timestamp(args.as_of) if args.as_of else now
    if as_of>now:raise ValueError("Future diagnostic cutoff is not allowed")
    report=build_report(*read_ledger(args.ledger),as_of.isoformat())
    with args.output.open('x') as output:
        json.dump(report,output,indent=2,sort_keys=True,allow_nan=False);output.write('\n')
    print(json.dumps({'version':report['version'],'prediction_count':report['primary']['prediction_count'],
                      'scored_event_count':report['primary']['scored_event_count'],
                      'challenger_mae':report['primary']['challenger_event_balanced_mae'],'diagnostic_only':True}))


if __name__=='__main__':main()
