// OFFLINE ONLY. Include after frozen v4 with its main renamed.
static void checkpoint_load(const Inst&I,const char*path,Sol&s){
 ifstream f(path);string text((istreambuf_iterator<char>(f)),{});JReader j(text.data(),text.data()+text.size());
 vector<int>a(I.ns,-1),w(I.nw,-1);vector<char>op(I.no,0);j.need('[');
 if(!j.eat(']')){do{
  j.need('{');int o=-1;vector<int>ss,ww;
  do{string k=j.str();j.need(':');if(k=="officeId")o=j.num();else if(k=="sites"||k=="workers"){
   auto&v=k=="sites"?ss:ww;j.need('[');if(!j.eat(']')){do{v.push_back(j.num());}while(j.eat(','));j.need(']');}
  }else j.skip();}while(j.eat(','));j.need('}');
  if(o<0||o>=I.no||op[o])throw runtime_error("checkpoint office");op[o]=1;
  for(int x:ss){if(x<0||x>=I.ns||a[x]>=0)throw runtime_error("checkpoint site");a[x]=o;}
  for(int x:ww){if(x<0||x>=I.nw||w[x]>=0)throw runtime_error("checkpoint worker");w[x]=o;}
 }while(j.eat(','));j.need(']');}
 double value=0;if(!verify(I,a,op,w,&value))throw runtime_error("invalid checkpoint certificate");
 s.init(I);s.load_state(a,op);
 // Preserve the input certificate even when no improvement is found before deadline.
 g_best.store(value);g_best_asg=a;g_best_open=op;publish(serialize(I,a,op,w));
}
static int checkpoint_main(int argc,char**argv,void (*search)(Sol&,mt19937_64&,double,int,int)){
 if(argc!=6)return 2;
 const double seconds=atof(argv[4]),end=max(0.,seconds-.05);int mode=atoi(argv[5]);
 g_wdfs_deadline=end;DBG=true;
 Inst I=load_instance(argv[1]);g_geo_grid.init(I);Sol initial;
 g_fd=open(argv[3],O_WRONLY|O_CREAT|O_TRUNC,0644);publish("[]\n");
 checkpoint_load(I,argv[2],initial);double before=g_best.load(),loaded=elapsed();
 int nt=detect_cpus();uint64_t seed=getenv("SEED")?strtoull(getenv("SEED"),nullptr,10):0;
 auto run=[&](int tid){Sol s;s.init(I);s.load_state(initial.asg,initial.isopen);
  mt19937_64 rng(0xABC8837ULL+seed*1000003ULL+tid*7919ULL);
  if(elapsed()<end)search(s,rng,end,mode,tid);
 };
 vector<thread>th;for(int i=1;i<nt;i++)th.emplace_back(run,i);run(0);for(auto&t:th)t.join();
 raw_write(g_idx.load(),false);if(g_fd>=0)close(g_fd);g_fd=-1;
 fprintf(stderr,"checkpoint before=%.12f after=%.12f init=%.6f wall=%.6f threads=%d mode=%d\n",before,g_best.load(),loaded,elapsed(),nt,mode);
 return 0;
}
