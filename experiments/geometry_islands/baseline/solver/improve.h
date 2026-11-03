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
