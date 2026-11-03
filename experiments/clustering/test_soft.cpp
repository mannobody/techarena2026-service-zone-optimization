#define main prototype_main
#include "artifacts/prototype.cpp"
#undef main

int main() {
    Inst I;I.ns=7;I.no=3;I.nsk=1;I.alpha=2.7;I.A=0;I.ext=2.;
    I.ntask={0,1,2,3,1,2,1};I.totalTasks=10;I.maxsize={1,2,3};I.servable.assign(7,1);
    I.P={{.2,.1},{.3,.7},{.8,.2},{.9,.9},{.4,.5},{.6,.3},{.7,.8},{0.,0.},{1.,0.},{.5,1.}};
    I.prof.resize(21);I.D.resize(21);
    for(int b=0;b<3;b++)for(int s=0;s<7;s++){I.prof[b*7+s]=sin(s*1.3+b)*3+2.;I.D[b*7+s]=10.-I.prof[b*7+s];}
    vector<int> op={0,1,2};vector<array<double,3>> theta={{.3,-.2,.5},{-.7,.4,-.3},{.1,.9,.2}};
    double errors[2];
    for(int reject=0;reject<2;reject++) {
        SoftClusterProfit m(I,op,reject);vector<array<double,3>> grad;
        m.eval(theta,op,.7,&grad,1e100);double error=0.;
        for(int b=0;b<3;b++)for(int j=0;j<3;j++) {
            auto t=theta;t[b][j]+=1e-6;double plus=m.eval(t,op,.7,nullptr,1e100);
            t[b][j]-=2e-6;double minus=m.eval(t,op,.7,nullptr,1e100);
            error=max(error,fabs((plus-minus)/2e-6-grad[b][j]));
        }
        errors[reject]=error;if(error>1e-5)throw runtime_error("soft profit gradient mismatch");
    }
    printf("{\"gradient_error_without_reject\":%.12g,\"gradient_error_with_reject\":%.12g}\n",errors[0],errors[1]);
}
