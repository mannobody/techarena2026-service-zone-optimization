"""Exploratory grouped validation. All historical inputs are development now."""
import json,statistics,math,itertools,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=json.loads((R/'HISTORICAL_PAIRS.json').read_text());F=json.loads((R/'FEATURES.json').read_text())
# Predeclared physical bins, deliberately no input signatures, ids, seed, names or fitted midpoints.
BINS={'ns':[16,64,256,1024,4096],'balance_pressure':[0,.05,.2,1,5],'count_slack':[0,.1,.5,1,2],'geo_distance_corr':[-.5,.5,.95],'nearest_agreement':[.25,.75,.99],'capacity_ratio':[.75,1,1.25,2],'workers_per_skill_office':[.25,.5,1],'multiskill_fraction':[0,.5],'unservable_fraction':[0,.1],'task_mean':[1,2,4],'positive_pair_fraction':[.25,.5,.75,.95],'anisotropy':[.1,.5,.9]}
ps=[p for p in P if p['seconds']==280 and p['binary_sha256'].startswith('c3f76e')and p['env'].get('GW_MODE')=='1']
D=[]
for h in sorted(set(p['input_sha256']for p in ps)):
 a=[p for p in ps if p['input_sha256']==h]
 D.append(dict(h=h,f=F[h]['features'],y=statistics.mean(p['percent']for p in a),raw=[p['percent']for p in a],name=a[0]['case']))
def leaf(d,margin):
 m=statistics.mean(x['y']for x in d)if d else 0
 return dict(action='geometry'if m>margin else 'v4',n=len(d),mean=m)
def score(t,d):return sum(x['y']if predict(t,x['f'])=='geometry'else 0 for x in d)
def train(d,depth,minleaf,margin):
 best=leaf(d,margin);s=score(best,d)
 if depth:
  for k,bins in BINS.items():
   for th in bins:
    l=[x for x in d if x['f'][k]<=th];r=[x for x in d if x['f'][k]>th]
    if min(len(l),len(r))<minleaf:continue
    t=dict(feature=k,threshold=th,left=train(l,depth-1,minleaf,margin),right=train(r,depth-1,minleaf,margin));v=score(t,d)
    # Complexity cost in percentage points per new split; fixes tie preference for constant policy.
    if v>s+.5:best=t;s=v
 return best
def predict(t,f):return t['action']if'action'in t else predict(t['left']if f[t['feature']]<=t['threshold']else t['right'],f)
def evaluate(depth,minleaf,margin):
 rows=[]
 for x in D:
  t=train([z for z in D if z['h']!=x['h']],depth,minleaf,margin);a=predict(t,x['f']);rows.append(dict(case=x['name'],action=a,mean=x['y']if a=='geometry'else 0,worst=min(x['raw'])if a=='geometry'else 0))
 return dict(depth=depth,minleaf=minleaf,margin=margin,mean=statistics.mean(x['mean']for x in rows),worst=min(x['worst']for x in rows),rows=rows,tree=train(D,depth,minleaf,margin))
results=[evaluate(d,n,m)for d in [0,1,2]for n in [3,4,5]for m in [0,1,3]]
results.sort(key=lambda x:(x['mean'],x['worst']),reverse=True)
(R/'CLASSIFIER_EXPLORATION.json').write_text(json.dumps(dict(method='Grouped leave-one-input-out, historical TL280 only. Model-selection evidence, not independent confirmation.',bins=BINS,inputs=D,policies=results),indent=2))
for a in results[:6]:print(json.dumps({k:v for k,v in a.items()if k!='rows'}))
print('Best rows',json.dumps(results[0]['rows']))
