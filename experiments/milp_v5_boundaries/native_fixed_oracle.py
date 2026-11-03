from regions import *
import subprocess,os,json,itertools
D=H/'logs/native_fixed_oracle';D.mkdir();s=(H/'artifacts/oracle.cpp').read_text().replace('v52_select(I,R,base,a,op,staff,59,true);','for(int w=0;w<I.nw;w++)staff[w]=w%I.no;v52_select(I,R,base,a,op,staff,59,false);')
p=H/'artifacts/oracle_fixed.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix('')),'-ldl'],check=True);rs=[]
for f in sorted((H/'logs/oracle_v2').glob('311*.json')):
 d=json.loads(f.read_text());I=Instance(d['data']);regions=d['regions'];have=[set() for _ in range(I.m)]
 for w,ks in enumerate(I.workers):have[w%I.m].update(ks)
 choices=[]
 for o in range(I.m):
  opts=[(set(),0,0,0)]
  for e in regions:
   if e['o']!=o:continue
   ss=[s for s in e['sites'] if set(I.sites[s]['tasks'])<=have[o]]
   for bits in range(1,1<<len(ss)):
    chosen=[s for j,s in enumerate(ss) if bits>>j&1]
    if len(chosen)>I.cap[o]:continue
    opts.append((set(e['footprint']),len(chosen),sum(int(I.tasks[s]) for s in chosen),sum(float(I.profit[o,s]) for s in chosen)-I.cost[o]))
  choices.append(opts)
 best=0
 for cs in itertools.product(*choices):
  if cs[0][0]&cs[1][0]:continue
  counts=[c[1] for c in cs if c[1]];loads=[c[2] for c in cs if c[1]]
  if counts and max(counts)-min(counts)<=I.a:best=max(best,sum(c[3] for c in cs)-I.alpha*(max(loads)-min(loads)))
 inp=H/'logs/native_oracle'/(f.stem+'.input.json');sp=H/'logs/native_oracle'/(f.stem+'.regions');out=D/(f.stem+'.solution.json');q=subprocess.run([str(p.with_suffix('')),str(inp),str(out),str(sp)],env=dict(os.environ,LD_LIBRARY_PATH='/tmp/ta-boundary-venv/lib64/python3.14/site-packages/highspy'),capture_output=True,text=True,timeout=60);assert q.returncode==0,q.stderr;score=value(I,json.loads(out.read_text()));assert not isinstance(score,str),score;assert abs(score-best)<1e-6,(f,score,best);rs.append(dict(seed=f.stem,value=score,expected=best));print(f.stem,score,flush=True)
(D/'results.json').write_text(json.dumps(rs,indent=2))
