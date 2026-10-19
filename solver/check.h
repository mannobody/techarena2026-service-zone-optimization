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
