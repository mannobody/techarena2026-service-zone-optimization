// TechArena 2026, кейс 3 "Service Zone Optimization" — решатель на C++.
// Только стандартная библиотека (+ pthread). Код разбит на части solver/*.h,
// solve.cpp включает их по порядку (одна единица трансляции). Для посылки
// submission/make_zips.sh склеивает всё обратно в один solve.cpp.
//
// Читает instance.json, пишет solution.json в текущем каталоге.
// Отладка: ./solve [in.json] [out.json] [секунды] ; лимит также через TL=...,
// потоки NT=..., зерно SEED=... (без SEED поведение как раньше).
//
// Схема:
//   1) конструкторы стартовых разбиений (power diagram, секторы, дорожная близость,
//      разрезы прямыми) — все дают геометрически допустимое разбиение;
//   2) точный DP "какие сайты оставить" при фиксированных зонах: окно нагрузки
//      [lo,hi] + 0/1-рюкзак по числу задач. Удаление сайтов не ломает геометрию,
//      поэтому DP точен внутри зон;
//   3) LNS (ruin & recreate) + отжиг по одиночным ходам, многопоточно;
//   4) защита от TLE: пред-сериализованный буфер + обработчик сигналов.

// base.h: заголовки std, время (elapsed), глобальные флаги отладки.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <climits>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <memory>
#include <mutex>
#include <numeric>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unistd.h>
#include <fcntl.h>
#include <sched.h>
#include <malloc.h>
#include <csignal>
#include <vector>
#include <map>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace std;
using Clock = chrono::steady_clock;
static const Clock::time_point T0 = Clock::now();
static inline double elapsed() { return chrono::duration<double>(Clock::now() - T0).count(); }

static const double NEG = -1e300;
static bool DBG = false, DBG2 = false;

// json.h: минимальный разбор JSON.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ===================================================================== JSON
// Специализированный парсер под известную схему: не строит дерево.
struct JReader {
    const char* p;
    const char* e;
    JReader(const char* b, const char* en) : p(b), e(en) {}
    void ws() { while (p < e && (unsigned char)*p <= ' ') p++; }
    bool eat(char c) { ws(); if (p < e && *p == c) { p++; return true; } return false; }
    void need(char c) { if (!eat(c)) throw runtime_error(string("expected ") + c); }
    double num() {
        ws();
        char* q;
        double v = strtod(p, &q);
        if (q == p) throw runtime_error("bad number");
        p = q;
        return v;
    }
    string str() {
        ws();
        need('"');
        string r;
        while (p < e && *p != '"') {
            if (*p == '\\') {
                p++;
                char c = *p++;
                switch (c) {
                    case 'n': r += '\n'; break;
                    case 't': r += '\t'; break;
                    case 'r': r += '\r'; break;
                    case 'b': r += '\b'; break;
                    case 'f': r += '\f'; break;
                    case 'u': p += 4; r += '?'; break;
                    default: r += c;
                }
            } else r += *p++;
        }
        need('"');
        return r;
    }
    void skip() {  // пропустить произвольное значение
        ws();
        if (p >= e) return;
        if (*p == '"') { str(); return; }
        if (*p == '{' || *p == '[') {
            char open = *p, close = open == '{' ? '}' : ']';
            int d = 0;
            bool instr = false;
            while (p < e) {
                char c = *p;
                if (instr) {
                    if (c == '\\') p++;
                    else if (c == '"') instr = false;
                } else if (c == '"') instr = true;
                else if (c == open) d++;
                else if (c == close) { d--; if (!d) { p++; return; } }
                p++;
            }
            return;
        }
        while (p < e && *p != ',' && *p != '}' && *p != ']') p++;
    }
};

// geom.h: точки, векторное произведение, выпуклая оболочка.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ================================================================ геометрия
struct Pt { double x = 0, y = 0; };
static inline bool ptless(const Pt& a, const Pt& b) { return a.x < b.x || (a.x == b.x && a.y < b.y); }
static inline bool pteq(const Pt& a, const Pt& b) { return a.x == b.x && a.y == b.y; }
static inline double cr(const Pt& o, const Pt& a, const Pt& b) {
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
}

// Original exact dyadic fallback for finite binary64 inputs; no external library.
// Filter principle follows robust orientation literature; fallback sums six exact products.
static bool g_geo_exact=!getenv("GEO_EXACT")||atoi(getenv("GEO_EXACT"));
struct GeoDyadic{uint64_t m;int e;bool neg;};
static GeoDyadic geo_decode(double x){uint64_t u;memcpy(&u,&x,8);int e=(u>>52)&2047;return{(u&((1ULL<<52)-1))|(e?(1ULL<<52):0),e?e-1023-52:-1074,(bool)(u>>63)};}
static int geo_exact_orientation(Pt a,Pt b,Pt c){
 GeoDyadic v[6]={geo_decode(a.x),geo_decode(a.y),geo_decode(b.x),geo_decode(b.y),geo_decode(c.x),geo_decode(c.y)};
 const int ij[6][3]={{0,3,0},{2,5,0},{4,1,0},{1,2,1},{3,4,1},{5,0,1}};int emin=10000;
 for(auto&t:ij)if(v[t[0]].m&&v[t[1]].m)emin=min(emin,v[t[0]].e+v[t[1]].e);if(emin==10000)return 0;
 array<uint64_t,70>pos{},neg{};
 auto addword=[](array<uint64_t,70>&arr,int i,uint64_t z){while(z&&i<70){uint64_t old=arr[i];arr[i]+=z;z=arr[i]<old;i++;}};
 for(auto&t:ij){auto u=v[t[0]],w=v[t[1]];if(!u.m||!w.m)continue;unsigned __int128 product=(unsigned __int128)u.m*w.m;int shift=u.e+w.e-emin,word=shift/64,bit=shift%64;auto&arr=(u.neg^w.neg^(bool)t[2])?neg:pos;
  uint64_t lo=(uint64_t)product,hi=(uint64_t)(product>>64);addword(arr,word,lo<<bit);addword(arr,word+1,hi<<bit);
  if(bit){addword(arr,word+1,lo>>(64-bit));addword(arr,word+2,hi>>(64-bit));}}
 for(int i=69;i>=0;i--)if(pos[i]!=neg[i])return pos[i]>neg[i]?1:-1;return 0;
}
static int geo_orientation(Pt a,Pt b,Pt c){
 double ax=a.x-c.x,bx=b.x-c.x,ay=a.y-c.y,by=b.y-c.y;
 double left=ax*by,right=ay*bx,det=left-right,sum=fabs(left)+fabs(right);
 if(isfinite(sum)&&sum>1e-280&&fabs(det)>1.7763568394002505e-15*sum)return det>0?1:-1;
 return geo_exact_orientation(a,b,c);
}
static double geo_turn(Pt a,Pt b,Pt c){return g_geo_exact?(double)geo_orientation(a,b,c):cr(a,b,c);}
static bool geo_on_segment(Pt a,Pt b,Pt p){return geo_orientation(a,b,p)==0&&p.x>=min(a.x,b.x)&&p.x<=max(a.x,b.x)&&p.y>=min(a.y,b.y)&&p.y<=max(a.y,b.y);}
static bool geo_exact_covers(const vector<Pt>&h,Pt p){
 int m=h.size();if(!m)return false;if(m==1)return pteq(h[0],p);if(m==2)return geo_on_segment(h[0],h[1],p);
 if(m<=8){for(int i=0;i<m;i++)if(geo_orientation(h[i],h[(i+1)%m],p)<0)return false;return true;}
 int a=geo_orientation(h[0],h[1],p),b=geo_orientation(h[0],h[m-1],p);if(a<0||b>0)return false;
 if(a==0)return geo_on_segment(h[0],h[1],p);if(b==0)return geo_on_segment(h[0],h[m-1],p);
 int lo=1,hi=m-1;while(hi-lo>1){int mid=(lo+hi)/2;if(geo_orientation(h[0],h[mid],p)>=0)lo=mid;else hi=mid;}return geo_orientation(h[lo],h[hi],p)>=0;
}

// Выпуклая оболочка (монотонная цепь), CCW, без коллинеарных. 1, 2 или >=3 точки.
static void hull_of(vector<Pt>& p) {
    sort(p.begin(), p.end(), ptless);
    p.erase(unique(p.begin(), p.end(), pteq), p.end());
    size_t n = p.size();
    if (n <= 2) return;
    static thread_local vector<Pt> h;
    h.resize(2 * n);
    size_t k = 0;
    for (size_t i = 0; i < n; i++) {
        while (k >= 2 && geo_turn(h[k - 2], h[k - 1], p[i]) <= 0) k--;
        h[k++] = p[i];
    }
    for (size_t i = n - 1, t = k + 1; i-- > 0;) {
        while (k >= t && geo_turn(h[k - 2], h[k - 1], p[i]) <= 0) k--;
        h[k++] = p[i];
    }
    p.assign(h.begin(), h.begin() + k - 1);
}

// inst.h: Inst: чтение инстанса, расстояния, навыки, рабочие.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// =================================================================== инстанс
struct Inst {
    int ns = 0, no = 0, nw = 0, nsk = 0;
    long long A = 0;
    double alpha = 0;
    vector<double> reward, cost;
    vector<int> ntask;                 // число задач сайта (с повторами)
    vector<int> maxsize;
    vector<vector<int>> skillset;      // уникальные навыки сайта
    vector<vector<int>> wskills;       // навыки рабочего
    vector<vector<char>> wmask;        // рабочий -> маска навыков
    vector<int> wcount;
    vector<int> Nk;                    // число рабочих с навыком k
    vector<double> D;                  // [o*ns + s]
    vector<double> prof;               // reward[s] - D[o][s]
    vector<char> servable;
    vector<Pt> P;                      // сайты, затем офисы
    vector<vector<int>> cand;          // сайт -> офисы по возрастанию расстояния
    bool simple_workers = true;        // у каждого рабочего ровно один навык
    double ext = 1, eps_len = 0, eps_cr = 0;
    int totalTasks = 0;

    inline double d(int o, int s) const { return D[(size_t)o * ns + s]; }
    inline double pr(int o, int s) const { return prof[(size_t)o * ns + s]; }
};

static Inst load_instance(const string& path) {
    ifstream f(path, ios::binary);
    if (!f) throw runtime_error("no input file");
    string src((istreambuf_iterator<char>(f)), istreambuf_iterator<char>());
    size_t off = 0;
    if (src.size() >= 3 && (unsigned char)src[0] == 0xEF) off = 3;
    JReader R(src.data() + off, src.data() + src.size());
    Inst I;
    vector<vector<int>> tasks;
    vector<double> flatD;
    vector<Pt> sitePts, offPts;
    bool haveA = false, haveAl = false;
    R.need('{');
    if (!R.eat('}')) {
        while (true) {
            string key = R.str();
            R.need(':');
            if (key == "sites") {
                R.need('[');
                if (!R.eat(']')) while (true) {
                    R.need('{');
                    Pt q; double rw = 0; vector<int> tk;
                    if (!R.eat('}')) while (true) {
                        string k2 = R.str(); R.need(':');
                        if (k2 == "x") q.x = R.num();
                        else if (k2 == "y") q.y = R.num();
                        else if (k2 == "reward") rw = R.num();
                        else if (k2 == "tasks") {
                            R.need('[');
                            if (!R.eat(']')) while (true) { tk.push_back((int)llround(R.num())); if (R.eat(',')) continue; R.need(']'); break; }
                        } else R.skip();
                        if (R.eat(',')) continue;
                        R.need('}'); break;
                    }
                    sitePts.push_back(q); I.reward.push_back(rw); tasks.push_back(move(tk));
                    if (R.eat(',')) continue;
                    R.need(']'); break;
                }
            } else if (key == "offices") {
                R.need('[');
                if (!R.eat(']')) while (true) {
                    R.need('{');
                    Pt q; double c = 0; long long ms = 0;
                    if (!R.eat('}')) while (true) {
                        string k2 = R.str(); R.need(':');
                        if (k2 == "x") q.x = R.num();
                        else if (k2 == "y") q.y = R.num();
                        else if (k2 == "cost") c = R.num();
                        else if (k2 == "maxSize") ms = (long long)llround(R.num());
                        else R.skip();
                        if (R.eat(',')) continue;
                        R.need('}'); break;
                    }
                    I.cost.push_back(c);
                    I.maxsize.push_back((int)max(0LL, min(ms, (long long)INT_MAX)));
                    offPts.push_back(q);
                    if (R.eat(',')) continue;
                    R.need(']'); break;
                }
            } else if (key == "workers") {
                R.need('[');
                if (!R.eat(']')) while (true) {
                    vector<int> sk;
                    R.need('[');
                    if (!R.eat(']')) while (true) { sk.push_back((int)llround(R.num())); if (R.eat(',')) continue; R.need(']'); break; }
                    I.wskills.push_back(move(sk));
                    if (R.eat(',')) continue;
                    R.need(']'); break;
                }
            } else if (key == "distances") {
                R.need('[');
                if (!R.eat(']')) while (true) {
                    R.need('[');
                    if (!R.eat(']')) while (true) { flatD.push_back(R.num()); if (R.eat(',')) continue; R.need(']'); break; }
                    if (R.eat(',')) continue;
                    R.need(']'); break;
                }
            } else if (key == "maxDifference") { I.A = (long long)llround(R.num()); haveA = true; }
            else if (key == "balanceCoefficient") { I.alpha = R.num(); haveAl = true; }
            else R.skip();
            if (R.eat(',')) continue;
            R.need('}'); break;
        }
    }
    I.ns = tasks.size();
    I.no = I.cost.size();
    I.nw = I.wskills.size();
    if (!haveA) I.A = I.ns;
    if (!haveAl) I.alpha = 0;
    if (I.A < 0) I.A = 0;
    I.P.clear();
    I.P.reserve(I.ns + I.no);
    I.P.insert(I.P.end(), sitePts.begin(), sitePts.end());
    I.P.insert(I.P.end(), offPts.begin(), offPts.end());
    int maxsk = 0;
    for (auto& t : tasks) for (int k : t) maxsk = max(maxsk, k + 1);
    for (auto& w : I.wskills) for (int k : w) maxsk = max(maxsk, k + 1);
    I.nsk = max(1, maxsk);
    I.ntask.resize(I.ns);
    I.skillset.resize(I.ns);
    for (int s = 0; s < I.ns; s++) {
        I.ntask[s] = tasks[s].size();
        I.totalTasks += I.ntask[s];
        set<int> u(tasks[s].begin(), tasks[s].end());
        I.skillset[s].assign(u.begin(), u.end());
    }
    I.Nk.assign(I.nsk, 0);
    I.wmask.assign(I.nw, vector<char>(I.nsk, 0));
    I.wcount.assign(I.nw, 0);
    for (int w = 0; w < I.nw; w++) {
        set<int> u(I.wskills[w].begin(), I.wskills[w].end());
        for (int k : u) { I.wmask[w][k] = 1; I.Nk[k]++; }
        I.wcount[w] = u.size();
        if ((int)u.size() != 1) I.simple_workers = false;
    }
    I.servable.assign(I.ns, 1);
    for (int s = 0; s < I.ns; s++)
        for (int k : I.skillset[s]) if (I.Nk[k] == 0) I.servable[s] = 0;
    // расстояния
    I.D.assign((size_t)I.no * I.ns, 0.0);
    if ((long long)flatD.size() == (long long)I.no * I.ns)
        copy(flatD.begin(), flatD.end(), I.D.begin());
    else if (!flatD.empty())
        for (size_t i = 0; i < min(flatD.size(), I.D.size()); i++) I.D[i] = flatD[i];
    I.prof.resize(I.D.size());
    for (int o = 0; o < I.no; o++)
        for (int s = 0; s < I.ns; s++) I.prof[(size_t)o * I.ns + s] = I.reward[s] - I.D[(size_t)o * I.ns + s];
    double mnx = 1e300, mxx = -1e300, mny = 1e300, mxy = -1e300;
    for (auto& q : I.P) { mnx = min(mnx, q.x); mxx = max(mxx, q.x); mny = min(mny, q.y); mxy = max(mxy, q.y); }
    I.ext = I.P.empty() ? 1.0 : max(mxx - mnx, mxy - mny);
    if (!(I.ext > 0)) I.ext = 1.0;
    I.eps_len = 1e-9 * I.ext;
    I.eps_cr = 1e-9 * I.ext * I.ext;
    // кандидаты: офисы по возрастанию расстояния
    I.cand.resize(I.ns);
    {
        vector<int> all(I.no);
        iota(all.begin(), all.end(), 0);
        for (int s = 0; s < I.ns; s++) {
            vector<int> v = all;
            sort(v.begin(), v.end(), [&](int a, int b) { return I.d(a, s) < I.d(b, s); });
            I.cand[s] = move(v);
        }
    }
    return I;
}

// Immutable uniform-grid index of ALL input points, including closed offices/unassigned sites.
// Query is only a broad phase; original predicates remain unchanged.
struct GeoGrid{
 const Inst* inst=nullptr;int side=1;double minx=0,miny=0,sx=1,sy=1;bool enabled=true;
 vector<vector<int>>bucket;vector<int>all;
 int bx(double x)const{double v=(x-minx)*sx;if(v<=0)return 0;if(v>=side)return side-1;return (int)v;}
 int by(double y)const{double v=(y-miny)*sy;if(v<=0)return 0;if(v>=side)return side-1;return (int)v;}
 void init(const Inst&I){inst=&I;enabled=!getenv("GEO_INDEX")||atoi(getenv("GEO_INDEX"));int n=I.P.size();all.resize(n);iota(all.begin(),all.end(),0);side=max(1,min(128,(int)sqrt(max(1,n)/12.)));bucket.assign(side*side,{});if(!n)return;
  minx=miny=1e300;double maxx=-1e300,maxy=-1e300;for(Pt p:I.P){minx=min(minx,p.x);miny=min(miny,p.y);maxx=max(maxx,p.x);maxy=max(maxy,p.y);}sx=side/max(1e-100,maxx-minx);sy=side/max(1e-100,maxy-miny);
  for(int i=0;i<n;i++)bucket[by(I.P[i].y)*side+bx(I.P[i].x)].push_back(i);
 }
 const vector<int>& query(const Inst&I,double x0,double x1,double y0,double y1)const{
  if(!enabled||inst!=&I||side==1)return all;int a=bx(x0),b=bx(x1),c=by(y0),d=by(y1);
  if((b-a+1)*(d-c+1)*2>side*side)return all;
  static thread_local vector<int>v;v.clear();for(int y=c;y<=d;y++)for(int x=a;x<=b;x++)v.insert(v.end(),bucket[y*side+x].begin(),bucket[y*side+x].end());return v;
 }
};
static GeoGrid g_geo_grid;

// sol.h: Sol: решение, нагрузки, навыки инкрементально, цель.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ================================================================== решение
// Bounded fallback for multi-skilled workers. Set once before starting threads.
static double g_wdfs_deadline = 1e100;
static atomic<long> g_wdfs_calls{0}, g_wdfs_success{0}, g_wdfs_nodes{0};

// Инвариант: cov[i] = число открытых офисов, чья оболочка покрывает точку i.
// Допустимо, пока cov[i] <= 1 для всех i.
struct Sol {
    const Inst* I = nullptr;
    vector<char> isopen;
    vector<int> asg, pos, size_;
    vector<long long> load;
    vector<vector<int>> members;
    vector<vector<int>> need;      // [o][k] сколько сайтов офиса требуют навык k
    vector<int> cntSkill;          // сколько офисов требуют навык k
    vector<vector<Pt>> hull;
    vector<vector<int>> covlist;   // точки, покрытые оболочкой o
    vector<char> incov;            // [o*np + i]
    vector<int16_t> cov;
    double psum = 0;
    int np = 0;
    uint64_t sig = 0;              // хэш «какой офис какие навыки требует»
    vector<uint64_t> sigkey;       // [o*nsk+k] и [no*nsk+o] для isopen

    void init(const Inst& In) {
        I = &In;
        np = I->ns + I->no;
        isopen.assign(I->no, 0);
        asg.assign(I->ns, -1);
        pos.assign(I->ns, -1);
        size_.assign(I->no, 0);
        load.assign(I->no, 0);
        members.assign(I->no, {});
        need.assign(I->no, vector<int>(I->nsk, 0));
        cntSkill.assign(I->nsk, 0);
        hull.assign(I->no, {});
        covlist.assign(I->no, {});
        incov.assign((size_t)I->no * np, 0);
        cov.assign(np, 0);
        psum = 0;
        sigkey.resize((size_t)I->no * I->nsk + I->no);
        mt19937_64 r(0xC0FFEE123ULL);
        for (auto& v : sigkey) v = r();
        sig = 0;
    }
    inline void sig_need(int o, int k) { sig ^= sigkey[(size_t)o * I->nsk + k]; }
    inline void sig_open(int o) { sig ^= sigkey[(size_t)I->no * I->nsk + o]; }

    // --- геометрия
    void clear_cov(int o) {
        char* row = &incov[(size_t)o * np];
        for (int i : covlist[o]) { row[i] = 0; cov[i]--; }
        covlist[o].clear();
    }
    void legacy_apply_cov(int o, const vector<Pt>& h) {
        char* row = &incov[(size_t)o * np];
        const auto& P = I->P;
        int n = np;
        if (h.empty()) return;
        if (h.size() == 1) {
            for (int i : g_geo_grid.query(*I,h[0].x-I->eps_len,h[0].x+I->eps_len,h[0].y-I->eps_len,h[0].y+I->eps_len))
                if (fabs(P[i].x - h[0].x) <= I->eps_len && fabs(P[i].y - h[0].y) <= I->eps_len) {
                    row[i] = 1; cov[i]++; covlist[o].push_back(i);
                }
            return;
        }
        if (h.size() == 2) {
            double ax = h[0].x, ay = h[0].y, dx = h[1].x - ax, dy = h[1].y - ay;
            double L2 = dx * dx + dy * dy, L = sqrt(L2);
            double pad=2*I->eps_len+I->eps_cr/max(L,1e-300);
            for (int i : g_geo_grid.query(*I,min(ax,ax+dx)-pad,max(ax,ax+dx)+pad,min(ay,ay+dy)-pad,max(ay,ay+dy)+pad)) {
                double X = P[i].x - ax, Y = P[i].y - ay;
                double c = dx * Y - dy * X, t = dx * X + dy * Y;
                if (fabs(c) <= I->eps_cr + I->eps_len * L && t >= -I->eps_len * L && t <= L2 + I->eps_len * L) {
                    row[i] = 1; cov[i]++; covlist[o].push_back(i);
                }
            }
            return;
        }
        size_t m = h.size();
        double mnx = 1e300, mxx = -1e300, mny = 1e300, mxy = -1e300;
        for (auto& q : h) { mnx = min(mnx, q.x); mxx = max(mxx, q.x); mny = min(mny, q.y); mxy = max(mxy, q.y); }
        mnx -= I->eps_len; mxx += I->eps_len; mny -= I->eps_len; mxy += I->eps_len;
        for (int i : g_geo_grid.query(*I,mnx,mxx,mny,mxy)) {
            double X = P[i].x, Y = P[i].y;
            if (X < mnx || X > mxx || Y < mny || Y > mxy) continue;
            bool in = true;
            for (size_t e2 = 0; e2 < m && in; e2++) {
                const Pt& a = h[e2];
                const Pt& b = h[(e2 + 1) % m];
                double ex = b.x - a.x, ey = b.y - a.y;
                double tol = -I->eps_cr - I->eps_len * sqrt(ex * ex + ey * ey);
                in = ex * (Y - a.y) - ey * (X - a.x) >= tol;
            }
            if (in) { row[i] = 1; cov[i]++; covlist[o].push_back(i); }
        }
    }
    void set_hull(int o, const vector<Pt>& h) {
        clear_cov(o);
        hull[o] = h;
        apply_cov(o, hull[o]);
    }
    void rebuild_hull(int o) {
        static thread_local vector<Pt> pts;
        pts.clear(); pts.reserve(members[o].size() + 1);
        for (int s : members[o]) pts.push_back(I->P[s]);
        if (isopen[o]) pts.push_back(I->P[I->ns + o]);
        hull_of(pts);
        set_hull(o, move(pts));
    }
    // можно ли добавить сайт s в офис o по геометрии; newh — новая оболочка (пусто = без изменений)
    bool legacy_geo_ok(int s, int o, vector<Pt>& newh) const {
        newh.clear();
        if (incov[(size_t)o * np + s]) return true;
        auto& pts = newh;
        pts.assign(hull[o].begin(), hull[o].end());
        pts.push_back(I->P[s]);
        hull_of(pts);
        // проверяем точки, которые станут покрытыми
        const auto& P = I->P;
        const char* row = &incov[(size_t)o * np];
        size_t m = pts.size();
        if (m >= 3) {
            double mnx = 1e300, mxx = -1e300, mny = 1e300, mxy = -1e300;
            for (auto& q : pts) { mnx = min(mnx, q.x); mxx = max(mxx, q.x); mny = min(mny, q.y); mxy = max(mxy, q.y); }
            mnx -= I->eps_len; mxx += I->eps_len; mny -= I->eps_len; mxy += I->eps_len;
            for (int i : g_geo_grid.query(*I,mnx,mxx,mny,mxy)) {
                if (row[i] || cov[i] == 0) continue;
                double X = P[i].x, Y = P[i].y;
                if (X < mnx || X > mxx || Y < mny || Y > mxy) continue;
                bool in = true;
                for (size_t e2 = 0; e2 < m && in; e2++) {
                    const Pt& a = pts[e2];
                    const Pt& b = pts[(e2 + 1) % m];
                    double ex = b.x - a.x, ey = b.y - a.y;
                    double tol = -I->eps_cr - I->eps_len * sqrt(ex * ex + ey * ey);
                    in = ex * (Y - a.y) - ey * (X - a.x) >= tol;
                }
                if (in) return false;
            }
        } else if (m == 2) {
            double ax = pts[0].x, ay = pts[0].y, dx = pts[1].x - ax, dy = pts[1].y - ay;
            double L2 = dx * dx + dy * dy, L = sqrt(L2);
            double pad=2*I->eps_len+I->eps_cr/max(L,1e-300);
            for (int i : g_geo_grid.query(*I,min(ax,ax+dx)-pad,max(ax,ax+dx)+pad,min(ay,ay+dy)-pad,max(ay,ay+dy)+pad)) {
                if (row[i] || cov[i] == 0) continue;
                double X = P[i].x - ax, Y = P[i].y - ay;
                double c = dx * Y - dy * X, t = dx * X + dy * Y;
                if (fabs(c) <= I->eps_cr + I->eps_len * L && t >= -I->eps_len * L && t <= L2 + I->eps_len * L) return false;
            }
        }
        return true;
    }

