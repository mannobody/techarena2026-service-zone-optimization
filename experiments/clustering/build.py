"""Build runtime-only clustering prototypes from the integrated solver snapshot."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def once(s,a,b):
    assert s.count(a)==1,a
    return s.replace(a,b)


def main():
    source=(ROOT/'experiments/evolution/artifacts/integrated.cpp').read_text()
    source=once(source,'static bool greedy_fill(Sol& s, Engine& E, double deadline) {',
        (HERE/'territory.h').read_text()+'\n'+(HERE/'fill.h').read_text()+'\nstatic bool greedy_fill(Sol& s, Engine& E, double deadline) {\n'
        '    if(getenv("FILL_RETRY")&&atoi(getenv("FILL_RETRY")))return cluster_fill_retry(s,E,deadline);')
    helpers=(HERE/'constructors.h').read_text()
    helpers=once(helpers,'static vector<int> ctor_cluster(', (HERE/'soft_profit.h').read_text()+'\nstatic vector<int> ctor_cluster(')
    helpers=once(helpers,'    if(mode==1)return cluster_mixed',
                 '    if(mode==4)return cluster_soft_profit(I,op,which,deadline);\n    if(mode==1)return cluster_mixed')
    source=once(source,'static void worker(', helpers+'\nstatic void worker(')
    source=once(source,'    const int NC = 6;',
        '    int cluster_mode=getenv("CLUSTER_MODE")?atoi(getenv("CLUSTER_MODE")):0;\n'
        '    int schedule=getenv("CTOR_SCHEDULE")?atoi(getenv("CTOR_SCHEDULE")):0;\n'
        '    const int NC = cluster_mode ? (cluster_mode==1?9:8) : 6;\n'
        '    int screened[12]={0};')
    source=once(source,'        } else if (ctor == 2) cellOf = ctor_road(I, c.op);',
        '        } else if(ctor>=6)cellOf=ctor_cluster(I,c.op,cluster_mode,ctor-6,min(deadline,elapsed()+.04*tend));\n'
        '        else if (ctor == 2) cellOf = ctor_road(I, c.op);')
    source=once(source,'        int combo = (t + tid * 7) % NCOMBO;',
        '        int combo = (t + tid * 7) % NCOMBO;\n'
        '        if(cluster_mode || schedule==1 || (schedule==2 && (tid&1))){\n'
        '            bool solo=getenv("NT")&&atoi(getenv("NT"))==1;\n'
        '            int shift=cluster_mode&&((tid&1)||solo)?6:tid;\n'
        '            int ctor=(t+shift)%NC;\n'
        '            combo=ctor*(int)cands.size()+(t/NC+tid*7)%(int)cands.size();\n'
        '        }\n        screened[combo/(int)cands.size()]++;')
    source=once(source,'    // Ранжируем НАБОРЫ ОФИСОВ,',
        '    if(getenv("CLUSTER_TRACE")){fprintf(stderr,"ctor_screen tid=%d counts=",tid);'
        'for(int j=0;j<NC;j++)fprintf(stderr,"%d,",screened[j]);fprintf(stderr,"\\n");}\n'
        '    // Ранжируем НАБОРЫ ОФИСОВ,')
    source=once(source,'        exact2_publish(I);',
        '''        exact2_publish(I);
        if(getenv("POST_FILL")&&atoi(getenv("POST_FILL"))&&elapsed()<limit){
            double before=g_best.load();vector<int>a;vector<char>o;
            {lock_guard<mutex> lk(g_best_mx);a=g_best_asg;o=g_best_open;}
            if(!a.empty()){
                Sol s;s.init(I);s.load_state(a,o);Engine E(s);
                g_wdfs_deadline=limit;
                cluster_fill_retry(s,E,limit);s.recompute_psum();offer(I,s);
            }
            fprintf(stderr,"post_fill before=%.9f after=%.9f t=%.3f\\n",before,g_best.load(),elapsed());
        }
        if(getenv("POST_TERRITORY")&&atoi(getenv("POST_TERRITORY"))&&I.alpha==0.&&elapsed()<limit){
            double before=g_best.load();vector<int>a;vector<char>o;
            {lock_guard<mutex>lk(g_best_mx);a=g_best_asg;o=g_best_open;}
            if(!a.empty()){
                g_wdfs_deadline=limit;Sol s;s.init(I);s.load_state(a,o);
                if(cluster_territory_select(s,limit))offer(I,s);
            }
            fprintf(stderr,"territory before=%.9f after=%.9f t=%.3f\\n",before,g_best.load(),elapsed());
        }''')
    out=HERE/'artifacts';out.mkdir(exist_ok=True)
    (out/'prototype.cpp').write_text(source)
    subprocess.run(['g++','-O2','-std=c++17',str(out/'prototype.cpp'),'-o',str(out/'prototype')],check=True)
    inputs=[ROOT/'experiments/evolution/artifacts/integrated.cpp',HERE/'constructors.h',HERE/'soft_profit.h',HERE/'territory.h',HERE/'fill.h',HERE/'build.py']
    (out/'build.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},indent=2))


if __name__=='__main__':main()
