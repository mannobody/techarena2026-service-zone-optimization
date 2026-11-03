import hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];d=R/'artifacts/singleton_mechanism';d.mkdir(exist_ok=False)
harness=r'''
int main(int argc,char**argv) {
 if(argc!=2)return 2;Inst I=load_instance(argv[1]);Fast F(I);
 vector<Pt>G0(I.P.begin()+I.ns,I.P.end());int tested=0;double worst=0,start=elapsed();
 printf("{\"offices\":[");
 for(int o=0;o<I.no;o++) {
  if(elapsed()-start>45.)break;
  vector<int>op{o};vector<double>h(I.no,0.);auto G=G0;
  double before=elapsed(),direct=F.evaluate(op,h,G),searched=F.search(op,h,G,40,start+45.);
  worst=max(worst,fabs(direct-searched));
  if(tested++)printf(",");
  printf("{\"office\":%d,\"direct\":%.17g,\"searched\":%.17g,\"equal\":%s,\"seconds\":%.9f}",o,direct,searched,direct==searched?"true":"false",elapsed()-before);
 }
 printf("],\"tested\":%d,\"max_error\":%.17g,\"seconds\":%.9f}\n",tested,worst,elapsed()-start);
 return worst==0.?0:3;
}
'''
for rev in ['v5','v6']:
 source=R/'artifacts'/rev/'main.cpp';assert source.exists()
 s=source.read_text().replace('int main(int argc, char** argv) {','static int unused_contest_main(int argc, char** argv) {')+harness
 p=d/(rev+'.cpp');p.write_text(s)
 cmd=['taskset','-c','14,15','g++','-O3','-std=c++17',str(p),'-o',str(d/rev)];subprocess.run(cmd,check=True)
 inp=ROOT/'experiments/structural_v9/inputs/dev/huge.json'
 with (d/(rev+'.json')).open('x')as f:subprocess.run(['taskset','-c','14,15',str(d/rev),str(inp)],stdout=f,check=True,timeout=60)
 a=json.loads((d/(rev+'.json')).read_text());print(json.dumps(dict(revision=rev,tested=a['tested'],max_error=a['max_error'],seconds=a['seconds'],source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())),flush=True)
