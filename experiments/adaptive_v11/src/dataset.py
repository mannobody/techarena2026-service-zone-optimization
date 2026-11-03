import hashlib,json,statistics,collections,re
from pathlib import Path
from features import features
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cache={};pairs=[];excluded=[];catalog=json.loads((R/'CATALOG.json').read_text())
basehash='5cc54b6ad0f02a3d6d471d0e2f9129c229b4925aaa2b2c01ce26bd5305a4963c'
for entry in catalog:
 if not entry['variants']or not entry['result_count']:continue
 p=ROOT/entry['path'];m=json.loads(p.read_text());s=m['spec'];rows=json.loads((p.parent/'results.json').read_text());seconds=s.get('seconds',0)
 if seconds<30:continue
 if any('checkpoint' in k for k in s)or'tail_competition'in str(p):continue
 controls=[k for k in s['variants']if m.get('binaries',{}).get(k)==basehash]
 if not controls:excluded.append(dict(series=entry['path'],reason='No exact-v4 binary SHA'));continue
 base=controls[0];by={(x.get('case'),x.get('seed'),x.get('variant')):x for x in rows}
 for variant,conf in s['variants'].items():
  if variant==base:continue
  binary=ROOT/conf['binary'];h=m['binaries'][variant]
  if not binary.exists()or sha(binary)!=h:excluded.append(dict(series=entry['path'],variant=variant,reason='binary missing/hash drift'));continue
  env=conf.get('env',{});method=h[:12]+':'+json.dumps({k:v for k,v in env.items()if k not in ['DBG','DBG2','GW_TRACE']},sort_keys=True)
  for case,inp in s['cases'].items():
   inp=ROOT/inp
   if not inp.exists():continue
   ih=sha(inp)
   if ih!=m['inputs'][case]:raise ValueError(inp)
   if ih not in cache:cache[ih]=dict(path=str(inp.relative_to(ROOT)),features=features(json.loads(inp.read_text())))
   for seed in s['seeds']:
    a=by.get((case,seed,variant));b=by.get((case,seed,base))
    if not a or not b:continue
    if not a.get('valid')or not b.get('valid'):excluded.append(dict(series=entry['path'],case=case,seed=seed,variant=variant,reason='invalid row'));continue
    av=a.get('official',a.get('objective'));bv=b.get('official',b.get('objective'))
    if not isinstance(av,(int,float))or not isinstance(bv,(int,float))or abs(bv)<1e-9:continue
    pairs.append(dict(series=str(p.parent.relative_to(ROOT)),seconds=seconds,case=case,input_sha256=ih,seed=seed,variant=variant,method=method,binary=str(binary.relative_to(ROOT)),env=env,base=bv,candidate=av,percent=100*(av-bv)/abs(bv),both_success=a.get('success')and b.get('success'),affinity_equal=a.get('affinity')==b.get('affinity'),binary_sha256=h))
(R/'FEATURES.json').write_text(json.dumps(cache,indent=2));(R/'HISTORICAL_PAIRS.json').write_text(json.dumps(pairs,indent=2));(R/'HISTORICAL_EXCLUSIONS.json').write_text(json.dumps(excluded,indent=2))
for method in sorted(set(p['method']for p in pairs if p['seconds']==280)):
 ps=[p for p in pairs if p['method']==method and p['seconds']==280];cases=set(p['input_sha256']for p in ps);means=[statistics.mean(x['percent']for x in ps if x['input_sha256']==c)for c in cases]
 print(ps[0]['binary'],ps[0]['env'],'n',len(ps),'inputs',len(cases),'mean',round(statistics.mean(means),4),'worst',round(min(p['percent']for p in ps),4),'bad',sum(not p['both_success']for p in ps))
print('ALL full matched pairs',len(pairs),'inputs',len(cache),'exclusions',len(excluded))