    void apply_cov(int o,const vector<Pt>&h){
        if(!g_geo_exact){legacy_apply_cov(o,h);return;}if(h.empty())return;
        double x0=1e300,x1=-1e300,y0=1e300,y1=-1e300;for(Pt p:h){x0=min(x0,p.x);x1=max(x1,p.x);y0=min(y0,p.y);y1=max(y1,p.y);}
        char*row=&incov[(size_t)o*np];for(int i:g_geo_grid.query(*I,x0,x1,y0,y1))if(geo_exact_covers(h,I->P[i])){row[i]=1;cov[i]++;covlist[o].push_back(i);}
    }
    bool geo_ok(int x,int o,vector<Pt>&newh)const{
        if(!g_geo_exact)return legacy_geo_ok(x,o,newh);newh.clear();const char*row=&incov[(size_t)o*np];if(row[x])return true;
        newh=hull[o];newh.push_back(I->P[x]);hull_of(newh);
        double x0=1e300,x1=-1e300,y0=1e300,y1=-1e300;for(Pt p:newh){x0=min(x0,p.x);x1=max(x1,p.x);y0=min(y0,p.y);y1=max(y1,p.y);}
        for(int i:g_geo_grid.query(*I,x0,x1,y0,y1))if(!row[i]&&cov[i]&&geo_exact_covers(newh,I->P[i]))return false;return true;
    }

    // --- навыки
    bool skills_ok() const {
        for (int k = 0; k < I->nsk; k++) if (cntSkill[k] > I->Nk[k]) return false;
        if (I->simple_workers) return true;
        return greedy_workers(nullptr);
    }
    // жадное назначение рабочих; если out != null — записать wof
    bool legacy_workers(vector<int>* out) const {
        struct Scratch { vector<int> wof; vector<char> used, have; };
        static thread_local Scratch ws;
        auto& wof=ws.wof; auto& used=ws.used; auto& have=ws.have;
        wof.assign(I->nw,-1);used.assign(I->nw,0);
        for (int o = 0; o < I->no; o++) {
            if (!isopen[o] || size_[o] == 0) continue;
            have.assign(I->nsk, 0);
            for (int k = 0; k < I->nsk; k++) {
                if (need[o][k] == 0 || have[k]) continue;
                // выбираем рабочего, закрывающего больше всего недостающих навыков
                int bw = -1, bg = -1;
                for (int w = 0; w < I->nw; w++) {
                    if (used[w] || !I->wmask[w][k]) continue;
                    int g = 0;
                    for (int k2 = 0; k2 < I->nsk; k2++) if (need[o][k2] > 0 && !have[k2] && I->wmask[w][k2]) g++;
                    if (g > bg) { bg = g; bw = w; }
                }
                if (bw < 0) return false;
                used[bw] = 1; wof[bw] = o;
                for (int k2 = 0; k2 < I->nsk; k2++) have[k2] |= I->wmask[bw][k2];
            }
        }
        if (out) *out = wof;
        return true;
    }

    bool greedy_workers(vector<int>* out) const {
        if (legacy_workers(out)) return true;
        static const bool enabled = !getenv("WORKER_DFS") || atoi(getenv("WORKER_DFS")) > 0;
        if (!enabled || elapsed() >= g_wdfs_deadline) return false;
        g_wdfs_calls.fetch_add(1, memory_order_relaxed);
        struct Frame {
            vector<int> available, demand;
            vector<pair<int,int>> choices;
            vector<char> old;
        };
        struct Scratch {
            vector<char> used, have, required;
            vector<int> wof;
            // Heap-owned frames stay valid when a deeper call grows the index.
            vector<unique_ptr<Frame>> frames;
        };
        static thread_local Scratch ws;
        auto& used=ws.used;auto& have=ws.have;auto& required=ws.required;auto& wof=ws.wof;
        used.assign(I->nw,0);have.assign((size_t)I->no*I->nsk,0);
        required.assign(have.size(),0);wof.assign(I->nw,-1);
        for (int o = 0; o < I->no; o++) if (isopen[o] && size_[o] > 0)
            for (int k = 0; k < I->nsk; k++) required[(size_t)o * I->nsk + k] = need[o][k] > 0;
        int nodes = 0, budget = (int)max(64LL, min(4096LL, 4LL * I->nw * max(1, I->no)));
        auto dfs = [&](auto&& self, size_t depth) -> bool {
            if (++nodes > budget || ((nodes & 31) == 0 && elapsed() >= g_wdfs_deadline)) return false;
            if(depth==ws.frames.size())ws.frames.emplace_back(new Frame);
            auto& frame=*ws.frames[depth];
            auto& available=frame.available;auto& demand=frame.demand;
            available.assign(I->nsk,0);demand.assign(I->nsk,0);
            for (int w = 0; w < I->nw; w++) if (!used[w])
                for (int k = 0; k < I->nsk; k++) available[k] += I->wmask[w][k] != 0;
            int bo = -1, bk = -1, bn = INT_MAX, bt = -1;
            for (int o = 0; o < I->no; o++) {
                int count = 0;
                for (int k = 0; k < I->nsk; k++)
                    if (required[(size_t)o * I->nsk + k] && !have[(size_t)o * I->nsk + k]) count++;
                for (int k = 0; k < I->nsk; k++)
                    if (required[(size_t)o * I->nsk + k] && !have[(size_t)o * I->nsk + k]) {
                        demand[k]++;
                        if (available[k] < bn || (available[k] == bn && count > bt)) {
                            bo = o; bk = k; bn = available[k]; bt = count;
                        }
                    }
            }
            if (bo < 0) return true;
            for (int k = 0; k < I->nsk; k++) if (demand[k] > available[k]) return false;
            auto& choices=frame.choices;choices.clear();
            for (int w = 0; w < I->nw; w++) if (!used[w] && I->wmask[w][bk]) {
                bool duplicate = false;
                for (auto e : choices) if (I->wmask[e.second] == I->wmask[w]) { duplicate = true; break; }
                if (duplicate) continue;
                int gain = 0, harm = 0;
                for (int k = 0; k < I->nsk; k++) if (I->wmask[w][k]) {
                    bool own = required[(size_t)bo * I->nsk + k] && !have[(size_t)bo * I->nsk + k];
                    gain += own;
                    harm += (demand[k] - (own ? 1 : 0)) * 100 / max(1, available[k]);
                }
                choices.push_back({gain * 1000 - harm, w});
            }
            sort(choices.rbegin(), choices.rend());
            auto& old=frame.old;old.assign(have.begin() + (size_t)bo * I->nsk, have.begin() + (size_t)(bo + 1) * I->nsk);
            for (auto e : choices) {
                int w = e.second; used[w] = 1; wof[w] = bo;
                for (int k = 0; k < I->nsk; k++) have[(size_t)bo * I->nsk + k] |= I->wmask[w][k];
                if (self(self,depth+1)) return true;
                copy(old.begin(), old.end(), have.begin() + (size_t)bo * I->nsk);
                used[w] = 0; wof[w] = -1;
            }
            return false;
        };
        bool ok = dfs(dfs,0);
        g_wdfs_nodes.fetch_add(nodes, memory_order_relaxed);
        if (ok) {
            g_wdfs_success.fetch_add(1, memory_order_relaxed);
            if (out) *out = wof;
        }
        return ok;
    }

    // --- ходы
    void open_office(int o) {
        if (isopen[o]) return;
        isopen[o] = 1;
        sig_open(o);
        rebuild_hull(o);
    }
    void close_office(int o) {
        if (!isopen[o]) return;
        while (!members[o].empty()) remove_site(members[o].back());
        isopen[o] = 0;
        clear_cov(o);
        hull[o].clear();
    }
    void remove_site(int s) {
        int o = asg[s];
        if (o < 0) return;
        asg[s] = -1;
        int p = pos[s], last = members[o].back();
        members[o][p] = last; pos[last] = p; members[o].pop_back(); pos[s] = -1;
        size_[o]--; load[o] -= I->ntask[s]; psum -= I->pr(o, s);
        for (int k : I->skillset[s]) if (--need[o][k] == 0) { cntSkill[k]--; sig_need(o, k); }
        bool onhull = false;
        for (auto& q : hull[o]) if (pteq(q, I->P[s])) { onhull = true; break; }
        if (onhull) rebuild_hull(o);
    }
    void add_site_raw(int s, int o, vector<Pt>& newh) {
        asg[s] = o;
        pos[s] = members[o].size();
        members[o].push_back(s);
        size_[o]++; load[o] += I->ntask[s]; psum += I->pr(o, s);
        for (int k : I->skillset[s]) if (need[o][k]++ == 0) { cntSkill[k]++; sig_need(o, k); }
        if (!newh.empty()) set_hull(o, move(newh));
    }
    void force_add(int s, int o) {  // без проверок (откат)
        asg[s] = o;
        pos[s] = members[o].size();
        members[o].push_back(s);
        size_[o]++; load[o] += I->ntask[s]; psum += I->pr(o, s);
        for (int k : I->skillset[s]) if (need[o][k]++ == 0) { cntSkill[k]++; sig_need(o, k); }
        rebuild_hull(o);
    }

    bool size_ok_after(int oadd, int orem) const {
        int mx = INT_MIN, mn = INT_MAX;
        for (int o = 0; o < I->no; o++) {
            if (!isopen[o]) continue;
            int sz = size_[o] + (o == oadd ? 1 : 0) - (o == orem ? 1 : 0);
            if (sz == 0) continue;
            if (sz > I->maxsize[o]) return false;
            mx = max(mx, sz); mn = min(mn, sz);
        }
        return mx < mn || (long long)(mx - mn) <= I->A;
    }

    // --- целевая
    double objective() const {
        double c = 0, p = 0;
        long long mx = LLONG_MIN, mn = LLONG_MAX;
        for (int o = 0; o < I->no; o++) {
            if (!isopen[o] || size_[o] == 0) continue;
            c += I->cost[o];
            for (int s : members[o]) p += I->pr(o, s);
            mx = max(mx, load[o]); mn = min(mn, load[o]);
        }
        if (mx == LLONG_MIN) return 0.0;
        return p - c - I->alpha * (double)(mx - mn);
    }
    // быстрая версия через psum (может чуть плыть, пересчитываем в offer)
    double objective_fast() const {
        double c = 0;
        long long mx = LLONG_MIN, mn = LLONG_MAX;
        for (int o = 0; o < I->no; o++) {
            if (!isopen[o] || size_[o] == 0) continue;
            c += I->cost[o];
            mx = max(mx, load[o]); mn = min(mn, load[o]);
        }
        if (mx == LLONG_MIN) return 0.0;
        return psum - c - I->alpha * (double)(mx - mn);
    }
    double tail(const vector<int>& sz, const vector<long long>& ld) const {
        double c = 0;
        long long mx = LLONG_MIN, mn = LLONG_MAX;
        for (int o = 0; o < I->no; o++) {
            if (!isopen[o] || sz[o] == 0) continue;
            c += I->cost[o];
            mx = max(mx, ld[o]); mn = min(mn, ld[o]);
        }
        if (mx == LLONG_MIN) return 0.0;
        return -c - I->alpha * (double)(mx - mn);
    }

    void recompute_psum() {
        double p = 0;
        for (int o = 0; o < I->no; o++) if (isopen[o]) for (int x : members[o]) p += I->pr(o, x);
        psum = p;
    }
    vector<int> state() const { return asg; }
    void load_state(const vector<int>& st, const vector<char>& op) {
        // полная пересборка
        for (int o = 0; o < I->no; o++) {
            members[o].clear(); size_[o] = 0; load[o] = 0;
            fill(need[o].begin(), need[o].end(), 0);
        }
        fill(cntSkill.begin(), cntSkill.end(), 0);
        fill(pos.begin(), pos.end(), -1);
        psum = 0;
        isopen = op;
        for (int s = 0; s < I->ns; s++) {
            int o = st[s];
            asg[s] = o;
            if (o < 0) continue;
            pos[s] = members[o].size();
            members[o].push_back(s);
            size_[o]++; load[o] += I->ntask[s]; psum += I->pr(o, s);
            for (int k : I->skillset[s]) if (need[o][k]++ == 0) cntSkill[k]++;
        }
        sig = 0;
        for (int o = 0; o < I->no; o++) {
            if (isopen[o]) sig_open(o);
            for (int k = 0; k < I->nsk; k++) if (need[o][k] > 0) sig_need(o, k);
        }
        for (int o = 0; o < I->no; o++) {
            if (isopen[o]) rebuild_hull(o);
            else { clear_cov(o); hull[o].clear(); }
        }
    }
};

// check.h: полная проверка валидности (как validate_solution.py).
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ======================================================= проверка валидности
// Полная проверка «как в валидаторе» (консервативная по eps).
static bool verify(const Inst& I, const vector<int>& asg, const vector<char>& isopen,
                   const vector<int>& wof, double* obj) {
    int np = I.ns + I.no;
    vector<int> sz(I.no, 0);
    vector<long long> ld(I.no, 0);
    vector<vector<int>> mem(I.no);
    for (int s = 0; s < I.ns; s++) {
        int o = asg[s];
        if (o < 0) continue;
        if (o >= I.no || !isopen[o]) return false;
        mem[o].push_back(s); sz[o]++; ld[o] += I.ntask[s];
    }
    // ёмкость и баланс
    int mx = INT_MIN, mn = INT_MAX;
    for (int o = 0; o < I.no; o++) {
        if (!isopen[o] || sz[o] == 0) continue;
        if (sz[o] > I.maxsize[o]) return false;
        mx = max(mx, sz[o]); mn = min(mn, sz[o]);
    }
    if (mx != INT_MIN && (long long)(mx - mn) > I.A) return false;
    // навыки
    for (int w = 0; w < I.nw; w++) if (wof[w] >= 0 && (wof[w] >= I.no || !isopen[wof[w]] || sz[wof[w]] == 0)) return false;
    for (int o = 0; o < I.no; o++) {
        if (!isopen[o] || sz[o] == 0) continue;
        vector<char> have(I.nsk, 0);
        for (int w = 0; w < I.nw; w++) if (wof[w] == o) for (int k = 0; k < I.nsk; k++) have[k] |= I.wmask[w][k];
        for (int s : mem[o]) for (int k : I.skillset[s]) if (!have[k]) return false;
    }
    // геометрия
    vector<int> cnt(np, 0);
    for (int o = 0; o < I.no; o++) {
        if (!isopen[o] || sz[o] == 0) continue;
        vector<Pt> h;
        for (int s : mem[o]) h.push_back(I.P[s]);
        h.push_back(I.P[I.ns + o]);
        hull_of(h);
        size_t m = h.size();
        for (int i = 0; i < np; i++) {
            bool in;
            if(g_geo_exact)in=geo_exact_covers(h,I.P[i]);
            else if (m == 1) in = fabs(I.P[i].x - h[0].x) <= I.eps_len && fabs(I.P[i].y - h[0].y) <= I.eps_len;
            else if (m == 2) {
                double ax = h[0].x, ay = h[0].y, dx = h[1].x - ax, dy = h[1].y - ay;
                double L2 = dx * dx + dy * dy, L = sqrt(L2);
                double X = I.P[i].x - ax, Y = I.P[i].y - ay;
                double c = dx * Y - dy * X, t = dx * X + dy * Y;
                in = fabs(c) <= I.eps_cr + I.eps_len * L && t >= -I.eps_len * L && t <= L2 + I.eps_len * L;
            } else {
                in = true;
                for (size_t e2 = 0; e2 < m && in; e2++) {
                    const Pt& a = h[e2];
                    const Pt& b = h[(e2 + 1) % m];
                    double ex = b.x - a.x, ey = b.y - a.y;
                    double tol = -I.eps_cr - I.eps_len * sqrt(ex * ex + ey * ey);
                    in = ex * (I.P[i].y - a.y) - ey * (I.P[i].x - a.x) >= tol;
                }
            }
            if (in && ++cnt[i] > 1) return false;
        }
    }
    double p = 0, c = 0;
    long long Lmx = LLONG_MIN, Lmn = LLONG_MAX;
    for (int o = 0; o < I.no; o++) {
        if (!isopen[o] || sz[o] == 0) continue;
        c += I.cost[o];
        for (int s : mem[o]) p += I.pr(o, s);
        Lmx = max(Lmx, ld[o]); Lmn = min(Lmn, ld[o]);
    }
    *obj = Lmx == LLONG_MIN ? 0.0 : p - c - I.alpha * (double)(Lmx - Lmn);
    return true;
}

// output.h: вывод (запись одним write, сигналы), глобальное лучшее решение, пул элитных решений.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ========================================================== вывод (robust)
// Пред-сериализованный буфер + обработчик сигналов: даже убитый по таймеру
// процесс оставляет на диске валидный JSON.
static int g_fd = -1;
static string g_buf[2];
static atomic<int> g_idx{-1};
static atomic<bool> g_writing{false};

static size_t g_lastlen = 0;
static void raw_write(int which, bool sync) {
    if (g_fd < 0 || which < 0) return;
    const string& b = g_buf[which];
    if (lseek(g_fd, 0, SEEK_SET) < 0) return;
    size_t off = 0;
    while (off < b.size()) {
        ssize_t n = write(g_fd, b.data() + off, b.size() - off);
        if (n <= 0) break;
        off += n;
    }
    if (ftruncate(g_fd, off) != 0) { /* ignore */ }
    g_lastlen = off;
    if (sync) fsync(g_fd);
}
static void on_signal(int) {
    raw_write(g_idx.load(memory_order_acquire), true);
    _exit(0);
}
static mutex g_outmx;
static void publish(const string& text) {
    lock_guard<mutex> lk(g_outmx);
    int cur = g_idx.load(memory_order_relaxed);
    int nxt = cur == 0 ? 1 : 0;
    g_buf[nxt] = text;
    if (g_buf[nxt].size() < g_lastlen) g_buf[nxt].append(g_lastlen - g_buf[nxt].size(), ' ');
    g_idx.store(nxt, memory_order_release);
    raw_write(nxt, false);
}

static string serialize(const Inst& I, const vector<int>& asg, const vector<char>& isopen, const vector<int>& wof) {
    vector<vector<int>> mem(I.no);
    for (int s = 0; s < I.ns; s++) if (asg[s] >= 0) mem[asg[s]].push_back(s);
    string out = "[";
    bool first = true;
    char tmp[32];
    for (int o = 0; o < I.no; o++) {
        if (!isopen[o] || mem[o].empty()) continue;
        if (!first) out += ',';
        first = false;
        out += "{\"officeId\":";
        snprintf(tmp, sizeof tmp, "%d", o); out += tmp;
        out += ",\"sites\":[";
        sort(mem[o].begin(), mem[o].end());
        for (size_t i = 0; i < mem[o].size(); i++) {
            if (i) out += ',';
            snprintf(tmp, sizeof tmp, "%d", mem[o][i]); out += tmp;
        }
        out += "],\"workers\":[";
        bool fw = true;
        for (int w = 0; w < I.nw; w++) if (wof[w] == o) {
            if (!fw) out += ',';
            fw = false;
            snprintf(tmp, sizeof tmp, "%d", w); out += tmp;
        }
        out += "]}";
    }
    out += "]\n";
    return out;
}

// глобально лучшее
static mutex g_best_mx;
static atomic<double> g_best{0.0};
static vector<int> g_best_asg;
static vector<char> g_best_open;

struct Elite { double f; vector<int> asg; vector<char> open; };
static mutex g_el_mx;
static vector<Elite> g_elite;

static void push_elite(double f, const vector<int>& asg, const vector<char>& op) {
    lock_guard<mutex> lk(g_el_mx);
    for (auto& e : g_elite) if (fabs(e.f - f) <= 1e-9 * max(1.0, fabs(f))) return;
    g_elite.push_back({f, asg, op});
    sort(g_elite.begin(), g_elite.end(), [](const Elite& a, const Elite& b) { return a.f > b.f; });
    if (g_elite.size() > 6) g_elite.resize(6);
}
// выбрать элитное решение (с уклоном в лучшие); false, если пул пуст
static bool pick_elite(mt19937_64& rng, vector<int>& asg, vector<char>& op) {
    lock_guard<mutex> lk(g_el_mx);
    if (g_elite.empty()) return false;
    size_t i = 0;
    while (i + 1 < g_elite.size() && (rng() & 1)) i++;
    asg = g_elite[i].asg;
    op = g_elite[i].open;
    return true;
}

static bool offer(const Inst& I, Sol& s) {
    double f = s.objective();
    {
        lock_guard<mutex> lk(g_best_mx);
        if (f <= g_best.load(memory_order_relaxed) + 1e-9) return false;
    }
    vector<int> wof;
    if (!s.greedy_workers(&wof)) return false;
    double obj = 0;
    if (!verify(I, s.asg, s.isopen, wof, &obj)) return false;
    lock_guard<mutex> lk(g_best_mx);
    if (obj <= g_best.load(memory_order_relaxed) + 1e-9) return false;
    g_best.store(obj, memory_order_relaxed);
    g_best_asg = s.asg;
    g_best_open = s.isopen;
    publish(serialize(I, s.asg, s.isopen, wof));
    push_elite(obj, s.asg, s.isopen);
    return true;
}

// добавить решение в элиту, если оно близко к лучшему (с полной проверкой)
static void try_elite(const Inst& I, Sol& s) {
    double f = s.objective();
    double b = g_best.load(memory_order_relaxed);
    if (f <= 0 || f < b * (b > 0 ? 0.96 : 1.04)) return;
    vector<int> wof;
    double obj = 0;
    if (!s.greedy_workers(&wof)) return;
    if (!verify(I, s.asg, s.isopen, wof, &obj)) return;
    push_elite(obj, s.asg, s.isopen);
}

// dp.h: точный выбор подмножества сайтов при фиксированных зонах (DP).
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ============================================ точный выбор подмножества (DP)
// При фиксированных зонах удаление сайтов не ломает геометрию (оболочка только
// сжимается) и не ломает навыки. Значит «какие сайты оставить» решается точно:
// 0/1-рюкзак по числу задач внутри офиса + перебор окна нагрузки [lo,hi].
struct DPResult { bool ok = false; };

