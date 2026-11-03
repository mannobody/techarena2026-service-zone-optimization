int main(int argc,char**argv){
 Inst I=load_instance(argv[1]);ifstream f(argv[2]);vector<int>a(I.ns,-1);vector<char>op(I.no,0);for(int&x:a){f>>x;if(x>=0)op[x]=1;}
 int n;f>>n;vector<int>xs(n);for(int&x:xs)f>>x;vector<int>ops;for(int o=0;o<I.no;o++)if(op[o])ops.push_back(o);
 Sol s;s.init(I);s.load_state(a,op);BoundarySearch b(s,xs,ops,elapsed()+10,atoi(argv[3]));b.dfs(0);b.finish();
 vector<int>w;double val=0;bool ok=s.greedy_workers(&w)&&verify(I,s.asg,s.isopen,w,&val);
 printf("{\"score\":%.15g,\"valid\":%s,\"stopped\":%s,\"nodes\":%ld}\n",val,ok?"true":"false",b.stopped?"true":"false",boundary_stats.nodes);
}
