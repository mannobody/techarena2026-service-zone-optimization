from pathlib import Path
import subprocess,json,hashlib,time
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];out=R/'artifacts/certified';out.mkdir(exist_ok=False)
s=(R/'baseline/main.cpp').read_text();original=s;h=(R/'src/certified.h').read_text();needle='int main(int argc, char** argv) {';s=s.replace(needle,h+'\n'+needle,1)
call='        if((!getenv("V12_CERT")||atoi(getenv("V12_CERT")))&&(specialists::single_office(I)||specialists::collinear(I,limit)))return 0;\n'
needle='        if (I.ns == 0 || I.no == 0) return 0;\n';s=s.replace(needle,needle+call,1);assert s.replace(h+'\n','',1).replace(call,'',1)==original
(out/'main.cpp').write_text(s);cmd=['taskset','-c','18,19','g++','-O3','-std=c++17','-o',str(out/'candidate'),str(out/'main.cpp'),'-ldl'];begin=time.time()
with(out/'compile.log').open('w')as f:p=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();(out/'BUILD.json').write_text(json.dumps(dict(rc=p.returncode,wall=time.time()-begin,command=cmd,source_sha256=sha(out/'main.cpp'),binary_sha256=sha(out/'candidate')if p.returncode==0 else None,roundtrip_to_original_submission_exact=True),indent=2));assert p.returncode==0
print('certified baseline built',flush=True)