static bool resize_dp(Sol& s, double deadline, bool allow_close = true) {
    const Inst& I = *s.I;
    if (I.alpha <= 0) {
        // без штрафа за баланс: просто снять все убыточные сайты
        bool ch = false;
        for (int o = 0; o < I.no; o++) {
            if (!s.isopen[o]) continue;
            vector<int> mem = s.members[o];
            for (int x : mem) if (I.pr(o, x) < 0) { s.remove_site(x); ch = true; }
        }
        return ch;
    }
    vector<int> ops;
    for (int o = 0; o < I.no; o++) if (s.isopen[o] && s.size_[o] > 0) ops.push_back(o);
    if (ops.size() <= 1) {
        bool ch = false;
        for (int o : ops) {
            vector<int> mem = s.members[o];
            for (int x : mem) if (I.pr(o, x) < 0) { s.remove_site(x); ch = true; }
        }
        return ch;
    }
    int K = ops.size();
    // бюджет на DP
    long long budget = 0;
    vector<int> Wo(K, 0);
    for (int b = 0; b < K; b++) {
        int o = ops[b];
        for (int x : s.members[o]) Wo[b] += I.ntask[x];
        budget += (long long)s.members[o].size() * (Wo[b] + 1);
    }
    if (budget > 200000000LL) return false;
    int Wmax = *max_element(Wo.begin(), Wo.end());
    if (Wmax <= 0) return false;

    vector<vector<double>> f(K);
    vector<vector<uint64_t>> choice(K);
    vector<vector<int>> items(K);
    vector<double> const0(K, 0.0);
    for (int b = 0; b < K; b++) {
        int o = ops[b];
        int W = Wo[b];
        auto& fo = f[b];
        fo.assign(W + 1, NEG);
        fo[0] = 0;
        vector<int>& it = items[b];
        for (int x : s.members[o]) {
            if (I.ntask[x] == 0) { if (I.pr(o, x) > 0) const0[b] += I.pr(o, x); }
            else it.push_back(x);
        }
        size_t words = (size_t)(W + 1 + 63) / 64;
        choice[b].assign(it.size() * words, 0ULL);
        for (size_t i = 0; i < it.size(); i++) {
            int x = it[i];
            int w = I.ntask[x];
            double p = I.pr(o, x);
            uint64_t* row = &choice[b][i * words];
            for (int l = W; l >= w; l--) {
                double v = fo[l - w];
                if (v <= NEG / 2) continue;
                if (v + p > fo[l] + 1e-12) { fo[l] = v + p; row[l >> 6] |= 1ULL << (l & 63); }
            }
        }
        for (int l = 0; l <= W; l++) if (fo[l] > NEG / 2) fo[l] += const0[b];
        if (elapsed() > deadline) return false;
    }
    // сетка значений окна
    vector<int> grid;
    if (Wmax <= 2500) { grid.resize(Wmax + 1); iota(grid.begin(), grid.end(), 0); }
    else {
        set<int> g;
        for (int i = 0; i <= 600; i++) g.insert((int)((long long)Wmax * i / 600));
        for (int b = 0; b < K; b++) g.insert((int)s.load[ops[b]]);
        grid.assign(g.begin(), g.end());
    }
    int G = grid.size();
    // blk[b][j] = max f_b[l] для l из (grid[j-1], grid[j]]
    vector<vector<double>> blk(K, vector<double>(G, NEG));
    vector<vector<double>> at(K, vector<double>(G, NEG));
    for (int b = 0; b < K; b++) {
        int W = Wo[b];
        for (int j = 0; j < G; j++) {
            int hi = min(grid[j], W);
            int lo = j == 0 ? 0 : min(grid[j - 1] + 1, W + 1);
            double m = NEG;
            for (int l = lo; l <= hi; l++) m = max(m, f[b][l]);
            blk[b][j] = m;
            at[b][j] = grid[j] <= W ? f[b][grid[j]] : NEG;
        }
    }
    double bestScore = 0.0;  // вариант «все закрыты»
    int bi = -1, bj = -1;
    vector<double> run(K);
    for (int i = 0; i < G; i++) {
        if ((i & 31) == 0 && elapsed() > deadline) break;
        for (int b = 0; b < K; b++) run[b] = at[b][i];
        for (int j = i; j < G; j++) {
            if (j > i) for (int b = 0; b < K; b++) run[b] = max(run[b], blk[b][j]);
            double tot = 0;
            bool anyopen = false, bad = false;
            for (int b = 0; b < K; b++) {
                double v = run[b] > NEG / 2 ? run[b] - I.cost[ops[b]] : NEG;
                if (!allow_close) {
                    if (v <= NEG / 2) { bad = true; break; }
                    tot += v; anyopen = true;
                } else if (v > 0) { tot += v; anyopen = true; }
            }
            if (bad || !anyopen) continue;
            double sc = tot - I.alpha * (double)(grid[j] - grid[i]);
            if (sc > bestScore + 1e-9) { bestScore = sc; bi = i; bj = j; }
        }
    }
    if (bi < 0) return false;
    int lo = grid[bi], hi = grid[bj];
    bool changed = false;
    for (int b = 0; b < K; b++) {
        int o = ops[b], W = Wo[b];
        int lstar = -1;
        double bv = NEG;
        for (int l = max(0, lo); l <= min(hi, W); l++) if (f[b][l] > bv) { bv = f[b][l]; lstar = l; }
        if (lstar < 0 || bv <= NEG / 2 || (allow_close && bv - I.cost[o] <= 0)) {
            if (allow_close) {
                if (!s.members[o].empty()) { s.close_office(o); changed = true; }
                continue;
            }
            if (lstar < 0 || bv <= NEG / 2) continue;
        }
        // восстановление выбора
        vector<char> keep(I.ns, 0);
        for (int x : s.members[o]) if (I.ntask[x] == 0 && I.pr(o, x) > 0) keep[x] = 1;
        size_t words = (size_t)(W + 1 + 63) / 64;
        int l = lstar;
        for (int i = (int)items[b].size() - 1; i >= 0; i--) {
            int x = items[b][i];
            int w = I.ntask[x];
            if (l - w < 0) continue;
            const uint64_t* row = &choice[b][(size_t)i * words];
            if (row[l >> 6] >> (l & 63) & 1ULL) { keep[x] = 1; l -= w; }
        }
        vector<int> mem = s.members[o];
        for (int x : mem) if (!keep[x]) { s.remove_site(x); changed = true; }
    }
    return changed;
}

// снимаем наименее выгодные сайты, пока не выполнены maxSize и баланс A
static void repair_sizes(Sol& s) {
    const Inst& I = *s.I;
    for (int guard = 0; guard < I.ns + 10; guard++) {
        int mx = INT_MIN, mn = INT_MAX, omx = -1, over = -1;
        for (int o = 0; o < I.no; o++) {
            if (!s.isopen[o] || s.size_[o] == 0) continue;
            if (s.size_[o] > I.maxsize[o]) over = o;
            if (s.size_[o] > mx) { mx = s.size_[o]; omx = o; }
            mn = min(mn, s.size_[o]);
        }
        if (mx == INT_MIN) return;
        int pick = over >= 0 ? over : ((long long)(mx - mn) > I.A ? omx : -1);
        if (pick < 0) return;
        int worst = -1;
        for (int x : s.members[pick])
            if (worst < 0 || I.pr(pick, x) < I.pr(pick, worst)) worst = x;
        if (worst < 0) return;
        s.remove_site(worst);
    }
}

// fast.h: быстрая оценка набора офисов через power diagram.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// =================================================== быстрая оценка офисов
// Power diagram: ячейки выпуклы и не пересекаются, поэтому разбиение заведомо
// геометрически допустимо. Используется для выбора множества офисов.
struct Fast {
    const Inst& I;
    vector<int> skills, wcnt;
    vector<vector<char>> req;
    double scale2 = 1;

