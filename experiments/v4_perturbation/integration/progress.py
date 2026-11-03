"""Read-only compact progress of the frozen protocol; no score-driven decisions."""
import json,time
from pathlib import Path
I=Path(__file__).resolve().parent;ROOT=I.parents[2]
state=json.loads((I/'HOLDOUT_PIPELINE_PROGRESS.json').read_text())
event=state['events'][-1]
report={'phase':event['label'],'phase_elapsed_seconds':round(time.time()-event['started_unix']),
        'pipeline_complete':'completed_unix' in state,'last_returncode':event.get('returncode')}
for label in ['holdout60','holdout60_variance','holdout280','holdout280_variance']:
    d=I/'logs'/label
    if not (d/'MANIFEST.json').exists():continue
    spec=json.loads((d/'MANIFEST.json').read_text())['spec']
    rows=json.loads((d/'results.json').read_text()) if (d/'results.json').exists() else []
    report[label]={'expected':len(spec['cases'])*len(spec['seeds'])*len(spec['variants']),
        'completed':len(rows),'success':sum(x['success'] for x in rows),
        'max_wall':max([x['wall'] for x in rows],default=None),
        'snapshot_files':len(list(d.glob('*.t*.solution.json'))),'complete':(d/'COMPLETE.json').exists()}
print(json.dumps(report,indent=2))
