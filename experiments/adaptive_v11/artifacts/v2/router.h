int main(int argc,char**argv){
 using namespace std;double limit=argc>3?atof(argv[3]):(getenv("TL")?atof(getenv("TL")):280.);
 string input=argc>1?argv[1]:"instance.json",output=argc>2?argv[2]:"solution.json";
 portfolio::fd=open(output.c_str(),O_WRONLY|O_CREAT|O_TRUNC,0644);portfolio::output("[]\n");
 struct sigaction sa{};sa.sa_handler=portfolio::signal_stop;sigemptyset(&sa.sa_mask);
 for(int s:{SIGTERM,SIGINT,SIGALRM,SIGHUP,SIGUSR1})sigaction(s,&sa,nullptr);
 struct itimerval timer{};double budget=max(.005,limit-portfolio::elapsed()-.03);
 timer.it_value.tv_sec=(time_t)budget;timer.it_value.tv_usec=(suseconds_t)((budget-timer.it_value.tv_sec)*1e6);setitimer(ITIMER_REAL,&timer,nullptr);
 try{
  auto I=spatial::load_instance(input); // Same allowed instance, no answer files or cache.
  const char*forced=getenv("AP_FORCE");
  int policy=getenv("AP_POLICY")?max(0,min(2,atoi(getenv("AP_POLICY")))):1;
  portfolio::share=!getenv("AP_SHARE")||atoi(getenv("AP_SHARE"));
  // Fix the selected expert configuration independently of inherited shell flags.
  setenv("GW_MODE","1",1);setenv("ZM_POOL","0",1);setenv("ZM_RESERVE","0",1);setenv("NT","2",1);setenv("EXACT2","0",1);
  // Exact tiny zone master is guarded internally by size/domain and returns to native search if incomplete.
  if(I.ns<=16||I.no==0||(forced&&string(forced)=="geometry")){
   fprintf(stderr,"AP_ROUTE method=geometry_or_tiny sites=%d offices=%d\n",I.ns,I.no);return spatial::main_entry(argc,argv);
  }
  if(forced&&string(forced)=="v4"){
   fprintf(stderr,"AP_ROUTE method=v4 sites=%d offices=%d\n",I.ns,I.no);return classic::main_entry(argc,argv);
  }
  double scale=0;for(double r:I.reward)scale+=fabs(r);scale=max(1e-12,scale/max(1,I.ns));
  double pressure=I.alpha*max(1.,(double)I.totalTasks/max(1,I.ns))/scale;
  // Dimensionless workload classification controls observation time, not an oracle winner label.
  double sx=0,sy=0,sxx=0,syy=0,sxy=0;size_t n=0;
  for(int o=0;o<I.no;o++)for(int s=0;s<I.ns;s++){
   double x=hypot(I.P[s].x-I.P[I.ns+o].x,I.P[s].y-I.P[I.ns+o].y),y=I.d(o,s);
   sx+=x;sy+=y;sxx+=x*x;syy+=y*y;sxy+=x*y;n++;
  }
  double corr=0,den=(n*sxx-sx*sx)*(n*syy-sy*sy);if(den>0)corr=(n*sxy-sx*sy)/sqrt(den);
  bool difficult=I.ns>2000||pressure>1||corr<-.5;
  double fraction=difficult?.55:.40;
  fprintf(stderr,"AP_ROUTE method=race sites=%d offices=%d balance_pressure=%.9f geo_corr=%.9f horizon=%.3f policy=%d share=%d overhead=%.6f\n",I.ns,I.no,pressure,corr,fraction,policy,(int)portfolio::share,portfolio::elapsed());
  // Release the router's duplicate input before starting both experts.
  I=spatial::Inst();portfolio::active=true;mallopt(M_ARENA_MAX,4);
  thread a([&]{classic::main_entry(argc,argv);portfolio::complete(0);});
  thread b([&]{spatial::main_entry(argc,argv);portfolio::complete(1);});
  if(policy)portfolio::monitor(limit,fraction,policy);
  // Under permanent dual policy no helper is ever promoted; let compute workers finish.
  while(!portfolio::done[0].load()||!portfolio::done[1].load()){
   // Idle helper threads must be released once their own main worker has stopped.
   if(portfolio::elapsed()>limit-.20){portfolio::stop[0].store(true);portfolio::stop[1].store(true);portfolio::cv.notify_all();}
   this_thread::sleep_for(chrono::milliseconds(10));
  }
  a.join();b.join();fprintf(stderr,"AP_FINAL objective=%.9f t=%.6f promoted=%d\n",portfolio::best,portfolio::elapsed(),portfolio::promoted.load());
 }catch(const exception&e){fprintf(stderr,"error: adaptive %s\n",e.what());return 1;}
 return 0;
}
