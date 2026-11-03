from pathlib import Path
import subprocess,json
H=Path(__file__).resolve().parent;B=H.parent/'boundary_beam';s=(H/'artifacts/package/main.cpp').read_text();s=s[:s.index('int main(int argc, char** argv)')]
o=(B/'artifacts/oracle.cpp').read_text();o=o[o.index('int main(int argc,char**argv)'):].replace('Inst I=load_instance(argv[1]);','Inst I=load_instance(argv[1]);g_geo_grid.init(I);')
p=H/'artifacts/oracle.cpp';p.write_text(s+o);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
rows=[]
for ref in json.loads((B/'logs/oracle.json').read_text()):
 seed=ref['seed']-101000
 pr=subprocess.run([str(p.with_suffix('')),str(B/'data/oracle'/f'{seed}.json'),str(B/'data/oracle'/f'{seed}.asg'),str(ref['strong'])],capture_output=True,text=True,check=True);r=json.loads(pr.stdout)
 assert r['valid'] and not r['stopped'] and abs(r['score']-ref['expected'])<1e-7,(ref,r)
 rows.append(dict(seed=ref['seed'],strong=ref['strong'],expected=ref['expected'],**r))
(H/'logs/oracle.json').write_text(json.dumps(rows,indent=2));print(len(rows),'oracle checks passed')
