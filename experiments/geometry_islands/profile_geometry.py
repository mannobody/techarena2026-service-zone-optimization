from pathlib import Path
import subprocess,json,time
H=Path(__file__).resolve().parent
s=(H/'artifacts/robust_v1.cpp').read_text();s=s[:s.index('int main(int argc, char** argv)')]
s=s.replace('static int geo_orientation(Pt a,Pt b,Pt c){','static long long geo_calls=0,geo_fallbacks=0;\nstatic int geo_orientation(Pt a,Pt b,Pt c){\n geo_calls++;').replace(' return geo_exact_orientation(a,b,c);',' geo_fallbacks++;return geo_exact_orientation(a,b,c);')
s+=r'''
int main(int argc,char**argv){
 Inst I=load_instance(argv[1]);g_geo_grid.init(I);ifstream f(argv[2]);vector<int>asg(I.ns,-1);vector<char>op(I.no,0);for(int&x:asg){f>>x;if(x>=0)op[x]=1;}
 Sol a,b;a.init(I);b.init(I);g_geo_exact=false;a.load_state(asg,op);g_geo_exact=true;b.load_state(asg,op);
 long initial=0;for(size_t i=0;i<a.incov.size();i++)initial+=a.incov[i]!=b.incov[i];
 Engine A(a),B(b);mt19937_64 rng(12345);double ta=0,tb=0;long checks=0,different=0;geo_calls=geo_fallbacks=0;double end=elapsed()+60;
 for(int it=0;it<2000&&elapsed()<end;it++){
  if(!I.ns||!I.no)break;int x=rng()%I.ns,o=rng()%I.no;bool remove=rng()%3==0,aa=false,bb=false;
  auto step=[&](bool exact){g_geo_exact=exact;double t=elapsed();if(exact){if(remove)B.doRemove(x);else bb=B.doAdd(x,o);tb+=elapsed()-t;}else{if(remove)A.doRemove(x);else aa=A.doAdd(x,o);ta+=elapsed()-t;}};
  if(it%2){step(true);step(false);}else{step(false);step(true);}
  if(aa!=bb||a.asg!=b.asg||a.incov!=b.incov||a.cov!=b.cov||a.size_!=b.size_)different++;
  checks++;
 }
 printf("{\"initial_footprint_differences\":%ld,\"checks\":%ld,\"different_states\":%ld,\"legacy_seconds\":%.9f,\"exact_seconds\":%.9f,\"orient_calls\":%lld,\"fallback_calls\":%lld}\n",initial,checks,different,ta,tb,geo_calls,geo_fallbacks);
}
'''
p=H/'artifacts/geometry_profile.cpp';assert not p.exists();p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
D=H/'logs/geometry_profile';D.mkdir();rows=[]
for split,tag,seed in [('train','train_base60',1),('validation2','robust_holdout60',71)]:
 for inp in sorted((H/'data'/split).glob('*.json')):
  source=H/'logs'/tag/f'{inp.stem}_{seed}_base.json'
  if not source.exists():continue
  asg=[-1]*len(json.loads(inp.read_text())['sites'])
  for of in json.loads(source.read_text()):
   for x in of['sites']:asg[x]=of['officeId']
  q=D/f'{split}_{inp.stem}.asg';q.write_text(' '.join(map(str,asg)))
  pr=subprocess.run([str(p.with_suffix('')),str(inp),str(q)],capture_output=True,text=True,timeout=65,check=True)
  row=dict(split=split,case=inp.stem,input=str(inp),reference=str(source),**json.loads(pr.stdout));rows.append(row);print(row,flush=True)
(D/'results.json').write_text(json.dumps(rows,indent=2))
