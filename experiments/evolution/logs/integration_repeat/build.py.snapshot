"""Build isolated native variants, never edit the shared solver sources."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=HERE/'baseline'  # Freeze the pre-integration solver for reproducible A/B.


def replace_once(s,old,new):
    assert s.count(old)==1,old
    return s.replace(old,new)


def build():
    out=HERE/'artifacts';out.mkdir(exist_ok=True)
    source=(SOURCE/'solve.cpp').read_text()
    warm=replace_once(source,'int main(int argc, char** argv) {',
                      (HERE/'warm.h').read_text()+'\n'+(HERE/'memetic.h').read_text()+'\n'+(HERE/'scout.h').read_text()+'\nint main(int argc, char** argv) {')
    thread_setup='''        int nth = detect_cpus();
        if (I.ns > 20000) nth = min(nth, 6);
        // без явного предела арен malloc в потоках сам читает /sys/devices/system/cpu/online
        mallopt(M_ARENA_MAX, nth + 2);
        vector<thread> th;'''
    warm=replace_once(warm,thread_setup,'')
    warm=replace_once(warm,'        double dp_deadline = limit - max(1.0, 0.05 * limit);','')
    warm=replace_once(warm,'        mt19937_64 rng(0x9E3779B97F4A7C15ULL ^ seed0);',
        '        mt19937_64 rng(0x9E3779B97F4A7C15ULL ^ seed0);\n'+thread_setup+'\n'
        '        double dp_deadline = limit - max(1.0, 0.05 * limit);\n'
        '        int early = getenv("SCOUT") && atoi(getenv("SCOUT")) ? nth/2 : 0;\n'
        '        for(int i=1;i<=early;i++)th.emplace_back(evo_scout,cref(I),cref(F),'
        '(0x51C0A7ULL*(i+1))^seed0,limit,dp_deadline,i);')
    warm=replace_once(warm,'        for (int i = 1; i < nth; i++)','        for (int i = 1+early; i < nth; i++)')
    warm=replace_once(warm,'double t_outer = min(0.22 * limit, 60.0);',
        'int evo_mode = getenv("EVO") ? atoi(getenv("EVO")) : 2;\n'
        '        double t_outer = min((evo_mode ? 0.10 : 0.22) * limit, evo_mode ? 30.0 : 60.0);')
    warm=replace_once(warm,'        vector<Cand> cands;',
        '        vector<Cand> evo_real;\n'
        '        if(evo_mode) evo_real=evo_warm(I,F,cache,rng,min(.22*limit,60.0),limit,evo_mode);\n'
        '        vector<Cand> cands;')
    warm=replace_once(warm,'        if (cands.empty()) {',
        '        for(const auto& e:evo_real){bool have=false;for(const auto& c:cands)if(c.op==e.op)have=true;'
        'if(!have)cands.push_back(e);}\n        if (cands.empty()) {')
    warm=warm.replace('th.emplace_back(worker,','th.emplace_back(evo_dispatch,')
    warm=replace_once(warm,'        worker(I, F, cands, 777 ^ seed0, limit, dp_deadline, 0);',
                          '        evo_dispatch(I, F, cands, 777 ^ seed0, limit, dp_deadline, 0);')
    warm=replace_once(warm,'    DBG = getenv("DBG") != nullptr;',
                          '    g_wdfs_deadline=limit-max(.5,.01*limit);\n    DBG = getenv("DBG") != nullptr;')
    warm=replace_once(warm,'        fprintf(stderr, "objective=',
        '        if(getenv("WORKER_DFS"))fprintf(stderr,"worker_dfs calls=%ld solved=%ld nodes=%ld\\n",'
        'g_wdfs_calls.load(),g_wdfs_success.load(),g_wdfs_nodes.load());\n'
        '        fprintf(stderr, "objective=')
    for name,text in [('baseline',source),('warm',warm)]:
        for p in SOURCE.glob('*.h'):
            header=p.read_text()
            if name=='warm' and p.name=='sol.h':
                header=replace_once(header,'    bool greedy_workers(vector<int>* out) const {',
                                      '    bool legacy_workers(vector<int>* out) const {')
                header=replace_once(header,'    // --- ходы', (HERE/'workers.h').read_text()+'    // --- ходы')
                header='#include <functional>\nstatic atomic<long> g_wdfs_calls{0},g_wdfs_success{0},g_wdfs_nodes{0};\nstatic double g_wdfs_deadline=1e100;\n'+header
            text=text.replace(f'#include "{p.name}"',header)
        path=out/f'{name}.cpp';path.write_text(text)
        subprocess.run(['g++','-O2','-std=c++17',str(path),'-o',str(out/name)],check=True)
    files=[SOURCE/'solve.cpp',*SOURCE.glob('*.h'),HERE/'warm.h',HERE/'memetic.h',HERE/'workers.h',HERE/'scout.h',HERE/'build.py']
    (out/'build.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
    print(out)


if __name__=='__main__':
    build()
