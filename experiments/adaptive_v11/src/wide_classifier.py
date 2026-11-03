"""Auxiliary TL250 grouped policy diagnostic; never joins TL280 labels."""
import json,statistics,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];wide=json.loads((R/'WIDE_TL250_AUDIT.json').read_text());bins=json.loads((R/'CLASSIFIER_EXPLORATION.json').read_text())['bins'];blocks=wide['complete_blocks'];methods=sorted(set(blocks[0]['scores'])-{'geometry_robust'}) # timeout-prone experimental geometry retained in audit, not proposed for deployment
D=[]
for h in sorted(set(x['input']for x in blocks)):
 a=[x for x in blocks if x['input']==h];D.append(dict(h=h,f=a[0]['features'],case=a[0]['case_alias'],y={m:statistics.mean(x['scores'][m]['percent']for x in a)for m in methods},raw={m:[x['scores'][m]['percent']for x in a]for m in methods}))
def leaf(d):
 means={m:statistics.mean(x['y'][m]for x in d)for m in methods};eligible=[m for m in methods if m=='v4_exact'or means[m]>.1 and min(x['y'][m]for x in d)>=-1]
 best=max(eligible,key=lambda m:means[m]);return dict(action=best,n=len(d),mean=means[best])
def predict(t,f):return t['action']if'action'in t else predict(t['left']if f[t['feature']]<=t['threshold']else t['right'],f)
def score(t,d):return sum(x['y'][predict(t,x['f'])]for x in d)
def train(d,depth,minleaf):
 t=leaf(d);v=score(t,d)
 if depth:
  for k,thresholds in bins.items():
   for th in thresholds:
    l=[x for x in d if x['f'][k]<=th];r=[x for x in d if x['f'][k]>th]
    if min(len(l),len(r))<minleaf:continue
    a=dict(feature=k,threshold=th,left=train(l,depth-1,minleaf),right=train(r,depth-1,minleaf));s=score(a,d)
    if s>v+.5:t=a;v=s
 return t
results=[]
for depth in [0,1,2]:
 for minleaf in [3,4,5]:
  out=[]
  for x in D:
   t=train([z for z in D if z['h']!=x['h']],depth,minleaf);a=predict(t,x['f']);out.append(dict(case=x['case'],method=a,percent=x['y'][a],worst=min(x['raw'][a])))
  results.append(dict(depth=depth,minleaf=minleaf,mean=statistics.mean(x['percent']for x in out),worst=min(x['worst']for x in out),rows=out,tree=train(D,depth,minleaf)))
results.sort(key=lambda x:x['mean'],reverse=True)
constant={m:statistics.mean(x['y'][m]for x in D)for m in methods};oracle=statistics.mean(max(x['y'].values())for x in D)
(R/'WIDE_TL250_CLASSIFIER.json').write_text(json.dumps(dict(inputs=len(D),complete_blocks=len(blocks),methods=methods,constant=constant,oracle=oracle,policies=results,warning='Exploratory TL250 model selection on unfinished21-input data; do not treat as independent or TL280 confirmation. One worker counterexample dominates positive mean, and existing v9/v10 tiny already covers that class.'),indent=2))
print(json.dumps(dict(inputs=len(D),complete_blocks=len(blocks),constant=constant,oracle=oracle,top={k:v for k,v in results[0].items()if k!='rows'})))
