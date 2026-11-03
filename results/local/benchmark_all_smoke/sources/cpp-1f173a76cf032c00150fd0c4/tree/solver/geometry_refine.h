// geometry_refine.h: opt-in final pair repartition; main search remains unchanged.
// Geometry lab: independent monotone tail; include after existing improve/boundary/exact helpers.
// Original move_resplit/polish are unchanged; flags=7 counts+expanded pool,15 also A0 negative padding.
// All function deadlines are absolute elapsed(). Caller must supply only its available budget.
static bool geom_resplit(Engine& E, Guide& Gd, mt19937_64& rng, bool force,
                         int fo1 = -1, int fo2 = -1, int ndir = 9, double hard = 1e18, int gm = 7) {
    if(elapsed()>=hard)return false;
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

    int cap1=I.maxsize[o1],cap2=I.maxsize[o2];
    if(gm&1){
        int othermin=INT_MAX;
        for(int o:op)if(o!=o1&&o!=o2&&s.size_[o]>0)othermin=min(othermin,s.size_[o]);
        if(othermin<INT_MAX){
            long long lim=(long long)othermin+I.A;
            cap1=(int)min((long long)cap1,lim);cap2=(int)min((long long)cap2,lim);
        }
    }
    bool pad=false;
    if((gm&8)&&I.A==0)for(int o:op)if(o!=o1&&o!=o2&&s.size_[o]>0)pad=true;
    auto cap=[&](int o){return o==o1?cap1:cap2;};
    // кандидаты: сайты обеих зон плюс свободные, чей ближайший открытый офис — один из двух
    vector<int> U = s.members[o1];
    U.insert(U.end(), s.members[o2].begin(), s.members[o2].end());
    for (int x = 0; x < I.ns; x++) {
        if (s.asg[x] >= 0 || !I.servable[x]) continue;
        if(gm&2){
            // Other hulls stay fixed. A site covered by a third zone cannot join this pair.
            bool blocked=false;
            if(s.cov[x])for(int o:op)if(o!=o1&&o!=o2&&geo_exact_covers(s.hull[o],I.P[x])){blocked=true;break;}
            if(!blocked && (pad || I.pr(o1,x)>0 || I.pr(o2,x)>0))U.push_back(x);
        }else for (int o : I.cand[x]) if (s.isopen[o]) { if (o == o1 || o == o2) U.push_back(x); break; }
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
    int bLo = o1, bHi = o2, bestCapLo=cap1, bestCapHi=cap2;
    vector<pair<double, int>> pr;
    pr.reserve(U.size());
    TopSum L, H;
    auto sweep = [&](double th) {
        if(elapsed()>=hard)return;
        double dx = cos(th), dy = sin(th);
        double p1 = q1.x * dx + q1.y * dy, p2 = q2.x * dx + q2.y * dy;
        int lo_off = o1, hi_off = o2;
        if (p1 > p2) { swap(p1, p2); lo_off = o2; hi_off = o1; }
        if (p2 - p1 < 1e-12 * max(1.0, I.ext)) return;
        pr.clear();
        for (int x : U) pr.push_back({I.P[x].x * dx + I.P[x].y * dy, x});
        sort(pr.begin(), pr.end());
        L.init(cap(lo_off), I.ntask);
        H.init(cap(hi_off), I.ntask);
        size_t start = 0;
        while (start < pr.size() && pr[start].first <= p1) {
            int x = pr[start].second;
            double v = Gd.eff(lo_off, x);
            if ((pad || v > 0) && fits(x, lo_off)) L.insert(v, x);
            start++;
        }
        for (size_t i = start; i < pr.size(); i++) {
            int x = pr[i].second;
            double v = Gd.eff(hi_off, x);
            if ((pad || v > 0) && fits(x, hi_off)) H.insert(v, x);
        }
        for (size_t k = start;; k++) {
            if((k&127)==0 && elapsed()>=hard)return;
            if(gm&4){
                int availableL=L.top.size()+L.rest.size(),availableH=H.top.size()+H.rest.size();
                L.m=(int)min((long long)cap(lo_off),(long long)min(availableH,cap(hi_off))+I.A);
                H.m=(int)min((long long)cap(hi_off),(long long)min(availableL,cap(lo_off))+I.A);
                L.balance();H.balance();
            }
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
                    bLo = lo_off; bHi = hi_off; bestCapLo=L.size(); bestCapHi=H.size();
                }
            }
            if (k >= pr.size() || pr[k].first > p2) break;
            int x = pr[k].second;
            double vh = Gd.eff(hi_off, x), vl = Gd.eff(lo_off, x);
            if ((pad || vh > 0) && fits(x, hi_off)) H.erase(vh, x);
            if ((pad || vl > 0) && fits(x, lo_off)) L.insert(vl, x);
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
    s.begin_defer();
    for (int x : U) if (s.asg[x] >= 0) E.doRemove(x);
    s.end_defer();
    vector<pair<double, int>> sl, sh;
    for (size_t i = 0; i < pr.size(); i++) {
        int x = pr[i].second;
        int o = i < bestkAll ? bLo : bHi;
        double v = Gd.eff(o, x);
        if ((!pad && v <= 0) || !fits(x, o)) continue;
        (o == bLo ? sl : sh).push_back({v, x});
    }
    sort(sl.rbegin(), sl.rend());
    sort(sh.rbegin(), sh.rend());
    if ((int)sl.size() > bestCapLo) sl.resize(bestCapLo);
    if ((int)sh.size() > bestCapHi) sh.resize(bestCapHi);
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

static void geom_polish(Sol& s, mt19937_64& rng, double tend, double dp_deadline, bool lock_offices = false, int flags = 7) {
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
                    if (!geom_resplit(E, G0, rng, false, op[i], op[j], I.ns > 2000 ? 12 : 36,
                                          pend, flags)) continue;
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

static void geom_finish(const Inst&I,double limit){
 int flags=getenv("GEOM_TAIL")?atoi(getenv("GEOM_TAIL")):0;
 if(!flags)return;
 double end=limit-max(.25,.002*limit);
 if(elapsed()>=end||g_best.load()<=0)return;
 double requested=getenv("GEOM_SECONDS")?max(0.,atof(getenv("GEOM_SECONDS"))):1.;
 end=min(end,elapsed()+requested);
 vector<int>a;vector<char>op;{lock_guard<mutex>lk(g_best_mx);a=g_best_asg;op=g_best_open;}
 if(a.empty())return;
 Sol s;s.init(I);s.load_state(a,op);g_wdfs_deadline=end;
 uint64_t seed=getenv("SEED")?strtoull(getenv("SEED"),nullptr,10):0;
 mt19937_64 rng(seed^0x63E0F17ULL);double before=g_best.load(),start=elapsed();
 geom_polish(s,rng,end,end,false,flags);
 fprintf(stderr,"geom_tail flags=%d before=%.12f after=%.12f seconds=%.6f\n",flags,before,g_best.load(),elapsed()-start);
}
