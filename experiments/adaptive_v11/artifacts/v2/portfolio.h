// Per-instance online portfolio; only two compute workers are ever active.
namespace portfolio {
using Clock=std::chrono::steady_clock;
static const auto start=Clock::now();
static bool active=false,share=false;
static std::atomic<bool>stop[2]{{false},{false}},done[2]{{false},{false}};
static std::atomic<int>promoted{-1};
static std::atomic<bool>idle_release[2]{{false},{false}};
static std::mutex mx,write_mx;
static std::condition_variable cv;
static double best=0,individual[2]={0,0};
static std::vector<int>best_asg;static std::vector<char>best_open;
static std::vector<std::pair<double,double>>history[2];
static int fd=-1;static std::string buffer[2];static std::atomic<int>index{-1};
static std::atomic<bool>writing{false},pending{false};
static double elapsed(){return std::chrono::duration<double>(Clock::now()-start).count();}
static void raw_write(int k){
 if(fd<0||k<0)return;const auto&b=buffer[k];size_t n=0;
 while(n<b.size()){ssize_t r=pwrite(fd,b.data()+n,b.size()-n,n);if(r<=0)break;n+=r;}
 ftruncate(fd,n);
}
static void signal_stop(int){
 if(writing.exchange(true,std::memory_order_acq_rel)){pending.store(true,std::memory_order_release);return;}
 raw_write(index.load(std::memory_order_acquire));_exit(0);
}
static void output(const std::string&text){
 std::lock_guard<std::mutex>lock(write_mx);
 // A signal owning writing will exit the process; it never waits on this mutex.
 while(writing.exchange(true,std::memory_order_acq_rel))std::this_thread::yield();
 int k=index.load(std::memory_order_relaxed)==0?1:0;buffer[k]=text;
 index.store(k,std::memory_order_release);raw_write(k);
 writing.store(false,std::memory_order_release);
 if(pending.load(std::memory_order_acquire))signal_stop(0);
}
static void submit(int id,double value,const std::string&text,const std::vector<int>*a=nullptr,const std::vector<char>*o=nullptr){
 std::lock_guard<std::mutex>lock(mx);
 if(value>individual[id]+1e-9){individual[id]=value;history[id].push_back({elapsed(),value});}
 if(value>best+1e-9){best=value;if(a&&o){best_asg=*a;best_open=*o;}output(text);}
}
static bool borrow(int id,double own,std::vector<int>&a,std::vector<char>&o){
 if(!active||!share)return false;std::lock_guard<std::mutex>lock(mx);
 if(best<=own+1e-9||best_asg.empty())return false;a=best_asg;o=best_open;return true;
}
static bool await_second(int id){
 std::unique_lock<std::mutex>lock(mx);
 cv.wait(lock,[&]{return stop[id].load()||idle_release[id].load()||promoted.load()==id;});return !stop[id].load()&&!idle_release[id].load()&&promoted.load()==id;
}
static void complete(int id){done[id].store(true);cv.notify_all();}
static double at(int id,double time){double v=0;for(auto q:history[id])if(q.first<=time)v=q.second;return v;}
static void monitor(double limit,double fraction,int policy){
 const double decision=std::min(limit-.5,std::max(.2,limit*fraction));
 while(elapsed()<decision&&!done[0].load()&&!done[1].load())std::this_thread::sleep_for(std::chrono::milliseconds(20));
 int winner=-1;double x=0,y=0,slope[2]={0,0};
 {
  std::lock_guard<std::mutex>lock(mx);x=individual[0];y=individual[1];int lead=y>x?1:0,lag=1-lead;
  double dt=std::max(.1,std::min(30.,.1*limit));
  for(int i=0;i<2;i++)slope[i]=(individual[i]-at(i,elapsed()-dt))/dt;
  double gap=(individual[lead]-individual[lag])/std::max(1e-12,std::fabs(individual[lag]));
  bool decisive=gap>.02&&individual[lead]+slope[lead]*(limit-elapsed())>individual[lag]+slope[lag]*(limit-elapsed());
  if(policy==2||decisive||done[lag].load())winner=lead;
  fprintf(stderr,"AP_RACE at=%.6f v4=%.9f geometry=%.9f slope0=%.9f slope1=%.9f winner=%d policy=%d share=%d\n",elapsed(),x,y,slope[0],slope[1],winner,policy,(int)share);
 }
 if(winner>=0){
  int loser=1-winner;stop[loser].store(true);cv.notify_all();
  // Wait for cancellation to finish before starting the winner's second compute worker.
  while(!done[loser].load()&&elapsed()<limit-.3)std::this_thread::sleep_for(std::chrono::milliseconds(5));
  if(done[loser].load()&&!done[winner].load()){promoted.store(winner);cv.notify_all();}
 }
}
}