    explicit Fast(const Inst& In) : I(In) {
        set<int> u;
        for (auto& ss : I.skillset) for (int k : ss) u.insert(k);
        skills.assign(u.begin(), u.end());
        for (int k : skills) wcnt.push_back(I.Nk[k]);
        req.assign(I.ns, vector<char>(skills.size(), 0));
        for (int s = 0; s < I.ns; s++)
            for (int k : I.skillset[s])
                req[s][lower_bound(skills.begin(), skills.end(), k) - skills.begin()] = 1;
        vector<double> mins;
        for (int s = 0; s < I.ns; s++) {
            double m = 1e300;
            for (int o = 0; o < I.no; o++) {
                const Pt& a = I.P[s];
                const Pt& b = I.P[I.ns + o];
                m = min(m, (a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
            }
            mins.push_back(m);
        }
        if (!mins.empty()) {
            nth_element(mins.begin(), mins.begin() + mins.size() / 2, mins.end());
            scale2 = mins[mins.size() / 2] + 1e-12;
        }
    }

    void cells(const vector<int>& op, const vector<double>& h, const vector<Pt>& G, vector<int>& c) const {
        int K = op.size();
        c.assign(I.ns, 0);
        for (int s = 0; s < I.ns; s++) {
            const Pt& p = I.P[s];
            int arg = 0; double best = 1e300;
            for (int b = 0; b < K; b++) {
                const Pt& g = G[op[b]];
                double v = (p.x - g.x) * (p.x - g.x) + (p.y - g.y) * (p.y - g.y) - h[op[b]];
                if (v < best) { best = v; arg = b; }
            }
            c[s] = arg;
        }
    }
    bool offices_in_own_cell(const vector<int>& op, const vector<double>& h, const vector<Pt>& G) const {
        int K = op.size();
        for (int a = 0; a < K; a++) {
            const Pt& p = I.P[I.ns + op[a]];
            int arg = 0; double best = 1e300;
            for (int b = 0; b < K; b++) {
                const Pt& g = G[op[b]];
                double v = (p.x - g.x) * (p.x - g.x) + (p.y - g.y) * (p.y - g.y) - h[op[b]];
                if (v < best) { best = v; arg = b; }
            }
            if (arg != a) return false;
        }
        return true;
    }

    double evaluate(const vector<int>& op, const vector<double>& h, const vector<Pt>& G,
                    vector<vector<int>>* out = nullptr) const {
        int K = op.size();
        if (!K) return 0.0;
        if (!offices_in_own_cell(op, h, G)) return NEG;
        // Reused per thread: evaluate is called thousands of times per start.
        struct Scratch {
            vector<int> c, idx, bestcut, cut;
            vector<double> prof, val, L, levels;
            vector<char> ok, allow;
            vector<vector<int>> mem, rm;
            vector<vector<double>> ct, cp;
        };
        static thread_local Scratch ws;
        auto& c=ws.c; auto& prof=ws.prof; auto& ok=ws.ok;
        cells(op, h, G, c);
        prof.resize(I.ns); ok.resize(I.ns);
        for (int s = 0; s < I.ns; s++) {
            prof[s] = I.pr(op[c[s]], s);
            ok[s] = prof[s] > 0 && I.servable[s];
        }
        int J = skills.size();
        auto& allow=ws.allow; allow.assign((size_t)K*J, 1);
        auto& val=ws.val; auto& idx=ws.idx;
        for (int j = 0; j < J; j++) {
            if (wcnt[j] >= K) continue;
            val.assign(K, 0.);
            for (int s = 0; s < I.ns; s++) if (ok[s] && req[s][j]) val[c[s]] += prof[s];
            idx.resize(K);
            iota(idx.begin(), idx.end(), 0);
            sort(idx.begin(), idx.end(), [&](int a, int b) { return val[a] > val[b] || (val[a] == val[b] && a < b); });
            for (int r = wcnt[j]; r < K; r++) allow[(size_t)idx[r]*J+j] = 0;
        }
        for (int s = 0; s < I.ns; s++) if (ok[s])
            for (int j = 0; j < J; j++) if (req[s][j] && !allow[(size_t)c[s]*J+j]) { ok[s] = 0; break; }
        auto& mem=ws.mem; if ((int)mem.size()<K) mem.resize(K);
        for(int b=0;b<K;b++) mem[b].clear();
        for (int s = 0; s < I.ns; s++) if (ok[s]) mem[c[s]].push_back(s);
        int smin = INT_MAX;
        for (int b = 0; b < K; b++) {
            auto& m = mem[b];
            sort(m.begin(), m.end(), [&](int x, int y) { return prof[x] > prof[y]; });
            if ((int)m.size() > I.maxsize[op[b]]) m.resize(I.maxsize[op[b]]);
            smin = min(smin, (int)m.size());
        }
        for (int b = 0; b < K; b++)
            if ((long long)mem[b].size() > smin + I.A) mem[b].resize(smin + I.A);
        double base_cost = 0;
        for (int o : op) base_cost += I.cost[o];
        double P0 = 0;
        for (int b = 0; b < K; b++) for (int s : mem[b]) P0 += prof[s];
        if (I.alpha <= 0) {
            if (out) { out->assign(I.no, {}); for (int b = 0; b < K; b++) (*out)[op[b]] = mem[b]; }
            return P0 - base_cost;
        }
        auto& rm=ws.rm; auto& ct=ws.ct; auto& cp=ws.cp; auto& L=ws.L;
        if((int)rm.size()<K){rm.resize(K);ct.resize(K);cp.resize(K);}
        for(int b=0;b<K;b++){rm[b].clear();ct[b].clear();cp[b].clear();}
        L.assign(K,0.);
        for (int b = 0; b < K; b++) {
            for (int s : mem[b]) { L[b] += I.ntask[s]; if (I.ntask[s] > 0) rm[b].push_back(s); }
            sort(rm[b].begin(), rm[b].end(), [&](int x, int y) {
                return prof[x] / I.ntask[x] < prof[y] / I.ntask[y];
            });
            double a = 0, q = 0;
            for (int s : rm[b]) { a += I.ntask[s]; q += prof[s]; ct[b].push_back(a); cp[b].push_back(q); }
        }
        double lo = *min_element(L.begin(), L.end()), hi = *max_element(L.begin(), L.end());
        auto& levels=ws.levels; levels.assign(L.begin(), L.end());
        for (int i = 0; i <= 40; i++) levels.push_back(lo + (hi - lo) * i / 40.0);
        sort(levels.begin(), levels.end());
        levels.erase(unique(levels.begin(), levels.end()), levels.end());
        double bestf = NEG;
        auto& bestcut=ws.bestcut; auto& cut=ws.cut; bestcut.clear();cut.resize(K);
        for (double t : levels) {
            double cost = 0, mx = NEG, mn = 1e300;
            int smx = INT_MIN, smn = INT_MAX;
            for (int b = 0; b < K; b++) {
                double ex = L[b] - t, nl = L[b];
                int k = 0;
                if (ex > 0 && !rm[b].empty()) {
                    k = lower_bound(ct[b].begin(), ct[b].end(), ex - 1e-9) - ct[b].begin() + 1;
                    k = min(k, (int)rm[b].size());
                    cost += cp[b][k - 1];
                    nl -= ct[b][k - 1];
                }
                cut[b] = k;
                int sz = mem[b].size() - k;
                smx = max(smx, sz); smn = min(smn, sz);
                mx = max(mx, nl); mn = min(mn, nl);
            }
            if ((long long)(smx - smn) > I.A) continue;
            double f = P0 - cost - base_cost - I.alpha * (mx - mn);
            if (f > bestf) { bestf = f; bestcut = cut; }
        }
        if (out && !bestcut.empty()) {
            out->assign(I.no, {});
            for (int b = 0; b < K; b++) {
                set<int> drop(rm[b].begin(), rm[b].begin() + bestcut[b]);
                for (int s : mem[b]) if (!drop.count(s)) (*out)[op[b]].push_back(s);
            }
        }
        return bestf;
    }

    double search(const vector<int>& op, vector<double>& h, vector<Pt>& G, int iters, double deadline) const {
        double best = evaluate(op, h, G);
        vector<array<double, 3>> step(I.no);
        for (int o : op) step[o] = {0.5 * scale2, 0.05 * I.ext, 0.05 * I.ext};
        for (int it = 0; it < iters; it++) {
            if (elapsed() > deadline) break;
            bool improved = false, alive = false;
            for (int o : op)
                for (int p = 0; p < 3; p++) {
                    bool moved = false;
                    for (double sg : {1.0, -1.0}) {
                        double d = sg * step[o][p];
                        double& v = p == 0 ? h[o] : (p == 1 ? G[o].x : G[o].y);
                        v += d;
                        double f = evaluate(op, h, G);
                        if (f > best + 1e-9) { best = f; improved = moved = true; step[o][p] *= 1.6; break; }
                        v -= d;
                    }
                    if (!moved) step[o][p] *= 0.5;
                    if (step[o][p] > 1e-7 * (p == 0 ? scale2 : I.ext)) alive = true;
                }
            if (!improved && !alive) break;
        }
        return best;
    }
};

// engine.h: Engine: движок ходов поверх Sol.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ============================================================ движок ходов
struct Engine {
    Sol& s;
    const Inst& I;
    struct Op { uint8_t t; int x, o; };   // 0 add, 1 remove, 2 open, 3 close
    vector<Op> jr;
    bool rec = false;
    vector<char> ban;                     // [o*nsk+k] офису o запрещён навык k
    bool hasban = false;
    vector<Pt> add_hull; // Reused by sequential doAdd calls on this engine.

    Engine(Sol& so) : s(so), I(*so.I) { ban.assign((size_t)I.no * I.nsk, 0); }

    void set_ban(int o, int k, bool v) { ban[(size_t)o * I.nsk + k] = v; hasban = true; }
    void clear_ban() { if (hasban) { fill(ban.begin(), ban.end(), 0); hasban = false; } }

    bool can_add_skills(int x, int o) const {
        for (int k : I.skillset[x]) {
            if (hasban && ban[(size_t)o * I.nsk + k]) return false;
            if (s.need[o][k] == 0 && s.cntSkill[k] + 1 > I.Nk[k]) return false;
        }
        return true;
    }
    // насколько нарушен баланс числа сайтов (0 = всё хорошо)
    long long size_viol(int oadd, int orem) const {
        int mx = INT_MIN, mn = INT_MAX;
        for (int o = 0; o < I.no; o++) {
            if (!s.isopen[o]) continue;
            int sz = s.size_[o] + (o == oadd ? 1 : 0) - (o == orem ? 1 : 0);
            if (sz == 0) continue;
            if (sz > I.maxsize[o]) return (long long)4e18;
            mx = max(mx, sz); mn = min(mn, sz);
        }
        if (mx == INT_MIN) return 0;
        return max(0LL, (long long)(mx - mn) - I.A);
    }
    void doRemove(int x) {
        int o = s.asg[x];
        if (o < 0) return;
        s.remove_site(x);
        if (rec) jr.push_back({1, x, o});
    }
    bool doAdd(int x, int o) {
        if (s.asg[x] >= 0 || !I.servable[x] || !s.isopen[o]) return false;
        if (s.size_[o] >= I.maxsize[o]) return false;
        if (!can_add_skills(x, o)) return false;
        if (!s.geo_ok(x, o, add_hull)) return false;
        s.add_site_raw(x, o, add_hull);
        if (rec) jr.push_back({0, x, o});
        return true;
    }
    void doOpen(int o) {
        if (s.isopen[o]) return;
        if (s.cov[I.ns + o] > 0) return;          // точка офиса уже в чужой зоне
        s.isopen[o] = 1;
        s.sig_open(o);
        s.rebuild_hull(o);
        if (rec) jr.push_back({2, -1, o});
    }
    void doClose(int o) {
        if (!s.isopen[o]) return;
        while (!s.members[o].empty()) doRemove(s.members[o].back());
        s.isopen[o] = 0;
        s.sig_open(o);
        s.clear_cov(o);
        s.hull[o].clear();
        if (rec) jr.push_back({3, -1, o});
    }
    void undo(size_t mark) {
        while (jr.size() > mark) {
            Op op = jr.back();
            jr.pop_back();
            bool r = rec; rec = false;
            if (op.t == 0) s.remove_site(op.x);
            else if (op.t == 1) s.force_add(op.x, op.o);
            else if (op.t == 2) { s.isopen[op.o] = 0; s.sig_open(op.o); s.clear_cov(op.o); s.hull[op.o].clear(); }
            else { s.isopen[op.o] = 1; s.sig_open(op.o); s.rebuild_hull(op.o); }
            rec = r;
        }
    }
};

// build.h: конструкторы стартовых разбиений (power diagram, секторы, гильотина, ...).
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ================================================================ сборка
// Кому из офисов достаётся дефицитный навык: берём N_k зон с наибольшей
// прибылью от сайтов, которым этот навык нужен. Пара итераций с учётом того,
// что сайту нужны ВСЕ его навыки.
static void plan_skills(const Inst& I, const vector<int>& ops, const vector<int>& cellOf,
                        vector<char>& allow, mt19937_64* rng = nullptr, double temp = 0.0) {
    int K = ops.size();
    vector<int> idx(I.no, -1);
    for (int b = 0; b < K; b++) idx[ops[b]] = b;
    allow.assign((size_t)K * I.nsk, 1);
    vector<char> ok(I.ns, 0);
    for (int x = 0; x < I.ns; x++)
        ok[x] = I.servable[x] && cellOf[x] >= 0 && idx[cellOf[x]] >= 0 && I.pr(cellOf[x], x) > 0;
    for (int iter = 0; iter < 3; iter++) {
        vector<char> prev = allow;
        fill(allow.begin(), allow.end(), 1);
        for (int k = 0; k < I.nsk; k++) {
            if (I.Nk[k] >= K) continue;
            vector<double> val(K, 0.0);
            for (int x = 0; x < I.ns; x++) {
                if (!ok[x]) continue;
                if (!binary_search(I.skillset[x].begin(), I.skillset[x].end(), k)) continue;
                val[idx[cellOf[x]]] += I.pr(cellOf[x], x);
            }
            vector<int> ord(K);
            iota(ord.begin(), ord.end(), 0);
            if (rng && temp > 0) {
                // случайный выбор зон с весом по прибыли: распределение навыков —
                // отдельное измерение поиска, жадный выбор застревает в одном варианте
                vector<double> w(K);
                double mx = *max_element(val.begin(), val.end());
                double sc = max(1e-12, fabs(mx)) * temp;
                for (int b = 0; b < K; b++) w[b] = exp((val[b] - mx) / sc);
                vector<int> pick;
                for (int r = 0; r < K; r++) {
                    double tot = 0;
                    for (int b = 0; b < K; b++) tot += w[b];
                    if (tot <= 0) break;
                    double u = (double)((*rng)() % 1000000) / 1000000.0 * tot, acc2 = 0;
                    int sel = -1;
                    for (int b = 0; b < K; b++) { acc2 += w[b]; if (acc2 >= u) { sel = b; break; } }
                    if (sel < 0) break;
                    pick.push_back(sel);
                    w[sel] = 0;
                }
                for (int b = 0; b < K; b++) if (find(pick.begin(), pick.end(), b) == pick.end()) pick.push_back(b);
                ord = pick;
            } else
                stable_sort(ord.begin(), ord.end(), [&](int a, int b) { return val[a] > val[b]; });
            for (int r = I.Nk[k]; r < K; r++) allow[(size_t)ord[r] * I.nsk + k] = 0;
        }
        for (int x = 0; x < I.ns; x++) {
            if (!I.servable[x] || cellOf[x] < 0 || idx[cellOf[x]] < 0 || I.pr(cellOf[x], x) <= 0) { ok[x] = 0; continue; }
            ok[x] = 1;
            for (int k : I.skillset[x]) if (!allow[(size_t)idx[cellOf[x]] * I.nsk + k]) { ok[x] = 0; break; }
        }
        if (allow == prev) break;
    }
}

// Ценность плана навыков: суммарная прибыль сайтов, которые при нём обслужимы.
static double plan_value(const Inst& I, const vector<int>& cellOf, const vector<int>& idx,
                         const vector<char>& allow) {
    double v = 0;
    for (int x = 0; x < I.ns; x++) {
        int o = cellOf[x];
        if (o < 0 || idx[o] < 0 || !I.servable[x]) continue;
        double p = I.pr(o, x);
        if (p <= 0) continue;
        bool ok = true;
        for (int k : I.skillset[x])
            if (!allow[(size_t)idx[o] * I.nsk + k]) { ok = false; break; }
        if (ok) v += p;
    }
    return v;
}

// Локальный поиск по матрице allow[зона][навык]: добавить дефицитный навык
// свободной зоне или перенести его между зонами. Один жадный проход, как было
// раньше, сильно недобирает: офисы остаются без навыков и простаивают.
static void optimize_skill_plan(const Inst& I, const vector<int>& ops, const vector<int>& cellOf,
                                vector<char>& allow, double deadline) {
    int K = ops.size();
    if (!K) return;
    vector<int> idx(I.no, -1);
    for (int b = 0; b < K; b++) idx[ops[b]] = b;
    vector<int> scarce;
    for (int k = 0; k < I.nsk; k++) if (I.Nk[k] > 0 && I.Nk[k] < K) scarce.push_back(k);
    if (scarce.empty()) return;
    long long work = (long long)I.ns * scarce.size() * (K + K * K);
    int rounds = work > 200000000LL ? 1 : (work > 40000000LL ? 3 : 8);
    double best = plan_value(I, cellOf, idx, allow);
    for (int r = 0; r < rounds; r++) {
        bool imp = false;
        for (int k : scarce) {
            if (elapsed() > deadline) return;
            int cnt = 0;
            for (int b = 0; b < K; b++) cnt += allow[(size_t)b * I.nsk + k] ? 1 : 0;
            if (cnt < I.Nk[k]) {                       // есть свободный рабочий — кому отдать
                for (int b = 0; b < K; b++) {
                    if (allow[(size_t)b * I.nsk + k]) continue;
                    allow[(size_t)b * I.nsk + k] = 1;
                    double v = plan_value(I, cellOf, idx, allow);
                    if (v > best + 1e-9) { best = v; imp = true; cnt++; }
                    else allow[(size_t)b * I.nsk + k] = 0;
                }
            }
            for (int a = 0; a < K; a++) {              // перенести навык между зонами
                if (!allow[(size_t)a * I.nsk + k]) continue;
                for (int b = 0; b < K; b++) {
                    if (b == a || allow[(size_t)b * I.nsk + k]) continue;
                    allow[(size_t)a * I.nsk + k] = 0;
                    allow[(size_t)b * I.nsk + k] = 1;
                    double v = plan_value(I, cellOf, idx, allow);
                    if (v > best + 1e-9) { best = v; imp = true; a = b; }
                    else { allow[(size_t)a * I.nsk + k] = 1; allow[(size_t)b * I.nsk + k] = 0; }
                }
            }
        }
        if (!imp) break;
    }
}

static void realize(Sol& s, const Inst& I, const vector<int>& ops, const vector<int>& cellOf,
                    double deadline = 1e18, mt19937_64* rng = nullptr, double temp = 0.0) {
    s.init(I);
    for (int o : ops) {
        if (s.cov[I.ns + o] > 0) continue;
        s.isopen[o] = 1;
        s.rebuild_hull(o);
    }
    Engine E(s);
    vector<char> allow;
    plan_skills(I, ops, cellOf, allow, rng, temp);
    if (temp <= 0) optimize_skill_plan(I, ops, cellOf, allow, deadline);
    for (size_t b = 0; b < ops.size(); b++)
        for (int k = 0; k < I.nsk; k++)
            if (!allow[b * I.nsk + k]) E.set_ban(ops[b], k, true);
    vector<pair<double, pair<int, int>>> order;
    order.reserve(I.ns);
    for (int x = 0; x < I.ns; x++) {
        int o = cellOf[x];
        if (o < 0 || !s.isopen[o] || !I.servable[x]) continue;
        order.push_back({I.pr(o, x), {x, o}});
    }
    sort(order.rbegin(), order.rend());
    // План навыков считает по числу рабочих N_k, а многопрофильный рабочий не
    // закроет навыки в двух офисах сразу: сайт с новым для офиса навыком берём,
    // только если рабочих ещё можно раздать (WFIX=0 — без проверки)
    static const bool wfix = !getenv("WFIX") || atoi(getenv("WFIX")) > 0;
    const bool chk = wfix && !I.simple_workers;
    auto add = [&](int x, int o) {
        uint64_t sg = s.sig;
        if (E.doAdd(x, o) && chk && s.sig != sg && !s.greedy_workers(nullptr)) s.remove_site(x);
    };
    size_t i = 0;
    for (auto& e : order) {
        if ((++i & 63) == 0 && elapsed() > deadline) break;
        add(e.second.first, e.second.second);
    }
    E.clear_ban();
    // вторым проходом добиваем то, что влезает и без плана
    i = 0;
    for (auto& e : order) {
        if ((++i & 63) == 0 && elapsed() > deadline) break;
        if (s.asg[e.second.first] < 0) add(e.second.first, e.second.second);
    }
}

// конструктор: ближайший по дороге открытый офис
static vector<int> ctor_road(const Inst& I, const vector<int>& ops) {
    vector<int> c(I.ns, -1);
    for (int s = 0; s < I.ns; s++) {
        int b = -1;
        for (int o : ops) if (b < 0 || I.d(o, s) < I.d(b, s)) b = o;
        c[s] = b;
    }
    return c;
}
// конструктор: угловые секторы вокруг центра (выпуклые клинья)
static vector<int> ctor_sector(const Inst& I, const vector<int>& ops, Pt cen) {
    int K = ops.size();
    vector<pair<double, int>> ang;
    for (int o : ops) ang.push_back({atan2(I.P[I.ns + o].y - cen.y, I.P[I.ns + o].x - cen.x), o});
    sort(ang.begin(), ang.end());
    vector<double> bnd(K);
    for (int i = 0; i < K; i++) {
        double a = ang[i].first, b = ang[(i + 1) % K].first;
        if (b < a) b += 2 * M_PI;
        bnd[i] = 0.5 * (a + b);
    }
    vector<int> c(I.ns, -1);
    for (int s = 0; s < I.ns; s++) {
        double a = atan2(I.P[s].y - cen.y, I.P[s].x - cen.x);
        int pick = ang[0].second;
        for (int i = 0; i < K; i++) {
            double lo = i == 0 ? bnd[K - 1] - 2 * M_PI : bnd[i - 1];
            double hi = bnd[i];
            double aa = a;
            if (aa < lo) aa += 2 * M_PI;
            if (aa >= lo && aa < hi) { pick = ang[i].second; break; }
        }
        c[s] = pick;
    }
    return c;
}

// Конструктор «гильотина»: рекурсивно делим множество офисов прямой, выбирая
// направление и положение разреза по честной сумме max(reward - dist, 0).
// В отличие от power diagram опирается на дорожные расстояния, а не на
// геометрическую близость — важно там, где они расходятся.
static void guillotine_rec(const Inst& I, vector<int> ops, vector<int> sites,
                           vector<int>& cellOf, mt19937_64& rng, int ndir) {
    if (ops.empty()) return;
    if (ops.size() == 1) { for (int x : sites) cellOf[x] = ops[0]; return; }
    int K = ops.size();
    double bestv = NEG, bdx = 1, bdy = 0, bcut = 0;
    int bm = 1;
    vector<int> bord;
    vector<double> lv(sites.size()), rv(sites.size());
    vector<pair<double, int>> sp(sites.size());
    for (int di = 0; di < ndir; di++) {
        double th = di < ndir / 2 ? M_PI * di / max(1, ndir / 2)
                                  : 2 * M_PI * (double)(rng() % 10000) / 10000.0;
        double dx = cos(th), dy = sin(th);
        vector<pair<double, int>> op2;
        for (int o : ops) op2.push_back({I.P[I.ns + o].x * dx + I.P[I.ns + o].y * dy, o});
        sort(op2.begin(), op2.end());
        for (size_t i = 0; i < sites.size(); i++)
            sp[i] = {I.P[sites[i]].x * dx + I.P[sites[i]].y * dy, sites[i]};
        sort(sp.begin(), sp.end());
        for (int m = 1; m < K; m++) {
            double lo = op2[m - 1].first, hi = op2[m].first;
            if (hi - lo < 1e-12 * max(1.0, I.ext)) continue;
            for (size_t i = 0; i < sp.size(); i++) {
                int x = sp[i].second;
                double a = NEG, b = NEG;
                for (int j = 0; j < m; j++) a = max(a, I.pr(op2[j].second, x));
                for (int j = m; j < K; j++) b = max(b, I.pr(op2[j].second, x));
                lv[i] = max(0.0, a); rv[i] = max(0.0, b);
            }
            double cur = 0;
            for (size_t i = 0; i < sp.size(); i++) cur += rv[i];   // разрез на уровне lo
            double bc = lo, bv = NEG;
            for (size_t i = 0;; i++) {
                if (cur > bv) { bv = cur; bc = i == 0 ? lo : sp[i - 1].first; }
                if (i >= sp.size() || sp[i].first > hi) break;
                if (sp[i].first <= lo) { cur += lv[i] - rv[i]; continue; }
                cur += lv[i] - rv[i];
            }
            if (bv > bestv) {
                bestv = bv; bdx = dx; bdy = dy; bcut = bc; bm = m;
                bord.clear();
                for (auto& e : op2) bord.push_back(e.second);
            }
        }
    }
    if (bestv <= NEG / 2) { for (int x : sites) cellOf[x] = ops[0]; return; }
    vector<int> lo_ops(bord.begin(), bord.begin() + bm), hi_ops(bord.begin() + bm, bord.end());
    vector<int> lo_s, hi_s;
    for (int x : sites)
        (I.P[x].x * bdx + I.P[x].y * bdy <= bcut ? lo_s : hi_s).push_back(x);
    guillotine_rec(I, lo_ops, lo_s, cellOf, rng, ndir);
    guillotine_rec(I, hi_ops, hi_s, cellOf, rng, ndir);
}

static vector<int> ctor_guillotine(const Inst& I, const vector<int>& ops, mt19937_64& rng) {
    vector<int> cellOf(I.ns, -1), all(I.ns);
    iota(all.begin(), all.end(), 0);
    guillotine_rec(I, ops, all, cellOf, rng, I.ns > 2000 ? 8 : 16);
    return cellOf;
}

// moves.h: LNS-ходы: Guide (сглаженная цель), TopSum, переразрез прямой, recreate, сдвиг навыка.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ============================================================ LNS + отжиг
// Штраф alpha*(max-min) близорук: одиночная вставка почти всегда выглядит
// убыточной, даже когда набор в целом хорош. Поэтому поиск ведётся по
// сглаженной цели: alpha*(max-min) + lam*sum|L_o - mean|.

// Двойственность по балансу нагрузки:
//   alpha*(max L - min L) = max_{pi in Pi} sum_o pi_o * L_o,
//   Pi = { pi : sum_o pi_o = 0, sum_o max(pi_o,0) <= alpha }.
// Значит при фиксированных ценах pi задача распадается по сайтам: сайт стоит
// брать в офис o, если pr(o,s) - pi_o * tasks(s) > 0. Цены подтягиваются
// субградиентным шагом по текущим нагрузкам. Это убирает «обрыв» штрафа
// max-min: вместо цены alpha ровно на двух офисах получаем гладкие цены на всех.
struct Guide {
    Sol& s;
    const Inst& I;
    double lam;
    vector<double> pi;
    Guide(Sol& so, double l) : s(so), I(*so.I), lam(l) { pi.assign(I.no, 0.0); }

    inline double eff(int o, int x) const { return I.pr(o, x) - pi[o] * I.ntask[x]; }

    void dual_step(double rate) {
        if (I.alpha <= 0) return;
        double sum = 0;
        int n = 0;
        for (int o = 0; o < I.no; o++)
            if (s.isopen[o] && s.size_[o] > 0) { sum += (double)s.load[o]; n++; }
        if (n < 2) { fill(pi.begin(), pi.end(), 0.0); return; }
        double mean = sum / n;
        double scale = max(1.0, mean);
        for (int o = 0; o < I.no; o++) {
            if (!s.isopen[o] || s.size_[o] == 0) { pi[o] = 0; continue; }
            pi[o] += rate * I.alpha * ((double)s.load[o] - mean) / scale;
        }
        double m = 0;
        for (int o = 0; o < I.no; o++) if (s.isopen[o] && s.size_[o] > 0) m += pi[o];
        m /= n;
        double pos = 0;
        for (int o = 0; o < I.no; o++)
            if (s.isopen[o] && s.size_[o] > 0) { pi[o] -= m; if (pi[o] > 0) pos += pi[o]; }
        if (pos > I.alpha && pos > 0)
            for (int o = 0; o < I.no; o++) pi[o] *= I.alpha / pos;
    }

    // -cost - alpha*(max-min) - lam*spread при гипотетических сдвигах двух офисов
    double tail2(int o1, int d1sz, long long d1ld, int o2, int d2sz, long long d2ld) const {
        double c = 0, sum = 0;
        long long mx = LLONG_MIN, mn = LLONG_MAX;
        int n = 0;
        for (int o = 0; o < I.no; o++) {
            if (!s.isopen[o]) continue;
            int sz = s.size_[o] + (o == o1 ? d1sz : 0) + (o == o2 ? d2sz : 0);
            if (sz <= 0) continue;
            long long ld = s.load[o] + (o == o1 ? d1ld : 0) + (o == o2 ? d2ld : 0);
            c += I.cost[o];
            sum += (double)ld;
            n++;
            mx = max(mx, ld); mn = min(mn, ld);
        }
        if (!n) return 0.0;
        double r = -c - I.alpha * (double)(mx - mn);
        if (lam > 0 && n > 1) {
            double mean = sum / n, sp = 0;
            for (int o = 0; o < I.no; o++) {
                if (!s.isopen[o]) continue;
                int sz = s.size_[o] + (o == o1 ? d1sz : 0) + (o == o2 ? d2sz : 0);
                if (sz <= 0) continue;
                long long ld = s.load[o] + (o == o1 ? d1ld : 0) + (o == o2 ? d2ld : 0);
                sp += fabs((double)ld - mean);
            }
            r -= lam * sp;
        }
        return r;
    }
    double val() const { return s.psum + tail2(-1, 0, 0, -1, 0, 0); }

    // то же, но для o1,o2 размер/нагрузка заданы абсолютно
    double tail_abs(int o1, int sz1, long long ld1, int o2, int sz2, long long ld2) const {
        double c = 0, sum = 0;
        long long mx = LLONG_MIN, mn = LLONG_MAX;
        int n = 0;
        for (int o = 0; o < I.no; o++) {
            if (!s.isopen[o]) continue;
            int sz = o == o1 ? sz1 : (o == o2 ? sz2 : s.size_[o]);
            if (sz <= 0) continue;
            long long ld = o == o1 ? ld1 : (o == o2 ? ld2 : s.load[o]);
            c += I.cost[o]; sum += (double)ld; n++;
            mx = max(mx, ld); mn = min(mn, ld);
        }
        if (!n) return 0.0;
        double r = -c - I.alpha * (double)(mx - mn);
        if (lam > 0 && n > 1) {
            double mean = sum / n, sp = 0;
            for (int o = 0; o < I.no; o++) {
                if (!s.isopen[o]) continue;
                int sz = o == o1 ? sz1 : (o == o2 ? sz2 : s.size_[o]);
                if (sz <= 0) continue;
                long long ld = o == o1 ? ld1 : (o == o2 ? ld2 : s.load[o]);
                sp += fabs((double)ld - mean);
            }
            r -= lam * sp;
        }
        return r;
    }
    // вклад всех офисов, кроме o1 и o2
    double psum_other(int o1, int o2) const {
        double p = 0;
        for (int o = 0; o < I.no; o++) {
            if (!s.isopen[o] || o == o1 || o == o2) continue;
            for (int x : s.members[o]) p += I.pr(o, x);
        }
        return p;
    }
};

// Сумма прибыли и нагрузки по m лучшим (по прибыли) элементам множества,
// меняющегося по одному элементу. Нужна для развёртки разреза при жёстком maxSize.
struct TopSum {
    int m = 0;
    const vector<int>* nt = nullptr;
    set<pair<double, int>> top, rest;   // (профит, сайт); top — m лучших
    double psum = 0;
    long long lsum = 0;
    void init(int mm, const vector<int>& ntask) { m = mm; nt = &ntask; top.clear(); rest.clear(); psum = 0; lsum = 0; }
    void push_top(const pair<double, int>& e) { top.insert(e); psum += e.first; lsum += (*nt)[e.second]; }
    void pop_top(const pair<double, int>& e) { top.erase(e); psum -= e.first; lsum -= (*nt)[e.second]; }
    void balance() {
        while ((int)top.size() > m) { auto e = *top.begin(); pop_top(e); rest.insert(e); }
        while ((int)top.size() < m && !rest.empty()) { auto e = *prev(rest.end()); rest.erase(e); push_top(e); }
    }
    void insert(double p, int x) {
        pair<double, int> e{p, x};
        if ((int)top.size() < m || (!top.empty() && p > top.begin()->first)) push_top(e);
        else rest.insert(e);
        balance();
    }
    void erase(double p, int x) {
        pair<double, int> e{p, x};
        auto it = top.find(e);
        if (it != top.end()) pop_top(e);
        else rest.erase(e);
        balance();
    }
    int size() const { return (int)top.size(); }
};

// Переразрезать две зоны новой прямой. Главный ход: при выпуклых зонах
// одиночный перенос сайта почти всегда ломает геометрию, двигать нужно
// границу целиком. Перебираем все положения разреза вдоль направления.
static bool move_resplit(Engine& E, Guide& Gd, mt19937_64& rng, bool force,
                         int fo1 = -1, int fo2 = -1, int ndir = 9, double hard = 1e18) {
    Sol& s = E.s;
    const Inst& I = E.I;
    vector<int> op;
    for (int o = 0; o < I.no; o++) if (s.isopen[o]) op.push_back(o);
    if (op.size() < 2) return false;
    int o1, o2;
    if (fo1 >= 0 && fo2 >= 0) { o1 = fo1; o2 = fo2; }
    else {
        int a = rng() % op.size(), b = rng() % op.size();
        if (a == b) b = (b + 1) % op.size();
        o1 = op[a]; o2 = op[b];
    }
    if (o1 == o2 || !s.isopen[o1] || !s.isopen[o2]) return false;
    const Pt& q1 = I.P[I.ns + o1];
    const Pt& q2 = I.P[I.ns + o2];

    // кандидаты: сайты обеих зон плюс свободные, чей ближайший открытый офис — один из двух
    vector<int> U = s.members[o1];
    U.insert(U.end(), s.members[o2].begin(), s.members[o2].end());
    for (int x = 0; x < I.ns; x++) {
        if (s.asg[x] >= 0 || !I.servable[x]) continue;
        for (int o : I.cand[x]) if (s.isopen[o]) { if (o == o1 || o == o2) U.push_back(x); break; }
    }
    if (U.size() < 2) return false;

    double pother = Gd.psum_other(o1, o2);
    // текущее значение пары зон — базовая планка
    double pcur = 0;
    for (int x : s.members[o1]) pcur += I.pr(o1, x);
    for (int x : s.members[o2]) pcur += I.pr(o2, x);
    double curv = pother + pcur + Gd.tail_abs(o1, s.size_[o1], s.load[o1], o2, s.size_[o2], s.load[o2]);

    // какие навыки доступны каждой из двух зон после снятия всех их сайтов
    vector<char> alw1(I.nsk, 0), alw2(I.nsk, 0);
    for (int k = 0; k < I.nsk; k++) {
        int used = s.cntSkill[k] - (s.need[o1][k] > 0 ? 1 : 0) - (s.need[o2][k] > 0 ? 1 : 0);
        int avail = I.Nk[k] - used;
        if (avail >= 2) { alw1[k] = alw2[k] = 1; }
        else if (avail == 1) {
            double w1 = 0, w2 = 0;
            for (int x : s.members[o1]) if (binary_search(I.skillset[x].begin(), I.skillset[x].end(), k)) w1 += max(0.0, I.pr(o1, x));
            for (int x : s.members[o2]) if (binary_search(I.skillset[x].begin(), I.skillset[x].end(), k)) w2 += max(0.0, I.pr(o2, x));
            if (w1 == w2 ? (rng() & 1) : (w1 > w2)) alw1[k] = 1; else alw2[k] = 1;
        }
    }
    auto fits = [&](int x, int o) {
        const vector<char>& A = (o == o1) ? alw1 : alw2;
        for (int k : I.skillset[x]) if (!A[k]) return false;
        return true;
    };

    double vx = q2.x - q1.x, vy = q2.y - q1.y;
    double base = sqrt(vx * vx + vy * vy) < 1e-15 ? 0.0 : atan2(vy, vx);
    double bestAll = NEG, bDx = 1, bDy = 0, bTh = base;
    size_t bestkAll = 0;
    int bLo = o1, bHi = o2;
    vector<pair<double, int>> pr;
    pr.reserve(U.size());
    TopSum L, H;
    auto sweep = [&](double th) {
        double dx = cos(th), dy = sin(th);
        double p1 = q1.x * dx + q1.y * dy, p2 = q2.x * dx + q2.y * dy;
        int lo_off = o1, hi_off = o2;
        if (p1 > p2) { swap(p1, p2); lo_off = o2; hi_off = o1; }
        if (p2 - p1 < 1e-12 * max(1.0, I.ext)) return;
        pr.clear();
        for (int x : U) pr.push_back({I.P[x].x * dx + I.P[x].y * dy, x});
        sort(pr.begin(), pr.end());
        L.init(I.maxsize[lo_off], I.ntask);
        H.init(I.maxsize[hi_off], I.ntask);
        size_t start = 0;
        while (start < pr.size() && pr[start].first <= p1) {
            int x = pr[start].second;
            double v = Gd.eff(lo_off, x);
            if (v > 0 && fits(x, lo_off)) L.insert(v, x);
            start++;
        }
        for (size_t i = start; i < pr.size(); i++) {
            int x = pr[i].second;
            double v = Gd.eff(hi_off, x);
            if (v > 0 && fits(x, hi_off)) H.insert(v, x);
        }
        for (size_t k = start;; k++) {
            int szL = L.size(), szH = H.size();
            // истинная прибыль = сумма эффективных + pi_o * нагрузка
            double trueL = L.psum + Gd.pi[lo_off] * (double)L.lsum;
            double trueH = H.psum + Gd.pi[hi_off] * (double)H.lsum;
            double v = pother + trueL + trueH + Gd.tail_abs(lo_off, szL, L.lsum, hi_off, szH, H.lsum);
            if (v > bestAll) {
                int mx = INT_MIN, mn = INT_MAX;
                for (int o = 0; o < I.no; o++) {
                    if (!s.isopen[o]) continue;
                    int sz = o == lo_off ? szL : (o == hi_off ? szH : s.size_[o]);
                    if (sz <= 0) continue;
                    mx = max(mx, sz); mn = min(mn, sz);
                }
                if (mx == INT_MIN || (long long)(mx - mn) <= I.A) {
                    bestAll = v; bestkAll = k; bDx = dx; bDy = dy; bTh = th;
                    bLo = lo_off; bHi = hi_off;
                }
            }
            if (k >= pr.size() || pr[k].first > p2) break;
            int x = pr[k].second;
            double vh = Gd.eff(hi_off, x), vl = Gd.eff(lo_off, x);
            if (vh > 0 && fits(x, hi_off)) H.erase(vh, x);
            if (vl > 0 && fits(x, lo_off)) L.insert(vl, x);
        }
    };
    int ND = ndir;
    for (int di = 0; di < ND; di++)
        sweep(di == 0 ? base
                      : base + ((double)(rng() % 20001) / 10000.0 - 1.0) * (di < 5 ? 0.8 : M_PI));
    // уточнение направления вокруг лучшего
    for (double del = 0.4; del > 0.012; del *= 0.5) {
        double th0 = bTh, before = bestAll;
        sweep(th0 + del);
        sweep(th0 - del);
        if (bestAll <= before + 1e-12) continue;
    }
    if (bestAll <= NEG / 2) return false;
    if (!force && bestAll <= curv + 1e-9) return false;

    pr.clear();
    for (int x : U) pr.push_back({I.P[x].x * bDx + I.P[x].y * bDy, x});
    sort(pr.begin(), pr.end());
    for (int x : U) if (s.asg[x] >= 0) E.doRemove(x);
    vector<pair<double, int>> sl, sh;
    for (size_t i = 0; i < pr.size(); i++) {
        int x = pr[i].second;
        int o = i < bestkAll ? bLo : bHi;
        double v = Gd.eff(o, x);
        if (v <= 0 || !fits(x, o)) continue;
        (o == bLo ? sl : sh).push_back({v, x});
    }
    sort(sl.rbegin(), sl.rend());
    sort(sh.rbegin(), sh.rend());
    if ((int)sl.size() > I.maxsize[bLo]) sl.resize(I.maxsize[bLo]);
    if ((int)sh.size() > I.maxsize[bHi]) sh.resize(I.maxsize[bHi]);
    vector<pair<double, pair<int, int>>> ord;
    for (auto& e : sl) ord.push_back({e.first, {e.second, bLo}});
    for (auto& e : sh) ord.push_back({e.first, {e.second, bHi}});
    sort(ord.rbegin(), ord.rend());
    int nadd = 0;
    for (auto& e : ord) {
        if ((++nadd & 127) == 0 && elapsed() > hard) break;
        E.doAdd(e.second.first, e.second.second);
    }
    return true;
}

static void recreate(Engine& E, Guide& Gd, mt19937_64& rng, bool aggressive, int topk,
                     double deadline = 1e18) {
    Sol& s = E.s;
    const Inst& I = E.I;
    vector<int> un;
    for (int x = 0; x < I.ns; x++) if (s.asg[x] < 0 && I.servable[x]) un.push_back(x);
    if (un.empty()) return;
    shuffle(un.begin(), un.end(), rng);
    long long v0 = E.size_viol(-1, -1);
    int nn = 0;
    for (int x : un) {
        if ((++nn & 63) == 0 && elapsed() > deadline) return;
        int bo = -1;
        double bs = NEG;
        int tried = 0;
        for (int o : I.cand[x]) {
            if (!s.isopen[o]) continue;
            if (++tried > topk) break;
            if (s.size_[o] >= I.maxsize[o]) continue;
            if (E.size_viol(o, -1) > max(v0, 0LL)) continue;
            if (!E.can_add_skills(x, o)) continue;
            double sc = Gd.eff(o, x);
            if (sc > bs) { bs = sc; bo = o; }
        }
        if (bo < 0) continue;
        if (!aggressive && bs <= 0) continue;
        E.doAdd(x, bo);
    }
}

// Перераспределить дефицитный навык: отобрать его у офиса-донора и отдать
// другому (возможно, закрытому — тогда он открывается). Без этого хода поиск
// намертво застревает: все рабочие разобраны, новые офисы открыть нечем.
static bool move_skill_shift(Engine& E, Guide& Gd, mt19937_64& rng) {
    Sol& s = E.s;
    const Inst& I = E.I;
    vector<int> ks;
    for (int k = 0; k < I.nsk; k++) if (I.Nk[k] > 0) ks.push_back(k);
    if (ks.empty()) return false;
    int k = ks[rng() % ks.size()];
    vector<int> users, others;
    for (int o = 0; o < I.no; o++) {
        if (s.isopen[o] && s.need[o][k] > 0) users.push_back(o);
        else others.push_back(o);
    }
    if (others.empty()) return false;
    int target = others[rng() % others.size()];
    int donor = -1;
    if ((int)users.size() >= I.Nk[k]) {
        if (users.empty()) return false;
        donor = users[rng() % users.size()];
    }
    if (donor == target) return false;
    if (donor >= 0) {
        E.set_ban(donor, k, true);
        vector<int> mem = s.members[donor];
        for (int x : mem)
            if (binary_search(I.skillset[x].begin(), I.skillset[x].end(), k)) E.doRemove(x);
    }
    if (!s.isopen[target]) E.doOpen(target);
    if (!s.isopen[target]) { E.clear_ban(); return false; }
    // сначала сознательно заселяем получателя сайтами, которым нужен этот навык
    vector<pair<double, int>> want;
    for (int x = 0; x < I.ns; x++) {
        if (s.asg[x] >= 0 || !I.servable[x]) continue;
        if (!binary_search(I.skillset[x].begin(), I.skillset[x].end(), k)) continue;
        double v = I.pr(target, x);
        if (v > 0) want.push_back({v, x});
    }
    sort(want.rbegin(), want.rend());
    for (auto& e : want) E.doAdd(e.second, target);
    recreate(E, Gd, rng, false, 6);
    E.clear_ban();
    return true;
}

// improve.h: greedy_fill, try_open_office, polish, перепланирование навыков.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// Дозаполнение «уровнем»: при жёстком A (часто A = 0) любое одиночное добавление
// ломает баланс размеров, а DP умеет только снимать — зоны застревают ниже
// возможного. Раунд добавляет по сайту каждой зоне минимального размера и
// принимается целиком, если цель выросла. LEVEL=0 — выключить.
static bool level_fill(Sol& s, Engine& E, double deadline) {
    static const bool on = !getenv("LEVEL") || atoi(getenv("LEVEL")) > 0;
    const Inst& I = *s.I;
    if (!on) return false;
    bool rec0 = E.rec;
    size_t base = E.jr.size();
    E.rec = true;
    bool any = false;
    vector<pair<double, int>> c;
    for (int round = 0; round < I.ns && elapsed() < deadline; round++) {
        int mn = INT_MAX, nz = 0;
        for (int o = 0; o < I.no; o++)
            if (s.isopen[o] && s.size_[o] > 0) { mn = min(mn, s.size_[o]); nz++; }
        if (nz < 2) break;
        double f0 = s.objective();
        size_t mark = E.jr.size();
        bool ok = true;
        for (int o = 0; o < I.no && ok; o++) {
            if (!s.isopen[o] || s.size_[o] != mn) continue;
            if (s.size_[o] >= I.maxsize[o]) { ok = false; break; }
            c.clear();
            for (int x = 0; x < I.ns; x++)
                if (s.asg[x] < 0 && I.servable[x]) c.push_back({I.pr(o, x), x});
            int k = min((int)c.size(), 40);
            partial_sort(c.begin(), c.begin() + k, c.end(), greater<pair<double, int>>());
            ok = false;
            for (int i = 0; i < k && !ok; i++) ok = E.doAdd(c[i].second, o);
        }
        if (ok) {
            s.recompute_psum();
            ok = E.size_viol(-1, -1) == 0 && s.objective() > f0 + 1e-9
                 && (I.simple_workers || s.greedy_workers(nullptr));
        }
        if (!ok) { E.undo(mark); s.recompute_psum(); break; }
        any = true;
    }
    if (!rec0) E.jr.resize(base);
    E.rec = rec0;
    return any;
}

// Дозаполнение: добавляем все свободные сайты, которые улучшают честную цель.
// Точный DP умеет только снимать сайты, переразрез работает парами зон, поэтому
// без этого шага выгодные и допустимые сайты так и остаются неназначенными.
static bool greedy_fill(Sol& s, Engine& E, double deadline) {
    const Inst& I = *s.I;
    Guide G0(s, 0.0);
    bool any = false;
    for (int pass = 0; pass < 3; pass++) {
        vector<pair<double, int>> un;
        for (int x = 0; x < I.ns; x++) {
            if (s.asg[x] >= 0 || !I.servable[x]) continue;
            double b = NEG;
            for (int o = 0; o < I.no; o++) if (s.isopen[o]) b = max(b, I.pr(o, x));
            if (b > 0) un.push_back({b, x});
        }
        if (un.empty()) break;
        sort(un.rbegin(), un.rend());
        bool changed = false;
        int c = 0;
        for (auto& e : un) {
            if ((++c & 31) == 0 && elapsed() > deadline) return any;
            int x = e.second;
            double base = G0.tail2(-1, 0, 0, -1, 0, 0);
            int bo = -1;
            double bd = 1e-9;
            int tried = 0;
            for (int o : I.cand[x]) {
                if (!s.isopen[o]) continue;
                if (++tried > 6) break;
                if (s.size_[o] >= I.maxsize[o]) continue;
                if (E.size_viol(o, -1) > 0) continue;
                if (!E.can_add_skills(x, o)) continue;
                double d = I.pr(o, x) + G0.tail2(o, 1, I.ntask[x], -1, 0, 0) - base;
                if (d > bd) { bd = d; bo = o; }
            }
            if (bo >= 0 && E.doAdd(x, bo)) {
                if (!I.simple_workers && !s.greedy_workers(nullptr)) s.remove_site(x);
                else changed = any = true;
            }
        }
        if (!changed) break;
    }
    if (level_fill(s, E, deadline)) any = true;
    return any;
}

// Открыть закрытый офис, расчистив вокруг него место, и дозаполнить. Без
// расчистки точка офиса почти всегда лежит в чужой зоне и открыть его нельзя,
// а именно ёмкость часто и упирается (на instance4 — 33 сайта).
static bool try_open_office(Sol& s, Engine& E, double deadline) {
    const Inst& I = *s.I;
    bool any = false;
    for (int o = 0; o < I.no; o++) {
        if (s.isopen[o] || elapsed() > deadline) continue;
        if (I.maxsize[o] <= 0) continue;
        const Pt& q = I.P[I.ns + o];
        vector<pair<double, int>> near;
        for (int x = 0; x < I.ns; x++)
            if (s.asg[x] >= 0) {
                double dx = I.P[x].x - q.x, dy = I.P[x].y - q.y;
                near.push_back({dx * dx + dy * dy, x});
            }
        sort(near.begin(), near.end());
        for (int kk : {0, 8, 20, 45, 90}) {
            if (kk > (int)near.size()) break;
            if (elapsed() > deadline) return any;
            vector<int> sv = s.asg;
            vector<char> so = s.isopen;
            double f0 = s.objective();
            for (int i = 0; i < kk; i++) s.remove_site(near[i].second);
            if (s.cov[I.ns + o] == 0) {
                s.isopen[o] = 1;
                s.rebuild_hull(o);
                s.recompute_psum();
                greedy_fill(s, E, deadline);
                repair_sizes(s);
                s.recompute_psum();
                if (s.objective() > f0 + 1e-9) { any = true; break; }
            }
            s.load_state(sv, so);
        }
    }
    return any;
}

// Детерминированная доводка: прогоняем переразрез по всем парам открытых
// офисов с плотным перебором направлений, пока хоть что-то улучшается, и
// чередуем с точным DP. Снимает разброс между прогонами и поднимает плато.
static void polish(Sol& s, mt19937_64& rng, double tend, double dp_deadline, bool lock_offices = false) {
    const Inst& I = *s.I;
    Engine E(s);
    E.rec = false;
    Guide G0(s, 0.0);   // чистая цель, без сглаживания
    int maxr = I.ns > 2000 ? 3 : 12;
    for (int round = 0; round < maxr; round++) {
        bool improved = false;
        vector<int> op;
        for (int o = 0; o < I.no; o++) if (s.isopen[o] && s.size_[o] > 0) op.push_back(o);
        if (op.size() >= 2) {
            double pend = tend;
            for (size_t i = 0; i < op.size() && elapsed() < pend; i++)
                for (size_t j = i + 1; j < op.size() && elapsed() < pend; j++) {
                    vector<int> sv = s.asg;
                    vector<char> so = s.isopen;
                    double f0 = s.objective();
                    if (!move_resplit(E, G0, rng, false, op[i], op[j], I.ns > 2000 ? 12 : 36,
                                          I.ns > 1500 ? pend + 1.0 : 1e18)) continue;
                    s.recompute_psum();
                    if (E.size_viol(-1, -1) == 0 && (I.simple_workers || s.greedy_workers(nullptr))
                        && s.objective() > f0 + 1e-9) {
                        improved = true;
                        offer(I, s);
                    } else s.load_state(sv, so);
                }
        }
        if (greedy_fill(s, E, tend)) { improved = true; s.recompute_psum(); offer(I, s); }
        if (!lock_offices && I.ns <= 2000 && try_open_office(s, E, tend)) {
            improved = true; s.recompute_psum(); offer(I, s);
        }
        if (elapsed() < dp_deadline) {
            vector<int> sv = s.asg;
            vector<char> so = s.isopen;
            double before = s.objective();
            if (resize_dp(s, dp_deadline, !lock_offices)) {
                repair_sizes(s);
                s.recompute_psum();
                if (s.objective() < before - 1e-9) s.load_state(sv, so);
                else if (s.objective() > before + 1e-9) { improved = true; offer(I, s); }
            }
        }
        if (!improved || elapsed() >= tend) break;
    }
    offer(I, s);
}

// Пересчитать план навыков под текущие зоны и перестроиться под него.
static bool move_replan_skills(Engine& E, Guide& Gd, mt19937_64& rng) {
    Sol& s = E.s;
    const Inst& I = E.I;
    vector<int> ops;
    for (int o = 0; o < I.no; o++) if (s.isopen[o]) ops.push_back(o);
    if (ops.size() < 2) return false;
    bool scarce = false;
    for (int k = 0; k < I.nsk; k++) if (I.Nk[k] > 0 && I.Nk[k] < (int)ops.size()) scarce = true;
    if (!scarce) return false;
    vector<int> cellOf(I.ns, -1);
    for (int x = 0; x < I.ns; x++) {
        if (s.asg[x] >= 0) { cellOf[x] = s.asg[x]; continue; }
        if (!I.servable[x]) continue;
        for (int o : I.cand[x]) if (s.isopen[o]) { cellOf[x] = o; break; }
    }
    vector<char> allow;
    plan_skills(I, ops, cellOf, allow);
    optimize_skill_plan(I, ops, cellOf, allow, elapsed() + 0.5);
    vector<int> idx(I.no, -1);
    for (size_t b = 0; b < ops.size(); b++) idx[ops[b]] = b;
    for (size_t b = 0; b < ops.size(); b++)
        for (int k = 0; k < I.nsk; k++)
            if (!allow[b * I.nsk + k]) E.set_ban(ops[b], k, true);
    for (int o : ops) {
        vector<int> mem = s.members[o];
        for (int x : mem) {
            for (int k : I.skillset[x])
                if (!allow[(size_t)idx[o] * I.nsk + k]) { E.doRemove(x); break; }
        }
    }
    recreate(E, Gd, rng, false, 6, I.ns > 1500 ? elapsed() + 1.5 : 1e18);
    E.clear_ban();
    return true;
}

// Native bounded reconstruction: fixed nonempty office cores, free boundary sites.
// Point-footprints use Sol's selected geometry kernel (exact by default in v4).
struct BoundaryStats { long calls=0,nodes=0,pruned=0,geo=0,leaves=0,wfail=0,complete=0,wins=0; double gain=0; };
static thread_local BoundaryStats boundary_stats;

struct BoundarySearch {
    Sol& s; const Inst& I; Engine E;
    vector<int> xs,ops,old,best; vector<vector<int>> dom;
    vector<double> bound_prices; vector<double> suf; vector<vector<int>> reach;
    vector<vector<long long>> tasks;
    double deadline,bestval,cost=0; bool stopped=false; int strong;
    BoundarySearch(Sol& v,vector<int> sites,vector<int> offices,double end,int st=1):
        s(v),I(*v.I),E(v),xs(move(sites)),ops(move(offices)),deadline(end),strong(st) {
        E.rec=true; bestval=s.objective();
        // Expensive decisions first: geometry and count constraints then propagate early.
        stable_sort(xs.begin(),xs.end(),[&](int a,int b){
            double va=0,vb=0;for(int o:ops){va=max(va,I.pr(o,a));vb=max(vb,I.pr(o,b));}
            return va>vb;
        });
        for(int x:xs){old.push_back(s.asg[x]);E.doRemove(x);} best=old;
        // At least one site per incumbent office remains: opening costs are constant.
        for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o])cost+=I.cost[o];
        dom.resize(xs.size()); vector<Pt> h;
        for(size_t j=0;j<xs.size();j++) {
            int x=xs[j];
            for(int o:ops)if(E.can_add_skills(x,o)&&s.size_[o]<I.maxsize[o]&&s.geo_ok(x,o,h))dom[j].push_back(o);
            sort(dom[j].begin(),dom[j].end(),[&](int a,int b){return I.pr(a,x)>I.pr(b,x);});
            dom[j].push_back(-1);
        }
        bound_prices.reserve(xs.size());
        int n=xs.size();suf.assign(n+1,0);reach.assign(n+1,vector<int>(I.no,0));tasks.assign(n+1,vector<long long>(I.no,0));
        for(int j=n-1;j>=0;j--){double p=0;reach[j]=reach[j+1];tasks[j]=tasks[j+1];
            for(int o:dom[j])if(o>=0){p=max(p,I.pr(o,xs[j]));reach[j][o]++;tasks[j][o]+=I.ntask[xs[j]];}
            suf[j]=suf[j+1]+p;
        }
        E.jr.clear();
    }
    double bound(int j) {
        long long maxlo=0,minhi=LLONG_MAX;int maxcnt=0,mincnt=INT_MAX;
        for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o]){
            maxlo=max(maxlo,s.load[o]);minhi=min(minhi,s.load[o]+tasks[j][o]);
            maxcnt=max(maxcnt,s.size_[o]);mincnt=min(mincnt,min(I.maxsize[o],s.size_[o]+reach[j][o]));
        }
        if((long long)maxcnt>mincnt+I.A)return NEG;
        double extra=suf[j];
        if(strong){ // capacity relaxation: allow same site to earn in several offices, safely optimistic
            double capextra=0;
            for(int o:ops){auto& p=bound_prices;p.clear();for(int k=j;k<(int)xs.size();k++)
                if(find(dom[k].begin(),dom[k].end(),o)!=dom[k].end()&&I.pr(o,xs[k])>0)p.push_back(I.pr(o,xs[k]));
                sort(p.rbegin(),p.rend());int cap=I.maxsize[o]-s.size_[o];
                for(int k=0;k<min(cap,(int)p.size());k++)capextra+=p[k];}
            extra=min(extra,capextra);
        }
        return s.psum+extra-cost-I.alpha*(double)max(0LL,maxlo-minhi);
    }
    bool expired(){if(elapsed()>=deadline){stopped=true;return true;}return false;}
    void leaf(){
        boundary_stats.leaves++; if(E.size_viol(-1,-1))return;
        double val=s.objective_fast();if(val<=bestval+1e-7*max(1.,fabs(bestval)))return;
        if(!s.greedy_workers(nullptr)){boundary_stats.wfail++;return;}
        bestval=val;for(size_t k=0;k<xs.size();k++)best[k]=s.asg[xs[k]];
    }
    void dfs(int j){
        boundary_stats.nodes++;if(expired())return;
        if(bound(j)<=bestval+1e-9){boundary_stats.pruned++;return;}
        if(j==(int)xs.size()){leaf();return;}
        for(int o:dom[j]){size_t mark=E.jr.size();
            if(o<0||E.doAdd(xs[j],o)){dfs(j+1);E.undo(mark);}else boundary_stats.geo++;
            if(stopped)return;
        }
    }
    void beam(int width,bool diverse,bool adaptive=false){
        struct State{vector<int> path;double ub;uint64_t profile;};
        vector<State> beam{{{},bound(0),0}};
        for(int j=0;j<(int)xs.size()&&!beam.empty();j++){
            vector<State> next;
            for(const auto& st:beam){if(expired())break;size_t root=E.jr.size();bool ok=true;
                for(int k=0;k<j;k++)if(st.path[k]>=0&&!E.doAdd(xs[k],st.path[k])){ok=false;break;}
                if(ok)for(int o:dom[j]){
                    if(expired())break;boundary_stats.nodes++;size_t mark=E.jr.size();
                    if(o<0||E.doAdd(xs[j],o)){
                        double ub=bound(j+1);
                        if(ub>bestval+1e-9){
                            if(j+1==(int)xs.size())leaf();
                            else{auto path=st.path;path.push_back(o);uint64_t hash=0;
                                for(int p:ops)hash=(hash*1000003ULL)^((uint64_t)s.size_[p]*7919ULL+(uint64_t)s.load[p]);
                                next.push_back({move(path),ub,hash});}
                        }else boundary_stats.pruned++;
                        E.undo(mark);
                    }else boundary_stats.geo++;
                }
                E.undo(root);
            }
            if(stopped)break;
            sort(next.begin(),next.end(),[](const State&a,const State&b){return a.ub>b.ub;});
            if(adaptive){
                set<uint64_t> unique;for(const auto&v:next)unique.insert(v.profile);
                width=max(16,min(128,(int)unique.size()*2));
            }
            beam.clear();vector<char> used(next.size(),0);set<uint64_t> profiles;
            if(diverse)for(size_t k=0;k<next.size()&&(int)beam.size()<width/2;k++)
                if(profiles.insert(next[k].profile).second){beam.push_back(next[k]);used[k]=1;}
            for(size_t k=0;k<next.size()&&(int)beam.size()<width;k++)if(!used[k])beam.push_back(move(next[k]));
        }
    }
    bool finish(){
        double oldval=0; // restore with force_add; no floating accumulation survives a call
        for(size_t k=0;k<xs.size();k++)if(old[k]>=0)s.force_add(xs[k],old[k]);
        s.recompute_psum();oldval=s.objective();
        if(bestval>oldval+1e-7*max(1.,fabs(oldval))){
            auto saved=s.asg;auto opened=s.isopen;
            for(int x:xs)s.remove_site(x);
            for(size_t k=0;k<xs.size();k++)if(best[k]>=0)s.force_add(xs[k],best[k]);
            s.recompute_psum();vector<int>w;double val=0;
            if(!s.greedy_workers(&w)||!verify(I,s.asg,s.isopen,w,&val)||val<=oldval+1e-9){s.load_state(saved,opened);return false;}
            boundary_stats.wins++;boundary_stats.gain+=val-oldval;return true;
        }
        return false;
    }
};

