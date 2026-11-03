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
    s.begin_defer();
    for (int x : U) if (s.asg[x] >= 0) E.doRemove(x);
    s.end_defer();
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

// Точки P, покрытые оболочкой h (с теми же допусками, что Sol::apply_cov).
static void pts_in_hull(const Inst& I, const vector<Pt>& h, vector<int>& out) {
    out.clear();
    const auto& P = I.P;
    size_t m = h.size();
    if (m == 0) return;
    double mnx = 1e300, mxx = -1e300, mny = 1e300, mxy = -1e300;
    for (auto& q : h) { mnx = min(mnx, q.x); mxx = max(mxx, q.x); mny = min(mny, q.y); mxy = max(mxy, q.y); }
    double e = I.eps_len;
    if (m == 2) {
        double L = hypot(h[1].x - h[0].x, h[1].y - h[0].y);
        e = 2 * I.eps_len + (L > 0 ? I.eps_cr / L : 1e300);
        if (e > I.ext) e = 2 * I.ext;
    }
    I.for_box(mnx - e, mxx + e, mny - e, mxy + e, [&](int i) {
        bool in;
        if (m == 1) in = fabs(P[i].x - h[0].x) <= I.eps_len && fabs(P[i].y - h[0].y) <= I.eps_len;
        else if (m == 2) {
            double ax = h[0].x, ay = h[0].y, dx = h[1].x - ax, dy = h[1].y - ay;
            double L2 = dx * dx + dy * dy, L = sqrt(L2);
            double X = P[i].x - ax, Y = P[i].y - ay;
            double c = dx * Y - dy * X, t = dx * X + dy * Y;
            in = fabs(c) <= I.eps_cr + I.eps_len * L && t >= -I.eps_len * L && t <= L2 + I.eps_len * L;
        } else {
            in = !(P[i].x < mnx - e || P[i].x > mxx + e || P[i].y < mny - e || P[i].y > mxy + e);
            for (size_t e2 = 0; e2 < m && in; e2++) {
                const Pt& a = h[e2];
                const Pt& b = h[(e2 + 1) % m];
                double ex = b.x - a.x, ey = b.y - a.y;
                double tol = -I.eps_cr - I.eps_len * sqrt(ex * ex + ey * ey);
                in = ex * (P[i].y - a.y) - ey * (P[i].x - a.x) >= tol;
            }
        }
        if (in) out.push_back(i);
    });
}

