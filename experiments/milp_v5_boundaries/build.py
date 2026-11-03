from pathlib import Path
import subprocess,hashlib,json
H=Path(__file__).resolve().parent;s=(H.parent/'milp_v5/artifacts/native_v5.cpp').read_text();s=s.replace('int main(int argc, char** argv)',(H/'src/region_mip.h').read_text()+'\nint main(int argc, char** argv)',1)
# Research placement: one bounded regional call before starting native workers.
s=s.replace('        double dp_deadline = limit - max(1.0, 0.05 * limit);','        if(!getenv("REGION")||atoi(getenv("REGION")))v52_finish(I,min(limit-.8,elapsed()+min(2.,.035*limit)));\n        double dp_deadline = limit - max(1.0, 0.05 * limit);',1)
p=H/'artifacts/native.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix('')),'-ldl'],check=True)
prefix=s[:s.index('int main(int argc, char** argv)')]
driver=r'''
int main(int argc,char**argv){if(argc<6)return 2;Inst I=load_instance(argv[1]);g_geo_grid.init(I);g_fd=open(argv[2],O_WRONLY|O_CREAT|O_TRUNC,0644);publish("[]\n");ifstream f(argv[3]);vector<int>a(I.ns,-1);vector<char>op(I.no,0);for(int&x:a){f>>x;if(x>=0)op[x]=1;}double limit=atof(argv[4]);g_wdfs_deadline=limit-.3;Sol s;s.init(I);s.load_state(a,op);s.recompute_psum();vector<int>staff(I.nw,-1);ifstream fs(argv[5]);for(int&x:staff)fs>>x;v5_offer(I,a,op,staff);double before=g_best.load();DBG=true;v52_finish(I,limit-.3);fprintf(stderr,"{\"before\":%.15g,\"after\":%.15g,\"seconds\":%.9f}\n",before,g_best.load(),elapsed());}
'''
p=H/'artifacts/post.cpp';p.write_text(prefix+driver);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix('')),'-ldl'],check=True)
(H/'BUILD.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [H/'artifacts/native.cpp',H/'artifacts/post.cpp',H/'src/region_mip.h']},indent=2))
