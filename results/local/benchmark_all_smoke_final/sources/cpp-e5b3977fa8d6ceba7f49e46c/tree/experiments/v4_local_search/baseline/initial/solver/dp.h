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
