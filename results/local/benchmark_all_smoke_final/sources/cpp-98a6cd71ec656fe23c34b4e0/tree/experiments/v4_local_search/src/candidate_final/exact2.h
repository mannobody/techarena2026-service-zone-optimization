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
