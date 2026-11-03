"""Audit the unfinished external study; TL250 stays separate from TL280."""
import json,hashlib,statistics,collections,os
from pathlib import Path
from features import features
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15});p=ROOT/'results/local/compare7_30_tl250_j5';m=json.loads((p/'manifest.json').read_text());rows=json.loads((p/'results.json').read_text())
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode();hc={}
assert sha(p/'validator.py')==m['validator_sha256']==sha(ROOT/'task/validate_solution.py')
for sid,s in m['sources'].items():
 for file,h in s['files'].items():assert sha(p/'sources'/sid/'tree'/file)==h,(sid,file)
base=next(k for k,v in m['variants'].items()if'v4_exact'in v['aliases']);assert m['sources'][m['variants'][base]['source']]['effective_sha256']=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
for x in rows:
 assert x['record_sha256']==hashlib.sha256(canon({k:v for k,v in x.items()if k!='record_sha256'})).hexdigest(),x['job_id']
 assert x['manifest_sha256']==sha(p/'manifest.json')
 assert sha(p/'sources'/m['variants'][x['variant']]['source']/'solution')==x['binary_sha256']
 for name,h in x['artifacts'].items():
  q=p/name
  if q not in hc:hc[q]=sha(q)
  assert hc[q]==h,name
F={}
for h in sorted(set(x['input']for x in rows)):
 q=p/'inputs'/(h+'.json');assert sha(q)==h
 F[h]=dict(features=features(json.loads(q.read_text())),aliases=m['cases'][h]['aliases'])
by={(x['input'],x['seed'],x['variant']):x for x in rows};pairs=[]
for x in rows:
 b=by.get((x['input'],x['seed'],base))
 if x['variant']==base or not b:continue
 assert x['cpus']==b['cpus']
 pairs.append(dict(input=x['input'],case_alias=x['case_alias'],seed=x['seed'],variant=x['variant_alias'],candidate=x['objective'],base=b['objective'],percent=100*(x['objective']-b['objective'])/abs(b['objective'])if abs(b['objective'])>1e-9 else None,candidate_status=x['status'],base_status=b['status'],cpus=x['cpus'],candidate_timeout=x['timeout'],base_timeout=b['timeout']))
summary={}
for v in sorted(set(x['variant']for x in pairs)):
 a=[x for x in pairs if x['variant']==v and x['percent']is not None];ids=set(x['input']for x in a);means=[statistics.mean(x['percent']for x in a if x['input']==h)for h in ids]
 summary[v]=dict(pairs=len(a),inputs=len(ids),mean_case_percent=statistics.mean(means),worst=min(x['percent']for x in a),wins=sum(x['candidate']>x['base']+1e-7 for x in a),ties=sum(abs(x['candidate']-x['base'])<=1e-7 for x in a),losses=sum(x['candidate']<x['base']-1e-7 for x in a),non_ok=sum(x['candidate_status']!='ok'or x['base_status']!='ok'for x in a))
complete=[]
for h,seed in sorted(set((x['input'],x['seed'])for x in rows)):
 a=[by.get((h,seed,v))for v in m['variants']]
 if not all(a):continue
 b=by[h,seed,base]
 if abs(b['objective'])<=1e-9:continue
 complete.append(dict(input=h,seed=seed,case_alias=b['case_alias'],cpus=b['cpus'],features=F[h]['features'],scores={x['variant_alias']:dict(objective=x['objective'],percent=100*(x['objective']-b['objective'])/abs(b['objective']),status=x['status'])for x in a}))
result=dict(root=str(p.relative_to(ROOT)),seconds=250,observed=len(rows),planned=630,unfinished=394,valid=sum(x['valid']for x in rows),statuses=dict(collections.Counter(x['status']for x in rows)),verified_artifact_files=len(hc),manifest_sha256=sha(p/'manifest.json'),exact_v4_source=True,control_binary_sha256=sha(p/'sources'/m['variants'][base]['source']/'solution'),warning='Different study flags/link and TL250; do not pool with TL280. Unfinished blocks not filled or relabelled complete. Timed-out checkpoints retained in all-valid statistics, separately from statusok.',summary=summary,complete_blocks=complete,pairs=pairs,features=F)
(R/'WIDE_TL250_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k not in ['pairs','features','complete_blocks']}));print('complete blocks',len(complete),'inputs',len(set(x['input']for x in complete)))
