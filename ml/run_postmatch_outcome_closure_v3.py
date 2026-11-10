"""Versioned orchestration using the corrected immutable history-score path adapter."""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from ml import run_postmatch_outcome_closure_v1 as base
from ml.c1_history_residual_v1 import ResidualRuntime

VERSION='postmatch-outcome-closure-v3'


def contract(branch,commit):
    result=base.contract(branch,commit)
    result.update(version=VERSION,history_score_path_adapter='c1-history-score-path-adapter-v1')
    for name in ('ml/run_postmatch_outcome_closure_v3.py','ml/c1_history_scoring_adapter_v1.py'):
        result['source_hashes'][name]=hashlib.sha256((base.ROOT/name).read_bytes()).hexdigest()
    return result


def score_unchanged():
    from ml.c1_outcome_scoring_bridge_v1 import run_scorers
    result={'old_fixed_lanes':run_scorers(),
            'support26':base.score_support_only(Path('/workspace/ops-runtime/2026-11-05-c1-support26-collector'))}
    for name,module,runtime in (
        ('history','ml.c1_history_scoring_adapter_v1','2026-11-05-c1-history-residual-collector'),
        ('fresh_structural','ml.run_structural_history_refresh_v1','2026-11-06-structural-history-refresh-collector')):
        command=[sys.executable,'-m',module,'cycle','--runtime','/workspace/ops-runtime/'+runtime]
        process=subprocess.run(command,cwd=base.ROOT,capture_output=True,text=True,timeout=240)
        if process.returncode:raise ValueError('Unchanged scorer failed closed: '+name)
        result[name]=json.loads(process.stdout)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--branch',required=True);p.add_argument('--commit',required=True);p.add_argument('--once',action='store_true');a=p.parse_args()
    if a.runtime.resolve().is_relative_to(base.ROOT):raise ValueError('Private runtime required')
    a.runtime.mkdir(mode=0o700,parents=True,exist_ok=True);configuration=contract(a.branch,a.commit);path=a.runtime/'source-contract.json'
    if path.exists():
        if json.loads(path.read_text())!=configuration:raise ValueError('Closure v3 source changed')
    else:
        if base.api('/git/ref/heads/'+a.branch)['object']['sha']!=a.commit:raise ValueError('Published immutable execution ref required')
        base.save(path,configuration)
    with (a.runtime/'closure.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        base.save(a.runtime/'launch.json',{'version':VERSION,'pid':os.getpid(),'started_at':datetime.now(timezone.utc).isoformat(),
            'until':base.UNTIL,'local_check_seconds':60,'host_dependent':True})
        statepath=a.runtime/'state.json';state=json.loads(statepath.read_text()) if statepath.exists() else {}
        while datetime.now(timezone.utc)<base.stamp(base.UNTIL):
            if configuration!=contract(a.branch,a.commit):raise ValueError('Active v3 closure source changed')
            try:result=base.tick(a.runtime,state,configuration,datetime.now(timezone.utc),scorer=score_unchanged)
            except Exception as exc:
                result={'status':'FAILED_CLOSED','checked_at':datetime.now(timezone.utc).isoformat(),'error_type':type(exc).__name__,
                    'reason':str(exc)[:180],'production_change':False,'live_adjustment':0}
            result['operational_orchestrator']=VERSION
            base.save(a.runtime/'latest-cycle.json',result)
            with (a.runtime/'audit.jsonl').open('a') as file:file.write(json.dumps(result)+'\n')
            print(json.dumps(result),flush=True)
            if a.once:break
            time.sleep(min(60,max(0,(base.stamp(base.UNTIL)-datetime.now(timezone.utc)).total_seconds())))


if __name__=='__main__':main()