static bool boundary_move(Sol&s,mt19937_64&rng,double end,int method=1,int style=0,int q=12){
    const Inst&I=*s.I;if(elapsed()>=end)return false;
    vector<int>active;for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o]>1)active.push_back(o);
    if(active.size()<2)return false;
    int a=active[rng()%active.size()];int anchor=s.members[a][rng()%s.members[a].size()];
    // Alternate geometric proximity and road opportunity; geometry remains in original coordinates.
    if(style&&rng()%2){vector<pair<double,int>>v;for(int x=0;x<I.ns;x++)if(I.servable[x]&&(s.asg[x]<0||s.asg[x]!=a)){
        double gain=I.pr(a,x)-(s.asg[x]<0?0:I.pr(s.asg[x],x));if(gain>0)v.push_back({gain,x});}
        sort(v.rbegin(),v.rend());if(!v.empty())anchor=v[rng()%min<size_t>(16,v.size())].second;
    }
    vector<pair<double,int>>near;
    for(int o:active)if(o!=a){double d=1e300;
        for(int x:s.members[o]){double dx=I.P[x].x-I.P[anchor].x,dy=I.P[x].y-I.P[anchor].y;d=min(d,dx*dx+dy*dy);}
        near.push_back({d,o});}
    sort(near.begin(),near.end());vector<int>ops{a,near[rng()%min<size_t>(2,near.size())].second};
    if(rng()%3==0&&near.size()>1)for(auto e:near)if(e.second!=ops[1]){ops.push_back(e.second);break;}
    vector<char>target(I.no,0);for(int o:ops)target[o]=1;
    vector<pair<double,int>>rank;
    for(int x=0;x<I.ns;x++)if(I.servable[x]&&(s.asg[x]<0||target[s.asg[x]])){
        double dx=I.P[x].x-I.P[anchor].x,dy=I.P[x].y-I.P[anchor].y;double d=dx*dx+dy*dy;
        // Support-focused variant prioritizes removable hull vertices near the opportunity.
        if(style&&s.asg[x]>=0)for(Pt p:s.hull[s.asg[x]])if(pteq(p,I.P[x])){d*=.12;break;}
        rank.push_back({d,x});
    }
    sort(rank.begin(),rank.end());vector<int>xs,removed(I.no,0);int free=0;
    for(auto e:rank){int x=e.second,o=s.asg[x];if(o<0&&free>=q/3)continue;
        if(o>=0&&removed[o]+1>=s.size_[o])continue;
        xs.push_back(x);if(o<0)free++;else removed[o]++;
        if((int)xs.size()>=q)break;
    }
    if(xs.empty())return false;
    boundary_stats.calls++;BoundarySearch b(s,xs,ops,end,method!=4);
    if(method==1||method==4)b.dfs(0);else b.beam(32,method==3||method==5,method==5);
    if(!b.stopped&&(method==1||method==4))boundary_stats.complete++;
    return b.finish();
}
static void boundary_polish(Sol&s,mt19937_64&rng,double end,int method,int style=0){
    while(elapsed()<end){double d=min(end,elapsed()+.04);long old=boundary_stats.calls;
        int q=getenv("B_Q")?max(4,min(40,atoi(getenv("B_Q")))):24;
        boundary_move(s,rng,d,method,style,q);
        if(old==boundary_stats.calls)break;}
}

// lns.h: главный цикл LNS + отжиг, detect_cpus.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

