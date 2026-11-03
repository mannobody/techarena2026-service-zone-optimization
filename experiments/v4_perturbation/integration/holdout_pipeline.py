"""Run the frozen independent protocol, including its predeclared extra seeds.

No solver edits, no adaptive parameter selection, no omission after bad outcomes.
Every child must finish before its dependent analysis starts. Existing log
directories are refused by the shared runner rather than overwritten.
"""
import json, subprocess, sys, time
from pathlib import Path
from verify_freeze import verify

I = Path(__file__).resolve().parent
R = I.parent
ROOT = R.parents[1]
state = {'started_unix':time.time(), 'events':[]}
progress = I/'HOLDOUT_PIPELINE_PROGRESS.json'

def step(label, command):
    event = {'label':label, 'command':command, 'started_unix':time.time()}
    state['events'].append(event)
    progress.write_text(json.dumps(state, indent=2))
    log = I/f'PIPELINE_{label}.log'
    with log.open('x') as output:
        p = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
    event.update(returncode=p.returncode, ended_unix=time.time())
    progress.write_text(json.dumps(state, indent=2))
    if p.returncode:
        raise RuntimeError(f'{label} failed, see {log}')

if __name__ == '__main__':
    assert not progress.exists(), 'pipeline already started; inspect saved state'
    py=sys.executable
    for seconds in [60,280]:
        verify(I/f'HOLDOUT{seconds}.json')
        step(f'holdout{seconds}', [py,str(R/'shared/run_blocks.py'),str(I/f'HOLDOUT{seconds}.json')])
        step(f'evaluate{seconds}', [py,str(I/'evaluate_holdout.py'),str(seconds)])
        extra = I/f'HOLDOUT{seconds}_VARIANCE.json'
        if extra.exists():
            verify(extra)
            step(f'variance{seconds}', [py,str(R/'shared/run_blocks.py'),str(extra)])
            dest = json.loads(extra.read_text())['destination']
            step(f'analyze_variance{seconds}', [py,str(R/'shared/analyze.py'),str(ROOT/dest),str(I/f'HOLDOUT{seconds}_VARIANCE_SUMMARY.json')])
        step(f'finalize{seconds}', [py,str(I/'finalize_holdout.py'),str(seconds)])
    state['completed_unix']=time.time()
    progress.write_text(json.dumps(state, indent=2))
