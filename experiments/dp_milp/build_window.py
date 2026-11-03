from pathlib import Path
import subprocess,json,hashlib
H=Path(__file__).resolve().parent;V=H.parent/'server_v4/artifacts/package/main.cpp';s=V.read_text()
s=s.replace('// dp.h:',(H/'src/window.h').read_text()+'\nstatic thread_local long dp_calls=0;\nstatic thread_local double dp_knap_time=0,dp_window_time=0;\n// dp.h:',1)
a=s.index('static bool resize_dp(');b=s.index('// снимаем наименее',a);old=s[a:b]
old=old.replace('    const Inst& I = *s.I;','    dp_calls++;double dp_begin=elapsed();\n    const Inst& I = *s.I;',1)
old=old.replace('    // сетка значений окна','    dp_knap_time+=elapsed()-dp_begin;\n    // сетка значений окна',1)
old=old.replace('    double bestScore = 0.0;','    double window_begin=elapsed();\n    double bestScore = 0.0;',1)
old=old.replace('    if (bi < 0) return false;','    dp_window_time+=elapsed()-window_begin;\n    if (bi < 0) return false;',1)
fast=old.replace('resize_dp(', 'resize_dp_window(',1);start=fast.index('    double bestScore = 0.0;');end=fast.index('    dp_window_time+=',start)
fast=fast[:start]+'''    vector<double> costs(K);for(int b=0;b<K;b++)costs[b]=I.cost[ops[b]];
    auto win=dp_fast_window(at,blk,grid,costs,I.alpha,allow_close,deadline);
    int bi=win.lo,bj=win.hi;
'''+fast[end:]
old=old.replace('resize_dp(', 'resize_dp_reference(',1)
wrapper='''static bool resize_dp(Sol&s,double deadline,bool allow_close=true){
    static int mode=getenv("DP_MODE")?atoi(getenv("DP_MODE")):1;
    return mode?resize_dp_window(s,deadline,allow_close):resize_dp_reference(s,deadline,allow_close);
}
\n'''
s=s[:a]+old+fast+wrapper+s[b:]
p=H/'artifacts/window_v1.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
prefix=s[:s.index('int main(int argc, char** argv)')]
driver=r'''
int main(int argc,char**argv){
 if(argc<6)return 2;Inst I=load_instance(argv[1]);g_geo_grid.init(I);g_fd=open(argv[2],O_WRONLY|O_CREAT|O_TRUNC,0644);publish("[]\n");ifstream f(argv[3]);vector<int>a(I.ns,-1);vector<char>op(I.no,0);for(int&x:a){f>>x;if(x>=0)op[x]=1;}
 double end=atof(argv[4]);g_wdfs_deadline=end;int repeats=atoi(argv[5]);Sol s;s.init(I);s.load_state(a,op);s.recompute_psum();double before=s.objective();offer(I,s);double total=0,first=0;int done=0;
 while(done<repeats&&elapsed()<end-.25){s.load_state(a,op);double t=elapsed();resize_dp(s,end-.25);double dt=elapsed()-t;if(!done)first=dt;total+=dt;repair_sizes(s);s.recompute_psum();offer(I,s);done++;}
 fprintf(stderr,"{\"before\":%.15g,\"after\":%.15g,\"repeats\":%d,\"dp_seconds\":%.9f,\"first_dp_seconds\":%.9f,\"knapsack_seconds\":%.9f,\"window_seconds\":%.9f,\"wall_internal\":%.6f}\n",before,g_best.load(),done,total,first,dp_knap_time,dp_window_time,elapsed());
}
'''
p=H/'artifacts/post_window.cpp';p.write_text(prefix+driver);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
(H/'BUILD_WINDOW.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (H/'artifacts').glob('window_v1*')},indent=2))