static void lns(Sol& s, mt19937_64& rng, double tend, double dp_deadline, bool deep,
                double lam_frac = 0.25, double ruin_scale = 1.0, bool lock_offices = false) {
    const Inst& I = *s.I;
    Engine E(s);
    E.rec = true;
    vector<int> cand;
    for (int x = 0; x < I.ns; x++) if (I.servable[x]) cand.push_back(x);
    if (cand.empty()) return;

    double scale = 0;
    {
        long cnt = 0;
        for (int o = 0; o < I.no; o++) if (s.isopen[o])
            for (int x = 0; x < I.ns; x += max(1, I.ns / 200)) { scale += fabs(I.pr(o, x)); cnt++; }
        scale = cnt ? scale / cnt : 1.0;
        if (!(scale > 0)) scale = 1.0;
    }
    Guide Gd(s, I.alpha * lam_frac);
    double cur = Gd.val();
    double T_hi = 0.25 * scale, T_lo = 1e-4 * scale, T = T_hi;
    double t_start = elapsed();
    // хвост чанка резервируем под детерминированную доводку
    double tloop = max(t_start + 0.05 * (tend - t_start), tend - min(0.3 * (tend - t_start), 25.0));
    // на больших инстансах один ход идёт десятки мс: не даём ему выйти за tend
    const double hardcap = I.ns > 1500 ? min(tloop + 1.0, tend) : 1e18;
    double dur = max(1e-3, tloop - t_start);
    uniform_real_distribution<double> U(0, 1);
    // при одном навыке на рабочего счётный критерий точен; иначе нужна проверка
    // назначением — один рабочий не может закрыть навыки в двух офисах сразу
    uint64_t wsig = ~0ULL;
    bool wok = false;
    auto feasible = [&]() {
        if (E.size_viol(-1, -1) > 0) return false;
        if (I.simple_workers) return true;
        if (s.sig != wsig) { wsig = s.sig; wok = s.greedy_workers(nullptr); }
        return wok;
    };
    vector<int> assigned;
    long it = 0, acc = 0, dpn = 0; long cnt[4][4] = {};  // [kind][0 try,1 fail,2 viol,3 acc]
    int since_dp = 0;
    vector<Pt> hh;

    auto try_dp = [&](void) {
        vector<int> sv = s.asg;
        vector<char> so = s.isopen;
        double before = s.objective();
        E.rec = false;
        bool ch = resize_dp(s, min(tloop + 5.0, dp_deadline), !lock_offices);
        if (ch) {
            repair_sizes(s);
            if (s.objective() < before - 1e-9) s.load_state(sv, so);
            else offer(I, s);
        }
        s.recompute_psum();
        if (greedy_fill(s, E, min(tloop + 2.0, dp_deadline))) { s.recompute_psum(); offer(I, s); }
        E.rec = true;
        E.jr.clear();
        s.recompute_psum();
        cur = Gd.val();
        dpn++;
    };

    for (;; it++) {
        if ((it & 63) == 0 || I.ns > 1500) {  // большие: время на каждой итерации
            double now = elapsed();
            if (now >= tloop) break;
            T = T_hi * pow(T_lo / T_hi, (now - t_start) / dur);
            if ((it & 1023) == 0) Gd.dual_step(0.08);
            if ((it & 262143) == 0) { s.recompute_psum(); cur = Gd.val(); }
        }
        size_t mark = E.jr.size();
        int kind = rng() % 100;

        if (kind < 7) {
            // --- пересчитать план навыков целиком
            cnt[3][0]++;
            if (!move_replan_skills(E, Gd, rng)) { cnt[3][1]++; E.undo(mark); continue; }
            if (!feasible()) { cnt[3][2]++; E.undo(mark); continue; }
            {
                double f = Gd.val();
                double d = f - cur;
                if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
                    cur = f; acc++; cnt[3][3]++; E.jr.clear();
                    if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
                    if (++since_dp > (deep ? 120 : 300) && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
                } else E.undo(mark);
            }
            continue;
        }

        if (kind < 16) {
            // --- перераспределить навык между зонами
            cnt[3][0]++;
            if (!move_skill_shift(E, Gd, rng)) { cnt[3][1]++; E.undo(mark); continue; }
            if (!feasible()) { cnt[3][2]++; E.undo(mark); continue; }
            double f = Gd.val();
            double d = f - cur;
            if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
                cur = f; acc++; cnt[3][3]++; E.jr.clear();
                if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
                if (++since_dp > (deep ? 120 : 300) && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
            } else E.undo(mark);
            continue;
        }

        if (kind < 45) {
            // --- переразрезать две зоны прямой
            cnt[0][0]++;
            if (!move_resplit(E, Gd, rng, U(rng) < 0.15, -1, -1, 9, hardcap)) { cnt[0][1]++; E.undo(mark); continue; }
            if (!feasible()) { cnt[0][2]++; E.undo(mark); continue; }
            double f = Gd.val();
            double d = f - cur;
            if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
                cur = f; acc++; cnt[0][3]++; E.jr.clear();
                if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
                if (++since_dp > (deep ? 120 : 300) && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
            } else E.undo(mark);
            continue;
        }

        if (kind < 72) {
            // --- одиночный ход: перенести сайт в другой офис / снять
            int x = cand[rng() % cand.size()];
            int oold = s.asg[x];
            int onew;
            if (oold >= 0 && (rng() % 100) < 22) onew = -1;
            else {
                int tries = 0, pick = -1;
                for (int o : I.cand[x]) { if (s.isopen[o]) { if (tries == 0 || (rng() % 4) == 0) pick = o; if (++tries >= 5) break; } }
                onew = pick;
            }
            cnt[1][0]++;
            if (onew == oold || (oold < 0 && onew < 0)) { cnt[1][1]++; continue; }
            if (oold >= 0) E.doRemove(x);
            if (onew >= 0 && !E.doAdd(x, onew)) { cnt[1][1]++; E.undo(mark); continue; }
            if (!feasible()) { cnt[1][2]++; E.undo(mark); continue; }
            double f = Gd.val();
            double d = f - cur;
            if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
                cur = f; acc++; cnt[1][3]++; E.jr.clear();
                if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
            } else E.undo(mark);
            if (++since_dp > 20000 && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
            continue;
        }

        // --- ruin & recreate
        assigned.clear();
        for (int x = 0; x < I.ns; x++) if (s.asg[x] >= 0) assigned.push_back(x);
        int mode = rng() % 100;
        if (mode < 40 && !assigned.empty()) {
            int c = assigned[rng() % assigned.size()];
            int q = max(1, (int)((3 + rng() % 25) * ruin_scale));
            vector<pair<double, int>> v;
            v.reserve(assigned.size());
            for (int x : assigned) {
                double dx = I.P[x].x - I.P[c].x, dy = I.P[x].y - I.P[c].y;
                v.push_back({dx * dx + dy * dy, x});
            }
            if ((int)v.size() > q) nth_element(v.begin(), v.begin() + q, v.end());
            for (int i = 0; i < min((int)v.size(), q); i++) E.doRemove(v[i].second);
        } else if (mode < 62 && !assigned.empty()) {
            int q = max(1, (int)((3 + rng() % 20) * ruin_scale));
            shuffle(assigned.begin(), assigned.end(), rng);
            for (int i = 0; i < min((int)assigned.size(), q); i++) E.doRemove(assigned[i]);
        } else if (mode < 80) {
            vector<int> op;
            for (int o = 0; o < I.no; o++) if (s.isopen[o] && s.size_[o] > 0) op.push_back(o);
            if (op.empty()) { E.undo(mark); continue; }
            int o = op[rng() % op.size()];
            vector<int> mem = s.members[o];
            shuffle(mem.begin(), mem.end(), rng);
            int q = max(1, (int)(mem.size() * (0.2 + 0.6 * U(rng))));
            for (int i = 0; i < min((int)mem.size(), q); i++) E.doRemove(mem[i]);
        } else if (mode < 91) {
            if (lock_offices) { E.undo(mark); continue; }
            vector<int> op;
            for (int o = 0; o < I.no; o++) if (s.isopen[o]) op.push_back(o);
            if (op.empty()) { E.undo(mark); continue; }
            E.doClose(op[rng() % op.size()]);
        } else {
            vector<int> cl;
            for (int o = 0; o < I.no; o++) if (!s.isopen[o]) cl.push_back(o);
            if (cl.empty()) { E.undo(mark); continue; }
            int o = cl[rng() % cl.size()];
            const Pt& q = I.P[I.ns + o];
            vector<pair<double, int>> v;
            v.reserve(assigned.size());
            for (int x : assigned) {
                double dx = I.P[x].x - q.x, dy = I.P[x].y - q.y;
                v.push_back({dx * dx + dy * dy, x});
            }
            int k = min((int)v.size(), 10 + (int)(rng() % 40));
            if ((int)v.size() > k) nth_element(v.begin(), v.begin() + k, v.end());
            for (int i = 0; i < k; i++) E.doRemove(v[i].second);
            E.doOpen(o);
        }
        cnt[2][0]++;
        recreate(E, Gd, rng, U(rng) < 0.3, 5, hardcap);
        if (!feasible()) { cnt[2][2]++; E.undo(mark); continue; }
        double f = Gd.val();
        double d = f - cur;
        if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
            cur = f; acc++; cnt[2][3]++; E.jr.clear();
            if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
            if (++since_dp > (deep ? 120 : 300) && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
        } else E.undo(mark);
    }
    if (elapsed() < dp_deadline) try_dp();
    offer(I, s);
    polish(s, rng, min(tend, dp_deadline), dp_deadline, lock_offices);
    try_elite(I, s);
    if (DBG)
        fprintf(stderr, "   lns it=%ld acc=%ld dp=%ld obj=%.4f best=%.4f | split %ld/%ld/%ld/%ld  single %ld/%ld/%ld/%ld  ruin %ld/%ld/%ld/%ld  skill %ld/%ld/%ld/%ld\n",
                it, acc, dpn, s.objective(), g_best.load(),
                cnt[0][0],cnt[0][1],cnt[0][2],cnt[0][3], cnt[1][0],cnt[1][1],cnt[1][2],cnt[1][3], cnt[2][0],cnt[2][1],cnt[2][2],cnt[2][3], cnt[3][0],cnt[3][1],cnt[3][2],cnt[3][3]);
}

// Сколько потоков запускать: ядра, доступные процессу (sched_getaffinity — системный
// вызов, учитывает --cpuset-cpus). Файлы (/sys, /proc, квоту cgroup) не читаем: по
// правилам открывать можно только instance.json и solution.json.
static int detect_cpus() {
    if (getenv("NT")) return max(1, atoi(getenv("NT")));
    cpu_set_t cs;
    CPU_ZERO(&cs);
    int n = sched_getaffinity(0, sizeof cs, &cs) == 0 ? CPU_COUNT(&cs) : 1;
    if (n < 1) n = 1;
    if (n > 16) n = 16;
    return n;
}

// exact2.h: точный перебор решений с 1–2 офисами: все разбиения прямой + точный рюкзак (сайты × задачи).
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

#include <unordered_set>

// ============================================== точный перебор для 1–2 офисов
// Две зоны по разные стороны прямой не делят точек. Перебираем все такие разбиения
// (прямые через пары точек, точки на прямой — целиком одной стороне), все раздачи
// навыков между двумя офисами и на каждой стороне точно решаем рюкзак
// F[c][t] = max прибыль при c сайтах и t задачах. Сочетание сторон учитывает
// maxSize, A и α|t1 − t2|. Малые инстансы: LNS иногда не находит лучшее разбиение,
// а здесь оно точное в своём классе. Результат идёт в offer и пул элиты.

struct Exact2 {
    const Inst& I;
    double deadline;
    bool useT;                       // при α = 0 задачи не важны: рюкзак только по числу сайтов
    vector<uint64_t> sm;             // маска навыков сайта
    double best = 0;
    vector<int> bestAsg;
    vector<char> bestOpen;

    Exact2(const Inst& In, double dl) : I(In), deadline(dl), useT(In.alpha > 0) {}

    int tdim(const vector<int>& it, int C) const {
        if (!useT) return 0;
        vector<int> w;
        for (int x : it) w.push_back(I.ntask[x]);
        sort(w.rbegin(), w.rend());
        int T = 0;
        for (int i = 0; i < (int)w.size() && i < C; i++) T += w[i];
        return T;
    }
    // f[c*(T+1)+t]; take != null — сохранить выбор для восстановления
    void knap(int o, const vector<int>& it, int C, int T, vector<double>& f, vector<char>* take) const {
        int L = (C + 1) * (T + 1);
        f.assign(L, NEG);
        f[0] = 0;
        if (take) take->assign((size_t)it.size() * L, 0);
        for (size_t i = 0; i < it.size(); i++) {
            int x = it[i], w = useT ? I.ntask[x] : 0;
            double p = I.pr(o, x);
            char* tk = take ? &(*take)[i * L] : nullptr;
            for (int c = C; c >= 1; c--) {
                double* dst = &f[c * (T + 1)];
                const double* src = &f[(c - 1) * (T + 1)];
                for (int t = T; t >= w; t--) {
                    double v = src[t - w];
                    if (v <= NEG / 2) continue;
                    if (v + p > dst[t]) { dst[t] = v + p; if (tk) tk[c * (T + 1) + t] = 1; }
                }
            }
        }
    }
    vector<int> restore(int o, const vector<int>& it, int C, int T, int c, int t) const {
        vector<double> f;
        vector<char> take;
        knap(o, it, C, T, f, &take);
        int L = (C + 1) * (T + 1);
        vector<int> r;
        for (int i = (int)it.size() - 1; i >= 0 && c > 0; i--)
            if (take[(size_t)i * L + c * (T + 1) + t]) { r.push_back(it[i]); c--; t -= useT ? I.ntask[it[i]] : 0; }
        return r;
    }
    // max F1[c1][t1] + F2[c2][t2] − α|t1 − t2|, |c1 − c2| ≤ A, оба офиса не пусты
    double combine(const vector<double>& F1, int C1, int T1, const vector<double>& F2, int C2, int T2,
                   int& bc1, int& bt1, int& bc2, int& bt2) const {
        double best = NEG;
        int T = max(T1, T2);
        vector<double> G(T + 1), H(T + 1);
        vector<int> Gc(T + 1), Ht(T + 1);
        for (int c1 = 1; c1 <= C1; c1++) {
            fill(G.begin(), G.end(), NEG);
            long long lo = max(1LL, c1 - I.A), hi = min((long long)C2, c1 + I.A);
            for (long long c2 = lo; c2 <= hi; c2++)
                for (int t = 0; t <= T2; t++) {
                    double v = F2[c2 * (T2 + 1) + t];
                    if (v > G[t]) { G[t] = v; Gc[t] = (int)c2; }
                }
            for (int t = 0; t <= T; t++) { H[t] = G[t]; Ht[t] = t; }
            for (int t = 1; t <= T; t++) if (H[t - 1] - I.alpha > H[t]) { H[t] = H[t - 1] - I.alpha; Ht[t] = Ht[t - 1]; }
            for (int t = T - 1; t >= 0; t--) if (H[t + 1] - I.alpha > H[t]) { H[t] = H[t + 1] - I.alpha; Ht[t] = Ht[t + 1]; }
            for (int t1 = 0; t1 <= T1; t1++) {
                double v1 = F1[c1 * (T1 + 1) + t1];
                if (v1 <= NEG / 2 || H[t1] <= NEG / 2) continue;
                if (v1 + H[t1] > best) { best = v1 + H[t1]; bc1 = c1; bt1 = t1; bt2 = Ht[t1]; bc2 = Gc[bt2]; }
            }
        }
        return best;
    }
    void found(double v, const vector<pair<int, vector<int>>>& zones) {
        if (v <= best + 1e-9) return;
        best = v;
        bestAsg.assign(I.ns, -1);
        bestOpen.assign(I.no, 0);
        for (auto& z : zones) { bestOpen[z.first] = 1; for (int x : z.second) bestAsg[x] = z.first; }
        // только в элиту: как глобальное лучшее оно стягивает к себе все потоки
        // (финальная фаза стартует с лучшего) и мешает найти решения с 3+ офисами
        Sol s;
        s.init(I);
        s.load_state(bestAsg, bestOpen);
        vector<int> wof;
        double obj = 0;
        if (s.greedy_workers(&wof) && verify(I, s.asg, s.isopen, wof, &obj)) push_elite(obj, s.asg, s.isopen);
        if (DBG) fprintf(stderr, "exact2 %.6f t=%.1f\n", v, elapsed());
    }
    // раздачи навыков (K1, K2) между двумя офисами, без доминируемых; пусто — слишком много
    vector<pair<uint64_t, uint64_t>> splits(uint64_t rel) const {
        set<pair<uint64_t, uint64_t>> st{{0, 0}};
        for (int w = 0; w < I.nw; w++) {
            uint64_t m = 0;
            for (int k : I.wskills[w]) m |= 1ULL << k;
            m &= rel;
            if (!m) continue;
            set<pair<uint64_t, uint64_t>> nx;
            for (auto& e : st) { nx.insert({e.first | m, e.second}); nx.insert({e.first, e.second | m}); }
            st.swap(nx);
            if (st.size() > 4096) return {};
        }
        vector<pair<uint64_t, uint64_t>> v(st.begin(), st.end()), r;
        for (auto& a : v) {
            bool dom = false;
            for (auto& b : v)
                if (a != b && (a.first & ~b.first) == 0 && (a.second & ~b.second) == 0) { dom = true; break; }
            if (!dom) r.push_back(a);
        }
        return r;
    }
    void run(uint64_t seed) {
        if (I.nsk > 64) return;
        sm.assign(I.ns, 0);
        uint64_t rel = 0;
        for (int x = 0; x < I.ns; x++) { for (int k : I.skillset[x]) sm[x] |= 1ULL << k; rel |= sm[x]; }
        uint64_t all = 0;
        for (int w = 0; w < I.nw; w++) for (int k : I.wskills[w]) all |= 1ULL << k;
        all &= rel;
        auto items = [&](uint64_t K, const vector<int>& sites) {
            vector<int> it;
            for (int x : sites) if ((sm[x] & ~K) == 0) it.push_back(x);
            return it;
        };
        // один офис: все рабочие ему
        vector<int> allS(I.ns);
        iota(allS.begin(), allS.end(), 0);
        vector<double> F1, F2;
        for (int o = 0; o < I.no && elapsed() < deadline; o++) {
            int C = min(I.maxsize[o], I.ns);
            if (C <= 0) continue;
            vector<int> it = items(all, allS);
            int T = tdim(it, C);
            knap(o, it, C, T, F1, nullptr);
            int bc = -1, bt = 0;
            double bv = 0;
            for (int c = 1; c <= C; c++) for (int t = 0; t <= T; t++)
                if (F1[c * (T + 1) + t] - I.cost[o] > bv) { bv = F1[c * (T + 1) + t] - I.cost[o]; bc = c; bt = t; }
            if (bc > 0) found(bv, {{o, restore(o, it, C, T, bc, bt)}});
        }
        auto sp = splits(rel);
        if (sp.empty()) return;
        // одна оценка разбиения ~ ns·C·T; дороже — перебор не успеет ничего
        {
            int C = 0;
            for (int o = 0; o < I.no; o++) C = max(C, min(I.maxsize[o], I.ns));
            if ((double)I.ns * (C + 1) * (tdim(allS, C) + 1) > 2e7) return;
        }
        // пары офисов: сначала с большей суммой положительной прибыли
        vector<pair<double, pair<int, int>>> pairs;
        vector<double> pot(I.no, 0);
        for (int o = 0; o < I.no; o++) for (int x = 0; x < I.ns; x++) pot[o] += max(0.0, I.pr(o, x));
        for (int a = 0; a < I.no; a++) for (int b = a + 1; b < I.no; b++)
            if (I.maxsize[a] > 0 && I.maxsize[b] > 0) pairs.push_back({pot[a] + pot[b] - I.cost[a] - I.cost[b], {a, b}});
        sort(pairs.rbegin(), pairs.rend());
        const int N = I.ns + I.no;
        const auto& P = I.P;
        vector<pair<int, int>> lines;
        for (int p = 0; p < N; p++) for (int q = p + 1; q < N; q++)
            if (P[p].x != P[q].x || P[p].y != P[q].y) lines.push_back({p, q});
        mt19937_64 rng(seed);
        shuffle(lines.begin(), lines.end(), rng);
        vector<int> side(N);
        vector<char> lab(I.ns);
        for (auto& pr : pairs) {
            int o1 = pr.second.first, o2 = pr.second.second;
            int Cmax1 = min(I.maxsize[o1], I.ns), Cmax2 = min(I.maxsize[o2], I.ns);
            unordered_set<uint64_t> seen;
            for (size_t li = 0; li < lines.size(); li++) {
                if (elapsed() > deadline) return;
                int p = lines[li].first, q = lines[li].second;
                double dx = P[q].x - P[p].x, dy = P[q].y - P[p].y;
                for (int i = 0; i < N; i++) {
                    double cr = dx * (P[i].y - P[p].y) - dy * (P[i].x - P[p].x);
                    side[i] = cr > 0 ? 1 : cr < 0 ? -1 : 0;
                }
                for (int lineTo : {1, -1}) for (int orient : {1, -1}) {
                    auto S = [&](int i) { int s = side[i] ? side[i] : lineTo; return s == orient ? 1 : 2; };
                    if (S(I.ns + o1) != 1 || S(I.ns + o2) != 2) continue;
                    uint64_t h = 1469598103934665603ULL;
                    for (int i = 0; i < I.ns; i++) { lab[i] = S(i); h = (h ^ (uint64_t)lab[i]) * 1099511628211ULL; }
                    if (!seen.insert(h).second) continue;
                    vector<int> s1, s2;
                    for (int i = 0; i < I.ns; i++) (lab[i] == 1 ? s1 : s2).push_back(i);
                    for (auto& k : sp) {
                        if (elapsed() > deadline) return;
                        vector<int> it1 = items(k.first, s1), it2 = items(k.second, s2);
                        int C1 = min(Cmax1, (int)it1.size()), C2 = min(Cmax2, (int)it2.size());
                        if (C1 <= 0 || C2 <= 0) continue;
                        int T1 = tdim(it1, C1), T2 = tdim(it2, C2);
                        knap(o1, it1, C1, T1, F1, nullptr);
                        knap(o2, it2, C2, T2, F2, nullptr);
                        int c1 = 0, t1 = 0, c2 = 0, t2 = 0;
                        double v = combine(F1, C1, T1, F2, C2, T2, c1, t1, c2, t2);
                        if (v <= NEG / 2) continue;
                        v -= I.cost[o1] + I.cost[o2];
                        if (v > best + 1e-9)
                            found(v, {{o1, restore(o1, it1, C1, T1, c1, t1)}, {o2, restore(o2, it2, C2, T2, c2, t2)}});
                    }
                }
            }
        }
    }
};

static vector<int> g_ex2_asg;
static vector<char> g_ex2_open;

// отдельный поток: EXACT2=1, только малые инстансы, до 30% лимита
static void exact2_thread(const Inst& I, double limit, uint64_t seed) {
    if (I.ns > 600) return;
    Exact2 E(I, 0.3 * limit);
    E.run(seed);
    g_ex2_asg = E.bestAsg;
    g_ex2_open = E.bestOpen;
    if (DBG) fprintf(stderr, "exact2 done best=%.6f t=%.1f\n", E.best, elapsed());
}
// после join: ответ = лучшее из LNS и перебора
static void exact2_publish(const Inst& I) {
    if (g_ex2_asg.empty()) return;
    Sol s;
    s.init(I);
    s.load_state(g_ex2_asg, g_ex2_open);
    offer(I, s);
}


// ================================================================== main
struct Cand { double f; vector<int> op; vector<double> h; vector<Pt> G; };

static void v52_finish(const Inst&,double);
static void worker(const Inst& I, const Fast& F, const vector<Cand>& cands,
                   uint64_t seed, double tend, double dp_deadline, int tid) {
    static const double LAMS[4] = {0.25, 0.10, 0.50, 0.0};
    static const double RUINS[3] = {1.0, 0.4, 2.5};
    const double PA = 0.25 * tend, P3 = 0.85 * tend;
    mt19937_64 rng(seed);
    Sol s;
    uniform_real_distribution<double> U(0, 1);
    Pt cen{0, 0};
    for (int o = 0; o < I.no; o++) { cen.x += I.P[I.ns + o].x; cen.y += I.P[I.ns + o].y; }
    if (I.no) { cen.x /= I.no; cen.y /= I.no; }
    const int NC = 6;
    if (cands.empty()) return;

    // строит стартовое решение по связке (набор офисов, конструктор)
    auto build = [&](int ci, int ctor, double deadline, bool refine, double skt = 0.0) {
        const Cand& c = cands[ci];
        vector<double> h = c.h;
        vector<Pt> G = c.G;
        if (h.empty()) { h.assign(I.no, 0.0); G.assign(I.P.begin() + I.ns, I.P.end()); }
        vector<int> cellOf(I.ns, -1);
        if (ctor <= 1) {
            if (refine) F.search(c.op, h, G, 300, min(deadline, elapsed() + 3.0));
            if (ctor == 0) {
                vector<vector<int>> mem;
                if (F.evaluate(c.op, h, G, &mem) > NEG / 2 && !mem.empty())
                    for (int o : c.op) for (int x : mem[o]) cellOf[x] = o;
            } else {
                vector<int> cell;
                F.cells(c.op, h, G, cell);
                for (int x = 0; x < I.ns; x++) cellOf[x] = c.op[cell[x]];
            }
        } else if (ctor == 2) cellOf = ctor_road(I, c.op);
        else if (ctor == 3) cellOf = ctor_sector(I, c.op, cen);
        else if (ctor == 5) cellOf = ctor_guillotine(I, c.op, rng);
        else {
            Pt r{cen.x + (U(rng) - 0.5) * 2 * I.ext, cen.y + (U(rng) - 0.5) * 2 * I.ext};
            cellOf = ctor_sector(I, c.op, r);
        }
        realize(s, I, c.op, cellOf, deadline, &rng, skt);
        repair_sizes(s);
        Engine E(s);
        if (elapsed() < dp_deadline) { resize_dp(s, dp_deadline); repair_sizes(s); }
        s.recompute_psum();
        greedy_fill(s, E, min(deadline, dp_deadline));
        s.recompute_psum();
        offer(I, s);
    };

    // --- фаза A: дешёвый отбор всех связок
    int NCOMBO = (int)cands.size() * NC;
    vector<pair<double, int>> rank;
    for (int t = 0; t < NCOMBO && elapsed() < PA; t++) {
        int combo = (t + tid * 7) % NCOMBO;
        build(combo % cands.size(), combo / cands.size(), min(PA, dp_deadline), false);
        rank.push_back({s.objective(), combo});
    }
    // Ранжируем НАБОРЫ ОФИСОВ, а не связки: набор с большим числом офисов
    // стартует хуже (навыки и геометрию ещё надо развести), но после глубокого
    // поиска часто выигрывает. Берём для каждого набора его лучший конструктор.
    {
        vector<pair<double, int>> bestOf(cands.size(), {NEG, 0});
        for (auto& e : rank) {
            int ci = e.second % (int)cands.size();
            if (e.first > bestOf[ci].first) bestOf[ci] = {e.first, e.second};
        }
        rank.clear();
        for (size_t ci = 0; ci < cands.size(); ci++)
            if (bestOf[ci].first > NEG / 2) rank.push_back(bestOf[ci]);
        sort(rank.rbegin(), rank.rend());
    }
    if (rank.empty()) rank.push_back({0.0, tid % NCOMBO});
    if (DBG && tid == 0) {
        for (size_t i = 0; i < cands.size(); i++) {
            fprintf(stderr, "cand%zu f=%.2f ops=", i, cands[i].f);
            for (int o : cands[i].op) fprintf(stderr, "%d,", o);
            fprintf(stderr, "\n");
        }
        for (size_t i = 0; i < rank.size() && i < 8; i++)
            fprintf(stderr, "  rank%zu val=%.2f cand=%d ctor=%d\n", i, rank[i].first,
                    rank[i].second % (int)cands.size(), rank[i].second / (int)cands.size());
    }

    // --- фаза B и C: глубокие прогоны по лучшим связкам и по общему лучшему
    int round = 0;
    bool regional_done=false;
    while (elapsed() < tend - max(0.5, 0.02 * tend)) {
        if(tid==0&&!regional_done&&elapsed()>=.70*tend&&(!getenv("REGION")||atoi(getenv("REGION")))&&(!getenv("MIP")||atoi(getenv("MIP")))){
            regional_done=true;v52_finish(I,min(tend-max(.8,.02*tend),elapsed()+min(2.,.035*tend)));
        }
        double now0 = elapsed();
        double left = tend - now0;
        bool last = now0 >= P3;
        double chunk = last ? left : max(1.5, min(left, min(0.12 * tend, left / 2.0)));
        double ce = now0 + chunk;
        bool fromBest = false;
        // половина потоков идёт независимо, чтобы выборка была разнообразнее
        double pBest = last ? 1.0 : ((tid & 1) ? 0.0 : 0.5);
        if (U(rng) < pBest) {
            vector<int> ea;
            vector<char> eo;
            bool got = last ? false : pick_elite(rng, ea, eo);
            if (!got) {
                lock_guard<mutex> lk(g_best_mx);
                ea = g_best_asg;
                eo = g_best_open;
                got = !ea.empty();
            }
            if (got) { s.init(I); s.load_state(ea, eo); fromBest = true; }
        }
        if (!fromBest) {
            int r = round % max<size_t>(1, min<size_t>(rank.size(), 6));
            int combo = rank[r].second;
            // каждый третий глубокий прогон стартует со случайного плана навыков
            double skt = (round % 3 == 2) ? 0.15 + 0.5 * U(rng) : 0.0;
            build(combo % cands.size(), combo / cands.size(), min(ce, dp_deadline), true, skt);
        }
        round++;
        if (!fromBest && !last) {
            // сначала заставляем выбранный набор офисов заработать, потом отпускаем
            lns(s, rng, now0 + 0.55 * chunk, dp_deadline, false, LAMS[tid % 4], RUINS[tid % 3], true);
            lns(s, rng, ce, dp_deadline, true, LAMS[tid % 4], RUINS[tid % 3], false);
        } else lns(s, rng, ce, dp_deadline, fromBest, LAMS[tid % 4], RUINS[tid % 3]);
    }
}

