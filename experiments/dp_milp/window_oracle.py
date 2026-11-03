from pathlib import Path
import subprocess,json
H=Path(__file__).resolve().parent;R=H.parents[1]
s=(R/'solver/base.h').read_text()+'\n'+(H/'src/window.h').read_text()+r'''
int main(){mt19937_64 rng(221000);int checks=0;for(int test=0;test<10000;test++){
 int K=1+rng()%12,G=1+rng()%60;vector<int>grid(G);for(int i=1;i<G;i++)grid[i]=grid[i-1]+1+rng()%6;
 vector<vector<double>>at(K,vector<double>(G,NEG)),blk=at;vector<double>cost(K);
 for(int k=0;k<K;k++){cost[k]=(int)(rng()%50)-10;for(int j=0;j<G;j++)for(int l=j?grid[j-1]+1:0;l<=grid[j];l++){double f=rng()%4?((int)(rng()%2000)-400)/10.:NEG;blk[k][j]=max(blk[k][j],f);if(l==grid[j])at[k][j]=f;}}
 double alpha=test%7==0?1e10:(rng()%100)/10.;bool close=test%2;long double best=0;
 for(int l=0;l<G;l++){vector<double>run(K);for(int k=0;k<K;k++)run[k]=at[k][l];for(int r=l;r<G;r++){long double value=-(long double)alpha*(grid[r]-grid[l]);bool ok=true;
  for(int k=0;k<K;k++){if(r>l)run[k]=max(run[k],blk[k][r]);if(run[k]<=NEG/2){if(!close)ok=false;}else value+=close?max((long double)0,(long double)run[k]-cost[k]):(long double)run[k]-cost[k];}
  if(ok)best=max(best,value);
 }}
 auto got=dp_fast_window(at,blk,grid,cost,alpha,close,1e9);if(!got.complete||fabsl(best-got.score)>1e-6L){fprintf(stderr,"FAIL test=%d K=%d G=%d expected=%.18Lg got=%.18Lg\n",test,K,G,best,got.score);return 1;}checks++;
 }printf("{\"seed\":221000,\"checks\":%d}\n",checks);}
'''
p=H/'artifacts/window_oracle.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
r=subprocess.run([str(p.with_suffix(''))],capture_output=True,text=True);(H/'logs/window_oracle.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr;(H/'logs/window_oracle.json').write_text(r.stdout);print(r.stdout)
