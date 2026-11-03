"""Retain the submission's complete optional MIP extension on every native port."""
from pathlib import Path
import hashlib,json,re,subprocess,os,concurrent.futures,time
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15});sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=(R/'baseline/main.cpp').read_text();v4=(ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp').read_text();assert hashlib.sha256(base.encode()).hexdigest()=='4144e63be49b938ca4885562dfd87bfdec78e46c8b3bd2ee9d32907997ff7bee'
body=base[base.index('// Optional HiGHS C API'):base.index('int main(int argc, char** argv) {')]
forward='static void v52_finish(const Inst&,double);\n'
hook=re.search(r'        if\(tid==0&&!regional_done.*?\n        }\n',base,re.S).group()
tail='        if(!getenv("MIP")||atoi(getenv("MIP")))v5_finish(I,limit);\n'
stripped=base.replace(body,'',1).replace(forward,'',1).replace('    bool regional_done=false;\n','',1).replace(hook,'',1).replace(tail,'',1)
assert stripped==v4,'Submission delta contains more than the audited MIP extension'
(R/'artifacts/retained_mip_extension.h').write_text(body)
cert=(ROOT/'experiments/adaptive_v11/src/specialists.h').read_text().replace('using spatial::Inst;','using ::Inst;').replace('spatial::','::').replace('portfolio::elapsed()','elapsed()')
cert=cert.replace(' portfolio::submit(1,value,::serialize(I,asg,op,workers),&asg,&op);',''' {lock_guard<mutex>lk(g_best_mx);if(value>g_best.load()){
  g_best.store(value);g_best_asg=asg;g_best_open=op;::publish(::serialize(I,asg,op,workers));push_elite(value,asg,op);
 }}''')
assert 'portfolio::'not in cert and 'spatial::'not in cert
(R/'src/certified.h').write_text(cert)
sources=dict(hybrid='experiments/v4_deep_parallel/integration/src/hybrid_frozen.cpp',plateau='experiments/server_v8/artifacts/package/main.cpp',exact='experiments/v8_exact_neighborhoods/artifacts/final/main.cpp',zones='experiments/structural_v9/artifacts/final_research/main.cpp',geometry='experiments/warm_v10/artifacts/v5/main.cpp')
audit={}
for name,path in sources.items():
 p=ROOT/path;s=p.read_text();original=s
 assert 'V5Highs'not in s
 needle='static void worker(const Inst& I, const Fast& F, const vector<Cand>& cands,';assert s.count(needle)==1;s=s.replace(needle,forward+needle,1)
 a=s.index('    int round = 0;',s.index(needle));start=s.index('    while (elapsed() <',a);end=s.index('\n',start)+1
 s=s[:a]+s[a:start].replace('    int round = 0;','    int round = 0;\n    bool regional_done=false;',1)+s[start:end]+hook+s[end:]
 needle='        if (DBG) fprintf(stderr, "worker_dfs calls=';assert s.count(needle)==1;s=s.replace(needle,tail+needle,1)
 needle='int main(int argc, char** argv) {';assert s.count(needle)==1;s=s.replace(needle,body+cert+'\n'+needle,1)
 call='        if((!getenv("V12_CERT")||atoi(getenv("V12_CERT")))&&(specialists::single_office(I)||specialists::collinear(I,limit)))return 0;\n'
 needle='        if (I.ns == 0 || I.no == 0) return 0;\n';assert s.count(needle)==1;s=s.replace(needle,needle+call,1)
 # Removing all new MIP hooks and certified dispatcher must recover the exact historical method.
 check=s.replace(body,'',1).replace(cert+'\n','',1).replace(forward,'',1).replace('    bool regional_done=false;\n','',1).replace(hook,'',1).replace(tail,'',1).replace(call,'',1)
 assert check==original,name
 out=R/'artifacts'/name;out.mkdir(exist_ok=False);(out/'main.cpp').write_text(s)
 audit[name]=dict(parent=path,parent_sha256=sha(p),source_sha256=sha(out/'main.cpp'),retained_mip_sha256=hashlib.sha256(body.encode()).hexdigest(),roundtrip_to_parent_exact=True)
(R/'COMPOSITION.json').write_text(json.dumps(dict(submission_without_mip_equals_exact_v4=True,submission_mip_preserved=True,certified_source='adaptive_v11 numerical revisionv4, global publisher adapter only',ports=audit),indent=2))
def build(item):
 name,cpu=item;out=R/'artifacts'/name;cmd=['taskset','-c',str(cpu),'g++','-O3','-std=c++17','-o',str(out/'candidate'),str(out/'main.cpp'),'-ldl'];begin=time.time()
 with(out/'compile.log').open('w')as f:p=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 b=dict(command=cmd,rc=p.returncode,wall=time.time()-begin,source_sha256=sha(out/'main.cpp'),binary_sha256=sha(out/'candidate')if p.returncode==0 else None);(out/'BUILD.json').write_text(json.dumps(b,indent=2));return name,b
# Two compiler processes, each on one controller CPU, before quality measurements.
items=list(sources);results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
 for k in range(0,len(items),2):
  for name,b in pool.map(build,[(n,14+j)for j,n in enumerate(items[k:k+2])]):results.append((name,b));print(name,b['rc'],round(b['wall'],2),flush=True)
assert all(b['rc']==0 for n,b in results)
(R/'BUILD_STATUS.json').write_text(json.dumps(dict(stage='complete',ports=len(results)),indent=2))
