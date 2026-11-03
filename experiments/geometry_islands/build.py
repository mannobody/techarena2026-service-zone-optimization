from pathlib import Path
import subprocess,json,hashlib,sys
tag=sys.argv[1] if len(sys.argv)>1 else "v2"
H=Path(__file__).resolve().parent;b=H/'baseline/solver'
s=(b/'solve.cpp').read_text()
for p in b.glob('*.h'):s=s.replace(f'#include "{p.name}"',p.read_text())
s=s[:s.index('int main(int argc, char** argv)')]
s+=(H.parent/'boundary_beam/src/boundary.h').read_text()+'\n'+(H/'src/island.h').read_text()+'\n'+(H/'src/operators.h').read_text()
post=r'''
int main(int argc,char**argv){
 if(argc<6)return 2;Inst I=load_instance(argv[1]);ifstream f(argv[2]);vector<int>a(I.ns,-1);vector<char>op(I.no,0);for(int&v:a){f>>v;if(v>=0)op[v]=1;}if(!f)return 3;
 Sol s;s.init(I);s.load_state(a,op);double before=s.objective(),start=elapsed(),end=start+atof(argv[3]);g_wdfs_deadline=end;mt19937_64 rng(strtoull(argv[5],nullptr,10));
 gi_polish(s,rng,end,atoi(argv[4]));vector<int>w;double val=0;bool valid=s.greedy_workers(&w)&&verify(I,s.asg,s.isopen,w,&val);
 fprintf(stderr,"{\"before\":%.12g,\"after\":%.12g,\"valid\":%s,\"seconds\":%.6f,\"calls\":%ld,\"wins\":%ld,\"geo_fail\":%ld,\"balance_fail\":%ld,\"worker_fail\":%ld,\"trimmed\":%ld,\"triangles\":%ld}\n",before,val,valid?"true":"false",elapsed()-start,geo_stats.calls,geo_stats.wins,geo_stats.geo_fail,geo_stats.balance_fail,geo_stats.worker_fail,geo_stats.trimmed,geo_stats.triangles);
 if(!valid)return 4;printf("[");bool first=true;for(int o=0;o<I.no;o++)if(s.size_[o]){printf("%s{\"officeId\":%d,\"sites\":[",first?"":",",o);first=false;for(size_t k=0;k<s.members[o].size();k++)printf("%s%d",k?",":"",s.members[o][k]);printf("],\"workers\":[");bool fw=true;for(int j=0;j<I.nw;j++)if(w[j]==o){printf("%s%d",fw?"":",",j);fw=false;}printf("]}");}printf("]\n");}
'''
p=H/'artifacts'/f'post_{tag}.cpp';p.write_text(s+post);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
oracle='#include <iostream>\n'+(b/'base.h').read_text()+'\n'+(b/'geom.h').read_text()+'\n'+(H/'src/island.h').read_text()+r'''
int main(){int n,k,must,mode;cin>>n>>k>>must>>mode;vector<Pt>p(n);vector<double>w(n);vector<char>red(n);for(int i=0;i<n;i++){int r;cin>>p[i].x>>p[i].y>>w[i]>>r;red[i]=r;}vector<int>v(k);for(int&i:v)cin>>i;
 if(mode==0){auto a=gi_island(p,w,red,v,must,elapsed()+60,1e-12);printf("%.12g %d %ld\n",a.score,a.complete,a.triangles);}
 else{int t;cin>>t;vector<Pt>pr(t);for(auto&a:pr)cin>>a.x>>a.y;auto a=gi_trim_sweep(p,v,w,p[must],pr,elapsed()+60,1e-12);printf("%.12g\n",a.loss);}}
'''
p=H/'artifacts'/f'oracle_{tag}.cpp';p.write_text(oracle);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
(H/f'build_{tag}.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (H/'artifacts').iterdir() if p.is_file()},indent=2))
