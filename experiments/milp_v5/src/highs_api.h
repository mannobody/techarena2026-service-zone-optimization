// Optional HiGHS C API, compatible with the documented 32-bit HighsInt ABI.
// Library absence or ABI mismatch disables only the MIP tail.
#include <dlfcn.h>
struct V5Highs {
 void* lib=nullptr;bool ready=false;
 void*(*create)()=nullptr;void(*destroy)(void*)=nullptr;
 int(*intsize)(const void*)=nullptr;
 int(*setbool)(void*,const char*,int)=nullptr;
 int(*setint)(void*,const char*,int)=nullptr;
 int(*setdouble)(void*,const char*,double)=nullptr;
 int(*pass)(void*,int,int,int,int,int,double,const double*,const double*,const double*,const double*,const double*,const int*,const int*,const double*,const int*)=nullptr;
 int(*setsol)(void*,const double*,const double*,const double*,const double*)=nullptr;
 int(*getsol)(const void*,double*,double*,double*,double*)=nullptr;
 int(*getint)(const void*,const char*,int*)=nullptr;
 int(*run)(void*)=nullptr;int(*status)(const void*)=nullptr;
 template<class T>bool bind(T&f,const char*n){f=reinterpret_cast<T>(dlsym(lib,n));return f!=nullptr;}
 V5Highs(){
  lib=dlopen("libhighs.so",RTLD_NOW|RTLD_LOCAL);if(!lib)lib=dlopen("libhighs.so.1",RTLD_NOW|RTLD_LOCAL);if(!lib)return;
  ready=bind(create,"Highs_create")&&bind(destroy,"Highs_destroy")&&bind(intsize,"Highs_getSizeofHighsInt")&&bind(setbool,"Highs_setBoolOptionValue")&&bind(setint,"Highs_setIntOptionValue")&&bind(setdouble,"Highs_setDoubleOptionValue")&&bind(pass,"Highs_passMip")&&bind(setsol,"Highs_setSolution")&&bind(getsol,"Highs_getSolution")&&bind(getint,"Highs_getIntInfoValue")&&bind(run,"Highs_run")&&bind(status,"Highs_getModelStatus");
  if(ready){void*h=create();ready=h&&intsize(h)==sizeof(int);if(h)destroy(h);}
 }
};
static V5Highs&v5_api(){static V5Highs a;return a;}
struct V5Model {
 vector<double>cost,lb,ub,rl,ru,av,warm;vector<int>integer,rs{0},ai;
 int var(double c,double low,double high,int integral,double w=0){int j=cost.size();cost.push_back(c);lb.push_back(low);ub.push_back(high);integer.push_back(integral);warm.push_back(w);return j;}
 void row(vector<pair<int,double>> r,double low,double high){sort(r.begin(),r.end());for(size_t i=0;i<r.size();){size_t j=i+1;double v=r[i].second;while(j<r.size()&&r[j].first==r[i].first)v+=r[j++].second;if(v){ai.push_back(r[i].first);av.push_back(v);}i=j;}rs.push_back(ai.size());rl.push_back(low);ru.push_back(high);}
};
