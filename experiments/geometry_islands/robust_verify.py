import json,random,math,struct,subprocess,time
from fractions import Fraction as F
from pathlib import Path
from shapely.geometry import MultiPoint,Point
H=Path(__file__).resolve().parent;r=random.Random(161000);lines=[];expected=[];kinds=[]
def bits(x):return struct.unpack('Q',struct.pack('d',x))[0]
for i in range(18000):
 if i%3==0:pts=[(math.ldexp(r.uniform(-1,1),r.randint(-1000,1000)),math.ldexp(r.uniform(-1,1),r.randint(-1000,1000))) for j in range(3)]
 elif i%3==1:
  a=(r.uniform(-1e8,1e8),r.uniform(-1e8,1e8));b=(r.uniform(-1e8,1e8),r.uniform(-1e8,1e8));t=r.random();c=(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]));c=(math.nextafter(c[0],math.inf if i%2 else -math.inf),c[1]);pts=[a,b,c]
 else:
  pts=[(r.randint(-10,10)*2.**r.randint(-100,100),r.randint(-10,10)*2.**r.randint(-100,100)) for j in range(3)]
  if i%7==0:pts[2]=pts[1]
 a,b,c=[tuple(map(F,p)) for p in pts];v=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);expected.append((v>0)-(v<0));kinds.append('orientation');lines.append('0 '+' '.join(str(bits(x)) for p in pts for x in p))
for i in range(4000):
 n=r.randint(1,24);pts=[(r.randrange(-8,9),r.randrange(-8,9)) if i%3 else (r.random(),r.random()) for _ in range(n)]
 if i%7==0:pts=[(x,0) for x,y in pts]
 q=r.choice(pts) if i%3==0 else (r.uniform(-10,10),r.uniform(-10,10));expected.append(int(MultiPoint(pts).convex_hull.covers(Point(q))));kinds.append('covers');lines.append('1 '+str(n)+' '+' '.join(format(float(x),'.17g') for p in pts+[q] for x in p))
while not (H/'build_robust.json').exists():time.sleep(2)
p=subprocess.run([str(H/'artifacts/robust_oracle')],input='\n'.join(lines)+'\n',text=True,capture_output=True,timeout=65);got=list(map(int,p.stdout.split()));assert len(got)==len(expected),(len(got),len(expected),p.stderr)
failed=[dict(index=i,type=kinds[i],actual=a,expected=b,input=lines[i]) for i,(a,b) in enumerate(zip(got,expected)) if a!=b]
(H/'logs/robust_oracle.json').write_text(json.dumps(dict(seed=161000,orientation_count=18000,covers_count=4000,failures=failed,rc=p.returncode),indent=2));print('passed',len(got)-len(failed),'/',len(got));print(failed[:4]);assert not failed
