import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'tools'))
import gen
params=[
 ('road120',dict(ns=120,no=7,nw=20,nsk=4,dist='road',af=.02,A=2,tmax=5)),
 ('anti180',dict(ns=180,no=10,nw=30,nsk=5,dist='anti',af=.015,A=4,tmax=3)),
 ('equal_count150',dict(ns=150,no=8,nw=18,nsk=3,af=.6,A=0,tmax=7,wsk=2)),
 ('multi220',dict(ns=220,no=11,nw=13,nsk=6,dist='road',af=.03,A=4,tmax=4,wsk=3,deficit=2)),
 ('cluster400',dict(ns=400,no=12,nw=32,nsk=5,layout='cluster',af=0,A=10,tmax=3,span=1.,dscale=10000.)),
 ('grid160',dict(ns=160,no=9,nw=24,nsk=4,layout='grid',offices='onsite',af=.12,A=1,tmax=4,wsk=2)),
 ('road1500',dict(ns=1500,no=18,nw=48,nsk=7,dist='road',af=.015,A=20,tmax=4)),
 ('huge10000',dict(ns=10000,no=24,nw=64,nsk=6,af=.01,A=100,tmax=3)),
]
if len(sys.argv)>1 and sys.argv[1]=='plan':
 p=R/'INDEPENDENT_PLAN.json';assert not p.exists()
 p.write_text(json.dumps(dict(parameters=params,seed_offset=1080000,run_seeds=[10501,10502,10503],seconds=280,generator_sha256=hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()),indent=2))
else:
 freeze=json.loads((R/'FREEZE.json').read_text())
 for p,h in freeze['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 plan=json.loads((R/'INDEPENDENT_PLAN.json').read_text());assert plan['parameters']==[[name,kw]for name,kw in params]
 assert plan['generator_sha256']==hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
 d=R/'inputs/fresh';d.mkdir(exist_ok=False);rows={}
 old=set()
 for q in (ROOT/'experiments/structural_v9').glob('*INPUTS.json'):
  a=json.loads(q.read_text());old|={x['sha256']for x in a.values()if isinstance(x,dict)and 'sha256'in x}
 for j,(name,kw)in enumerate(params):
  p=d/(name+'.json');gen.gen2(plan['seed_offset']+j,str(p),**kw);h=hashlib.sha256(p.read_bytes()).hexdigest();assert h not in old
  rows[name]=dict(path=str(p.relative_to(ROOT)),sha256=h,seed=plan['seed_offset']+j,parameters=kw)
 (R/'FRESH_INPUTS.json').write_text(json.dumps(rows,indent=2))
 selection=json.loads((R/'SELECTION.json').read_text());s=json.loads((R/selection['long_spec']).read_text());s['name']='independent280';s['cases']={k:v['path']for k,v in rows.items()};s['seeds']=plan['run_seeds'];s['seconds']=plan['seconds']
 s['variants']={k:v for k,v in s['variants'].items()if k in ['v4','v9',selection['variant']]}
 (R/'INDEPENDENT280.json').write_text(json.dumps(s,indent=2));print(json.dumps(dict(fresh_inputs=len(rows),no_overlap=True,selected=selection['variant'])))
