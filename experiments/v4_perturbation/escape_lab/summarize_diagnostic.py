from pathlib import Path
import json,re,statistics,itertools,hashlib
lab=Path(__file__).resolve().parent;root=lab.parents[2];d=lab/'logs/diagnostic'
s=json.loads((d/'MANIFEST.json').read_text())['spec'];runs=json.loads((d/'results.json').read_text());expect=set(itertools.product(s['cases'],s['seeds'],s['variants']));keys=[(x['case'],x['seed'],x['variant']) for x in runs];assert len(keys)==len(set(keys)) and set(keys)==expect
rows=[]
for case,seed,v in keys:
 for line in (d/f'{case}_{seed}_{v}.stderr').read_text().splitlines():
  if line.startswith('ESCAPE_RECOVERY '):
   r={k:float(x) for k,x in re.findall(r'(\w+)=([-+\d.eE]+)',line)};r.update(case=case,seed=seed,variant=v);rows.append(r)
def dist(v):return dict(n=len(v),min=min(v),median=statistics.median(v),max=max(v),mean=statistics.mean(v)) if v else dict(n=0)
out={'runs':len(runs),'success':sum(r['success'] for r in runs),'records':rows,'modes':{}}
for v in s['variants']:
 a=[r for r in rows if r['variant']==v];e=[r for r in a if r['changed'] and not r['failed']]
 out['modes'][v]={'episodes':len(a),'failed':sum(r['failed'] for r in a),'feasibility_rejected':sum(r['failed_reason']==1 for r in a),'loss_rejected':sum(r['failed_reason']==2 for r in a),'effective_changed_kicks':len(e),'effective_recovered':sum(r['recovered'] for r in e),'effective_censored':sum(not r['recovered'] for r in e),'effective_first_return':dist([r['first_return'] for r in e if r['recovered']]),'effective_censor_duration':dist([r['censored_seconds'] for r in e if not r['recovered']]),'all_recovered':sum(r['recovered'] for r in a),'all_first_return':dist([r['first_return'] for r in a if r['recovered']]),'all_censor_duration':dist([r['censored_seconds'] for r in a if not r['recovered']])}
f=json.loads((lab/'FREEZE_SCREEN.json').read_text());names=['src/escape.h','src/escape_v4.cpp','bin/escape_v4','bin/post_escape'];out['quality_freeze_unchanged']={name:hashlib.sha256((lab/name).read_bytes()).hexdigest()==f['files'][str((lab/name).relative_to(root))] for name in names}
(lab/'DIAGNOSTIC_SUMMARY.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))
