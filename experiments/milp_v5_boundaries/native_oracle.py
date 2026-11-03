from regions import *
import subprocess,os,json
D=H/'logs/native_oracle';D.mkdir();s=(H/'artifacts/native.cpp').read_text();prefix=s[:s.index('int main(int argc, char** argv)')]
driver=r'''
int main(int argc,char**argv){Inst I=load_instance(argv[1]);g_geo_grid.init(I);g_fd=open(argv[2],O_WRONLY|O_CREAT|O_TRUNC,0644);publish("[]\n");ifstream f(argv[3]);int n;f>>n;vector<V52Region>R;for(int e=0;e<n;e++){int o,ns,np;f>>o>>ns>>np;vector<int>ss(ns),pp(np);for(int&x:ss)f>>x;for(int&x:pp)f>>x;R.push_back({o,ss,pp,0});}vector<int>a(I.ns,-1),staff(I.nw,-1),base(I.no,-1);vector<char>op(I.no,0);v52_select(I,R,base,a,op,staff,59,true);}
'''
p=H/'artifacts/oracle.cpp';p.write_text(prefix+driver);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix('')),'-ldl'],check=True);rs=[]
for f in sorted((H/'logs/oracle_v2').glob('311*.json')):
 d=json.loads(f.read_text());inp=D/(f.stem+'.input.json');inp.write_text(json.dumps(d['data']));sp=D/(f.stem+'.regions');lines=[str(len(d['regions']))]
 for r in d['regions']:lines.append(' '.join(map(str,[r['o'],len(r['sites']),len(r['footprint']),*r['sites'],*r['footprint']])))
 sp.write_text('\n'.join(lines));out=D/(f.stem+'.solution.json');q=subprocess.run([str(p.with_suffix('')),str(inp),str(out),str(sp)],env=dict(os.environ,LD_LIBRARY_PATH='/tmp/ta-boundary-venv/lib64/python3.14/site-packages/highspy'),capture_output=True,text=True,timeout=60);assert q.returncode==0,q.stderr;score=value(Instance(d['data']),json.loads(out.read_text()));assert not isinstance(score,str),score;assert abs(score-d['expected'])<1e-6,(f,score,d['expected']);rs.append(dict(seed=f.stem,value=score,expected=d['expected']));print(f.stem,score,flush=True)
(D/'results.json').write_text(json.dumps(rs,indent=2))
