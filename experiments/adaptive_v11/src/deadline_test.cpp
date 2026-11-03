#include <bits/stdc++.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>
#include "portfolio.h"
int main(int argc,char**argv){
 using namespace portfolio;fd=open(argv[1],O_CREAT|O_TRUNC|O_WRONLY,0644);output("[]\n");
 std::string text="{\"complete\":true,\"payload\":\""+std::string(512*1024,'x')+"\"}\n";
 struct sigaction sa{};sa.sa_handler=signal_stop;sigemptyset(&sa.sa_mask);sigaction(SIGALRM,&sa,nullptr);
 struct itimerval timer{};timer.it_value.tv_usec=atoi(argv[2]);setitimer(ITIMER_REAL,&timer,nullptr);
 for(;;)output(text);
}
