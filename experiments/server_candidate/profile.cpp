#include <new>
#include <cstdlib>
static bool count_alloc=false;
static unsigned long long allocations=0, allocated_bytes=0;
void* operator new(std::size_t n) {if(count_alloc){allocations++;allocated_bytes+=n;}if(void*p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}
void operator delete(void*p)noexcept{std::free(p);}
void operator delete[](void*p)noexcept{std::free(p);}
void operator delete(void*p,std::size_t)noexcept{std::free(p);}
void operator delete[](void*p,std::size_t)noexcept{std::free(p);}
#define main solver_main
#ifndef SOURCE
#define SOURCE "artifacts/before.cpp"
#endif
#include SOURCE
#undef main
int main(int argc,char**argv){
    Inst I=load_instance(argv[1]);Fast F(I);mt19937_64 r(1701);
    vector<double> h(I.no,0);vector<Pt> G(I.P.begin()+I.ns,I.P.end());
    vector<vector<int>> subsets(64);
    for(auto&op:subsets){vector<int> order(I.no);iota(order.begin(),order.end(),0);shuffle(order.begin(),order.end(),r);int k=1+r()%max(1,I.no);op.assign(order.begin(),order.begin()+k);sort(op.begin(),op.end());}
    vector<vector<int>> mem;
    for(int t=0;t<128;t++)F.evaluate(subsets[t%64],h,G,t%7?nullptr:&mem);
    allocations=allocated_bytes=0;count_alloc=true;double start=elapsed(),checksum=0;
    for(int t=0;t<384;t++){double v=F.evaluate(subsets[t%64],h,G,t%7?nullptr:&mem);if(v>NEG/2)checksum+=v;}
    double seconds=elapsed()-start;count_alloc=false;
    printf("{\"kind\":\"fast\",\"calls\":384,\"allocations\":%llu,\"bytes\":%llu,\"seconds\":%.9f,\"checksum\":%.17g}\n",allocations,allocated_bytes,seconds,checksum);
    vector<Pt> points, hull;for(int j=0;j<min(I.ns,500);j++)points.push_back(I.P[j]);
    for(int t=0;t<4;t++){hull=points;hull_of(hull);}
    allocations=allocated_bytes=0;count_alloc=true;start=elapsed();checksum=0;
    for(int t=0;t<5000;t++){hull=points;hull_of(hull);for(auto p:hull)checksum+=p.x+p.y;}
    seconds=elapsed()-start;count_alloc=false;
    printf("{\"kind\":\"hull\",\"calls\":5000,\"allocations\":%llu,\"bytes\":%llu,\"seconds\":%.9f,\"checksum\":%.17g}\n",allocations,allocated_bytes,seconds,checksum);
}
