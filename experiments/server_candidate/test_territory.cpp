#define main prototype_main
#include "../evolution/artifacts/integrated.cpp"
#undef main

int main() {
    Inst I;I.ns=10;I.no=3;I.nw=0;I.nsk=1;I.A=0;I.alpha=0.;I.maxsize={4,4,2};I.cost={0.,0.,1.};
    I.reward.assign(10,100.);I.ntask.assign(10,0);I.skillset.resize(10);I.servable.assign(10,1);I.Nk={0};
    I.cand.assign(10,{0,1,2});I.D.assign(30,150.);I.prof.assign(30,-50.);
    for(int s=0;s<10;s++){int o=s<4?0:s<8?1:2;double p=s>=8?1.:(s%4>=2?10.:5.);I.prof[o*10+s]=p;I.D[o*10+s]=100.-p;}
    I.P={{-1.,0.},{1.,0.},{.2,0.},{.4,0.},{9.,0.},{11.,0.},{10.2,0.},{10.4,0.},{19.,0.},{21.,0.},
         {0.,0.},{10.,0.},{20.,0.}};
    Sol s;s.init(I);for(int o=0;o<3;o++)s.open_office(o);
    s.force_add(0,0);s.force_add(1,0);s.force_add(4,1);s.force_add(5,1);s.force_add(8,2);s.force_add(9,2);
    double before=s.objective();
    if(fabs(before-21.)>1e-8||!territory_select(s,1e100))throw runtime_error("territory did not improve");
    vector<int> staff;double score=0.;
    if(!s.greedy_workers(&staff)||!verify(I,s.asg,s.isopen,staff,&score)||fabs(score-60.)>1e-8)
        throw runtime_error("territory answer invalid");
    printf("{\"before\":21,\"after\":60,\"sites\":[4,4,0],\"closed_bottleneck_office\":2}\n");
}