// Кроссовер по зонам (по умолчанию вкл., XOVER=0 — выключить): пересадить в текущее решение 1–3 соседние зоны
// элитного решения целиком. Сначала расчищаем их оболочки (чужие сайты внутри
// снимаем, офисы внутри закрываем), потом заселяем зоны элиты от офиса наружу.
// Дозаполнение — recreate у вызывающего.
static bool ruin_crossover(Engine& E, mt19937_64& rng) {
    Sol& s = E.s;
    const Inst& I = E.I;
    vector<int> ea;
    vector<char> eo;
    if (!pick_elite(rng, ea, eo) || ea == s.asg) return false;
    vector<int> bs;
    for (int x = 0; x < I.ns; x++) if (ea[x] >= 0) bs.push_back(x);
    if (bs.empty()) return false;
    const Pt c = I.P[bs[rng() % bs.size()]];
    vector<pair<double, int>> near;
    for (int o = 0; o < I.no; o++)
        if (eo[o]) near.push_back({hypot(I.P[I.ns + o].x - c.x, I.P[I.ns + o].y - c.y), o});
    sort(near.begin(), near.end());
    int k = min((int)near.size(), 1 + (int)(rng() % 3));
    vector<int> Z;
    vector<vector<int>> mem;
    vector<char> inZ(I.no, 0);
    for (int i = 0; i < k; i++) { Z.push_back(near[i].second); inZ[near[i].second] = 1; }
    mem.assign(k, {});
    for (int x : bs) for (int i = 0; i < k; i++) if (ea[x] == Z[i]) mem[i].push_back(x);
    // расчистка
    vector<int> inside;
    s.begin_defer();
    for (int i = 0; i < k; i++) {
        vector<Pt> h;
        for (int x : mem[i]) h.push_back(I.P[x]);
        h.push_back(I.P[I.ns + Z[i]]);
        hull_of(h);
        pts_in_hull(I, h, inside);
        for (int p : inside) {
            if (p < I.ns) { if (s.asg[p] >= 0 && s.asg[p] != Z[i]) E.doRemove(p); }
            else if (!inZ[p - I.ns] && s.isopen[p - I.ns]) E.doClose(p - I.ns);
        }
    }
    for (int i = 0; i < k; i++) {
        int o = Z[i];
        if (!s.isopen[o]) continue;
        for (int x : vector<int>(s.members[o])) if (ea[x] != o) E.doRemove(x);
    }
    s.end_defer();
    for (int i = 0; i < k; i++) {
        int o = Z[i];
        if (!s.isopen[o]) E.doOpen(o);
        if (!s.isopen[o]) continue;
        const Pt& q = I.P[I.ns + o];
        sort(mem[i].begin(), mem[i].end(), [&](int a, int b) {
            return hypot(I.P[a].x - q.x, I.P[a].y - q.y) < hypot(I.P[b].x - q.x, I.P[b].y - q.y);
        });
        for (int x : mem[i]) if (s.asg[x] < 0) E.doAdd(x, o);
    }
    return true;
}


