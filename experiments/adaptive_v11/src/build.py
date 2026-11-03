import re,json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
revision=sys.argv[1]if len(sys.argv)>1 else'v1';d=R/'artifacts'/revision;d.mkdir(exist_ok=False)
paths=[ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp',ROOT/'experiments/warm_v10/artifacts/v5/main.cpp']
texts=[p.read_text()for p in paths]
headers=sorted(set(h for s in texts for h in re.findall(r'^#include (<[^>]+>)',s,re.M))|{'<condition_variable>'})
out='// Adaptive per-instance portfolio over immutable v4 and geometry v10 experts.\n'+'\n'.join('#include '+h for h in headers)+'\n'+(R/'src/portfolio.h').read_text()+'\n'
for id,(ns,s)in enumerate(zip(['classic','spatial'],texts)):
 s=re.sub(r'^#include <[^>]+>\n','',s,flags=re.M)
 s=s.replace('static inline double elapsed() { return chrono::duration<double>(Clock::now() - T0).count(); }',f'static inline double elapsed() {{ if(portfolio::active&&portfolio::stop[{id}].load())return 1e30;return chrono::duration<double>(Clock::now() - T0).count(); }}')
 # Common arbiter receives only natively verified improvements. Existing per-expert best is retained.
 a=s.index('static void publish(const string& text) {');b=s.index('\nstatic string serialize',a)
 s=s[:a]+f'static double portfolio_value();\nstatic void publish(const string& text) {{ portfolio::submit({id},portfolio_value(),text); }}\n'+s[b:]
 needle='static vector<char> g_best_open;';assert needle in s
 s=s.replace(needle,needle+'\nstatic double portfolio_value(){return g_best.load();}')
 # Capture the actual compatible site/open state after the expert's own verification.
 needle='publish(serialize(I, s.asg, s.isopen, wof));';assert needle in s
 s=s.replace(needle,f'portfolio::submit({id},obj,serialize(I,s.asg,s.isopen,wof),&s.asg,&s.isopen);')
 needle='static bool pick_elite(mt19937_64& rng, vector<int>& asg, vector<char>& op) {';assert needle in s
 s=s.replace(needle,needle+f'\n    if(portfolio::active&&portfolio::share&&(rng()&3)==0&&portfolio::borrow({id},g_best.load(),asg,op))return true;')
 needle='static int detect_cpus() {';assert needle in s
 s=s.replace(needle,needle+'\n    if(portfolio::active)return 1;')
 s=s.replace('int main(int argc, char** argv) {','int main_entry(int argc, char** argv) {')
 a=s.index('    g_wdfs_deadline =',s.index('int main_entry('));b=s.index('    try {',a)
 s=s[:a]+'    g_wdfs_deadline = limit - max(0.5,0.01*limit);\n    DBG=getenv("DBG")!=nullptr;DBG2=getenv("DBG2")!=nullptr;\n'+s[b:]
 # Main-worker completion must release the passive helper before joining it.
 needle='        vector<thread> th;';assert s.count(needle)==1
 helper=f'''        if(portfolio::active)th.emplace_back([&](){{if(portfolio::await_second({id}))worker(I,F,cands,((0xA5A5ULL*2+12345)^seed0),limit,dp_deadline,1);}});'''
 s=s.replace(needle,needle+'\n'+helper)
 needle='        for (auto& t : th) t.join();';assert s.count(needle)==1
 s=s.replace(needle,f'        if(portfolio::active){{portfolio::idle_release[{id}].store(true);portfolio::cv.notify_all();}}\n'+needle)
 out+='namespace '+ns+' {\n'+s+'\n}\n'
out+=(R/'src/specialists.h').read_text()+'\n'+(R/'src/router.h').read_text();(d/'main.cpp').write_text(out)
(d/'BUILD.json').write_text(json.dumps(dict(revision=revision,base_sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths},new_sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [R/'src/portfolio.h',R/'src/router.h',R/'src/specialists.h',R/'src/build.py']},main_sha256=hashlib.sha256(out.encode()).hexdigest()),indent=2))
print(d/'main.cpp')
