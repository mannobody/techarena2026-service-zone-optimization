import hashlib,json,random,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'tools'))
import gen
split=sys.argv[1]if len(sys.argv)>1 else 'dev'
assert split in ['dev','holdout']
d=R/'inputs'/split;d.mkdir(exist_ok=False)
offset=960000 if split=='dev'else 970000
specs=[
 ('small_road',dict(ns=14,no=4,nw=8,nsk=3,dist='road',af=.8,A=0,tmax=7,wsk=2)),
 ('small_anti',dict(ns=16,no=5,nw=10,nsk=3,dist='anti',af=.05,A=1,tmax=5,wsk=2)),
 ('small_grid',dict(ns=15,no=4,nw=6,nsk=3,layout='grid',offices='onsite',af=1,A=0,tmax=5,wsk=2)),
 ('small_multi',dict(ns=13,no=6,nw=5,nsk=4,dist='road',af=.2,A=1,tmax=6,wsk=3,deficit=1)),
 ('small_alpha0',dict(ns=16,no=6,nw=12,nsk=3,af=0,A=3,tmax=3,wsk=2)),
 ('small_load',dict(ns=16,no=3,nw=8,nsk=2,dist='road',af=4,A=1,tmax=9,wsk=1)),
 ('medium_road',dict(ns=100,no=7,nw=20,nsk=4,dist='road',af=.02,A=2,tmax=5)),
 ('medium_anti',dict(ns=160,no=9,nw=28,nsk=4,dist='anti',af=.01,A=4,tmax=3)),
 ('medium_A0',dict(ns=140,no=8,nw=18,nsk=3,af=.5,A=0,tmax=6,wsk=2)),
 ('medium_multi',dict(ns=180,no=10,nw=12,nsk=5,dist='road',af=.03,A=4,tmax=4,wsk=3,deficit=2)),
 ('cluster_alpha0',dict(ns=320,no=10,nw=28,nsk=5,layout='cluster',af=0,A=12,tmax=3)),
 ('grid_boundary',dict(ns=120,no=8,nw=22,nsk=3,layout='grid',offices='onsite',af=.1,A=1,tmax=4)),
 ('large',dict(ns=1200,no=16,nw=40,nsk=6,dist='road',af=.01,A=20,tmax=4)),
 ('huge',dict(ns=10000,no=24,nw=64,nsk=6,af=.01,A=100,tmax=3)),
]
out={}
for j,(name,kw)in enumerate(specs):
    p=d/(name+'.json');gen.gen2(offset+j,str(p),**kw)
    out[name]=dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),seed=offset+j,parameters=kw)
(R/(split.upper()+'_INPUTS.json')).write_text(json.dumps(out,indent=2))
print(json.dumps(dict(split=split,count=len(out),generator_sha256=hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest())))
