from pathlib import Path
import subprocess,json,hashlib
H=Path(__file__).resolve().parent;E=H.parent
s=(E/'server_v4/artifacts/package/main.cpp').read_text();s=s.replace('int main(int argc, char** argv)',(H/'src/highs_api.h').read_text()+'\n'+(H/'src/mip_tail_v5.h').read_text()+'\nint main(int argc, char** argv)',1)
s=s.replace('        boundary_finish(I, limit);','        boundary_finish(I, limit);\n        if(!getenv("MIP")||atoi(getenv("MIP")))v5_finish(I,limit);',1)
p=H/'artifacts/native_v5.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17','-o',str(p.with_suffix('')),str(p),'-ldl'],check=True)
prefix=s[:s.index('int main(int argc, char** argv)')]
driver=r'''
int main(int argc,char**argv){if(argc<6)return 2;Inst I=load_instance(argv[1]);g_geo_grid.init(I);g_fd=open(argv[2],O_WRONLY|O_CREAT|O_TRUNC,0644);publish("[]\n");ifstream f(argv[3]);vector<int>a(I.ns,-1);vector<char>op(I.no,0);for(int&x:a){f>>x;if(x>=0)op[x]=1;}double limit=atof(argv[4]);g_wdfs_deadline=limit-.25;Sol s;s.init(I);s.load_state(a,op);s.recompute_psum();offer(I,s);double before=g_best.load();v5_finish(I,limit);fprintf(stderr,"{\"before\":%.15g,\"after\":%.15g,\"seconds\":%.9f,\"highs\":%d}\n",before,g_best.load(),elapsed(),v5_api().ready);}
'''
p=H/'artifacts/post_v5.cpp';p.write_text(prefix+driver);subprocess.run(['g++','-O3','-std=c++17','-o',str(p.with_suffix('')),str(p),'-ldl'],check=True)
(H/'BUILD_NATIVE_V5.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [H/'artifacts/native_v5.cpp',H/'artifacts/post_v5.cpp',H/'src/highs_api.h',H/'src/mip_tail_v5.h']},indent=2))
