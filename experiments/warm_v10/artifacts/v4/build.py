import hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
revision=sys.argv[1] if len(sys.argv)>1 else 'v1'
d=R/'artifacts'/revision;d.mkdir(exist_ok=False)
for p in [R/'src/geometry_warm.h',Path(__file__)]:
    (d/p.name).write_bytes(p.read_bytes())
base=ROOT/'experiments/structural_v9/artifacts/final_research/main.cpp'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='d72e0c83540c0ddbeaa63aafbf9697906cae5b6c425314b244553b2d6a7e44e8'
s=base.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a[:80],s.count(a))
 s=s.replace(a,b)
replace('struct Cand { double f; vector<int> op; vector<double> h; vector<Pt> G; };',
        'struct Cand { double f; vector<int> op; vector<double> h; vector<Pt> G; vector<int> asg; vector<char> open; };')
replace('    for (auto& e : g_elite) if (fabs(e.f - f) <= 1e-9 * max(1.0, fabs(f))) return;', '''    const bool spatial=(!getenv("GW_MODE")||atoi(getenv("GW_MODE"))>=2);
    if(spatial) {
        auto distance=[](const vector<int>&a,const vector<int>&b){
            size_t d=0,n=0;for(size_t x=0;x<a.size();x++)if(a[x]>=0||b[x]>=0){n++;d+=a[x]!=b[x];}
            return n?(double)d/n:0.;
        };
        for(auto& e:g_elite)if(distance(e.asg,asg)<.025) {
            if(f>e.f){e={f,asg,op};stable_sort(g_elite.begin(),g_elite.end(),[](const Elite&a,const Elite&b){return a.f>b.f;});}
            return;
        }
        g_elite.push_back({f,asg,op});
        stable_sort(g_elite.begin(),g_elite.end(),[](const Elite&a,const Elite&b){return a.f>b.f;});
        if(g_elite.size()>12) {
            double scale=max(1.,fabs(g_elite[0].f)),worst=1e300;size_t drop=1;
            for(size_t i=1;i<g_elite.size();i++) {
                double nearest=1.;for(size_t j=0;j<g_elite.size();j++)if(i!=j)nearest=min(nearest,distance(g_elite[i].asg,g_elite[j].asg));
                double score=g_elite[i].f/scale+.18*nearest;
                if(score<worst){worst=score;drop=i;}
            }
            g_elite.erase(g_elite.begin()+drop);
        }
        return;
    }
    for (auto& e : g_elite) if (fabs(e.f - f) <= 1e-9 * max(1.0, fabs(f))) return;''')
replace('if (f <= 0 || f < b * (b > 0 ? 0.96 : 1.04)) return;',
        'if (f <= 0 || f < b * (b > 0 ? ((!getenv("GW_MODE")||atoi(getenv("GW_MODE"))>=2)?.90:.96) : 1.04)) return;')
replace('// evolution_warm.h: broad office-subset search, included after worker().',
        (R/'src/geometry_warm.h').read_text()+'\n// evolution_warm.h: broad office-subset search, included after worker().')
replace('    int warm_mode = getenv("WARM_START") ?',
        '    int gw_mode = getenv("GW_MODE") ? max(0,min(2,atoi(getenv("GW_MODE")))) : 2;\n        if(getenv("FORCE_OPS"))gw_mode=0;\n        int warm_mode = getenv("WARM_START") ?')
replace('if (warm_mode) warm_real = wide_start(I, F, cache, rng, min(0.22 * limit, 60.0), limit, warm_mode);',
        '''if(gw_mode) {
            double warm_end=min(.22*limit,60.);
            // Cheap broad office masks before expensive geometric phenotypes.
            // On large inputs the preceding greedy search may have reached only singletons.
            auto preliminary=wide_start(I,F,cache,rng,elapsed()+.30*max(0.,warm_end-elapsed()),limit,2);
            warm_real=geometry_start(I,F,cache,seed0^0x67E0ULL,warm_end,limit,gw_mode);
        } else if (warm_mode) warm_real = wide_start(I, F, cache, rng, min(0.22 * limit, 60.0), limit, warm_mode);''')
replace('            if (!have) cands.push_back(c);\n        }\n        if (cands.empty())',
        '            if (!have || (gw_mode&&!c.asg.empty())) cands.push_back(c);\n        }\n        if (cands.empty())')
replace('        realize(s, I, c.op, cellOf, deadline, &rng, skt);',
        '        if(ctor==0&&!c.asg.empty()){s.init(I);s.load_state(c.asg,c.open);}\n        else realize(s, I, c.op, cellOf, deadline, &rng, skt);')
# Avoid computing an unused diagram when directly loading a feasible phenotype.
replace('        if (ctor <= 1) {','        if(ctor==0&&!c.asg.empty()) { /* Direct feasible warm start. */ }\n        else if (ctor <= 1) {')
out=d/'main.cpp';out.write_text(s)
cmd=['taskset','-c','14,15','g++','-O3','-std=c++17',str(out),'-o',str(d/'candidate')]
subprocess.run(cmd,check=True,cwd=ROOT)
files=[base,R/'src/geometry_warm.h',Path(__file__),out,d/'candidate',ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp']
(d/'BUILD.json').write_text(json.dumps(dict(command=cmd,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}),indent=2))
print(json.dumps(dict(revision=revision,binary=str(d/'candidate'))))
