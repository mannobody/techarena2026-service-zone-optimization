"""Generate untouched inputs only after freeze; never overwrites prior inputs."""
import hashlib,json,random,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'tools'));import gen
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
f=json.loads((R/'integration/FINAL_FREEZE.json').read_text())
for k in ['source','binary']:assert sha(ROOT/f[k])==f[k+'_sha256']
classes=list(json.loads((R/'shared/DEV_INPUTS.json').read_text()))
d=R/'integration/inputs/holdout';d.mkdir(parents=True,exist_ok=False)
records={}
for j,name in enumerate(classes):
 seed=951000+100*j;base=name if name in gen.SUITE else 'medium'
 params=gen.SUITE[base][1](random.Random(seed))
 if name=='tightA':params['A']=0
 if name=='large':params['ns']=3500
 if name=='huge':params['ns']=10000
 if name=='negative':params.update(A=10000,dist='road')
 p=d/f'{name}.json';gen.gen2(seed,str(p),**params);data=json.loads(p.read_text());transforms=[]
 if name=='elongated':
  for x in data['sites']+data['offices']:x['y']*=.005
  transforms.append('y *= .005; original distances retained (coordinate/road mismatch)')
 if name=='negative':
  for k,x in enumerate(data['sites']):
   if k%3==0:x['reward']*=.03
  transforms.append('every third reward *= .03; A=10000')
 p.write_text(json.dumps(data,separators=(',',':')))
 records[name]={'path':str(p.relative_to(ROOT)),'generator_seed':seed,'parameters':params,'transforms':transforms,'sha256':sha(p)}
(R/'integration/HOLDOUT_INPUTS.json').write_text(json.dumps({'generated_unix':time.time(),'freeze_sha256':sha(R/'integration/FINAL_FREEZE.json'),'generator_sha256':sha(Path(__file__)),'gen_py_sha256':sha(ROOT/'tools/gen.py'),'inputs':records},indent=2))
pairs=[[0,1],[3,6],[8,10],[12,13],[14,15],[16,17],[18,19],[20,21]]
variants={'v4':{'binary':str((R/'baseline/v4').relative_to(ROOT)),'source':str((R/'baseline/frozen_v4.cpp').relative_to(ROOT)),'env':{'DBG':'1'}},'off':{'binary':f['binary'],'source':f['source'],'env':f['off_env']},'candidate':{'binary':f['binary'],'source':f['source'],'env':f['candidate_env']}}
for name,seconds,seeds,cases in [('holdout60',60,[2101,2102,2103],classes),('holdout280',280,[2201,2202],classes[:5]+['huge'])]:
 spec={'destination':str((R/'integration/logs'/name).relative_to(ROOT)),'seconds':seconds,'seeds':seeds,'cpu_pairs':pairs,'cases':{k:records[k]['path'] for k in cases},'variants':variants,'order_seed':421,'snapshots':[10,30,50] if seconds==60 else [60,120,200,260]}
 (R/'integration'/f'{name.upper()}.json').write_text(json.dumps(spec,indent=2))
print('Holdout generated after source/binary freeze; no solver run yet.')
