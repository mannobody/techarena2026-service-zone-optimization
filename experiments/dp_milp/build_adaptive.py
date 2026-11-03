from pathlib import Path
import subprocess,json,hashlib
H=Path(__file__).resolve().parent
old=(H/'src/window.h').read_text();needle='DPWindowTree tree(G);'
extra='''
 // Small grids have too little work to amortize segment-tree overhead.
 if(G<=128){
  vector<double>run(K);
  for(int l=0;l<G;l++){
   if((l&31)==0&&elapsed()>=deadline){result.complete=false;break;}
   for(int k=0;k<K;k++)run[k]=at[k][l];
   for(int r=l;r<G;r++){
    long double score=-(long double)alpha*(grid[r]-grid[l]);bool valid=true;
    for(int k=0;k<K;k++){
     if(r>l)run[k]=max(run[k],blk[k][r]);
     if(run[k]<=NEG/2){if(!allow_close)valid=false;}
     else score+=allow_close?max((long double)0,(long double)run[k]-cost[k]):(long double)run[k]-cost[k];
    }
    if(valid&&score>result.score+1e-9L){result.score=score;result.lo=l;result.hi=r;}
   }
  }return result;
 }
 DPWindowTree tree(G);'''
new=old.replace(needle,extra,1);(H/'src/window_v2.h').write_text(new)
for name in ['scaled_v1','post_scaled']:
 s=(H/'artifacts'/f'{name}.cpp').read_text();assert old in s;s=s.replace(old,new,1);dest='adaptive_v1' if name=='scaled_v1' else 'post_adaptive';p=H/'artifacts'/f'{dest}.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
# Oracle uses larger grids too, so both the fallback and tree are exercised.
s=(H/'artifacts/window_oracle.cpp').read_text().replace(old,new,1).replace('test<10000','test<2000').replace('rng()%60','rng()%400')
p=H/'artifacts/window_oracle_v2.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True);pr=subprocess.run([str(p.with_suffix(''))],capture_output=True,text=True);(H/'logs/window_oracle_v2.stderr').write_text(pr.stderr);assert pr.returncode==0,pr.stderr;(H/'logs/window_oracle_v2.json').write_text(pr.stdout)
(H/'BUILD_ADAPTIVE.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (H/'artifacts').glob('*adaptive*')},indent=2))