// evolution_warm.h: broad office-subset search, included after worker().
// All state is per invocation, with the existing instance/solution I/O only.
struct WarmGenome { Cand c; double fitness = NEG; };
static vector<Cand> wide_start(const Inst& I, const Fast& F, map<vector<int>,Cand>& cache,
                            mt19937_64& rng, double end, double limit, int mode) {
    vector<WarmGenome> pop;
    vector<Cand> realized;
    vector<double> real_by_k(I.no+1,NEG);
    const int maxpop = max(12, (int)(4*sqrt((double)max(1,I.no))));
    const int ndecode = max(3,(int)sqrt((double)max(1,I.no)));
    vector<Pt> original(I.P.begin()+I.ns,I.P.end());
    uniform_real_distribution<double> U(0.,1.);
    for (const auto& kv:cache) if(kv.second.f>NEG/2) pop.push_back({kv.second,kv.second.f});
    auto trim = [&]() {
        sort(pop.begin(),pop.end(),[](const WarmGenome&a,const WarmGenome&b){return a.fitness>b.fitness;});
        if((int)pop.size()<=maxpop)return;
        vector<WarmGenome> keep;
        set<int> sizes;
        for(const auto& e:pop) if(sizes.insert((int)e.c.op.size()).second)keep.push_back(e);
        for(const auto& e:pop) {
            if((int)keep.size()>=maxpop)break;
            bool have=false;for(const auto& k:keep)if(k.c.op==e.c.op){have=true;break;}
            if(!have)keep.push_back(e);
        }
        pop.swap(keep);
    };
    trim();
    vector<double> proxy_by_k(I.no+1,NEG);
    for(const auto&e:pop)proxy_by_k[e.c.op.size()]=max(proxy_by_k[e.c.op.size()],e.c.f);
    long attempts=0,evaluated=0,decoded=0;
    double decode_cost=0.;
    auto parent = [&]()->const WarmGenome& {
        int a=rng()%pop.size(),b=rng()%pop.size();
        // Half the selections preserve a random cardinality niche.
        if(rng()&1)return pop[a];
        return pop[a].fitness>=pop[b].fitness?pop[a]:pop[b];
    };
    vector<char> chosen(I.no), aa(I.no), bb(I.no);
    vector<int> order(I.no);
    while(elapsed()<end) {
        if(I.no<20 && cache.size()>=(1ULL<<I.no)-1)break;
        attempts++;
        Cand c;c.h.assign(I.no,0.);c.G=original;
        fill(chosen.begin(),chosen.end(),0);
        bool immigrant=mode==1 || pop.size()<2 || U(rng)<.25;
        if(immigrant) {
            int k=1+(int)((attempts-1)%max(1,I.no));
            iota(order.begin(),order.end(),0);shuffle(order.begin(),order.end(),rng);
            for(int i=0;i<k;i++)chosen[order[i]]=1;
        } else {
            const auto& a=parent().c;const auto& b=parent().c;
            fill(aa.begin(),aa.end(),0);fill(bb.begin(),bb.end(),0);
            for(int o:a.op)aa[o]=1;for(int o:b.op)bb[o]=1;
            for(int o=0;o<I.no;o++)chosen[o]=(U(rng)<.7?aa[o]:bb[o]);
            int changes=1+(rng()%max(1,(int)sqrt((double)I.no)));
            while(changes--){int o=rng()%I.no;chosen[o]=!chosen[o];}
        }
        // Coincident offices cannot both occur in any valid solution.
        for(int o=0;o<I.no;o++)if(chosen[o]) {
            bool duplicate=false;for(int p:c.op)if(pteq(original[o],original[p])){duplicate=true;break;}
            if(!duplicate)c.op.push_back(o);
        }
        if(c.op.empty())continue;
        if(cache.count(c.op))continue;
        c.f=F.evaluate(c.op,c.h,c.G);
        evaluated++;
        bool niche=c.f>proxy_by_k[c.op.size()]+1e-9;
        proxy_by_k[c.op.size()]=max(proxy_by_k[c.op.size()],c.f);
        cache.emplace(c.op,c);
        if(c.f<=NEG/2)continue;
        pop.push_back({c,c.f});trim();
        if(niche && decoded<ndecode && elapsed()+1.5*decode_cost<end) {
            double before=elapsed();
            vector<int> cells,assignment(I.ns,-1);F.cells(c.op,c.h,c.G,cells);
            for(int x=0;x<I.ns;x++)assignment[x]=c.op[cells[x]];
            Sol s;realize(s,I,c.op,assignment,end,&rng,decoded%3==2?.25:0.);
            repair_sizes(s);
            if(elapsed()<end){resize_dp(s,end);repair_sizes(s);}
            Engine E(s);s.recompute_psum();greedy_fill(s,E,end);s.recompute_psum();
            offer(I,s);
            double f=s.objective();
            if(f>real_by_k[c.op.size()]){real_by_k[c.op.size()]=f;Cand d=c;d.f=f;realized.push_back(move(d));}
            decoded++;decode_cost=max(decode_cost,elapsed()-before);
        }
        // A finite genotype space on small M should not burn the whole budget.
        if(I.no<20 && cache.size()>=(1ULL<<I.no)-1)break;
    }
    sort(realized.begin(),realized.end(),[](const Cand&a,const Cand&b){return a.f>b.f;});
    if(realized.size()>6)realized.resize(6);
    fprintf(stderr,"wide_start mode=%d attempts=%ld evaluated=%ld decoded=%ld best=%.6f t=%.3f\n",
            mode,attempts,evaluated,decoded,g_best.load(),elapsed());
    return realized;
}

// finish.h: monotone improvement in the unused final time budget.
// Exact alpha=0 selection within fixed convex territories and fixed staff teams.
// Sites inside those hulls can be added without expanding any footprint.
static bool territory_select(Sol& s,double deadline) {
    const Inst&I=*s.I;if(I.alpha!=0.||elapsed()>=deadline)return false;
    vector<int> staff;if(!s.greedy_workers(&staff))return false;
    vector<vector<char>> have(I.no,vector<char>(I.nsk,0));
    for(int w=0;w<I.nw;w++)if(staff[w]>=0)for(int k=0;k<I.nsk;k++)have[staff[w]][k]|=I.wmask[w][k];
    vector<vector<int>> pool(I.no);vector<vector<double>> prefix(I.no);vector<int> positive(I.no,0),cap(I.no,0);
    for(int x=0;x<I.ns;x++) {
        if((x&127)==0&&elapsed()>=deadline)return false;
        if(!I.servable[x])continue;int o=s.asg[x];
        if(o<0&&s.cov[x])for(int p=0;p<I.no;p++)if(s.isopen[p]&&s.size_[p]>0&&s.incov[(size_t)p*s.np+x]){o=p;break;}
        if(o<0)continue;bool ok=true;for(int k:I.skillset[x])if(!have[o][k]){ok=false;break;}
        if(ok)pool[o].push_back(x);
    }
    int largest=0;
    for(int o=0;o<I.no;o++) {
        auto&v=pool[o];sort(v.begin(),v.end(),[&](int a,int b){return I.pr(o,a)>I.pr(o,b);});
        cap[o]=min((int)v.size(),I.maxsize[o]);prefix[o].assign(cap[o]+1,0.);
        for(int j=0;j<cap[o];j++){prefix[o][j+1]=prefix[o][j]+I.pr(o,v[j]);positive[o]+=I.pr(o,v[j])>0.;}
        largest=max(largest,cap[o]);
    }
    double before=s.objective(),best=max(0.,before);vector<int> chosen(I.no,0),trial(I.no,0);
    for(int lo=1;lo<=largest;lo++) {
        if((lo&31)==0&&elapsed()>=deadline)return false;
        double score=0.;fill(trial.begin(),trial.end(),0);
        for(int o=0;o<I.no;o++)if(cap[o]>=lo) {
            int hi=(int)min((long long)cap[o],lo+I.A),n=max(lo,min(hi,positive[o]));
            double value=prefix[o][n]-I.cost[o];if(value>0.){trial[o]=n;score+=value;}
        }
        if(score>best+1e-9){best=score;chosen=trial;}
    }
    if(best<=before+1e-9||elapsed()>=deadline)return false;
    vector<int>a(I.ns,-1);vector<char>open(I.no,0);
    for(int o=0;o<I.no;o++)if(chosen[o]) {
        open[o]=1;for(int j=0;j<chosen[o];j++)a[pool[o][j]]=o;
    }
    s.load_state(a,open);s.recompute_psum();return true;
}

// Find the best FEASIBLE road offer, not just the best road offer.
static bool finish_fill(Sol& s, Engine& E, double deadline) {
    const Inst& I=*s.I;Guide G0(s,0.);bool any=false;
    vector<pair<double,int>> un,choices;
    un.reserve(I.ns);choices.reserve(I.no);
    for(int pass=0;pass<3;pass++) {
        un.clear();
        for(int x=0;x<I.ns;x++)if(s.asg[x]<0&&I.servable[x]) {
            double best=NEG;for(int o=0;o<I.no;o++)if(s.isopen[o])best=max(best,I.pr(o,x));
            if(best>0)un.push_back({best,x});
        }
        if(un.empty())break;sort(un.rbegin(),un.rend());bool changed=false;
        for(auto e:un) {
            if(elapsed()>=deadline)return any;
            int x=e.second;double base=G0.tail2(-1,0,0,-1,0,0);
            choices.clear();
            for(int o:I.cand[x]) {
                if(!s.isopen[o])continue;

                if(s.size_[o]>=I.maxsize[o]||E.size_viol(o,-1)>0||!E.can_add_skills(x,o))continue;
                // Already covered points can only join their covering office.
                if(s.cov[x]>0&&!s.incov[(size_t)o*s.np+x])continue;
                double delta=I.pr(o,x)+G0.tail2(o,1,I.ntask[x],-1,0,0)-base;
                if(delta>1e-9)choices.push_back({delta,o});
            }
            stable_sort(choices.begin(),choices.end(),[](const auto&a,const auto&b){return a.first>b.first;});
            for(auto choice:choices) {
                if(elapsed()>=deadline)return any;
                size_t mark=E.jr.size();
                if(!E.doAdd(x,choice.second))continue;
                if(!I.simple_workers&&!s.greedy_workers(nullptr)) {
                    if(E.rec)E.undo(mark);else s.remove_site(x);
                    continue;
                }
                changed=any=true;break;
            }
        }
        if(!changed)break;
    }
    if(elapsed()<deadline&&level_fill(s,E,deadline))any=true;
    return any;
}

// Run only after search threads have joined, in their unused wall-clock tail.
static void finish_solution(const Inst& I, double limit) {
    const bool enabled=!getenv("FINAL_POLISH")||atoi(getenv("FINAL_POLISH"))>0;
    double end=limit-max(.5,.002*limit);
    if(!enabled||elapsed()>=end||g_best.load()<=0.)return;
    vector<int>a;vector<char>open;
    {lock_guard<mutex> lk(g_best_mx);a=g_best_asg;open=g_best_open;}
    if(a.empty())return;
    double before=g_best.load();
    // No worker threads remain; the feasibility deadline can use the tail too.
    g_wdfs_deadline=end;
    Sol s;s.init(I);s.load_state(a,open);
    if(I.alpha==0.&&elapsed()<end)territory_select(s,end);
    Engine E(s);E.rec=true;
    if(elapsed()<end)finish_fill(s,E,end);
    s.recompute_psum();
    if(s.objective()>before+1e-9)offer(I,s);
    if(DBG)fprintf(stderr,"finish before=%.9f after=%.9f t=%.3f\n",before,g_best.load(),elapsed());
}


// Separate final operator: keep the baseline search trajectory and use its remaining budget.
static void boundary_finish(const Inst&I,double limit){
    if((getenv("BOUNDARY")&&!atoi(getenv("BOUNDARY")))||I.ns>1500||g_best.load()<=0)return;
    const double end=limit-max(.25,.002*limit);
    if(elapsed()>=end)return;
    g_wdfs_deadline=end;
    vector<int>a;vector<char>op;
    {lock_guard<mutex> lk(g_best_mx);a=g_best_asg;op=g_best_open;}
    if(a.empty())return;
    double before=g_best.load(),start=elapsed();int nt=detect_cpus();
    auto run=[&](int tid){
        Sol s;s.init(I);s.load_state(a,op);
        uint64_t seed=getenv("SEED")?strtoull(getenv("SEED"),nullptr,10):0;
        mt19937_64 rng(0xBB017ULL+tid*7919ULL+seed*1000003ULL);
        while(elapsed()<end){
            long n=boundary_stats.calls;
            boundary_move(s,rng,min(end,elapsed()+.04),1,1,24);
            if(n==boundary_stats.calls)break;
            if(s.objective_fast()>g_best.load()+1e-9)offer(I,s);
        }
        if(DBG)fprintf(stderr,"boundary tid=%d calls=%ld nodes=%ld complete=%ld wins=%ld gain=%.9f\n",tid,boundary_stats.calls,boundary_stats.nodes,boundary_stats.complete,boundary_stats.wins,boundary_stats.gain);
    };
    vector<thread>th;for(int i=1;i<nt;i++)th.emplace_back(run,i);run(0);for(auto&t:th)t.join();
    if(DBG)fprintf(stderr,"boundary_finish before=%.9f after=%.9f seconds=%.6f\n",before,g_best.load(),elapsed()-start);
}

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

// Safe enlarged envelopes + exact grouped selection/count/load/worker MILP.
// Only runs after native workers have joined. The best published solution survives failures.
static bool v5_offer(const Inst&I,const vector<int>&asg,const vector<char>&op,const vector<int>&wof){
 double score=0;if(!verify(I,asg,op,wof,&score))return false;
 lock_guard<mutex>lk(g_best_mx);if(score<=g_best.load()+1e-9)return false;
 g_best.store(score);g_best_asg=asg;g_best_open=op;publish(serialize(I,asg,op,wof));push_elite(score,asg,op);return true;
}
struct V5Group{int o,w;vector<int>skills,sites,x;int q=-1;};
static bool v5_select(const Inst&I,Sol&env,const vector<int>&old,const vector<char>&oldop,const vector<int>&staff,double deadline,bool joint){
 auto&A=v5_api();if(!A.ready||elapsed()>=deadline-.02)return false;
 double begin=elapsed(),before=g_best.load();const double inf=1e30;
 vector<vector<char>>have(I.no,vector<char>(I.nsk));for(int w=0;w<I.nw;w++)if(staff[w]>=0)for(int k=0;k<I.nsk;k++)have[staff[w]][k]|=I.wmask[w][k];
 map<vector<int>,int>lookup;vector<V5Group>groups;vector<int>ops;vector<int>poolsize(I.no);vector<long long>maxload(I.no);
 for(int o=0;o<I.no;o++)if(env.isopen[o]){
  for(int s:env.covlist[o])if(s<I.ns&&I.servable[s]){
   bool ok=true;if(!joint)for(int k:I.skillset[s])if(!have[o][k]){ok=false;break;}if(!ok)continue;
   vector<int>key{o,I.ntask[s]};if(joint)key.insert(key.end(),I.skillset[s].begin(),I.skillset[s].end());
   auto it=lookup.find(key);int g;if(it==lookup.end()){g=groups.size();lookup[key]=g;groups.push_back({o,I.ntask[s],joint?I.skillset[s]:vector<int>{},{},{},-1});}else g=it->second;
   groups[g].sites.push_back(s);poolsize[o]++;maxload[o]+=I.ntask[s];
  }
  if(poolsize[o]&&I.maxsize[o]>0)ops.push_back(o);
 }
 if(ops.empty()||elapsed()>=deadline-.02)return false;
 V5Model M;vector<vector<int>>og(I.no);vector<int>y(I.no,-1);long long T=1;
 for(auto&g:groups){sort(g.sites.begin(),g.sites.end(),[&](int a,int b){double pa=I.pr(g.o,a),pb=I.pr(g.o,b);return pa!=pb?pa>pb:a<b;});int n=0;for(int s:g.sites)n+=old[s]==g.o;g.q=M.var(0,0,g.sites.size(),1,n);og[g.o].push_back(&g-&groups[0]);}
 for(int o:ops){y[o]=M.var(I.cost[o],oldop[o]?1:0,1,1,oldop[o]);T=max(T,maxload[o]);}
 long long oldmin=LLONG_MAX,oldmax=0;for(int o:ops)if(oldop[o]){long long w=0;for(int s=0;s<I.ns;s++)if(old[s]==o)w+=I.ntask[s];oldmin=min(oldmin,w);oldmax=max(oldmax,w);}
 int hi=M.var(I.alpha,0,T,0,oldmax),lo=M.var(-I.alpha,0,T,0,oldmin==LLONG_MAX?0:oldmin);
 map<vector<int>,vector<int>>profiles;for(int w=0;w<I.nw;w++){vector<int>p;for(int k=0;k<I.nsk;k++)if(I.wmask[w][k])p.push_back(k);if(!p.empty())profiles[p].push_back(w);}
 vector<vector<int>>pk,pw;for(auto&e:profiles){pk.push_back(e.first);pw.push_back(e.second);}int P=pk.size();vector<vector<int>>u(I.no,vector<int>(P,-1));
 if(joint)for(int o:ops)for(int p=0;p<P;p++){bool used=false;for(int w:pw[p])used|=staff[w]==o;u[o][p]=M.var(0,0,1,1,used);M.row({{u[o][p],1},{y[o],-1}},-inf,0);}
 if(joint)for(int p=0;p<P;p++){vector<pair<int,double>>r;for(int o:ops)r.push_back({u[o][p],1});M.row(r,-inf,pw[p].size());}
 for(auto&g:groups){vector<pair<int,double>>r{{g.q,-1}};int warmn=lround(M.warm[g.q]);for(int j=0;j<(int)g.sites.size();j++){int x=M.var(-I.pr(g.o,g.sites[j]),0,1,0,j<warmn);g.x.push_back(x);r.push_back({x,1});}M.row(r,0,0);
  if(joint)for(int k:g.skills){vector<pair<int,double>>c{{g.q,1}};for(int p=0;p<P;p++)if(binary_search(pk[p].begin(),pk[p].end(),k))c.push_back({u[g.o][p],-(double)g.sites.size()});M.row(c,-inf,0);}
 }
 for(int o:ops){vector<pair<int,double>>cnt,load;for(int g:og[o]){cnt.push_back({groups[g].q,1});load.push_back({groups[g].q,(double)groups[g].w});}
  auto r=cnt;r.push_back({y[o],-(double)I.maxsize[o]});M.row(r,-inf,0);r=cnt;r.push_back({y[o],-1});M.row(r,0,inf);
  for(int p:ops)if(p!=o){r=cnt;for(int g:og[p])r.push_back({groups[g].q,-1});r.push_back({y[o],(double)I.maxsize[o]});r.push_back({y[p],(double)I.maxsize[o]});M.row(r,-inf,I.A+2.*I.maxsize[o]);}
  r=load;r.push_back({hi,-1});M.row(r,-inf,0);r.clear();for(auto e:load)r.push_back({e.first,-e.second});r.push_back({lo,1});r.push_back({y[o],(double)T});M.row(r,-inf,T);
 }
 M.row({{lo,1},{hi,-1}},-inf,0);if(elapsed()>=deadline-.02)return false;
 void*h=A.create();if(!h)return false;A.setbool(h,"output_flag",0);A.setint(h,"threads",1);A.setint(h,"random_seed",1);A.setdouble(h,"mip_rel_gap",1e-8);
 int rc=A.pass(h,M.cost.size(),M.rl.size(),M.ai.size(),2,1,0,M.cost.data(),M.lb.data(),M.ub.data(),M.rl.data(),M.ru.data(),M.rs.data(),M.ai.data(),M.av.data(),M.integer.data());
 if(rc<0){A.destroy(h);return false;}
 A.setsol(h,M.warm.data(),nullptr,nullptr,nullptr);double prep=elapsed()-begin;A.setdouble(h,"time_limit",max(.001,deadline-elapsed()-.03));A.run(h);
 vector<double>v(M.cost.size());int feasible=0;A.getint(h,"primal_solution_status",&feasible);int status=A.status(h);bool improved=false;
 if(feasible==2&&A.getsol(h,v.data(),nullptr,nullptr,nullptr)>=0){vector<int>asg(I.ns,-1),wof(I.nw,-1);vector<char>open(I.no,0);bool good=true;
  for(auto&g:groups){double z=v[g.q];int n=lround(z);if(!isfinite(z)||fabs(z-n)>1e-4||n<0||n>(int)g.sites.size()){good=false;break;}if(n)open[g.o]=1;for(int j=0;j<n;j++)asg[g.sites[j]]=g.o;}
  if(joint){for(int p=0;p<P;p++){int w=0;for(int o:ops)if(v[u[o][p]]>.5&&open[o]){if(w>=(int)pw[p].size()){good=false;break;}wof[pw[p][w++]]=o;}}}else for(int w=0;w<I.nw;w++)if(staff[w]>=0&&open[staff[w]])wof[w]=staff[w];
  if(good)improved=v5_offer(I,asg,open,wof);
 }
 A.destroy(h);if(DBG)fprintf(stderr,"v5_mip joint=%d groups=%zu vars=%zu rows=%zu status=%d prep=%.6f seconds=%.6f before=%.12f after=%.12f\n",joint,groups.size(),M.cost.size(),M.rl.size(),status,prep,elapsed()-begin,before,g_best.load());return improved;
}
// Read the already published worker certificate from memory, after all workers joined.
static bool v5_saved_staff(const Inst&I,vector<int>&staff){
 staff.assign(I.nw,-1);int ix=g_idx.load(memory_order_acquire);if(ix<0)return false;
 const string&text=g_buf[ix];JReader r(text.data(),text.data()+text.size());
 try{r.need('[');if(r.eat(']'))return true;
  while(true){r.need('{');int o=-1;vector<int>ws;
   while(true){string key=r.str();r.need(':');if(key=="officeId")o=(int)r.num();else if(key=="workers"){r.need('[');if(!r.eat(']')){while(true){ws.push_back((int)r.num());if(r.eat(']'))break;r.need(',');}}}else r.skip();if(r.eat('}'))break;r.need(',');}
   if(o<0||o>=I.no)return false;for(int w:ws){if(w<0||w>=I.nw||staff[w]>=0)return false;staff[w]=o;}
   if(r.eat(']'))break;r.need(',');
  }
 }catch(...){return false;}return true;
}
static void v5_finish(const Inst&I,double limit){
 double end=limit-.15;if(elapsed()>=end-.05||g_best.load()<=0)return;if(!v5_api().ready)return;
 vector<int>old,staff;vector<char>op;{lock_guard<mutex>lk(g_best_mx);old=g_best_asg;op=g_best_open;}Sol env;env.init(I);env.load_state(old,op);if(!v5_saved_staff(I,staff))return;
 int mode=getenv("MIP_MODE")?atoi(getenv("MIP_MODE")):2;
 // Mode 0: fixed territory; mode 1/2: safe expansion; mode 3: also new offices.
 if(mode>=3){vector<pair<double,int>>rank;for(int o=0;o<I.no;o++)if(!op[o]&&I.maxsize[o]>0&&!env.cov[I.ns+o]){vector<double>p;for(int s=0;s<I.ns;s++)if(I.servable[s]&&!env.cov[s]&&I.pr(o,s)>0)p.push_back(I.pr(o,s));sort(p.rbegin(),p.rend());double b=-I.cost[o];for(int j=0;j<min((int)p.size(),I.maxsize[o]);j++)b+=p[j];rank.push_back({b,o});}sort(rank.rbegin(),rank.rend());int count=0;for(auto e:rank)if(count<3&&e.first>0&&!env.cov[I.ns+e.second]){env.isopen[e.second]=1;env.set_hull(e.second,{I.P[I.ns+e.second]});count++;}}
 if(mode>=1&&elapsed()<end-.05){vector<tuple<double,int,int>>offers;for(int o=0;o<I.no;o++)if(env.isopen[o]){vector<pair<double,int>>v;for(int s=0;s<I.ns;s++)if(I.servable[s]&&!env.cov[s]&&I.pr(o,s)>0)v.push_back({I.pr(o,s),s});sort(v.rbegin(),v.rend());for(int j=0;j<min(64,(int)v.size());j++)offers.emplace_back(v[j].first,o,v[j].second);}sort(offers.rbegin(),offers.rend());int attempts=0,accepted=0;double growend=min(end-.05,elapsed()+.25);for(auto e:offers){if(attempts>=320||elapsed()>=growend)break;int o=get<1>(e),s=get<2>(e);if(env.cov[s])continue;attempts++;vector<Pt>h;if(env.geo_ok(s,o,h)){if(!h.empty())env.set_hull(o,h);accepted++;}}if(DBG)fprintf(stderr,"v5_envelope attempts=%d accepted=%d t=%.6f\n",attempts,accepted,elapsed());}
 bool joint=mode>=2;
 if(joint && end-elapsed()>.65){double left=end-elapsed();if(left>.08)v5_select(I,env,old,op,staff,min(end,elapsed()+min(.45,left*.4)),false);
  {lock_guard<mutex>lk(g_best_mx);old=g_best_asg;op=g_best_open;}
  if(elapsed()<end-.04)v5_select(I,env,old,op,staff,end,true);
 }else v5_select(I,env,old,op,staff,end,false);
}

