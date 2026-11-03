from pathlib import Path
import sys,json,subprocess,random,itertools,os
from grouped import Instance,value
H=Path(__file__).resolve().parent;D=H/'logs/native_oracle_v2';D.mkdir()
s=(H/'artifacts/native_v1.cpp').read_text();prefix=s[:s.index('int main(int argc, char** argv)')]
driver=r'''
int main(int argc,char**argv){if(argc<5)return 2;Inst I=load_instance(argv[1]);g_geo_grid.init(I);g_fd=open(argv[2],O_WRONLY|O_CREAT|O_TRUNC,0644);publish("[]\n");ifstream f(argv[3]);vector<int>a(I.ns,-1);vector<char>op(I.no,0);for(int&x:a){f>>x;if(x>=0)op[x]=1;}g_wdfs_deadline=59;Sol s;s.init(I);s.load_state(a,op);vector<int>staff;if(!s.greedy_workers(&staff))return 3;if(!v5_api().ready)return 4;offer(I,s);v5_select(I,s,a,op,staff,59,atoi(argv[4]));}
'''
p=H/'artifacts/oracle_native_v2.cpp';p.write_text(prefix+driver);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix('')),'-ldl'],check=True)
cases=[]
for old in []:
 cases.append((old['seed'],old['data'],[dict(officeId=o,sites=list(range(o*4,o*4+4)),workers=[o]) for o in range(3)],False))
for seed in range(261000,261020):
 r=random.Random(seed);n=12;m=3;data=dict(sites=[],offices=[],workers=[[0],[0],[1],[1],[0,1]],distances=[],maxDifference=r.choice([0,1,12]),balanceCoefficient=r.choice([0,.5,7,30]));inc=[];profits=[]
 for o in range(3):
  data['offices'].append(dict(x=10*o,y=0,cost=r.randrange(10),maxSize=4))
  for j in range(4):
   tasks=([0],[1],[0,1])[o] if j==3 else [r.randrange(2) for _ in range(r.randrange(4))];data['sites'].append(dict(x=10*o+.125*(j+1),y=.125*(j+1),reward=100,tasks=list(tasks)));profits.append(r.randrange(-30,80))
  inc.append(dict(officeId=o,sites=[o*4+3],workers=[[0],[2],[4]][o]))
 data['distances']=[[100-profits[s] if s//4==o else 1000 for s in range(n)] for o in range(m)];cases.append((seed,data,inc,True))
rows=[]
for seed,data,inc,joint in cases:
 I=Instance(data);pools={o:list(range(o*4,o*4+4)) for o in range(3)};feas=set()
 for wa in itertools.product(range(-1,3),repeat=I.w):
  masks=[0]*3
  for w,o in enumerate(wa):
   if o>=0:
    for k in I.workers[w]:masks[o]|=1<<k
  for req in itertools.product(range(4 if joint else 2),repeat=3):
   if all(req[o]&masks[o]==req[o] for o in range(3)):feas.add(req)
 best=0
 for bits in range(1<<I.n):
  ss=[[s for s in pools[o] if bits>>s&1] for o in range(3)]
  if any(not v for v in ss):continue
  counts=list(map(len,ss))
  if max(counts)-min(counts)>I.a:continue
  req=tuple(sum(1<<k for k in set(k for s in ss[o] for k in I.sites[s]['tasks'])) for o in range(3))
  if req not in feas:continue
  loads=[sum(int(I.tasks[s]) for s in v) for v in ss];score=sum(float(I.profit[o,s]) for o in range(3) for s in ss[o])-sum(I.cost)-I.alpha*(max(loads)-min(loads));best=max(best,score)
 inp=D/f'{seed}.input.json';inp.write_text(json.dumps(data));ap=D/f'{seed}.asg';a=[-1]*I.n
 for r in inc:
  for x in r['sites']:a[x]=r['officeId']
 ap.write_text(' '.join(map(str,a)));out=D/f'{seed}.solution.json';q=subprocess.run([str(p.with_suffix('')),str(inp),str(out),str(ap),str(int(joint))],env=dict(os.environ,LD_LIBRARY_PATH='/tmp/ta-boundary-venv/lib64/python3.14/site-packages/highspy'),capture_output=True,text=True,timeout=60);assert q.returncode==0,(seed,q.stderr);score=value(I,json.loads(out.read_text()));assert not isinstance(score,str),(seed,score);assert abs(score-best)<1e-6,(seed,score,best);rows.append(dict(seed=seed,joint=joint,expected=best,value=score));print(seed,score,flush=True)
(D/'results.json').write_text(json.dumps(rows,indent=2));print(len(rows),'native matches')
