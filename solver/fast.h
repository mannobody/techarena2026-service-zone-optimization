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
