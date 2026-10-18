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
        vector<Pt> h;
        if (!s.geo_ok(x, o, h)) return false;
        s.add_site_raw(x, o, h);
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
        bool d = s.defer;
        s.defer = true;      // оболочку всё равно снимаем целиком
        while (!s.members[o].empty()) doRemove(s.members[o].back());
        s.defer = d;
        s.dirty[o] = 0;
        s.isopen[o] = 0;
        s.sig_open(o);
        s.clear_cov(o);
        s.hull[o].clear();
        if (rec) jr.push_back({3, -1, o});
    }
    void undo(size_t mark) {
        s.begin_defer();   // снимает и отложенное состояние вызывающего (end_defer ниже)
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
        s.end_defer();
    }
};
