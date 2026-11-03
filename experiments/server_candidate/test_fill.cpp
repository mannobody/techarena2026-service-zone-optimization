#define main prototype_main
#include "../evolution/artifacts/integrated.cpp"
#undef main

int main() {
    Inst I;I.ns=4;I.no=2;I.nw=0;I.nsk=1;I.A=4;I.alpha=0.;
    I.reward.assign(4,100.);I.cost={0.,0.};I.ntask.assign(4,0);I.maxsize={10,10};
    I.skillset.resize(4);I.Nk={0};I.servable.assign(4,1);I.cand.assign(4,{0,1});
    I.D.assign(8,0.);I.D[7]=10.;I.prof.assign(8,100.);I.prof[7]=90.;
    I.P={{-1.,0.},{9.,0.},{11.,0.},{10.,0.},{0.,0.},{10.,0.}};
    auto initial=[&](){Sol s;s.init(I);s.open_office(0);s.open_office(1);s.force_add(0,0);s.force_add(1,1);s.force_add(2,1);return s;};
    Sol old=initial();Engine E0(old);setenv("FILL_RETRY","0",1);greedy_fill(old,E0,1e100);
    Sol now=initial();Engine E1(now);finish_fill(now,E1,1e100);
    if(old.asg[3]!=-1||now.asg[3]!=1||fabs(old.objective()-300.)>1e-8||fabs(now.objective()-390.)>1e-8)
        throw runtime_error("best-feasible fill witness failed");
    vector<int> workers;double value=0.;
    if(!now.greedy_workers(&workers)||!verify(I,now.asg,now.isopen,workers,&value)||fabs(value-390.)>1e-8)
        throw runtime_error("fill witness not valid");
    Inst J=I;J.ns=5;J.A=5;J.reward.assign(5,100.);J.ntask.assign(5,0);J.skillset.resize(5);
    J.servable.assign(5,1);J.cand.assign(5,{0,1});J.D.assign(10,0.);J.D[9]=10.;J.prof.assign(10,100.);J.prof[9]=90.;
    J.P={{0.,-1.},{0.,1.},{3.,-1.},{3.,1.},{5.,0.},{0.,0.},{3.,0.}};
    Sol u;u.init(J);u.open_office(0);u.open_office(1);u.force_add(0,0);u.force_add(1,0);u.force_add(2,1);u.force_add(3,1);
    Sol v=u;Engine EU(u),EV(v);setenv("FILL_RETRY","0",1);greedy_fill(u,EU,1e100);
    EV.rec=true;finish_fill(v,EV,1e100);
    if(u.asg[4]!=-1||v.asg[4]!=1||fabs(v.objective()-490.)>1e-8)throw runtime_error("uncovered retry witness");
    if(!v.greedy_workers(&workers)||!verify(J,v.asg,v.isopen,workers,&value))throw runtime_error("uncovered witness invalid");
    EV.undo(0);v.recompute_psum();
    if(v.asg[4]!=-1||fabs(v.objective()-400.)>1e-8)throw runtime_error("retry journal rollback");
    printf("{\"covered\":{\"legacy\":300,\"retry\":390},\"uncovered\":{\"legacy\":400,\"retry\":490},\"journal_rollback\":true}\n");
}