// Count-preserving composite exchanges. All removals precede all insertions:
// intermediate A/worker violations are allowed, the final state must be feasible.
// Exact objective and geometry; the bounded candidate pool is heuristic.
struct ExchangeStats {
    long proposed=0, positive=0, geometry_or_skill=0, worker_reject=0, accepted=0;
    double gain=0, seconds=0;
};
static bool exchange_apply(Engine& E, const vector<pair<int,int>>& changes) {
    size_t mark=E.jr.size();
    E.s.begin_defer();
    for(auto [x,o]:changes) E.doRemove(x);
    E.s.end_defer();
    for(auto [x,o]:changes) if(o>=0 && !E.doAdd(x,o)) { E.undo(mark); return false; }
    if(E.size_viol(-1,-1)>0 || (!E.I.simple_workers && !E.s.greedy_workers(nullptr))) {
        E.undo(mark); return false;
    }
    return true;
}
static bool exchange_descent(Sol& s, mt19937_64& rng, double deadline, int depth,
                             ExchangeStats* stats=nullptr) {
    const Inst& I=*s.I;
    ExchangeStats st; double t0=elapsed();
    Engine E(s);E.rec=true;Guide G(s,0.);
    bool any=false;
    struct Item {vector<int> xs;long long load;double delta;};
    for(int pass=0;pass<8 && elapsed()<deadline;pass++) {
        bool changed=false;
        vector<int> offices;
        for(int o=0;o<I.no;o++)if(s.isopen[o] && s.size_[o]>0)offices.push_back(o);
        shuffle(offices.begin(),offices.end(),rng);
        for(int a:offices) {
            if(elapsed()>=deadline)break;
            // b=-1 replaces assigned sites with currently unassigned sites.
            vector<int> destinations=offices;destinations.push_back(-1);
            for(int b:destinations) {
                if(b==a || (b>=0 && b<a) || elapsed()>=deadline)continue;
                vector<int> ax=s.members[a],bx;
                if(b>=0)bx=s.members[b];
                else for(int x=0;x<I.ns;x++)if(s.asg[x]<0 && I.servable[x])bx.push_back(x);
                auto gain=[&](int x,bool left) {
                    if(b<0)return left ? -I.pr(a,x) : I.pr(a,x);
                    return left ? I.pr(b,x)-I.pr(a,x) : I.pr(a,x)-I.pr(b,x);
                };
                // Mix profit candidates, task-load extremes, and random sites.
                auto trim=[&](vector<int>& v,bool left) {
                    if(v.size()<=20)return;
                    vector<int> q=v,out;
                    sort(q.begin(),q.end(),[&](int x,int y){double dx=gain(x,left),dy=gain(y,left);return dx!=dy?dx>dy:x<y;});
                    for(int i=0;i<10;i++)out.push_back(q[i]);
                    sort(q.begin(),q.end(),[&](int x,int y){return I.ntask[x]!=I.ntask[y]?I.ntask[x]<I.ntask[y]:x<y;});
                    for(int i=0;i<3;i++){out.push_back(q[i]);out.push_back(q[q.size()-1-i]);}
                    shuffle(v.begin(),v.end(),rng);
                    for(int x:v){if(out.size()>=20)break;if(find(out.begin(),out.end(),x)==out.end())out.push_back(x);}
                    sort(out.begin(),out.end());out.erase(unique(out.begin(),out.end()),out.end());v.swap(out);
                };
                trim(ax,true);trim(bx,false);
                for(int k=1;k<=depth && !changed && elapsed()<deadline;k++) {
                    vector<Item> aa,bb;
                    auto groups=[&](const vector<int>& v,bool left,vector<Item>& out) {
                        for(size_t i=0;i<v.size();i++) {
                            int x=v[i];
                            if(k==1)out.push_back({{x},I.ntask[x],gain(x,left)});
                            else for(size_t j=i+1;j<v.size();j++)out.push_back({{x,v[j]},(long long)I.ntask[x]+I.ntask[v[j]],gain(x,left)+gain(v[j],left)});
                        }
                    };
                    groups(ax,true,aa);groups(bx,false,bb);
                    struct Proposal{double gain;int i,j;};vector<Proposal> todo;
                    double tail=G.tail2(-1,0,0,-1,0,0);
                    for(int i=0;i<(int)aa.size() && elapsed()<deadline;i++)for(int j=0;j<(int)bb.size();j++) {
                        st.proposed++;
                        long long dl=bb[j].load-aa[i].load;
                        double d=aa[i].delta+bb[j].delta+G.tail2(a,0,dl,b,0,b<0?0:-dl)-tail;
                        if(d>1e-9){st.positive++;todo.push_back({d,i,j});}
                    }
                    // Bounding the checks limits expensive hull/worker work, not the objective.
                    size_t n=min<size_t>(todo.size(),128);
                    partial_sort(todo.begin(),todo.begin()+n,todo.end(),[](const Proposal&x,const Proposal&y){return x.gain>y.gain;});
                    for(size_t z=0;z<n && elapsed()<deadline;z++) {
                        auto p=todo[z];vector<pair<int,int>> changes;
                        for(int x:aa[p.i].xs)changes.push_back({x,b});
                        for(int x:bb[p.j].xs)changes.push_back({x,a});
                        double f0=s.objective();size_t mark=E.jr.size();
                        if(!exchange_apply(E,changes)){st.geometry_or_skill++;continue;}
                        s.recompute_psum();
                        if(s.objective()<=f0+1e-9){E.undo(mark);s.recompute_psum();continue;}
                        st.accepted++;st.gain+=s.objective()-f0;E.jr.clear();
                        any=changed=true;offer(I,s);break;
                    }
                }
                if(changed)break;
            }
            if(changed)break;
        }
        if(!changed)break;
    }
    st.seconds=elapsed()-t0;
    if(stats)*stats=st;
    if(getenv("SEARCH_TRACE"))fprintf(stderr,"trace_exchange proposed=%ld positive=%ld rejected=%ld accepted=%ld gain=%.9f seconds=%.6f depth=%d\n",st.proposed,st.positive,st.geometry_or_skill,st.accepted,st.gain,st.seconds,depth);
    return any;
}
