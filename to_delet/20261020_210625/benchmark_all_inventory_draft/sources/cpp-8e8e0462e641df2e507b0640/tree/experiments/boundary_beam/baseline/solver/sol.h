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
    void apply_cov(int o, const vector<Pt>& h) {
        char* row = &incov[(size_t)o * np];
        const auto& P = I->P;
        int n = np;
        if (h.empty()) return;
        if (h.size() == 1) {
            for (int i = 0; i < n; i++)
                if (fabs(P[i].x - h[0].x) <= I->eps_len && fabs(P[i].y - h[0].y) <= I->eps_len) {
                    row[i] = 1; cov[i]++; covlist[o].push_back(i);
                }
            return;
        }
        if (h.size() == 2) {
            double ax = h[0].x, ay = h[0].y, dx = h[1].x - ax, dy = h[1].y - ay;
            double L2 = dx * dx + dy * dy, L = sqrt(L2);
            for (int i = 0; i < n; i++) {
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
        for (int i = 0; i < n; i++) {
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
    bool geo_ok(int s, int o, vector<Pt>& newh) const {
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
            for (int i = 0; i < np; i++) {
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
            for (int i = 0; i < np; i++) {
                if (row[i] || cov[i] == 0) continue;
                double X = P[i].x - ax, Y = P[i].y - ay;
                double c = dx * Y - dy * X, t = dx * X + dy * Y;
                if (fabs(c) <= I->eps_cr + I->eps_len * L && t >= -I->eps_len * L && t <= L2 + I->eps_len * L) return false;
            }
        }
        return true;
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
