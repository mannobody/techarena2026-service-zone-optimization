import json,re,time,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];name=sys.argv[1];d=R/'logs'/name
if not d.exists():print(json.dumps(dict(series=name,not_started=True)));sys.exit()
s=json.loads((d/'MANIFEST.json').read_text())['spec'];rows=[]
for p in d.glob('*.json'):
 if p.name in ['MANIFEST.json','results.json','ANALYSIS.json','SUMMARY.json']or p.name.endswith('solution.json')or p.name.endswith('analysis.json'):continue
 a=json.loads(p.read_text())
 if 'variant'in a:rows.append(a)
active=[]
for p in d.glob('*.stderr'):
 if p.with_suffix('.json').exists():continue
 txt=p.read_text();warm=re.findall(r'^(?:GEOWARM|wide_start).*$',txt,re.M)
 active.append(dict(run=p.stem,stderr_age=round(time.time()-p.stat().st_mtime,1),warm=warm[-1]if warm else None,snapshots=len(list(d.glob(p.stem+'.t*.solution.json')))))
print(json.dumps(dict(series=name,complete=len(rows),expected=len(s['cases'])*len(s['seeds'])*len(s['variants']),valid=sum(x['valid']for x in rows),working_success=sum(x['success']for x in rows),recent=[{k:x[k]for k in ['case','seed','variant','official','wall','success']}for x in sorted(rows,key=lambda x:x['ended_unix'])[-5:]],active=active),ensure_ascii=False))
