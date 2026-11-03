import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
d=R/'artifacts/balanced_mechanism';d.mkdir(exist_ok=False)
a=dict(sites=[dict(x=x,y=0,reward=10,tasks=[0])for x in [-3,-2,-1,2]],offices=[dict(x=x,y=0,cost=0,maxSize=2)for x in [-3,3]],workers=[[0],[0]],distances=[[0]*4,[0]*4],maxDifference=0,balanceCoefficient=0)
inp=R/'inputs/balanced_geometry.json';inp.write_text(json.dumps(a))
h=r'''
int main(int argc,char**argv){
 Inst I=load_instance(argv[1]);g_geo_grid.init(I);Fast F(I);vector<int>op{0,1};
 vector<double>h(I.no,0.);vector<Pt>G(I.P.begin()+I.ns,I.P.end());vector<int>labels;
 F.cells(op,h,G,labels);for(int&x:labels)x=op[x];
 Sol before;realize(before,I,op,labels,elapsed()+5);repair_sizes(before);before.recompute_psum();
 vector<int>wb;double fb=0.;bool vb=before.greedy_workers(&wb)&&verify(I,before.asg,before.isopen,wb,&fb);
 double loss=gw_balance_cells(I,F,op,h,G,labels,elapsed()+1.);
 Sol after;realize(after,I,op,labels,elapsed()+5);repair_sizes(after);after.recompute_psum();
 vector<int>wa;double fa=0.;bool va=after.greedy_workers(&wa)&&verify(I,after.asg,after.isopen,wa,&fa);
 vector<int>single{1};vector<double>hs(I.no,0.);vector<int>ls;
 gw_balance_cells(I,F,single,hs,G,ls,elapsed()+1.);bool ids=true;for(int x:ls)ids&=x==1;
 if(!vb||!va||fb!=20.||fa!=40.||!ids)return 4;
 printf("{\"before\":%.0f,\"after\":%.0f,\"mass_loss\":%.9g,\"singleton_office_ids\":true,\"before_solution\":%s,\"after_solution\":%s}\n",fb,fa,loss,serialize(I,before.asg,before.isopen,wb).c_str(),serialize(I,after.asg,after.isopen,wa).c_str());
}
'''
s=(R/'artifacts/v8/main.cpp').read_text().replace('int main(int argc, char** argv) {','static int unused_contest_main(int argc, char** argv) {')+h
p=d/'main.cpp';p.write_text(s);subprocess.run(['taskset','-c','14,15','g++','-O3','-std=c++17',str(p),'-o',str(d/'check')],check=True)
with (d/'result.json').open('x')as f:subprocess.run(['taskset','-c','14,15',str(d/'check'),str(inp)],stdout=f,check=True)
result=json.loads((d/'result.json').read_text());checks=[]
for name,value in [('before',20),('after',40)]:
 out=d/(name+'.solution.json');out.write_text(json.dumps(result[name+'_solution']));v=validate(inp,out);assert v==value;checks.append(dict(name=name,official=v))
(R/'BALANCED_MECHANISM.json').write_text(json.dumps(dict(mechanism=result,official=checks,note='Constructor mechanism, not a proof that the whole frozen v4 fails this tiny instance.'),indent=2));print(json.dumps(checks))
