#include <bits/stdc++.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>
#include "portfolio.h"
int main(int argc,char**argv){
 using namespace portfolio;fd=open(argv[1],O_CREAT|O_TRUNC|O_WRONLY,0644);output("[]\n");
 active=share=true;std::vector<int>a{0,1,0};std::vector<char>o{1,1};
 std::thread t0([&]{for(int i=1;i<=2000;i++)submit(0,i,"{\"value\":"+std::to_string(i)+"}\n",&a,&o);});
 std::thread t1([&]{for(int i=1;i<=2000;i++)submit(1,2*i,"{\"value\":"+std::to_string(2*i)+"}\n",&a,&o);});
 t0.join();t1.join();assert(best==4000);std::vector<int>b;std::vector<char>p;
 assert(borrow(0,2000,b,p)&&b==a&&p==o);assert(!borrow(1,4000,b,p));
 submit(0,1,"[]\n");assert(best==4000);
 std::thread helper([]{assert(await_second(0));});promoted.store(0);cv.notify_all();helper.join();
 std::thread canceled([]{assert(!await_second(1));});stop[1].store(true);cv.notify_all();canceled.join();
 fprintf(stderr,"arbiter best=%.0f output_monotone=1 borrow=1 cancellation=1 promotion=1\n",best);
}