// v5.2 research: select convex envelopes with exact finite input-point packing.
static double v52_publish(const Inst&I,const vector<int>&asg,const vector<char>&op,const vector<int>&staff){
 double value=0;if(!verify(I,asg,op,staff,&value))return 0;lock_guard<mutex>lk(g_best_mx);double before=g_best.load();if(value<=before+1e-9)return 0;
 g_best.store(value);g_best_asg=asg;g_best_open=op;publish(serialize(I,asg,op,staff));push_elite(value,asg,op);return value-before;
}
struct V52Region {int o;vector<int> sites,foot;int tag;};
static vector<V52Region> v52_regions(const Inst&I,const vector<int>&old,const vector<char>&op,vector<int>&base,double end,int mode){
 vector<V52Region>regions;set<pair<int,vector<int>>>seen;Sol E,tmp;E.init(I);E.load_state(old,op);tmp.init(I);base.assign(I.no,-1);vector<int>ops;
 auto add=[&](int o,const vector<int>&ss,int tag,const vector<char>*blocked)->int{
  vector<Pt>h;h.reserve(ss.size()+1);for(int s:ss)h.push_back(I.P[s]);h.push_back(I.P[I.ns+o]);hull_of(h);tmp.set_hull(o,h);auto foot=tmp.covlist[o];tmp.clear_cov(o);sort(foot.begin(),foot.end());
  if(blocked)for(int p:foot)if((*blocked)[p])return -1;
  if(!seen.insert({o,foot}).second)return -1;vector<int>pool;for(int p:foot)if(p<I.ns&&I.servable[p])pool.push_back(p);if(pool.empty()||I.maxsize[o]<=0)return -1;
  int e=regions.size();regions.push_back({o,move(pool),move(foot),tag});return e;
 };
 for(int o=0;o<I.no;o++)if(op[o]){ops.push_back(o);base[o]=add(o,E.members[o],0,nullptr);}
 if(ops.empty())return regions;
 vector<tuple<double,int,int>>pairs;
 for(int j=0;j<(int)ops.size();j++)for(int k=j+1;k<(int)ops.size();k++){
  int o=ops[j],p=ops[k];double gain=0;for(int s:regions[base[o]].sites)gain+=max(0.,I.pr(p,s)-I.pr(o,s));for(int s:regions[base[p]].sites)gain+=max(0.,I.pr(o,s)-I.pr(p,s));Pt a=I.P[I.ns+o],b=I.P[I.ns+p];pairs.emplace_back(gain/(1+hypot(a.x-b.x,a.y-b.y)),o,p);
 }
 sort(pairs.rbegin(),pairs.rend());
 if(mode!=2)for(int pi=0;pi<min(3,(int)pairs.size())&&elapsed()<end;pi++){
  int o=get<1>(pairs[pi]),p=get<2>(pairs[pi]);vector<char>blocked(I.ns+I.no);for(int s=0;s<I.ns+I.no;s++)blocked[s]=E.cov[s]-E.incov[(size_t)o*E.np+s]-E.incov[(size_t)p*E.np+s]>0;
  vector<int>pool=regions[base[o]].sites;pool.insert(pool.end(),regions[base[p]].sites.begin(),regions[base[p]].sites.end());vector<pair<double,int>>free;
  for(int s=0;s<I.ns;s++)if(I.servable[s]&&!E.cov[s])free.push_back({max(I.pr(o,s),I.pr(p,s)),s});sort(free.rbegin(),free.rend());for(int j=0;j<min(256,(int)free.size());j++)pool.push_back(free[j].second);sort(pool.begin(),pool.end());pool.erase(unique(pool.begin(),pool.end()),pool.end());
  Pt a=I.P[I.ns+o],b=I.P[I.ns+p];double dx=b.x-a.x,dy=b.y-a.y;if(dx==0&&dy==0)continue;
  for(auto rt:vector<pair<double,double>>{{0,.25},{0,.5},{0,.75},{.5,.5},{-.5,.5}}){if(elapsed()>=end)break;double nx=dx-rt.first*dy,ny=dy+rt.first*dx,cut=(1-rt.second)*(a.x*nx+a.y*ny)+rt.second*(b.x*nx+b.y*ny);
   for(int side=0;side<2;side++){int office=side?p:o;vector<int>ss;for(int s:pool){double v=I.P[s].x*nx+I.P[s].y*ny;if(side?v>cut:v<cut)ss.push_back(s);}
    if(add(office,ss,1,&blocked)<0){sort(ss.begin(),ss.end(),[&](int x,int y){double px=I.pr(office,x),py=I.pr(office,y);return px!=py?px>py:x<y;});vector<int>cur;int attempts=0;
     for(int s:ss){if(elapsed()>=end||attempts++>=256)break;vector<Pt>h;for(int t:cur)h.push_back(I.P[t]);h.push_back(I.P[s]);h.push_back(I.P[I.ns+office]);hull_of(h);tmp.set_hull(office,h);bool ok=true;for(int t:tmp.covlist[office])if(blocked[t]){ok=false;break;}tmp.clear_cov(office);if(ok)cur.push_back(s);}
     add(office,cur,2,&blocked);
    }
   }
  }
 }
 if(mode!=1&&elapsed()<end){vector<pair<double,int>>rank;for(int o=0;o<I.no;o++)if(!op[o]&&I.maxsize[o]>0){vector<double>pp;for(int s=0;s<I.ns;s++)if(I.servable[s])pp.push_back(I.pr(o,s));sort(pp.rbegin(),pp.rend());double v=-I.cost[o];for(int j=0;j<min(I.maxsize[o],(int)pp.size());j++)v+=max(0.,pp[j]);rank.push_back({v,o});}sort(rank.rbegin(),rank.rend());
  for(int nr=0;nr<(rank.empty()?1:2)&&elapsed()<end;nr++){int neo=nr?rank[0].second:-1;vector<int>oo=ops;if(neo>=0)oo.push_back(neo);double scale=1e300;if(neo>=0)for(int o:ops){Pt a=I.P[I.ns+neo],b=I.P[I.ns+o];scale=min(scale,(a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y));}
   for(double bias:(neo<0?vector<double>{0}:vector<double>{-.45,0,.45})){if(elapsed()>=end)break;vector<vector<int>>ss(I.no);vector<int>owner(I.no,-1);
    for(int s=0;s<I.ns+I.no;s++){double best=1e300,second=1e300;int who=-1;for(int o:oo){Pt a=I.P[s],b=I.P[I.ns+o];double d=(a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(o==neo?bias*scale:0);if(d<best){second=best;best=d;who=o;}else second=min(second,d);}if(s<I.ns){if(I.servable[s]&&best<second)ss[who].push_back(s);}else owner[s-I.ns]=who;}
    for(int o:oo)if(owner[o]==o)add(o,ss[o],neo<0?3:4,nullptr);
   }
  }
 }
 return regions;
}
struct V52Group {int e,o,w,q,v;vector<int>skills,sites;};
static bool v52_select(const Inst&I,const vector<V52Region>&R,const vector<int>&base,const vector<int>&old,const vector<char>&op,const vector<int>&staff,double end,bool joint){
 auto&A=v5_api();if(!A.ready||elapsed()>=end-.03||R.empty())return false;double start=elapsed(),before=g_best.load(),inf=1e30;V5Model M;vector<int>ops,y(I.no,-1),z;vector<vector<int>>oe(I.no),og(I.no);vector<vector<char>>have(I.no,vector<char>(I.nsk));
 for(int w=0;w<I.nw;w++)if(staff[w]>=0)for(int k=0;k<I.nsk;k++)have[staff[w]][k]|=I.wmask[w][k];
 for(int e=0;e<(int)R.size();e++){int o=R[e].o;oe[o].push_back(e);z.push_back(M.var(0,0,1,1,base[o]==e));}
 for(int o=0;o<I.no;o++)if(!oe[o].empty()){ops.push_back(o);y[o]=M.var(I.cost[o],0,1,1,op[o]);}
 vector<V52Group>G;map<vector<int>,int>lookup;long long T=1;int C=1;
 for(int e=0;e<(int)R.size();e++){int o=R[e].o;vector<int>weights;C=max(C,I.maxsize[o]);for(int s:R[e].sites){bool ok=true;if(!joint)for(int k:I.skillset[s])if(!have[o][k]){ok=false;break;}if(!ok)continue;
   vector<int>key{e,I.ntask[s]};if(joint)key.insert(key.end(),I.skillset[s].begin(),I.skillset[s].end());auto it=lookup.find(key);int g;if(it==lookup.end()){g=G.size();lookup[key]=g;og[o].push_back(g);G.push_back({e,o,I.ntask[s],-1,-1,joint?I.skillset[s]:vector<int>{},{}});}else g=it->second;G[g].sites.push_back(s);weights.push_back(I.ntask[s]);}
  sort(weights.rbegin(),weights.rend());long long load=0;for(int j=0;j<min(I.maxsize[o],(int)weights.size());j++)load+=weights[j];T=max(T,load);
 }
 for(auto&g:G){sort(g.sites.begin(),g.sites.end(),[&](int a,int b){double pa=I.pr(g.o,a),pb=I.pr(g.o,b);return pa!=pb?pa>pb:a<b;});int n=0;for(int s:g.sites)n+=base[g.o]==g.e&&old[s]==g.o;int cap=min(I.maxsize[g.o],(int)g.sites.size());g.q=M.var(0,0,cap,1,n);double warm=0;for(int j=0;j<n;j++)warm+=I.pr(g.o,g.sites[j]);g.v=M.var(-1,-inf,inf,0,warm);M.row({{g.q,1},{z[g.e],-(double)cap}},-inf,0);
  double prefix=0,last=0;for(int j=0;j<(int)g.sites.size();j++){double p=I.pr(g.o,g.sites[j]);if(!j||p!=last)M.row({{g.v,1},{g.q,-p},{z[g.e],-(prefix-j*p)}},-inf,0);prefix+=p;last=p;}
 }
 map<vector<int>,vector<int>>profiles;for(int w=0;w<I.nw;w++){vector<int>ks;for(int k=0;k<I.nsk;k++)if(I.wmask[w][k])ks.push_back(k);if(!ks.empty())profiles[ks].push_back(w);}vector<vector<int>>pk,pw;for(auto&a:profiles){pk.push_back(a.first);pw.push_back(a.second);}int P=pk.size();vector<vector<int>>u(I.no,vector<int>(P,-1));
 if(joint){for(int o:ops)for(int p=0;p<P;p++){bool warm=false;for(int w:pw[p])warm|=staff[w]==o;u[o][p]=M.var(0,0,1,1,warm);M.row({{u[o][p],1},{y[o],-1}},-inf,0);}for(int p=0;p<P;p++){vector<pair<int,double>>row;for(int o:ops)row.push_back({u[o][p],1});M.row(row,-inf,pw[p].size());}for(auto&g:G)for(int k:g.skills){vector<pair<int,double>>row{{g.q,1}};for(int p=0;p<P;p++)if(binary_search(pk[p].begin(),pk[p].end(),k))row.push_back({u[g.o][p],-(double)min(I.maxsize[g.o],(int)g.sites.size())});M.row(row,-inf,0);}}
 long long minload=T,maxload=0;int mincount=C,maxcount=0;for(int o:ops)if(op[o]){long long load=0;int n=0;for(int s=0;s<I.ns;s++)if(old[s]==o){n++;load+=I.ntask[s];}minload=min(minload,load);maxload=max(maxload,load);mincount=min(mincount,n);maxcount=max(maxcount,n);}
 if(!maxcount){mincount=0;minload=0;}
 int hi=M.var(I.alpha,0,T,0,maxload),lo=M.var(-I.alpha,0,T,0,minload),ch=M.var(0,0,C,0,maxcount),cl=M.var(0,0,C,0,mincount);
 for(int o:ops){vector<pair<int,double>>row{{y[o],-1}},cnt,load;for(int e:oe[o])row.push_back({z[e],1});M.row(row,0,0);for(int g:og[o]){cnt.push_back({G[g].q,1});load.push_back({G[g].q,(double)G[g].w});}
  row=cnt;row.push_back({y[o],-(double)I.maxsize[o]});M.row(row,-inf,0);row=cnt;row.push_back({y[o],-1});M.row(row,0,inf);row=cnt;row.push_back({ch,-1});M.row(row,-inf,0);row.clear();for(auto a:cnt)row.push_back({a.first,-a.second});row.push_back({cl,1});row.push_back({y[o],(double)C});M.row(row,-inf,C);
  row=load;row.push_back({hi,-1});M.row(row,-inf,0);row.clear();for(auto a:load)row.push_back({a.first,-a.second});row.push_back({lo,1});row.push_back({y[o],(double)T});M.row(row,-inf,T);
 }
 M.row({{lo,1},{hi,-1}},-inf,0);M.row({{cl,1},{ch,-1}},-inf,0);M.row({{ch,1},{cl,-1}},-inf,I.A);
 vector<vector<int>>covers(I.ns+I.no);for(int e=0;e<(int)R.size();e++)for(int p:R[e].foot)covers[p].push_back(e);set<vector<int>>conflicts;for(auto&es:covers)if(es.size()>1){bool mixed=false;for(int e:es)mixed|=R[e].o!=R[es[0]].o;if(mixed)conflicts.insert(es);}for(auto&es:conflicts){vector<pair<int,double>>row;for(int e:es)row.push_back({z[e],1});M.row(row,-inf,1);}
 if(elapsed()>=end-.03)return false;void*h=A.create();if(!h)return false;A.setbool(h,"output_flag",0);A.setint(h,"threads",1);A.setint(h,"random_seed",1);A.setdouble(h,"mip_rel_gap",1e-8);int rc=A.pass(h,M.cost.size(),M.rl.size(),M.ai.size(),2,1,0,M.cost.data(),M.lb.data(),M.ub.data(),M.rl.data(),M.ru.data(),M.rs.data(),M.ai.data(),M.av.data(),M.integer.data());if(rc<0){A.destroy(h);return false;}
 A.setsol(h,M.warm.data(),nullptr,nullptr,nullptr);double prep=elapsed()-start;A.setdouble(h,"time_limit",max(.001,end-elapsed()-.04));A.run(h);int feasible=0,status=A.status(h);A.getint(h,"primal_solution_status",&feasible);bool improved=false;double own_gain=0;
 if(feasible==2){vector<double>v(M.cost.size());if(A.getsol(h,v.data(),nullptr,nullptr,nullptr)>=0){vector<int>asg(I.ns,-1),wof(I.nw,-1);vector<char>open(I.no,0);bool good=true;
  for(auto&g:G){double val=v[g.q];if(!isfinite(val)){good=false;break;}int n=lround(val);if(fabs(val-n)>1e-4||n<0||n>(int)g.sites.size()){good=false;break;}for(int j=0;j<n;j++){int s=g.sites[j];if(asg[s]>=0){good=false;break;}asg[s]=g.o;open[g.o]=1;}}
  if(joint){for(int p=0;p<P;p++){int w=0;for(int o:ops)if(open[o]&&v[u[o][p]]>.5){if(w>=(int)pw[p].size()){good=false;break;}wof[pw[p][w++]]=o;}}}else for(int w=0;w<I.nw;w++)if(staff[w]>=0&&open[staff[w]])wof[w]=staff[w];
  if(good){own_gain=v52_publish(I,asg,open,wof);improved=own_gain>0;}
 }}
 A.destroy(h);if(DBG)fprintf(stderr,"v52_mip joint=%d regions=%zu groups=%zu vars=%zu rows=%zu status=%d prep=%.6f seconds=%.6f before=%.12f after=%.12f own_gain=%.12f\n",joint,R.size(),G.size(),M.cost.size(),M.rl.size(),status,prep,elapsed()-start,before,g_best.load(),own_gain);return improved;
}
static void v52_finish(const Inst&I,double end){
 if(elapsed()>=end-.1||g_best.load()<=0)return;if(!v5_api().ready)return;vector<int>old,staff,base;vector<char>op;{lock_guard<mutex>lk(g_best_mx);old=g_best_asg;op=g_best_open;if(!v5_saved_staff(I,staff))return;}
 int mode=getenv("REGION_MODE")?atoi(getenv("REGION_MODE")):0;bool joint=getenv("REGION_JOINT")&&atoi(getenv("REGION_JOINT"));double start=elapsed();auto regions=v52_regions(I,old,op,base,min(end-.06,elapsed()+min(.5,(end-elapsed())*.2)),mode);if(DBG)fprintf(stderr,"v52_regions n=%zu seconds=%.6f\n",regions.size(),elapsed()-start);v52_select(I,regions,base,old,op,staff,end,joint);
}

int main(int argc, char** argv) {
    string inp = argc > 1 ? argv[1] : "instance.json";
    string outp = argc > 2 ? argv[2] : "solution.json";
    double limit = argc > 3 ? atof(argv[3]) : (getenv("TL") ? atof(getenv("TL")) : 280.0);

    g_wdfs_deadline = limit - max(0.5, 0.01 * limit);
    DBG = getenv("DBG") != nullptr; DBG2 = getenv("DBG2") != nullptr;
    g_fd = open(outp.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
    publish("[]\n");
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_signal;
    sigaction(SIGTERM, &sa, nullptr);
    sigaction(SIGINT, &sa, nullptr);
    sigaction(SIGALRM, &sa, nullptr);
    sigaction(SIGHUP, &sa, nullptr);
    sigaction(SIGUSR1, &sa, nullptr);
    alarm((unsigned)max(5.0, limit + 14));

    try {
        Inst I = load_instance(inp);
        g_geo_grid.init(I);
        if (I.ns == 0 || I.no == 0) return 0;
        Fast F(I);
        const uint64_t seed0 = getenv("SEED") ? strtoull(getenv("SEED"), nullptr, 10) * 0x9E3779B97F4A7C15ULL : 0;
        mt19937_64 rng(0x9E3779B97F4A7C15ULL ^ seed0);

        // WARM_START=0: legacy; 1: random subsets; 2: genetic subsets (default).
        int warm_mode = getenv("WARM_START") ? max(0, min(2, atoi(getenv("WARM_START")))) : 2;
        if (getenv("FORCE_OPS")) warm_mode = 0;
        double t_outer = min((warm_mode ? 0.10 : 0.22) * limit, warm_mode ? 30.0 : 60.0);
        map<vector<int>, Cand> cache;
        vector<Pt> G0(I.P.begin() + I.ns, I.P.end());
        auto ev = [&](vector<int> op) -> double {
            sort(op.begin(), op.end());
            if (op.empty()) return 0.0;
            auto it = cache.find(op);
            if (it != cache.end()) return it->second.f;
            Cand c;
            c.op = op;
            c.h.assign(I.no, 0.0);
            c.G = G0;
            c.f = F.search(op, c.h, c.G, 40, t_outer);
            cache.emplace(op, move(c));
            return cache[op].f;
        };
        // жадное добавление офисов
        vector<int> cur;
        double cur_f = 0;
        const bool lazy = !getenv("LAZY") || atoi(getenv("LAZY")) > 0;  // LAZY=0 — старый жадный
        if (lazy) {
            // ленивый жадный: приросты с прошлых шагов — оценки сверху, пересчитываем
            // только лидера; полный перебор на каждом шаге на 10⁴ сайтов не успевает
            vector<double> gain(I.no, 1e300);
            vector<char> in(I.no, 0);
            while (elapsed() < t_outer) {
                bool added = false;
                while (elapsed() < t_outer) {
                    int bo = -1;
                    for (int o = 0; o < I.no; o++)
                        if (!in[o] && (bo < 0 || gain[o] > gain[bo])) bo = o;
                    if (bo < 0 || gain[bo] <= 1e-9) break;
                    vector<int> v = cur; v.push_back(bo);
                    double g = ev(v) - cur_f;
                    gain[bo] = g;
                    double next = -1e300;
                    for (int o = 0; o < I.no; o++) if (!in[o] && o != bo) next = max(next, gain[o]);
                    if (g > 1e-9 && g >= next) {
                        cur.push_back(bo); in[bo] = 1; cur_f += g; added = true;
                        break;
                    }
                }
                if (!added) break;
            }
        }
        while (!lazy && elapsed() < t_outer) {
            double bf = NEG; int bo = -1;
            for (int o = 0; o < I.no && elapsed() < t_outer; o++) {
                if (find(cur.begin(), cur.end(), o) != cur.end()) continue;
                vector<int> v = cur; v.push_back(o);
                double f = ev(v);
                if (f > bf) { bf = f; bo = o; }
            }
            if (bo < 0 || bf <= cur_f + 1e-9) break;
            cur.push_back(bo); cur_f = bf;
        }
        // локальный поиск add / drop / swap
        bool improved = true;
        while (improved && elapsed() < t_outer) {
            improved = false;
            vector<vector<int>> moves;
            for (int o : cur) { vector<int> v; for (int x : cur) if (x != o) v.push_back(x); moves.push_back(v); }
            for (int n = 0; n < I.no; n++) if (find(cur.begin(), cur.end(), n) == cur.end()) {
                vector<int> v = cur; v.push_back(n); moves.push_back(v);
                for (int o : cur) { vector<int> w; for (int x : cur) if (x != o) w.push_back(x); w.push_back(n); moves.push_back(w); }
            }
            shuffle(moves.begin(), moves.end(), rng);
            for (auto& m : moves) {
                if (elapsed() > t_outer) break;
                double f = ev(m);
                if (f > cur_f + 1e-9) { cur = m; cur_f = f; improved = true; break; }
            }
        }
        // одиночные офисы как запасные варианты
        for (int o = 0; o < I.no && elapsed() < t_outer + 2; o++) { vector<int> v{o}; ev(v); }

        vector<Cand> warm_real;
        if (warm_mode) warm_real = wide_start(I, F, cache, rng, min(0.22 * limit, 60.0), limit, warm_mode);
        vector<Cand> cands;
        if (getenv("FORCE_OPS")) {               // отладка: задать набор офисов вручную
            Cand c;
            char* t = strdup(getenv("FORCE_OPS"));
            for (char* q = strtok(t, ","); q; q = strtok(nullptr, ",")) c.op.push_back(atoi(q));
            sort(c.op.begin(), c.op.end());
            c.h.assign(I.no, 0.0);
            c.G.assign(I.P.begin() + I.ns, I.P.end());
            c.f = F.search(c.op, c.h, c.G, 300, elapsed() + 5.0);
            cands.push_back(c);
        } else {
            vector<pair<double, const Cand*>> top;
            for (auto& kv : cache) if (kv.second.f > NEG / 2) top.push_back({kv.second.f, &kv.second});
            sort(top.rbegin(), top.rend());
            for (size_t i = 0; i < top.size() && i < 5; i++) cands.push_back(*top[i].second);
            // плюс лучший набор каждого размера: иначе варианты с другим числом
            // офисов (и другим делением навыков) просто не попадают в перебор
            map<size_t, const Cand*> bysize;
            for (auto& e : top) {
                size_t k = e.second->op.size();
                bool near = lazy && abs((int)k - (int)top[0].second->op.size()) <= 2;
                if ((k <= 8 || near) && !bysize.count(k)) bysize[k] = e.second;
            }
            for (auto& kv : bysize) {
                bool have = false;
                for (auto& c : cands) if (c.op == kv.second->op) { have = true; break; }
                if (!have) cands.push_back(*kv.second);
            }
        }
        for (const auto& c : warm_real) {
            bool have = false;
            for (const auto& old : cands) if (old.op == c.op) { have = true; break; }
            if (!have) cands.push_back(c);
        }
        if (cands.empty()) {
            Cand c;
            for (int o = 0; o < I.no; o++) c.op.push_back(o);
            c.f = 0;
            cands.push_back(c);
        }

        double dp_deadline = limit - max(1.0, 0.05 * limit);
        int nth = detect_cpus();
        if (I.ns > 20000) nth = min(nth, 6);
        // без явного предела арен malloc в потоках сам читает /sys/devices/system/cpu/online
        mallopt(M_ARENA_MAX, nth + 2);
        vector<thread> th;
        // EXACT2=1: точный перебор 1–2 офисов отдельным потоком (сверх nth)
        if (getenv("EXACT2") && atoi(getenv("EXACT2")) > 0)
            th.emplace_back(exact2_thread, cref(I), limit, 0xE2ULL ^ seed0);
        for (int i = 1; i < nth; i++)
            th.emplace_back(worker, cref(I), cref(F), cref(cands),
                            (0xA5A5ULL * (i + 1) + 12345) ^ seed0, limit, dp_deadline, i);
        worker(I, F, cands, 777 ^ seed0, limit, dp_deadline, 0);
        for (auto& t : th) t.join();
        exact2_publish(I);
        finish_solution(I, limit);
        boundary_finish(I, limit);
        if(!getenv("MIP")||atoi(getenv("MIP")))v5_finish(I,limit);

        if (DBG) fprintf(stderr, "worker_dfs calls=%ld solved=%ld nodes=%ld\n",
                         g_wdfs_calls.load(), g_wdfs_success.load(), g_wdfs_nodes.load());
        fprintf(stderr, "objective=%.6f fast=%.3f sets=%zu threads=%d t=%.1f\n",
                g_best.load(), cur_f, cache.size(), nth, elapsed());
    } catch (const exception& ex) {
        fprintf(stderr, "error: %s\n", ex.what());
    }
    return 0;
}
