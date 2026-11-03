from pathlib import Path
import subprocess,json,hashlib
H=Path(__file__).resolve().parent;B=H/'baseline/solver'
sol=(B/'sol.h').read_text();sol=sol.replace('for (int i = 0; i < n; i++)\n                if (fabs(P[i].x', 'for (int i : g_geo_grid.query(*I,h[0].x-I->eps_len,h[0].x+I->eps_len,h[0].y-I->eps_len,h[0].y+I->eps_len))\n                if (fabs(P[i].x',1)
sol=sol.replace('for (int i = 0; i < n; i++) {\n                double X', 'double pad=2*I->eps_len+I->eps_cr/max(L,1e-300);\n            for (int i : g_geo_grid.query(*I,min(ax,ax+dx)-pad,max(ax,ax+dx)+pad,min(ay,ay+dy)-pad,max(ay,ay+dy)+pad)) {\n                double X',1)
sol=sol.replace('for (int i = 0; i < n; i++) {\n            double X','for (int i : g_geo_grid.query(*I,mnx,mxx,mny,mxy)) {\n            double X',1)
sol=sol.replace('for (int i = 0; i < np; i++) {\n                if (row[i]', 'for (int i : g_geo_grid.query(*I,mnx,mxx,mny,mxy)) {\n                if (row[i]',1)
sol=sol.replace('for (int i = 0; i < np; i++) {\n                if (row[i]', 'double pad=2*I->eps_len+I->eps_cr/max(L,1e-300);\n            for (int i : g_geo_grid.query(*I,min(ax,ax+dx)-pad,max(ax,ax+dx)+pad,min(ay,ay+dy)-pad,max(ay,ay+dy)+pad)) {\n                if (row[i]',1)
assert sol.count('g_geo_grid.query')==5
s=(B/'solve.cpp').read_text()
for p in B.glob('*.h'):s=s.replace(f'#include "{p.name}"',((H/'src/spatial.h').read_text()+'\n'+sol) if p.name=='sol.h' else p.read_text())
s=s.replace('Inst I = load_instance(inp);','Inst I = load_instance(inp);\n        g_geo_grid.init(I);',1)
p=H/'artifacts/index_v1.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
prefix=s[:s.index('int main(int argc, char** argv)')]
oracle=r'''
int main(int argc,char**argv){
 if(argc<3)return 2;Inst I=load_instance(argv[1]);g_geo_grid.init(I);ifstream f(argv[2]);vector<int>asg(I.ns,-1);vector<char>op(I.no,0);for(int&x:asg){f>>x;if(x>=0)op[x]=1;}
 Sol a,b;a.init(I);b.init(I);g_geo_grid.enabled=false;a.load_state(asg,op);g_geo_grid.enabled=true;b.load_state(asg,op);Engine A(a),B(b);mt19937_64 rng(12345);double ta=0,tb=0;long checks=0;double end=elapsed()+60;
 for(int it=0;it<2000&&elapsed()<end;it++){
  if(!I.ns||!I.no)break;int x=rng()%I.ns,o=rng()%I.no;bool remove=rng()%3==0,aa=false,bb=false;
  g_geo_grid.enabled=false;double t=elapsed();if(remove)A.doRemove(x);else aa=A.doAdd(x,o);ta+=elapsed()-t;
  g_geo_grid.enabled=true;t=elapsed();if(remove)B.doRemove(x);else bb=B.doAdd(x,o);tb+=elapsed()-t;
  if(aa!=bb||a.asg!=b.asg||a.incov!=b.incov||a.cov!=b.cov||a.size_!=b.size_){fprintf(stderr,"mismatch %d\n",it);return 3;}checks++;
 }
 printf("{\"checks\":%ld,\"scan_seconds\":%.9f,\"grid_seconds\":%.9f}\n",checks,ta,tb);
}
'''
p=H/'artifacts/index_oracle.cpp';p.write_text(prefix+oracle);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
(H/'build_index.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (H/'artifacts').glob('index*')},indent=2))
